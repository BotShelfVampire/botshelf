#!/usr/bin/env python3
"""BSV C# checks for the NinjaTrader 8 and cTrader targets (batch 30).
1) Static: every recipe's `ninjatrader` output compiles (dotnet, warnings as errors) against cs_eval/NinjaEval.cs, BSV's stand-in for the
   NinjaScript members the generator uses (the cTrader outputs are compiled by check_ctrader_stubs.sh).
2) Run: the symbol-scan recipe's output for both targets is compiled with a functional stand-in (cs_eval/CAlgoEval.cs, NinjaEval.cs) and RUN
   on the BSV synthetic bars (bsv_py_reference): the chart plus three symbols whose bars start later (different bars at every chart time)
   and, on cTrader, one unknown symbol. Every alert / Print must equal the independent Python reference: chart alerts unchanged, each
   symbol listed exactly when the scanned signal holds on that symbol's bar that just closed. Variants: cTrader GetIndexByTime rounding
   both ways (the reference does not say), NinjaTrader shared-timestamp order both ways. Mutants must change the result.
Not NinjaTrader, not cTrader (UNTESTED_RUNTIME). usage: python check_cs_scan.py   (needs node and the .NET 8 SDK; DOTNET=... to override)"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bsv_py_reference as R

ROOT = pathlib.Path(__file__).resolve().parents[2]; HERE = ROOT / "scripts/site"; EV = HERE / "cs_eval"
DOTNET = os.environ.get("DOTNET", "/workspace/tools/dotnet/dotnet" if pathlib.Path("/workspace/tools/dotnet/dotnet").exists() else "dotnet")
ENV = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1")
FAILS, N = [], [0]
OFFS = {"EURUSD": 5, "GBPUSD": 17, "USDJPY": 160}  # symbol bar m opens at chart bar m + offset (a later start)
def sym_bars(k):  # each symbol gets its own synthetic bars (other swings than the chart), so reading the chart instead changes the result
    out, c0 = [], 100.0
    for i in range(R.NB):
        o = c0; c0 = 100 + (12 + 4 * k) * R.math.sin(i / (11 + 5 * k)) + (2 + k) * R.math.sin(i * (1.3 + 0.2 * k))
        out.append({"t": R.T0 + i * R.STEP, "open": o, "high": max(o, c0) + 0.4 + 0.2 * abs(R.math.sin(i + k)), "low": min(o, c0) - 0.6, "close": c0})
    return out
def ref_on(rec, bars, sig, osc):  # the independent Python reference on another bar set (re-bases the module globals, then restores them)
    keep = [dict(b) for b in R.bars]; R.bars[:] = bars; R.use_rounded(12)
    try:
        V, S, val, boo = R.reference(rec); return list(boo(sig)), [x if R.fin(x) else None for x in val(osc)]
    finally:
        R.bars[:] = keep; R.use_rounded(12)
LIVE = 300
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg)
def render(recipe_path, target): return subprocess.run(["node", str(ROOT / "trader-toolkit/generator/render.mjs"), str(recipe_path), "--target", target], capture_output=True, text=True, check=True).stdout
PROJ = """<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework><OutputType>%s</OutputType><Nullable>disable</Nullable>
<TreatWarningsAsErrors>%s</TreatWarningsAsErrors><ImplicitUsings>disable</ImplicitUsings><NoWarn>CS0649;CS0169;CS0414</NoWarn></PropertyGroup></Project>"""
def build(files, exe, strict=True):
    d = pathlib.Path(tempfile.mkdtemp(prefix="bsv-cs-"))
    for name, text in files.items(): (d / name).write_text(text)
    (d / "p.csproj").write_text(PROJ % ("Exe" if exe else "Library", "true" if strict else "false"))
    r = subprocess.run([DOTNET, "build", str(d / "p.csproj"), "-nologo", "-v", "q", "-o", str(d / "out")], capture_output=True, text=True, env=ENV, timeout=600)
    return d, r
def run(d, data):
    (d / "data.json").write_text(json.dumps(data)); r = subprocess.run([DOTNET, str(d / "out/p.dll"), str(d / "data.json"), str(d / "o.txt")], capture_output=True, text=True, env=ENV, timeout=600)
    return r, ((d / "o.txt").read_text().splitlines() if (d / "o.txt").exists() else [])

def main():
    recipes = sorted((ROOT / "trader-toolkit/recipes").glob("*.json"))
    # 1) NinjaTrader static compile of every recipe
    nt = {p.stem: render(p, "ninjatrader") for p in recipes}
    d, r = build({"NinjaEval.cs": (EV / "NinjaEval.cs").read_text(), **{f"{k}.cs": v for k, v in nt.items()}}, exe=False)
    ok(r.returncode == 0, "ninjatrader: all recipes compile against the BSV NinjaScript stand-in: " + (r.stdout + r.stderr)[-1500:])
    ok(all(not re.search(r"\b(EnterLong|EnterShort|ExitLong|ExitShort|SubmitOrder\w*)\b", v) for v in nt.values()), "ninjatrader: no order methods")
    shutil.rmtree(d, ignore_errors=True)
    # 2) runs of the scan recipe
    out = {"target": "ninjatrader+ctrader (BSV C# stand-ins)", "ninjatrader_compiled": len(nt)}
    for p in recipes:
        rec = json.loads(p.read_text()); sc = [b for b in rec["blocks"] if b["type"] == "scanner.symbol_set"]
        if not sc: continue
        sid = sc[0]["id"]; sig = sc[0].get("params", {}).get("signal") or next(b["params"]["when"] for b in rec["blocks"] if b["type"] == "alert.condition")
        alert = next(b for b in rec["blocks"] if b["type"] == "alert.condition" and b["params"]["when"] == sig)["params"]["message"]
        osc = next(b["params"]["oscillator"] for b in rec["blocks"] if b["id"] == sig)
        w, rs = ref_on(rec, [dict(b) for b in R.bars], sig, osc); SW, SB = {}, {}
        for k, s in enumerate(OFFS, 1): SB[s] = sym_bars(k); SW[s], srs = ref_on(rec, SB[s], sig, osc); SB[s] = {"off": OFFS[s], "bars": [[b["open"], b["high"], b["low"], b["close"]] for b in SB[s]], "rsi": srs}
        data = {"bars": [[b["open"], b["high"], b["low"], b["close"]] for b in R.bars], "rsi": rs,
                "t0": R.T0.strftime("%Y-%m-%dT%H:%M:%S"), "step_min": 15, "symbols": SB, "live_from": LIVE}
        NB = len(R.bars)
        # ---- cTrader
        ct = render(p, "ctrader"); W = int(re.search(r"const int Warmup = (\d+);", ct).group(1))
        names = list(OFFS) + ["BSVNOPE"]
        want_ct = ["-1|BSV scan %s: cannot load BSVNOPE: symbol not found" % sid]
        for n in range(LIVE, NB):
            if w[n - 1]: want_ct.append(f"{n}|{alert}")
            js = {s: n - OFFS[s] - 1 for s in OFFS}; skipped = 1 + sum(1 for j in js.values() if j < W); hits = [s for s, j in js.items() if j >= W and SW[s][j]]
            want_ct.append(f"{n}|BSV scan {sid}: {skipped} symbol(s) skipped, no data yet")
            if hits: want_ct.append(f"{n}|BSV scan {sid}: " + " ".join(hits))
        hits_ct = sum(len(l.split(":", 1)[1].split()) for l in want_ct if re.match(rf"^\d+\|BSV scan {sid}: [A-Z]", l))
        def ct_run(code, round_up):
            d, r = build({"CAlgoEval.cs": (EV / "CAlgoEval.cs").read_text(), "CtHarness.cs": (EV / "CtHarness.cs").read_text(), "g.cs": code}, exe=True, strict=False)
            if r.returncode: shutil.rmtree(d, ignore_errors=True); return None, (r.stdout + r.stderr)[-800:]
            res, lines = run(d, dict(data, list=",".join(names), round_up=round_up)); shutil.rmtree(d, ignore_errors=True)
            return lines, res.stderr[-800:]
        for ru in (False, True):
            got, err = ct_run(ct, ru)
            ok(got == want_ct, f"ctrader {p.stem}: Print lines = reference (GetIndexByTime {'rounds up' if ru else 'rounds down'}); {len(got or [])} vs {len(want_ct)} lines; first diff: "
               + str(next(((a, b) for a, b in zip(got or [], want_ct) if a != b), None)) + " " + err)
        CT_MUT = [("scan reads the forming bar", "while (k >= 0 && s.OpenTimes[k] >= t) k--;", "while (k >= 0 && s.OpenTimes[k] > t) k--;"),
                  ("scan keeps the chart bars", f"                    _b = _scanBars_{sid}[k];\n", ""),
                  ("scan keeps the chart indicator", f"                    _c_{osc} = _scan_{osc}[k];\n", ""),
                  ("chart bars not restored after the scan", "                }\n                _b = Bars;\n", "                }\n")]
        caught_ct = 0
        for label, a, b in CT_MUT:
            got, _ = ct_run(ct.replace(a, b, 1), False) if a in ct else (want_ct, "")
            ok(a in ct and got != want_ct, f"ctrader mutant not caught: {label}"); caught_ct += (a in ct and got != want_ct)
        # ---- NinjaTrader
        ntc = nt[p.stem]; Wn = int(re.search(r"const int Warmup = (\d+);", ntc).group(1))
        want_nt = sorted([f"0|{m}|{alert}" for m in range(Wn, NB) if w[m]] + [f"{k}|{m}|BSV scan {sid}: {s}" for k, s in enumerate(OFFS, 1) for m in range(Wn, NB - OFFS[s]) if SW[s][m]])
        def nt_run(code, rev):
            d, r = build({"NinjaEval.cs": (EV / "NinjaEval.cs").read_text(), "NtHarness.cs": (EV / "NtHarness.cs").read_text(), "g.cs": code}, exe=True, strict=False)
            if r.returncode: shutil.rmtree(d, ignore_errors=True); return None, (r.stdout + r.stderr)[-800:]
            res, lines = run(d, dict(data, reverse_ties=rev)); shutil.rmtree(d, ignore_errors=True)
            return sorted(lines), res.stderr[-800:]
        for rev in (False, True):
            got, err = nt_run(ntc, rev)
            ok(got == want_nt, f"ninjatrader {p.stem}: Alert lines = reference (shared timestamps: {'symbols first' if rev else 'chart first'}); {len(got or [])} vs {len(want_nt)}; "
               + str(sorted(set(got or []) ^ set(want_nt))[:4]) + " " + err)
        NT_MUT = [("scan evaluates the chart series", "                _s = BarsInProgress;\n", "                _s = 0;\n"),
                  ("scan reads the bar before the one that closed", f"CurrentBars[_s] >= Warmup && S_{sig}(0)", f"CurrentBars[_s] >= Warmup && S_{sig}(1)"),
                  ("scan keeps the chart indicator", f"return _s == 0 ? _{osc}[ago] : _scan_{osc}[_s - 1][ago];", f"return _{osc}[ago];"),
                  ("chart series not restored after a symbol", "                _s = 0;\n                return;\n", "                return;\n")]
        caught_nt = 0
        for label, a, b in NT_MUT:
            got, _ = nt_run(ntc.replace(a, b, 1), False) if a in ntc else (want_nt, "")
            ok(a in ntc and got != want_nt, f"ninjatrader mutant not caught: {label}"); caught_nt += (a in ntc and got != want_nt)
        out.update({"scan_recipe": p.stem, "ctrader_scan_hits": hits_ct, "ninjatrader_scan_alerts": sum(1 for l in want_nt if not l.startswith("0|")),
                    "chart_alerts_nt": sum(1 for l in want_nt if l.startswith("0|")), "mutants_caught": caught_ct + caught_nt, "mutants": len(CT_MUT) + len(NT_MUT)})
        ok(hits_ct >= 3 and out["ninjatrader_scan_alerts"] >= 3, "scan must hit on the test bars")
    out.update({"checks": N[0], "failures": len(FAILS), "fail": FAILS, "note": "BSV C# stand-ins built from the NinjaTrader 8 / cTrader references; not NinjaTrader or cTrader (UNTESTED_RUNTIME)"})
    print(json.dumps(out))
    return 1 if FAILS else 0

if __name__ == "__main__":
    sys.exit(main())
