#!/usr/bin/env python3
"""BSV recipe: flatten a JSON Lines file into a CSV of top-level keys.

Input : path to .jsonl (default: writes a labeled synthetic sample).
Output: flat.csv
Original BSV code, MIT. Nested objects become JSON strings; arrays become '|'-joined text.
"""
import csv, json, os, sys

SAMPLE = [
    {"id": 1, "tag": "example-row", "metrics": {"a": 1, "b": 2}, "labels": ["x", "y"]},
    {"id": 2, "tag": "example-row", "metrics": {"a": 3}, "labels": ["z"]},
    {"id": 3, "tag": "example-row", "metrics": {}, "labels": []},
]

def cell(v):
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    if isinstance(v, list):
        return "|".join(str(x) for x in v)
    return v

def main(path=None):
    if not path:
        path = "sample_labeled.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for row in SAMPLE:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("wrote labeled synthetic sample:", path)
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open("flat.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: cell(r.get(k)) for k in keys})
    print(f"flattened {len(rows)} lines → flat.csv ({len(keys)} columns)")

if __name__ == "__main__":
    main(*sys.argv[1:])
