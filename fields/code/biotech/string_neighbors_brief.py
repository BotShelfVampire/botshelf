#!/usr/bin/env python3
"""BSV recipe: list a few STRING DB interaction neighbors for one protein symbol.

Research / education network literacy only. Scores are computational evidence aggregates —
not wet-lab proof and not pathogen or dual-use guidance. Default is human TP53.

Input : protein identifier (default TP53), species NCBI taxid (default 9606), limit (default 8).
Output: string_neighbors.csv
Original BSV code, MIT. Data: STRING Consortium (CC BY 4.0).
"""
import csv, json, sys, urllib.parse, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (research education; +https://botshelfvampire.com)"}

def main(ident="TP53", species="9606", limit="8"):
    ident = (ident or "TP53").strip()
    species = str(species or "9606").strip()
    limit = max(1, min(20, int(limit)))
    q = urllib.parse.urlencode({"identifiers": ident, "species": species, "limit": limit})
    url = f"https://string-db.org/api/json/network?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"unexpected STRING response for {ident!r}")
    rows = []
    for e in data:
        rows.append({
            "preferredName_A": e.get("preferredName_A"),
            "preferredName_B": e.get("preferredName_B"),
            "score": e.get("score"),
            "nscore": e.get("nscore"),
            "fscore": e.get("fscore"),
            "pscore": e.get("pscore"),
            "ascore": e.get("ascore"),
            "escore": e.get("escore"),
            "dscore": e.get("dscore"),
            "tscore": e.get("tscore"),
        })
    with open("string_neighbors.csv", "w", newline="", encoding="utf-8") as f:
        fields = list(rows[0].keys()) if rows else [
            "preferredName_A", "preferredName_B", "score", "nscore", "fscore",
            "pscore", "ascore", "escore", "dscore", "tscore"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} STRING edges for {ident!r} (taxid {species}) -> string_neighbors.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
