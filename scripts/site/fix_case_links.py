#!/usr/bin/env python3
"""Make internal links match the exact case of the shipped file.

Netlify serves paths case-insensitively, so /x/README.md answers 200 even
though the deployed tree stores readme.md. Local checkers, mirrors and
crawlers are case-sensitive and report such links as missing (QC: 15
research-desk-local sample links). For every root-absolute href/src whose
exact path does not exist but exactly one case-insensitive match does, the
link is rewritten to the shipped name. Visible text is not changed.
Idempotent. --check exits 1 if anything would change.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ATTR = re.compile(r'(\s(?:href|src)=")(/[^"#?]*)([^"]*")')


def build_index(site: Path) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = {}
    for p in site.rglob("*"):
        if "node_modules" in p.parts or ".git" in p.parts:
            continue
        rel = "/" + p.relative_to(site).as_posix() + ("/" if p.is_dir() else "")
        idx.setdefault(rel.lower(), []).append(rel)
    return idx


def fix_text(text: str, site: Path, idx: dict) -> tuple[str, int]:
    n = 0

    def sub(m):
        nonlocal n
        path = m.group(2)
        if path.startswith("//") or (site / path.lstrip("/")).exists():
            return m.group(0)
        hits = idx.get(path.lower(), [])
        if len(hits) == 1 and hits[0] != path:
            n += 1
            return m.group(1) + hits[0] + m.group(3)
        return m.group(0)

    return ATTR.sub(sub, text), n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    site = Path(a.site)
    idx = build_index(site)
    files = links = 0
    for p in site.rglob("*.html"):
        if "node_modules" in p.parts:
            continue
        t = p.read_text(errors="surrogateescape")
        t2, n = fix_text(t, site, idx)
        if n:
            files += 1
            links += n
            print(f"{p.relative_to(site)}: {n}")
            if not a.check:
                p.write_text(t2, errors="surrogateescape")
    print(f"case-fixed links: {links} in {files} files{' (check)' if a.check else ''}")
    return 1 if (a.check and links) else 0


if __name__ == "__main__":
    sys.exit(main())
