#!/usr/bin/env python3
"""Higher-timeframe honesty check for every generator target (data.higher_timeframe + timeframeRef).
- backtrader, Backtesting.py, NautilusTrader: real values from closed higher-timeframe bars (their library checks run
  them; see check_backtrader.py / check_backtesting_py.py / check_nautilus.py) — no unsupported-block TODO here.
- every other target: each block that uses a higher timeframe is an unsupported stub with a TODO line, so nothing is
  computed on the chart timeframe. A timeframe the generator cannot read (e.g. weekly) is unsupported everywhere."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_live_toolkit as blt  # noqa: E402
REAL = {"backtrader", "backtesting-py", "nautilus"}
import build_request_market as brm  # noqa: E402
src = (ROOT / "trader-toolkit/generator/render.mjs").read_text()
m = re.search(r"function htfRealTargets\(\) \{ return \[([^\]]*)\]", src)
checks = failures = 0
def ok(c, m):
    global checks, failures
    checks += 1
    if not c: failures += 1; print("FAIL", m, file=sys.stderr)
ok(m and set(re.findall(r"'([a-z0-9-]+)'", m[1])) == REAL == set(brm.HTF_REAL), "generator, coverage.json and this check agree on the real higher-timeframe targets")
def render(path, t):
    return subprocess.run(["node", str(ROOT / "trader-toolkit/generator/render.mjs"), str(path), "--target", t], capture_output=True, text=True, check=True).stdout
recipes = [p for p in sorted((ROOT / "trader-toolkit/recipes").glob("*.json")) if any((b.get("params") or {}).get("timeframeRef") for b in json.loads(p.read_text())["blocks"])]
ok(recipes, "at least one recipe uses a higher timeframe")
tmp = Path(tempfile.mkdtemp(prefix="bsv-htf-"))
for p in recipes:
    r = json.loads(p.read_text()); refs = [b for b in r["blocks"] if (b.get("params") or {}).get("timeframeRef")]
    weekly = json.loads(p.read_text())
    for b in weekly["blocks"]:
        if b["type"] == "data.higher_timeframe": b["params"]["timeframe"] = "W"
    wp = tmp / p.name; wp.write_text(json.dumps(weekly))
    for t, _, _ in blt.TARGETS:
        out = render(p, t)
        stub = [b["id"] for b in refs if not re.search(rf"TODO unsupported block data\.higher_timeframe: {re.escape(b['id'])}\b", out)]
        if t in REAL:
            ok(not stub or len(stub) == len(refs), f"{p.stem} {t}: all or none")
            ok(len(stub) == len(refs) and "BsvHtf(" in out and "closed bars only" in out, f"{p.stem} {t}: real higher-timeframe values (no stub)")
        else:
            ok(not stub, f"{p.stem} {t}: every higher-timeframe block is an unsupported stub with a TODO line ({stub} missing)")
            ok("BsvHtf(" not in out, f"{p.stem} {t}: no higher-timeframe helper claimed")
        wout = render(wp, t)
        ok(all(re.search(rf"TODO unsupported block data\.higher_timeframe: {re.escape(b['id'])}\b", wout) for b in refs), f"{p.stem} {t}: weekly timeframe (not readable) is unsupported")
print(json.dumps({"check": "higher-timeframe", "recipes": len(recipes), "targets": len(blt.TARGETS), "real": sorted(REAL), "checks": checks, "failures": failures}))
sys.exit(1 if failures else 0)
