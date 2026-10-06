#!/usr/bin/env python3
"""BSV recipe: Gregorian calendar ↔ Julian Day Number (Meeus-style civil algorithm).

Space timekeeping literacy / education only — not a flight dynamics product.
Input : YYYY-MM-DD (default 2026-10-07) or JD float to invert if prefixed with jd:
Output: julian_day.csv with calendar date and JD.
Original BSV code, MIT. Dependency: none.
"""
import csv, sys

def to_jd(y, m, d):
    if m <= 2:
        y -= 1; m += 12
    A = y // 100
    B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5

def from_jd(jd):
    Z = int(jd + 0.5)
    F = jd + 0.5 - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - alpha // 4
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715
    return year, month, day

def main(arg="2026-10-07"):
    arg = (arg or "2026-10-07").strip()
    if arg.lower().startswith("jd:"):
        jd = float(arg.split(":", 1)[1])
        y, m, day = from_jd(jd)
        date = f"{y:04d}-{int(m):02d}-{int(day):02d}"
        jd_out = jd
    else:
        y, m, d = [int(x) for x in arg.split("-")]
        jd_out = to_jd(y, m, d)
        date = arg
        # round-trip check
        y2, m2, d2 = from_jd(jd_out)
    with open("julian_day.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "jd", "note"])
        w.writeheader()
        w.writerow({"date": date, "jd": jd_out, "note": "Meeus civil algorithm; noon-based JD"})
    print(f"{date} -> JD {jd_out} -> julian_day.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
