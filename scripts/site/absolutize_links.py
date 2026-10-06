#!/usr/bin/env python3
"""Rewrite relative links in every built HTML page to root-absolute paths (idempotent).

Why: pages are served at more than one URL. The source gate redirects /library/source/* and /trading/items/* to the
register pages, 404.html is served at any missing path, and 80 Traders Library pages rely on <base href="/trading/">.
A relative link ("library/", "guides/licenses.html") then resolves against the wrong directory for clients that do not
apply <base> or the final redirect URL (crawlers, link checkers) and nests (/library/source/library/library/...).

Rule: href / src / action / poster / srcset values that are path-relative (not "/", "#", "?", "//" or a scheme) are
resolved against the page's <base href> if it has one, else the page's own URL path, and written as "/...". The
browser result is unchanged for a page served at its own path. Text inside <script>, <style>, <textarea> and
escaped code is not touched. usage: absolutize_links.py --site DIR [--check]
"""
import argparse, re, sys, urllib.parse
from pathlib import Path

SKIP_BLOCK = re.compile(r"(<(script|style|textarea)\b[^>]*>.*?</\2\s*>)", re.S | re.I)
TAG = re.compile(r"<[a-zA-Z][^<>]*>")
ATTR = re.compile(r"""(\s(?:href|src|action|poster)\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
SRCSET = re.compile(r"""(\ssrcset\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
BASE = re.compile(r"""<base\s[^>]*href\s*=\s*["']([^"']*)["']""", re.I)
NOT_REL = re.compile(r"^(?:$|/|#|\?|[a-zA-Z][a-zA-Z0-9+.-]*:|\{\{|\$\{)")


def page_url(site: Path, p: Path) -> str:
    rel = p.relative_to(site).as_posix()
    return "/" + rel


def resolve(base_url: str, href: str) -> str:
    """Browser resolution (RFC 3986 via urljoin) of a path-relative href against base_url ("/dir/page.html" or
    "/dir/"); returns the root-absolute path with ?query and #fragment kept."""
    u = urllib.parse.urlsplit(urllib.parse.urljoin("https://bsv.invalid" + base_url, href))
    if u.netloc != "bsv.invalid" or not u.path.startswith("/") or u.path.startswith("//"):
        raise ValueError(f"cannot absolutize {href!r} against {base_url!r}")
    return urllib.parse.urlunsplit(("", "", u.path, u.query, u.fragment))


def is_rel(v: str) -> bool:
    return not NOT_REL.match(v.strip())


def fix_html(text: str, url: str) -> tuple[str, int]:
    b = BASE.search(text)
    base_url = b.group(1) if b and b.group(1).startswith("/") and not b.group(1).startswith("//") else url
    n = [0]

    def attr(m):
        v = m.group(3)
        if not is_rel(v):
            return m.group(0)
        n[0] += 1
        return m.group(1) + m.group(2) + resolve(base_url, v.strip()) + m.group(2)

    def srcset(m):
        parts, changed = [], False
        for item in m.group(3).split(","):
            s = item.strip()
            if not s:
                parts.append(item); continue
            u, _, d = s.partition(" ")
            if is_rel(u):
                u = resolve(base_url, u); changed = True
            parts.append(u + (" " + d if d else ""))
        if not changed:
            return m.group(0)
        n[0] += 1
        return m.group(1) + m.group(2) + ", ".join(parts) + m.group(2)

    def tag(m):
        t = m.group(0)
        if re.match(r"<base\b", t, re.I):
            return t
        t = ATTR.sub(attr, t)
        return SRCSET.sub(srcset, t)

    out = []
    pos = 0
    for m in SKIP_BLOCK.finditer(text):
        seg = text[pos:m.start()]
        # the opening <script src="..."> tag itself carries a src to fix
        out.append(TAG.sub(tag, seg))
        blk = m.group(1)
        open_end = blk.find(">") + 1
        out.append(TAG.sub(tag, blk[:open_end]) + blk[open_end:])
        pos = m.end()
    out.append(TAG.sub(tag, text[pos:]))
    return "".join(out), n[0]


def relative_links(text: str) -> list[str]:
    """Path-relative link values left in tags (outside script/style/textarea), for tests."""
    bare = SKIP_BLOCK.sub(lambda m: m.group(1)[: m.group(1).find(">") + 1], text)
    found = []
    for t in TAG.findall(bare):
        if re.match(r"<base\b", t, re.I):
            continue
        found += [m.group(3) for m in ATTR.finditer(t) if is_rel(m.group(3))]
        for m in SRCSET.finditer(t):
            found += [s.strip().partition(" ")[0] for s in m.group(3).split(",") if s.strip() and is_rel(s.strip().partition(" ")[0])]
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    site = Path(a.site).resolve()
    files = changed = links = 0
    left = []
    for p in sorted(site.rglob("*.html")):
        files += 1
        t = p.read_text(encoding="utf-8", errors="surrogateescape")
        if a.check:
            r = relative_links(t)
            if r:
                left.append((p.relative_to(site).as_posix(), r[:3]))
            continue
        new, n = fix_html(t, page_url(site, p))
        if new != t:
            p.write_text(new, encoding="utf-8", errors="surrogateescape")
            changed += 1; links += n
    if a.check:
        print(f'{{"check":"absolutize_links","files":{files},"pages_with_relative_links":{len(left)}}}')
        for x in left[:10]:
            print("  ", x)
        return 1 if left else 0
    print(f'{{"absolutize_links":true,"files":{files},"changed":{changed},"links":{links}}}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
