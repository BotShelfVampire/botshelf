#!/usr/bin/env python3
"""BSV recipe: look up one small body on JPL SBDB and write a short markdown + JSON.

Education / research only. Orbital elements are as published by JPL; BSV does not propagate impacts
or claim hazard. Verify on the Small-Body Database before quoting.

Input : designation or name (default 433 = Eros).
Output: sbdb_<id>.md and sbdb_<id>.json
Original BSV code, MIT. Data: NASA/JPL SSD SBDB API.
"""
import json, re, sys, urllib.parse, urllib.request

UA = {"User-Agent": "BSV-fields-recipe/1.0 (education; +https://botshelfvampire.com)"}

def main(sstr="433"):
    sstr = (sstr or "433").strip()
    q = urllib.parse.urlencode({"sstr": sstr, "phys-par": "true"})
    url = f"https://ssd-api.jpl.nasa.gov/sbdb.api?{q}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode("utf-8"))
    obj = data.get("object") or {}
    orbit = data.get("orbit") or {}
    phys = {p.get("name"): p.get("value") for p in (data.get("phys_par") or []) if isinstance(p, dict)}
    name = obj.get("fullname") or obj.get("des") or sstr
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", str(obj.get("des") or sstr))[:40]
    md = [f"# JPL SBDB lookup — {name}", "",
          f"Query: `{sstr}`", "",
          "**Education/research only. Not an impact forecast.**", "",
          f"- designation: {obj.get('des')}",
          f"- fullname: {obj.get('fullname')}",
          f"- kind: {obj.get('kind')}",
          f"- orbit class: {(obj.get('orbit_class') or {}).get('name') if isinstance(obj.get('orbit_class'), dict) else obj.get('orbit_class')}",
          f"- epoch: {orbit.get('epoch')}",
          f"- data arc (days): {orbit.get('data_arc')}",
          f"- condition code: {orbit.get('condition_code')}",
          "", "## Selected physical parameters (as published)", ""]
    for k in sorted(phys)[:12]:
        md.append(f"- {k}: {phys[k]}")
    md += ["", f"Source: {url}", "Verify: https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html", ""]
    open(f"sbdb_{safe}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump(data, open(f"sbdb_{safe}.json", "w", encoding="utf-8"), indent=1)
    print(f"wrote sbdb_{safe}.md + sbdb_{safe}.json for {name!r}")

if __name__ == "__main__":
    main(*sys.argv[1:2])
