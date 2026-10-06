#!/usr/bin/env python3
"""BSV recipe: weekly literature digest from PubMed (NCBI E-utilities).

Input : a PubMed query (default: AlphaFold protein structure), days back (default 7), max papers (default 20).
        Set NCBI_EMAIL (and optionally NCBI_API_KEY) as NCBI asks.
Output: digest_<date>.md (title, journal, date, PMID link) ready to hand to a summarising AI agent.
Original BSV code, MIT. Data: NCBI PubMed via E-utilities.
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def get(path: str, **params) -> dict:
    params.update({"retmode": "json", "tool": "bsv-recipe", "email": os.environ.get("NCBI_EMAIL", "")})
    if os.environ.get("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    with urllib.request.urlopen(BASE + path + "?" + urllib.parse.urlencode(params), timeout=60) as r:
        return json.load(r)

def main(query="AlphaFold protein structure", days="7", n="20"):
    ids = get("esearch.fcgi", db="pubmed", term=query, reldate=days, datetype="pdat", retmax=n, sort="pub_date")["esearchresult"]["idlist"]
    today = dt.date.today().isoformat()
    out = [f"# PubMed digest: {query}", "", f"Last {days} days, {len(ids)} papers (newest first). Generated {today}.", ""]
    if ids:
        summ = get("esummary.fcgi", db="pubmed", id=",".join(ids))["result"]
        for pmid in ids:
            s = summ[pmid]
            out.append(f"- **{s['title']}** — {s.get('fulljournalname', s.get('source', ''))}, {s.get('pubdate', '')}. "
                       f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
    out += ["", "Read the abstracts yourself before relying on any AI summary of this list."]
    open(f"digest_{today}.md", "w").write("\n".join(out) + "\n")
    print(f"{len(ids)} papers -> digest_{today}.md")

if __name__ == "__main__":
    main(*sys.argv[1:])
