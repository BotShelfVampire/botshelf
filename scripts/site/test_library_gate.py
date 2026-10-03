#!/usr/bin/env python3
"""Checks for gated Library bodies (70 team implementations + pack items).
Local:  --site <tree> --orig <pre-gate tree> [--packs a,b|all]
Live:   --live https://botshelfvampire.com --orig <pre-gate tree> [--packs ...] [--cookies <jar>] [--skip-teams]
        anonymous: public pages 200 without body + gate link; gated pages 302 -> /register.html; items.json/search/sitemap/llms clean
        cookies (operator test session): gated pages 200 containing the exact body
"""
import argparse, html, json, re, sys, urllib.request, http.cookiejar
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KNOWN_OUT_OF_SCOPE = ("cross-ai/kits/research-desk-local/",)  # separate public kit; owner decided to leave it as is
GATED_PREFIX = ("library/source/", "trading/items/", "trading/sources/", "trading/downloads/", "registered", "switchboard-cos", "netlify/", "node_modules/")
TEAM_PRE = re.compile(r'<pre class="lib-pre" id="lib-body">(.*?)</pre>', re.S)
PACK_PRE = re.compile(r'<p class="section-label">Full FREE body</p>.*?<pre class="lib-pre" id="lib-body">(.*?)</pre>', re.S)
SKIP = {"toolkit", "teams", "source", "catalog", "registry"}
BIN = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".zip", ".mp4", ".woff2", ".pdf")
norm = lambda s: re.sub(r"\s+", " ", s).strip()


def collect(orig: Path, teams=True, packs=None):
    out = {}
    if teams:
        reg = json.loads((orig / "library/registry.json").read_text())
        for t in reg["teams"]:
            for i in t["implementations"]:
                u = i["url"]; rt, slug = u.split("/")[2:4]
                out[u] = {"gated": f"/library/source/team-{rt}-{slug}.html", "body": html.unescape(TEAM_PRE.search((orig / u.lstrip("/") / "index.html").read_text()).group(1))}
    if packs:
        for pp in sorted(orig.glob("library/*/*/index.html")):
            rt, slug = pp.parts[-3], pp.parts[-2]
            if rt in SKIP or (packs != {"all"} and rt not in packs):
                continue
            m = PACK_PRE.search(pp.read_text())
            if m:
                out[f"/library/{rt}/{slug}/"] = {"gated": f"/library/source/item-{rt}-{slug}.html", "body": html.unescape(m.group(1))}
    # probes: long lines unique to one body, else a 70-char window from the middle of the normalised body
    seen = {}
    for u, d in out.items():
        for l in {l.strip() for l in d["body"].splitlines() if len(l.strip()) >= 40}:
            seen.setdefault(l, set()).add(u)
    for u, d in out.items():
        ls = [l for l in {l.strip() for l in d["body"].splitlines()} if len(seen.get(l, ())) == 1][:4]
        n = norm(d["body"]); mid = len(n) // 2
        d["probes"] = [norm(l) for l in ls] + ([n[max(0, mid - 35): mid + 35]] if len(n) >= 70 else [n])
    return out


def leaks(text, d):
    t = norm(html.unescape(text))
    return [p for p in d["probes"] if p in t]


def fail(msg, errs):
    errs.append(msg); print("FAIL", msg)


def local(site: Path, b: dict):
    errs = []
    files = {}
    for f in site.rglob("*"):
        rel = str(f.relative_to(site))
        if f.is_file() and not rel.startswith(GATED_PREFIX) and f.suffix not in BIN:
            files[rel] = norm(html.unescape(f.read_text(errors="ignore")))
    probes = {p: u for u, d in b.items() for p in d["probes"]}
    for rel, t in files.items():
        for p, u in probes.items():
            if p in t:
                if rel.startswith(KNOWN_OUT_OF_SCOPE):
                    print(f"WARN out-of-scope public kit {rel} overlaps {u}"); break
                fail(f"public file {rel} contains body of {u}: {p[:50]}", errs); break
    for u, d in b.items():
        g = site / d["gated"].lstrip("/")
        if not g.exists():
            fail(f"missing gated page {d['gated']}", errs); continue
        if d["body"].strip() not in html.unescape(g.read_text()):
            fail(f"gated page {d['gated']} lacks exact body", errs)
        pt = (site / u.lstrip("/") / "index.html").read_text()
        if 'data-bsv-gate="lib-body"' not in pt or d["gated"] not in pt:
            fail(f"public page {u} lacks gate entry", errs)
    for f in site.rglob("*.bak*"):
        fail(f"backup artifact still in deploy tree: {f.relative_to(site)}", errs)
    print(f"local: {len(b)} bodies checked, errors={len(errs)}")
    return errs


class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def live(base: str, b: dict, jar):
    errs = []
    anon = urllib.request.build_opener(NoRedir)
    logged = None
    if jar:
        cj = http.cookiejar.MozillaCookieJar(jar); cj.load(ignore_discard=True, ignore_expires=True)
        logged = urllib.request.build_opener(NoRedir, urllib.request.HTTPCookieProcessor(cj))

    def get(op, path):
        for _ in range(3):
            try:
                r = op.open(urllib.request.Request(base + path, headers={"User-Agent": "bsv-gate-test/1"}), timeout=30)
                return r.status, r.headers, r.read().decode("utf-8", "ignore")
            except urllib.error.HTTPError as e:
                return e.code, e.headers, ""
            except Exception:
                continue
        return 0, {}, ""

    def check(item):
        u, d = item
        e = []
        s, h, t = get(anon, u)
        if s != 200: e.append(f"anon {u} -> {s}")
        if leaks(t, d): e.append(f"anon {u} shows body")
        if d["gated"] not in t: e.append(f"anon {u} lacks gate link")
        s, h, _ = get(anon, d["gated"])
        loc = h.get("Location", "") if h else ""
        if s != 302 or not loc.startswith("/register.html?next="): e.append(f"anon gated {d['gated']} -> {s} {loc}")
        if logged:
            s, h, t = get(logged, d["gated"])
            if s != 200 or d["body"].strip() not in html.unescape(t): e.append(f"logged gated {d['gated']} -> {s} exact_body={d['body'].strip() in html.unescape(t)}")
        return e
    with ThreadPoolExecutor(8) as ex:
        for e in ex.map(check, b.items()):
            for m in e: fail(m, errs)
    for path in ("/library/catalog/items.json", "/library/search-index.json", "/library/registry.json", "/sitemap.xml", "/sitemap.txt", "/llms.txt", "/library/", "/search/"):
        s, h, t = get(anon, path)
        hit = [u for u, d in b.items() if leaks(t, d)] if s == 200 else []
        if hit: fail(f"anon {path} leaks bodies of {hit[:3]}", errs)
        if path.endswith("items.json") and '"body":' in t: fail("items.json still has body field", errs)
    for path in ("/library/crewai/coding-review/index.html.bak-pre-recon", "/library/build_library.py"):
        if get(anon, path)[0] == 200: fail(f"anon {path} still served", errs)
    print(f"live: {len(b)} items, logged={'yes' if logged else 'no'}, errors={len(errs)}")
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--site"); ap.add_argument("--orig", required=True); ap.add_argument("--live"); ap.add_argument("--cookies")
    ap.add_argument("--packs", default=""); ap.add_argument("--skip-teams", action="store_true")
    a = ap.parse_args()
    b = collect(Path(a.orig), teams=not a.skip_teams, packs=set(a.packs.split(",")) if a.packs else None)
    e = local(Path(a.site), b) if a.site else []
    if a.live:
        e += live(a.live.rstrip("/"), b, a.cookies)
    sys.exit(1 if e else 0)
