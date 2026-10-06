#!/usr/bin/env python3
"""Release evidence: compact inventory of the eight peer-level categories → live URLs + provenance.

Writes /release-inventory.json (and a short /release-inventory.html index) from the built site.
Counts are computed from published files only — no invented numbers.
"""
import argparse, json, pathlib, re, sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
CATS = [
 ("ai", "AI", "/library/", "Build Library (AI teams, workflows, toolkits)"),
 ("trading", "Trading", "/trading/", "Traders Library + chart tools + recipe builder"),
 ("robotics", "Robotics", "/robot-pilot/", "Robot Pilot Academy (simulation curricula + teleop recipes)"),
 ("healthcare", "Healthcare & Medical Robotics", "/fields/healthcare/", "Field recipes / tools / sources (research & simulation only)"),
 ("data", "Data", "/search/?q=data", "Search index entries tagged use_case=Data (no dedicated hub yet when count is from search)"),
 ("space", "Space", "/fields/space/", "Field recipes / tools / sources"),
 ("biotech", "Biotech", "/fields/biotech/", "Field recipes / tools / sources"),
 ("quantum", "Quantum", "/fields/quantum/", "Field recipes / tools / sources"),
]

def exists(site, rel):
    rel = rel.split("?")[0]
    p = site / rel.lstrip("/")
    if p.is_dir():
        return (p / "index.html").exists()
    if not rel.endswith(".html") and (site / (rel.lstrip("/") + ".html")).exists():
        return True
    return p.exists()

def sample_urls(site, key):
    out = []
    if key == "ai":
        for sub in ("workflows/index.html", "toolkit/index.html", "index.html"):
            if (site / "library" / sub).exists() or (site / "library" / sub.replace("index.html","")).exists():
                out.append("/library/" + ("" if sub == "index.html" else sub.replace("index.html","")))
        # cap
    elif key == "trading":
        for u in ("/trading/", "/trading/tools/", "/trading/tools/bsv-builder.html", "/trading-gold-morning-3.html"):
            if exists(site, u): out.append(u)
    elif key == "robotics":
        for u in ("/robot-pilot/", "/robot-pilot/curricula/isaac-teleop-so101-sim-v1.json"):
            if exists(site, u): out.append(u)
    elif key in ("healthcare", "space", "biotech", "quantum"):
        base = f"/fields/{key}/"
        if exists(site, base): out.append(base)
        # first recipe anchor if any
        p = site / "fields" / key / "index.html"
        if p.exists():
            ids = re.findall(r'id="(fld-[a-z0-9\-]+)"', p.read_text())[:3]
            out.extend(f"{base}#{i}" for i in ids)
    elif key == "data":
        out.append("/search/?q=data")
        idx = sorted((site / "search").glob("index.v*.json"))
        if idx:
            try:
                rows = json.loads(idx[-1].read_text()).get("rows") or []
                for e in rows:
                    blob = json.dumps(e, ensure_ascii=False).lower()
                    if "data" in blob and e.get("u"):
                        out.append(e["u"] if str(e["u"]).startswith("/") else "/" + str(e["u"]))
                        if len(out) >= 4: break
            except Exception:
                pass
    # dedupe preserve order
    seen=set(); uniq=[]
    for u in out:
        if u not in seen: seen.add(u); uniq.append(u)
    return uniq[:8]

def home_counts(site: pathlib.Path) -> dict:
    """Reuse the same live counts the homepage tiles use (build_home_value.counts)."""
    import build_home_value as H
    return H.counts(site)

def count_for(site, key, hc=None):
    hc = hc or home_counts(site)
    return int(hc.get(f"cat_{key}", 0))

def provenance(key):
    return {
        "ai": "Generated/curated under library/; team bodies may be gated after email verify",
        "trading": "Traders Library catalog + BSV recipe builder outputs; third-party sources keep upstream license",
        "robotics": "Original BSV Robot Pilot curricula/recipes; links NVIDIA docs, does not redistribute NVIDIA code",
        "healthcare": "BSV field recipes on /fields/healthcare/; research, education and simulation only",
        "data": "Entries discovered via site search index (use_case=Data)",
        "space": "BSV field recipes on /fields/space/",
        "biotech": "BSV field recipes on /fields/biotech/",
        "quantum": "BSV field recipes on /fields/quantum/",
    }[key]

def build(site: pathlib.Path) -> dict:
    hc = home_counts(site)
    cats = []
    for key, name, hub, blurb in CATS:
        n = count_for(site, key, hc)
        live = n > 0 and exists(site, hub.split("?")[0] if not hub.startswith("/search") else "search/index.html") or (key=="data" and n>=0)
        # data hub is search — always "exists" if search index present
        if key == "data":
            live = n > 0
        elif hub.startswith("/fields/") or hub in ("/library/", "/trading/", "/robot-pilot/"):
            live = exists(site, hub) and n > 0
        cats.append({
            "key": key, "name": name, "hub": hub, "blurb": blurb,
            "live_count": n, "status": "live" if (exists(site, hub) if not hub.startswith("/search") else True) and n > 0 else ("coming_soon" if n == 0 else "live"),
            "sample_urls": sample_urls(site, key),
            "provenance": provenance(key),
        })
    return {
        "generated_at_jst": datetime.now(JST).strftime("%Y-%m-%d %H:%M JST"),
        "purpose": "Release evidence — eight peer-level categories mapped to live destinations",
        "categories": cats,
    }

def html_page(inv: dict) -> str:
    rows = []
    for c in inv["categories"]:
        samples = " · ".join(f'<a href="{u}">{u}</a>' for u in c["sample_urls"][:4]) or "—"
        rows.append(f"<tr><th>{c['name']}</th><td>{c['status']}</td><td>{c['live_count']}</td>"
                    f"<td><a href=\"{c['hub']}\">{c['hub']}</a></td><td>{samples}</td>"
                    f"<td>{c['provenance']}</td></tr>")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Release inventory — eight categories | BotShelf Vampire</title>
<meta name="robots" content="noindex,follow">
<link rel="stylesheet" href="/css/shelf.v20261001menu.g2961d54b.css">
</head><body><main class="wrap" style="padding:24px 16px 48px;max-width:1100px;margin:0 auto">
<h1>Release inventory</h1>
<p class="muted">Build-computed map of the eight peer-level categories. Generated {inv['generated_at_jst']}. JSON: <a href="/release-inventory.json">/release-inventory.json</a>.</p>
<table class="qa-table" style="width:100%;border-collapse:collapse;font-size:14px">
<thead><tr><th>Category</th><th>Status</th><th>Count</th><th>Hub</th><th>Sample URLs</th><th>Provenance</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p class="muted">Counts come from published files on this build. Coming soon means zero published items in that field.</p>
</main></body></html>
"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); ap.add_argument("--check", action="store_true")
    a = ap.parse_args(); site = pathlib.Path(a.site)
    inv = build(site)
    if a.check:
        fails = []
        if len(inv["categories"]) != 8: fails.append("need 8 categories")
        for c in inv["categories"]:
            if not c["hub"]: fails.append(f"{c['key']}: no hub")
            if c["status"] == "live" and not c["sample_urls"]: fails.append(f"{c['key']}: live but no samples")
        print({"test": "release_inventory", "categories": 8, "failures": len(fails), "fail": fails, "counts": {c["key"]: c["live_count"] for c in inv["categories"]}})
        sys.exit(1 if fails else 0)
    (site / "release-inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n")
    (site / "release-inventory.html").write_text(html_page(inv))
    print({"pass": "release_inventory", "path": "release-inventory.json", "counts": {c["key"]: c["live_count"] for c in inv["categories"]}})

if __name__ == "__main__":
    main()
