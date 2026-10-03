#!/usr/bin/env python3
"""Checks for the gated Library team bodies.
Local:  --site <tree> --orig <pre-gate tree>   (no body line in any public file; gated pages hold the body)
Live:   --live https://botshelfvampire.com --orig <pre-gate tree> [--cookies <jar>]
        anonymous: public pages 200 without body, gated pages 302 -> /register.html, items.json/search/sitemap clean
        cookies (operator test session): gated pages 200 with the body
"""
import argparse, html, json, re, sys, urllib.request, http.cookiejar
from pathlib import Path

# Separate public kit that overlaps two Open WebUI bodies; reported to the owner, not part of the 70-item gate.
KNOWN_OUT_OF_SCOPE = ("cross-ai/kits/research-desk-local/",)
GATED_PREFIX = ("library/source/", "trading/items/", "trading/sources/", "trading/downloads/", "registered", "switchboard-cos", "netlify/")
PRE = re.compile(r'<pre class="lib-pre" id="lib-body">(.*?)</pre>', re.S)


def bodies(orig: Path):
    reg = json.loads((orig / "library/registry.json").read_text())
    out = {}
    for t in reg["teams"]:
        for i in t["implementations"]:
            u = i["url"]; rt, slug = u.split("/")[2:4]
            m = PRE.search((orig / u.lstrip("/") / "index.html").read_text())
            body = html.unescape(m.group(1))
            lines = [l.strip() for l in body.splitlines() if len(l.strip()) >= 40]
            # lines that are unique to this body among public pages are the probes
            out[u] = {"gated": f"/library/source/team-{rt}-{slug}.html", "probes": lines[:6] or [body.strip()[:60]], "body": body}
    return out


def fail(msg, errs):
    errs.append(msg); print("FAIL", msg)


def local(site: Path, orig: Path):
    errs = []
    b = bodies(orig)
    probes = {p: u for u, d in b.items() for p in d["probes"]}
    for f in site.rglob("*"):
        rel = str(f.relative_to(site))
        if not f.is_file() or rel.startswith(GATED_PREFIX) or rel.startswith("node_modules/") or f.suffix in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".zip", ".mp4", ".woff2", ".pdf"):
            continue
        t = html.unescape(f.read_text(errors="ignore"))
        for p, u in probes.items():
            if p in t and rel.startswith(KNOWN_OUT_OF_SCOPE):
                print(f"WARN out-of-scope public kit {rel} overlaps {u}"); break
            if p in t:
                fail(f"public file {rel} contains body line of {u}: {p[:50]}", errs); break
    for u, d in b.items():
        g = site / d["gated"].lstrip("/")
        if not g.exists():
            fail(f"missing gated page {d['gated']}", errs); continue
        gt = html.unescape(g.read_text())
        if d["body"].strip() not in gt:
            fail(f"gated page {d['gated']} lacks exact body", errs)
        pt = (site / u.lstrip("/") / "index.html").read_text()
        if 'data-bsv-gate="lib-body"' not in pt or d["gated"] not in pt:
            fail(f"public page {u} lacks gate entry", errs)
    for f in site.rglob("*.bak*"):
        fail(f"backup artifact still in deploy tree: {f.relative_to(site)}", errs)
    print(f"local: {len(b)} bodies checked, errors={len(errs)}")
    return errs


def live(base: str, orig: Path, jar: str | None):
    errs = []
    b = bodies(orig)

    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    anon = urllib.request.build_opener(NoRedir)
    def get(op, path):
        try:
            r = op.open(urllib.request.Request(base + path, headers={"User-Agent": "bsv-gate-test/1"}), timeout=30)
            return r.status, r.headers, r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.headers, ""
    logged = None
    if jar:
        cj = http.cookiejar.MozillaCookieJar(jar); cj.load(ignore_discard=True, ignore_expires=True)
        logged = urllib.request.build_opener(NoRedir, urllib.request.HTTPCookieProcessor(cj))
    for u, d in b.items():
        s, h, t = get(anon, u)
        t = html.unescape(t)
        if s != 200: fail(f"anon {u} -> {s}", errs)
        if any(p in t for p in d["probes"]): fail(f"anon {u} shows body", errs)
        if d["gated"] not in t: fail(f"anon {u} lacks gate link", errs)
        s, h, _ = get(anon, d["gated"])
        loc = h.get("Location", "") if h else ""
        if s != 302 or not loc.startswith("/register.html?next="): fail(f"anon gated {d['gated']} -> {s} {loc}", errs)
        if logged:
            s, h, t = get(logged, d["gated"])
            if s != 200 or d["body"].strip() not in html.unescape(t): fail(f"logged gated {d['gated']} -> {s} body={'ok' if d['body'].strip() in html.unescape(t) else 'missing'}", errs)
    probes = [p for d in b.values() for p in d["probes"]]
    for path in ("/library/catalog/items.json", "/library/search-index.json", "/library/registry.json", "/sitemap.xml", "/sitemap.txt", "/llms.txt", "/library/", "/search/"):
        s, h, t = get(anon, path)
        t = html.unescape(t)
        if s == 200 and any(p in t for p in probes): fail(f"anon {path} leaks a body", errs)
        if path.endswith("items.json") and '"body":' in t: fail("items.json still has body field", errs)
    s, _, _ = get(anon, "/library/crewai/coding-review/index.html.bak-pre-recon")
    if s == 200: fail("anon .bak file still served", errs)
    print(f"live: {len(b)} items, logged={'yes' if logged else 'no'}, errors={len(errs)}")
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--site"); ap.add_argument("--orig", required=True); ap.add_argument("--live"); ap.add_argument("--cookies")
    a = ap.parse_args()
    e = local(Path(a.site), Path(a.orig)) if a.site else []
    if a.live:
        e += live(a.live.rstrip("/"), Path(a.orig), a.cookies)
    sys.exit(1 if e else 0)
