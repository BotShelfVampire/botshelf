#!/usr/bin/env node
// BSV MQL5 SUBSET translator + stub of the documented MT5 custom-indicator API, run in node:vm, for the generator's mql5
// output (Issue #4). Not MetaTrader 5 and not MetaEditor: the generated subset is translated to JavaScript (types dropped,
// anything outside the subset rejected) and run against a BSV model of the documented calls (OnInit / OnCalculate with
// rates_total / prev_calculated, iMA / iRSI / iATR handles + CopyBuffer, ArraySetAsSeries, SetIndexBuffer, iTime /
// iBarShift, TimeToStruct, Alert). Built-in algorithms follow the MT5 example sources (Indicators/Examples): MA EMA
// seeded with the first price, RSI Wilder-smoothed, ATR = SIMPLE moving average of the true range (ATR.mq5), first
// values 0. Checks: every name declared or documented (the undeclared-name audit), no trade calls, array indexes in range
// (MT5 stops an indicator on "array out of range"), indicator / signal values against independent references, plots,
// incremental OnCalculate calls (new bar + ticks) equal one full calculation, alerts once per CLOSED bar, the higher
// timeframe = previous closed higher bar, INIT_FAILED on a too-coarse chart, mutants. UNTESTED_RUNTIME on MT5.
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm'; import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..'), dir = path.join(root, 'trader-toolkit/recipes');
let checks = 0, failures = 0, QUIET = false; const fail = (f, m) => { failures++; if (!QUIET) console.error('FAIL', f, m); }, ok = (c, f, m) => { checks++; if (!c) fail(f, m); };
const EMPTY = 1.7976931348623157e308, PER = { PERIOD_CURRENT: 0, PERIOD_M1: 1, PERIOD_M5: 5, PERIOD_M15: 15, PERIOD_M30: 30, PERIOD_H1: 16385, PERIOD_H4: 16388, PERIOD_D1: 16408 };
const perSec = (p) => ({ 1: 60, 5: 300, 15: 900, 30: 1800, 16385: 3600, 16388: 14400, 16408: 86400 })[p];
const API = new Set(['_Symbol', '_Period', ...Object.keys(PER), 'INVALID_HANDLE', 'INIT_SUCCEEDED', 'INIT_FAILED', 'EMPTY_VALUE', 'MODE_EMA', 'MODE_SMA', 'PRICE_CLOSE', 'PRICE_OPEN', 'PRICE_HIGH', 'PRICE_LOW', 'PRICE_MEDIAN', 'PRICE_TYPICAL',
  'INDICATOR_DATA', 'INDICATOR_SHORTNAME', 'iMA', 'iRSI', 'iATR', 'CopyBuffer', 'BarsCalculated', 'IndicatorRelease', 'IndicatorSetString', 'ArraySetAsSeries', 'SetIndexBuffer', 'iTime', 'iOpen', 'iHigh', 'iLow', 'iClose', 'iBarShift',
  'PeriodSeconds', 'Bars', 'TimeToStruct', 'Alert', 'Print', 'MathMin', 'MathMax', 'MathAbs', 'Comment', 'DoubleToString', 'EnumToString', 'StringSubstr', 'TimeToString', 'TIME_DATE', 'TIME_MINUTES', '_Digits']);
const JSKW = new Set(['function', 'let', 'var', 'return', 'if', 'else', 'for', 'while', 'true', 'false', 'mqlArr']);
function stripComment(line) { let s = false; for (let i = 0; i < line.length; i++) { if (line[i] === '"' && line[i - 1] !== '\\') s = !s; if (!s && line[i] === '/' && line[i + 1] === '/') return line.slice(0, i); } return line; }
const noStr = (s) => s.replace(/"(?:[^"\\]|\\.)*"/g, '""');
function translate(src) {
  const props = {}, declared = new Set(); let body = [];
  for (const raw of src.split('\n')) { const s = stripComment(raw); let m;
    if ((m = /^#property\s+(\w+)(?:\s+(.+?))?\s*$/.exec(s.trim()))) { props[m[1]] = m[2] ?? true; continue; }
    if ((m = /^#define\s+(\w+)\s+(-?\d+(?:\.\d+)?)\s*$/.exec(s.trim()))) { body.push(`var ${m[1]} = ${m[2]};`); declared.add(m[1]); continue; }
    if (/^\s*#/.test(s)) throw new Error('preprocessor line outside the subset: ' + s.trim());
    body.push(s); }
  let js = body.join('\n');
  if (/\/\s*\d+(?![\d.])/.test(noStr(js))) throw new Error('division by an integer literal (integer division in MQL5) is outside the subset');
  js = js.replace(/\b(int|double|bool|void|datetime|string)\s+(\w+)\s*\(([^)]*)\)\s*\{/g, (m0, t, n, ps) => { declared.add(n); const names = ps.split(',').map(p => p.trim()).filter(Boolean).map(p => { const q = /(\w+)\s*(\[\])?$/.exec(p); if (!q) throw new Error('parameter ' + p); declared.add(q[1]); return q[1]; }); return `function ${n}(${names.join(', ')}) {`; });
  js = js.replace(/\bMqlDateTime\s+(\w+)\s*;/g, (m0, n) => { declared.add(n); return `let ${n} = {};`; });
  js = js.replace(/\b(?:double|int|bool)\s+(\w+)\[(\d*)\]\s*;/g, (m0, n, k) => { declared.add(n); return `let ${n} = mqlArr(${k || 0});`; });
  js = js.replace(/\b(?:int|double|bool|datetime|string|long)\s+(\w+)\s*=/g, (m0, n) => { declared.add(n); return `let ${n} =`; });
  js = js.replace(/\b(?:int|double|bool|datetime|string)\s+(\w+)\s*;/g, (m0, n) => { declared.add(n); return `let ${n} = 0;`; });
  const left = /\b(int|double|bool|void|datetime|string|long|ENUM_TIMEFRAMES|MqlDateTime|const|input|static|class|struct)\b/.exec(noStr(js));
  if (left) throw new Error(`"${left[1]}" left after translation (cast, input, static or another construct outside the subset)`);
  return { js, props, declared };
}
function names(js) { const out = new Set(); const s = noStr(js); for (const m of s.matchAll(/(\.)?\b([A-Za-z_][A-Za-z0-9_]*)\b/g)) if (!m[1] && !/^\d/.test(m[2])) out.add(m[2]); return out; }
// --- MT5 model ---
function compress(bars, ms) { const out = []; let key = null; for (const b of bars) { const k = Math.floor(b.time / ms); if (k !== key) { key = k; out.push({ time: k * ms, open: b.open, high: b.high, low: b.low, close: b.close }); } else { const o = out[out.length - 1]; o.high = Math.max(o.high, b.high); o.low = Math.min(o.low, b.low); o.close = b.close; } } return out; }
function mt5Values(h, bs) { const n = bs.length, px = bs.map(b => h.price === 'median' ? (b.high + b.low) / 2 : h.price === 'typical' ? (b.high + b.low + b.close) / 3 : b[h.price]), o = new Array(n).fill(0), p = h.period;
  if (h.kind === 'ema') { const a = 2 / (p + 1); for (let i = 0; i < n; i++) o[i] = i === 0 ? px[0] : px[i] * a + o[i - 1] * (1 - a); return o; } // Moving Average.mq5 CalculateEMA: first value = first price
  if (h.kind === 'sma') { let s = 0; for (let i = 0; i < n; i++) { s += px[i]; if (i >= p) s -= px[i - p]; o[i] = i >= p - 1 ? s / p : 0; } return o; }
  if (h.kind === 'rsi') { let P = 0, N = 0; for (let i = 1; i < n; i++) { const d = px[i] - px[i - 1]; if (i <= p) { P += Math.max(d, 0); N += Math.max(-d, 0); if (i < p) continue; P /= p; N /= p; } else { P = (P * (p - 1) + Math.max(d, 0)) / p; N = (N * (p - 1) + Math.max(-d, 0)) / p; } o[i] = N !== 0 ? 100 - 100 / (1 + P / N) : (P !== 0 ? 100 : 50); } return o; } // RSI.mq5
  if (h.kind === 'atr') { const tr = bs.map((b, i) => i === 0 ? 0 : Math.max(b.high, bs[i - 1].close) - Math.min(b.low, bs[i - 1].close)); let s = 0; for (let i = 1; i <= p && i < n; i++) s += tr[i]; if (p < n) o[p] = s / p; for (let i = p + 1; i < n; i++) o[i] = o[i - 1] + (tr[i] - tr[i - p]) / p; return o; } // ATR.mq5: simple average of the true range
  throw new Error('handle kind ' + h.kind); }
class MqlRangeError extends Error {}
function makeRuntime(chartMin) {
  const st = { cur: [], ver: 0 }, handles = [], buffers = [], alerts = [], prints = [], comments = [], cache = new Map();
  const tfOf = (tf) => tf === 0 || tf === chartMin ? 0 : tf;
  const tfBars = (tf) => { tf = tfOf(tf); if (tf === 0) return st.cur; const k = 'b' + tf; if (cache.get(k)?.ver !== st.ver) cache.set(k, { ver: st.ver, v: compress(st.cur, perSec(tf) * 1000) }); return cache.get(k).v; };
  const vals = (id) => { const k = 'h' + id; if (cache.get(k)?.ver !== st.ver) cache.set(k, { ver: st.ver, v: mt5Values(handles[id], tfBars(handles[id].tf)) }); return cache.get(k).v; };
  const mqlArr = (n = 0) => { const t = { store: new Array(n).fill(0), series: false };
    return new Proxy(t, { get(o, k) { if (k === '__t') return o; if (typeof k === 'string' && /^\d+$/.test(k)) { const i = +k; if (i >= o.store.length) throw new MqlRangeError(`array out of range [${i}] of ${o.store.length}`); return o.store[o.series ? o.store.length - 1 - i : i]; } return undefined; },
      set(o, k, v) { if (typeof k === 'string' && /^\d+$/.test(k)) { const i = +k; if (i >= o.store.length) throw new MqlRangeError(`array out of range [${i}] of ${o.store.length}`); o.store[o.series ? o.store.length - 1 - i : i] = v; return true; } throw new Error('property set ' + String(k)); } }); };
  const price = { 1: 'close', 2: 'open', 3: 'high', 4: 'low', 5: 'median', 6: 'typical' };
  const handle = (h) => { if (tfOf(h.tf) !== 0 && !perSec(h.tf)) return -1; handles.push(h); return handles.length - 1; };
  const at = (tf, i, f) => { const b = tfBars(tf), j = b.length - 1 - i; return j >= 0 && j < b.length ? (f === 'time' ? b[j].time / 1000 : b[j][f]) : 0; };
  const api = { _Symbol: 'BSVTEST', _Period: chartMin, ...PER, INVALID_HANDLE: -1, INIT_SUCCEEDED: 0, INIT_FAILED: 1, EMPTY_VALUE: EMPTY, MODE_SMA: 0, MODE_EMA: 1, PRICE_CLOSE: 1, PRICE_OPEN: 2, PRICE_HIGH: 3, PRICE_LOW: 4, PRICE_MEDIAN: 5, PRICE_TYPICAL: 6, INDICATOR_DATA: 0, INDICATOR_SHORTNAME: 0,
    iMA: (s, tf, p, sh, m, pr) => sh === 0 ? handle({ kind: m === 1 ? 'ema' : 'sma', tf, period: p, price: price[pr] }) : -1, iRSI: (s, tf, p, pr) => handle({ kind: 'rsi', tf, period: p, price: price[pr] }), iATR: (s, tf, p) => handle({ kind: 'atr', tf, period: p, price: 'close' }),
    CopyBuffer: (id, buf, start, count, arr) => { if (!handles[id] || buf !== 0) return -1; const v = vals(id), n = v.length; if (start < 0 || count <= 0 || start + count > n) return -1; const t = arr.__t; if (t.store.length < count) t.store.length = count; t.store.fill(0);
      for (let k = 0; k < count; k++) { const val = v[n - 1 - start - k]; t.store[t.series ? t.store.length - 1 - k : count - 1 - k] = val; } return count; },
    BarsCalculated: (id) => handles[id] ? tfBars(handles[id].tf).length : -1, IndicatorRelease: () => true, IndicatorSetString: () => true,
    ArraySetAsSeries: (arr, f) => { arr.__t.series = !!f; return true; }, SetIndexBuffer: (k, arr) => { buffers[k] = arr; return true; },
    iTime: (s, tf, i) => at(tf, i, 'time'), iOpen: (s, tf, i) => at(tf, i, 'open'), iHigh: (s, tf, i) => at(tf, i, 'high'), iLow: (s, tf, i) => at(tf, i, 'low'), iClose: (s, tf, i) => at(tf, i, 'close'),
    iBarShift: (s, tf, t, exact) => { const b = tfBars(tf); let j = -1; for (let k = b.length - 1; k >= 0; k--) if (b[k].time / 1000 <= t) { j = k; break; } return j < 0 ? -1 : b.length - 1 - j; },
    Bars: (s, tf) => tfBars(tf).length, PeriodSeconds: (tf) => tfOf(tf) === 0 ? chartMin * 60 : perSec(tf), TimeToStruct: (t, o) => { const d = new Date(t * 1000); Object.assign(o, { year: d.getUTCFullYear(), mon: d.getUTCMonth() + 1, day: d.getUTCDate(), hour: d.getUTCHours(), min: d.getUTCMinutes(), sec: d.getUTCSeconds(), day_of_week: d.getUTCDay() }); return true; },
    Alert: (...a) => { alerts.push({ len: st.cur.length, msg: a.join('') }); }, Print: (...a) => { prints.push(a.join('')); }, Comment: (...a) => { comments.push({ len: st.cur.length, text: a.join('') }); }, // Comment / DoubleToString / EnumToString / StringSubstr / TimeToString per the MQL5 reference
    DoubleToString: (v, d = 8) => v.toFixed(Number.isInteger(d) && d >= 0 && d <= 16 ? d : 8), EnumToString: (p) => Object.keys(PER).find(k => PER[k] === p && p !== 0) || ({ 60: 'PERIOD_H1', 240: 'PERIOD_H4', 1440: 'PERIOD_D1' })[p] || String(p),
    StringSubstr: (s, a, len = -1) => len < 0 ? String(s).slice(a) : String(s).substr(a, len), TIME_DATE: 1, TIME_MINUTES: 2, _Digits: 5,
    TimeToString: (t, fl = 3) => { const d = new Date(t * 1000), p2 = (x) => String(x).padStart(2, '0'); return [(fl & 1) ? `${d.getUTCFullYear()}.${p2(d.getUTCMonth() + 1)}.${p2(d.getUTCDate())}` : '', (fl & 2) ? `${p2(d.getUTCHours())}:${p2(d.getUTCMinutes())}` : ''].filter(Boolean).join(' '); },
    MathMin: Math.min, MathMax: Math.max, MathAbs: Math.abs, mqlArr };
  return { st, api, buffers, alerts, prints, comments, handles };
}
const firstTick = (b) => ({ time: b.time, open: b.open, high: b.open, low: b.open, close: b.open });
function run(js, bars, chartMin, n0) { // n0 = bars on the first call; then each new bar arrives as a first tick and then its final tick
  const rt = makeRuntime(chartMin), ctx = vm.createContext({ ...rt.api });
  vm.runInContext('"use strict";\n' + js + '\n;globalThis.__bsv = { OnInit, OnCalculate, OnDeinit: typeof OnDeinit === "function" ? OnDeinit : null, call: (n, i) => globalThis[n](i) };', ctx, { timeout: 20000 });
  for (const [k, v] of Object.entries(rt.api)) if (k !== 'mqlArr' && typeof v !== 'function' && ctx[k] !== v) throw new Error('documented constant overwritten: ' + k);
  const F = ctx.__bsv, init = F.OnInit(); if (init !== 0) return { init, rt, F };
  let prev = 0; const call = (cur) => { rt.st.cur = cur; rt.st.ver++; for (const b of rt.buffers) if (b) { const t = b.__t, add = cur.length - t.store.length; if (add > 0) { const fresh = new Array(add).fill(NaN); t.store = t.series ? [...fresh.slice(0, 0), ...t.store, ...fresh] : [...t.store, ...fresh]; } } const T = cur.map(b => b.time / 1000), r = F.OnCalculate(cur.length, prev, T, cur.map(b => b.open), cur.map(b => b.high), cur.map(b => b.low), cur.map(b => b.close), [], [], []); prev = r; };
  call(bars.slice(0, n0));
  for (let k = n0; k < bars.length; k++) { call([...bars.slice(0, k), firstTick(bars[k])]); call(bars.slice(0, k + 1)); }
  return { init, rt, F };
}
// --- independent references (standard formulas) and synthetic bars (same as the Pine / AFL / thinkScript checks) ---
const fin = Number.isFinite, val = (v) => v === EMPTY ? NaN : v, same = (a, b) => (Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-9, tr = (v) => !!v;
const refSma = (x, p) => x.map((_, i) => i < p - 1 ? NaN : x.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p);
function refEma(x, p) { const a = 2 / (p + 1); let e = NaN; return x.map((v, i) => { if (i === p - 1) e = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) e = a * v + (1 - a) * e; return i >= p - 1 ? e : NaN; }); }
function refRma(x, p) { let r = NaN; return x.map((v, i) => { if (i === p - 1) r = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) r = (r * (p - 1) + v) / p; return i >= p - 1 ? r : NaN; }); }
const mkBars = (n, ms, f) => { const out = []; let q = 100; const t0 = Date.UTC(2026, 0, 5); for (let i = 0; i < n; i++) { const o = q; q = f(i); out.push({ time: t0 + i * ms, open: o, high: Math.max(o, q) + 0.5 + 0.3 * Math.abs(Math.sin(i)), low: Math.min(o, q) - 0.5, close: q }); } return out; };
const bars60 = mkBars(1200, 3600e3, i => 100 + 10 * Math.sin(i / 15) + 3 * Math.sin(i * 1.7)), bars15 = mkBars(4000, 900e3, i => 100 + 10 * Math.sin(i / 37) + 2 * Math.sin(i * 1.3));
const fires = {}; // recipe -> [closed alert bars on bars60, on barsAlt60]
const barsAlt60 = mkBars(1200, 3600e3, i => 100 + 22 * Math.sin(i / 23) + 6 * Math.sin(i / 4.1) + 2 * Math.sin(i * 1.9)); // stronger swings: alert conditions that never hold on bars60
const srcOf = (bs, s) => bs.map(b => s === 'hl2' ? (b.high + b.low) / 2 : s === 'hlc3' ? (b.high + b.low + b.close) / 3 : b[s || 'close']);
const refInd = (bs, b) => { const p = b.params || {}, x = srcOf(bs, p.source); if (b.type === 'indicator.sma') return refSma(x, p.length); if (b.type === 'indicator.ema') return refEma(x, p.length);
  if (b.type === 'indicator.rsi') { const G = refRma(x.slice(1).map((w, i) => Math.max(w - x[i], 0)), p.length), L = refRma(x.slice(1).map((w, i) => Math.max(x[i] - w, 0)), p.length); return [NaN, ...G.map((u, i) => 100 * u / (u + L[i]))]; }
  const trs = bs.map((h, i) => i === 0 ? NaN : Math.max(h.high, bs[i - 1].close) - Math.min(h.low, bs[i - 1].close)); return [NaN, ...refSma(trs.slice(1), p.length)]; }; // MT5 ATR: simple average of the true range
const vacuous = []; let panelsSeen = 0, hooksSeen = 0, pivChecked = 0, pivSigSeen = 0, zonesSeen = 0, rangeChecked = 0, breakoutsSeen = 0, todoLines = 0, indChecked = 0, sigChecked = 0, htfChecked = 0, plotsChecked = 0, alertsSeen = 0, mutantsCaught = 0, files = 0, auditNames = 0;
for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')), by = Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
  const code = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), path.join(dir, f), '--target', 'mql5'], { encoding: 'utf8' });
  files++; todoLines += (code.match(/TODO unsupported block /g) || []).length;
  let T; try { T = translate(code); checks++; } catch (e) { fail(f, 'translate: ' + e.message); continue; }
  // undeclared-name audit: every identifier is declared in the file or is a documented MQL5 name the BSV model implements
  const used = names(T.js), unknown = [...used].filter(n => !T.declared.has(n) && !API.has(n) && !JSKW.has(n)); auditNames += used.size;
  ok(unknown.length === 0, f, `undeclared or undocumented names: ${unknown.join(', ')}`);
  ok(!/\b(OrderSend|CTrade|PositionOpen|OrderCalcMargin|WebRequest|FileOpen)\b/.test(code.split('\n').map(stripComment).join('\n')), f, 'no trade, web or file calls (indicator only; comments may name them)');
  ok(T.props.indicator_buffers !== undefined && +T.props.indicator_buffers === (code.match(/SetIndexBuffer\(/g) || []).length && +T.props.indicator_plots === (code.match(/^#property indicator_type\d+/gm) || []).length, f, '#property indicator_buffers / indicator_plots match SetIndexBuffer calls and plot types');
  if (unknown.length) continue;
  const htfB = recipe.blocks.filter(b => b.params?.timeframeRef && new RegExp(`^double V_${b.id}\\(int i\\) \\{ return BsvHtfAt\\(`, 'm').test(code));
  if (htfB.length) { let r; try { r = run(T.js, bars60.slice(0, 400), 60, 400); } catch (e) { r = { init: 'error ' + e.message }; } ok(r.init === 1, f, `OnInit returns INIT_FAILED on an hourly chart (higher timeframe must be higher; got ${r.init})`); }
  const chartMin = htfB.length || recipe.blocks.some(b => b.type === 'filter.session') ? 15 : 60, bs = chartMin === 15 ? bars15 : bars60, n = bs.length, n0 = Math.max(400, n - 1500), W = +((/^#define BSV_WARMUP (\d+)$/m.exec(code) || [])[1] || 0);
  let full, inc; try { full = run(T.js, bs, chartMin, n); inc = run(T.js, bs, chartMin, n0); checks++; } catch (e) { fail(f, 'run: ' + (e instanceof MqlRangeError ? 'MT5 would stop the indicator: ' : '') + e.message); continue; }
  ok(full.init === 0 && inc.init === 0, f, 'OnInit returns INIT_SUCCEEDED on the test chart');
  const S = (name, i) => full.F.call(name, i), hasFn = (name) => new RegExp(`^(?:bool|double) ${name}\\(int i\\)`, 'm').test(code);
  const top = n - W; // series indexes 0 .. top - 1 are calculated; chronological j = n - 1 - i
  const series = (name, conv = (x) => x) => { const out = new Array(n).fill(NaN); for (let i = 0; i < top; i++) out[n - 1 - i] = conv(S(name, i)); return out; };
  const env = new Map();
  for (const b of recipe.blocks) { const p = b.params || {};
    if (/^indicator\./.test(b.type) && hasFn(`V_${b.id}`)) { const v = series(`V_${b.id}`, val); env.set(b.id, v);
      if (htfB.includes(b)) { const hourly = compress(bs, 3600e3), R = refInd(hourly, b), gk = bs.map(x => Math.floor(x.time / 3600e3) - Math.floor(bs[0].time / 3600e3)); let worst = 0; const from = n - top + 4 * 15 * p.length + 8;
        for (let j = from; j < n; j++) { const want = gk[j] >= 1 ? R[gk[j] - 1] : NaN; worst = Math.max(worst, Math.abs(v[j] - want) / Math.max(1, Math.abs(want))); }
        ok(worst < 1e-6, f, `${b.id}: 15-minute value = previous closed hour of the reference (worst ${worst})`); htfChecked++; continue; }
      const R = refInd(bs, b), from = n - top + 15 * p.length; let worst = 0; for (let j = from; j < n; j++) worst = Math.max(worst, Math.abs(v[j] - R[j]) / Math.max(1, Math.abs(R[j])));
      ok(worst < 1e-6, f, `${b.id} (${b.type}) matches the reference${b.type === 'indicator.atr' ? ' (MT5 ATR: simple average of the true range)' : ''} from bar ${from}: worst ${worst}`); indChecked++; }
    if (/^(signal\.(cross|threshold|combine|recent)|filter\.session)$/.test(b.type) && hasFn(`S_${b.id}`)) { const v = series(`S_${b.id}`, x => +tr(x)), g = (r) => env.get(r) || srcOf(bs, r), want = new Array(n).fill(false);
      if (b.type === 'signal.cross') { const a = g(p.left), c = g(p.right); for (let j = 1; j < n; j++) want[j] = [a[j], c[j], a[j - 1], c[j - 1]].every(fin) && (p.direction === 'below' ? a[j] < c[j] && a[j - 1] >= c[j - 1] : a[j] > c[j] && a[j - 1] <= c[j - 1]); }
      if (b.type === 'signal.threshold') { const a = g(p.left), c = typeof p.right === 'string' && p.right ? g(p.right) : null, op = p.op || '>='; for (let j = 0; j < n; j++) { const x = c ? c[j] : Number(p.value); want[j] = fin(a[j]) && fin(x) && { '>': a[j] > x, '>=': a[j] >= x, '<': a[j] < x, '<=': a[j] <= x, '==': a[j] === x, '!=': a[j] !== x }[op]; } }
      if (b.type === 'signal.recent') { const sg = env.get(p.signal) || []; for (let j = 0; j < n; j++) { want[j] = false; for (let k = 1; k <= p.bars && j - k >= 0; k++) if (sg[j - k] === 1) want[j] = true; } }
      if (b.type === 'signal.combine') { const L = (p.signals || []).map(r => env.get(r)); for (let j = 0; j < n; j++) want[j] = L.length > 0 && L.every(Boolean) && (p.mode === 'any' ? L.some(s => s[j] === 1) : L.every(s => s[j] === 1)); }
      if (b.type === 'filter.session') { const [s0, s1] = String(p.session || '0000-2359').split('-').map(x => +x.slice(0, 2) * 60 + +x.slice(2, 4)); for (let j = 0; j < n; j++) { const d = new Date(bs[j].time), m = d.getUTCHours() * 60 + d.getUTCMinutes(); want[j] = s0 <= s1 ? m >= s0 && m < s1 : m >= s0 || m < s1; }
        if ((p.timezone || 'Etc/UTC') !== 'UTC' && (p.timezone || 'Etc/UTC') !== 'Etc/UTC') ok(code.includes(`// TODO ${b.id}: session`) && code.includes(`convert from ${p.timezone}`), f, `${b.id}: session in broker server time is flagged with a TODO to convert from ${p.timezone}`); }
      let bad = 0; for (let j = n - top + 1 + (b.type === 'signal.recent' ? p.bars : 0); j < n; j++) if (v[j] !== +want[j]) bad++; ok(bad === 0 && (b.type === 'filter.session' || b.type === 'signal.combine' || want.slice(n - top).some(Boolean) || b.type === 'signal.threshold'), f, `${b.id} (${b.type}) equals the independent recomputation (${bad} differ)`); env.set(b.id, v); sigChecked++; } }
  // ranges / breakouts: independent window reference from the session signal checked above (broker server time = UTC in this model)
  const rngB = recipe.blocks.filter(b => b.type === 'structure.range' && hasFn(`V_${b.id}_high`)), bos = recipe.blocks.filter(b => b.type === 'signal.breakout' && rngB.some(r => r.id === b.params?.range) && hasFn(`S_${b.id}_up`));
  const refRange = (rb) => { const R = env.get(rb.params.during).map(x => x === 1), H = [], Lo = []; let h = NaN, l = NaN; bs.forEach((b, j) => { if (R[j]) { const fresh = j === 0 || !R[j - 1]; h = fresh ? b.high : Math.max(h, b.high); l = fresh ? b.low : Math.min(l, b.low); } H.push(h); Lo.push(l); }); return { R, H, Lo }; };
  const badR = (F) => { let d = 0; const from = n - top + 1; for (const rb of rngB) { const q = refRange(rb); for (const k of rb.params.track) for (let j = from + 200; j < n; j++) { const v = val(F.call(`V_${rb.id}_${k}`, n - 1 - j)); if (!same(v, k === 'high' ? q.H[j] : q.Lo[j])) d++; } }
    for (const bb of bos) { const q = refRange(by[bb.params.range]), dir = bb.params.direction || 'either'; for (let j = from + 200; j < n; j++) { const c = bs[j].close, pc = bs[j - 1].close, okb = !q.R[j] && fin(q.H[j]), up = okb && c > q.H[j] && pc <= q.H[j], dn = okb && c < q.Lo[j] && pc >= q.Lo[j]; if (!!F.call(`S_${bb.id}`, n - 1 - j) !== (dir === 'either' ? up || dn : dir === 'above' ? up : dn)) d++; } }
    return d; };
  if (rngB.length) { const d0 = badR(full.F); ok(d0 === 0, f, `range / breakout equal the window reference on every bar (${d0} differ)`); rangeChecked += rngB.length; for (const rb of rngB) ok(refRange(rb).H.some(fin), f, `${rb.id}: windows occur (not vacuous)`);
    for (const bb of bos) { let c = 0; for (let i = 1; i < top - 200; i++) if (full.F.call(`S_${bb.id}`, i)) c++; ok(c > 0, f, `${bb.id}: breakouts fire (${c})`); breakoutsSeen += c; if (d0 === 0) env.set(bb.id, series(`S_${bb.id}`, x => +tr(x))); }
    for (const [mn, from, to, need] of [['window starts one bar too old', /double v = (iHigh|iLow)\(_Symbol, _Period, k\);/g, 'double v = $1(_Symbol, _Period, k + 1);', 0], ['breakout without the close before', / && iClose\(_Symbol, _Period, i \+ 1\) <= h;/, ';', 1]]) { if (need && !bos.length) continue;
      const mc = code.replace(from, to), caught = mc !== code && badR(run(translate(mc).js, bs, chartMin, n).F) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++; } }
  // TODO stubs: never true / never a value
  for (const m of code.matchAll(/^(bool|double) ([SV])_(\w+)\(int i\) \{ return (false|EMPTY_VALUE); \} \/\/ TODO unsupported block/gm)) { let bad = 0; for (let i = 0; i < top; i += 7) { const x = S(`${m[2]}_${m[3]}`, i); if (m[1] === 'bool' ? x !== false : x !== EMPTY) bad++; } ok(bad === 0, f, `${m[3]}: TODO stub never true / never a value`); }
  // pivots / sweeps / divergences / zones (batch 26): independent chronological pivot reference written here (not from the generator);
  // sweep and divergence use the model's ATR / oscillator buffers (checked above); compared on calculated bars from chronological bar 400
  const pivB = recipe.blocks.filter(b => b.type === 'structure.pivot' && hasFn(`V_${b.id}_high`)), pvSig = recipe.blocks.filter(b => /^signal\.(liquidity_sweep|divergence)$/.test(b.type) && pivB.some(x => x.id === b.params?.pivot) && hasFn(`S_${b.id}`));
  const zoneB = recipe.blocks.filter(b => b.type === 'visual.zone' && code.includes(`double Buf_${b.id}_high[];`));
  const refPiv = (pb) => { const q = pb.params, [hk, lk] = (q.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], H = bs.map(b => b[hk]), Lo = bs.map(b => b[lk]), out = { h: [], l: [], ph: [], pl: [], H, Lo }; let vh = NaN, vl = NaN;
    for (let i = 0; i < n; i++) { const j = i - q.right; let up = false, dn = false; if (j - q.left >= 0) { up = true; dn = true; for (let m = j - q.left; m <= i; m++) { if (m === j) continue; if (m < j ? !(H[j] > H[m]) : !(H[j] >= H[m])) up = false; if (m < j ? !(Lo[j] < Lo[m]) : !(Lo[j] <= Lo[m])) dn = false; } }
      if (up) { vh = H[j]; out.ph.push(j); } if (dn) { vl = Lo[j]; out.pl.push(j); } out.h.push(vh); out.l.push(vl); } return out; };
  const badP = (F) => { let d = 0; const from = Math.max(400, n - top);
    for (const pb of pivB) { const q = refPiv(pb); for (let j = from; j < n; j++) { if (!same(val(F.call(`V_${pb.id}_high`, n - 1 - j)), q.h[j])) d++; if (!same(val(F.call(`V_${pb.id}_low`, n - 1 - j)), q.l[j])) d++; } }
    for (const sb of pvSig) { const pb = by[sb.params.pivot], q = refPiv(pb);
      if (sb.type === 'signal.liquidity_sweep') { const fr = Number(sb.params.minAtrFraction || 0); for (let j = from; j < n; j++) { const b = bs[j], A = val(F.call(`V_${sb.params.atr}`, n - 1 - j)), ph = q.h[j - 1], pl = q.l[j - 1], w = fin(A) && ((fin(ph) && b.high > ph && b.high - ph >= fr * A && b.close < ph) || (fin(pl) && b.low < pl && pl - b.low >= fr * A && b.close > pl)); if (!!F.call(`S_${sb.id}`, n - 1 - j) !== w) d++; } }
      else { const O = (j) => val(F.call(`V_${sb.params.oscillator}`, n - 1 - j)), dir = sb.params.direction || 'both', w = new Array(n).fill(false), R = pb.params.right;
        if (dir !== 'bullish') for (let k = 1; k < q.ph.length; k++) { const a = q.ph[k - 1], j = q.ph[k]; if (q.H[j] > q.H[a] && fin(O(j)) && fin(O(a)) && O(j) < O(a)) w[j + R] = true; }
        if (dir !== 'bearish') for (let k = 1; k < q.pl.length; k++) { const a = q.pl[k - 1], j = q.pl[k]; if (q.Lo[j] < q.Lo[a] && fin(O(j)) && fin(O(a)) && O(j) > O(a)) w[j + R] = true; }
        for (let j = from; j < n; j++) if (!!F.call(`S_${sb.id}`, n - 1 - j) !== w[j]) d++; } }
    return d; };
  if (pivB.length) { const d0 = badP(full.F); ok(d0 === 0, f, `pivot / sweep / divergence equal the chronological reference on every calculated bar from 400 (${d0} differ)`);
    for (const pb of pivB) { const q = refPiv(pb); ok(q.ph.length > 0 && q.pl.length > 0, f, `${pb.id}: pivots occur (not vacuous)`); pivChecked++; }
    for (const sb of pvSig) { let c = 0; for (let j = Math.max(400, n - top); j < n; j++) if (full.F.call(`S_${sb.id}`, n - 1 - j)) c++; ok(c > 0, f, `${sb.id}: fires (${c}; not vacuous)`); pivSigSeen += c; if (d0 === 0) env.set(sb.id, series(`S_${sb.id}`, x => +tr(x))); }
    for (const [mn, from, to, need] of [['pivot without the right-side test', / for \(int k = 1; k <= \d+; k\+\+\) if \((iHigh|iClose)\(_Symbol, _Period, c - k\) > v\) return\(false\);/, '', null],
      ['sweep without the close back inside', / && c < ph\)/, ')', 'signal.liquidity_sweep'], ['divergence oscillator test flipped', / && o1 < o0; \}/, ' && o1 > o0; }', 'signal.divergence']]) {
      if (need && !pvSig.some(b => b.type === need)) continue; const mc = code.replace(from, to), caught = mc !== code && badP(run(translate(mc).js, bs, chartMin, n).F) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++; } }
  // zones: two extra buffers after the plots, holding the source's high / low; the incremental run equals one full calculation
  zoneB.forEach((z, k) => { const src = by[z.params.source], k0 = recipe.blocks.filter(b => b.type === 'visual.plot').length + 2 * k;
    const want = src.type === 'structure.pivot' ? (() => { const q = refPiv(src); return [q.h, q.l]; })() : [0, 1].map(s => { const R = env.get(src.params.during).map(x => x === 1), out = []; let h = NaN, l = NaN; bs.forEach((b, j) => { if (R[j]) { const fresh = j === 0 || !R[j - 1]; h = fresh ? b.high : Math.max(h, b.high); l = fresh ? b.low : Math.min(l, b.low); } out.push(s ? l : h); }); return out; });
    let bad = 0, binc = 0; for (const s of [0, 1]) { const fb = full.rt.buffers[k0 + s]?.__t, ib = inc.rt.buffers[k0 + s]?.__t; if (!fb || !ib) { bad++; continue; } for (let j = Math.max(400, n - top + 1); j < n; j++) { if (!same(val(fb.store[j]), want[s][j])) bad++; if (!same(val(ib.store[j]), val(fb.store[j]))) binc++; } }
    ok(bad === 0 && binc === 0 && want[0].some(fin), f, `${z.id}: zone buffers = ${z.params.source} high / low (${bad} differ; incremental differ ${binc}; not vacuous)`); zonesSeen++; });
  ok(recipe.blocks.every(b => !/^(structure|signal|visual\.(zone|table)|alert\.webhook|scanner)\./.test(b.type) || /^signal\.(cross|threshold|combine)$/.test(b.type) || hasFn(`S_${b.id}`) || hasFn(`V_${b.id}`) || hasFn(`V_${b.id}_high`) || hasFn(`V_${b.id}_low`) || code.includes(`TODO unsupported block ${b.type}: ${b.id}`)), f, 'every block is rendered or a declared TODO stub');
  // plots: one buffer per visual.plot holding its source; the incremental run (new bar + ticks) equals one full calculation
  const plotB = recipe.blocks.filter(b => b.type === 'visual.plot');
  ok(full.rt.buffers.length === plotB.length + 2 * zoneB.length, f, 'one indicator buffer per visual.plot, two per rendered zone');
  plotB.forEach((b, k) => { const fb = full.rt.buffers[k]?.__t, ib = inc.rt.buffers[k]?.__t; if (!fb || !ib) { ok(false, f, `${b.id}: buffer`); return; } const v = env.get(b.params.source) || srcOf(bs, b.params.source); let bad = 0, binc = 0;
    for (let i = 0; i < top; i++) { const j = n - 1 - i, a = fb.store[fb.series ? j : j], w = v[j]; if (!same(val(a), w)) bad++; if (!same(val(ib.store[j]), val(a))) binc++; }
    ok(bad === 0, f, `${b.id}: plot buffer = its source on every calculated bar (${bad} differ)`); ok(binc === 0, f, `${b.id}: incremental calls (new bar + ticks) equal one full calculation (${binc} differ)`); plotsChecked++; });
  // alerts: once per CLOSED bar where the condition holds, never from the forming bar (the first tick of each bar differs)
  const alB = recipe.blocks.filter(b => b.type === 'alert.condition'), alertsOf = (r) => r.rt.alerts.map(a => `${a.len}|${a.msg}`), stubbed = (id) => new RegExp(`^bool S_${id}\\(int i\\) \\{ return false; \\} // TODO`, 'm').test(code);
  const wantAl = (sig) => { const out = []; for (const b of alB) { const w = env.get(b.params.when); if (!w) continue; for (let j = n0 - 2; j <= n - 2; j++) if (w[j] === 1) out.push(`${j + 2}|${b.params.message || b.id}`); } return out.sort(); }; // bar j is checked when bar j + 1 opens (j + 2 bars visible)
  if (alB.length) { const got = alertsOf(inc).sort(), want = wantAl(); const real = alB.some(b => !stubbed(b.params.when)); ok(got.length === want.length && got.every((x, k) => x === want[k]) && (want.length > 0 || !real || chartMin === 60), f, `alerts once per closed bar on the condition (${got.length} fired, ${want.length} expected)`); alertsSeen += got.length;
    const mc = code.replace(/(S_\w+)\(1\) && (g_alert_\w+) != iTime\(_Symbol, _Period, 1\)\) \{ \2 = iTime\(_Symbol, _Period, 1\);/, '$1(0) && $2 != iTime(_Symbol, _Period, 0)) { $2 = iTime(_Symbol, _Period, 0);');
    if (real && chartMin === 60) { // closed bars where each real alert condition holds, on both 60-minute bar sets (full runs)
      const cnt = (r, t) => { let c = 0; for (const b of alB) if (!stubbed(b.params.when)) for (let i = 1; i < t; i++) if (r.F.call(`S_${b.params.when}`, i)) c++; return c; };
      const both = [cnt(full, top), cnt(run(T.js, barsAlt60, 60, barsAlt60.length), barsAlt60.length - W)]; fires[f.replace('.json', '')] = both;
      if (recipe.blocks.some(b => b.type === 'signal.recent')) ok(both[0] > 0 && both[1] > 0, f, `alert condition with a look-back fires on both bar sets (${both.join(' / ')})`); }
    if (!want.length && real && chartMin === 60) { // vacuous on bars60: alerts on the stronger-swing bars = closed bars where the full run's condition holds
      const fa = run(T.js, barsAlt60, 60, barsAlt60.length), ia = run(T.js, barsAlt60, 60, 400), na = barsAlt60.length, ta = na - W, wa = [];
      for (const b of alB) for (let j = 398; j <= na - 2; j++) { const i = na - 1 - j; if (i < ta && fa.F.call(`S_${b.params.when}`, i)) wa.push(`${j + 2}|${b.params.message || b.id}`); }
      const ga = alertsOf(ia).sort(); wa.sort(); if (!wa.length) vacuous.push(f.replace('.json', '')); ok(ga.length === wa.length && ga.every((x, k) => x === wa[k]), f, `stronger-swing bars: alerts once per closed bar on the condition (${ga.length} fired, ${wa.length} expected)`); alertsSeen += ga.length; }
    if (mc !== code && want.length) { const r = run(translate(mc).js, bs, chartMin, n0), g2 = alertsOf(r).sort(); const caught = !(g2.length === want.length && g2.every((x, k) => x === want[k])); ok(caught, f, 'mutant caught: alert from the forming bar (0 instead of 1)'); if (caught) mutantsCaught++; } }
  if (plotB.length) { const mc = code.replace('   if (prev_calculated > 0) limit++;\n', ''), r = run(translate(mc).js, bs, chartMin, n0); let binc = 0; plotB.forEach((b, k) => { const fb = full.rt.buffers[k].__t, ib = r.rt.buffers[k].__t; for (let i = 0; i < top; i++) if (!same(val(ib.store[n - 1 - i]), val(fb.store[n - 1 - i]))) binc++; });
    ok(mc !== code && binc > 0, f, 'mutant caught: the bar that just closed is not recalculated (no limit++)'); if (mc !== code && binc > 0) mutantsCaught++; }
  // value panels (batch 27): one Comment() per call; the text after the last call = title + "id: value" per field at shift 1 (the bar that just
  // closed), built here from the series checked above (independent of the generator's expression); fields are chosen independently
  const tabB = recipe.blocks.filter(b => b.type === 'visual.table');
  if (tabB.length) { const OKT = /^(indicator\.(ema|sma|rsi|atr)|signal\.(cross|threshold|combine|breakout)|filter\.session|structure\.range)$/, PXN = new Set(['open', 'high', 'low', 'close', 'hl2', 'hlc3', 'ohlc4']);
    const deps = (b) => { const q = b.params || {}; return b.type === 'signal.cross' ? [q.left, q.right] : b.type === 'signal.threshold' ? [q.left, typeof q.right === 'string' ? q.right : null] : b.type === 'signal.combine' ? (q.signals || []) : b.type === 'structure.range' ? [q.during] : b.type === 'signal.breakout' ? [q.range] : []; };
    const shown = (r, seen = new Set()) => { if (!by[r]) return PXN.has(r); if (seen.has(r)) return true; seen.add(r); return OKT.test(by[r].type) && deps(by[r]).filter(Boolean).every(x => shown(x, seen)); };
    const num = (v) => fin(v) ? v.toFixed(8) : 'n/a'; let skipped = 0, nPanels = 0;
    const wantAt = (j) => { const blocks = []; skipped = 0; nPanels = 0;
    for (const t of tabB) { const fs2 = (t.params?.fields || []).filter(x => shown(x)); skipped += (t.params?.fields || []).length - fs2.length; if (!fs2.length) { skipped++; continue; }
      const lines = [String(t.params?.title || t.id).replace(/[\r\n]/g, ' ').trim().slice(0, 80)];
      for (const x of fs2) { const b = by[x]; if (b.type === 'structure.range') { const q = refRange(b); for (const k of b.params.track) lines.push(`${x}.${k}: ${num(k === 'high' ? q.H[j] : q.Lo[j])}`); }
        else if (/^(signal|filter)\./.test(b.type)) lines.push(`${x}: ${env.get(x)[j] === 1 ? 'true' : 'false'}`); else lines.push(`${x}: ${num(env.get(x)[j])}`); }
      blocks.push(lines.join('\n')); nPanels++; }
    return blocks.join('\n\n'); };
    const want = wantAt(n - 2), last = (r) => r.rt.comments[r.rt.comments.length - 1]?.text, badC = (r) => r.rt.comments.filter(c => c.len >= n0 && c.text !== wantAt(c.len - 2)).length;
    ok((code.match(/\/\/ TODO \w+: visual\.table /g) || []).length === skipped && !code.includes('TODO unsupported block visual.table'), f, `panel TODO lines (${skipped})`);
    if (nPanels) { const bc = badC(inc); ok(last(full) === want && bc === 0, f, `value panel text = the fields at the bar that just closed, on every incremental call (${bc} differ; last ${JSON.stringify(last(full))})`); panelsSeen += nPanels;
      { const r0 = run(T.js, bs, chartMin, n); r0.F.OnDeinit && r0.F.OnDeinit(0); ok(!!r0.F.OnDeinit && last(r0) === '', f, 'OnDeinit removes the panel (Comment(""))'); }
      const mc = code.replace(/^(   Comment\((?!""\)).*)$/m, (l) => l.replace(/\(1\)/g, '(0)')), r = run(translate(mc).js, bs, chartMin, n0); const caught = mc !== code && badC(r) > 0; ok(caught, f, 'mutant caught: panel shows the forming bar (shift 0)'); if (caught) mutantsCaught++; } }
  // webhooks (batch 27): MT5 indicators cannot call WebRequest, so the JSON is printed once per closed bar where the condition holds;
  // expected JSON = the recipe payload with {{...}} filled from that bar (written here, independent of the generator)
  const hookB = recipe.blocks.filter(b => b.type === 'alert.webhook' && code.includes(`g_hook_${b.id} = iTime`));
  recipe.blocks.filter(b => b.type === 'alert.webhook' && !hookB.includes(b)).forEach(b => ok(code.includes(`TODO unsupported block alert.webhook: ${b.id}`), f, `${b.id}: webhook left as TODO`));
  if (hookB.length) { const tfName = { 1: 'M1', 5: 'M5', 15: 'M15', 30: 'M30', 60: 'H1' }[chartMin], p2 = (x) => String(x).padStart(2, '0');
    const wantH = () => { const out = []; for (const h of hookB) { const w = env.get(h.params.when); for (let jj = n0 - 2; jj <= n - 2; jj++) if (w && w[jj] === 1) { const b = bs[jj], d = new Date(b.time), fx = { symbol: 'BSVTEST', timeframe: tfName, time: `${d.getUTCFullYear()}.${p2(d.getUTCMonth() + 1)}.${p2(d.getUTCDate())} ${p2(d.getUTCHours())}:${p2(d.getUTCMinutes())}`, open: b.open.toFixed(5), high: b.high.toFixed(5), low: b.low.toFixed(5), close: b.close.toFixed(5) };
      out.push('BSV webhook ' + JSON.stringify(Object.fromEntries(Object.entries(h.params.payload).map(([k, x]) => [k, typeof x === 'string' ? x.replace(/\{\{(\w+)\}\}/g, (m0, nm) => fx[nm]) : x])))); } } return out; };
    const hooksOf = (r) => r.rt.prints.filter(x => x.startsWith('BSV webhook ')), want = wantH(), got = hooksOf(inc), same2 = (a, b) => a.length === b.length && a.every((x, k) => x === b[k]);
    ok(want.length > 0 && same2(got, want), f, `webhook JSON printed once per closed bar on the condition (${got.length} printed, ${want.length} expected)`); hooksSeen += got.length;
    for (const [mn, from, to] of [['price from the open', /DoubleToString\(iClose\(_Symbol, _Period, 1\), _Digits\)/, 'DoubleToString(iOpen(_Symbol, _Period, 1), _Digits)'], ['webhook from the forming bar', /if \((S_\w+)\(1\) && (g_hook_\w+) != iTime\(_Symbol, _Period, 1\)\) \{ \2 = iTime\(_Symbol, _Period, 1\);/, 'if ($1(0) && $2 != iTime(_Symbol, _Period, 0)) { $2 = iTime(_Symbol, _Period, 0);']]) {
      if (!from.test(code)) continue; const mc = code.replace(from, to), g2 = hooksOf(run(translate(mc).js, bs, chartMin, n0)), caught = mc !== code && !same2(g2, want); ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++; } }
  const cx = recipe.blocks.find(b => b.type === 'signal.cross' && env.get(b.id)?.some(x => x === 1));
  if (cx) { const mc = code.replace(new RegExp(`^(bool S_${cx.id}\\(int i\\) \\{ return .*?) (>|<) (.*?) && (.*?) (<=|>=) `, 'm'), (m0, a, o1, b, c, o2) => `${a} ${o1 === '>' ? '<' : '>'} ${b} && ${c} ${o2 === '<=' ? '>=' : '<='} `), r = run(translate(mc).js, bs, chartMin, n); let d = 0; for (let i = 1; i < top; i++) if (!!r.F.call(`S_${cx.id}`, i) !== (env.get(cx.id)[n - 1 - i] === 1)) d++;
    ok(mc !== code && d > 0, f, `mutant caught: flipped cross (${cx.id})`); if (mc !== code && d > 0) mutantsCaught++; }
  // signal.recent must look at the bars before, never the current one: the "(i+1)" -> "(i)" mutant must change the block
  for (const rc of recipe.blocks.filter(b => b.type === 'signal.recent' && env.get(b.id)?.some(x => x === 1))) { const mc = code.replace(new RegExp(`^(bool S_${rc.id}\\(int i\\) \\{ return S_\\w+)\\(i\\+1\\)`, 'm'), '$1(i)'), r = run(translate(mc).js, bs, chartMin, n); let d = 0; for (let i = 1; i < top; i++) if (!!r.F.call(`S_${rc.id}`, i) !== (env.get(rc.id)[n - 1 - i] === 1)) d++;
    ok(mc !== code && d > 0, f, `mutant caught: look-back includes the current bar (${rc.id})`); if (mc !== code && d > 0) mutantsCaught++; }
  if (htfB.length) { const mc = code.replace('CopyBuffer(handle, 0, s + 1, 1, v)', 'CopyBuffer(handle, 0, s, 1, v)'), r = run(translate(mc).js, bs, chartMin, n), b = htfB[0], hourly = compress(bs, 3600e3), R = refInd(hourly, b); let d = 0;
    for (let i = 0; i < top - 4 * 15 * b.params.length; i++) { const j = n - 1 - i, h = Math.floor(bs[j].time / 3600e3) - Math.floor(bs[0].time / 3600e3); if (h >= 1 && !same(val(r.F.call(`V_${b.id}`, i)), R[h - 1])) d++; }
    ok(mc !== code && d > 0, f, 'mutant caught: higher timeframe reads the forming higher bar (s instead of s + 1)'); if (mc !== code && d > 0) mutantsCaught++; }
  { const st0 = [...code.matchAll(/^bool (S_\w+)\(int i\) \{ return false; \} \/\/ TODO/gm)].find(m => code.split(m[1] + '(').length > 2), mc = st0 ? code.replace(st0[0], '// TODO') : code, changed = mc !== code; if (changed) { let caught = false; try { const t = translate(mc), u = [...names(t.js)].filter(x => !t.declared.has(x) && !API.has(x) && !JSKW.has(x)); caught = u.length > 0; } catch { caught = true; } ok(caught, f, 'mutant caught: a comment-only TODO block that is still referenced (the Pine bug) is an undeclared name'); if (caught) mutantsCaught++; } }
}
console.log(JSON.stringify({ target: 'mql5', recipes: files, checks, failures, names_audited: auditNames, indicators: indChecked, signals: sigChecked, htf_values: htfChecked, plots: plotsChecked, panels: panelsSeen, webhook_payloads: hooksSeen, ranges: rangeChecked, pivots: pivChecked, sweep_divergence: pivSigSeen, zones: zonesSeen, breakouts: breakoutsSeen, alerts: alertsSeen, todo_lines: todoLines, mutants_caught: mutantsCaught, alert_bars_60m_sets: fires, alerts_vacuous: vacuous, note: 'BSV MQL5-subset translator + stub of the documented MT5 API in node:vm, not MetaTrader 5' }));
process.exit(failures ? 1 : 0);
