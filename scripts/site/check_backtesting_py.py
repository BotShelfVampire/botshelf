#!/usr/bin/env python3
"""Check of the generator's Backtesting.py (Python) output for every recipe, run inside the real Backtesting.py library
(pip package backtesting) on synthetic 15-minute bars. This is a library run on made-up data, NOT a broker, live-feed
or trading-platform runtime test. Checks: allowed imports only; no order or position calls; the module imports and
Backtest.run() completes with 0 trades; EMA/SMA/RSI/ATR equal an independent reference on every bar (NaN while warming
up); signals and session filters equal the reference; plot lines carry the referenced values; no look-ahead (a run on
the first 700 bars gives exactly the prefix of the full run); next() is called once per bar from Backtesting.py's
warm-up start; running the file as a script on a CSV prints exactly one ALERT per qualifying completed bar from that
start. Usage: <python with backtesting> check_backtesting_py.py"""
import ast, contextlib, io, importlib.util, json, re, subprocess, sys, tempfile, warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES = ROOT / "trader-toolkit/recipes"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bsv_py_reference import NB, bars, fin, reference, write_csv  # noqa: E402
import numpy as np, pandas as pd, backtesting  # noqa: E402
from backtesting import Backtest, Strategy  # noqa: E402
warnings.filterwarnings("ignore")

checks = failures = files = alerts_seen = panels_seen = htf_seen = zones_seen = webhooks_seen = 0
import bsv_py_reference as BSVREF  # noqa: E402
def ok(c, f, m):
    global checks, failures
    checks += 1
    if not c:
        failures += 1
        print("FAIL", f, m, file=sys.stderr)

def frame(n):
    df = pd.DataFrame({"Open": [b["open"] for b in bars[:n]], "High": [b["high"] for b in bars[:n]], "Low": [b["low"] for b in bars[:n]],
                       "Close": [b["close"] for b in bars[:n]], "Volume": [0] * n}, index=pd.DatetimeIndex([b["t"].replace(tzinfo=None) for b in bars[:n]]))
    return df
def same(a, b): return (not fin(a) and not fin(b)) or (fin(a) and fin(b) and abs(a - b) <= 1e-9 * max(1, abs(b)))
def first_valid(xs):
    for i, x in enumerate(xs):
        if fin(x): return i
    return 0

tmp = Path(tempfile.mkdtemp(prefix="bsv-btpy-")); csvp = tmp / "bars.csv"; write_csv(csvp)
ALLOWED_IMPORTS = {"json", "sys", "numpy", "pandas", "backtesting"}
ORDER_CALLS = {"buy", "sell", "close", "cancel"}
for f in sorted(RECIPES.glob("*.json")):
    recipe = json.loads(f.read_text()); name = f.name; files += 1
    code = subprocess.run(["node", str(ROOT / "trader-toolkit/generator/render.mjs"), str(f), "--target", "backtesting-py"], capture_output=True, text=True, check=True).stdout
    ok(code.rstrip().endswith("# End BSV generated starter.") and "Not runtime tested by BSV" in code, name, "end marker / notice")
    try:
        tree = ast.parse(code); checks += 1
    except SyntaxError as e:
        ok(False, name, f"syntax {e}"); continue
    imps = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    ok(imps <= ALLOWED_IMPORTS, name, f"imports {imps - ALLOWED_IMPORTS}")
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    ok(not calls & ORDER_CALLS and not attrs & {"position", "trades", "orders", "closed_trades"}, name, f"order/position use {calls & ORDER_CALLS} {attrs & {'position', 'trades', 'orders'}}")
    ok(not re.search(r"\b(eval|exec|open|__import__|urllib|requests|socket|subprocess)\s*\(", code), name, "no eval/exec/file/network calls")
    mp = tmp / ("btpy_" + f.stem.replace("-", "_") + ".py"); mp.write_text(code)
    spec = importlib.util.spec_from_file_location(mp.stem, mp); mod = importlib.util.module_from_spec(spec); sys.modules[mp.stem] = mod; spec.loader.exec_module(mod)
    scls = [v for v in vars(mod).values() if isinstance(v, type) and issubclass(v, Strategy) and v.__module__ == mod.__name__]
    ok(len(scls) == 1, name, "one Strategy class")
    calls_seen = []
    class Count(scls[0]):
        def next(self):
            calls_seen.append(len(self.data) - 1); super().next()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            st = Backtest(frame(NB), Count, cash=1_000_000, commission=0.0).run()
            st2 = Backtest(frame(700), scls[0], cash=1_000_000, commission=0.0).run()
        strat, s2 = st._strategy, st2._strategy; checks += 1
    except Exception as e:
        ok(False, name, f"Backtest.run: {e!r}"); continue
    ok(st["# Trades"] == 0, name, f"no trades ({st['# Trades']})")
    V, S, val, boo = reference(recipe)
    for b in recipe["blocks"]:  # structure.range: the window's high/low on every bar equal the reference
        if b["type"] in ("structure.range", "structure.pivot") and b["id"] + ".high" in V:
            for KEYN in ("high", "low"):
                KEY = b["id"] + "." + KEYN; got = list(strat.bsv_values[KEY]); want = V[KEY]
                bad = sum(1 for g, w in zip(got, want) if not ((not BSVREF.fin(g) and not BSVREF.fin(w)) or (BSVREF.fin(g) and BSVREF.fin(w) and abs(g - w) < 1e-9)))
                ok(len(got) == len(want) and bad == 0 and sum(1 for w in want if BSVREF.fin(w)) > 0, name, f"{KEY} ({b['type']}) equals reference ({bad} bars differ)")
    for b in recipe["blocks"]:
        if b["type"] in ("indicator.ema", "indicator.sma", "indicator.rsi", "indicator.atr"):
            got = list(strat.bsv_values[b["id"]]); want = V[b["id"]]
            bad = sum(1 for g, w in zip(got, want) if not same(g, w))
            ok(len(got) == NB and bad == 0, name, f"{b['id']} ({b['type']}) equals reference ({bad} bars differ)")
        if re.match(r"^(signal\.(cross|threshold|combine|recent|breakout|liquidity_sweep|divergence)|filter\.session)$", b["type"]):
            got = [bool(x) for x in strat.bsv_signals[b["id"]]]; want = S[b["id"]]
            diff = sum(1 for g, w in zip(got, want) if g != bool(w))
            ok(diff == 0, name, f"{b['id']} ({b['type']}) equals reference ({diff} bars differ)")
            ok(b["type"] not in ("signal.liquidity_sweep", "signal.divergence") or sum(map(bool, S[b["id"]])) > 0, name, f"{b['id']} fires on the synthetic bars (the comparison is not vacuous)")
        if b["type"] == "alert.condition" and any(x["type"] == "signal.recent" for x in recipe["blocks"]):  # look-back recipes: the alert condition must hold on these bars
            al = b; c = sum(map(bool, S.get(al["params"]["when"], []))); ok(c > 0, name, f"{al['id']}: alert condition with a look-back holds on the synthetic bars ({c} bars)")
    look = sum(1 for k in strat.bsv_values for g, w in zip(s2.bsv_values[k], strat.bsv_values[k][:700]) if not same(g, w)) + \
           sum(1 for k in strat.bsv_signals for g, w in zip(s2.bsv_signals[k], strat.bsv_signals[k][:700]) if bool(g) != bool(w))
    ok(look == 0, name, f"no look-ahead: 700-bar run equals the prefix of the full run ({look} differ)")
    plots = [b for b in recipe["blocks"] if b["type"] == "visual.plot"]; alerts = [b for b in recipe["blocks"] if b["type"] == "alert.condition"]
    for n, pl in enumerate(plots):
        want = val(pl["params"]["source"]); got = list(np.asarray(getattr(strat, f"p{n + 1}"), float))
        ok(len(got) == NB and all(same(g, w) for g, w in zip(got, want)), name, f"p{n + 1} plots {pl['params']['source']}")
    by = {x["id"]: x for x in recipe["blocks"]}
    zl = []  # zone lines (self.I) also delay Backtesting.py's first next()
    for n, z in enumerate([x for x in recipe["blocks"] if x["type"] == "visual.zone" and BSVREF.zone_source(by, x)]):
        src = BSVREF.zone_source(by, z)
        for e, KEYN in (("h", "high"), ("l", "low")):
            want = V[src + "." + KEYN]; got = list(np.asarray(getattr(strat, f"z{n + 1}{e}"), float)); zl.append(want)
            ok(len(got) == NB and all(same(g, w) for g, w in zip(got, want)) and any(fin(w) for w in want), name, f"zone {z['id']} {KEYN} line equals {src}.{KEYN}")
        zones_seen += 1
    start = 1 + max([first_valid(val(pl["params"]["source"])) for pl in plots] + [first_valid(w) for w in zl], default=0)
    ok(calls_seen == list(range(start, NB)), name, f"next() once per bar from bar {start} ({len(calls_seen)} calls)")
    out = subprocess.run([sys.executable, str(mp), str(csvp)], capture_output=True, text=True, timeout=300)
    ok(out.returncode == 0, name, f"script run exit {out.returncode} {out.stderr[-300:]}")
    got = [tuple(l.split(" ", 2)) for l in out.stdout.splitlines() if l.startswith("ALERT ")]
    want = [("ALERT", bars[i]["t"].strftime("%Y-%m-%dT%H:%M:%S"), a["params"].get("message", a["id"])) for i in range(start, NB) for a in alerts if boo(a["params"]["when"])[i]]
    alerts_seen += len(got)
    if any(b["type"] == "visual.table" for b in recipe["blocks"]):  # value panels (visual.table) on the last bar
        want_p, skipped = BSVREF.panel_expect(recipe, V, S)
        okp, why = BSVREF.panels_match(BSVREF.parse_panels(out.stdout), want_p)
        ok(okp, name, f"value panel on the last bar equals the reference {why}")
        ok(len(re.findall(r"TODO [A-Za-z0-9_]+: visual\.table ", code)) == skipped and "TODO unsupported block visual.table" not in code, name, f"panel TODO lines for fields that cannot be shown ({skipped})")
        panels_seen += len(want_p)
    if BSVREF.uses_htf(recipe):  # higher timeframe: no lookahead, closed periods only, fails loudly on too-coarse bars
        BSVREF.htf_checks(recipe, lambda c: subprocess.run([sys.executable, str(mp), str(c)], capture_output=True, text=True, timeout=300), tmp, ok, name)
        htf_seen += 1
    ok(sorted(got) == sorted(want) and len(got) == len(set(got)), name, f"alerts printed {len(got)} expected {len(want)}")
    if any(x["type"] == "alert.webhook" for x in recipe["blocks"]):  # webhook payloads: printed (never sent) once per completed bar from the first next()
        gw = [tuple(l.split(" ", 2)) for l in out.stdout.splitlines() if l.startswith("WEBHOOK ")]; ww = BSVREF.webhook_expect(recipe, boo, start)
        ok(gw == ww and len(ww) > 0, name, f"webhook payloads printed {len(gw)} expected {len(ww)}")
        webhooks_seen += len(gw)
print(json.dumps({"target": "backtesting-py", "recipes": files, "checks": checks, "failures": failures, "alerts": alerts_seen, "panels": panels_seen, "htf_recipes": htf_seen, "zones": zones_seen, "webhooks": webhooks_seen,
                  "backtesting": backtesting.__version__, "note": "run inside the Backtesting.py library on synthetic bars; not a broker, live-feed or platform runtime test"}))
sys.exit(1 if failures else 0)
