#!/usr/bin/env python3
"""Deterministic checks for the toolkit integration output (local site tree or LIVE).

  python3 scripts/site/test_live_toolkit.py --site /path/to/site      # local tree
  python3 scripts/site/test_live_toolkit.py --live https://botshelfvampire.com

Checks: public pages carry no source bodies; gated paths are covered by the edge gate
(local) or answer anonymous requests with a redirect to registration (live); internal
links resolve; no forbidden copy; no false Verified claims; entry points exist.
"""
from __future__ import annotations
import argparse, json, re, sys, urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FORBIDDEN = ["元のライセンスとともに", "--gold", "Verified ✓", "runtime verified by BSV", "Tested by BSV"]


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("href", "src"):
            v = a.get(k)
            if v and not v.startswith(("http", "mailto:", "#", "data:", "javascript:")):
                self.links.append(v)


def source_lines():
    out = set()
    for cat in ("trader-toolkit/catalog.json", "ai-toolkit/catalog.json"):
        c = json.loads((REPO / cat).read_text())
        for e in c["entries"]:
            if e["type"] in ("guide", "integration-guide"):
                continue
            p = REPO / e["path"]
            files = [f for f in p.rglob("*") if f.is_file()] if p.is_dir() else [p]
            for f in files:
                if f.name == "README.md":
                    continue
                for line in f.read_text(errors="ignore").splitlines():
                    s = line.strip()
                    if len(s) >= 28 and not s.startswith(("#", "//", "- ", "* ", "http")) and not re.match(r"^[A-Z][^{}();=]*$", s):
                        out.add(s)
    return out


class Fetch:
    def __init__(self, base):
        self.base = base.rstrip("/")
    def get(self, path, follow=True):
        class NoRedir(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedir)
        req = urllib.request.Request(self.base + path, headers={"User-Agent": "bsv-toolkit-check/1", "Cache-Control": "no-cache"})
        try:
            r = opener.open(req, timeout=30)
            return r.status, r.headers, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read().decode("utf-8", "replace") if e.fp else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site"); ap.add_argument("--live")
    ap.add_argument("--part", choices=["trader", "ai", "all"], default="all")
    a = ap.parse_args()
    fails, notes = [], []
    lines = source_lines()
    tmeta = json.loads((REPO / "trader-toolkit/catalog.json").read_text())
    amEta = json.loads((REPO / "ai-toolkit/catalog.json").read_text())
    t_public = ["/trading/build/", "/trading/build/toolkit.v1.json"] + [f"/trading/tools/bsv-{e['id']}.html" for e in tmeta["entries"] if e["id"] != "trader-build-own-chart"] + [f"/trading/tools/bsv-recipe-{r}.html" for r in tmeta["recipes"]]
    t_gated = [f"/trading/items/bsv-{e['id']}.html" for e in tmeta["entries"] if e["type"] not in ("guide", "integration-guide")] + [f"/trading/items/bsv-recipe-{r}.html" for r in tmeta["recipes"]] + [f"/trading/downloads/bsv-recipe-{r}.zip" for r in tmeta["recipes"]]
    a_public = ["/library/toolkit/", "/library/toolkit/toolkit.v1.json"] + [f"/library/toolkit/{e['id']}/" for e in amEta["entries"]]
    a_gated = [f"/library/source/{e['id']}.html" for e in amEta["entries"]] + [f"/library/source/{e['id']}.zip" for e in amEta["entries"]]
    public, gated = [], []
    if a.part in ("trader", "all"): public += t_public; gated += t_gated
    if a.part in ("ai", "all"): public += a_public; gated += a_gated
    entry_checks = []
    if a.part in ("trader", "all"): entry_checks.append(("/trading/", "/trading/build/"))
    if a.part in ("ai", "all"): entry_checks.append(("/library/", "/library/toolkit/"))

    if a.site:
        site = Path(a.site)
        def read(p):
            f = site / p.lstrip("/")
            if p.endswith("/"): f = f / "index.html"
            return f.read_text() if f.exists() else None
        gate = (site / "netlify/edge-functions/free-session-gate.ts").read_text()
        cfg = re.search(r"path:\s*\[(.*?)\]", gate, re.S).group(1)
        pats = [p.strip().strip('"') for p in cfg.split(",") if p.strip()]
        for g in gated:
            f = site / g.lstrip("/")
            if not f.exists(): fails.append(f"missing gated file {g}")
            if not any(re.fullmatch(re.escape(p).replace(r"\*", ".*"), g) for p in pats): fails.append(f"gated path not covered by edge gate: {g}")
        for p in public:
            t = read(p)
            if t is None: fails.append(f"missing public {p}"); continue
            leaked = [l for l in lines if l in t or l.replace('"', "&quot;") in t or l.replace("<", "&lt;") in t]
            if leaked: fails.append(f"source body leaked on public {p}: {leaked[0][:60]}")
            for bad in FORBIDDEN:
                if bad in t: fails.append(f"forbidden text {bad!r} in {p}")
            if p.endswith((".html", "/")):
                lp = Links(); lp.feed(t)
                for l in lp.links:
                    path = l.split("#")[0].split("?")[0]
                    if not path: continue
                    if not path.startswith("/"): path = "/trading/" + path if p.startswith("/trading/") else str(Path(p).parent / path)
                    tgt = site / path.lstrip("/")
                    if path.endswith("/"): tgt = tgt / "index.html"
                    if not (tgt.exists() or path.startswith(("/trading/register.html", "/register.html")) or (site / (path.lstrip('/') + '.html')).exists()):
                        fails.append(f"broken link {l} on {p}")
        for page, needle in entry_checks:
            t = read(page)
            if needle not in (t or ""): fails.append(f"entry point {needle} missing on {page}")
        css = next(iter(sorted((site / "trading/assets").glob("build.v*.css"))), site / "nonexistent")
        if css.exists() and "gold" in css.read_text(): fails.append("gold in build css")
    if a.live:
        F = Fetch(a.live)
        for p in public:
            s, h, t = F.get(p)
            if s != 200: fails.append(f"LIVE {p} -> {s}"); continue
            leaked = [l for l in lines if l in t or l.replace('"', "&quot;") in t]
            if leaked: fails.append(f"LIVE source leaked on {p}: {leaked[0][:60]}")
        for g in gated:
            s, h, t = F.get(g, follow=False)
            loc = (h.get("Location") if h else "") or ""
            want_ok = ("register" in loc) or (g.startswith("/trading/items/") and loc.endswith("/trading/tools/" + g.rsplit("/", 1)[1]))
            if s not in (301, 302, 303, 307) or not want_ok: fails.append(f"LIVE gate not enforced for anonymous {g}: {s} {loc}")
            elif any(l in t for l in lines): fails.append(f"LIVE gated body leaked in redirect {g}")
        for page, needle in entry_checks:
            s, h, t = F.get(page)
            if needle not in t: fails.append(f"LIVE entry point {needle} missing on {page}")
        notes.append(f"live checked public={len(public)} gated={len(gated)}")
    print(json.dumps({"ok": not fails, "fails": fails[:50], "fail_count": len(fails), "notes": notes, "public": len(public), "gated": len(gated), "source_lines_checked": len(lines)}, ensure_ascii=False, indent=1))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
