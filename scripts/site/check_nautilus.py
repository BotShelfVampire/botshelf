#!/usr/bin/env python3
"""Check of the generator's NautilusTrader (Python) output for every recipe, run inside the real NautilusTrader
backtest engine (pip package nautilus_trader) on synthetic 15-minute bars rounded to the test instrument's 5 decimals.
This is a library run on made-up data, NOT a broker, live-feed or venue runtime test. Checks: allowed imports only; no
order/position calls; the module imports and BacktestEngine.run() completes with 0 orders; on_bar() runs once per bar;
EMA/SMA/RSI/ATR equal an independent reference on every bar (NaN while warming up); signals and session filters equal
the reference; plot values carry the referenced values; a 700-bar run equals the prefix of the full run (no look-ahead); running the file as a script on a CSV prints exactly one ALERT
per qualifying completed bar, with no misses. Usage: <python with nautilus_trader> check_nautilus.py"""
import ast, contextlib, importlib.util, io, json, re, subprocess, sys, tempfile, warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES = ROOT / "trader-toolkit/recipes"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsv_py_reference as R  # noqa: E402
R.use_rounded(5)
import nautilus_trader  # noqa: E402
warnings.filterwarnings("ignore")

checks = failures = files = alerts_seen = panels_seen = htf_seen = zones_seen = webhooks_seen = 0
import bsv_py_reference as BSVREF  # noqa: E402
def ok(c, f, m):
    global checks, failures
    checks += 1
    if not c:
        failures += 1
        print("FAIL", f, m, file=sys.stderr)
def same(a, b): return (not R.fin(a) and not R.fin(b)) or (R.fin(a) and R.fin(b) and abs(a - b) <= 1e-9 * max(1, abs(b)))

tmp = Path(tempfile.mkdtemp(prefix="bsv-nt-")); csvp = tmp / "bars.csv"; R.write_csv(csvp)
ROWS = [(b["t"], b["open"], b["high"], b["low"], b["close"], 0.0) for b in R.bars]
ALLOWED_IMPORTS = {"csv", "json", "math", "sys", "collections", "datetime", "zoneinfo", "nautilus_trader"}
ORDER = {"submit_order", "submit_order_list", "modify_order", "cancel_order", "cancel_all_orders", "close_position", "close_all_positions", "order_factory"}
for f in sorted(RECIPES.glob("*.json")):
    recipe = json.loads(f.read_text()); name = f.name; files += 1
    code = subprocess.run(["node", str(ROOT / "trader-toolkit/generator/render.mjs"), str(f), "--target", "nautilus"], capture_output=True, text=True, check=True).stdout
    ok(code.rstrip().endswith("# End BSV generated starter.") and "Not runtime tested by BSV" in code, name, "end marker / notice")
    try:
        tree = ast.parse(code); checks += 1
    except SyntaxError as e:
        ok(False, name, f"syntax {e}"); continue
    imps = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    ok(imps <= ALLOWED_IMPORTS, name, f"imports {imps - ALLOWED_IMPORTS}")
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    ok(not attrs & ORDER, name, f"order/position use {attrs & ORDER}")
    opens = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open"]
    lc = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_csv"]
    ok(len(opens) == 1 and lc and any(o in ast.walk(lc[0]) for o in opens) and not re.search(r"\b(eval|exec|__import__|urllib|requests|socket|subprocess)\s*\(", code), name, "only load_csv opens a file (read); no eval/exec/network")
    mp = tmp / ("nt_" + f.stem.replace("-", "_") + ".py"); mp.write_text(code)
    spec = importlib.util.spec_from_file_location(mp.stem, mp); mod = importlib.util.module_from_spec(spec); sys.modules[mp.stem] = mod; spec.loader.exec_module(mod)
    from nautilus_trader.trading.strategy import Strategy
    scls = [v for v in vars(mod).values() if isinstance(v, type) and issubclass(v, Strategy) and v.__module__ == mod.__name__]
    ok(len(scls) == 1, name, "one Strategy class")
    hist = []
    class Rec(scls[0]):
        def on_bar(self, bar):
            super().on_bar(bar); hist.append((dict(self._pv), dict(self._ps)))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            st = mod.run_backtest(ROWS, Rec)
        checks += 1
    except Exception as e:
        ok(False, name, f"run_backtest: {e!r}"); continue
    ok(st.bsv_orders == 0, name, f"0 orders ({st.bsv_orders})")
    full = list(hist); hist.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        mod.run_backtest(ROWS[:700], Rec)
    ok(len(hist) == 700 and all(json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str) for a, b in zip(hist, full)), name, "first-700-bar run equals the prefix of the full run (no look-ahead)")
    hist[:] = full
    ok(len(hist) == R.NB, name, f"on_bar once per bar ({len(hist)})")
    ok(all(same(h[0]["close"], b["close"]) and same(h[0]["high"], b["high"]) for h, b in zip(hist, R.bars)), name, "bar prices arrive unchanged (5 decimals)")
    V, S, val, boo = R.reference(recipe)
    for b in recipe["blocks"]:  # structure.range: the window's high/low on every bar equal the reference
        if b["type"] in ("structure.range", "structure.pivot") and b["id"] + ".high" in V:
            for KEYN in ("high", "low"):
                KEY = b["id"] + "." + KEYN; got = [h[0].get(KEY, float("nan")) for h in hist]; want = V[KEY]
                bad = sum(1 for g, w in zip(got, want) if not ((not BSVREF.fin(g) and not BSVREF.fin(w)) or (BSVREF.fin(g) and BSVREF.fin(w) and abs(g - w) < 1e-9)))
                ok(len(got) == len(want) and bad == 0 and sum(1 for w in want if BSVREF.fin(w)) > 0, name, f"{KEY} ({b['type']}) equals reference ({bad} bars differ)")
    for b in recipe["blocks"]:
        if b["type"] in ("indicator.ema", "indicator.sma", "indicator.rsi", "indicator.atr"):
            got = [h[0].get(b["id"], float("nan")) for h in hist]; bad = sum(1 for g, w in zip(got, V[b["id"]]) if not same(g, w))
            ok(bad == 0, name, f"{b['id']} ({b['type']}) equals reference ({bad} bars differ)")
        if re.match(r"^(signal\.(cross|threshold|combine|breakout)|filter\.session)$", b["type"]):
            got = [bool(h[1].get(b["id"])) for h in hist]; diff = sum(1 for g, w in zip(got, S[b["id"]]) if g != bool(w))
            ok(diff == 0, name, f"{b['id']} ({b['type']}) equals reference ({diff} bars differ)")
        if b["type"] == "visual.plot":
            got = [h[0].get("plot:" + b["id"], float("nan")) for h in hist]
            ok(all(same(g, w) for g, w in zip(got, val(b["params"]["source"]))), name, f"plot value {b['id']}")
    by = {x["id"]: x for x in recipe["blocks"]}
    for z in [x for x in recipe["blocks"] if x["type"] == "visual.zone" and BSVREF.zone_source(by, x)]:  # zone values = the source's high/low
        src = BSVREF.zone_source(by, z)
        for KEYN in ("high", "low"):
            got = [h[0].get(f"zone:{z['id']}.{KEYN}", float("nan")) for h in hist]; want = V[src + "." + KEYN]
            ok(all(same(g, w) for g, w in zip(got, want)) and any(R.fin(w) for w in want), name, f"zone {z['id']} {KEYN} equals {src}.{KEYN}")
        zones_seen += 1
    alerts = [b for b in recipe["blocks"] if b["type"] == "alert.condition"]
    out = subprocess.run([sys.executable, str(mp), str(csvp)], capture_output=True, text=True, timeout=300)
    ok(out.returncode == 0, name, f"script run exit {out.returncode} {out.stderr[-300:]}")
    got = [tuple(l.split(" ", 2)) for l in out.stdout.splitlines() if l.startswith("ALERT ")]
    want = [("ALERT", R.bars[i]["t"].strftime("%Y-%m-%dT%H:%M:%S"), a["params"].get("message", a["id"])) for i in range(R.NB) for a in alerts if boo(a["params"]["when"])[i]]
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
    if any(x["type"] == "alert.webhook" for x in recipe["blocks"]):  # webhook payloads: printed (never sent) once per completed bar
        gw = [tuple(l.split(" ", 2)) for l in out.stdout.splitlines() if l.startswith("WEBHOOK ")]; ww = BSVREF.webhook_expect(recipe, boo)
        ok(gw == ww and len(ww) > 0, name, f"webhook payloads printed {len(gw)} expected {len(ww)}")
        webhooks_seen += len(gw)
print(json.dumps({"target": "nautilus", "recipes": files, "checks": checks, "failures": failures, "alerts": alerts_seen, "panels": panels_seen, "htf_recipes": htf_seen, "zones": zones_seen, "webhooks": webhooks_seen,
                  "nautilus_trader": nautilus_trader.__version__, "note": "run inside the NautilusTrader backtest engine on synthetic bars; not a broker, live-feed or venue runtime test"}))
sys.exit(1 if failures else 0)
