#!/usr/bin/env python3
"""BSV recipe: visible-pass table for a satellite over your location (CelesTrak GP data + Skyfield).

Input : NORAD catalog number (default 25544 = ISS), latitude, longitude, hours ahead.
Output: passes_<catnr>.csv with rise / culmination / set times (UTC), max elevation and whether the satellite is sunlit.
Original BSV code, MIT. Orbit data: CelesTrak GP (TLE format). Library: Skyfield (MIT).
"""
import csv, sys, urllib.request
from skyfield.api import EarthSatellite, load, wgs84

def main(catnr="25544", lat=35.6812, lon=139.7671, hours=24, min_el=10.0):
    url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=TLE"
    with urllib.request.urlopen(url, timeout=30) as r:
        name, l1, l2 = [x.strip() for x in r.read().decode().strip().splitlines()[:3]]
    ts = load.timescale()
    sat = EarthSatellite(l1, l2, name, ts)
    here = wgs84.latlon(float(lat), float(lon))
    t0 = ts.now(); t1 = ts.tt_jd(t0.tt + float(hours) / 24)
    age_days = t0 - sat.epoch
    times, events = sat.find_events(here, t0, t1, altitude_degrees=float(min_el))
    eph = None
    try:
        eph = load("de421.bsp")  # ~17 MB once; needed only for the sunlit flag
    except Exception as e:
        print("sunlit flag skipped:", e)
    rows, cur = [], {}
    for t, ev in zip(times, events):
        key = ("rise", "culminate", "set")[ev]
        cur[key] = t.utc_strftime("%Y-%m-%d %H:%M:%S")
        if ev == 1:
            alt, _, _ = (sat - here).at(t).altaz()
            cur["max_el_deg"] = round(alt.degrees, 1)
            cur["sunlit"] = bool(sat.at(t).is_sunlit(eph)) if eph else ""
        if ev == 2 and "rise" in cur:
            rows.append(cur); cur = {}
    with open(f"passes_{catnr}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rise", "culminate", "set", "max_el_deg", "sunlit"])
        w.writeheader(); w.writerows(rows)
    print(f"{name}: TLE age {age_days:.2f} d, {len(rows)} passes above {min_el} deg in {hours} h -> passes_{catnr}.csv")

if __name__ == "__main__":
    main(*sys.argv[1:])
