"""Validate canonical CSV data and generate the buildless public site dataset."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = {"待核对", "已核对", "有争议"}


def main():
    data = {}
    for key in ["films", "people", "companies", "relations", "sources", "review_queue"]:
        with (ROOT / "data" / f"{key}.csv").open(encoding="utf-8-sig", newline="") as handle:
            data[key] = list(csv.DictReader(handle))
        ids = [r["id"] for r in data[key]]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {key}"
        assert all(ids), f"Blank ID: {key}"
    films = {r["id"] for r in data["films"]}
    nodes = films | {r["id"] for r in data["people"] + data["companies"]}
    assert len(nodes) == sum(len(data[k]) for k in ["films", "people", "companies"]), "Cross-table ID collision"
    sources = {r["id"] for r in data["sources"]}
    for key in ["films", "relations", "review_queue"]:
        for row in data[key]:
            assert row["source_id"] in sources, f"Unknown source: {row['id']}"
            assert row["status"] in STATUS, f"Unknown status: {row['id']}"
            assert row["source_row"].isdigit(), f"Missing source row: {row['id']}"
    for row in data["relations"]:
        assert row["from_id"] in nodes and row["to_id"] in nodes, f"Broken relation: {row['id']}"
    for row in data["review_queue"]:
        assert row["film_id"] in films, f"Broken review item: {row['id']}"
    for row in data["people"] + data["companies"]:
        assert row["name"].strip() and row["status"] in STATUS
    (ROOT / "docs" / "data.js").write_text("window.FILM_DATA = " + json.dumps(data, ensure_ascii=False).replace("<", "\\u003c") + ";\n", encoding="utf-8")
    (ROOT / "docs" / "catalog.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Validated and built:", ", ".join(f"{k}={len(v)}" for k, v in data.items()))


if __name__ == "__main__":
    main()
