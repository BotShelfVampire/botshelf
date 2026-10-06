#!/usr/bin/env python3
"""BSV recipe: value_counts for one column of an embedded practice CSV.

Practice data hygiene only — browser Field Lab CSV profile is the interactive twin.
Input : column name (default city).
Output: value_counts.csv.
Original BSV code, MIT. Dependency: none.
"""
import csv, io, sys

SAMPLE = """id,city,temp_c
1,Tokyo,22.1
2,Osaka,18.7
3,Tokyo,19.4
4,Nagoya,21.0
5,Osaka,18.7
6,Tokyo,20.2
"""

def main(column="city"):
    rows = list(csv.DictReader(io.StringIO(SAMPLE)))
    if column not in rows[0]:
        raise SystemExit(f"column {column!r} missing")
    counts = {}
    for r in rows:
        v = r[column]
        counts[v] = counts.get(v, 0) + 1
    out = [{"value": k, "count": v, "column": column} for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
    with open("value_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["column", "value", "count"]); w.writeheader(); w.writerows(out)
    print(f"wrote {len(out)} distinct values for {column!r} -> value_counts.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
