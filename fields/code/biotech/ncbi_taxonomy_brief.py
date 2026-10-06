#!/usr/bin/env python3
"""BSV recipe: NCBI Datasets taxonomy summary for a taxon name.

Research / education only — model organisms / taxonomy literacy; no pathogen protocols.
Input : taxon (default Drosophila melanogaster).
Output: ncbi_taxonomy.md + ncbi_taxonomy.json.
Original BSV code, MIT. Data: api.ncbi.nlm.nih.gov/datasets/v2.
"""
import json, sys, urllib.parse, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (research-education; +https://botshelfvampire.com)"}

def main(taxon="Drosophila melanogaster"):
    taxon = (taxon or "Drosophila melanogaster").strip()
    # taxonomy suggest/name endpoint
    q = urllib.parse.quote(taxon)
    url = f"https://api.ncbi.nlm.nih.gov/datasets/v2/taxonomy/taxon/{q}"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode())
    except Exception:
        # fallback taxonomy report by name search
        url2 = f"https://api.ncbi.nlm.nih.gov/datasets/v2/taxonomy/taxon_suggest/{q}"
        req2 = urllib.request.Request(url2, headers=UA)
        with urllib.request.urlopen(req2, timeout=45) as r:
            d = json.loads(r.read().decode())
    with open("ncbi_taxonomy.json", "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    # normalize a few fields if present
    tax = d
    if isinstance(d, dict) and "taxonomy_nodes" in d:
        node = (d.get("taxonomy_nodes") or [{}])[0]
        tax = node.get("taxonomy") or node
    elif isinstance(d, dict) and "sci_name" in str(d):
        pass
    lines = ["# NCBI taxonomy brief", "", f"- query: {taxon}", f"- raw_keys: {', '.join(list(d)[:12]) if isinstance(d, dict) else type(d).__name__}", "",
             "_Research/education only. Not a biosafety manual._", ""]
    # try common fields
    for k in ("tax_id", "organism_name", "common_name", "rank", "species", "genus"):
        if isinstance(tax, dict) and tax.get(k) is not None:
            lines.insert(-3, f"- {k}: {tax.get(k)}")
    open("ncbi_taxonomy.md", "w", encoding="utf-8").write("\n".join(lines))
    print(f"NCBI taxonomy brief for {taxon!r} -> ncbi_taxonomy.md / .json")

if __name__ == "__main__":
    main(*sys.argv[1:2])
