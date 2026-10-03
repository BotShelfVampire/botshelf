#!/usr/bin/env python3
"""Check of the generator's backtrader (Python) output for every recipe, run inside the real backtrader library
(pip package backtrader) on synthetic 15-minute bars. This is a library run on made-up data, NOT a broker, live-feed
or trading-platform runtime test. Checks: only allowed imports, no order calls (buy/sell/close/order_target*),
the module imports and runs under backtrader; EMA/SMA/RSI/ATR equal an independent reference on every bar (NaN while
warming up); signals and session filters equal an independent reference; plot lines carry the referenced values;
running the file as a script on a CSV prints one ALERT per completed bar where the condition holds, with no misses.
Usage: <python with backtrader> check_backtrader.py"""
import ast, csv, importlib.util, json, math, os, re, subprocess, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES = ROOT / "trader-toolkit/recipes"
import backtrader as bt  # noqa: E402

checks = failures = files = alerts_seen = panels_seen = htf_seen = zones_seen = webhooks_seen = 0
import bsv_py_reference as BSVREF  # noqa: E402
def ok(c, f, m):
    global checks, failures
    checks += 1
    if not c:
        failures += 1
        print("FAIL", f, m, file=sys.stderr)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bsv_py_reference import NB, NAN, bars, fin, reference, write_csv  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="bsv-bt-"))
csvp = tmp / "bars.csv"
write_csv(csvp)
ALLOWED_IMPORTS = {"json", "math", "sys", "datetime", "zoneinfo", "backtrader"}
for f in sorted(RECIPES.glob("*.json")):
    recipe = json.loads(f.read_text()); name = f.name; files += 1
    code = subprocess.run(["node", str(ROOT / "trader-toolkit/generator/render.mjs"), str(f), "--target", "backtrader"], capture_output=True, text=True, check=True).stdout
    ok(code.rstrip().endswith("# End BSV generated starter.") and "Not runtime tested by BSV" in code, name, "end marker / notice")
    try:
        tree = ast.parse(code); checks += 1
    except SyntaxError as e:
        ok(False, name, f"syntax {e}"); continue
    imps = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    ok(imps <= ALLOWED_IMPORTS, name, f"imports {imps - ALLOWED_IMPORTS}")
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    ok(not calls & {"buy", "sell", "close", "order_target_size", "order_target_value", "order_target_percent", "buy_bracket", "sell_bracket", "setcommission", "setcash"}, name, f"order calls {calls}")
    ok(not re.search(r"\b(eval|exec|open|__import__|urllib|requests|socket|subprocess)\s*\(", code), name, "no eval/exec/file/network calls")
    mp = tmp / (f.stem.replace("-", "_") + ".py"); mp.write_text(code)
    spec = importlib.util.spec_from_file_location(mp.stem, mp); mod = importlib.util.module_from_spec(spec); sys.modules[mp.stem] = mod; spec.loader.exec_module(mod)
    ind_cls = [v for v in vars(mod).values() if isinstance(v, type) and issubclass(v, bt.Indicator) and v.__module__ == mod.__name__]
    ok(len(ind_cls) == 1, name, "one indicator class")
    plots = [b for b in recipe["blocks"] if b["type"] == "visual.plot"]; alerts = [b for b in recipe["blocks"] if b["type"] == "alert.condition"]
    rec = {"lines": [], "subs": [], "sig": []}
    class Cap(bt.Strategy):
        def __init__(self): self.ind = ind_cls[0](self.data)
        def prenext(self): self.next()
        def next(self):
            rec["lines"].append({ln: getattr(self.ind.lines, ln)[0] for ln in self.ind.lines.getlinealiases()})
            rec["subs"].append({k[2:]: getattr(self.ind, k)[0] for k in vars(self.ind) if k.startswith("i_")})
            rec["sig"].append(dict(self.ind._prev))
    def run(runonce):
        cer = bt.Cerebro(stdstats=False, runonce=runonce)
        cer.adddata(bt.feeds.GenericCSVData(dataname=str(csvp), dtformat="%Y-%m-%d %H:%M:%S", datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1, timeframe=bt.TimeFrame.Minutes))
        cer.addstrategy(Cap); cer.run()
    try:
        run(True); vec = rec["lines"]; rec.update(lines=[], subs=[], sig=[])  # backtrader's default vectorised mode: only the output lines are comparable
        run(False); checks += 1  # bar-by-bar mode, as the generated main() uses
    except Exception as e:
        ok(False, name, f"backtrader run: {e!r}"); continue
    same = lambda a, b: (a == b) or (not fin(a) and not fin(b)) or (fin(a) and fin(b) and abs(a - b) < 1e-9)
    ok(len(vec) == len(rec["lines"]) and all(same(x[k], y[k]) for x, y in zip(vec, rec["lines"]) for k in y), name, "output lines identical with runonce=True and runonce=False")
    ok(len(rec["lines"]) == NB, name, f"one next() per bar ({len(rec['lines'])})")
    V, S, val, boo = reference(recipe)
    for b in recipe["blocks"]:  # structure.range: the window's high/low on every bar equal the reference
        if b["type"] in ("structure.range", "structure.pivot") and b["id"] + ".high" in V:
            for KEYN in ("high", "low"):
                KEY = b["id"] + "." + KEYN; got = [r.get(KEY, NAN) for r in rec["sig"]]; want = V[KEY]
                bad = sum(1 for g, w in zip(got, want) if not ((not BSVREF.fin(g) and not BSVREF.fin(w)) or (BSVREF.fin(g) and BSVREF.fin(w) and abs(g - w) < 1e-9)))
                ok(len(got) == len(want) and bad == 0 and sum(1 for w in want if BSVREF.fin(w)) > 0, name, f"{KEY} ({b['type']}) equals reference ({bad} bars differ)")
    for b in recipe["blocks"]:
        k = re.sub(r"[^A-Za-z0-9_]", "_", b["id"])
        if b["type"] in ("indicator.ema", "indicator.sma", "indicator.rsi", "indicator.atr"):
            got = [r.get(b["id"], NAN) for r in rec["sig"]] if (b.get("params") or {}).get("timeframeRef") else [r.get(k, NAN) for r in rec["subs"]]; want = V[b["id"]]
            worst = max((abs(g - w) / max(1, abs(w)) for g, w in zip(got, want) if fin(w)), default=0); warm = sum(1 for g, w in zip(got, want) if not fin(w) and fin(g))
            ok(worst < 1e-9 and warm == 0 and all(fin(g) for g, w in zip(got, want) if fin(w)), name, f"{b['id']} ({b['type']}) equals reference: worst {worst}, early values {warm}")
        if re.match(r"^(signal\.(cross|threshold|combine|breakout|liquidity_sweep|divergence)|filter\.session)$", b["type"]):
            got = [bool(r.get(b["id"])) for r in rec["sig"]]; want = S[b["id"]]
            diff = sum(1 for g, w in zip(got, want) if g != bool(w))
            ok(diff == 0, name, f"{b['id']} ({b['type']}) equals reference ({diff} bars differ)")
            ok(b["type"] not in ("signal.liquidity_sweep", "signal.divergence") or sum(map(bool, S[b["id"]])) > 0, name, f"{b['id']} fires on the synthetic bars (the comparison is not vacuous)")
    by = {x["id"]: x for x in recipe["blocks"]}
    for n, z in enumerate([x for x in recipe["blocks"] if x["type"] == "visual.zone" and BSVREF.zone_source(by, x)]):  # zone lines = the source's high/low
        src = BSVREF.zone_source(by, z)
        for e, KEYN in (("h", "high"), ("l", "low")):
            got = [r.get(f"z{n + 1}{e}", NAN) for r in rec["lines"]]; want = V[src + "." + KEYN]
            ok(all(same(g, w) for g, w in zip(got, want)) and any(fin(w) for w in want), name, f"zone {z['id']} {KEYN} line equals {src}.{KEYN}")
        zones_seen += 1
    for n, pl in enumerate(plots):
        want = val(pl["params"]["source"]); got = [r[f"p{n + 1}"] for r in rec["lines"]]
        ok(all((abs(g - w) < 1e-9) if fin(w) else not fin(g) for g, w in zip(got, want)), name, f"p{n + 1} plots {pl['params']['source']}")
    out = subprocess.run([sys.executable, str(mp), str(csvp)], capture_output=True, text=True, timeout=300)
    ok(out.returncode == 0, name, f"script run exit {out.returncode} {out.stderr[-300:]}")
    got = [l.split(" ", 2) for l in out.stdout.splitlines() if l.startswith("ALERT ")]
    want = []
    for i in range(NB):
        for a in alerts:
            if boo(a["params"]["when"])[i]: want.append(["ALERT", bars[i]["t"].strftime("%Y-%m-%dT%H:%M:%S"), a["params"].get("message", a["id"])])
    alerts_seen += len(got)
    if any(b["type"] == "visual.table" for b in recipe["blocks"]):  # value panels (visual.table) on the last bar
        want_p, skipped = BSVREF.panel_expect(recipe, V, S)
        okp, why = BSVREF.panels_match(BSVREF.parse_panels(out.stdout), want_p)
        ok(okp, name, f"value panel on the last bar equals the reference {why}")
        ok(len(re.findall(r"TODO [A-Za-z0-9_]+: visual\.table ", code)) == skipped and "TODO unsupported block visual.table" not in code, name, f"panel TODO lines for fields that cannot be shown ({skipped})")
        panels_seen += len(want_p)
    if BSVREF.uses_htf(recipe):  # higher timeframe: no lookahead, closed periods only, fails loudly on too-coarse bars
        BSVREF.htf_checks(recipe, lambda c: subprocess.run([sys.executable, str(mp), str(c)], capture_output=True, text=True, timeout=300), tmp, ok, name)
        BSVREF.htf_mutations(recipe, code, tmp, sys.executable, ok, name)  # the same helper is emitted for all three Python targets
        htf_seen += 1
    ok(sorted(map(tuple, got)) == sorted(map(tuple, want)) and len(got) == len(set(map(tuple, got))), name, f"alerts printed {len(got)} expected {len(want)}")
    for mname, frm, to in (("sweep without the close back inside", "and c < ph  #", "and True  #"), ("sweep without the ATR distance", "h - ph >= frac * atr", "True"),
                           ("divergence oscillator test flipped", "and o < st[3][1]", "and o > st[3][1]"), ("divergence with the price test dropped", "p > st[3][0] and", "True and")):
        if frm in code:  # the helpers are emitted identically for all three Python targets; the reference must tell them apart
            mm = tmp / (mp.stem + "_mut.py"); mm.write_text(code.replace(frm, to, 1))
            o2 = subprocess.run([sys.executable, str(mm), str(csvp)], capture_output=True, text=True, timeout=300)
            g2 = [l.split(" ", 2) for l in o2.stdout.splitlines() if l.startswith("ALERT ")]
            ok(o2.returncode == 0 and sorted(map(tuple, g2)) != sorted(map(tuple, want)), name, f"mutant caught: {mname}")
    if any(x["type"] == "alert.webhook" for x in recipe["blocks"]):  # webhook payloads: printed (never sent) once per completed bar
        gw = [tuple(l.split(" ", 2)) for l in out.stdout.splitlines() if l.startswith("WEBHOOK ")]; ww = BSVREF.webhook_expect(recipe, boo)
        ok(gw == ww and len(ww) > 0, name, f"webhook payloads printed {len(gw)} expected {len(ww)}")
        webhooks_seen += len(gw)
print(json.dumps({"target": "backtrader", "recipes": files, "checks": checks, "failures": failures, "alerts": alerts_seen, "panels": panels_seen, "htf_recipes": htf_seen, "zones": zones_seen, "webhooks": webhooks_seen,
                  "backtrader": bt.__version__, "note": "run inside the backtrader library on synthetic bars; not a broker, live-feed or platform runtime test"}))
sys.exit(1 if failures else 0)
