#!/usr/bin/env python3
"""BSV recipe: Reactome content service — pathways for a gene symbol.

Research / education only — not a treatment pathway.
Input : gene symbol (default TP53).
Output: reactome_pathways.csv.
Original BSV code, MIT. Data: reactome.org ContentService.
"""
import csv, json, sys, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (research-education; +https://botshelfvampire.com)"}

def main(symbol="TP53"):
    symbol = (symbol or "TP53").strip()
    url = f"https://reactome.org/ContentService/data/pathways/top/homo%20sapiens/{symbol}"
    # Actually endpoint: /data/pathways/top/{species}/{gene} may vary — use query by name
    url = f"https://reactome.org/ContentService/search/query?query={symbol}&species=Homo%20sapiens&types=Pathway&cluster=true"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.loads(r.read().decode())
    rows = []
    for group in d.get("results") or []:
        for entry in group.get("entries") or []:
            rows.append({"stId": entry.get("stId"), "name": entry.get("name"),
                         "exactType": entry.get("exactType")})
            if len(rows) >= 12:
                break
        if len(rows) >= 12:
            break
    if not rows:
        raise SystemExit("no Reactome pathway hits")
    with open("reactome_pathways.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["stId", "name", "exactType"]); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} Reactome hits for {symbol!r} -> reactome_pathways.csv")

if __name__ == "__main__":
    main(*sys.argv[1:2])
