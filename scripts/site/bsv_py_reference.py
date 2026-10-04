"""Shared synthetic bars and independent reference for the Python-library target checks (check_backtrader.py,
check_backtesting_py.py): 1200 synthetic 15-minute bars (January-February 2026, before DST) and a pure-Python reference
for EMA/SMA/RSI (Wilder)/ATR (Wilder), crosses, thresholds, combines and session filters. Not market data."""
import csv, json, math, re
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

def htf_minutes(b):
    t = str((b.get("params") or {}).get("timeframe", "")).strip().upper()
    if t.isdigit(): return int(t)
    m = re.match(r"^(\d*)D$", t)
    return (int(m[1] or 1)) * 1440 if m else None


def htf_series(t, p, minutes):
    """Reference for an indicator on a higher timeframe, written separately from the generator: group the chart bars
    into UTC-aligned periods, compute the indicator over the period bars, and give chart bar i the value of the last
    period that ended before bar i's period began (closed higher-timeframe bars only)."""
    sec, groups = minutes * 60, []
    for i, b_ in enumerate(bars):
        k = int(b_["t"].timestamp() // sec)
        if groups and groups[-1][0] == k: groups[-1][1].append(i)
        else: groups.append((k, [i]))
    hb = [{"open": bars[g[0]]["open"], "high": max(bars[j]["high"] for j in g), "low": min(bars[j]["low"] for j in g), "close": bars[g[-1]]["close"]} for _, g in groups]
    P = {k: [x[k] for x in hb] for k in ("open", "high", "low", "close")}
    P["hl2"] = [(x["high"] + x["low"]) / 2 for x in hb]; P["hlc3"] = [(x["high"] + x["low"] + x["close"]) / 3 for x in hb]
    P["ohlc4"] = [(x["open"] + x["high"] + x["low"] + x["close"]) / 4 for x in hb]
    n, x = p["length"], P[p.get("source", "close")]
    if t == "indicator.sma": ser = sma(x, n)
    elif t == "indicator.ema": ser = ema(x, n)
    elif t == "indicator.rsi":
        G, Lo = rma([max(x[i] - x[i - 1], 0) for i in range(1, len(x))], n), rma([max(x[i - 1] - x[i], 0) for i in range(1, len(x))], n)
        ser = [NAN] + [NAN if not fin(u) else (50.0 if u + d == 0 else (100.0 if d == 0 else 100 * u / (u + d))) for u, d in zip(G, Lo)]
    else:
        tr = [max(hb[i]["high"], hb[i - 1]["close"]) - min(hb[i]["low"], hb[i - 1]["close"]) for i in range(1, len(hb))]
        ser = [NAN] + rma(tr, n)
    out = []
    for g, (_, idx) in enumerate(groups):
        out += [ser[g - 1] if g >= 1 else NAN] * len(idx)
    return out


def range_ok(by, b):
    if not b or b["type"] != "structure.range": return False
    p = b.get("params") or {}; d = by.get(p.get("during")); tr = p.get("track") or []
    return bool(d) and bool(re.match(r"^(signal|filter|alert)\.", d["type"])) and tr == ["high", "low"]


def pivot_ok(b):
    p = (b or {}).get("params") or {}; n = lambda x: isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= 50
    return bool(b) and b["type"] == "structure.pivot" and n(p.get("left")) and n(p.get("right")) and p.get("source", "close") in ("close", "high_low")


def sweep_ok(by, b):
    p = b.get("params") or {}; a = by.get(p.get("atr")); f = p.get("minAtrFraction", 0)
    return b["type"] == "signal.liquidity_sweep" and pivot_ok(by.get(p.get("pivot"))) and bool(a) and a["type"] == "indicator.atr" and not (a.get("params") or {}).get("timeframeRef") \
        and isinstance(f, (int, float)) and not isinstance(f, bool) and 0 <= f <= 10


def divergence_ok(by, b):
    p = b.get("params") or {}; pv = by.get(p.get("pivot")); o = by.get(p.get("oscillator"))
    return b["type"] == "signal.divergence" and pivot_ok(pv) and bool(o) and o["type"] in ("indicator.ema", "indicator.sma", "indicator.rsi", "indicator.atr") \
        and not (o.get("params") or {}).get("timeframeRef") and p.get("price", pv["params"].get("source", "close")) == pv["params"].get("source", "close") \
        and p.get("direction", "both") in ("both", "bullish", "bearish")


def zone_source(by, b):
    """The range/pivot id a visual.zone draws, or None when it cannot be drawn."""
    d = by.get(((b or {}).get("params") or {}).get("source"))
    return d["id"] if d and (pivot_ok(d) or range_ok(by, d)) else None


WEBHOOK_NAMES = ("symbol", "timeframe", "time", "open", "high", "low", "close")
def webhook_ok(by, b):
    p = (b or {}).get("params") or {}; w = by.get(p.get("when")); pl = p.get("payload")
    if not (w and re.match(r"^(signal|filter|alert)\.", w["type"]) and w["type"] != "alert.webhook" and isinstance(pl, dict) and pl): return False
    return all(isinstance(x, (int, float, bool)) or (isinstance(x, str) and all(m in WEBHOOK_NAMES for m in re.findall(r"\{\{([^}]*)\}\}", x))) for x in pl.values())


def webhook_expect(recipe, boo, start=0):
    """("WEBHOOK", time, json) per completed bar where the condition holds; written separately from the generator."""
    by = {b["id"]: b for b in recipe["blocks"]}; out = []
    for i in range(start, NB):
        t = bars[i]["t"].strftime("%Y-%m-%dT%H:%M:%S")
        f = {"symbol": "SYMBOL", "timeframe": "TIMEFRAME", "time": t, **{k: "%.10g" % bars[i][k] for k in ("open", "high", "low", "close")}}
        for b in recipe["blocks"]:
            if b["type"] == "alert.webhook" and webhook_ok(by, b) and boo(b["params"]["when"])[i]:
                pl = {k: (re.sub(r"\{\{([a-z]+)\}\}", lambda m: f[m[1]], x) if isinstance(x, str) else x) for k, x in b["params"]["payload"].items()}
                out.append(("WEBHOOK", t, json.dumps(pl, separators=(",", ":"))))
    return out


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
        src = by.get(p.get("timeframeRef")) if p.get("timeframeRef") else None
        if src is not None and src["type"] == "data.higher_timeframe" and htf_minutes(src) and t in ("indicator.sma", "indicator.ema", "indicator.rsi", "indicator.atr"):
            V[b["id"]] = htf_series(t, p, htf_minutes(src)); return
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
            L = val(p["left"]); op = p.get("op") if p.get("op") in (">", ">=", "<", "<=", "==", "!=") else ">="
            R = val(p["right"]) if isinstance(p.get("right"), str) and p.get("right") else [float(p["value"])] * NB  # right = another value (trend state), else the fixed number
            f = {">": lambda a, x: a > x, ">=": lambda a, x: a >= x, "<": lambda a, x: a < x, "<=": lambda a, x: a <= x, "==": lambda a, x: a == x, "!=": lambda a, x: a != x}[op]
            S[b["id"]] = [fin(v) and fin(r) and f(v, r) for v, r in zip(L, R)]
        elif t == "signal.recent":
            # written separately from the generator: look back over the previous `bars` bars (not the current one)
            sg, n = boo(p["signal"]), int(p["bars"])
            S[b["id"]] = [any(sg[i - k] for k in range(1, n + 1) if i - k >= 0) for i in range(NB)]
        elif t == "signal.combine":
            ls = [boo(r) for r in p.get("signals", [])]
            S[b["id"]] = [bool(ls) and (any(a[i] for a in ls) if p.get("mode") == "any" else all(a[i] for a in ls)) for i in range(NB)]
        elif t == "structure.range" and range_ok(by, b):
            # written separately from the generator: find each run of bars inside the window, take running
            # extremes inside the run, then hold the finished run's values until the next run starts
            ins = boo(p["during"]); hi, lo = [NAN] * NB, [NAN] * NB; i = 0
            while i < NB:
                if not ins[i]:
                    if i: hi[i], lo[i] = hi[i - 1], lo[i - 1]
                    i += 1; continue
                j = i
                while j < NB and ins[j]:
                    hi[j] = max(x["high"] for x in bars[i:j + 1]); lo[j] = min(x["low"] for x in bars[i:j + 1]); j += 1
                i = j
            V[b["id"] + ".high"], V[b["id"] + ".low"] = hi, lo
        elif t == "structure.pivot" and pivot_ok(b):
            # written separately from the generator: test every bar j against its whole window, then publish the
            # pivot on bar j + right (the first bar that has seen the right side) and hold it
            hv = PX["close"] if p.get("source", "close") == "close" else PX["high"]; lv = PX["close"] if p.get("source", "close") == "close" else PX["low"]
            L_, R_ = p["left"], p["right"]; ph, pl_ = {}, {}
            for j in range(L_, NB - R_):
                before, after = range(j - L_, j), range(j + 1, j + R_ + 1)  # strict before, ties allowed after (first bar of a flat top)
                if all(hv[j] > hv[k] for k in before) and all(hv[j] >= hv[k] for k in after): ph[j + R_] = hv[j]
                if all(lv[j] < lv[k] for k in before) and all(lv[j] <= lv[k] for k in after): pl_[j + R_] = lv[j]
            hi, lo, ch, cl = [], [], NAN, NAN
            for i in range(NB):
                ch, cl = ph.get(i, ch), pl_.get(i, cl); hi.append(ch); lo.append(cl)
            V[b["id"] + ".high"], V[b["id"] + ".low"] = hi, lo
        elif t == "signal.breakout" and range_ok(by, by.get(p.get("range"))) and p.get("direction", "either") in ("either", "above", "below"):
            r = by[p["range"]]; comp(r); ins = boo(r["params"]["during"]); hi, lo = V[r["id"] + ".high"], V[r["id"] + ".low"]; c = PX["close"]; out = []
            for i in range(NB):
                if i == 0 or ins[i] or not fin(hi[i]): out.append(False); continue
                up, dn = c[i] > hi[i] and c[i - 1] <= hi[i], c[i] < lo[i] and c[i - 1] >= lo[i]
                out.append({"either": up or dn, "above": up, "below": dn}[p.get("direction", "either")])
            S[b["id"]] = out
        elif t == "signal.liquidity_sweep" and sweep_ok(by, b):
            # written separately from the generator: the pivot levels the reference published up to bar i-1, bar i's ATR
            pid = p["pivot"]; comp(by[pid]); A = val(p["atr"]); hi, lo = V[pid + ".high"], V[pid + ".low"]; m = float(p.get("minAtrFraction", 0)); out = [False]
            for i in range(1, NB):
                x = bars[i]; a, z = hi[i - 1], lo[i - 1]
                out.append(fin(A[i]) and ((fin(a) and x["high"] > a and x["high"] - a >= m * A[i] and x["close"] < a) or (fin(z) and x["low"] < z and z - x["low"] >= m * A[i] and x["close"] > z)))
            S[b["id"]] = out
        elif t == "signal.divergence" and divergence_ok(by, b):
            # written separately from the generator: list every pivot bar j over the whole series, then compare each with the
            # pivot before it and mark bar j + right (when j is first confirmed)
            q = by[p["pivot"]]["params"]; L_, R_ = q["left"], q["right"]; O = val(p["oscillator"])
            hv = PX["close"] if q.get("source", "close") == "close" else PX["high"]; lv = PX["close"] if q.get("source", "close") == "close" else PX["low"]
            ph = [j for j in range(L_, NB - R_) if all(hv[j] > hv[k] for k in range(j - L_, j)) and all(hv[j] >= hv[k] for k in range(j + 1, j + R_ + 1))]
            pl_ = [j for j in range(L_, NB - R_) if all(lv[j] < lv[k] for k in range(j - L_, j)) and all(lv[j] <= lv[k] for k in range(j + 1, j + R_ + 1))]
            out, d = [False] * NB, p.get("direction", "both")
            if d in ("both", "bearish"):
                for a, j in zip(ph, ph[1:]):
                    if hv[j] > hv[a] and fin(O[j]) and fin(O[a]) and O[j] < O[a]: out[j + R_] = True
            if d in ("both", "bullish"):
                for a, j in zip(pl_, pl_[1:]):
                    if lv[j] < lv[a] and fin(O[j]) and fin(O[a]) and O[j] > O[a]: out[j + R_] = True
            S[b["id"]] = out
        elif t in ("visual.plot", "alert.condition"): pass
        elif t == "visual.zone" and zone_source(by, b): comp(by[zone_source(by, b)])
        elif t == "alert.webhook" and webhook_ok(by, b): comp(by.get(p["when"]))
        elif isb(t): S[b["id"]] = [False] * NB
        else: V[b["id"]] = [NAN] * NB
    for b in recipe["blocks"]: comp(b)
    return V, S, val, boo



def write_csv(path, n=None, every=1):
    """All bars, or the first n bars (n), or every k-th bar (every=k: coarser bars for the fail-loudly check)."""
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["datetime", "open", "high", "low", "close", "volume"])
        for b in bars[:n][::every]: w.writerow([b["t"].strftime("%Y-%m-%d %H:%M:%S"), repr(b["open"]), repr(b["high"]), repr(b["low"]), repr(b["close"]), 0])


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


# ---- value panels (visual.table), shared by the Python target checks. Written independently of the generator:
# a field is expected on the panel only when its whole dependency chain uses block types BSV renders and no
# higher timeframe; the panel shows the field's value on the last bar.
PANEL_TYPES = {"indicator.ema", "indicator.sma", "indicator.rsi", "indicator.atr", "signal.cross", "signal.threshold", "signal.combine", "signal.recent", "filter.session", "structure.range", "signal.breakout"}
PX_NAMES = {"open", "high", "low", "close", "hl2", "hlc3", "ohlc4"}


def _deps(b):
    p = b.get("params") or {}
    if b["type"] == "signal.cross": return [p.get("left"), p.get("right")]
    if b["type"] == "signal.threshold": return [p.get("left"), p.get("right") if isinstance(p.get("right"), str) else None]
    if b["type"] == "signal.recent": return [p.get("signal")]
    if b["type"] == "signal.combine": return list(p.get("signals") or [])
    if b["type"] == "structure.range": return [p.get("during")]
    if b["type"] == "signal.breakout": return [p.get("range")]
    return []


def panel_expect(recipe, V, S, at=-1):
    by = {b["id"]: b for b in recipe["blocks"]}
    def shown(ref, seen):
        if ref not in by: return ref in PX_NAMES
        if ref in seen: return True
        seen.add(ref); b = by[ref]
        if b["type"] not in PANEL_TYPES: return False  # higher-timeframe fields are shown: the Python targets compute them
        return all(shown(r, seen) for r in _deps(b) if r)
    out, skipped = [], 0
    for b in recipe["blocks"]:
        if b["type"] != "visual.table": continue
        p = b.get("params") or {}
        cells = []
        for f in p.get("fields") or []:
            if not shown(f, set()): skipped += 1; continue
            if by[f]["type"] == "structure.range" if f in by else False:
                cells += [(f"{f}.{k}", "num", V[f"{f}.{k}"][at]) for k in by[f]["params"]["track"]]
            elif f in S: cells.append((f, "bool", bool(S[f][at])))
            elif f in V: cells.append((f, "num", V[f][at]))
            else: cells.append((f, "num", PX[f][at] if f in PX else NAN))
        if not cells: skipped += 1
        else: out.append((str(p.get("title") or b["id"]).strip(), cells))
    return out, skipped


def parse_panels(stdout):
    out, cur = [], None
    for line in stdout.splitlines():
        if line.startswith("TABLE "): cur = (line[6:].strip(), []); out.append(cur)
        elif line.startswith("  ") and cur is not None and len(line.split()) == 2: cur[1].append(tuple(line.split()))
        else: cur = None
    return out


def panels_match(got, want):
    if [t for t, _ in got] != [t for t, _ in want]: return False, f"titles {[t for t, _ in got]} != {[t for t, _ in want]}"
    for (t, gc), (_, wc) in zip(got, want):
        if [n for n, _ in gc] != [n for n, _, _ in wc]: return False, f"{t}: fields {[n for n, _ in gc]} != {[n for n, _, _ in wc]}"
        for (n, g), (_, kind, w) in zip(gc, wc):
            if kind == "bool":
                if g != ("true" if w else "false"): return False, f"{t}.{n}: {g} != {w}"
            elif not fin(w):
                if g != "n/a": return False, f"{t}.{n}: {g} != n/a"
            else:
                try: x = float(g)
                except ValueError: return False, f"{t}.{n}: {g} is not a number"
                if abs(x - w) > 1e-5 * max(abs(w), 1e-9): return False, f"{t}.{n}: {g} != {w}"
    return True, ""


# ---- higher timeframe (data.higher_timeframe), shared by the Python target checks
def uses_htf(recipe):
    return any((b.get("params") or {}).get("timeframeRef") for b in recipe["blocks"])


def htf_checks(recipe, run_script, tmp, ok, name):
    """run_script(csv_path) -> CompletedProcess of the generated script. Three checks on the generated code:
    (1) values never look ahead: a run on the first CUT bars prints, on its last bar, exactly the reference values for
    bar CUT-1 of the full data (CUT is in the middle of a higher-timeframe period); (2) the reference keeps each value
    constant inside a period (closed higher-timeframe bars only); (3) chart bars that are not shorter than the higher
    timeframe make the script stop with an error instead of computing it on the chart timeframe."""
    V, S, _, _ = reference(recipe)
    cut = 702  # 702 * 15 min = 175.5 h: the run ends in the middle of an hour
    p = tmp / "htf_cut.csv"; write_csv(p, n=cut)
    out = run_script(p)
    want, _ = panel_expect(recipe, V, S, at=cut - 1)
    good, why = panels_match(parse_panels(out.stdout), want)
    ok(out.returncode == 0 and good and bool(want), name, f"higher timeframe: a run cut at bar {cut} prints the full-data values of bar {cut - 1} (no lookahead) {why}")
    by = {b["id"]: b for b in recipe["blocks"]}
    for b in recipe["blocks"]:
        src = by.get((b.get("params") or {}).get("timeframeRef"))
        if not src: continue
        sec = htf_minutes(src) * 60; ser = V[b["id"]]
        per = [int(x["t"].timestamp() // sec) for x in bars]
        flat = all((ser[i] == ser[i - 1]) or (not fin(ser[i]) and not fin(ser[i - 1])) for i in range(1, NB) if per[i] == per[i - 1])
        ok(flat and sum(1 for v in ser if fin(v)) > 0, name, f"higher timeframe: reference {b['id']} changes only when a period closes")
    p2 = tmp / "htf_coarse.csv"; write_csv(p2, every=max(1, int(htf_minutes(next(x for x in recipe["blocks"] if x["type"] == "data.higher_timeframe")) // 15)))
    out2 = run_script(p2)
    ok(out2.returncode != 0 and "must be shorter" in (out2.stderr + out2.stdout), name, "higher timeframe: chart bars as long as the higher timeframe stop the script with an error")


HTF_MUTATIONS = {  # deliberately broken copies of the generated helper: each one must fail htf_checks
    "uses the open period (lookahead)": ("bsv_htf_last(self.done, kind, source, n)", "bsv_htf_last(self.done + [tuple(self.cur[1:])], kind, source, n)"),
    "computes on the chart timeframe": ("self.sec, self.done, self.cur, self.last, self.step, self.memo = int(minutes) * 60", "self.sec, self.done, self.cur, self.last, self.step, self.memo = 1"),
    "does not stop on coarse bars": ('raise SystemExit("BSV higher timeframe: chart bars must be shorter', 'print("BSV higher timeframe: chart bars must be shorter'),
}


def htf_mutations(recipe, code, tmp, python, ok, name):
    import subprocess
    for label, (a, b) in HTF_MUTATIONS.items():
        mp = tmp / "htf_mutant.py"; mp.write_text(code.replace(a, b)); res = []
        htf_checks(recipe, lambda c: subprocess.run([python, str(mp), str(c)], capture_output=True, text=True, timeout=300), tmp, lambda c, n, m: res.append(bool(c)), name)
        ok(a in code and not all(res), name, f"higher-timeframe check catches a helper that {label}")


# ---- symbol scans (scanner.symbol_set, batch 28), shared by the Python target checks
SCAN_MUTATIONS = {  # one deliberately broken copy per target: each must change the scan result
    "backtrader": ("scan latches any earlier bar (not only the last completed bar)", "self.hit, self.when = bool(", "self.hit, self.when = self.hit or bool("),
    "backtesting-py": ("scan reads the bar before the last", "][-1]):", "][-2]):"),
    "nautilus": ("scan stops one bar early", "st = run_backtest(rows, Quiet)", "st = run_backtest(rows[:-1], Quiet)"),
}


def scan_checks(recipe, code, mp, tmp, python, target, ok, name):
    """The script's --scan mode on four CSVs (prefixes of the test bars that end on chosen bars) prints exactly the symbols whose
    scanned signal holds on their last completed bar, from the independent reference (no lookahead in the reference, so a
    prefix ending at bar i has the full-data value of bar i). Returns the number of hits printed."""
    import subprocess
    seen = 0
    for b in [x for x in recipe["blocks"] if x["type"] == "scanner.symbol_set"]:
        sid = re.sub(r"[^A-Za-z0-9_]", "_", b["id"])
        if f"def bsv_scan_{sid}(" not in code:
            ok(f"TODO unsupported block scanner.symbol_set: {b['id']} - " in code, name, f"{b['id']}: scan left as an explicit TODO with the reason"); continue
        _, _, _, boo = reference(recipe)
        sig = (b.get("params") or {}).get("signal") or next(x["params"]["when"] for x in recipe["blocks"] if x["type"] == "alert.condition")
        w = boo(sig); on = [i for i in range(400, NB) if w[i] and not w[i - 1]]; off = [i for i in range(400, NB) if w[i - 1] and not w[i]]
        if not (len(on) >= 2 and off):
            ok(False, name, f"{b['id']}: {sig} must fire on the test bars for the scan check"); continue
        picks = {"AAA": on[0], "BBB": off[0], "CCC": on[-1], "DDD": NB - 1}  # ends on: a new hit, the bar after a hit, the last hit, the full data
        args = []
        for sym, i in picks.items():
            p = tmp / f"scan_{sym}.csv"; write_csv(p, n=i + 1); args.append(f"{sym}={p}")
        want = [("SCAN", b["id"], sym, bars[i]["t"].strftime("%Y-%m-%dT%H:%M:%S")) for sym, i in picks.items() if w[i]] + [("SCAN", b["id"], "done", str(len(picks)))]
        run = lambda path: subprocess.run([python, str(path), "--scan", *args], capture_output=True, text=True, timeout=600)
        out = run(mp); got = [tuple(l.split(" ")) for l in out.stdout.splitlines() if l.startswith("SCAN ")]
        ok(out.returncode == 0 and got == want and len(want) >= 3 and not any(l.startswith("ALERT ") for l in out.stdout.splitlines()), name,
           f"{b['id']}: --scan lists the symbols whose {sig} held on their last completed bar ({len(got) - 1} listed, {len(want) - 1} expected; no ALERT lines) {out.stderr[-200:]}")
        seen += len(want) - 1
        label, a, c = SCAN_MUTATIONS[target]
        mm = tmp / "scan_mutant.py"; mm.write_text(code.replace(a, c)); out2 = run(mm)
        got2 = [tuple(l.split(" ")) for l in out2.stdout.splitlines() if l.startswith("SCAN ")]
        ok(a in code and got2 != want, name, f"{b['id']}: mutant caught: {label}")
    return seen
