#!/usr/bin/env python3
"""One-shot: replace bilingual Search / 検索 nav with data-i18n=navSearch; patch i18n*.js COMMON."""
from pathlib import Path
import re, sys
NAV = {"en": "Search", "ja": "検索", "es": "Buscar", "zh": "搜索", "ko": "검색"}
REPL = [
    ('<a href="/search/" class="nav-search">Search / 検索</a>',
     '<a href="/search/" class="nav-search" data-i18n="navSearch">Search</a>'),
    ('<a href="/search/">Search / 検索</a>',
     '<a href="/search/" data-i18n="navSearch">Search</a>'),
]
def fix_html(root: Path):
    n = 0
    for p in root.rglob("*.html"):
        t = p.read_text(errors="replace"); o = t
        for a, b in REPL: t = t.replace(a, b)
        if t != o: p.write_text(t); n += 1
    return n
def patch_i18n(path: Path) -> bool:
    t = path.read_text()
    if "navSearch:" in t: return False
    lines, out, cur, added = t.splitlines(True), [], None, 0
    for i, line in enumerate(lines):
        m = re.match(r"\s*(en|ja|es|zh|ko)\s*:\s*\{", line)
        if m: cur = m.group(1)
        if cur and re.match(r"\s*navRegister:\s*", line) and (i + 1 >= len(lines) or "navSearch" not in lines[i + 1]):
            out.append(line)
            ind = re.match(r"(\s*)", line).group(1)
            out.append(f'{ind}navSearch: "{NAV[cur]}",\n'); added += 1; continue
        out.append(line)
    if added != 5: raise SystemExit(f"{path}: expected 5 inserts, got {added}")
    path.write_text("".join(out)); return True
def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print("html", fix_html(root))
    js = root / "js"
    if js.is_dir():
        for p in sorted(js.glob("i18n*.js")):
            print(p.name, "patched" if patch_i18n(p) else "skip")
if __name__ == "__main__":
    main()
