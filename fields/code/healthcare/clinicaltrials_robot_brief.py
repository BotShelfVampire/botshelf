#!/usr/bin/env python3
"""BSV recipe: list a few ClinicalTrials.gov studies matching a research query (default: surgical robot).

Research / education discovery only. Not recruitment, not enrollment advice, not a complete registry dump.
Titles and NCT IDs come from ClinicalTrials.gov API v2 as published.

Input : query string (default "surgical robot") and page size (default 5, max 10).
Output: trials_brief.csv
Original BSV code, MIT.
"""
import csv, json, sys, urllib.parse, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (research education; +https://botshelfvampire.com)"}

def main(term="surgical robot", page_size="5"):
    term = term.strip() or "surgical robot"
    n = max(1, min(10, int(page_size)))
    q = urllib.parse.urlencode({"query.term": term, "pageSize": n, "format": "json"})
    url = f"https://clinicaltrials.gov/api/v2/studies?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    rows = []
    for st in data.get("studies") or []:
        proto = st.get("protocolSection") or {}
        ident = proto.get("identificationModule") or {}
        status = (proto.get("statusModule") or {})
        design = (proto.get("designModule") or {})
        rows.append({
            "nct_id": ident.get("nctId"),
            "brief_title": ident.get("briefTitle"),
            "overall_status": status.get("overallStatus"),
            "study_type": design.get("studyType"),
            "url": f"https://clinicaltrials.gov/study/{ident.get('nctId')}" if ident.get("nctId") else "",
        })
    with open("trials_brief.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nct_id", "brief_title", "overall_status", "study_type", "url"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} trials for term={term!r} -> trials_brief.csv (ClinicalTrials.gov API v2)")

if __name__ == "__main__":
    main(*sys.argv[1:3])
