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
    NinjaTrader 8: AddDataSeries in State.Configure, Calculate forced to OnBarClose there (the chart bars then only know the
           last closed bar of the added series), indicator input from that series, values stored per chart bar in
           BarsInProgress 0; DataLoaded throws when the chart timeframe is not lower
           (https://ninjatrader.com/support/helpGuides/nt8/multi-time_frame__instruments.htm).
    cTrader: MarketData.GetBars(TimeFrame.X); index = GetIndexByTime(chart bar open), clamped, then stepped back with the
           OpenTimes indexer while that bar opened after the chart bar's open; value at index - 1. The reference does not
           state GetIndexByTime's rounding, so the step-back makes index - 1 a closed bar under any rounding (worst case one
           extra bar of lag). Indicators take the higher-timeframe series; the chart TimeFrame must be in the generated
           list of strictly lower time frames (https://help.ctrader.com/ctrader-algo/references/Collections/DataSeries/TimeSeries/).
    AmiBroker: TimeFrameSet(sec); H_x = Ref(<indicator>, -1); TimeFrameRestore(); V_x = IIf(Interval() < sec,
           TimeFrameExpand(H_x, sec, expandFirst), Null) — the guide's negative-shift construction
           (https://www.amibroker.com/guide/h_timeframe.html); signals require NOT IsNull. check_amibroker_afl.mjs also
           evaluates it against an hourly reference with a prefix (no-lookahead) test.
    thinkScript: C_x = close(period = AggregationPeriod.X) (only that aggregation), E_x = indicator of it, H_x = E_x[1]
           (previous secondary bar, as High(period = AggregationPeriod.DAY)[1] in the manual), V_x = if bsvHtfOk_X then H_x else
           Double.NaN with bsvHtfOk_X = GetAggregationPeriod() < AggregationPeriod.X; nothing chart-period mixed in
           (https://toslc.thinkorswim.com/center/reference/thinkScript/tutorials/Advanced/Chapter-11---Referencing-Secondary-Aggregation).
           check_thinkscript.mjs models secondary contexts and runs the reference + prefix tests.
  A timeframe the target cannot name (e.g. 45 minutes on MT4/MT5) stays a TODO stub there.
- every other target: each block that uses a higher timeframe is an unsupported stub with a TODO line, so nothing is
  computed on the chart timeframe. A timeframe the generator cannot read (e.g. weekly "W") is unsupported everywhere."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_live_toolkit as blt  # noqa: E402
import build_request_market as brm  # noqa: E402
REAL = {"backtrader", "backtesting-py", "nautilus", "tradovate"}
IDIOM = {"pine-v6", "mql5", "mql4", "ninjatrader", "ctrader", "amibroker", "thinkscript"}
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

def nt_problems(out, ids):
    p = []
    cfg = re.search(r"else if \(State == State\.Configure\)\n            \{\n(.*?)\n            \}", out, re.S)
    cfg = cfg[1] if cfg else ""
    if not re.search(r"^                Calculate = Calculate\.OnBarClose;", cfg, re.M): p.append("Calculate not forced to OnBarClose in State.Configure")
    if re.search(r"Calculate\.On(EachTick|PriceChange)", out): p.append("tick-level Calculate")
    if "            if (BarsInProgress != 0) return;" not in out: p.append("no BarsInProgress filter")
    series = re.findall(r"^                AddDataSeries\((BarsPeriodType\.(?:Minute|Day|Week), \d+)\); // BarsInProgress (\d+)$", cfg, re.M)
    for i in ids:
        m = re.search(rf"^                _{re.escape(i)} = (?:EMA|SMA|RSI)\((?:Opens|Highs|Lows|Closes|Medians|Typicals)\[(\d+)\], |^                _{re.escape(i)} = ATR\(BarsArray\[(\d+)\], ", out, re.M)
        if not m: p.append(f"{i}: indicator input is not an added series"); continue
        k = m[1] or m[2]
        tf = [a for a, n in series if n == k]
        if not tf: p.append(f"{i}: series {k} not added in State.Configure"); continue
        if not re.search(rf"^            _htf_{re.escape(i)}\[0\] = CurrentBars\[{k}\] >= \d+ \? _{re.escape(i)}\[0\] : double\.NaN;", out, re.M): p.append(f"{i}: not stored per chart bar from the added series")
        if not re.search(rf"^        private double V_{re.escape(i)}\(int ago\) \{{ return _htf_{re.escape(i)}\[ago\]; \}}", out, re.M): p.append(f"{i}: V_ does not read the stored closed-bar series")
        kind, n = tf[0].replace("BarsPeriodType.", "").split(", ")
        if not re.search(rf"if \(bsvChartMinutes >= \d+\) throw new ArgumentException\(\"BSV: the higher timeframe {kind} {n} must", out): p.append(f"{i}: no guard for {kind} {n}")
    return p

CT_HELPER = """        private int BsvHtfClosed(Bars htf, int i)
        {
            if (htf.OpenTimes.Count == 0) return -1;
            DateTime t = Bars.OpenTimes[i];
            int k = htf.OpenTimes.GetIndexByTime(t);
            if (k > htf.OpenTimes.Count - 1) k = htf.OpenTimes.Count - 1;
            while (k >= 0 && htf.OpenTimes[k] > t) k--;
            return k - 1;
        }"""
CT_MIN = {"Minute": 1, **{f"Minute{n}": n for n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 45)}, "Hour": 60, **{f"Hour{n}": 60 * n for n in (2, 3, 4, 6, 8, 12)},
          "Daily": 1440, "Day2": 2880, "Day3": 4320, "Weekly": 10080}
def ct_problems(out, ids):
    """cTrader: closed index = (GetIndexByTime stepped back to a bar opened at/before the chart bar) - 1; HTF input; strict-lower guard."""
    p = []
    if CT_HELPER not in out: p.append("BsvHtfClosed is not the stepped-back GetIndexByTime - 1 helper")
    for i in ids:
        m = re.search(rf"^        private double V_{re.escape(i)}\(int i\) \{{ int j = BsvHtfClosed\(_htfBars_(\w+), i\); return \(!_htfOk_\1 \|\| j < \d+\) \? double\.NaN : _{re.escape(i)}\.Result\[j\]; \}}", out, re.M)
        if not m: p.append(f"{i}: not read at the closed higher-timeframe index"); continue
        n = m[1]
        if n not in CT_MIN or not re.search(rf"^            _htfBars_{n} = MarketData\.GetBars\(TimeFrame\.{n}\);$", out, re.M): p.append(f"{i}: bars for {n} not from MarketData.GetBars"); continue
        if not re.search(rf"^            _{re.escape(i)} = Indicators\.(?:(?:ExponentialMovingAverage|SimpleMovingAverage|RelativeStrengthIndex)\(_htfBars_{n}\.\w+Prices, |AverageTrueRange\(_htfBars_{n}, )", out, re.M): p.append(f"{i}: indicator input is not the {n} series")
        g = re.search(rf"^            _htfOk_{n} = Array\.IndexOf\(new\[\] \{{ ([^}}]*) \}}, TimeFrame\) >= 0;", out, re.M)
        lower = [x.replace("TimeFrame.", "") for x in g[1].split(", ")] if g else []
        if not g or not lower or any(CT_MIN.get(x, 10 ** 9) >= CT_MIN[n] for x in lower): p.append(f"{i}: no strict lower-timeframe guard for {n}")
    for i in ids:
        if re.search(rf"_{re.escape(i)}\.Result\[(?!j\])", out) or re.search(rf"_{re.escape(i)}\.Result\.Last", out): p.append(f"{i}: higher-timeframe result read at a chart index or the newest bar")
    return p

def afl_problems(out, ids):
    """AmiBroker: Ref(x, -1) inside TimeFrameSet/Restore, expanded with expandFirst on the same interval, Null unless the chart is shorter."""
    p = []
    code = "\n".join(l for l in out.splitlines() if not l.lstrip().startswith("//"))
    if re.search(r"expandLast|expandPoint|TimeFrameGetPrice|TimeFrameCompress", code): p.append("other expand/compress mode used")
    blocks = re.findall(r"^TimeFrameSet\((\w+)\);\n((?:H_\w+ = .*\n)*)TimeFrameRestore\(\);$", code, re.M)
    inblock = {m: iv for iv, body in blocks for m in re.findall(r"^H_(\w+) = ", body, re.M)}
    for iv, body in blocks:
        for line in body.splitlines():
            SRC = r"(?:Open|High|Low|Close|\(High \+ Low\) / 2|\(High \+ Low \+ Close\) / 3|\(Open \+ High \+ Low \+ Close\) / 4)"
            if not (re.fullmatch(rf"H_\w+ = Ref\((?:EMA|MA|RSIa)\({SRC}, \d+\), -1\);", line) or re.fullmatch(r"H_\w+ = Ref\(ATR\(\d+\), -1\);", line)):
                p.append(f"not Ref(<indicator>, -1) in the higher time frame: {line}")
    if len(re.findall(r"^TimeFrameSet\(", code, re.M)) != len(blocks) or len(re.findall(r"^TimeFrameRestore\(", code, re.M)) != len(blocks): p.append("TimeFrameSet/Restore not paired around Ref assignments only")
    for i in ids:
        iv = inblock.get(i)
        if not iv: p.append(f"{i}: not computed as Ref(x, -1) inside TimeFrameSet"); continue
        sec = "86400" if iv == "inDaily" else iv
        if not re.search(rf"^V_{re.escape(i)} = IIf\(Interval\(\) < {sec}, TimeFrameExpand\(H_{re.escape(i)}, {iv}, expandFirst\), Null\);$", code, re.M): p.append(f"{i}: not expanded with expandFirst behind the shorter-chart guard")
        for line in re.findall(rf"^S_\w+ = .*\bV_{re.escape(i)}\b.*$", code, re.M):
            if f"NOT IsNull(V_{i})" not in line: p.append(f"{i}: signal without NOT IsNull guard: {line}")
    return p

def ts_problems(out, ids):
    """thinkScript: secondary-only chain C_/E_ -> H_x = E_x[1] -> guarded V_x; no chart-period price in the chain; V_x not offset again."""
    p = []
    code = "\n".join(l.split("#")[0].rstrip() for l in out.splitlines())
    for i in ids:
        e = re.escape(i)
        m = re.search(rf"^def V_{e} = if bsvHtfOk_(\w+) then H_{e} else Double\.NaN;$", code, re.M)
        if not m: p.append(f"{i}: V_ is not the guarded closed value"); continue
        g = m[1]
        if not re.search(rf"^def bsvHtfOk_{g} = GetAggregationPeriod\(\) < AggregationPeriod\.{g};$", code, re.M): p.append(f"{i}: no shorter-chart guard for {g}")
        if not re.search(rf"^def H_{e} = E_{e}\[1\];$", code, re.M): p.append(f"{i}: H_ is not E_[1] (previous secondary bar)")
        chain = [l for l in code.splitlines() if re.match(rf"def (?:C|U|D|E)_{e} = ", l)]
        if not chain: p.append(f"{i}: no secondary chain"); continue
        for l in chain:
            rhs = l.split(" = ", 1)[1]
            if re.search(r"\b(?:open|high|low|close)\b(?!\(period = AggregationPeriod\.)", rhs) or set(re.findall(r"AggregationPeriod\.(\w+)", rhs)) - {g}: p.append(f"{i}: chart-period price or another aggregation in the secondary chain: {l}")
            if re.search(r"\bV_|\bH_", rhs): p.append(f"{i}: secondary chain reads a shown value: {l}")
    return p

PROBLEMS = {"thinkscript": ts_problems, "pine-v6": pine_problems, "mql5": mql5_problems, "mql4": mql4_problems, "ninjatrader": nt_problems, "ctrader": ct_problems, "amibroker": afl_problems}
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
    "ninjatrader": [("OnEachTick", lambda o: o.replace("                Calculate = Calculate.OnBarClose; // forced", "                Calculate = Calculate.OnEachTick; // forced")),
                    ("Calculate not forced", lambda o: o.replace("                Calculate = Calculate.OnBarClose; // forced", "                // forced")),
                    ("no BarsInProgress filter", lambda o: o.replace("            if (BarsInProgress != 0) return;", "")),
                    ("chart-series input", lambda o: re.sub(r"(_\w+ = (?:EMA|SMA|RSI)\()Closes\[\d+\]", r"\1Close", o)),
                    ("read HTF indicator directly", lambda o: re.sub(r"return _htf_(\w+)\[ago\];", r"return _\1[ago];", o)),
                    ("no guard", lambda o: re.sub(r"                if \(bsvChartMinutes.*\n", "", o))],
    "ctrader": [("bare GetIndexByTime (no step-back)", lambda o: o.replace("            while (k >= 0 && htf.OpenTimes[k] > t) k--;\n", "")),
                ("index not minus 1", lambda o: o.replace("            return k - 1;", "            return k;")),
                ("chart index", lambda o: re.sub(r"\.Result\[j\]; \}", ".Result[i]; }", o)),
                ("newest bar", lambda o: re.sub(r"\.Result\[j\]; \}", ".Result.LastValue; }", o)),
                ("chart-series input", lambda o: re.sub(r"(Indicators\.\w+\()_htfBars_\w+\.ClosePrices", r"\1Bars.ClosePrices", o)),
                ("guard allows the same timeframe", lambda o: o.replace("TimeFrame.Minute45 }", "TimeFrame.Minute45, TimeFrame.Hour }")),
                ("guard not used", lambda o: re.sub(r"\(!_htfOk_\w+ \|\| ", "(", o))],
    "thinkscript": [("no [1]", lambda o: re.sub(r"^def (H_\w+) = (E_\w+)\[1\];", r"def \1 = \2;", o, flags=re.M)),
                    ("chart-period close", lambda o: re.sub(r"^(def C_\w+ = )close\(period = AggregationPeriod\.\w+\)", r"\1close", o, count=1, flags=re.M)),
                    ("no guard", lambda o: re.sub(r"if bsvHtfOk_\w+ then (H_\w+) else Double\.NaN", r"\1", o)),
                    ("guard <=", lambda o: o.replace("GetAggregationPeriod() < ", "GetAggregationPeriod() <= ")),
                    ("mixed aggregation", lambda o: o.replace("ExpAverage(C_ema, 50)", "ExpAverage(C_ema + close(period = AggregationPeriod.DAY) * 0, 50)"))],
    "amibroker": [("shift 0", lambda o: re.sub(r"^(H_\w+) = Ref\((.*), -1\);$", r"\1 = \2;", o, flags=re.M)),
                  ("expandLast", lambda o: o.replace(", expandFirst)", ", expandLast)")),
                  ("no shorter-chart guard", lambda o: re.sub(r"IIf\(Interval\(\) < \w+, (TimeFrameExpand\([^)]*\)), Null\)", r"\1", o)),
                  ("guard <=", lambda o: o.replace("IIf(Interval() < ", "IIf(Interval() <= ")),
                  ("no IsNull on signals", lambda o: re.sub(r"NOT IsNull\(\w+\) AND ", "", o)),
                  ("TimeFrameGetPrice shift 0", lambda o: re.sub(r"TimeFrameExpand\(H_\w+, (\w+), expandFirst\)", r'TimeFrameGetPrice("C", \1, 0)', o))],
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
            ok(not any(re.search(stubre(i), dout) for i in refs) and not PROBLEMS[t](dout, refs) and ({"pine-v6": '"1D"', "ninjatrader": "AddDataSeries(BarsPeriodType.Day, 1)", "ctrader": "MarketData.GetBars(TimeFrame.Daily)", "amibroker": "TimeFrameSet(inDaily);", "thinkscript": "AggregationPeriod.DAY"}.get(t, "PERIOD_D1") in dout), f"{p.stem} {t}: daily timeframe uses the closed-bar idiom")
            m45out = render(m45, t)
            if t in ("pine-v6", "ninjatrader", "ctrader", "amibroker"): ok(not any(re.search(stubre(i), m45out) for i in refs) and {"pine-v6": '"45"', "ninjatrader": "BarsPeriodType.Minute, 45", "ctrader": "TimeFrame.Minute45)", "amibroker": "TimeFrameSet(2700);"}[t] in m45out and not PROBLEMS[t](m45out, refs), f"{p.stem} {t}: 45 minutes readable on {t}")
            else: ok(all(re.search(stubre(i), m45out) for i in refs) and "BsvHtf" not in m45out, f"{p.stem} {t}: 45 minutes has no MT period, stays a TODO stub")
        else:
            ok(len(stub) == len(refs), f"{p.stem} {t}: every higher-timeframe block is an unsupported stub with a TODO line ({set(refs) - set(stub)} missing)")
            ok("BsvHtf" not in out and "request.security" not in out, f"{p.stem} {t}: no higher-timeframe helper claimed")
        wout = render(weekly, t)
        ok(all(re.search(stubre(i), wout) for i in refs), f"{p.stem} {t}: weekly timeframe (not readable) is unsupported")
print(json.dumps({"check": "higher-timeframe", "recipes": len(recipes), "targets": len(blt.TARGETS), "real": sorted(REAL), "documentedIdiom": sorted(IDIOM), "checks": checks, "failures": failures}))
sys.exit(1 if failures else 0)
