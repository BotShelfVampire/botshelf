#!/usr/bin/env python3
"""BSV recipe: profile a CSV — column types, nulls, distinct counts, sample values.

Input : path to a CSV (default: writes and profiles a labeled synthetic sample).
Output: profile.csv + profile.md in the working directory.
Original BSV code, MIT. Synthetic sample rows are labeled examples, not customer or production data.
"""
import csv, os, sys
from collections import Counter

SAMPLE = """id,city,temp_c,note
1,Tokyo,22.1,example-row
2,Osaka,,example-row
3,Tokyo,19.4,example-row
4,Nagoya,21.0,example-row
5,Osaka,18.7,example-row
"""

def is_float(s):
    try:
        float(s); return True
    except Exception:
        return False

def main(path=None):
    if not path:
        path = "sample_labeled.csv"
        open(path, "w", encoding="utf-8").write(SAMPLE)
        print("wrote labeled synthetic sample:", path)
    rows = list(csv.DictReader(open(path, encoding="utf-8", newline="")))
    if not rows:
        raise SystemExit("empty csv")
    cols = list(rows[0].keys())
    out_rows = []
    lines = [f"# CSV profile for `{path}`", "", f"Rows: {len(rows)}  Columns: {len(cols)}", "",
             "Synthetic or practice files should stay labeled as such; do not treat sample numbers as live metrics.", ""]
    for c in cols:
        vals = [r.get(c, "") for r in rows]
        empty = sum(1 for v in vals if v is None or str(v).strip() == "")
        filled = [str(v).strip() for v in vals if v is not None and str(v).strip() != ""]
        numeric = all(is_float(v) for v in filled) if filled else False
        distinct = len(set(filled))
        top = Counter(filled).most_common(3)
        samples = ", ".join(repr(v) for v, _ in top) if top else ""
        out_rows.append({"column": c, "non_null": len(filled), "nulls": empty,
                         "distinct": distinct, "numeric": str(numeric).lower(), "top_values": samples})
        lines.append(f"## {c}")
        lines.append(f"- non-null: {len(filled)} / nulls: {empty} / distinct: {distinct} / numeric: {numeric}")
        lines.append(f"- top: {samples}")
        lines.append("")
    with open("profile.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["column", "non_null", "nulls", "distinct", "numeric", "top_values"])
        w.writeheader(); w.writerows(out_rows)
    open("profile.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"profiled {len(rows)} rows × {len(cols)} cols -> profile.csv, profile.md")

if __name__ == "__main__":
    main(*sys.argv[1:])
