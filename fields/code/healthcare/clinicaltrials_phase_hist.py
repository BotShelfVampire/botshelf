#!/usr/bin/env python3
"""BSV recipe: histogram ClinicalTrials.gov phases for a query (robot OR surgical).

Research / education only — not a clinical recommendation.
Input : query expression (default AREA[ConditionSearch]robotics), pageSize (default 50).
Output: trials_phase_hist.csv.
Original BSV code, MIT. Data: clinicaltrials.gov API v2.
"""
import csv, json, sys, urllib.parse, urllib.request
UA = {"User-Agent": "BSV-fields-recipe/1.0 (research-education; +https://botshelfvampire.com)"}

def main(query="AREA[ConditionSearch]robotics", page_size="50"):
    page_size = int(page_size)
    q = urllib.parse.urlencode({"query.term": query, "pageSize": page_size, "format": "json"})
    url = f"https://clinicaltrials.gov/api/v2/studies?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    hist = {}
    for st in d.get("studies") or []:
        phases = (((st.get("protocolSection") or {}).get("designModule") or {}).get("phases")) or ["NA"]
        for p in phases:
            hist[p] = hist.get(p, 0) + 1
    rows = [{"phase": k, "count": v, "query": query, "page_size": page_size} for k, v in sorted(hist.items())]
    if not rows:
        raise SystemExit("no studies returned")
    with open("trials_phase_hist.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["phase", "count", "query", "page_size"]); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} phase bins from {page_size} studies -> trials_phase_hist.csv")

if __name__ == "__main__":
    main(*sys.argv[1:3])
