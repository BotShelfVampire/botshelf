#!/usr/bin/env python3
"""BSV recipe: geomagnetic storm watch log from NOAA SWPC's planetary K-index feed.

Input : threshold Kp (default 5 = NOAA G1 'minor storm' level on the NOAA space weather scales).
Output: appends new 3-hour readings to kp_log.csv and prints any reading at or above the threshold.
Original BSV code, MIT. Data: NOAA Space Weather Prediction Center (public domain, US Government).
"""
import csv, json, os, sys, urllib.request

URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

def main(threshold="5"):
    with urllib.request.urlopen(URL, timeout=30) as r:
        data = json.load(r)
    if data and isinstance(data[0], list):   # older table form: header row + rows
        hdr, rows = data[0], data[1:]
        rows = [dict(zip(hdr, x)) for x in rows]
    else:
        rows = data
    seen = set()
    if os.path.exists("kp_log.csv"):
        seen = {r["time_tag"] for r in csv.DictReader(open("kp_log.csv"))}
    new = [r for r in rows if r["time_tag"] not in seen]
    write_header = not os.path.exists("kp_log.csv")
    with open("kp_log.csv", "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["time_tag", "kp"])
        for r in new:
            w.writerow([r["time_tag"], r.get("Kp", r.get("kp_index"))])
    hits = [r for r in rows if float(r.get("Kp", r.get("kp_index", 0))) >= float(threshold)]
    print(f"{len(rows)} readings in feed, {len(new)} new logged; latest {rows[-1]['time_tag']} Kp={rows[-1].get('Kp', rows[-1].get('kp_index'))}")
    for r in hits:
        print("AT/ABOVE THRESHOLD:", r["time_tag"], r.get("Kp", r.get("kp_index")))

if __name__ == "__main__":
    main(*sys.argv[1:])
