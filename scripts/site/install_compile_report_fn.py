#!/usr/bin/env python3
"""Copy site-functions/compile-report.js into <root>/netlify/functions/ (idempotent).
The deploy root's existing functions (commerce, license, free-*) are not touched. Usage: --root <deploy root>"""
import argparse, filecmp, shutil, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); ap.add_argument("--check", action="store_true")
a = ap.parse_args()
src = REPO / "site-functions/compile-report.js"; dst = Path(a.root) / "netlify/functions/compile-report.js"
if not (Path(a.root) / "netlify/functions/_lib/session.js").exists(): sys.exit("not a deploy root (missing netlify/functions/_lib/session.js)")
same = dst.exists() and filecmp.cmp(src, dst, shallow=False)
if a.check: print({"compile_report_fn_current": same}); sys.exit(0 if same else 1)
if not same: shutil.copyfile(src, dst)
print({"installed": str(dst), "changed": not same})
