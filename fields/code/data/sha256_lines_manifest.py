#!/usr/bin/env python3
"""BSV recipe: SHA-256 each non-empty line of stdin text embedded as practice lines.

Practice integrity hygiene only.
Input : none (uses embedded lines); optional label (default practice).
Output: sha256_manifest.csv.
Original BSV code, MIT. Dependency: hashlib.
"""
import csv, hashlib, sys

LINES = [
    "alpha-practice-row",
    "beta-practice-row",
    "gamma-practice-row",
]

def main(label="practice"):
    rows = []
    for i, line in enumerate(LINES):
        h = hashlib.sha256(line.encode()).hexdigest()
        rows.append({"label": label, "index": i, "sha256": h, "nbytes": len(line.encode())})
    with open("sha256_manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["label", "index", "sha256", "nbytes"]); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} line digests -> sha256_manifest.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
