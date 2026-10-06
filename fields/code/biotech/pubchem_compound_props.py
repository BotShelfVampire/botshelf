#!/usr/bin/env python3
"""BSV recipe: pull basic PubChem compound properties for a common name.

Research / education cheminformatics only. Not efficacy, safety, or dosing advice.
Input : compound name (default aspirin).
Output: pubchem_<name>.csv and pubchem_<name>.md (CID, formula, MW, IUPAC).
Original BSV code, MIT. Data: NCBI PubChem PUG REST (public).
"""
import csv, json, re, sys, urllib.parse, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (research education; +https://botshelfvampire.com)"}

def main(name="aspirin"):
    name = (name or "aspirin").strip()
    q = urllib.parse.quote(name)
    url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/"
           "property/MolecularWeight,MolecularFormula,IUPACName,CanonicalSMILES/JSON")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    props = (data.get("PropertyTable") or {}).get("Properties") or []
    if not props:
        raise SystemExit(f"no PubChem properties for {name!r}")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:40]
    rows = []
    for p in props:
        rows.append({
            "query": name,
            "cid": p.get("CID"),
            "molecular_formula": p.get("MolecularFormula"),
            "molecular_weight": p.get("MolecularWeight"),
            "iupac_name": p.get("IUPACName"),
            "canonical_smiles": p.get("CanonicalSMILES"),
        })
    with open(f"pubchem_{safe}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    md = [f"# PubChem properties — {name}", "",
          "**Research/education only. Not clinical advice.**", "",
          f"Hits: {len(rows)}", ""]
    for r in rows:
        md += [f"## CID {r['cid']}", f"- formula: {r['molecular_formula']}",
               f"- MW: {r['molecular_weight']}", f"- IUPAC: {r['iupac_name']}", ""]
    md += ["Source: PubChem PUG REST — https://pubchem.ncbi.nlm.nih.gov/", ""]
    open(f"pubchem_{safe}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"wrote {len(rows)} PubChem row(s) -> pubchem_{safe}.csv + .md")

if __name__ == "__main__":
    main(*sys.argv[1:2])
