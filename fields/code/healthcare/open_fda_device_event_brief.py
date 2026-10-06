#!/usr/bin/env python3
"""BSV recipe: brief openFDA device adverse-event counts for a device generic name.

Research / education only — not pharmacovigilance, not clinical advice.
Input : generic_name query (default endoscope), limit (default 5).
Output: openfda_device_events.csv with report counts sample.
Original BSV code, MIT. Data: api.fda.gov (openFDA terms).
"""
import csv, json, sys, urllib.parse, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (research-education; +https://botshelfvampire.com)"}

def main(name="endoscope", limit="5"):
    limit = int(limit)
    q = urllib.parse.quote(f'device.generic_name:"{name}"')
    url = f"https://api.fda.gov/device/event.json?search={q}&limit={limit}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.loads(r.read().decode())
    rows = []
    for ev in d.get("results") or []:
        device = (ev.get("device") or [{}])[0]
        rows.append({
            "report_number": ev.get("report_number"),
            "date_received": ev.get("date_received"),
            "generic_name": device.get("generic_name"),
            "brand_name": device.get("brand_name"),
            "event_type": ev.get("event_type"),
        })
    if not rows:
        raise SystemExit("no results — try another generic_name")
    with open("openfda_device_events.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    meta = d.get("meta", {}).get("results", {})
    print(f"wrote {len(rows)} sample rows (openFDA total≈{meta.get('total','?')}) -> openfda_device_events.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
