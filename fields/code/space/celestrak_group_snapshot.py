#!/usr/bin/env python3
"""BSV recipe: snapshot a CelesTrak GP group (default: stations) into a CSV.

Civil / education orbit-data handling only. Not an operational SSA product and not for targeting.
Input : CelesTrak GROUP name (default stations).
Output: celestrak_<group>.csv with name, NORAD id, epoch, mean motion, inclination, eccentricity.
Original BSV code, MIT. Data: CelesTrak GP (see CelesTrak terms of use).
"""
import csv, json, sys, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}

def main(group="stations"):
    group = (group or "stations").strip().lower()
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=json"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit(f"empty or unexpected CelesTrak response for group={group!r}")
    rows = []
    for o in data:
        rows.append({
            "object_name": o.get("OBJECT_NAME"),
            "norad_cat_id": o.get("NORAD_CAT_ID"),
            "epoch": o.get("EPOCH"),
            "mean_motion": o.get("MEAN_MOTION"),
            "eccentricity": o.get("ECCENTRICITY"),
            "inclination_deg": o.get("INCLINATION"),
            "raan_deg": o.get("RA_OF_ASC_NODE"),
        })
    out = f"celestrak_{group}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} objects from CelesTrak group={group!r} -> {out}")

if __name__ == "__main__":
    main(*sys.argv[1:2])
