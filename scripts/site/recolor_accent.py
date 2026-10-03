#!/usr/bin/env python3
"""Replace gold accents in the site's CSS with the green accent, under new hashed file names.

Owner rule: no gold-themed surfaces. CSS is cached immutable for a year, so recoloured files get a new
name (<stem>.g<sha8>.css) and every HTML <link> that points at an old file is rewritten.
- Primary gold accents (#d4b45a, #dfc583, #d4b675, #c9a227 and their rgba forms) -> #bad4b7 / rgba(186,212,183,a).
- Other gold-hued colours keep their lightness (so contrast stays the same) and move to the green hue.
Idempotent; run after externalize_inline_styles.py.
Usage: python3 scripts/site/recolor_accent.py --site <site> [--check]
"""
import argparse, colorsys, hashlib, json, re, sys
from pathlib import Path

GREEN = (186, 212, 183)
PRIMARY = {(212, 180, 90), (223, 197, 131), (212, 182, 117), (201, 162, 39), (212, 175, 55)}
BG = (7, 8, 10)  # darkest site background
GH, GS = colorsys.rgb_to_hls(*(c / 255 for c in GREEN))[0], 0.26
HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGB = re.compile(r"(rgba?\(\s*)(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")
LINK = re.compile(r'(<link\b[^>]*?\bhref=")([^"]+?\.css)((?:\?[^"]*)?")')
SKIP = re.compile(r"\.g[0-9a-f]{8}\.css$")


def is_gold(rgb):
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return 30 / 360 <= h <= 60 / 360 and s > 0.3 and 0.3 < l < 0.9


def to_green(rgb):
    if rgb in PRIMARY:
        return GREEN
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    target = contrast(rgb, BG)
    while True:  # keep at least the original contrast against the dark page background
        out = tuple(round(x * 255) for x in colorsys.hls_to_rgb(GH, l, min(s, GS)))
        if contrast(out, BG) >= target or l >= 0.95:
            return out
        l += 0.005


def _lum(c):
    v = [x / 255 for x in c]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def contrast(a, b):
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def recolor(css):
    n = [0]

    def hx(m):
        v = m.group(1)
        v = "".join(c * 2 for c in v) if len(v) == 3 else v
        rgb = tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
        if not is_gold(rgb):
            return m.group(0)
        n[0] += 1
        return "#%02x%02x%02x" % to_green(rgb)

    def rg(m):
        rgb = tuple(int(m.group(i)) for i in (2, 3, 4))
        if max(rgb) > 255 or not is_gold(rgb):
            return m.group(0)
        n[0] += 1
        return m.group(1) + "%d,%d,%d" % to_green(rgb)
    return RGB.sub(rg, HEX.sub(hx, css)), n[0]


def resolve(site, page, href):
    if href.startswith(("http:", "https:", "//", "data:")):
        return None
    f = (site / href.lstrip("/")) if href.startswith("/") else (page.parent / href)
    try:
        return f.resolve().relative_to(site.resolve())
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--check", action="store_true", help="report referenced CSS that still contains gold")
    a = ap.parse_args()
    site = Path(a.site)
    pages = [p for p in site.rglob("*.html") if "node_modules" not in p.parts]
    newname, cache, remaining, changed_pages = {}, {}, set(), 0

    def target(rel):
        if rel in cache:
            return cache[rel]
        f = site / rel
        res = None
        if f.exists() and not SKIP.search(f.name):
            css, n = recolor(f.read_text(encoding="utf-8", errors="surrogateescape"))
            if n:
                if a.check:
                    remaining.add(str(rel))
                else:
                    name = f"{f.name[:-4]}.g{hashlib.sha256(css.encode('utf-8', 'surrogateescape')).hexdigest()[:8]}.css"
                    (f.parent / name).write_text(css, encoding="utf-8", errors="surrogateescape")
                    newname[str(rel)] = (name, n)
                    res = name
        cache[rel] = res
        return res
    for p in pages:
        t = p.read_text(encoding="utf-8", errors="surrogateescape")
        if ".css" not in t:
            continue

        def rep(m):
            rel = resolve(site, p, m.group(2))
            name = target(rel) if rel else None
            if not name:
                return m.group(0)
            href = m.group(2)
            return m.group(1) + href[: href.rfind("/") + 1] + name + m.group(3)
        t2 = LINK.sub(rep, t)
        if t2 != t and not a.check:
            p.write_text(t2, encoding="utf-8", errors="surrogateescape")
            changed_pages += 1
    if a.check:
        print(json.dumps({"referenced_css_with_gold": sorted(remaining)}))
        return 1 if remaining else 0
    print(json.dumps({"pages_edited": changed_pages, "css_recoloured": {k: {"as": v[0], "colours": v[1]} for k, v in sorted(newname.items())}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
