#!/usr/bin/env python3
"""BSV recipe: sunrise/sunset times for a lat/lon/date (sunrise-sunset.org).

Civil / education only.
Input : lat, lon, date YYYY-MM-DD (defaults 35.68 139.76 today UTC date).
Output: sunrise_sunset.csv.
Original BSV code, MIT. Data: api.sunrise-sunset.org (UTC times).
"""
import csv, datetime as dt, json, sys, urllib.parse, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}

def main(lat="35.68", lon="139.76", date=""):
    lat, lon = float(lat), float(lon)
    if not date:
        date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    q = urllib.parse.urlencode({"lat": lat, "lng": lon, "date": date, "formatted": 0})
    url = f"https://api.sunrise-sunset.org/json?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    if d.get("status") != "OK":
        raise SystemExit(f"API status={d.get('status')!r}")
    res = d["results"]
    row = {"date": date, "lat": lat, "lon": lon, "sunrise_utc": res.get("sunrise"),
           "sunset_utc": res.get("sunset"), "day_length_s": res.get("day_length"),
           "solar_noon_utc": res.get("solar_noon")}
    with open("sunrise_sunset.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys())); w.writeheader(); w.writerow(row)
    print(f"{date} lat={lat} lon={lon} sunrise={row['sunrise_utc']} -> sunrise_sunset.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
