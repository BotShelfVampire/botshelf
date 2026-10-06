#!/usr/bin/env python3
"""BSV recipe: pull one OpenFDA drug label result into a short markdown + CSV index.

Research / education only. OpenFDA is not a complete archive and is not medical advice.
Do not use this output for prescribing, diagnosis, or treatment decisions.

Input : brand or generic name query (default: aspirin) and limit (default 1, max 5).
Output: openfda_label_<query>.md and openfda_index.csv
Original BSV code, MIT. Source: open.fda.gov (public domain / CC0 attribution as published).
"""
import csv, json, sys, urllib.parse, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (research education; +https://botshelfvampire.com)"}

def main(name="aspirin", limit="1"):
    name = name.strip() or "aspirin"
    limit = max(1, min(5, int(limit)))
    # Prefer brand_name match; fall back to bare term if needed.
    search = urllib.parse.quote(f"openfda.brand_name:{name}")
    url = f"https://api.fda.gov/drug/label.json?search={search}&limit={limit}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    results = data.get("results") or []
    if not results:
        raise SystemExit(f"no OpenFDA label results for {name!r}")
    rows = []
    for i, res in enumerate(results):
        of = res.get("openfda") or {}
        brand = ",".join(of.get("brand_name") or []) or name
        generic = ",".join(of.get("generic_name") or [])
        mfr = ",".join(of.get("manufacturer_name") or [])
        purpose = " ".join(res.get("purpose") or res.get("indications_and_usage") or [])[:400]
        warnings = " ".join(res.get("warnings") or [])[:400]
        md = [f"# OpenFDA label pull — {brand}", "",
              f"Query: `{name}`  Result: {i+1}/{len(results)}", "",
              "**Research/education only. Not clinical advice.**", "",
              f"- generic: {generic}", f"- manufacturer: {mfr}",
              f"- product_ndc: {','.join(of.get('product_ndc') or [])}", "",
              "## Purpose / indications (truncated from API)", purpose or "(none in this record)", "",
              "## Warnings (truncated)", warnings or "(none in this record)", "",
              "Source: https://open.fda.gov/ — keep attribution if you republish.", ""]
        out = f"openfda_label_{name.replace(' ','_')}_{i+1}.md"
        open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
        rows.append({"query": name, "brand": brand, "generic": generic, "manufacturer": mfr, "md_file": out})
    with open("openfda_index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["query", "brand", "generic", "manufacturer", "md_file"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} OpenFDA label md file(s) + openfda_index.csv for query={name!r}")

if __name__ == "__main__":
    main(*sys.argv[1:3])
