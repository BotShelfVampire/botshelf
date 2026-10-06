#!/usr/bin/env python3
"""BSV recipe: one-page physico-chemical profile of a protein (UniProt REST + Biopython ProtParam).

Input : UniProt accession (default P69905 = human haemoglobin subunit alpha).
Output: profile_<acc>.md with length, molecular weight, theoretical pI, GRAVY, instability index and aromaticity.
Original BSV code, MIT. Data: UniProt (CC BY 4.0). Library: Biopython.
Values are sequence-based calculations, not lab measurements.
"""
import sys, urllib.request
from Bio.SeqUtils.ProtParam import ProteinAnalysis

def main(acc="P69905"):
    fasta = urllib.request.urlopen(f"https://rest.uniprot.org/uniprotkb/{acc}.fasta", timeout=60).read().decode()
    header, *seq = fasta.strip().splitlines()
    s = "".join(seq)
    pa = ProteinAnalysis(s)
    ii = pa.instability_index()
    lines = [f"# {header[1:]}", "", f"- Length: {len(s)} aa", f"- Molecular weight: {pa.molecular_weight():,.1f} Da",
             f"- Theoretical pI: {pa.isoelectric_point():.2f}", f"- GRAVY (hydropathy): {pa.gravy():.3f}",
             f"- Instability index: {ii:.1f} ({'predicted unstable (>40)' if ii > 40 else 'predicted stable (<=40)'})",
             f"- Aromaticity: {pa.aromaticity():.3f}", "",
             "Computed from sequence with Biopython ProtParam (Expasy ProtParam methods). Source: rest.uniprot.org."]
    open(f"profile_{acc}.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:9]))

if __name__ == "__main__":
    main(*sys.argv[1:])
