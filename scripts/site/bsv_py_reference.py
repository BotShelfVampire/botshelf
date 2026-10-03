"""Shared synthetic bars and independent reference for the Python-library target checks (check_backtrader.py,
check_backtesting_py.py): 1200 synthetic 15-minute bars (January-February 2026, before DST) and a pure-Python reference
for EMA/SMA/RSI (Wilder)/ATR (Wilder), crosses, thresholds, combines and session filters. Not market data."""
import csv, math, re
from datetime import datetime, timedelta, timezone

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



def write_csv(path):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["datetime", "open", "high", "low", "close", "volume"])
        for b in bars: w.writerow([b["t"].strftime("%Y-%m-%d %H:%M:%S"), repr(b["open"]), repr(b["high"]), repr(b["low"]), repr(b["close"]), 0])


def use_rounded(nd):
    """Re-base the module on prices rounded to nd decimals (for runtimes that store prices at a fixed precision, e.g.
    NautilusTrader's Price). Must be called before reference()/write_csv(); affects this module's globals only."""
    global PX, TR
    for b in bars:
        for k in ("open", "high", "low", "close"):
            b[k] = round(b[k], nd)
    PX = {k: [b[k] for b in bars] for k in ("open", "high", "low", "close")}
    PX["hl2"] = [(b["high"] + b["low"]) / 2 for b in bars]; PX["hlc3"] = [(b["high"] + b["low"] + b["close"]) / 3 for b in bars]
    PX["ohlc4"] = [(b["open"] + b["high"] + b["low"] + b["close"]) / 4 for b in bars]
    TR = [NAN] + [max(bars[i]["high"], bars[i - 1]["close"]) - min(bars[i]["low"], bars[i - 1]["close"]) for i in range(1, NB)]
