#!/usr/bin/env python3
"""BSV recipe: snapshot the ISS lat/lon from Open Notify.

Civil / education only — not SSA or targeting.
Input : none (live HTTP).
Output: iss_now.csv with timestamp, latitude, longitude, message.
Original BSV code, MIT. Data: api.open-notify.org.
"""
import csv, json, sys, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}

def main():
    req = urllib.request.Request("http://api.open-notify.org/iss-now.json", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    pos = d.get("iss_position") or {}
    row = {"timestamp": d.get("timestamp"), "latitude": pos.get("latitude"),
           "longitude": pos.get("longitude"), "message": d.get("message")}
    with open("iss_now.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys())); w.writeheader(); w.writerow(row)
    print(f"ISS now lat={row['latitude']} lon={row['longitude']} -> iss_now.csv")

if __name__ == "__main__":
    main()
