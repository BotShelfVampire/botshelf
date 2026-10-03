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
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
let checks = 0, failures = 0, files = 0, alertsSeen = 0;
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
  const V = new Map(), S = new Map(), byId = new Map(recipe.blocks.map(b => [b.id, b]));
  const isBool = (t) => /^(signal|filter|alert)\./.test(t || '');
  const val = (ref) => pxOf[ref] || (isBool(byId.get(ref)?.type) ? get(ref, S).map(Number) : get(ref, V));
  const boolOf = (ref) => isBool(byId.get(ref)?.type) ? get(ref, S) : val(ref).map(v => fin(v) && v !== 0);
  const done = new Set();
  function get(ref, m) { compute(byId.get(ref)); return m.get(ref) || new Array(NB).fill(m === S ? false : NaN); }
  function compute(b) {
    if (!b || done.has(b.id)) return; done.add(b.id);
    const p = b.params || {};
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
      case 'signal.threshold': { const L = val(p.left), x = Number(p.value), op = ['>', '>=', '<', '<=', '==', '!='].includes(p.op) ? p.op : '>=';
        S.set(b.id, L.map(v => fin(v) && { '>': v > x, '>=': v >= x, '<': v < x, '<=': v <= x, '==': v === x, '!=': v !== x }[op])); break; }
      case 'signal.combine': { const list = (p.signals || []).map(boolOf); S.set(b.id, new Array(NB).fill(0).map((_, i) => list.length ? (p.mode === 'any' ? list.some(a => a[i]) : list.every(a => a[i])) : false)); break; }
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
  const keys = [...plots.map((_, k) => 'P' + (k + 1)), ...alerts.map((_, k) => 'A' + (k + 1))];
  ok(Object.keys(ex).every(k => EXPORT_KEYS.has(k)), f, 'only documented Indicator fields: ' + Object.keys(ex));
  ok(/^[A-Za-z][A-Za-z0-9]*$/.test(ex.name) && typeof ex.description === 'string' && ex.description.length > 0, f, 'name/description');
  ok(typeof ex.calculator === 'function' && typeof ex.calculator.prototype.map === 'function' && typeof ex.calculator.prototype.init === 'function', f, 'calculator class with init/map');
  ok(ex.params && typeof ex.params === 'object' && Object.keys(ex.params).length === 0, f, 'params object');
  ok(ex.inputType === 'bars', f, 'inputType bars');
  ok(ex.areaChoice === (recipe.overlay ? 'overlay' : 'new'), f, 'areaChoice follows overlay');
  ok(Array.isArray(ex.tags) && ex.tags.every(t => typeof t === 'string'), f, 'tags');
  ok(JSON.stringify(Object.keys(ex.plots)) === JSON.stringify(keys) && Object.values(ex.plots).every(p => typeof p.title === 'string' && Object.keys(p).join() === 'title'), f, 'plots P*/A* with titles');
  ok(JSON.stringify(L.plotterCalls.map(x => x[1])) === JSON.stringify(keys) && L.plotterCalls.every(([t, n]) => t === (n[0] === 'A' ? 'dots' : 'singleline')), f, 'plotter: lines for plots, dots for alerts');
  ok(L.required.length <= 1, f, 'requires only predef');
  ok(alerts.length ? JSON.stringify(ex.shifts) === JSON.stringify(Object.fromEntries(alerts.map((_, k) => ['A' + (k + 1), -1]))) : ex.shifts === undefined, f, 'alert dots shifted onto the closed bar');
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
    if (/^indicator\.(sma|ema|rsi|atr)$/.test(b.type)) {
      const want = ref.V.get(b.id), got = A.calc.bars.map(s => s['V_' + k]);
      let worst = 0, warm = 0; for (let i = 0; i < NB; i++) { if (!fin(want[i])) { if (fin(got[i])) warm++; continue; } worst = Math.max(worst, Math.abs(got[i] - want[i]) / Math.max(1, Math.abs(want[i]))); }
      ok(worst < 1e-9 && warm === 0, f, `${b.id} (${b.type}) equals reference on every bar: worst ${worst}, values while warming up ${warm}`);
    }
    if (/^(signal\.(cross|threshold|combine)|filter\.session)$/.test(b.type)) {
      const want = ref.S.get(b.id), got = A.calc.bars.map(s => !!s['S_' + k]);
      const diff = want.reduce((n, w, i) => n + (!!w !== got[i]), 0);
      ok(diff === 0, f, `${b.id} (${b.type}) equals reference (${diff} bars differ)`);
    }
  }
  plots.forEach((pl, k) => { const want = ref.val(pl.params?.source), got = A.out.map(o => o['P' + (k + 1)]); ok(got.every((g, i) => fin(want[i]) ? Math.abs(g - want[i]) < 1e-9 : g === undefined), f, `P${k + 1} plots ${pl.params?.source}`); });
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
    ok(JSON.stringify(fired) === JSON.stringify(expect), f, `${key}: fired ${fired} expected ${expect}`);
  });
}
console.log(JSON.stringify({ target: 'tradovate', recipes: files, checks, failures, replay_alerts: alertsSeen, note: 'BSV stub of the documented Tradovate custom-indicator API in node:vm, not Tradovate' }));
process.exit(failures ? 1 : 0);
