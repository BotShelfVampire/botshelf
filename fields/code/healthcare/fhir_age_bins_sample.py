#!/usr/bin/env python3
"""BSV recipe: bin Patient birth years from a tiny embedded FHIR Bundle (no network).

Research / education only — synthetic data, not real PHI, not clinical.
Input : none.
Output: fhir_age_bins.csv with decade bucket counts.
Original BSV code, MIT. Dependency: none.
"""
import csv, json, sys
from datetime import date

BUNDLE = {
  "resourceType": "Bundle", "type": "collection",
  "entry": [
    {"resource": {"resourceType": "Patient", "id": "a", "birthDate": "1980-05-01"}},
    {"resource": {"resourceType": "Patient", "id": "b", "birthDate": "1992-11-12"}},
    {"resource": {"resourceType": "Patient", "id": "c", "birthDate": "1975-01-20"}},
    {"resource": {"resourceType": "Patient", "id": "d", "birthDate": "2001-07-04"}},
    {"resource": {"resourceType": "Patient", "id": "e", "birthDate": "1988-03-15"}},
    {"resource": {"resourceType": "Patient", "id": "f", "birthDate": "1969-09-09"}},
  ]
}

def main():
    today = date(2026, 10, 7)
    bins = {}
    for e in BUNDLE["entry"]:
        bd = e["resource"].get("birthDate")
        if not bd: continue
        y = int(bd[:4]); age = today.year - y
        bucket = f"{(age // 10) * 10}s"
        bins[bucket] = bins.get(bucket, 0) + 1
    rows = [{"age_decade": k, "count": v, "note": "synthetic FHIR only"} for k, v in sorted(bins.items())]
    with open("fhir_age_bins.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["age_decade", "count", "note"]); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} decade bins from synthetic Bundle -> fhir_age_bins.csv")

if __name__ == "__main__":
    main()
