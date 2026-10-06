#!/usr/bin/env python3
"""BSV recipe: toy circular-orbit ground-track samples (not real ephemeris).

Education / intuition only — Keplerian cartoon, not operational orbit determination.
Input : inclination_deg, period_min, samples (defaults 51.6 92.0 48).
Output: ground_track.csv with t_min, lat_deg, lon_deg.
Original BSV code, MIT. Dependency: math.
"""
import csv, math, sys

def main(inc="51.6", period="92.0", samples="48"):
    inc, period, n = math.radians(float(inc)), float(period), int(samples)
    rows = []
    for i in range(n):
        t = period * i / n
        # simplistic: arg of latitude progresses uniformly; node fixed at 0 for the cartoon
        u = 2 * math.pi * i / n
        lat = math.degrees(math.asin(math.sin(inc) * math.sin(u)))
        # longitude: Earth rotation neglected in this toy — only orbital phase
        lon = math.degrees(math.atan2(math.cos(inc) * math.sin(u), math.cos(u)))
        rows.append({"t_min": round(t, 4), "lat_deg": lat, "lon_deg": lon})
    with open("ground_track.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t_min", "lat_deg", "lon_deg"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} toy ground-track points period={period}min -> ground_track.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
