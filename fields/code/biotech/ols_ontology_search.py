#!/usr/bin/env python3
"""BSV recipe: EBI OLS4 search for an ontology term.

Research / education only.
Input : query (default apoptosis), ontology (default go), size (default 5).
Output: ols_terms.csv.
Original BSV code, MIT. Data: www.ebi.ac.uk/ols4.
"""
import csv, json, sys, urllib.parse, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (research-education; +https://botshelfvampire.com)"}

def main(query="apoptosis", ontology="go", size="5"):
    size = int(size)
    q = urllib.parse.urlencode({"q": query, "ontology": ontology, "rows": size})
    url = f"https://www.ebi.ac.uk/ols4/api/search?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.loads(r.read().decode())
    docs = ((d.get("response") or {}).get("docs")) or []
    rows = []
    for doc in docs:
        rows.append({"iri": doc.get("iri"), "short_form": doc.get("short_form"),
                     "label": doc.get("label"), "ontology_name": doc.get("ontology_name")})
    if not rows:
        raise SystemExit("no OLS hits")
    with open("ols_terms.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["short_form", "label", "ontology_name", "iri"]); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} OLS hits for {query!r} -> ols_terms.csv")

if __name__ == "__main__":
    main(*sys.argv[1:4])
