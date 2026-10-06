#!/usr/bin/env python3
"""BSV recipe: fetch recent daily weather for a lat/lon from Open-Meteo (no API key).

Input : latitude, longitude (default Tokyo 35.68,139.76), past_days (default 7).
Output: weather_daily.csv
Original BSV code, MIT. Data: Open-Meteo (CC BY 4.0 — cite Open-Meteo). Not a forecast product claim.
"""
import csv, json, sys, urllib.parse, urllib.request

def main(lat="35.68", lon="139.76", past_days="7"):
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "past_days": past_days,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    })
    url = "https://api.open-meteo.com/v1/forecast?" + q
    with urllib.request.urlopen(url, timeout=45) as r:
        data = json.load(r)
    daily = data.get("daily") or {}
    days = daily.get("time") or []
    with open("weather_daily.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "temp_max_c", "temp_min_c", "precip_mm", "lat", "lon"])
        for i, d in enumerate(days):
            w.writerow([
                d,
                (daily.get("temperature_2m_max") or [None])[i],
                (daily.get("temperature_2m_min") or [None])[i],
                (daily.get("precipitation_sum") or [None])[i],
                lat, lon,
            ])
    print(f"{len(days)} daily rows for {lat},{lon} -> weather_daily.csv (source: Open-Meteo)")

if __name__ == "__main__":
    main(*sys.argv[1:])
