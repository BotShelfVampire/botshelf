#!/usr/bin/env python3
"""BSV recipe: download one World Bank indicator series for one country into CSV.

Input : country ISO2 (default JP), indicator id (default SP.POP.TOTL = population).
Output: wb_series.csv
Original BSV code, MIT. Data: World Bank Open Data API (CC BY 4.0 — cite World Bank).
"""
import csv, json, sys, urllib.parse, urllib.request

def main(country="JP", indicator="SP.POP.TOTL"):
    q = urllib.parse.urlencode({"format": "json", "per_page": "20000"})
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?{q}"
    with urllib.request.urlopen(url, timeout=45) as r:
        payload = json.load(r)
    meta, rows = payload[0], payload[1] or []
    keep = [x for x in rows if x.get("value") is not None]
    keep.sort(key=lambda x: str(x.get("date") or ""))
    with open("wb_series.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["country", "indicator", "year", "value"])
        for x in keep:
            w.writerow([country, indicator, x.get("date"), x.get("value")])
    print(f"{country} {indicator}: {len(keep)} yearly points -> wb_series.csv (source: World Bank Open Data)")
    if keep:
        print("latest:", keep[-1].get("date"), keep[-1].get("value"))

if __name__ == "__main__":
    main(*sys.argv[1:])
