#!/usr/bin/env python3
"""BSV recipe: look up a human gene symbol via MyGene.info.

Research / education only. Summaries are public annotations — not diagnosis or care advice.
Input : gene symbol (default TP53), species (default human).
Output: mygene_<symbol>.json and mygene_<symbol>.md
Original BSV code, MIT. Data: MyGene.info (open gene annotation API).
"""
import json, re, sys, urllib.parse, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (research education; +https://botshelfvampire.com)"}

def main(symbol="TP53", species="human"):
    symbol = (symbol or "TP53").strip()
    species = (species or "human").strip()
    q = urllib.parse.urlencode({
        "q": f"symbol:{symbol}", "species": species,
        "fields": "symbol,name,entrezgene,summary,type_of_gene,taxid",
    })
    url = f"https://mygene.info/v3/query?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    hits = data.get("hits") or []
    if not hits:
        raise SystemExit(f"no MyGene hits for {symbol!r} ({species})")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", symbol)[:40]
    json.dump(data, open(f"mygene_{safe}.json", "w", encoding="utf-8"), indent=1)
    h0 = hits[0]
    summary = (h0.get("summary") or "")[:800]
    md = [f"# MyGene.info — {h0.get('symbol') or symbol}", "",
          "**Research/education only. Not clinical advice.**", "",
          f"- name: {h0.get('name')}",
          f"- entrezgene: {h0.get('entrezgene')}",
          f"- type: {h0.get('type_of_gene')}",
          f"- taxid: {h0.get('taxid')}",
          f"- hits returned: {len(hits)}", "",
          "## Summary (truncated from API)", summary or "(none)", "",
          f"Source: {url}", ""]
    open(f"mygene_{safe}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"wrote mygene_{safe}.md + .json ({len(hits)} hit(s)) for {symbol!r}")

if __name__ == "__main__":
    main(*sys.argv[1:3])
