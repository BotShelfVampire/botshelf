#!/usr/bin/env python3
"""Link regression test for the built site (QC 2026-10-06).

1) No path-relative href/src/action/srcset left in any HTML page (absolutize_links.py): pages served at another URL
   (source-gate redirects to /register.html, 404.html at any path, <base href="/trading/"> pages) cannot nest links.
2) The Traders Library header licenses link is /trading/guides/licenses.html on the 7 hub pages QC flagged, and exists.
3) /trading/tools/index.html exists and links every public tool summary page in /trading/tools/.
4) Every root-absolute internal link to an HTML page or directory resolves to a file in the tree.
5) A crawler that ignores <base> and resolves against the requested path (as the daily QC does) never builds
   /library/source/library/ or <dir>/guides/licenses.html from the register / 404 / hub pages.
usage: test_links.py --site DIR"""
import argparse, collections, json, re, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from absolutize_links import relative_links, SKIP_BLOCK, TAG

HUBS = ["requests/index.html", "trading/build/index.html", "trading/tools/index.html", "trading/build/coverage/index.html",
        "transparency/index.html", "capabilities/index.html", "robot-pilot/index.html"]
A = re.compile(r"""\s(?:href|src|action)\s*=\s*["']([^"']*)["']""", re.I)


def links(t):
    bare = SKIP_BLOCK.sub(lambda m: m.group(1)[: m.group(1).find(">") + 1], t)
    out = []
    for tg in TAG.findall(bare):
        if not tg.lower().startswith("<base"):
            out += A.findall(tg)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); a = ap.parse_args()
    s = Path(a.site).resolve(); fails, n = [], [0]
    def ok(c, m):
        n[0] += 1
        if not c: fails.append(m)
    def exists(path):
        path = urllib.parse.unquote(path.split("#")[0].split("?")[0])
        f = s / path.lstrip("/")
        return (f / "index.html").exists() if path.endswith("/") else (f.exists() or (f / "index.html").exists() or f.with_name(f.name + ".html").exists())  # Netlify serves /x from x.html
    pages = sorted(s.rglob("*.html")); rel_pages = []; proto = []; missing = collections.Counter()
    for p in pages:
        t = p.read_text(errors="replace")
        r = relative_links(t)
        if r: rel_pages.append((p.relative_to(s).as_posix(), r[:3]))
        pr = [v for v in links(t) if v.startswith("//")]
        if pr: proto.append((p.relative_to(s).as_posix(), pr[:2]))
        for v in links(t):
            if v.startswith("/") and not v.startswith("//") and not v.startswith(("/api/", "/.netlify/")):
                last = urllib.parse.urlparse(v).path.rsplit("/", 1)[-1]
                if (v.split("?")[0].split("#")[0].endswith("/") or last.endswith(".html") or "." not in last) and not exists(v):
                    missing[v.split("#")[0]] += 1
    ok(not rel_pages, f"path-relative links left on {len(rel_pages)} pages: {rel_pages[:5]}")
    ok(not proto, f"protocol-relative (//...) links on {len(proto)} pages (a bad absolutize turns 'x/' into '//x/'): {proto[:5]}")
    ok(not missing, f"internal HTML links to missing pages: {missing.most_common(8)}")
    ok((s / "trading/guides/licenses.html").exists(), "/trading/guides/licenses.html exists")
    for h in HUBS:
        f = s / h
        ok(f.exists(), f"hub exists: {h}")
        if not f.exists(): continue
        L = links(f.read_text(errors="replace"))
        ok("/trading/guides/licenses.html" in L, f"{h}: licenses link is /trading/guides/licenses.html")
        ok("guides/licenses.html" not in L, f"{h}: no relative guides/licenses.html")
    ti = s / "trading/tools/index.html"
    if ti.exists():
        L = set(links(ti.read_text(errors="replace")))
        tools = {"/trading/tools/" + p.name for p in (s / "trading/tools").glob("*.html") if p.name != "index.html"}
        cat = s / "trading/build/toolkit.v1.json"
        listed = {e["url"] for e in json.loads(cat.read_text())["entries"]} if cat.exists() else set()
        ok(listed and listed <= L | {u for u in listed if u.startswith("/trading/build/")}, "tools index links every catalog entry")
        ok(tools <= L, f"tools index links every summary page in /trading/tools/ ({len(tools & L)}/{len(tools)}; missing {sorted(tools - L)[:3]})")
        ok('rel="canonical" href="https://botshelfvampire.com/trading/tools/"' in ti.read_text(), "tools index canonical")
    # crawler model: content of register.html / 404.html served at a gated / missing path, links resolved against that path
    for served_at, file in (("/library/source/x.html", "register.html"), ("/trading/items/x.html", "trading/register.html"), ("/no/such/page/", "404.html")):
        f = s / file
        if not f.exists(): continue
        bad = [v for v in links(f.read_text(errors="replace")) if not re.match(r"^(/|#|\?|[a-zA-Z][a-zA-Z0-9+.-]*:)", v)]
        nested = [urllib.parse.urljoin("https://x" + served_at, v) for v in bad]
        ok(not any("/library/source/library/" in u for u in nested) and not bad, f"{file} served at {served_at}: no relative links ({bad[:3]})")
    print(json.dumps({"test": "links", "pages": len(pages), "checks": n[0], "failures": len(fails), "fail": fails[:10]}, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
