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

checks = failures = files = alerts_seen = 0
def ok(c, f, m):
    global checks, failures
    checks += 1
    if not c:
        failures += 1
        print("FAIL", f, m, file=sys.stderr)

NB, STEP = 1200, timedelta(minutes=15)
T0 = datetime(2026, 1, 5, tzinfo=timezone.utc)
bars, c0 = [], 100.0
for i in range(NB):
    o = c0; c0 = 100 + 10 * math.sin(i / 15) + 3 * math.sin(i * 1.7)
    bars.append({"t": T0 + i * STEP, "open": o, "high": max(o, c0) + 0.5 + 0.3 * abs(math.sin(i)), "low": min(o, c0) - 0.5, "close": c0})
assert bars[-1]["t"] < datetime(2026, 3, 8, tzinfo=timezone.utc)  # before DST: New York = UTC-5, London = UTC+0
OFFSET = {"UTC": 0, "Etc/UTC": 0, "Europe/London": 0, "America/New_York": -300}
PX = {k: [b[k] for b in bars] for k in ("open", "high", "low", "close")}
PX["hl2"] = [(b["high"] + b["low"]) / 2 for b in bars]; PX["hlc3"] = [(b["high"] + b["low"] + b["close"]) / 3 for b in bars]
PX["ohlc4"] = [(b["open"] + b["high"] + b["low"] + b["close"]) / 4 for b in bars]
NAN = float("nan"); fin = lambda v: isinstance(v, (int, float)) and math.isfinite(v)

def sma(x, p): return [NAN if i < p - 1 else sum(x[i - p + 1:i + 1]) / p for i in range(len(x))]
def ema(x, p):
    a, out, e = 2 / (p + 1), [], NAN
    for i, v in enumerate(x):
        if i == p - 1: e = sum(x[:p]) / p
        elif i >= p: e = a * v + (1 - a) * e
        out.append(e if i >= p - 1 else NAN)
    return out
def rma(x, p):
    out, r = [], NAN
    for i, v in enumerate(x):
        if i == p - 1: r = sum(x[:p]) / p
        elif i >= p: r = (r * (p - 1) + v) / p
        out.append(r if i >= p - 1 else NAN)
    return out
TR = [NAN] + [max(bars[i]["high"], bars[i - 1]["close"]) - min(bars[i]["low"], bars[i - 1]["close"]) for i in range(1, NB)]

def reference(recipe):
    by = {b["id"]: b for b in recipe["blocks"]}; V, S = {}, {}
    isb = lambda t: bool(re.match(r"^(signal|filter|alert)\.", t or ""))
    def get(ref, m):
        comp(by.get(ref)); return m.get(ref, [False] * NB if m is S else [NAN] * NB)
    def val(ref): return PX[ref] if ref in PX else ([float(v) for v in get(ref, S)] if isb(by.get(ref, {}).get("type")) else get(ref, V))
    def boo(ref): return get(ref, S) if isb(by.get(ref, {}).get("type")) else [fin(v) and v != 0 for v in val(ref)]
    done = set()
    def comp(b):
        if not b or b["id"] in done: return
        done.add(b["id"]); p = b.get("params") or {}; t = b["type"]
        if t == "indicator.sma": V[b["id"]] = sma(PX[p.get("source", "close")], p["length"])
        elif t == "indicator.ema": V[b["id"]] = ema(PX[p.get("source", "close")], p["length"])
        elif t == "indicator.rsi":
            x = PX[p.get("source", "close")]; g = [max(x[i] - x[i - 1], 0) for i in range(1, NB)]; l = [max(x[i - 1] - x[i], 0) for i in range(1, NB)]
            G, Lo = rma(g, p["length"]), rma(l, p["length"])
            V[b["id"]] = [NAN] + [NAN if not fin(u) else (50.0 if u + d == 0 else (100.0 if d == 0 else 100 * u / (u + d))) for u, d in zip(G, Lo)]
        elif t == "indicator.atr": V[b["id"]] = [NAN] + rma(TR[1:], p["length"])
        elif t == "filter.session":
            m = re.match(r"^(\d{2})(\d{2})-(\d{2})(\d{2})$", p.get("session", "0000-2359")); st, en = int(m[1]) * 60 + int(m[2]), int(m[3]) * 60 + int(m[4])
            off = OFFSET[p.get("timezone", "Etc/UTC")]
            mm = [((int(b_["t"].timestamp() // 60) + off) % 1440) for b_ in bars]
            S[b["id"]] = [(st <= v < en) if st <= en else (v >= st or v < en) for v in mm]
        elif t == "signal.cross":
            L, R = val(p["left"]), val(p["right"]); up = p.get("direction") != "below"
            S[b["id"]] = [i > 0 and ((L[i] > R[i] and L[i - 1] <= R[i - 1]) if up else (L[i] < R[i] and L[i - 1] >= R[i - 1])) for i in range(NB)]
        elif t == "signal.threshold":
            L = val(p["left"]); x = float(p["value"]); op = p.get("op") if p.get("op") in (">", ">=", "<", "<=", "==", "!=") else ">="
            f = {">": lambda a: a > x, ">=": lambda a: a >= x, "<": lambda a: a < x, "<=": lambda a: a <= x, "==": lambda a: a == x, "!=": lambda a: a != x}[op]
            S[b["id"]] = [fin(v) and f(v) for v in L]
        elif t == "signal.combine":
            ls = [boo(r) for r in p.get("signals", [])]
            S[b["id"]] = [bool(ls) and (any(a[i] for a in ls) if p.get("mode") == "any" else all(a[i] for a in ls)) for i in range(NB)]
        elif t in ("visual.plot", "alert.condition"): pass
        elif isb(t): S[b["id"]] = [False] * NB
        else: V[b["id"]] = [NAN] * NB
    for b in recipe["blocks"]: comp(b)
    return V, S, val, boo

tmp = Path(tempfile.mkdtemp(prefix="bsv-bt-"))
csvp = tmp / "bars.csv"
with csvp.open("w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["datetime", "open", "high", "low", "close", "volume"])
    for b in bars: w.writerow([b["t"].strftime("%Y-%m-%d %H:%M:%S"), repr(b["open"]), repr(b["high"]), repr(b["low"]), repr(b["close"]), 0])
ALLOWED_IMPORTS = {"math", "sys", "datetime", "zoneinfo", "backtrader"}
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
    for b in recipe["blocks"]:
        k = re.sub(r"[^A-Za-z0-9_]", "_", b["id"])
        if b["type"] in ("indicator.ema", "indicator.sma", "indicator.rsi", "indicator.atr"):
            got = [r.get(k, NAN) for r in rec["subs"]]; want = V[b["id"]]
            worst = max((abs(g - w) / max(1, abs(w)) for g, w in zip(got, want) if fin(w)), default=0); warm = sum(1 for g, w in zip(got, want) if not fin(w) and fin(g))
            ok(worst < 1e-9 and warm == 0 and all(fin(g) for g, w in zip(got, want) if fin(w)), name, f"{b['id']} ({b['type']}) equals reference: worst {worst}, early values {warm}")
        if re.match(r"^(signal\.(cross|threshold|combine)|filter\.session)$", b["type"]):
            got = [bool(r.get(b["id"])) for r in rec["sig"]]; want = S[b["id"]]
            diff = sum(1 for g, w in zip(got, want) if g != bool(w))
            ok(diff == 0, name, f"{b['id']} ({b['type']}) equals reference ({diff} bars differ)")
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
    ok(sorted(map(tuple, got)) == sorted(map(tuple, want)) and len(got) == len(set(map(tuple, got))), name, f"alerts printed {len(got)} expected {len(want)}")
print(json.dumps({"target": "backtrader", "recipes": files, "checks": checks, "failures": failures, "alerts": alerts_seen,
                  "backtrader": bt.__version__, "note": "run inside the backtrader library on synthetic bars; not a broker, live-feed or platform runtime test"}))
sys.exit(1 if failures else 0)
