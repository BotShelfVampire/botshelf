#!/usr/bin/env python3
"""BSV recipe: Ensembl REST lookup for a gene symbol (human).

Research / education only — not clinical genetics.
Input : symbol (default BRCA2).
Output: ensembl_gene.md + ensembl_gene.json.
Original BSV code, MIT. Data: rest.ensembl.org.
"""
import json, sys, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (research-education; +https://botshelfvampire.com)", "Content-Type": "application/json"}

def main(symbol="BRCA2"):
    symbol = (symbol or "BRCA2").strip()
    url = f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}?content-type=application/json"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.loads(r.read().decode())
    with open("ensembl_gene.json", "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    lines = [f"# Ensembl lookup: {symbol}", "",
             f"- id: {d.get('id')}", f"- display_name: {d.get('display_name')}",
             f"- biotype: {d.get('biotype')}", f"- species: {d.get('species')}",
             f"- description: {d.get('description')}", "",
             "_Research/education only. Not clinical advice._", ""]
    open("ensembl_gene.md", "w", encoding="utf-8").write("\n".join(lines))
    print(f"Ensembl {symbol} id={d.get('id')} -> ensembl_gene.md / .json")

if __name__ == "__main__":
    main(*sys.argv[1:2])
