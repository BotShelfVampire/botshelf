#!/usr/bin/env python3
"""BSV recipe: snapshot recent GOES X-ray flux from NOAA SWPC into a CSV.

Education / space-weather literacy only. Not a flare-warning service and not medical advice about radiation.
Input : optional feed URL (default: NOAA GOES primary xrays-6-hour JSON).
Output: xray_flux.csv with time_tag, energy_band, flux
Original BSV code, MIT. Data: NOAA SWPC (US Government public domain).
"""
import csv, json, sys, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}
DEFAULT = "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"

def main(url=DEFAULT):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not isinstance(data, list):
        raise SystemExit("unexpected NOAA xray JSON shape")
    rows = []
    for o in data:
        rows.append({
            "time_tag": o.get("time_tag"),
            "energy": o.get("energy"),
            "flux": o.get("flux"),
            "satellite": o.get("satellite"),
        })
    with open("xray_flux.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time_tag", "energy", "flux", "satellite"])
        w.writeheader(); w.writerows(rows)
    latest = rows[-1]["time_tag"] if rows else "(none)"
    print(f"wrote {len(rows)} X-ray samples (latest {latest}) -> xray_flux.csv (NOAA SWPC)")

if __name__ == "__main__":
    main(*sys.argv[1:2])
