#!/usr/bin/env python3
"""BSV recipe: public holidays for a country/year (Nager.Date).

Practice / education only.
Input : country ISO (default JP), year (default 2026).
Output: public_holidays.csv.
Original BSV code, MIT. Data: date.nager.at.
"""
import csv, json, sys, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}

def main(country="JP", year="2026"):
    country, year = country.strip().upper(), int(year)
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    if not isinstance(data, list) or not data:
        raise SystemExit("empty holiday list")
    rows = [{"date": x.get("date"), "localName": x.get("localName"), "name": x.get("name"),
             "countryCode": x.get("countryCode"), "global": x.get("global")} for x in data]
    with open("public_holidays.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "localName", "name", "countryCode", "global"]); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} holidays {country} {year} -> public_holidays.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
