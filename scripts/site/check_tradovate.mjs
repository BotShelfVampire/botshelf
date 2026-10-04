#!/usr/bin/env node
// Check of the generator's Tradovate custom-indicator (JavaScript) output for every recipe. The generated file is
// executed in a bare node:vm context (only Math, Number, Intl, Date) against a BSV stub of the documented API at
// tradovate.github.io/custom-indicators: module.exports fields, Calculator.init/map(d, index), BarInputEntity
// open/high/low/close/timestamp, require("./tools/predef") with plotters.singleline/dots only. NOT Tradovate.
// Checks: compiles; exports use only documented fields and values; only predef is required; no network/eval/order
// calls; indicator values equal an independent reference on every bar (NaN while warming up); signals equal an
// independent reference; re-running map() for the forming bar with other prices (as live updates do) changes
// nothing that is already closed; alert dots sit on closed bars only, once per bar, with no misses.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { execFileSync } from 'node:child_process';
import os from 'node:os';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
const lookBackAlerts = {}; // recipe -> bars where the alert condition holds, for recipes that use signal.recent
let checks = 0, failures = 0, files = 0, panelsSeen = 0, hooksSeen = 0, alertsSeen = 0, pivSeen = 0, mutCaught = 0, zoneSeen = 0, htfSeen = 0;
const fail = (f, m) => { failures++; console.error('FAIL', f, m); };
const ok = (c, f, m) => { checks++; if (!c) fail(f, m); };
const fin = Number.isFinite;
const EXPORT_KEYS = new Set(['name', 'description', 'calculator', 'params', 'inputType', 'areaChoice', 'tags', 'plots', 'plotter', 'shifts', 'schemeStyles']);

// --- bars: 15-minute bars in January 2026 (before any US/UK DST change, so New York = UTC-5, London = UTC+0) ---
const NB = 1200, R0 = NB - 150, t0 = Date.UTC(2026, 0, 5), STEP = 15 * 60e3;
const bars = []; let c0 = 100;
for (let i = 0; i < NB; i++) { const o = c0; c0 = 100 + 10 * Math.sin(i / 15) + 3 * Math.sin(i * 1.7); bars.push({ time: t0 + i * STEP, open: o, high: Math.max(o, c0) + 0.5 + 0.3 * Math.abs(Math.sin(i)), low: Math.min(o, c0) - 0.5, close: c0 }); }
if (bars[NB - 1].time >= Date.UTC(2026, 2, 8)) throw new Error('bars must end before the DST change');
const OFFSET = { 'UTC': 0, 'Etc/UTC': 0, 'Europe/London': 0, 'America/New_York': -300 };

// --- independent reference ---
const pxOf = { open: bars.map(b => b.open), high: bars.map(b => b.high), low: bars.map(b => b.low), close: bars.map(b => b.close) };
pxOf.hl2 = bars.map(b => (b.high + b.low) / 2); pxOf.hlc3 = bars.map(b => (b.high + b.low + b.close) / 3); pxOf.ohlc4 = bars.map(b => (b.open + b.high + b.low + b.close) / 4);
const refSma = (x, p) => x.map((_, i) => i < p - 1 ? NaN : x.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p);
function refEma(x, p) { const a = 2 / (p + 1); let e = NaN; return x.map((v, i) => { if (i === p - 1) e = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) e = a * v + (1 - a) * e; return i >= p - 1 ? e : NaN; }); }
function refRma(x, p) { let r = NaN; return x.map((v, i) => { if (i === p - 1) r = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) r = (r * (p - 1) + v) / p; return i >= p - 1 ? r : NaN; }); }
const TR = bars.map((b, i) => i === 0 ? NaN : Math.max(b.high, bars[i - 1].close) - Math.min(b.low, bars[i - 1].close));
function reference(recipe) {
  const V = new Map(), S = new Map(), RG = new Set(), byId = new Map(recipe.blocks.map(b => [b.id, b]));
  const isBool = (t) => /^(signal|filter|alert)\./.test(t || '');
  const val = (ref) => pxOf[ref] || (isBool(byId.get(ref)?.type) ? get(ref, S).map(Number) : get(ref, V));
  const boolOf = (ref) => isBool(byId.get(ref)?.type) ? get(ref, S) : val(ref).map(v => fin(v) && v !== 0);
  const done = new Set();
  function get(ref, m) { compute(byId.get(ref)); return m.get(ref) || new Array(NB).fill(m === S ? false : NaN); }
  function compute(b) {
    if (!b || done.has(b.id)) return; done.add(b.id);
    const p = b.params || {};
    if (p.timeframeRef) { // higher timeframe, written separately: group the bars into UTC-aligned periods; bar i sees only the periods before its own
      const tf = String(byId.get(p.timeframeRef)?.params?.timeframe ?? '').trim().toUpperCase(), dm = /^(\d*)D$/.exec(tf);
      const M = /^\d+$/.test(tf) ? +tf : dm ? (+dm[1] || 1) * 1440 : null;
      if (!M || M > 10080 || (dm && (+dm[1] || 1) > 7) || !/^indicator\.(sma|ema|rsi|atr)$/.test(b.type) || STEP >= M * 60e3) return; // unsupported or too-coarse chart bars: no value
      const per = [], idx = [];
      bars.forEach(x => { const k = Math.floor(x.time / (M * 60e3)), q = per[per.length - 1]; if (!q || q.k !== k) per.push({ k, o: x.open, h: x.high, l: x.low, c: x.close }); else { q.h = Math.max(q.h, x.high); q.l = Math.min(q.l, x.low); q.c = x.close; } idx.push(per.length - 1); });
      const hx = { open: per.map(q => q.o), high: per.map(q => q.h), low: per.map(q => q.l), close: per.map(q => q.c) };
      hx.hl2 = per.map(q => (q.h + q.l) / 2); hx.hlc3 = per.map(q => (q.h + q.l + q.c) / 3); hx.ohlc4 = per.map(q => (q.o + q.h + q.l + q.c) / 4);
      const x = hx[p.source || 'close'], n = p.length; let ser;
      if (b.type === 'indicator.sma') ser = refSma(x, n); else if (b.type === 'indicator.ema') ser = refEma(x, n);
      else if (b.type === 'indicator.rsi') { const g = x.slice(1).map((w, i) => Math.max(w - x[i], 0)), l = x.slice(1).map((w, i) => Math.max(x[i] - w, 0)), G = refRma(g, n), Lo = refRma(l, n); ser = [NaN, ...G.map((u, i) => !fin(u) ? NaN : u + Lo[i] === 0 ? 50 : 100 * u / (u + Lo[i]))]; }
      else { const tr = per.slice(1).map((q, i) => Math.max(q.h, per[i].c) - Math.min(q.l, per[i].c)); ser = [NaN, ...refRma(tr, n)]; }
      V.set(b.id, bars.map((_, i) => idx[i] > 0 ? ser[idx[i] - 1] : NaN));
      return;
    }
    switch (b.type) {
      case 'indicator.sma': V.set(b.id, refSma(pxOf[p.source || 'close'], p.length)); break;
      case 'indicator.ema': V.set(b.id, refEma(pxOf[p.source || 'close'], p.length)); break;
      case 'indicator.rsi': { const x = pxOf[p.source || 'close']; const g = x.slice(1).map((w, i) => Math.max(w - x[i], 0)), l = x.slice(1).map((w, i) => Math.max(x[i] - w, 0)); const G = refRma(g, p.length), Lo = refRma(l, p.length); V.set(b.id, [NaN, ...G.map((u, i) => !fin(u) ? NaN : u + Lo[i] === 0 ? 50 : 100 * u / (u + Lo[i]))]); break; }
      case 'indicator.atr': V.set(b.id, [NaN, ...refRma(TR.slice(1), p.length)]); break;
      case 'filter.session': {
        const m = /^(\d{2})(\d{2})-(\d{2})(\d{2})$/.exec(p.session || '0000-2359'), st = +m[1] * 60 + +m[2], en = +m[3] * 60 + +m[4];
        const off = OFFSET[p.timezone || 'Etc/UTC']; if (off === undefined) throw new Error('no reference offset for ' + p.timezone);
        S.set(b.id, bars.map(x => { const mm = (((Math.floor(x.time / 60e3) + off) % 1440) + 1440) % 1440; return st <= en ? mm >= st && mm < en : mm >= st || mm < en; }));
        break;
      }
      case 'signal.cross': { const L = val(p.left), R = val(p.right), up = p.direction !== 'below'; S.set(b.id, L.map((v, i) => i > 0 && (up ? v > R[i] && L[i - 1] <= R[i - 1] : v < R[i] && L[i - 1] >= R[i - 1]))); break; }
      case 'signal.threshold': { const L = val(p.left), R = typeof p.right === 'string' && p.right ? val(p.right) : null, op = ['>', '>=', '<', '<=', '==', '!='].includes(p.op) ? p.op : '>=';
        S.set(b.id, L.map((v, i) => { const x = R ? R[i] : Number(p.value); return fin(v) && fin(x) && { '>': v > x, '>=': v >= x, '<': v < x, '<=': v <= x, '==': v === x, '!=': v !== x }[op]; })); break; }
      case 'signal.recent': { const sg = boolOf(p.signal); S.set(b.id, sg.map((_, i) => { for (let k = 1; k <= p.bars && i - k >= 0; k++) if (sg[i - k]) return true; return false; })); break; } // written separately: previous bars only
      case 'signal.combine': { const list = (p.signals || []).map(boolOf); S.set(b.id, new Array(NB).fill(0).map((_, i) => list.length ? (p.mode === 'any' ? list.some(a => a[i]) : list.every(a => a[i])) : false)); break; }
      case 'structure.range': { // written separately: each run of bars inside the window gets running extremes; after the run they are held
        const tr = Array.isArray(p.track) ? p.track : [];
        if (!(tr.length && tr.every((x, i) => (x === 'high' || x === 'low') && tr.indexOf(x) === i)) || !isBool(byId.get(p.during)?.type)) break;
        const ins = boolOf(p.during), hi = new Array(NB).fill(NaN), lo = new Array(NB).fill(NaN);
        for (let i = 0; i < NB;) {
          if (!ins[i]) { if (i) { hi[i] = hi[i - 1]; lo[i] = lo[i - 1]; } i++; continue; }
          let j = i; while (j < NB && ins[j]) { hi[j] = Math.max(...bars.slice(i, j + 1).map(x => x.high)); lo[j] = Math.min(...bars.slice(i, j + 1).map(x => x.low)); j++; }
          i = j;
        }
        V.set(b.id + '.high', hi); V.set(b.id + '.low', lo); RG.add(b.id); break;
      }
      case 'signal.breakout': {
        const r = byId.get(p.range); compute(r); if (!r || !RG.has(r.id) || !['either', 'above', 'below'].includes(p.direction || 'either')) break;
        const tr = r.params.track; if (!(tr.includes('high') && tr.includes('low'))) break;
        const ins = boolOf(r.params.during), hi = V.get(r.id + '.high'), lo = V.get(r.id + '.low'), c = pxOf.close, d = p.direction || 'either';
        S.set(b.id, bars.map((_, i) => { if (i === 0 || ins[i] || !fin(hi[i])) return false; const up = c[i] > hi[i] && c[i - 1] <= hi[i], dn = c[i] < lo[i] && c[i - 1] >= lo[i]; return d === 'either' ? up || dn : d === 'above' ? up : dn; }));
        break;
      }
      case 'structure.pivot': { // written separately from the generator: test every bar j against its whole window, publish on j + right, hold
        const hv = (p.source || 'close') === 'close' ? pxOf.close : pxOf.high, lv = (p.source || 'close') === 'close' ? pxOf.close : pxOf.low, ph = new Map(), pl = new Map();
        for (let j = p.left; j < NB - p.right; j++) {
          let a = true, z = true;
          for (let n = j - p.left; n < j; n++) { if (!(hv[j] > hv[n])) a = false; if (!(lv[j] < lv[n])) z = false; }
          for (let n = j + 1; n <= j + p.right; n++) { if (!(hv[j] >= hv[n])) a = false; if (!(lv[j] <= lv[n])) z = false; }
          if (a) ph.set(j + p.right, j); if (z) pl.set(j + p.right, j);
        }
        let ch = NaN, cl = NaN; const H = [], Lw = [];
        for (let i = 0; i < NB; i++) { if (ph.has(i)) ch = hv[ph.get(i)]; if (pl.has(i)) cl = lv[pl.get(i)]; H.push(ch); Lw.push(cl); }
        V.set(b.id + '.high', H); V.set(b.id + '.low', Lw); V.set(b.id + '#ph', [...ph.values()]); V.set(b.id + '#pl', [...pl.values()]); V.set(b.id + '#hv', hv); V.set(b.id + '#lv', lv);
        break;
      }
      case 'signal.liquidity_sweep': {
        compute(byId.get(p.pivot)); const A = val(p.atr), H = V.get(p.pivot + '.high'), Lw = V.get(p.pivot + '.low'), m = Number(p.minAtrFraction || 0);
        S.set(b.id, bars.map((x, i) => i > 0 && fin(A[i]) && ((fin(H[i - 1]) && x.high > H[i - 1] && x.high - H[i - 1] >= m * A[i] && x.close < H[i - 1]) || (fin(Lw[i - 1]) && x.low < Lw[i - 1] && Lw[i - 1] - x.low >= m * A[i] && x.close > Lw[i - 1]))));
        break;
      }
      case 'signal.divergence': { // pairs of consecutive pivots over the whole series; marked on the confirming bar
        const pb = byId.get(p.pivot); compute(pb); const O = val(p.oscillator), R_ = pb.params.right, out = new Array(NB).fill(false), d = p.direction || 'both';
        const hs = V.get(pb.id + '#ph'), ls = V.get(pb.id + '#pl'), hv = V.get(pb.id + '#hv'), lv = V.get(pb.id + '#lv');
        if (d !== 'bullish') for (let n = 1; n < hs.length; n++) { const a = hs[n - 1], j = hs[n]; if (hv[j] > hv[a] && fin(O[j]) && fin(O[a]) && O[j] < O[a]) out[j + R_] = true; }
        if (d !== 'bearish') for (let n = 1; n < ls.length; n++) { const a = ls[n - 1], j = ls[n]; if (lv[j] < lv[a] && fin(O[j]) && fin(O[a]) && O[j] > O[a]) out[j + R_] = true; }
        S.set(b.id, out);
        break;
      }
      case 'visual.plot': case 'alert.condition': break;
      default: if (isBool(b.type)) S.set(b.id, new Array(NB).fill(false)); else V.set(b.id, new Array(NB).fill(NaN));
    }
  }
  recipe.blocks.forEach(compute);
  return { V, S, val, boolOf };
}

// --- stub of the documented API ---
function load(code, f) {
  const plotterCalls = [];
  const predef = Object.freeze({ plotters: Object.freeze({ singleline: (n) => (plotterCalls.push(['singleline', n]), { type: 'line', fields: [n] }), dots: (n) => (plotterCalls.push(['dots', n]), { type: 'dots', fields: [n] }) }) });
  const required = [];
  const module = { exports: {} };
  const ctx = vm.createContext({ module, exports: module.exports, require: (m) => { required.push(m); if (m !== './tools/predef') throw new Error('unexpected require ' + m); return predef; }, Math, Number, Intl, Date });
  new vm.Script(code, { filename: f }).runInContext(ctx, { timeout: 2000 });
  return { ex: module.exports, required, plotterCalls };
}
const entity = (b) => ({ open: () => b.open, high: () => b.high, low: () => b.low, close: () => b.close, value: () => b.close, timestamp: () => new Date(b.time), volume: () => 0 });

for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
  const code = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), path.join(dir, f), '--target', 'tradovate'], { encoding: 'utf8' });
  files++;
  const body = code.replace(/\/\/.*$/gm, '');
  ok(/^\/\/ End BSV generated starter\.\s*$/m.test(code), f, 'end marker');
  ok(/Not runtime tested by BSV/.test(code), f, 'not-runtime-tested notice');
  ok(!/\b(fetch|XMLHttpRequest|WebSocket|eval|Function|import|process|globalThis|setTimeout|setInterval|order|Order)\b/.test(body), f, 'no network, eval, timers or order calls');
  let L;
  try { L = load(code, f); checks++; } catch (e) { fail(f, 'load: ' + e.message); continue; }
  const { ex } = L;
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot'), alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const byIdR = new Map(recipe.blocks.map(b => [b.id, b]));
  const zones = recipe.blocks.filter(b => b.type === 'visual.zone' && /^structure\.(pivot|range)$/.test(byIdR.get(b.params?.source)?.type || '')); // pivot and range zones are rendered
  recipe.blocks.filter(b => b.type === 'visual.zone' && !zones.includes(b)).forEach(b => ok(code.includes(`// TODO unsupported block visual.zone: ${String(b.id).replace(/[^A-Za-z0-9_]/g, '_')}`), f, `${b.id}: zone without a pivot / range source left as TODO`));
  const hooks = recipe.blocks.filter(b => b.type === 'alert.webhook'); // every recipe webhook here is valid (see webhookOk), so each is rendered
  const keys = [...plots.map((_, k) => 'P' + (k + 1)), ...zones.flatMap((_, n) => ['Z' + (n + 1) + 'H', 'Z' + (n + 1) + 'L']), ...alerts.map((_, k) => 'A' + (k + 1)), ...hooks.map((_, n) => 'W' + (n + 1))];
  ok(Object.keys(ex).every(k => EXPORT_KEYS.has(k)), f, 'only documented Indicator fields: ' + Object.keys(ex));
  ok(/^[A-Za-z][A-Za-z0-9]*$/.test(ex.name) && typeof ex.description === 'string' && ex.description.length > 0, f, 'name/description');
  ok(typeof ex.calculator === 'function' && typeof ex.calculator.prototype.map === 'function' && typeof ex.calculator.prototype.init === 'function', f, 'calculator class with init/map');
  ok(ex.params && typeof ex.params === 'object' && Object.keys(ex.params).length === 0, f, 'params object');
  ok(ex.inputType === 'bars', f, 'inputType bars');
  ok(ex.areaChoice === (recipe.overlay ? 'overlay' : 'new'), f, 'areaChoice follows overlay');
  ok(Array.isArray(ex.tags) && ex.tags.every(t => typeof t === 'string'), f, 'tags');
  ok(JSON.stringify(Object.keys(ex.plots)) === JSON.stringify(keys) && Object.values(ex.plots).every(p => typeof p.title === 'string' && Object.keys(p).join() === 'title'), f, 'plots P*/A* with titles');
  ok(JSON.stringify(L.plotterCalls.map(x => x[1])) === JSON.stringify(keys) && L.plotterCalls.every(([t, n]) => t === (/^[AW]/.test(n) ? 'dots' : 'singleline')), f, 'plotter: lines for plots, dots for alerts and webhooks');
  ok(L.required.length <= 1, f, 'requires only predef');
  const dotKeys = keys.filter(k => /^[AW]/.test(k));
  ok(dotKeys.length ? JSON.stringify(ex.shifts) === JSON.stringify(Object.fromEntries(dotKeys.map(k => [k, -1]))) : ex.shifts === undefined, f, 'alert and webhook dots shifted onto the closed bar');
  ok(ex.schemeStyles && Object.keys(ex.schemeStyles).join() === 'dark' && Object.keys(ex.schemeStyles.dark).every(k => keys.includes(k)), f, 'schemeStyles.dark keys are plots');
  // full run
  const run = (perturb) => {
    const calc = new ex.calculator(); calc.props = {}; calc.init();
    const out = [], forming = [];
    for (let i = 0; i < NB; i++) {
      if (perturb && i >= R0) for (const dv of [7, -9, 3]) { const b = bars[i]; const o = calc.map(entity({ ...b, open: b.open + dv, high: b.high + Math.abs(dv) + 1, low: b.low - Math.abs(dv) - 1, close: b.close - dv }), i); forming.push([i, o]); }
      out.push(calc.map(entity(bars[i]), i));
    }
    return { calc, out, forming };
  };
  let A, B;
  try { A = run(false); B = run(true); checks++; } catch (e) { fail(f, 'run: ' + e.message); continue; }
  ok(A.out.every(o => o && Object.keys(o).every(k => keys.includes(k) && (o[k] === undefined || fin(o[k])))), f, 'map() returns only declared plots, numbers or undefined');
  const ref = reference(recipe);
  for (const b of recipe.blocks) {
    const k = String(b.id).replace(/[^A-Za-z0-9_]/g, '_');
    if (/^indicator\.(sma|ema|rsi|atr)$/.test(b.type) || (b.params || {}).timeframeRef) {
      const want = ref.V.get(b.id) || new Array(NB).fill(NaN), got = A.calc.bars.map(s => s['V_' + k]);
      let worst = 0, warm = 0; for (let i = 0; i < NB; i++) { if (!fin(want[i])) { if (fin(got[i])) warm++; continue; } worst = Math.max(worst, Math.abs(got[i] - want[i]) / Math.max(1, Math.abs(want[i]))); }
      ok(worst < 1e-9 && warm === 0, f, `${b.id} (${b.type}) equals reference on every bar: worst ${worst}, values while warming up ${warm}`);
    }
    if (/^(signal\.(cross|threshold|combine|liquidity_sweep|divergence|breakout)|filter\.session)$/.test(b.type)) {
      const want = ref.S.get(b.id), got = A.calc.bars.map(s => !!s['S_' + k]);
      const diff = want.reduce((n, w, i) => n + (!!w !== got[i]), 0);
      ok(diff === 0, f, `${b.id} (${b.type}) equals reference (${diff} bars differ)`);
      if (/sweep|divergence|breakout/.test(b.type)) { ok(want.some(Boolean), f, `${b.id} fires on the synthetic bars (comparison not vacuous)`); pivSeen++; }
    }
    if (b.type === 'structure.pivot' || (b.type === 'structure.range' && ref.V.has(b.id + '.high'))) for (const e of ['high', 'low']) {
      const want = ref.V.get(b.id + '.' + e), got = A.calc.bars.map(s => s['V_' + k + '_' + e]);
      const bad = want.reduce((n, w, i) => n + !((!fin(w) && !fin(got[i])) || Math.abs(w - got[i]) < 1e-12), 0);
      ok(bad === 0 && want.some(fin), f, `${b.id}.${e} (${b.type}) equals reference (${bad} bars differ)`);
    }
    if (b.type === 'structure.range' && ref.V.has(b.id + '.high')) { // mutant: a window that never resets must be caught
      const mc = code.replace(new RegExp(`const fresh = !p \\|\\| !p\\.R_${k};`), 'const fresh = !p;');
      let M4 = null; try { M4 = load(mc, f); } catch (e) {}
      if (mc !== code && M4) { const c6 = new M4.ex.calculator(); c6.props = {}; c6.init(); for (let i = 0; i < NB; i++) c6.map(entity(bars[i]), i);
        const w = ref.V.get(b.id + '.high'), caught = c6.bars.some((x, i) => fin(w[i]) ? !(Math.abs(x['V_' + k + '_high'] - w[i]) < 1e-12) : fin(x['V_' + k + '_high']));
        ok(caught, f, `mutant caught: ${b.id} window never resets`); if (caught) mutCaught++; }
      else ok(false, f, `range mutant could not be built for ${b.id}`);
    }
  }
  plots.forEach((pl, k) => { const want = ref.val(pl.params?.source), got = A.out.map(o => o['P' + (k + 1)]); ok(got.every((g, i) => fin(want[i]) ? Math.abs(g - want[i]) < 1e-9 : g === undefined), f, `P${k + 1} plots ${pl.params?.source}`); });
  // zone lines = the reference's held pivot high / low on every bar (undefined while none is confirmed); a swapped mutant must fail
  const zoneBad = (out) => zones.reduce((n, z, j) => n + ['high', 'low'].reduce((m, e) => { const want = ref.V.get(z.params.source + '.' + e), key = 'Z' + (j + 1) + e[0].toUpperCase();
    return m + out.reduce((c, o, i) => c + !(fin(want[i]) ? Math.abs(o[key] - want[i]) < 1e-12 : o[key] === undefined), 0); }, 0), 0);
  zones.forEach((z, j) => { const w = ref.V.get(z.params.source + '.high'); ok(w.some(fin) && ref.V.get(z.params.source + '.low').some(fin), f, `Z${j + 1}: reference has confirmed pivots (not vacuous)`); zoneSeen++; });
  if (zones.length) {
    ok(zoneBad(A.out) === 0, f, `zone lines equal the reference pivot high / low (${zoneBad(A.out)} values differ)`);
    const mc = code.replace(/Z1H: out\(s\.V_(\w+)_high\), Z1L: out\(s\.V_\w+_low\)/, 'Z1H: out(s.V_$1_low), Z1L: out(s.V_$1_high)');
    let M2; try { M2 = load(mc, f); } catch (e) { M2 = null; }
    if (mc !== code && M2) { const c3 = new M2.ex.calculator(); c3.props = {}; c3.init(); const o3 = []; for (let i = 0; i < NB; i++) o3.push(c3.map(entity(bars[i]), i)); const caught = zoneBad(o3) > 0; ok(caught, f, 'mutant caught: zone lines swapped'); if (caught) mutCaught++; }
    else ok(false, f, 'zone swap mutant could not be built');
  }
  // higher timeframe: values must not be vacuous; using the forming higher-timeframe bar (a repainting mutant) must be caught; too-coarse chart bars give no value
  const htfB = recipe.blocks.filter(b => /^indicator\./.test(b.type) && (b.params || {}).timeframeRef && ref.V.has(b.id));
  if (htfB.length) {
    htfB.forEach(b => { ok(ref.V.get(b.id).some(fin), f, `${b.id}: higher-timeframe reference has values (not vacuous)`); htfSeen++; });
    const mc = code.replace(/this\.BsvHtf\(p\.H_(\w+), ("\w+"), (\d+), p\.hb_(\w+),/g, 'this.BsvHtf(p.H_$1, $2, $3, s.hb_$4,');
    let M3 = null; try { M3 = load(mc, f); } catch (e) {}
    if (mc !== code && M3) { const c4 = new M3.ex.calculator(); c4.props = {}; c4.init(); for (let i = 0; i < NB; i++) c4.map(entity(bars[i]), i);
      const caught = htfB.some(b => { const k = String(b.id).replace(/[^A-Za-z0-9_]/g, '_'), w = ref.V.get(b.id); return c4.bars.some((x, i) => fin(w[i]) ? !(Math.abs(x['V_' + k] - w[i]) <= 1e-9 * Math.max(1, Math.abs(w[i]))) : fin(x['V_' + k])); });
      ok(caught, f, 'mutant caught: higher timeframe reads the forming bar'); if (caught) mutCaught++; }
    else ok(false, f, 'higher-timeframe mutant could not be built');
    const cr = JSON.parse(JSON.stringify(recipe)); cr.blocks.forEach(b => { if (b.type === 'data.higher_timeframe') b.params.timeframe = '15'; });
    const cp = path.join(os.tmpdir(), 'bsv-tradovate-coarse-' + f); fs.writeFileSync(cp, JSON.stringify(cr));
    const ccode = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), cp, '--target', 'tradovate'], { encoding: 'utf8' }); fs.unlinkSync(cp);
    const C = load(ccode, f), c5 = new C.ex.calculator(); c5.props = {}; c5.init(); for (let i = 0; i < NB; i++) c5.map(entity(bars[i]), i);
    ok(/BsvHtf\(/.test(ccode) && htfB.every(b => c5.bars.every(x => !fin(x['V_' + String(b.id).replace(/[^A-Za-z0-9_]/g, '_')]))), f, 'higher timeframe equal to the chart step (15 min): no value, never chart-timeframe values');
  }
  // live updates: re-running the forming bar must not change any output, and alerts only read the closed bar
  ok(JSON.stringify(A.out) === JSON.stringify(B.out), f, 'outputs unchanged after forming-bar updates');
  alerts.forEach((al, k) => {
    const key = 'A' + (k + 1), cond = ref.boolOf(al.params?.when);
    const wobble = B.forming.filter(([i, o]) => o[key] !== A.out[i][key]).length;
    ok(wobble === 0, f, `${key}: forming-bar prices change the alert (${wobble})`);
    const fired = [], expect = [];
    for (let i = R0; i < NB; i++) { if (A.out[i][key] !== undefined) fired.push(i - 1); if (cond[i - 1]) expect.push(i - 1); }
    ok(A.out.every((o, i) => o[key] === undefined || (i > 0 && Math.abs(o[key] - (recipe.overlay ? bars[i - 1].close : 1)) < 1e-12)), f, `${key}: dot value`);
    alertsSeen += fired.length;
    if (recipe.blocks.some(b => b.type === 'signal.recent')) { const c = cond.filter(Boolean).length; lookBackAlerts[f.replace('.json', '')] = c; ok(c > 0, f, `${key}: alert condition with a look-back holds on the test bars (${c} bars)`); }
    ok(JSON.stringify(fired) === JSON.stringify(expect), f, `${key}: fired ${fired} expected ${expect}`);
  });
  // value panels: per-bar values of every shown field equal the reference; reading the bar before (a stale panel) must be caught
  const tbls = recipe.blocks.filter(b => b.type === 'visual.table' && new RegExp(`s\\.T_${String(b.id).replace(/[^A-Za-z0-9_]/g, '_')} = \\{`).test(code));
  recipe.blocks.filter(b => b.type === 'visual.table' && !tbls.includes(b)).forEach(b => ok(code.includes(`// TODO unsupported block visual.table: ${String(b.id).replace(/[^A-Za-z0-9_]/g, '_')}`), f, `${b.id}: panel without a showable field left as TODO`));
  const panelBad = (calc) => tbls.reduce((n, t) => { const k = String(t.id).replace(/[^A-Za-z0-9_]/g, '_'); let m = 0;
    for (let i = 0; i < NB; i++) { const T = calc.bars[i]['T_' + k] || {}; for (const fid of Object.keys(A.calc.bars[NB - 1]['T_' + k] || {})) {
      const isB = /^(signal|filter|alert)\./.test(byIdR.get(fid)?.type || ''), w = isB ? !!ref.S.get(fid)[i] : (ref.V.get(fid) || [])[i], g = T[fid];
      if (isB ? g !== w : !((!fin(w) && !fin(g)) || Math.abs(w - g) / Math.max(1, Math.abs(w)) < 1e-9)) m++; } } return n + m; }, 0);
  if (tbls.length) {
    const fids = tbls.flatMap(t => Object.keys(A.calc.bars[NB - 1]['T_' + String(t.id).replace(/[^A-Za-z0-9_]/g, '_')] || {}));
    ok(fids.length > 0 && fids.every(x => byIdR.has(x) || ref.V.has(x)), f, `panel fields known to the reference (${fids})`);
    ok(panelBad(A.calc) === 0, f, `panel values equal the reference on every bar (${panelBad(A.calc)} differ)`);
    ok(panelBad(B.calc) === 0, f, 'panel values unchanged after forming-bar updates');
    panelsSeen += tbls.length;
    const mc = code.replace(/(s\.T_\w+ = \{)([^\n]*)/g, (m0, a, b) => a + b.replace(/\bs\.([VS])_/g, '(p || s).$1_'));
    if (mc === code) ok(false, f, 'panel mutant could not be built');
    else { const M = load(mc, f), c2 = new M.ex.calculator(); c2.props = {}; c2.init(); for (let i = 0; i < NB; i++) c2.map(entity(bars[i]), i);
      const caught = panelBad(c2) > 0; ok(caught, f, 'mutant caught: panel reads the bar before'); if (caught) mutCaught++; }
  }
  // webhooks: dots on the closed bar where the condition held; the payload of that bar equals a separately written fill; never sent
  const fill = (pl, b) => { const g = (v) => String(Number(v.toPrecision(10))), F = { symbol: 'SYMBOL', timeframe: 'TIMEFRAME', time: new Date(b.time).toISOString().slice(0, 19), open: g(b.open), high: g(b.high), low: g(b.low), close: g(b.close) };
    return JSON.stringify(Object.fromEntries(Object.entries(pl).map(([k, x]) => [k, typeof x === 'string' ? x.split(/(\{\{[^}]*\}\})/).map(t => /^\{\{.*\}\}$/.test(t) ? F[t.slice(2, -2)] : t).join('') : x]))); };
  const hookBad = (calc, out) => hooks.reduce((n, h, j) => { const key = 'W' + (j + 1), k = String(h.id).replace(/[^A-Za-z0-9_]/g, '_'), cond = ref.boolOf(h.params.when);
    let m = 0; for (let i = 0; i < NB; i++) { if ((calc.bars[i]['J_' + k] ?? null) !== (cond[i] ? fill(h.params.payload, bars[i]) : null)) m++; if ((out[i][key] !== undefined) !== (i > 0 && !!cond[i - 1])) m++; } return n + m; }, 0);
  hooks.forEach((h, j) => { const cond = ref.boolOf(h.params.when), n = cond.filter(Boolean).length; ok(n > 0, f, `W${j + 1}: condition fires on the synthetic bars (not vacuous)`); hooksSeen += n; });
  if (hooks.length) {
    ok(hookBad(A.calc, A.out) === 0, f, `webhook payloads and dots equal the reference (${hookBad(A.calc, A.out)} differ)`);
    ok(hookBad(B.calc, B.out) === 0, f, 'webhook payloads unchanged after forming-bar updates');
    for (const [mn, from, to] of [['payload close read from the open', 'close: g(s.c)', 'close: g(s.o)'], ['payload from the bar before', 'this.bsvWebhook(', 'this.bsvWebhook(p ? p : s, '], ['dots on the forming bar', /W1: p && p\.S_/, 'W1: s.S_']]) {
      let mc = typeof from === 'string' ? code.split(from).join(to) : code.replace(from, to);
      if (mn === 'payload from the bar before') mc = mc.replace(/this\.bsvWebhook\(p \? p : s, (\{.*?\}), d\.timestamp\(\), s\)/g, 'this.bsvWebhook($1, d.timestamp(), p ? p : s)');
      if (mc === code) { ok(false, f, `webhook mutant could not be built: ${mn}`); continue; }
      let M; try { M = load(mc, f); } catch (e) { ok(false, f, `webhook mutant ${mn} failed to load`); continue; }
      const c2 = new M.ex.calculator(); c2.props = {}; c2.init(); const o2 = []; for (let i = 0; i < NB; i++) o2.push(c2.map(entity(bars[i]), i));
      const caught = hookBad(c2, o2) > 0; ok(caught, f, `mutant caught: webhook ${mn}`); if (caught) mutCaught++;
    }
  }
  // mutants of the pivot / sweep / divergence code: each must change the signals (the reference tells them apart)
  for (const [mn, from, to] of [['sweep without the close back inside', / && s\.c < p\.V_\w+_high\)/, ')'], ['sweep without the ATR distance', / && s\.h - p\.V_\w+_high >= [^&]+&&/, ' &&'],
    ['divergence oscillator test flipped', /&& x\[1\] < s\.dh_/, '&& x[1] > s.dh_'], ['divergence price test dropped', /x\[0\] < s\.dl_\w+\[0\] &&/, 'true &&']]) {
    if (!from.test(code)) continue;
    const sig = recipe.blocks.filter(b => /^signal\.(liquidity_sweep|divergence)$/.test(b.type)), mc = code.replace(from, to);
    if (!sig.length) continue;
    let M; try { M = load(mc, f); } catch (e) { ok(false, f, `mutant ${mn} failed to load`); continue; }
    const c2 = new M.ex.calculator(); c2.props = {}; c2.init();
    try { for (let i = 0; i < NB; i++) c2.map(entity(bars[i]), i); } catch (e) { ok(false, f, `mutant ${mn} threw ${e.message}`); continue; }
    const same = sig.every(b => { const k = String(b.id).replace(/[^A-Za-z0-9_]/g, '_'), w = ref.S.get(b.id); return c2.bars.every((s, i) => !!s['S_' + k] === !!w[i]); });
    ok(!same, f, `mutant caught: ${mn}`); if (!same) mutCaught++;
  }
}
console.log(JSON.stringify({ target: 'tradovate', recipes: files, checks, failures, replay_alerts: alertsSeen, webhook_payloads: hooksSeen, panels: panelsSeen, sweep_divergence_signals: pivSeen, zones: zoneSeen, htf_values: htfSeen, mutants_caught: mutCaught, look_back_alert_bars: lookBackAlerts, note: 'BSV stub of the documented Tradovate custom-indicator API in node:vm, not Tradovate' }));
process.exit(failures ? 1 : 0);
