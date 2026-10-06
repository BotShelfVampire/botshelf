#!/usr/bin/env python3
"""Check every outbound source on the BSV field pages (starter stack, comparison table, recipe next steps).

A URL passes only when a direct GET (no redirect following) returns HTTP 200. Results go to
fields/sources_check.json; build_fields.py refuses to publish a starter-stack source whose last check failed.
usage: check_fields_sources.py"""
import datetime as dt, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fields_content as C

ROOT = Path(__file__).resolve().parents[2]

def urls():
    out = set()
    for f in C.F.values():
        out.update(s[1] for s in f["stack"])
        out.update(c[1] for c in f["compare"])
        out.update(r["next_href"] for r in f["recipes"] if r.get("next_href", "").startswith("http"))
    return sorted(out)

def main():
    res, bad = {}, []
    for u in urls():
        p = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "30", "-A",
                            "Mozilla/5.0 (compatible; BSV source check; +https://botshelfvampire.com/)", u], capture_output=True, text=True)
        code = int(p.stdout or 0)
        res[u] = {"status": code, "checked_jst": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d")}
        if code != 200:
            bad.append((u, code))
    (ROOT / "fields/sources_check.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({"checked": len(res), "not_200": bad}))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
