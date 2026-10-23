"""Append mechanically observable questions without changing source facts."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = {"title": "片名", "director_text": "编导／导演", "writer_text": "编剧",
          "cinematography_text": "摄影", "art_text": "美工", "cast_text": "主演原文"}


def main():
    path = ROOT / "data" / "films.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames)
        films = list(reader)
    if "assistant_notes" not in fields:
        fields.append("assistant_notes")
    counts = {"company_year": 0, "brackets": 0, "stars": 0}
    appendix = ["# 补充备注：待确认的原表文字", "",
                "当前版本已获用户确认，可继续整理。以下是程序能直接观察到的格式疑点，不代表已判定史实错误。原始记载未改写，建议修改须另据来源确认。", "",
                "这些说明也保存在影片的 `assistant_notes` 栏，并显示为网页的“补充备注”。该栏与原表 `notes` 备注分开。", "",
                "| 影片编号 | 原表片名 | 补充备注 |", "| --- | --- | --- |"]
    for film in films:
        notes = []
        years = re.findall(r"\d{4}", film["company_text"])
        if years:
            counts["company_year"] += 1
            notes.append(f"出品公司栏含四位数字“{'、'.join(years)}”，疑似混入年份。年份栏当前为“{film['year'] or '空白'}”；未自动移填或改写公司名，请对照原书确认。")
        for field, label in LABELS.items():
            value = film[field]
            if value and (value.count("(") != value.count(")") or value.count("（") != value.count("）")):
                counts["brackets"] += 1
                notes.append(f"{label}的圆括号数量不配对，可能是漏括号、混用括号或文字截断；需对照原书，暂未补字。")
        if re.search(r"[*＊]", film["title"]):
            counts["stars"] += 1
            notes.append("片名中的星号含义尚未确认，暂保留原记号，不据此推定影片属性。")
        previous = film.get("assistant_notes", "")
        for note in notes:
            if note not in previous:
                previous = (previous + "\n" + note).strip()
        film["assistant_notes"] = previous
        if previous:
            values = [film["id"], film["title"], previous]
            appendix.append("| " + " | ".join(v.replace("|", "\\|").replace("\n", "<br>") for v in values) + " |")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(films)
    summary = f"公司栏含四位数字：{counts['company_year']} 条；圆括号不配对：{counts['brackets']} 个字段；片名含星号：{counts['stars']} 条。类型间可能重叠。"
    appendix[6:6] = [summary, ""]
    (ROOT / "REVIEW_NOTES.md").write_text("\n".join(appendix) + "\n", encoding="utf-8")
    print(summary)
    print("Films with supplemental notes:", sum(bool(f["assistant_notes"]) for f in films))


if __name__ == "__main__":
    main()
