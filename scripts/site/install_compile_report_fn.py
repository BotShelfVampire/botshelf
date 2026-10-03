#!/usr/bin/env python3
"""Copy BSV site functions (site-functions/compile-report.js, site-functions/demand-request.js) into
<root>/netlify/functions/ (idempotent). The deploy root's existing functions (commerce, license, free-*) are not
touched. Usage: --root <deploy root> [--check]"""
import argparse, filecmp, shutil, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
FILES = ["compile-report.js", "demand-request.js"]
ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); ap.add_argument("--check", action="store_true")
a = ap.parse_args()
if not (Path(a.root) / "netlify/functions/_lib/session.js").exists(): sys.exit("not a deploy root (missing netlify/functions/_lib/session.js)")
out, stale = {}, False
for f in FILES:
    src = REPO / "site-functions" / f; dst = Path(a.root) / "netlify/functions" / f
    same = dst.exists() and filecmp.cmp(src, dst, shallow=False)
    stale |= not same
    if not a.check and not same: shutil.copyfile(src, dst)
    out[f] = "current" if same else ("stale" if a.check else "installed")
print(out)
if a.check: sys.exit(1 if stale else 0)
