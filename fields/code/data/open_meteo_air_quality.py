#!/usr/bin/env python3
"""BSV recipe: Open-Meteo air-quality hourly sample for a lat/lon.

Practice / education only — not an official AQI product.
Input : lat lon (defaults 35.68 139.76), hours (default 24).
Output: air_quality.csv.
Original BSV code, MIT. Data: air-quality-api.open-meteo.com.
"""
import csv, json, sys, urllib.parse, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}

def main(lat="35.68", lon="139.76", hours="24"):
    lat, lon, hours = float(lat), float(lon), int(hours)
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "hourly": "pm10,pm2_5,european_aqi",
        "forecast_days": 1,
    })
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.loads(r.read().decode())
    h = d.get("hourly") or {}
    times = h.get("time") or []
    rows = []
    for i, t in enumerate(times[:hours]):
        rows.append({"time": t, "pm10": (h.get("pm10") or [None])[i],
                     "pm2_5": (h.get("pm2_5") or [None])[i],
                     "european_aqi": (h.get("european_aqi") or [None])[i]})
    with open("air_quality.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time", "pm10", "pm2_5", "european_aqi"]); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} hourly AQ rows -> air_quality.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
