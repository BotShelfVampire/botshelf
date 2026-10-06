#!/usr/bin/env python3
"""BSV recipe: sample ISS (or any NORAD id) ground-track points from a fresh CelesTrak TLE.

Civil / education visualization only. Not guidance, not conjunction assessment, not targeting.
Input : NORAD catalog number (default 25544 = ISS), hours (default 3), step minutes (default 5).
Output: track_<catnr>.csv with utc, lat_deg, lon_deg, alt_km
Original BSV code, MIT. Orbit data: CelesTrak GP. Library: Skyfield (MIT).
"""
import csv, sys, urllib.request
from skyfield.api import EarthSatellite, load, wgs84

UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}

def main(catnr="25544", hours="3", step_min="5"):
    catnr = str(catnr).strip() or "25544"
    hours = float(hours); step_min = float(step_min)
    url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=TLE"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        lines = [x.strip() for x in r.read().decode().strip().splitlines()[:3]]
    name, l1, l2 = lines
    ts = load.timescale()
    sat = EarthSatellite(l1, l2, name, ts)
    t0 = ts.now()
    n = max(1, int(hours * 60 / step_min) + 1)
    rows = []
    for i in range(n):
        t = ts.tt_jd(t0.tt + (i * step_min) / (60 * 24))
        geo = wgs84.geographic_position_of(sat.at(t))
        rows.append({
            "utc": t.utc_strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lat_deg": round(geo.latitude.degrees, 4),
            "lon_deg": round(geo.longitude.degrees, 4),
            "alt_km": round(geo.elevation.km, 2),
        })
    out = f"track_{catnr}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["utc", "lat_deg", "lon_deg", "alt_km"])
        w.writeheader(); w.writerows(rows)
    print(f"{name}: {len(rows)} samples over {hours} h step {step_min} min -> {out}")

if __name__ == "__main__":
    main(*sys.argv[1:4])
