#!/usr/bin/env python3
"""BSV recipe: drug-likeness screen of active compounds for one target (ChEMBL API + RDKit).

Input : ChEMBL target id (default CHEMBL203 = EGFR), minimum pChEMBL value (default 7), max compounds.
Output: screen_<target>.csv with MW, cLogP, HBD, HBA, TPSA, rotatable bonds, QED and a Lipinski rule-of-five flag.
Original BSV code, MIT. Data: ChEMBL (EMBL-EBI, CC BY-SA 3.0). Library: RDKit (BSD-3-Clause).
This is a filtering exercise, not a prediction of efficacy or safety.
"""
import csv, json, sys, time, urllib.error, urllib.parse, urllib.request
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski, QED, rdMolDescriptors

def get_json(url: str, tries: int = 4) -> dict:
    for i in range(tries):   # the public ChEMBL API is sometimes slow or returns 5xx; back off and retry
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if i == tries - 1 or (isinstance(e, urllib.error.HTTPError) and e.code < 500):
                raise
            time.sleep(5 * (i + 1))

def fetch(target: str, min_p: float, limit: int) -> dict:
    q = urllib.parse.urlencode({"target_chembl_id": target, "pchembl_value__gte": min_p, "limit": 100,
                                "only": "molecule_chembl_id,canonical_smiles,pchembl_value,standard_type"})
    url = f"https://www.ebi.ac.uk/chembl/api/data/activity.json?{q}"
    best = {}
    while url and len(best) < limit:
        page = get_json(url)
        for a in page["activities"]:
            mid, smi = a["molecule_chembl_id"], a["canonical_smiles"]
            if smi and (mid not in best or float(a["pchembl_value"]) > best[mid][1]):
                best[mid] = (smi, float(a["pchembl_value"]), a["standard_type"])
        nxt = page["page_meta"]["next"]
        url = f"https://www.ebi.ac.uk{nxt}" if nxt else None
    return dict(list(best.items())[:limit])

def profile(smi: str) -> dict | None:
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    p = {"mw": Descriptors.MolWt(m), "clogp": Crippen.MolLogP(m), "hbd": Lipinski.NumHDonors(m),
         "hba": Lipinski.NumHAcceptors(m), "tpsa": rdMolDescriptors.CalcTPSA(m),
         "rot_bonds": Lipinski.NumRotatableBonds(m), "qed": QED.qed(m)}
    violations = sum([p["mw"] > 500, p["clogp"] > 5, p["hbd"] > 5, p["hba"] > 10])
    p["ro5_violations"] = violations
    p["ro5_pass"] = violations <= 1   # Lipinski: poor absorption more likely with 2+ violations
    return p

def main(target="CHEMBL203", min_p="7", limit="100"):
    mols = fetch(target, float(min_p), int(limit))
    rows = []
    for mid, (smi, pval, stype) in mols.items():
        p = profile(smi)
        if p:
            rows.append({"molecule": mid, "pchembl": pval, "type": stype, **{k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()}, "smiles": smi})
    rows.sort(key=lambda r: (-r["ro5_pass"], -r["qed"]))
    with open(f"screen_{target}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    passed = sum(r["ro5_pass"] for r in rows)
    print(f"{target}: {len(rows)} compounds profiled, {passed} pass rule-of-five (<=1 violation) -> screen_{target}.csv")
    print("top by QED:", rows[0]["molecule"], rows[0]["qed"])

if __name__ == "__main__":
    main(*sys.argv[1:])
