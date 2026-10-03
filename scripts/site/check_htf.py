#!/usr/bin/env python3
"""Higher-timeframe honesty check for every generator target (data.higher_timeframe + timeframeRef).
- backtrader, Backtesting.py, NautilusTrader: real values from closed higher-timeframe bars (their library checks run
  them; see check_backtrader.py / check_backtesting_py.py / check_nautilus.py) — no unsupported-block TODO here.
- Pine v6, MQL5, MQL4: real values through each platform's officially documented closed-bar idiom. BSV cannot run these
  platforms, so this script enforces the pattern statically (and proves the static check catches broken variants):
    Pine : every request.security(...) reads expr[1] with lookahead = barmerge.lookahead_on, plus a runtime.error guard
           when the chart timeframe is not lower (https://www.tradingview.com/pine-script-docs/concepts/repainting/).
    MQL5 : iBarShift(_Symbol, tf, iTime(chart bar), false) + 1 as CopyBuffer start_pos = last closed higher bar; the
           handle is created on that PERIOD; OnInit fails when the chart period is not lower.
    MQL4 : iBarShift(NULL, tf, iTime(NULL, 0, i), false) + 1 as the shift of iMA/iRSI/iATR on that PERIOD; same guard.
  A timeframe the target cannot name (e.g. 45 minutes on MT4/MT5) stays a TODO stub there.
- every other target: each block that uses a higher timeframe is an unsupported stub with a TODO line, so nothing is
  computed on the chart timeframe. A timeframe the generator cannot read (e.g. weekly "W") is unsupported everywhere."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_live_toolkit as blt  # noqa: E402
import build_request_market as brm  # noqa: E402
REAL = {"backtrader", "backtesting-py", "nautilus"}
IDIOM = {"pine-v6", "mql5", "mql4"}
src = (ROOT / "trader-toolkit/generator/render.mjs").read_text()
checks = failures = 0
def ok(c, m):
    global checks, failures
    checks += 1
    if not c: failures += 1; print("FAIL", m, file=sys.stderr)
def listed(fn):
    m = re.search(rf"function {fn}\(\) \{{ return \[([^\]]*)\]", src)
    return set(re.findall(r"'([a-z0-9-]+)'", m[1])) if m else None
ok(listed("htfRealTargets") == REAL == set(brm.HTF_REAL), "generator, coverage.json and this check agree on the library-checked higher-timeframe targets")
ok(listed("htfIdiomTargets") == IDIOM == set(brm.HTF_IDIOM), "generator, coverage.json and this check agree on the documented-idiom higher-timeframe targets")

def pine_problems(out, ids):
    """Closed-bar rule for Pine v6: [1] on the requested expression + lookahead_on, and a guard per timeframe."""
    p = []
    code = "\n".join(l for l in out.splitlines() if not l.lstrip().startswith("//"))
    calls = re.findall(r"request\.security\((.*)\)\s*$", code, re.M)
    for c in calls:
        if not re.fullmatch(r'syminfo\.tickerid, "(\d+D?)", .+\[1\], lookahead = barmerge\.lookahead_on', c): p.append(f"request.security without expr[1] + lookahead_on: {c}")
    for i in ids:
        m = re.search(rf'^{re.escape(i)} = request\.security\(syminfo\.tickerid, "(\d+D?)", .+\[1\], lookahead = barmerge\.lookahead_on\)$', out, re.M)
        if not m: p.append(f"{i}: not read with the closed-bar idiom"); continue
        if not re.search(rf'^if timeframe\.in_seconds\(\) >= timeframe\.in_seconds\("{m[1]}"\)\n    runtime\.error\(', out, re.M): p.append(f"{i}: no guard for timeframe {m[1]}")
    if len(re.findall(r"\blookahead\b", code)) != len(calls) or len(re.findall(r"lookahead_on", code)) != len(calls): p.append("lookahead_on outside a checked request.security call")
    return p

def mql5_problems(out, ids):
    p = []
    if not re.search(r"double BsvHtfAt\(int handle, ENUM_TIMEFRAMES tf, int i\)\n\{\n   int s = iBarShift\(_Symbol, tf, iTime\(_Symbol, _Period, i\), false\);\n   if \(s < 0\) return\(EMPTY_VALUE\);\n   double v\[1\];\n   if \(CopyBuffer\(handle, 0, s \+ 1, 1, v\) != 1\) return\(EMPTY_VALUE\);", out): p.append("BsvHtfAt is not iBarShift + 1 (last closed higher bar)")
    for i in ids:
        m = re.search(rf"^double V_{re.escape(i)}\(int i\) \{{ return BsvHtfAt\(h_{re.escape(i)}, (PERIOD_\w+), i\); \}}", out, re.M)
        if not m: p.append(f"{i}: not read through BsvHtfAt"); continue
        if not re.search(rf"^   h_{re.escape(i)} = i(MA|RSI|ATR)\(_Symbol, {m[1]}, ", out, re.M): p.append(f"{i}: handle not on {m[1]}")
        if not re.search(rf"^   if \(PeriodSeconds\({m[1]}\) <= PeriodSeconds\(_Period\)\) \{{ Print\(.*\); return\(INIT_FAILED\); \}}", out, re.M): p.append(f"{i}: no guard for {m[1]}")
        if re.search(rf"CopyBuffer\(h_{re.escape(i)},", out): p.append(f"{i}: higher-timeframe handle copied from the newest bar")
    return p

def mql4_problems(out, ids):
    p = []
    if "int BsvHtfShift(int tf, int i) { int s = iBarShift(NULL, tf, iTime(NULL, 0, i), false); return s < 0 ? -1 : s + 1; }" not in out: p.append("BsvHtfShift is not iBarShift + 1 (last closed higher bar)")
    for i in ids:
        m = re.search(rf"^double V_{re.escape(i)}\(int i\) \{{ int k = BsvHtfShift\((PERIOD_\w+), i\); return k < 1 \? \(double\)EMPTY_VALUE : i(MA|RSI|ATR)\(NULL, (PERIOD_\w+), [^;]*, k\); \}}", out, re.M)
        if not m or m[1] != m[3]: p.append(f"{i}: not read at the BsvHtfShift shift on the same period"); continue
        if not re.search(rf"^   if \(PeriodSeconds\({m[1]}\) <= PeriodSeconds\(\)\) \{{ Alert\(.*\); return\(INIT_FAILED\); \}}", out, re.M): p.append(f"{i}: no guard for {m[1]}")
    for c in re.findall(r"i(?:MA|RSI|ATR)\(NULL, (PERIOD_\w+), [^;]*?, (\w+)\)", out):
        if c[1] != "k": p.append(f"higher-timeframe indicator call not at the closed-bar shift: {c}")
    return p

PROBLEMS = {"pine-v6": pine_problems, "mql5": mql5_problems, "mql4": mql4_problems}
# Each mutant breaks the closed-bar rule; the static check must catch every one (otherwise it proves nothing).
MUTANTS = {
    "pine-v6": [("drop [1]", lambda o: o.replace(")[1], lookahead", "), lookahead")), ("lookahead off", lambda o: o.replace("lookahead_on", "lookahead_off")),
                ("no lookahead arg", lambda o: re.sub(r", lookahead = barmerge\.lookahead_on\)", ")", o)), ("no guard", lambda o: re.sub(r"if timeframe\.in_seconds.*\n    runtime\.error.*\n", "", o)),
                ("guard >", lambda o: o.replace("timeframe.in_seconds() >= ", "timeframe.in_seconds() > "))],
    "mql5": [("shift s", lambda o: o.replace("CopyBuffer(handle, 0, s + 1, 1, v)", "CopyBuffer(handle, 0, s, 1, v)")), ("exact true", lambda o: o.replace("i), false);", "i), true);")),
             ("chart period handle", lambda o: re.sub(r"(h_\w+ = i(?:MA|RSI|ATR)\(_Symbol, )PERIOD_\w+", r"\1_Period", o)), ("no guard", lambda o: re.sub(r"   if \(PeriodSeconds\(PERIOD.*\n", "", o)),
             ("newest-bar copy", lambda o: o.replace("   if (BarsCalculated(h_", "   CopyBuffer(h_ema, 0, 0, 1, v);\n   if (BarsCalculated(h_", 1))],
    "mql4": [("shift s", lambda o: o.replace("return s < 0 ? -1 : s + 1;", "return s < 0 ? -1 : s;")), ("shift i", lambda o: re.sub(r"(i(?:MA|RSI|ATR)\(NULL, PERIOD_\w+, [^;]*), k\)", r"\1, i)", o)),
             ("other period", lambda o: o.replace("iMA(NULL, PERIOD_H1", "iMA(NULL, PERIOD_H4")), ("no guard", lambda o: re.sub(r"   if \(PeriodSeconds\(PERIOD.*\n", "", o))],
}
def render(path, t):
    return subprocess.run(["node", str(ROOT / "trader-toolkit/generator/render.mjs"), str(path), "--target", t], capture_output=True, text=True, check=True).stdout
recipes = [p for p in sorted((ROOT / "trader-toolkit/recipes").glob("*.json")) if any((b.get("params") or {}).get("timeframeRef") for b in json.loads(p.read_text())["blocks"])]
ok(recipes, "at least one recipe uses a higher timeframe")
tmp = Path(tempfile.mkdtemp(prefix="bsv-htf-"))
def variant(p, tf):
    r = json.loads(p.read_text())
    for b in r["blocks"]:
        if b["type"] == "data.higher_timeframe": b["params"]["timeframe"] = tf
    vp = tmp / f"{p.stem}-{tf}.json"; vp.write_text(json.dumps(r)); return vp
stubre = lambda i: rf"TODO unsupported block data\.higher_timeframe: {re.escape(i)}\b"
for p in recipes:
    r = json.loads(p.read_text()); refs = [b["id"] for b in r["blocks"] if (b.get("params") or {}).get("timeframeRef")]
    weekly, m45, daily = variant(p, "W"), variant(p, "45"), variant(p, "D")
    for t, _, _ in blt.TARGETS:
        out = render(p, t)
        stub = [i for i in refs if re.search(stubre(i), out)]
        if t in REAL:
            ok(not stub and "BsvHtf(" in out and "closed bars only" in out, f"{p.stem} {t}: real higher-timeframe values (no stub)")
        elif t in IDIOM:
            ok(not stub, f"{p.stem} {t}: real higher-timeframe values (no stub) {stub}")
            ok("BsvHtf(" not in out and "UNTESTED_RUNTIME" in out, f"{p.stem} {t}: documented idiom, labelled not run by BSV")
            probs = PROBLEMS[t](out, refs)
            ok(not probs, f"{p.stem} {t}: closed-bar pattern {probs}")
            for name, mut in MUTANTS[t]:
                mo = mut(out)
                ok(mo != out and PROBLEMS[t](mo, refs), f"{p.stem} {t}: static check catches mutant '{name}'")
            dout = render(daily, t)
            ok(not any(re.search(stubre(i), dout) for i in refs) and not PROBLEMS[t](dout, refs) and ('"1D"' in dout if t == "pine-v6" else "PERIOD_D1" in dout), f"{p.stem} {t}: daily timeframe uses the closed-bar idiom")
            m45out = render(m45, t)
            if t == "pine-v6": ok(not any(re.search(stubre(i), m45out) for i in refs) and '"45"' in m45out and not PROBLEMS[t](m45out, refs), f"{p.stem} {t}: 45 minutes readable on Pine")
            else: ok(all(re.search(stubre(i), m45out) for i in refs) and "BsvHtf" not in m45out, f"{p.stem} {t}: 45 minutes has no MT period, stays a TODO stub")
        else:
            ok(len(stub) == len(refs), f"{p.stem} {t}: every higher-timeframe block is an unsupported stub with a TODO line ({set(refs) - set(stub)} missing)")
            ok("BsvHtf" not in out and "request.security" not in out, f"{p.stem} {t}: no higher-timeframe helper claimed")
        wout = render(weekly, t)
        ok(all(re.search(stubre(i), wout) for i in refs), f"{p.stem} {t}: weekly timeframe (not readable) is unsupported")
print(json.dumps({"check": "higher-timeframe", "recipes": len(recipes), "targets": len(blt.TARGETS), "real": sorted(REAL), "documentedIdiom": sorted(IDIOM), "checks": checks, "failures": failures}))
sys.exit(1 if failures else 0)
