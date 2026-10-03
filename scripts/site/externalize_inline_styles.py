#!/usr/bin/env python3
"""Move inline <style> blocks and style="" attributes out of HTML so pages work under the
production CSP (style-src 'self'). Idempotent; run last in the site pipeline.

- Each distinct <style> block -> /assets/inline/bsv-inline.<sha10>.css, replaced in place by a <link>
  (same position, so the cascade order is unchanged).
- Gold accents inside those blocks are replaced with the green accent (#bad4b7).
- style="..." attributes -> class "bsv-s-<sha8>" with the same declarations marked !important
  (inline styles beat author rules, so !important keeps the original precedence);
  rules ship in /assets/inline/bsv-attrs.<sha10>.css linked before </head>.
Usage: python3 scripts/site/externalize_inline_styles.py --site <site> [--check]
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

GOLD = [(re.compile(r"#c9a227", re.I), "#bad4b7"), (re.compile(r"rgba\(\s*201\s*,\s*162\s*,\s*39\s*,"), "rgba(186,212,183,")]
STYLE_RE = re.compile(r"<style(\s[^>]*)?>(.*?)</style>", re.S | re.I)
TAG_RE = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)(\s[^<>]*?)?\sstyle=\"([^\"]*)\"([^<>]*)>")
SKIP_DIRS = ("node_modules/",)


def h(s, n):
    return hashlib.sha256(s.encode()).hexdigest()[:n]


def green(css):
    for rx, rep in GOLD:
        css = rx.sub(rep, css)
    return css


def important(decls):
    out = []
    for d in decls.split(";"):
        d = d.strip()
        if not d or ":" not in d:
            continue
        out.append(d if d.endswith("!important") else d + " !important")
    return ";".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--check", action="store_true", help="only report remaining inline styles")
    a = ap.parse_args()
    site = Path(a.site)
    outdir = site / "assets/inline"
    pages = [p for p in site.rglob("*.html") if not any(s in str(p) for s in SKIP_DIRS)]
    blocks, attr_rules, edited, remaining = {}, {}, 0, []
    for p in pages:
        t = p.read_text(encoding="utf-8", errors="surrogateescape")
        if "<style" not in t and "style=\"" not in t:
            continue
        if a.check:
            if STYLE_RE.search(t) or TAG_RE.search(t):
                remaining.append(str(p.relative_to(site)))
            continue
        orig = t

        def rep_block(m):
            attrs = m.group(1) or ""
            css = green(m.group(2))
            name = f"bsv-inline.{h(css, 10)}.css"
            blocks[name] = css
            media = re.search(r"\smedia=\"[^\"]*\"", attrs)
            return f'<link rel="stylesheet" href="/assets/inline/{name}"{media.group(0) if media else ""}>'
        t = STYLE_RE.sub(rep_block, t)
        used = set()

        def rep_tag(m):
            tag, before, decls, after = m.group(1), m.group(2) or "", m.group(3), m.group(4)
            rule = important(green(decls))
            if not rule:
                return f"<{tag}{before}{after}>"
            cls = "bsv-s-" + h(rule, 8)
            attr_rules[cls] = rule
            used.add(cls)
            rest = before + after
            cm = re.search(r'\sclass="([^"]*)"', rest)
            if cm:
                rest = rest[:cm.start()] + f' class="{cm.group(1)} {cls}"' + rest[cm.end():]
            else:
                rest = f' class="{cls}"' + rest
            return f"<{tag}{rest}>"
        while TAG_RE.search(t):
            t = TAG_RE.sub(rep_tag, t)
        if used:
            t = t.replace("</head>", "<!--BSV-ATTRS-CSS--></head>", 1)
        if t != orig:
            p.write_text(t, encoding="utf-8", errors="surrogateescape")
            edited += 1
    if a.check:
        print(json.dumps({"pages_with_inline_style": len(remaining), "sample": remaining[:10]}))
        return 1 if remaining else 0
    outdir.mkdir(parents=True, exist_ok=True)
    for name, css in blocks.items():
        (outdir / name).write_text(css, encoding="utf-8")
    attrs_name = None
    if attr_rules:
        css = "".join(f".{c}{{{r}}}\n" for c, r in sorted(attr_rules.items()))
        attrs_name = f"bsv-attrs.{h(css, 10)}.css"
        (outdir / attrs_name).write_text(css, encoding="utf-8")
    # resolve placeholders to the attrs stylesheet built in this run
    if attrs_name:
        for p in pages:
            t = p.read_text(encoding="utf-8", errors="surrogateescape")
            if "<!--BSV-ATTRS-CSS-->" in t:
                p.write_text(t.replace("<!--BSV-ATTRS-CSS-->", f'<link rel="stylesheet" href="/assets/inline/{attrs_name}">'), encoding="utf-8", errors="surrogateescape")
    print(json.dumps({"pages_edited": edited, "style_files": len(blocks), "attr_classes": len(attr_rules), "attrs_css": attrs_name}))


if __name__ == "__main__":
    sys.exit(main())
