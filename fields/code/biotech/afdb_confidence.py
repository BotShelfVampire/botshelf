#!/usr/bin/env python3
"""BSV recipe: how much of a predicted protein structure can you trust? (AlphaFold DB API, pLDDT bands)

Input : UniProt accession (default P00533 = human EGFR).
Output: afdb_<acc>.pdb (downloaded model) and afdb_<acc>_confidence.csv with per-residue pLDDT,
        plus a printed summary of the four AlphaFold DB confidence bands and the low-confidence stretches.
Original BSV code, MIT. Data: AlphaFold Protein Structure Database (DeepMind / EMBL-EBI, CC BY 4.0).
"""
import csv, json, sys, urllib.request

BANDS = [(90, "very high"), (70, "confident"), (50, "low"), (0, "very low")]   # AlphaFold DB's published bands

def band(v: float) -> str:
    return next(name for lo, name in BANDS if v >= lo)

def main(acc="P00533"):
    with urllib.request.urlopen(f"https://alphafold.ebi.ac.uk/api/prediction/{acc}", timeout=60) as r:
        meta = json.load(r)[0]
    pdb_url = meta["pdbUrl"]
    pdb = urllib.request.urlopen(pdb_url, timeout=120).read().decode()
    open(f"afdb_{acc}.pdb", "w").write(pdb)
    res = {}
    for line in pdb.splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":   # pLDDT is stored in the B-factor column
            res[int(line[22:26])] = (line[17:20], float(line[60:66]))
    with open(f"afdb_{acc}_confidence.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["residue", "aa", "plddt", "band"])
        for i, (aa, v) in sorted(res.items()):
            w.writerow([i, aa, v, band(v)])
    n = len(res)
    print(f"{acc} {meta.get('uniprotDescription', '')} model {meta.get('entryId')} ({n} residues), source {pdb_url}")
    for lo, name in BANDS:
        k = sum(1 for _, v in res.values() if band(v) == name)
        print(f"  {name:9s} {k:5d} residues ({100 * k / n:.1f}%)")
    low, start = [], None
    for i in sorted(res):
        if res[i][1] < 50 and start is None:
            start = i
        if (res[i][1] >= 50 or i == max(res)) and start is not None:
            end = i - 1 if res[i][1] >= 50 else i
            if end - start + 1 >= 10:
                low.append((start, end))
            start = None
    print("  stretches of >=10 residues below pLDDT 50:", ", ".join(f"{a}-{b}" for a, b in low) or "none")

if __name__ == "__main__":
    main(*sys.argv[1:])
