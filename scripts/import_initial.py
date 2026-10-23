"""One-time, lossless import of the three supplied workbooks (standard library only)."""
import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
HEADERS = ["序号", "片名", "出品公司", "年份", "编导/导演", "编剧", "摄影", "美工", "主演", "其他主创", "备注"]
VOLUMES = [("upper", "上"), ("middle", "中"), ("lower", "下")]


def write_csv(name, fields, rows):
    with (ROOT / "data" / name).open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def extract(path):
    with zipfile.ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(x.itertext()) for x in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        # Read the actual worksheet XML, ignoring incorrect cached sheet dimensions.
        sheets = [n for n in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)]
        if len(sheets) != 1:
            raise ValueError(f"Expected one worksheet: {path}")
        for row in ET.fromstring(archive.read(sheets[0])).findall("m:sheetData/m:row", NS):
            cells = {}
            for cell in row.findall("m:c", NS):
                value = cell.find("m:v", NS)
                text = value.text or "" if value is not None else ""
                if cell.get("t") == "s":
                    text = strings[int(text)]
                elif cell.get("t") == "inlineStr":
                    text = "".join(cell.find("m:is", NS).itertext())
                cells[re.sub(r"\d", "", cell.get("r"))] = text
            yield int(row.get("r")), cells


def main():
    if (ROOT / "data" / "films.csv").exists():
        raise SystemExit("Formal data already exists. Import stopped to protect manual edits.")
    films, people, companies, relations, reviews, sources, raw = [], {}, {}, [], [], [], []

    def issue(film, field, reason, original):
        reviews.append(dict(id=f"review-{len(reviews)+1:05}", film_id=film["id"], field=field,
                            reason=reason, original_value=original, status="待核对",
                            source_id=film["source_id"], source_row=film["source_row"], resolution=""))

    for key, volume in VOLUMES:
        filename = f"中国无声电影剧本 {volume}_影片信息.xlsx"
        path = ROOT / "sources" / filename
        source_id = f"src-{key}"
        sources.append(dict(id=source_id, filename=filename, sheet="影片信息", sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            bibliography="", edition="", notes="文件名为暂定来源线索；书目、版本和页码尚未核实。"))
        for row_number, cells in extract(path):
            if row_number == 1:
                assert [cells.get(chr(65+i), "") for i in range(11)] == HEADERS
                continue
            if not cells.get("B"):
                continue
            values = {header: cells.get(chr(65+i), "") for i, header in enumerate(HEADERS)}
            film = dict(id=f"film-{key}-{row_number:04}", title=values["片名"], year=values["年份"],
                        company_text=values["出品公司"], director_text=values["编导/导演"], writer_text=values["编剧"],
                        cinematography_text=values["摄影"], art_text=values["美工"], cast_text=values["主演"],
                        other_text=values["其他主创"], notes=values["备注"], status="待核对",
                        source_id=source_id, source_row=str(row_number), source_page="")
            films.append(film)
            raw.append(dict(film_id=film["id"], source_id=source_id, sheet="影片信息", row=row_number, values=values))
            if not film["year"] or not re.fullmatch(r"\d{4}", film["year"]):
                issue(film, "year", "年份缺失或格式待确认，不从其他栏目推定", film["year"])
            if not film["company_text"]:
                issue(film, "company_text", "原表公司栏为空", "")
            if re.search(r"[*＊]", film["title"]):
                issue(film, "title", "星号含义待确认，暂不删除", film["title"])
            if "又名" in film["title"] or re.search(r"前.{0,2}后|[续集部]", film["title"]):
                issue(film, "title", "核对别名、分集或续作的条目边界", film["title"])
            if film["cast_text"]:
                issue(film, "cast_text", "演员与角色暂保留原文，待人工拆分", film["cast_text"])
            if film["other_text"]:
                issue(film, "other_text", "其他主创的具体职务待确认", film["other_text"])
            # Only exact, simple labels become candidate nodes. No inferred identities or aliases.
            company = film["company_text"].strip()
            if company and not re.search(r"[\d；;、/\n]|\s", company):
                if company not in companies:
                    companies[company] = dict(id=f"org-{len(companies)+1:04}", name=company, status="待核对", notes="原表名称候选；未合并异名或认定机构沿革")
                relations.append(dict(id=f"rel-{len(relations)+1:05}", from_id=companies[company]["id"], to_id=film["id"],
                                      type="出品（原表）", character="", source_id=source_id, source_row=str(row_number), source_column="C", source_page="", status="待核对"))
            elif company:
                issue(film, "company_text", "公司栏含数字或分隔符，暂不生成机构关系", company)
            for field, role, column in [("director_text", "编导／导演（原表）", "E"), ("writer_text", "编剧（原表）", "F"),
                                        ("cinematography_text", "摄影（原表）", "G"), ("art_text", "美工（原表）", "H")]:
                name = film[field].strip()
                if not name:
                    continue
                if re.fullmatch(r"[\u3400-\u9fff]{2,4}", name):
                    if name not in people:
                        people[name] = dict(id=f"person-{len(people)+1:04}", name=name, status="待核对", notes="同字姓名候选；身份与异名未核实，亦须排查短姓名连写")
                    relations.append(dict(id=f"rel-{len(relations)+1:05}", from_id=people[name]["id"], to_id=film["id"], type=role,
                                          character="", source_id=source_id, source_row=str(row_number), source_column=column, source_page="", status="待核对"))
                else:
                    issue(film, field, "姓名含分隔符、空格或长度异常，暂不自动拆分", name)
    for name, rows, fields in [
        ("films.csv", films, list(films[0])), ("people.csv", list(people.values()), ["id", "name", "status", "notes"]),
        ("companies.csv", list(companies.values()), ["id", "name", "status", "notes"]),
        ("relations.csv", relations, list(relations[0])), ("review_queue.csv", reviews, list(reviews[0])),
        ("sources.csv", sources, list(sources[0]))]:
        write_csv(name, fields, rows)
    (ROOT / "sources" / "original_records.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(films=len(films), people_candidates=len(people), company_candidates=len(companies), relations=len(relations), review_tasks=len(reviews)), ensure_ascii=False))


if __name__ == "__main__":
    main()
