#!/usr/bin/env python3
"""BSV recipe: flatten USGS past-day M2.5+ earthquakes GeoJSON into a CSV.

Input : optional feed URL (default: USGS 2.5_day summary).
Output: quakes_day.csv with time_utc, mag, place, lon, lat, depth_km, url
Original BSV code, MIT. USGS data are public domain; BSV does not alter magnitudes.
"""
import csv, json, sys, urllib.request
from datetime import datetime, timezone

DEFAULT = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

def main(url=DEFAULT):
    with urllib.request.urlopen(url, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    feats = data.get("features") or []
    rows = []
    for f in feats:
        p = f.get("properties") or {}
        g = (f.get("geometry") or {}).get("coordinates") or [None, None, None]
        lon, lat, depth = (g + [None, None, None])[:3]
        ms = p.get("time")
        t = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ms else ""
        rows.append({"time_utc": t, "mag": p.get("mag"), "place": p.get("place"),
                     "lon": lon, "lat": lat, "depth_km": depth, "url": p.get("url")})
    rows.sort(key=lambda r: r["time_utc"] or "", reverse=True)
    with open("quakes_day.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time_utc", "mag", "place", "lon", "lat", "depth_km", "url"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} events from USGS feed -> quakes_day.csv (public domain USGS)")

if __name__ == "__main__":
    main(*sys.argv[1:2])
