#!/usr/bin/env node
// BSV MQL4 SUBSET translator + stub of the documented MT4 custom-indicator API, run in node:vm, for the generator's mql4 output
// (Issue #4, batch 32). Not MetaTrader 4 and not MetaEditor: the generated subset is translated to JavaScript (types dropped, anything
// outside the subset rejected) and run against a BSV model of the documented calls (OnInit / OnCalculate with rates_total /
// prev_calculated, series arrays Time[] Close[] ..., built-in iMA / iRSI / iATR with a symbol, timeframe and shift, iTime / iClose /
// iBars / iBarShift on any symbol, SetIndexBuffer, TimeHour / TimeMinute, SymbolSelect / SymbolsTotal / SymbolName, StringSplit, Alert,
// Print). EMPTY_VALUE = 0x7FFFFFFF (MQL4 constant). Built-in values follow the MT4 example sources: EMA seeded with the first price,
// RSI Wilder-smoothed, ATR = SIMPLE moving average of the true range; 0 where no value. Checks: every name declared or documented, no
// trade / web / file calls, buffers match #property, no array out of range, indicator / signal values against independent references,
// higher timeframe = previous closed higher bar, plots, incremental calls (new bar + ticks) = one full calculation, alerts once per
// CLOSED bar, the symbol scan (each symbol at its own bar that just closed, Market Watch when the list is empty, unknown and not-yet-
// loaded symbols skipped), pivots / divergence / liquidity sweep / pivot zones against a chronological reference, mutants. UNTESTED_RUNTIME on MT4.
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm'; import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..'), dir = path.join(root, 'trader-toolkit/recipes');
let checks = 0, failures = 0; const fail = (f, m) => { failures++; console.error('FAIL', f, m); }, ok = (c, f, m) => { checks++; if (!c) fail(f, m); };
const EMPTY = 2147483647, PER = { PERIOD_CURRENT: 0, PERIOD_M1: 1, PERIOD_M5: 5, PERIOD_M15: 15, PERIOD_M30: 30, PERIOD_H1: 60, PERIOD_H4: 240, PERIOD_D1: 1440, PERIOD_W1: 10080 }; // MT4: period = minutes
const CLR = ['clrDodgerBlue', 'clrOrange', 'clrLimeGreen', 'clrMagenta', 'clrGold', 'clrAqua'];
const API = new Set(['NULL', 'Symbol', 'Period', '_Symbol', '_Period', ...Object.keys(PER), 'INIT_SUCCEEDED', 'INIT_FAILED', 'EMPTY_VALUE', 'MODE_EMA', 'MODE_SMA', 'PRICE_CLOSE', 'PRICE_OPEN', 'PRICE_HIGH', 'PRICE_LOW', 'PRICE_MEDIAN', 'PRICE_TYPICAL',
  'DRAW_LINE', 'STYLE_SOLID', ...CLR, 'Time', 'Open', 'High', 'Low', 'Close', 'iMA', 'iRSI', 'iATR', 'iTime', 'iOpen', 'iHigh', 'iLow', 'iClose', 'iBars', 'iBarShift', 'PeriodSeconds', 'TimeHour', 'TimeMinute',
  'IndicatorShortName', 'SetIndexBuffer', 'SetIndexStyle', 'SetIndexLabel', 'Alert', 'Print', 'MathMin', 'MathMax', 'MathAbs', 'SymbolSelect', 'SymbolsTotal', 'SymbolName', 'StringSplit', 'StringLen', 'ArraySize', 'ArrayResize']);
const JSKW = new Set(['function', 'let', 'var', 'return', 'if', 'else', 'for', 'while', 'continue', 'break', 'true', 'false', 'mqlArr', 'null']);
function stripComment(line) { let s = false; for (let i = 0; i < line.length; i++) { if (line[i] === '"' && line[i - 1] !== '\\') s = !s; if (!s && line[i] === '/' && line[i + 1] === '/') return line.slice(0, i); } return line; }
const noStr = (s) => s.replace(/"(?:[^"\\]|\\.)*"/g, '""');
function translate(src) {
  const props = {}, declared = new Set(); const body = [];
  for (const raw of src.split('\n')) { const s = stripComment(raw); let m;
    if ((m = /^#property\s+(\w+)(?:\s+(.+?))?\s*$/.exec(s.trim()))) { props[m[1]] = m[2] ?? true; continue; }
    if ((m = /^#define\s+(\w+)\s+(-?\d+(?:\.\d+)?)\s*$/.exec(s.trim()))) { body.push(`var ${m[1]} = ${m[2]};`); declared.add(m[1]); continue; }
    if (/^\s*#/.test(s)) throw new Error('preprocessor line outside the subset: ' + s.trim());
    body.push(s); }
  let js = body.join('\n');
  if (/\/\s*\d+(?![\d.])/.test(noStr(js))) throw new Error('division by an integer literal (integer division in MQL4) is outside the subset');
  js = js.replace(/\(double\)\s*EMPTY_VALUE\b/g, 'EMPTY_VALUE'); // the one cast the generator writes (ternary with a double branch)
  js = js.replace(/\b(int|double|bool|void|datetime|string)\s+(\w+)\s*\(([^)]*)\)\s*\{/g, (m0, t, n, ps) => { declared.add(n); const nm = ps.split(',').map(p => p.trim()).filter(Boolean).map(p => { const q = /(\w+)\s*(\[\])?$/.exec(p); if (!q) throw new Error('parameter ' + p); declared.add(q[1]); return q[1]; }); return `function ${n}(${nm.join(', ')}) {`; });
  js = js.replace(/^input\s+string\s+(\w+)\s*=\s*("(?:[^"\\]|\\.)*")\s*;/gm, (m0, n, v) => { declared.add(n); return `let ${n} = ${v};`; });
  js = js.replace(/\b(?:double|int|bool|string|datetime)\s+(\w+)\[(\d*)\]\s*;/g, (m0, n, k) => { declared.add(n); return `let ${n} = mqlArr(${k || 0});`; });
  js = js.replace(/\b(?:int|double|bool|datetime|string|long)\s+(\w+)\s*=/g, (m0, n) => { declared.add(n); return `let ${n} =`; });
  js = js.replace(/\b(?:int|double|bool|datetime|string)\s+(\w+)\s*;/g, (m0, n) => { declared.add(n); return `let ${n} = 0;`; });
  const left = /\b(int|double|bool|void|datetime|string|long|const|input|static|class|struct|extern)\b/.exec(noStr(js));
  if (left) throw new Error(`"${left[1]}" left after translation (cast, input, static or another construct outside the subset)`);
  return { js, props, declared };
}
function names(js) { const out = new Set(); const s = noStr(js); for (const m of s.matchAll(/(\.)?\b([A-Za-z_][A-Za-z0-9_]*)\b/g)) if (!m[1] && !/^\d/.test(m[2])) out.add(m[2]); return out; }
// --- MT4 model ---
function compress(bars, ms) { const out = []; let key = null; for (const b of bars) { const k = Math.floor(b.time / ms); if (k !== key) { key = k; out.push({ time: k * ms, open: b.open, high: b.high, low: b.low, close: b.close }); } else { const o = out[out.length - 1]; o.high = Math.max(o.high, b.high); o.low = Math.min(o.low, b.low); o.close = b.close; } } return out; }
function mt4Values(kind, p, price, bs) { const n = bs.length, px = bs.map(b => price === 'median' ? (b.high + b.low) / 2 : price === 'typical' ? (b.high + b.low + b.close) / 3 : b[price]), o = new Array(n).fill(0);
  if (kind === 'ema') { const a = 2 / (p + 1); for (let i = 0; i < n; i++) o[i] = i === 0 ? px[0] : px[i] * a + o[i - 1] * (1 - a); return o; } // Moving Averages.mq4: first value = first price
  if (kind === 'sma') { let s = 0; for (let i = 0; i < n; i++) { s += px[i]; if (i >= p) s -= px[i - p]; o[i] = i >= p - 1 ? s / p : 0; } return o; }
  if (kind === 'rsi') { let P = 0, N = 0; for (let i = 1; i < n; i++) { const d = px[i] - px[i - 1]; if (i <= p) { P += Math.max(d, 0); N += Math.max(-d, 0); if (i < p) continue; P /= p; N /= p; } else { P = (P * (p - 1) + Math.max(d, 0)) / p; N = (N * (p - 1) + Math.max(-d, 0)) / p; } o[i] = N !== 0 ? 100 - 100 / (1 + P / N) : (P !== 0 ? 100 : 50); } return o; } // RSI.mq4
  if (kind === 'atr') { const tr = bs.map((b, i) => i === 0 ? 0 : Math.max(b.high, bs[i - 1].close) - Math.min(b.low, bs[i - 1].close)); let s = 0; for (let i = 1; i <= p && i < n; i++) s += tr[i]; if (p < n) o[p] = s / p; for (let i = p + 1; i < n; i++) o[i] = o[i - 1] + (tr[i] - tr[i - p]) / p; return o; } // ATR.mq4: simple average of the true range
  throw new Error('kind ' + kind); }
class MqlRangeError extends Error {}
const firstTick = (b) => ({ time: b.time, open: b.open, high: b.open, low: b.open, close: b.open });
function makeRuntime(chartMin, syms = {}) { // syms: other symbols -> full test bars (Market Watch = these symbols); each is visible up to the chart's newest bar time
  const st = { cur: [], ver: 0, forming: false }, buffers = [], alerts = [], prints = [], cache = new Map(), CH = 'BSVTEST';
  const tfOf = (tf) => tf === 0 || tf === chartMin ? 0 : tf;
  const known = (s) => s === null || s === CH || Object.prototype.hasOwnProperty.call(syms, s);
  const symBars = (s) => { if (s === null || s === CH) return st.cur; const k = 's' + s; if (cache.get(k)?.ver !== st.ver) { const full = syms[s] || [], lastT = st.cur.length ? st.cur[st.cur.length - 1].time : -Infinity, v = full.filter(b => b.time <= lastT);
    if (st.forming && v.length && v[v.length - 1].time === lastT) v[v.length - 1] = firstTick(v[v.length - 1]); cache.set(k, { ver: st.ver, v }); } return cache.get(k).v; };
  const tfBars = (s, tf) => { if (!known(s)) return []; tf = tfOf(tf); const b = symBars(s); if (tf === 0) return b; if (s !== null && s !== CH) throw new Error('higher timeframe on another symbol is outside the model'); if (!PER[Object.keys(PER).find(k => PER[k] === tf)]) throw new Error('timeframe ' + tf);
    const k = 'b' + tf; if (cache.get(k)?.ver !== st.ver) cache.set(k, { ver: st.ver, v: compress(b, tf * 60e3) }); return cache.get(k).v; };
  const price = { 0: 'close', 1: 'open', 2: 'high', 3: 'low', 4: 'median', 5: 'typical' }; // MQL4 ENUM_APPLIED_PRICE: PRICE_CLOSE = 0 ... PRICE_TYPICAL = 5
  const ind = (s, tf, kind, p, pr, i) => { if (!known(s)) return 0; const b = tfBars(s, tf), key = `i|${s}|${tf}|${kind}|${p}|${pr}`; if (cache.get(key)?.ver !== st.ver) cache.set(key, { ver: st.ver, v: mt4Values(kind, p, price[pr], b) }); const v = cache.get(key).v, j = v.length - 1 - i; return j >= 0 && j < v.length ? v[j] : 0; };
  const at = (s, tf, i, f) => { const b = tfBars(s, tf), j = b.length - 1 - i; return j >= 0 && j < b.length ? (f === 'time' ? b[j].time / 1000 : b[j][f]) : 0; };
  const series = (f) => new Proxy({}, { get(o, k) { if (typeof k === 'string' && /^\d+$/.test(k)) { const i = +k, n = st.cur.length; if (i >= n) throw new MqlRangeError(`array out of range ${f}[${i}] of ${n}`); const b = st.cur[n - 1 - i]; return f === 'time' ? b.time / 1000 : b[f]; } return undefined; }, set() { throw new Error('series arrays are read-only'); } });
  const mqlArr = (n = 0) => { const t = { store: new Array(n).fill(0), series: false };
    return new Proxy(t, { get(o, k) { if (k === '__t') return o; if (typeof k === 'string' && /^\d+$/.test(k)) { const i = +k; if (i >= o.store.length) throw new MqlRangeError(`array out of range [${i}] of ${o.store.length}`); return o.store[o.series ? o.store.length - 1 - i : i]; } return undefined; },
      set(o, k, v) { if (typeof k === 'string' && /^\d+$/.test(k)) { const i = +k; if (i >= o.store.length) throw new MqlRangeError(`array out of range [${i}] of ${o.store.length}`); o.store[o.series ? o.store.length - 1 - i : i] = v; return true; } throw new Error('property set ' + String(k)); } }); };
  const api = { NULL: null, Symbol: () => CH, Period: () => chartMin, _Symbol: CH, _Period: chartMin, ...PER, INIT_SUCCEEDED: 0, INIT_FAILED: 1, EMPTY_VALUE: EMPTY, MODE_SMA: 0, MODE_EMA: 1, PRICE_CLOSE: 0, PRICE_OPEN: 1, PRICE_HIGH: 2, PRICE_LOW: 3, PRICE_MEDIAN: 4, PRICE_TYPICAL: 5,
    DRAW_LINE: 0, STYLE_SOLID: 0, ...Object.fromEntries(CLR.map((c, k) => [c, k + 1])), Time: series('time'), Open: series('open'), High: series('high'), Low: series('low'), Close: series('close'),
    iMA: (s, tf, p, sh, m, pr, i) => { if (sh !== 0) throw new Error('ma_shift outside the model'); return ind(s, tf, m === 1 ? 'ema' : 'sma', p, pr, i); }, iRSI: (s, tf, p, pr, i) => ind(s, tf, 'rsi', p, pr, i), iATR: (s, tf, p, i) => ind(s, tf, 'atr', p, 0, i),
    iTime: (s, tf, i) => at(s, tf, i, 'time'), iOpen: (s, tf, i) => at(s, tf, i, 'open'), iHigh: (s, tf, i) => at(s, tf, i, 'high'), iLow: (s, tf, i) => at(s, tf, i, 'low'), iClose: (s, tf, i) => at(s, tf, i, 'close'), iBars: (s, tf) => tfBars(s, tf).length,
    iBarShift: (s, tf, t, exact) => { const b = tfBars(s, tf); let j = -1; for (let k = b.length - 1; k >= 0; k--) if (b[k].time / 1000 <= t) { j = k; break; } return j < 0 ? -1 : b.length - 1 - j; },
    PeriodSeconds: (tf = 0) => (tfOf(tf) === 0 ? chartMin : tf) * 60, TimeHour: (t) => new Date(t * 1000).getUTCHours(), TimeMinute: (t) => new Date(t * 1000).getUTCMinutes(),
    IndicatorShortName: () => true, SetIndexBuffer: (k, arr) => { arr.__t.series = true; buffers[k] = arr; return true; }, SetIndexStyle: () => undefined, SetIndexLabel: () => undefined,
    Alert: (...a) => { alerts.push({ len: st.cur.length, msg: a.join('') }); }, Print: (...a) => { prints.push({ len: st.cur.length, msg: a.join('') }); },
    SymbolSelect: (s, on) => Object.prototype.hasOwnProperty.call(syms, s) || s === CH, SymbolsTotal: (sel) => Object.keys(syms).length, SymbolName: (k, sel) => Object.keys(syms)[k] ?? '', StringLen: (s) => String(s).length,
    StringSplit: (s, sep, arr) => { const parts = String(s).split(sep); arr.__t.store = parts; return parts.length; }, ArraySize: (arr) => arr.__t.store.length, ArrayResize: (arr, n) => { const t = arr.__t; while (t.store.length < n) t.store.push(0); t.store.length = n; return n; },
    MathMin: Math.min, MathMax: Math.max, MathAbs: Math.abs, mqlArr };
  return { st, api, buffers, alerts, prints };
}
function run(js, bars, chartMin, n0, syms = {}) { // n0 = bars on the first call; then each new bar arrives as a first tick and then its final tick
  const rt = makeRuntime(chartMin, syms), ctx = vm.createContext({ ...rt.api });
  vm.runInContext('"use strict";\n' + js + '\n;globalThis.__bsv = { OnInit, OnCalculate, call: (n, i) => globalThis[n](i) };', ctx, { timeout: 20000 });
  for (const [k, v] of Object.entries(rt.api)) if (k !== 'mqlArr' && typeof v !== 'function' && typeof v !== 'object' && ctx[k] !== v) throw new Error('documented constant overwritten: ' + k);
  const F = ctx.__bsv, init = F.OnInit(); if (init !== 0) return { init, rt, F };
  let prev = 0; const call = (cur, forming = false) => { rt.st.cur = cur; rt.st.forming = forming; rt.st.ver++; for (const b of rt.buffers) if (b) { const t = b.__t, add = cur.length - t.store.length; if (add > 0) t.store = [...t.store, ...new Array(add).fill(EMPTY)]; } // MT4 adds the new bar's buffer element (EMPTY_VALUE)
    prev = F.OnCalculate(cur.length, prev, [], [], [], [], [], [], [], []); };
  call(bars.slice(0, n0));
  for (let k = n0; k < bars.length; k++) { call([...bars.slice(0, k), firstTick(bars[k])], true); call(bars.slice(0, k + 1)); }
  return { init, rt, F };
}
// --- independent references (standard formulas) and synthetic bars (as in the MQL5 check) ---
const fin = Number.isFinite, val = (v) => v === EMPTY ? NaN : v, same = (a, b) => (Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-9, tr = (v) => !!v;
const refSma = (x, p) => x.map((_, i) => i < p - 1 ? NaN : x.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p);
function refEma(x, p) { const a = 2 / (p + 1); let e = NaN; return x.map((v, i) => { if (i === p - 1) e = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) e = a * v + (1 - a) * e; return i >= p - 1 ? e : NaN; }); }
function refRma(x, p) { let r = NaN; return x.map((v, i) => { if (i === p - 1) r = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) r = (r * (p - 1) + v) / p; return i >= p - 1 ? r : NaN; }); }
const mkBars = (n, ms, f, t0 = Date.UTC(2026, 0, 5)) => { const out = []; let q = 100; for (let i = 0; i < n; i++) { const o = q; q = f(i); out.push({ time: t0 + i * ms, open: o, high: Math.max(o, q) + 0.5 + 0.3 * Math.abs(Math.sin(i)), low: Math.min(o, q) - 0.5, close: q }); } return out; };
const bars60 = mkBars(1200, 3600e3, i => 100 + 10 * Math.sin(i / 15) + 3 * Math.sin(i * 1.7)), bars15 = mkBars(4000, 900e3, i => 100 + 10 * Math.sin(i / 37) + 2 * Math.sin(i * 1.3));
const barsAlt60 = mkBars(1200, 3600e3, i => 100 + 22 * Math.sin(i / 23) + 6 * Math.sin(i / 4.1) + 2 * Math.sin(i * 1.9));
const srcOf = (bs, s) => bs.map(b => s === 'hl2' ? (b.high + b.low) / 2 : s === 'hlc3' ? (b.high + b.low + b.close) / 3 : b[s || 'close']);
const refInd = (bs, b) => { const p = b.params || {}, x = srcOf(bs, p.source); if (b.type === 'indicator.sma') return refSma(x, p.length); if (b.type === 'indicator.ema') return refEma(x, p.length);
  if (b.type === 'indicator.rsi') { const G = refRma(x.slice(1).map((w, i) => Math.max(w - x[i], 0)), p.length), L = refRma(x.slice(1).map((w, i) => Math.max(x[i] - w, 0)), p.length); return [NaN, ...G.map((u, i) => 100 * u / (u + L[i]))]; }
  const trs = bs.map((h, i) => i === 0 ? NaN : Math.max(h.high, bs[i - 1].close) - Math.min(h.low, bs[i - 1].close)); return [NaN, ...refSma(trs.slice(1), p.length)]; };
const refPiv = (bs, pb) => { const q = pb.params, n = bs.length, [hk, lk] = (q.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], H = bs.map(b => b[hk]), Lo = bs.map(b => b[lk]), out = { h: [], l: [], ph: [], pl: [], H, Lo }; let vh = NaN, vl = NaN;
  for (let i = 0; i < n; i++) { const j = i - q.right; let up = false, dn = false; if (j - q.left >= 0) { up = true; dn = true; for (let m = j - q.left; m <= i; m++) { if (m === j) continue; if (m < j ? !(H[j] > H[m]) : !(H[j] >= H[m])) up = false; if (m < j ? !(Lo[j] < Lo[m]) : !(Lo[j] <= Lo[m])) dn = false; } }
    if (up) { vh = H[j]; out.ph.push(j); } if (dn) { vl = Lo[j]; out.pl.push(j); } out.h.push(vh); out.l.push(vl); } return out; };
const refDiv = (bs, pb, O, dir) => { const q = refPiv(bs, pb), w = new Array(bs.length).fill(false), R = pb.params.right; // O(j) = oscillator at chronological bar j
  if (dir !== 'bullish') for (let k = 1; k < q.ph.length; k++) { const a = q.ph[k - 1], j = q.ph[k]; if (q.H[j] > q.H[a] && fin(O(j)) && fin(O(a)) && O(j) < O(a)) w[j + R] = true; }
  if (dir !== 'bearish') for (let k = 1; k < q.pl.length; k++) { const a = q.pl[k - 1], j = q.pl[k]; if (q.Lo[j] < q.Lo[a] && fin(O(j)) && fin(O(a)) && O(j) > O(a)) w[j + R] = true; } return w; };
let sweepFires = 0, sweepMutants = 0, zonesChecked = 0, files = 0, auditNames = 0, indChecked = 0, sigChecked = 0, htfChecked = 0, plotsChecked = 0, alertsSeen = 0, todoLines = 0, mutantsCaught = 0, scanHits = 0, pivSig = 0, scanSkips = 0;
const same3 = (a, b) => a.length === b.length && a.every((x, k) => x === b[k]);
for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')), by = Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
  const code = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), path.join(dir, f), '--target', 'mql4'], { encoding: 'utf8' });
  files++; todoLines += (code.match(/TODO unsupported block /g) || []).length;
  let T; try { T = translate(code); checks++; } catch (e) { fail(f, 'translate: ' + e.message); continue; }
  const used = names(T.js), unknown = [...used].filter(n => !T.declared.has(n) && !API.has(n) && !JSKW.has(n)); auditNames += used.size;
  ok(unknown.length === 0, f, `undeclared or undocumented names: ${unknown.join(', ')}`);
  ok(!/\b(OrderSend|OrderClose|OrderModify|WebRequest|FileOpen|SendMail|SendNotification)\b/.test(code.split('\n').map(stripComment).join('\n')), f, 'no trade, web, mail or file calls (indicator only)');
  ok(T.props.strict === true && +T.props.indicator_buffers === (code.match(/SetIndexBuffer\(/g) || []).length, f, '#property strict and indicator_buffers = SetIndexBuffer calls');
  if (unknown.length) continue;
  const htfB = recipe.blocks.filter(b => new RegExp(`^double V_${b.id}\\(int i\\) \\{ int k = BsvHtfShift\\(`, 'm').test(code));
  if (htfB.length) { let r; try { r = run(T.js, bars60.slice(0, 400), 60, 400); } catch (e) { r = { init: 'error ' + e.message }; } ok(r.init === 1, f, `OnInit returns INIT_FAILED on an hourly chart (got ${r.init})`); }
  const chartMin = htfB.length || recipe.blocks.some(b => b.type === 'filter.session') ? 15 : 60, bs = chartMin === 15 ? bars15 : bars60, n = bs.length, n0 = Math.max(400, n - 1500), W = +((/^#define BSV_WARMUP (\d+)$/m.exec(code) || [])[1] || 0);
  let full, inc; try { full = run(T.js, bs, chartMin, n); inc = run(T.js, bs, chartMin, n0); checks++; } catch (e) { fail(f, 'run: ' + (e instanceof MqlRangeError ? 'MT4 would stop the indicator: ' : '') + e.message); continue; }
  ok(full.init === 0 && inc.init === 0, f, 'OnInit returns INIT_SUCCEEDED on the test chart');
  const S = (name, i) => full.F.call(name, i), hasFn = (name) => new RegExp(`^(?:bool|double) ${name}\\(int i\\)`, 'm').test(code), top = n - W;
  const series = (F, name, conv = (x) => x, nn = n, tt = top) => { const out = new Array(nn).fill(NaN); for (let i = 0; i < tt; i++) out[nn - 1 - i] = conv(F.call(name, i)); return out; };
  const env = new Map();
  for (const b of recipe.blocks) { const p = b.params || {};
    if (/^indicator\./.test(b.type) && hasFn(`V_${b.id}`)) { const v = series(full.F, `V_${b.id}`, val); env.set(b.id, v);
      if (htfB.includes(b)) { const hourly = compress(bs, 3600e3), R = refInd(hourly, b), gk = bs.map(x => Math.floor(x.time / 3600e3) - Math.floor(bs[0].time / 3600e3)); let worst = 0; const from = n - top + 4 * 15 * p.length + 8;
        for (let j = from; j < n; j++) { const want = gk[j] >= 1 ? R[gk[j] - 1] : NaN; worst = Math.max(worst, Math.abs(v[j] - want) / Math.max(1, Math.abs(want))); }
        ok(worst < 1e-6, f, `${b.id}: 15-minute value = previous closed hour of the reference (worst ${worst})`); htfChecked++; continue; }
      const R = refInd(bs, b), from = n - top + 15 * p.length; let worst = 0; for (let j = from; j < n; j++) worst = Math.max(worst, Math.abs(v[j] - R[j]) / Math.max(1, Math.abs(R[j])));
      ok(worst < 1e-6, f, `${b.id} (${b.type}) matches the reference from bar ${from}: worst ${worst}`); indChecked++; }
    if (/^(signal\.(cross|threshold|combine|recent)|filter\.session)$/.test(b.type) && hasFn(`S_${b.id}`)) { const v = series(full.F, `S_${b.id}`, x => +tr(x)), g = (r) => env.get(r) || srcOf(bs, r), want = new Array(n).fill(false);
      if (b.type === 'signal.cross') { const a = g(p.left), c = g(p.right); for (let j = 1; j < n; j++) want[j] = [a[j], c[j], a[j - 1], c[j - 1]].every(fin) && (p.direction === 'below' ? a[j] < c[j] && a[j - 1] >= c[j - 1] : a[j] > c[j] && a[j - 1] <= c[j - 1]); }
      if (b.type === 'signal.threshold') { const a = g(p.left), c = typeof p.right === 'string' && p.right ? g(p.right) : null, op = p.op || '>='; for (let j = 0; j < n; j++) { const x = c ? c[j] : Number(p.value); want[j] = fin(a[j]) && fin(x) && { '>': a[j] > x, '>=': a[j] >= x, '<': a[j] < x, '<=': a[j] <= x, '==': a[j] === x, '!=': a[j] !== x }[op]; } }
      if (b.type === 'signal.recent') { const sg = env.get(p.signal) || []; for (let j = 0; j < n; j++) { want[j] = false; for (let k = 1; k <= p.bars && j - k >= 0; k++) if (sg[j - k] === 1) want[j] = true; } }
      if (b.type === 'signal.combine') { const L = (p.signals || []).map(r => env.get(r)); for (let j = 0; j < n; j++) want[j] = L.length > 0 && L.every(Boolean) && (p.mode === 'any' ? L.some(s => s[j] === 1) : L.every(s => s[j] === 1)); }
      if (b.type === 'filter.session') { const [s0, s1] = String(p.session || '0000-2359').split('-').map(x => +x.slice(0, 2) * 60 + +x.slice(2, 4)); for (let j = 0; j < n; j++) { const d = new Date(bs[j].time), m = d.getUTCHours() * 60 + d.getUTCMinutes(); want[j] = s0 <= s1 ? m >= s0 && m < s1 : m >= s0 || m < s1; } }
      let bad = 0; for (let j = n - top + 1 + (b.type === 'signal.recent' ? p.bars : 0); j < n; j++) if (v[j] !== +want[j]) bad++; ok(bad === 0, f, `${b.id} (${b.type}) equals the independent recomputation (${bad} differ)`); env.set(b.id, v); sigChecked++; } }
  for (const m of code.matchAll(/^(bool|double) ([SV])_(\w+)\(int i\) \{ return (false|EMPTY_VALUE); \} \/\/ TODO unsupported block/gm)) { let bad = 0; for (let i = 0; i < top; i += 7) { const x = S(`${m[2]}_${m[3]}`, i); if (m[1] === 'bool' ? x !== false : x !== EMPTY) bad++; } ok(bad === 0, f, `${m[3]}: TODO stub never true / never a value`); }
  ok(recipe.blocks.every(b => /^(visual\.plot|alert\.condition)$/.test(b.type) || hasFn(`S_${b.id}`) || hasFn(`V_${b.id}`) || hasFn(`V_${b.id}_high`) || code.includes(`g_scan_${b.id}_t = Time[1]`) || code.includes(`TODO unsupported block ${b.type}: ${b.id}`) || code.includes(`// ${b.id}: higher timeframe`) || code.includes(`// ${b.id}: zone drawn as two lines`) || (b.type === 'visual.table' && code.includes(`// TODO ${b.id}`))), f, 'every block is rendered or a declared TODO stub');
  // pivots / divergence (only inside the scan recipe on MQL4): chronological reference written here; the oscillator = the model value checked above
  const pivB = recipe.blocks.filter(b => b.type === 'structure.pivot' && hasFn(`V_${b.id}_high`)), divB = recipe.blocks.filter(b => b.type === 'signal.divergence' && hasFn(`S_${b.id}_bear`));
  const badP = (F, bsx = bs, nx = n) => { let d = 0; const from = Math.max(400, nx - (nx - W));
    for (const pb of pivB) { const q = refPiv(bsx, pb); for (let j = from; j < nx; j++) { if (!same(val(F.call(`V_${pb.id}_high`, nx - 1 - j)), q.h[j])) d++; if (!same(val(F.call(`V_${pb.id}_low`, nx - 1 - j)), q.l[j])) d++; } }
    for (const sb of divB) { const w = refDiv(bsx, by[sb.params.pivot], (j) => val(F.call(`V_${sb.params.oscillator}`, nx - 1 - j)), sb.params.direction || 'both'); for (let j = from; j < nx; j++) if (!!F.call(`S_${sb.id}`, nx - 1 - j) !== w[j]) d++; } return d; };
  if (pivB.length) { const d0 = badP(full.F); ok(d0 === 0, f, `pivot / divergence equal the chronological reference on every bar from 400 (${d0} differ)`);
    for (const pb of pivB) { const q = refPiv(bs, pb); ok(q.ph.length > 0 && q.pl.length > 0, f, `${pb.id}: pivots occur (not vacuous)`); }
    for (const sb of divB) { let c = 0; for (let j = 400; j < n; j++) if (full.F.call(`S_${sb.id}`, n - 1 - j)) c++; ok(c > 0, f, `${sb.id}: fires (${c}; not vacuous)`); pivSig += c; if (d0 === 0) env.set(sb.id, series(full.F, `S_${sb.id}`, x => +tr(x))); }
    for (const [mn, from, to] of [['pivot without the right-side test', / for \(int k = 1; k <= \d+; k\+\+\) if \((?:iClose|iHigh)\((?:g_sym|NULL), 0, c - k\) > v\) return\(false\);/, ''], ...(divB.length ? [['divergence oscillator test flipped', / && o1 < o0; \}/, ' && o1 > o0; }']] : [])]) {
      const mc = code.replace(from, to), caught = mc !== code && badP(run(translate(mc).js, bs, chartMin, n).F) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++; } }
  // liquidity sweep (batch 37): chronological reference = last pivot confirmed BEFORE the bar (refPiv at j - 1), the model ATR (checked above against
  // the reference; MT4 iATR returns 0 while it has no value), wick beyond by >= minAtrFraction x ATR, close back inside.
  const swB = recipe.blocks.filter(b => b.type === 'signal.liquidity_sweep' && new RegExp(`^bool S_${b.id}\\(int i\\) \\{ double a = `, 'm').test(code));
  const swWant = (sb) => { const q = refPiv(bs, by[sb.params.pivot]), A = env.get(sb.params.atr) || [], fr = Number(sb.params.minAtrFraction || 0), w = new Array(n).fill(false);
    for (let j = 1; j < n; j++) { const a = A[j], ph = q.h[j - 1], pl = q.l[j - 1], b = bs[j]; if (!fin(a) || a <= 0) continue; const m = fr * a; w[j] = (fin(ph) && b.high > ph && b.high - ph >= m && b.close < ph) || (fin(pl) && b.low < pl && pl - b.low >= m && b.close > pl); } return w; };
  const swBad = (F, sb, w) => { let d = 0; for (let j = n - top + 1; j < n; j++) if (!!F.call(`S_${sb.id}`, n - 1 - j) !== w[j]) d++; return d; };
  for (const sb of swB) { const w = swWant(sb), d0 = swBad(full.F, sb, w), c = w.slice(n - top + 1).filter(Boolean).length;
    ok(d0 === 0, f, `${sb.id}: sweep equals the chronological reference on every calculated bar (${d0} differ)`); ok(c > 0, f, `${sb.id}: sweep fires (${c}; not vacuous)`); sweepFires += c; sigChecked++;
    if (d0 === 0) env.set(sb.id, series(full.F, `S_${sb.id}`, x => +tr(x)));
    for (const [mn, from, to] of [['sweep without the close-back-inside test', ' && c < ph)', ')'], ['sweep ignores the ATR fraction', ' && h - ph >= m && ', ' && '], ['sweep reads the pivot including bar i', `double ph = V_${sb.params.pivot}_high(i + 1); double pl = V_${sb.params.pivot}_low(i + 1);`, `double ph = V_${sb.params.pivot}_high(i); double pl = V_${sb.params.pivot}_low(i);`], ['sweep reads the forming direction (high/low swapped)', `return (ph != EMPTY_VALUE && h > ph`, `return (ph != EMPTY_VALUE && l > ph`]]) {
      const mc = code.replace(from, to), caught = mc !== code && swBad(run(translate(mc).js, bs, chartMin, n).F, sb, w) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) { mutantsCaught++; sweepMutants++; } } }
  // plots: one buffer per visual.plot holding its source; the incremental run equals one full calculation
  const plotB = recipe.blocks.filter(b => b.type === 'visual.plot');
  const zoneB = recipe.blocks.filter(b => b.type === 'visual.zone' && code.includes(`double Buf_${b.id}_high[];`));
  ok(full.rt.buffers.length === plotB.length + 2 * zoneB.length, f, 'one indicator buffer per visual.plot, two per rendered visual.zone');
  plotB.forEach((b, k) => { const fb = full.rt.buffers[k]?.__t, ib = inc.rt.buffers[k]?.__t; if (!fb || !ib) { ok(false, f, `${b.id}: buffer`); return; } const v = env.get(b.params.source) || srcOf(bs, b.params.source); let bad = 0, binc = 0;
    for (let i = 0; i < top; i++) { const j = n - 1 - i; if (!same(val(fb.store[j]), v[j])) bad++; if (!same(val(ib.store[j]), val(fb.store[j]))) binc++; }
    ok(bad === 0, f, `${b.id}: plot buffer = its source on every calculated bar (${bad} differ)`); ok(binc === 0, f, `${b.id}: incremental calls (new bar + ticks) equal one full calculation (${binc} differ)`); plotsChecked++; });
  if (plotB.length) { const mc = code.replace('   if (prev_calculated > 0) limit++;\n', ''), r = run(translate(mc).js, bs, chartMin, n0); let binc = 0; plotB.forEach((b, k) => { const fb = full.rt.buffers[k].__t, ib = r.rt.buffers[k].__t; for (let i = 0; i < top; i++) if (!same(val(ib.store[n - 1 - i]), val(fb.store[n - 1 - i]))) binc++; });
    ok(mc !== code && binc > 0, f, 'mutant caught: the bar that just closed is not recalculated (no limit++)'); if (mc !== code && binc > 0) mutantsCaught++; }
  // zones (batch 37): two buffers after the plots = last confirmed pivot high / low (chronological reference); incremental = full
  zoneB.forEach((z, k) => { const q = refPiv(bs, by[z.params.source]); for (const [jj, key] of [[0, 'h'], [1, 'l']]) { const x = plotB.length + 2 * k + jj, fb = full.rt.buffers[x]?.__t, ib = inc.rt.buffers[x]?.__t; if (!fb || !ib) { ok(false, f, `${z.id}: zone buffer ${x}`); continue; }
      let bad = 0, binc = 0, seen = 0; for (let i = 0; i < top; i++) { const j = n - 1 - i; if (!same(val(fb.store[j]), q[key][j])) bad++; if (!same(val(ib.store[j]), val(fb.store[j]))) binc++; if (fin(q[key][j])) seen++; }
      ok(bad === 0 && seen > 0, f, `${z.id}: zone ${key === 'h' ? 'high' : 'low'} buffer = last confirmed pivot on every calculated bar (${bad} differ, ${seen} with a value)`); ok(binc === 0, f, `${z.id}: zone incremental calls equal one full calculation (${binc} differ)`); zonesChecked++; }
    const mc = code.replace(`Buf_${z.id}_low[i] = V_${z.params.source}_low(i);`, `Buf_${z.id}_low[i] = V_${z.params.source}_high(i);`), r = mc !== code ? run(translate(mc).js, bs, chartMin, n) : null; let d = 0;
    if (r) { const lb = r.rt.buffers[plotB.length + 2 * k + 1].__t; for (let i = 0; i < top; i++) if (!same(val(lb.store[n - 1 - i]), q.l[n - 1 - i])) d++; }
    ok(d > 0, f, `mutant caught: zone low buffer holds the pivot high (${z.id})`); if (d > 0) mutantsCaught++; });
  // alerts: once per CLOSED bar where the condition holds, never from the forming bar
  const alB = recipe.blocks.filter(b => b.type === 'alert.condition'), alertsOf = (r) => r.rt.alerts.filter(a => !a.msg.startsWith('BSV scan ')).map(a => `${a.len}|${a.msg}`), stubbed = (id) => new RegExp(`^bool S_${id}\\(int i\\) \\{ return false; \\} // TODO`, 'm').test(code);
  const wantAl = () => { const out = []; for (const b of alB) { const w = env.get(b.params.when); if (!w) continue; for (let j = n0 - 2; j <= n - 2; j++) if (w[j] === 1) out.push(`${j + 2}|${b.params.message || b.id}`); } return out.sort(); };
  if (alB.length) { const got = alertsOf(inc).sort(), want = wantAl(); ok(same3(got, want), f, `alerts once per closed bar on the condition (${got.length} fired, ${want.length} expected)`); alertsSeen += got.length;
    const real = alB.filter(b => !stubbed(b.params.when));
    if (real.length && !want.length) { const fa = run(T.js, barsAlt60, 60, barsAlt60.length), ia = run(T.js, barsAlt60, 60, 400), na = barsAlt60.length, wa = [];
      if (chartMin === 60) { for (const b of real) for (let j = 398; j <= na - 2; j++) { const i = na - 1 - j; if (i < na - W && fa.F.call(`S_${b.params.when}`, i)) wa.push(`${j + 2}|${b.params.message || b.id}`); }
        const ga = alertsOf(ia).sort(); wa.sort(); ok(same3(ga, wa), f, `stronger-swing bars: alerts once per closed bar on the condition (${ga.length} fired, ${wa.length} expected)`); alertsSeen += ga.length; } }
    const mc = code.replace(/(S_\w+)\(1\) && (g_alert_\w+) != Time\[1\]\) \{ \2 = Time\[1\];/, '$1(0) && $2 != Time[0]) { $2 = Time[0];');
    if (mc !== code && want.length) { const g2 = alertsOf(run(translate(mc).js, bs, chartMin, n0)).sort(), caught = !same3(g2, want); ok(caught, f, 'mutant caught: alert from the forming bar (0 instead of 1)'); if (caught) mutantsCaught++; } }
  // symbol scan: once per closed chart bar, each symbol's signal at its own bar that just closed. Expected per symbol = the same script run as a chart
  // on that symbol's bars (the chart symbol's series is the one checked above). Other symbols have their own swings; one starts 370 bars later
  // (so it is "not loaded yet" at the first incremental call), one is only in Market Watch, one listed symbol is unknown in some runs.
  const scanB = recipe.blocks.filter(b => b.type === 'scanner.symbol_set' && code.includes(`g_scan_${b.id}_t = Time[1]`));
  recipe.blocks.filter(b => b.type === 'scanner.symbol_set' && !scanB.includes(b)).forEach(b => ok(code.includes(`TODO unsupported block scanner.symbol_set: ${b.id} - `), f, `${b.id}: scan left as an explicit TODO with the reason`));
  for (const sb of scanB) { const sig = sb.params.signal || alB[0].params.when, list = sb.params.symbols || [], dt = bs[1].time - bs[0].time, late = 370;
    const SY = Object.fromEntries(list.map((sy, k) => [sy, k === 0 ? bs : k === 1 ? mkBars(n - late, dt, i => 100 + 17 * Math.sin(i / 15) + 3 * Math.sin(i * 1.4), bs[late].time) : mkBars(n, dt, i => 100 + (12 + 5 * k) * Math.sin(i / (11 + 4 * k)) + (2 + k) * Math.sin(i * (1.1 + 0.3 * k)))]));
    SY.BSVXTRA = mkBars(n, dt, i => 100 + 9 * Math.sin(i / 9) + 4 * Math.sin(i * 0.7));
    const sigAt = {}; for (const sy of Object.keys(SY)) { const B = SY[sy], nn = B.length, F = B === bs ? full.F : run(T.js, B, chartMin, nn).F, m = new Map(); for (let i = 1; i < nn - W; i++) m.set(B[nn - 1 - i].time, !!F.call(`S_${sig}`, i)); sigAt[sy] = m; } // bar time -> signal
    ok([...sigAt[list[0]]].every(([t, x]) => { const j = bs.findIndex(b => b.time === t); return j < n - top + 1 || x === (env.get(sig)[j] === 1); }), f, `${sb.id}: symbol 1 (the chart bars) uses the signal series checked above`);
    const scanAl = (r) => r.rt.alerts.filter(a => a.msg.startsWith(`BSV scan ${sb.id}:`)).map(a => `${a.len}|${a.msg}`), skips = (r) => r.rt.prints.filter(x => x.msg.includes('symbol(s) skipped')).map(x => `${x.len}|${x.msg}`);
    const wantScan = (syms) => { const out = [], sk = []; for (let L = n0; L <= n; L++) { const t = bs[L - 2].time, tl = bs[L - 1].time; let skipped = 0; const h = [];
      for (const sy of syms) { if (!SY[sy]) { skipped++; continue; } const vis = SY[sy].filter(b => b.time <= tl).length; if (vis <= W) { skipped++; continue; } if (sigAt[sy].get(t)) h.push(sy); }
      if (skipped) sk.push(`${L}|BSV scan ${sb.id}: ${skipped} symbol(s) skipped, no data yet`); if (h.length) out.push(`${L}|BSV scan ${sb.id}: ${h.join(' ')}`); } return { out, sk }; };
    const SYl = Object.fromEntries(list.map(sy => [sy, SY[sy]])), rs = run(T.js, bs, chartMin, n0, SYl), w0 = wantScan(list), g0 = scanAl(rs), hits = list.map(sy => w0.out.filter(x => x.split(': ')[1].split(' ').includes(sy)).length);
    ok(same3(g0, w0.out), f, `${sb.id}: one alert per closed chart bar listing the symbols whose ${sig} held on their bar that just closed (${g0.length} alerts, ${w0.out.length} expected)`);
    ok(same3(skips(rs), w0.sk) && w0.sk.length > 0, f, `${sb.id}: a symbol without enough history yet is skipped and counted, then scanned (${skips(rs).length} skip prints, ${w0.sk.length} expected)`); scanSkips += w0.sk.length;
    ok(hits.every(h => h > 0), f, `${sb.id}: every symbol is listed on some bar (hits ${hits.join(' / ')}; not vacuous)`); scanHits += hits.reduce((a, b) => a + b, 0);
    { const ga = alertsOf(rs).sort(), wa = wantAl(); ok(same3(ga, wa), f, `${sb.id}: the chart alerts are unchanged while the scan runs (${ga.length} / ${wa.length})`); }
    { const mw = code.replace(new RegExp(`^(input string InpScan_${sb.id} = )"[^"]*";`, 'm'), '$1"";'), r = run(translate(mw).js, bs, chartMin, n0, SY), w = wantScan(Object.keys(SY));
      ok(mw !== code && same3(scanAl(r), w.out) && w.out.some(x => x.includes('BSVXTRA')), f, `${sb.id}: an empty list scans every Market Watch symbol (${scanAl(r).length} alerts, ${w.out.length} expected)`); }
    { const miss = list[list.length - 1], SYm = Object.fromEntries(list.filter(sy => sy !== miss).map(sy => [sy, SY[sy]])), r = run(T.js, bs, chartMin, n0, SYm), saved = SY[miss]; delete SY[miss]; const w = wantScan(list); SY[miss] = saved;
      ok(same3(scanAl(r), w.out) && r.rt.prints.some(x => x.msg === `BSV scan ${sb.id}: unknown symbol ${miss}`) && same3(skips(r), w.sk), f, `${sb.id}: an unknown symbol is reported in OnInit and skipped on every bar, the others are still scanned`); }
    for (const [mn, from, to] of [['scan reads the forming bar (shift 0)', `if (S_${sig}(1)) hits`, `if (S_${sig}(0)) hits`], ['scan ignores the symbol (reads the chart)', `         g_sym = g_scan_${sb.id}[k];\n`, ''],
      ['oscillator reads the chart symbol (NULL)', /iRSI\(g_sym, /, 'iRSI(NULL, '], ['pivot reads the chart prices', /double v = iClose\(g_sym, 0, c\);/, 'double v = Close[c];'], ['no history check', `         if (iBars(g_sym, 0) <= BSV_WARMUP) { skipped++; continue; } // no data yet\n`, '']]) {
      const mc = code.replace(from, to), r = mc !== code ? run(translate(mc).js, bs, chartMin, n0, SYl) : null, caught = !!r && !(same3(scanAl(r), w0.out) && same3(skips(r), w0.sk)); ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++; }
    { const mc = code.replace('      g_sym = Symbol();\n', ''), r = run(translate(mc).js, bs, chartMin, n0, SYl), caught = mc !== code && !same3(alertsOf(r).sort(), wantAl()); ok(caught, f, 'mutant caught: the chart symbol is not restored after the scan'); if (caught) mutantsCaught++; } }
  const cx = recipe.blocks.find(b => b.type === 'signal.cross' && env.get(b.id)?.some(x => x === 1));
  if (cx) { const mc = code.replace(new RegExp(`^(bool S_${cx.id}\\(int i\\) \\{ return .*?) (>|<) (.*?) && (.*?) (<=|>=) `, 'm'), (m0, a, o1, b, c, o2) => `${a} ${o1 === '>' ? '<' : '>'} ${b} && ${c} ${o2 === '<=' ? '>=' : '<='} `), r = run(translate(mc).js, bs, chartMin, n); let d = 0; for (let i = 1; i < top; i++) if (!!r.F.call(`S_${cx.id}`, i) !== (env.get(cx.id)[n - 1 - i] === 1)) d++;
    ok(mc !== code && d > 0, f, `mutant caught: flipped cross (${cx.id})`); if (mc !== code && d > 0) mutantsCaught++; }
  if (htfB.length) { const mc = code.replace('return s < 0 ? -1 : s + 1; }', 'return s < 0 ? -1 : s; }'), r = run(translate(mc).js, bs, chartMin, n), b = htfB[0], hourly = compress(bs, 3600e3), R = refInd(hourly, b); let d = 0;
    for (let i = 0; i < top - 4 * 15 * b.params.length; i++) { const j = n - 1 - i, h = Math.floor(bs[j].time / 3600e3) - Math.floor(bs[0].time / 3600e3); if (h >= 1 && !same(val(r.F.call(`V_${b.id}`, i)), R[h - 1])) d++; }
    ok(mc !== code && d > 0, f, 'mutant caught: higher timeframe reads the forming higher bar (s instead of s + 1)'); if (mc !== code && d > 0) mutantsCaught++; }
}
console.log(JSON.stringify({ target: 'mql4', recipes: files, checks, failures, names_audited: auditNames, indicators: indChecked, signals: sigChecked, htf_values: htfChecked, plots: plotsChecked, alerts: alertsSeen, scan_hits: scanHits, sweep_fires: sweepFires, sweep_mutants: sweepMutants, zone_buffers: zonesChecked, scan_skip_prints: scanSkips, divergence_fires: pivSig, todo_lines: todoLines, mutants_caught: mutantsCaught, note: 'BSV MQL4-subset translator + stub of the documented MT4 API in node:vm, not MetaTrader 4 (UNTESTED_RUNTIME)' }));
process.exit(failures ? 1 : 0);
