#!/usr/bin/env python3
"""BSV recipe: fetch a PDBe entry summary for one PDB id.

Research / education structural biology only. Experimental metadata as published — not a drug design claim.
Input : PDB id (default 1cbs = cellular retinoic acid-binding protein).
Output: pdbe_<id>.json and pdbe_<id>.md
Original BSV code, MIT. Data: PDBe / EMBL-EBI (PDB archive).
"""
import json, re, sys, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (research education; +https://botshelfvampire.com)"}

def main(pdb_id="1cbs"):
    pdb_id = (pdb_id or "1cbs").strip().lower()
    url = f"https://www.ebi.ac.uk/pdbe/api/pdb/entry/summary/{pdb_id}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    entries = data.get(pdb_id) or []
    if not entries:
        raise SystemExit(f"no PDBe summary for {pdb_id!r}")
    e0 = entries[0]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", pdb_id)[:40]
    json.dump(data, open(f"pdbe_{safe}.json", "w", encoding="utf-8"), indent=1)
    title = e0.get("title") or ""
    md = [f"# PDBe summary — {pdb_id}", "",
          "**Research/education only.**", "",
          f"- title: {title}",
          f"- experimental method: {e0.get('experimental_method')}",
          f"- resolution_summary: {e0.get('resolution')}",
          f"- entry authors: {', '.join(e0.get('entry_authors') or [])[:200]}",
          f"- deposition date: {e0.get('deposition_date')}",
          f"- release date: {e0.get('release_date')}", "",
          f"Source: {url}",
          f"RCSB mirror: https://www.rcsb.org/structure/{pdb_id.upper()}", ""]
    open(f"pdbe_{safe}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"wrote pdbe_{safe}.md + .json for {pdb_id!r}")

if __name__ == "__main__":
    main(*sys.argv[1:2])
