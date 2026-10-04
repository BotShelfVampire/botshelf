#!/usr/bin/env node
// Check of the generator's AmiBroker AFL output for every recipe, with a small BSV-written AFL-subset
// parser and array evaluator. NOT AmiBroker: it only covers the statements BSV generates and follows the
// AFL function reference on amibroker.com/guide (MA, EMA, RSIa, ATR, Ref, TimeNum, BarIndex, LastValue,
// Plot, AlertIf). Checks: comments/strings/parentheses parse, every statement ends with ';', only these
// documented functions and constants are used, names are assigned before use, Ref only looks back, no Buy/Sell/Short/Cover,
// indicator values match an independent JS reference once warmed up, and replayed alerts fire only on
// completed bars, once per bar, with no misses.
// Higher timeframe (TimeFrameSet / Ref(x, -1) / TimeFrameRestore / TimeFrameExpand(..., expandFirst), AFL guide
// https://www.amibroker.com/guide/h_timeframe.html): statically, every assignment inside a TimeFrameSet block is
// Ref(<expr>, -k) (k >= 1), compressed names are used only through TimeFrameExpand with the same interval and expandFirst,
// and every TimeFrameSet is restored; dynamically, on 15-minute bars the expanded values equal an independent hourly
// reference of the previous closed hour, evaluating any prefix of the bars gives the same value at its last bar (no
// lookahead), and on hourly bars (chart not shorter) the values stay Null.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
const FN = { ema: [2, 2], ma: [2, 2], rsia: [1, 2], atr: [1, 1], ref: [2, 2], timenum: [0, 0], barindex: [0, 0], lastvalue: [1, 1], plot: [2, 9], alertif: [2, 6], printf: [1, 9], numtostr: [1, 4], writeif: [3, 3],
  timeframeset: [1, 1], timeframerestore: [0, 0], timeframeexpand: [3, 3], interval: [0, 0], iif: [3, 3], isnull: [1, 1], highestsince: [2, 2], lowestsince: [2, 2], valuewhen: [2, 3], hhv: [2, 2], llv: [2, 2] };
const CONST = new Set(['open', 'high', 'low', 'close', 'true', 'false', 'null', 'styleline',
  'expandfirst', 'indaily', 'colorblue', 'colorred', 'colorgreen', 'colororange', 'colorviolet', 'colorteal', 'colorbrown', 'colorgrey50']);
const ORDER = new Set(['buy', 'sell', 'short', 'cover']);
let checks = 0, failures = 0, files = 0;
const fail = (f, m) => { failures++; console.error('FAIL', f, m); };
const ok = (c, f, m) => { checks++; if (!c) fail(f, m); };

function tokenize(src) {
  const t = []; let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (/\s/.test(c)) { i++; continue; }
    if (src.startsWith('//', i)) { while (i < src.length && src[i] !== '\n') i++; continue; }
    if (src.startsWith('/*', i)) { const e = src.indexOf('*/', i + 2); if (e < 0) throw new Error('unclosed /* comment'); i = e + 2; continue; }
    if (c === '"') { const e = src.indexOf('"', i + 1); if (e < 0 || src.slice(i, e).includes('\n')) throw new Error('unclosed string'); t.push({ k: 'str', v: src.slice(i + 1, e) }); i = e + 1; continue; }
    let m;
    if ((m = /^\d+(\.\d+)?/.exec(src.slice(i)))) { t.push({ k: 'num', v: Number(m[0]) }); i += m[0].length; continue; }
    if ((m = /^[A-Za-z][A-Za-z0-9_]*/.exec(src.slice(i)))) { t.push({ k: 'id', v: m[0] }); i += m[0].length; continue; }
    if ((m = /^(==|!=|>=|<=|[-+*\/()<>=,;])/.exec(src.slice(i)))) { t.push({ k: 'op', v: m[0] }); i += m[0].length; continue; }
    throw new Error(`unexpected character ${JSON.stringify(c)}`);
  }
  return t;
}

function parse(tokens) {
  let i = 0; const peek = () => tokens[i], next = () => tokens[i++];
  const isOp = (v) => peek() && peek().k === 'op' && peek().v === v;
  const isKw = (v) => peek() && peek().k === 'id' && peek().v.toUpperCase() === v;
  const expect = (v) => { const x = next(); if (!x || x.v !== v) throw new Error(`expected ${v}, got ${x ? x.v : 'end'}`); };
  const bin = (sub, ops, kw) => () => { let l = sub(); for (;;) { const o = kw ? (ops.find(isKw)) : ops.find(isOp); if (!o) return l; next(); l = { t: 'bin', o, l, r: sub() }; } };
  const primary = () => {
    const x = next(); if (!x) throw new Error('unexpected end');
    if (x.k === 'num') return { t: 'num', v: x.v };
    if (x.k === 'str') return { t: 'str', v: x.v };
    if (x.k === 'op' && x.v === '(') { const e = orE(); expect(')'); return e; }
    if (x.k === 'op' && x.v === '-') return { t: 'neg', e: primary() };
    if (x.k === 'id') {
      if (isOp('(')) { next(); const args = []; if (!isOp(')')) { args.push(orE()); while (isOp(',')) { next(); args.push(orE()); } } expect(')'); return { t: 'call', f: x.v, args }; }
      return { t: 'id', v: x.v };
    }
    throw new Error(`unexpected ${x.v}`);
  };
  const mul = bin(primary, ['*', '/']), add = bin(mul, ['+', '-']), cmp = bin(add, ['==', '!=', '>=', '<=', '>', '<']);
  const notE = () => { if (isKw('NOT')) { next(); return { t: 'not', e: notE() }; } return cmp(); };
  const andE = bin(notE, ['AND'], true), orE = bin(andE, ['OR'], true);
  const stmts = [];
  while (i < tokens.length) {
    if (peek().k === 'id' && tokens[i + 1] && tokens[i + 1].v === '=') { const n = next().v; next(); stmts.push({ t: 'set', n, e: orE() }); }
    else stmts.push({ t: 'expr', e: orE() });
    expect(';');
  }
  return stmts;
}

const ivKey = (e) => e && (e.t === 'num' ? String(e.v) : e.t === 'id' ? e.v.toLowerCase() : null);
function statics(f, stmts) {
  const defined = new Set(), compressed = new Map(); let tf = null;
  const walk = (e) => {
    if (!e) return;
    if (e.t === 'call' && e.f.toLowerCase() === 'timeframeexpand') {
      const [x, iv, mode] = e.args;
      ok(x && x.t === 'id' && compressed.has(x.v.toLowerCase()) && compressed.get(x.v.toLowerCase()) === ivKey(iv), f, 'TimeFrameExpand must expand a name computed in the same TimeFrameSet interval');
      ok(mode && mode.t === 'id' && mode.v.toLowerCase() === 'expandfirst', f, 'TimeFrameExpand must use expandFirst on a Ref(x, -1) value');
      ok(tf === null, f, 'TimeFrameExpand inside a TimeFrameSet block');
      return;
    }
    if (e.t === 'id') { ok(!compressed.has(e.v.toLowerCase()), f, `compressed name ${e.v} used without TimeFrameExpand`); ok(defined.has(e.v.toLowerCase()) || CONST.has(e.v.toLowerCase()), f, `undefined name ${e.v}`); }
    if (e.t === 'call') { const s = FN[e.f.toLowerCase()]; ok(!!s, f, `undocumented function ${e.f}`); if (s) ok(e.args.length >= s[0] && e.args.length <= s[1], f, `${e.f} arg count ${e.args.length}`); if (e.f.toLowerCase() === 'ref') ok(e.args[1] && e.args[1].t === 'neg' && e.args[1].e.t === 'num' && e.args[1].e.v > 0, f, 'Ref must look back (negative constant), never ahead'); e.args.forEach(walk); }
    if (e.t === 'bin') { walk(e.l); walk(e.r); }
    if (e.t === 'not' || e.t === 'neg') walk(e.e);
  };
  for (const s of stmts) {
    const c = s.t === 'expr' && s.e.t === 'call' ? s.e.f.toLowerCase() : '';
    if (c === 'timeframeset') { ok(tf === null && ivKey(s.e.args[0]) !== null, f, 'TimeFrameSet without TimeFrameRestore first / interval not a constant'); tf = ivKey(s.e.args[0]); continue; }
    if (c === 'timeframerestore') { ok(tf !== null, f, 'TimeFrameRestore without TimeFrameSet'); tf = null; continue; }
    if (tf !== null) {
      ok(s.t === 'set' && s.e.t === 'call' && s.e.f.toLowerCase() === 'ref' && s.e.args[1] && s.e.args[1].t === 'neg' && s.e.args[1].e.t === 'num' && s.e.args[1].e.v >= 1, f, 'inside TimeFrameSet only Ref(<indicator>, -k) assignments (closed higher bars)');
      if (s.t === 'set') { s.e.args.forEach(walk); compressed.set(s.n.toLowerCase(), tf); defined.add(s.n.toLowerCase()); }
      continue;
    }
    walk(s.e);
    if (s.t === 'set') { ok(!ORDER.has(s.n.toLowerCase()) && !CONST.has(s.n.toLowerCase()) && !FN[s.n.toLowerCase()], f, `assigns reserved/order name ${s.n}`); defined.add(s.n.toLowerCase()); }
    else ok(s.e.t === 'call' && ['plot', 'alertif', 'printf'].includes(s.e.f.toLowerCase()), f, 'bare expression statement');
  }
  ok(tf === null, f, 'TimeFrameSet never restored');
}

// --- evaluator (arrays; Null = NaN) ---
const N = (n, v) => new Array(n).fill(v);
function maA(x, p) { const o = N(x.length, NaN); let s = 0; for (let i = 0; i < x.length; i++) { s += x[i]; if (i >= p) s -= x[i - p]; if (i >= p - 1) o[i] = s / p; } return o; }
function emaA(x, p) { const o = N(x.length, NaN), a = 2 / (p + 1); for (let i = p - 1; i < x.length; i++) o[i] = i === p - 1 ? x.slice(0, p).reduce((s, v) => s + v, 0) / p : a * x[i] + (1 - a) * o[i - 1]; return o; }
function rsiA(x, p) { const o = N(x.length, NaN); let P = 0, M = 0; for (let i = 1; i < x.length; i++) { const d = x[i] - x[i - 1], W = d > 0 ? d : 0, S = d < 0 ? -d : 0; P = ((p - 1) * P + W) / p; M = ((p - 1) * M + S) / p; if (i >= p) o[i] = 100 * P / (P + M); } return o; } // AFL guide: built-in RSI equivalent
function wilders(x, p) { const o = N(x.length, NaN); for (let i = 0; i < x.length; i++) o[i] = i === 0 ? x[0] : (o[i - 1] * (p - 1) + x[i]) / p; return o; }
function ctxOf(bs) {
  return { n: bs.length, price: { open: bs.map(b => b.open), high: bs.map(b => b.high), low: bs.map(b => b.low), close: bs.map(b => b.close) },
    tr: bs.map((b, i) => i === 0 ? b.high - b.low : Math.max(b.high, bs[i - 1].close) - Math.min(b.low, bs[i - 1].close)) };
}
function compress(bars, sec) {  // UTC-aligned periods of `sec` seconds: first open, max high, min low, last close
  const out = [], gidx = []; let key = null;
  bars.forEach((b, i) => { const k = Math.floor(b.time / (sec * 1000)); if (k !== key) { key = k; out.push({ time: k * sec * 1000, open: b.open, high: b.high, low: b.low, close: b.close }); } else { const o = out[out.length - 1]; o.high = Math.max(o.high, b.high); o.low = Math.min(o.low, b.low); o.close = b.close; } gidx.push(out.length - 1); });
  return { bars: out, gidx };
}
function evalAfl(stmts, bars, sink) {
  const base = ctxOf(bars), env = new Map(); let cur = base;
  const arr = (v) => Array.isArray(v) ? v : N(cur.n, v), secOf = (v) => v === 'indaily' ? 86400 : Number(v), comps = new Map();
  const comp = (sec) => { if (!comps.has(sec)) comps.set(sec, compress(bars, sec)); return comps.get(sec); };
  const ev = (e) => {
    const n = cur.n, price = cur.price, tr = cur.tr;
    switch (e.t) {
      case 'num': return e.v; case 'str': return e.v;
      case 'id': { const k = e.v.toLowerCase(); if (env.has(k)) return env.get(k); if (price[k]) return price[k]; if (k === 'true') return 1; if (k === 'false') return 0; if (k === 'null') return NaN; return k; }
      case 'neg': return arr(ev(e.e)).map(v => -v);
      case 'not': return arr(ev(e.e)).map(v => v ? 0 : 1);
      case 'bin': {
        const a = arr(ev(e.l)), b = arr(ev(e.r)), F = { '+': (x, y) => x + y, '-': (x, y) => x - y, '*': (x, y) => x * y, '/': (x, y) => x / y,
          '>': (x, y) => +(x > y), '<': (x, y) => +(x < y), '>=': (x, y) => +(x >= y), '<=': (x, y) => +(x <= y), '==': (x, y) => +(x === y), '!=': (x, y) => +(x !== y),
          AND: (x, y) => +(!!x && !!y && !Number.isNaN(x) && !Number.isNaN(y)), OR: (x, y) => +((!!x && !Number.isNaN(x)) || (!!y && !Number.isNaN(y))) }[e.o];
        return a.map((v, i) => F(v, b[i]));
      }
      case 'call': {
        const f = e.f.toLowerCase(), A = e.args.map(ev);
        if (f === 'ma') return maA(arr(A[0]), A[1]); if (f === 'ema') return emaA(arr(A[0]), A[1]); if (f === 'rsia') return rsiA(arr(A[0]), A[1] ?? 14);
        if (f === 'atr') return wilders(tr, A[0]);
        if (f === 'ref') { const x = arr(A[0]), k = Array.isArray(A[1]) ? A[1][0] : A[1]; /* -1 parses as neg(1), which evaluates to an array */ return x.map((_, i) => (i + k >= 0 && i + k < n) ? x[i + k] : NaN); }
        if (f === 'timenum') return bars.map(b => { const d = new Date(b.time); return d.getUTCHours() * 10000 + d.getUTCMinutes() * 100 + d.getUTCSeconds(); });
        if (f === 'barindex') return bars.map((_, i) => i);
        if (f === 'lastvalue') { const x = arr(A[0]); return N(n, x[n - 1]); }
        if (f === 'plot') { sink.plots.push({ name: A[1], v: arr(A[0]) }); return 0; }
        if (f === 'numtostr') { const d = Number(String(A[1] ?? 1.3).split('.')[1] || 0); return arr(A[0]).map(v => Number.isNaN(v) ? '{EMPTY}' : v.toFixed(d)); }
        if (f === 'writeif') return arr(A[0]).map(v => (v && !Number.isNaN(v)) ? A[1] : A[2]);
        if (f === 'printf') { (sink.prints || (sink.prints = [])).push(arr(A[0])[n - 1]); return 0; }
        if (f === 'timeframeset') { cur = ctxOf(comp(secOf(A[0])).bars); return 0; }
        if (f === 'timeframerestore') { cur = base; return 0; }
        if (f === 'timeframeexpand') { const c = comp(secOf(A[1])), x = A[0]; if (!Array.isArray(x) || x.length !== c.bars.length || A[2] !== 'expandfirst') throw new Error('TimeFrameExpand of a non-compressed array'); return c.gidx.map(g => x[g]); }
        if (f === 'interval') return bars.length > 1 ? (bars[1].time - bars[0].time) / 1000 : NaN;
        if (f === 'iif') { const c = arr(A[0]), a = arr(A[1]), b = arr(A[2]); return c.map((v, i) => (v && !Number.isNaN(v)) ? a[i] : b[i]); }
        if (f === 'isnull') return arr(A[0]).map(v => +Number.isNaN(v));
        if (f === 'highestsince' || f === 'lowestsince') { const c = arr(A[0]), x = arr(A[1]), hi = f === 'highestsince'; let m = NaN; return x.map((v, i) => { if (c[i] && !Number.isNaN(c[i])) m = v; else if (!Number.isNaN(m)) m = hi ? Math.max(m, v) : Math.min(m, v); return m; }); } // since the last bar where the condition held (that bar included); Null before
        if (f === 'valuewhen') { const c = arr(A[0]), x = arr(A[1]), k = A[2] === undefined ? 1 : Number(A[2]), seen = []; return x.map((v, i) => { if (c[i] && !Number.isNaN(c[i])) seen.push(v); return seen.length >= k ? seen[seen.length - k] : NaN; }); } // value at the k-th most recent bar where the condition held
        if (f === 'hhv' || f === 'llv') { const x = arr(A[0]), p = A[1]; return x.map((_, i) => { if (i < p - 1) return NaN; let m = x[i]; for (let j = i - p + 1; j < i; j++) m = f === 'hhv' ? Math.max(m, x[j]) : Math.min(m, x[j]); return m; }); } // over the last p bars, this bar included
        if (f === 'alertif') { sink.alerts.push({ text: A[2], cond: arr(A[0]), lookback: A[5] ?? 1, flags: A[4] ?? 15 }); return 0; }
      }
    }
    throw new Error('cannot evaluate ' + e.t);
  };
  for (const s of stmts) { const v = ev(s.e); if (s.t === 'set') env.set(s.n.toLowerCase(), v); }
  return env;
}

// --- independent reference (standard formulas) ---
const refSma = (x, p, i) => i < p - 1 ? NaN : x.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p;
function refEma(x, p) { const a = 2 / (p + 1); let e = NaN; return x.map((v, i) => { if (i === p - 1) e = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) e = a * v + (1 - a) * e; return i >= p - 1 ? e : NaN; }); }
function refRma(x, p) { let r = NaN; return x.map((v, i) => { if (i === p - 1) r = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) r = (r * (p - 1) + v) / p; return i >= p - 1 ? r : NaN; }); }
const bars = []; let p0 = 100; const t0 = Date.UTC(2026, 0, 5);
for (let i = 0; i < 400; i++) { const o = p0; p0 = 100 + 10 * Math.sin(i / 15) + 3 * Math.sin(i * 1.7); bars.push({ time: t0 + i * 3600e3, open: o, high: Math.max(o, p0) + 0.5 + 0.3 * Math.abs(Math.sin(i)), low: Math.min(o, p0) - 0.5, close: p0 }); }
const C = bars.map(b => b.close);
const TR = bars.map((b, i) => i === 0 ? b.high - b.low : Math.max(b.high, bars[i - 1].close) - Math.min(b.low, bars[i - 1].close));
const pxOf = { close: C, open: bars.map(b => b.open), high: bars.map(b => b.high), low: bars.map(b => b.low) };
pxOf.hl2 = bars.map(b => (b.high + b.low) / 2); pxOf.hlc3 = bars.map(b => (b.high + b.low + b.close) / 3); pxOf.ohlc4 = bars.map(b => (b.open + b.high + b.low + b.close) / 4);
let alertsSeen = 0, panelsSeen = 0, htfChecked = 0, rangeChecked = 0, breakoutsSeen = 0, mutantsCaught = 0, zonesSeen = 0, pivSigSeen = 0;
const byId = (recipe) => Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
let CUR_RECIPE = null;
function htfReadable(b) {  // indicator on a data.higher_timeframe of whole minutes < 1 day, or 1 day (what the generator renders for AFL)
  const d = byId(CUR_RECIPE)[(b.params || {}).timeframeRef], t = String(d?.params?.timeframe ?? '').toUpperCase();
  return !!d && d.type === 'data.higher_timeframe' && /^indicator\.(ema|sma|rsi|atr)$/.test(b.type) && (/^\d+$/.test(t) ? Number(t) >= 1 && Number(t) <= 1440 : /^1?D$/.test(t));
}
// 15-minute bars for the higher-timeframe check (1000 hours, aligned to the hour) and an independent hourly reference
const bars15 = []; { let q = 100; const t1 = Date.UTC(2026, 0, 5); for (let i = 0; i < 4000; i++) { const o = q; q = 100 + 10 * Math.sin(i / 37) + 2 * Math.sin(i * 1.3); bars15.push({ time: t1 + i * 900e3, open: o, high: Math.max(o, q) + 0.2 + 0.1 * Math.abs(Math.sin(i)), low: Math.min(o, q) - 0.2, close: q }); } }
const hourly = []; for (let h = 0; h < bars15.length / 4; h++) { const g = bars15.slice(4 * h, 4 * h + 4); hourly.push({ open: g[0].open, high: Math.max(...g.map(b => b.high)), low: Math.min(...g.map(b => b.low)), close: g[3].close }); }
function hourlyRef(b) {
  const p = b.params || {}, src = p.source || 'close', x = hourly.map(h => src === 'hl2' ? (h.high + h.low) / 2 : src === 'hlc3' ? (h.high + h.low + h.close) / 3 : src === 'ohlc4' ? (h.open + h.high + h.low + h.close) / 4 : h[src]);
  if (b.type === 'indicator.sma') return x.map((_, i) => refSma(x, p.length, i));
  if (b.type === 'indicator.ema') return refEma(x, p.length);
  if (b.type === 'indicator.rsi') { const g = x.map((w, i) => i ? Math.max(w - x[i - 1], 0) : 0), l = x.map((w, i) => i ? Math.max(x[i - 1] - w, 0) : 0), G = refRma(g.slice(1), p.length), Lo = refRma(l.slice(1), p.length); return [NaN, ...G.map((u, i) => 100 * u / (u + Lo[i]))]; }
  const tr = hourly.map((h, i) => i === 0 ? h.high - h.low : Math.max(h.high, hourly[i - 1].close) - Math.min(h.low, hourly[i - 1].close)); return [NaN, ...refRma(tr.slice(1), p.length)];
}
for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); CUR_RECIPE = recipe;
  const code = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), path.join(dir, f), '--target', 'amibroker'], { encoding: 'utf8' });
  files++;
  let stmts;
  try { stmts = parse(tokenize(code)); checks++; } catch (e) { fail(f, 'parse: ' + e.message); continue; }
  ok(/^\s*\/\/ End BSV generated starter\.\s*$/m.test(code), f, 'end marker');
  ok(!/\b(Buy|Sell|Short|Cover)\s*=/.test(code.replace(/\/\/.*$/gm, '')), f, 'no order arrays');
  const before = failures; statics(f, stmts);
  if (failures > before) continue; // do not evaluate code that failed the static checks
  const sink = { plots: [], alerts: [] };
  const env = evalAfl(stmts, bars, sink);
  const zoneB = recipe.blocks.filter(b => b.type === 'visual.zone' && new RegExp(`^Plot\\(V_${b.params?.source}_high, `, 'm').test(code));
  ok(sink.plots.length === recipe.blocks.filter(b => b.type === 'visual.plot').length + 2 * zoneB.length, f, 'one Plot per visual.plot, two per rendered zone');
  zoneB.forEach((z, k) => { const n0 = sink.plots.length - 2 * zoneB.length + 2 * k, hv = env.get(`v_${z.params.source}_high`), lv = env.get(`v_${z.params.source}_low`);
    const z15 = evalAfl(stmts, bars15, { plots: [], alerts: [] }); ok(sink.plots[n0].v === hv && sink.plots[n0 + 1].v === lv && z15.get(`v_${z.params.source}_high`).some(Number.isFinite), f, `${z.id}: zone lines are the source high / low (not vacuous on the 15-minute bars)`); zonesSeen++; });
  recipe.blocks.filter(b => b.type === 'visual.zone' && !zoneB.includes(b)).forEach(b => ok(code.includes(`// TODO unsupported block visual.zone: ${b.id}`), f, `${b.id}: zone left as TODO`));
  ok(sink.alerts.length === recipe.blocks.filter(b => b.type === 'alert.condition').length, f, 'one AlertIf per alert.condition');
  for (const b of recipe.blocks) {
    const v = env.get(('V_' + b.id).toLowerCase()), p = b.params || {};
    if (p.timeframeRef) { const arr = Array.isArray(v) ? v : [v]; ok(v !== undefined && arr.every(x => !Number.isFinite(x)), f, `${b.id}: higher-timeframe value stays Null when the chart (hourly here) is not shorter than the higher timeframe`); continue; }
    let want = null;
    if (b.type === 'indicator.sma') want = pxOf[p.source || 'close'].map((_, i) => refSma(pxOf[p.source || 'close'], p.length, i));
    if (b.type === 'indicator.ema') want = refEma(pxOf[p.source || 'close'], p.length);
    if (b.type === 'indicator.rsi') { const x = pxOf[p.source || 'close'], g = x.map((w, i) => i ? Math.max(w - x[i - 1], 0) : 0), l = x.map((w, i) => i ? Math.max(x[i - 1] - w, 0) : 0), G = refRma(g.slice(1), p.length), Lo = refRma(l.slice(1), p.length); want = [NaN, ...G.map((u, i) => 100 * u / (u + Lo[i]))]; }
    if (b.type === 'indicator.atr') want = refRma(TR.slice(1), p.length).map(x => x); if (b.type === 'indicator.atr') want = [NaN, ...want];
    if (!want) continue;
    const from = b.type === 'indicator.sma' ? p.length : Math.min(399, 15 * p.length); // Wilder/EMA seeds differ only while warming up
    let worst = 0; for (let i = from; i < 400; i++) worst = Math.max(worst, Math.abs(v[i] - want[i]) / Math.max(1, Math.abs(want[i])));
    ok(v && worst < 1e-6, f, `${b.id} (${b.type}) matches reference from bar ${from}: worst ${worst}`);
  }
  // higher timeframe on 15-minute bars: previous closed hour, equal to the independent reference; prefix runs agree (no lookahead)
  const htfB = recipe.blocks.filter(b => (b.params || {}).timeframeRef && htfReadable(b) && String(byId(recipe)[b.params.timeframeRef].params.timeframe) === '60');
  if (htfB.length) {
    const e15 = evalAfl(stmts, bars15, { plots: [], alerts: [] });
    for (const b of htfB) {
      const v = e15.get(('V_' + b.id).toLowerCase()), R = hourlyRef(b), from = 4 * (15 * b.params.length + 2);
      let worst = 0, bad = 0; for (let i = 0; i < bars15.length; i++) { const h = Math.floor(i / 4), want = h >= 1 ? R[h - 1] : NaN; if (i >= from) worst = Math.max(worst, Math.abs(v[i] - want) / Math.max(1, Math.abs(want))); if (i < 4) bad += Number.isFinite(v[i]) ? 1 : 0; }
      ok(worst < 1e-6 && bad === 0, f, `${b.id}: 15-minute chart value = previous closed hour of the reference (worst ${worst}, first hour non-empty ${bad})`);
      let diff = 0; for (let n = 3000; n <= 4000; n += 37) { const ep = evalAfl(stmts, bars15.slice(0, n), { plots: [], alerts: [] }).get(('V_' + b.id).toLowerCase()); const a = ep[n - 1], c = v[n - 1]; if (!(a === c || (Number.isNaN(a) && Number.isNaN(c)))) diff++; }
      ok(diff === 0, f, `${b.id}: prefix runs give the same last-bar value (no lookahead; ${diff} differ)`);
      htfChecked++;
    }
    // the prefix test must catch the shift-0 (forming bar) variant; run without the static check on purpose
    const m = code.replace(/^(H_\w+) = Ref\((.*), -1\);$/gm, '$1 = $2;');
    if (m !== code) { const ms = parse(tokenize(m)), full = evalAfl(ms, bars15, { plots: [], alerts: [] }); let caught = 0;
      for (const b of htfB) for (let n = 3001; n <= 3400; n += 1) { const a = evalAfl(ms, bars15.slice(0, n), { plots: [], alerts: [] }).get(('V_' + b.id).toLowerCase())[n - 1], c = full.get(('V_' + b.id).toLowerCase())[n - 1]; if (a !== c) { caught++; break; } }
      ok(caught === htfB.length, f, 'prefix test catches the shift-0 (forming higher bar) mutant'); }
  }
  // ranges and breakouts (structure.range / signal.breakout) on the 15-minute bars: an independent window reference written
  // here from the recipe's session (bar times read as UTC, as the evaluator's TimeNum does), every bar compared, breakouts must
  // fire (not vacuous), prefix runs agree (no lookahead), and two mutants must be caught
  const rngB = recipe.blocks.filter(b => b.type === 'structure.range' && new RegExp(`^R_${b.id} = `, 'm').test(code));
  if (rngB.length) {
    const by = byId(recipe), e15 = evalAfl(stmts, bars15, { plots: [], alerts: [] });
    const inside = (sb) => { const q = sb.params || {}, [a, z] = String(q.session || '0000-2359').split('-').map(x => +x.slice(0, 2) * 60 + +x.slice(2, 4)); return bars15.map(b => { const d = new Date(b.time), m = d.getUTCHours() * 60 + d.getUTCMinutes(); return a <= z ? m >= a && m < z : m >= a || m < z; }); };
    const refRange = (rb) => { const R = inside(by[rb.params.during]), H = [], Lo = []; let h = NaN, l = NaN;
      bars15.forEach((b, i) => { if (R[i]) { const fresh = i === 0 || !R[i - 1]; h = fresh ? b.high : Math.max(h, b.high); l = fresh ? b.low : Math.min(l, b.low); } H.push(h); Lo.push(l); }); return { R, H, Lo }; };
    const same = (a, b) => a === b || (Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-9;
    const bad = (env) => { let n = 0; for (const rb of rngB) { const q = refRange(rb); for (const k of (rb.params.track || [])) { const v = env.get(`v_${rb.id}_${k}`.toLowerCase()), w = k === 'high' ? q.H : q.Lo; for (let i = 0; i < bars15.length; i++) if (!same(v[i], w[i])) n++; } }
      for (const bb of recipe.blocks.filter(x => x.type === 'signal.breakout' && rngB.some(r => r.id === x.params?.range))) { const q = refRange(by[bb.params.range]), d = bb.params.direction || 'either', v = env.get(`s_${bb.id}`.toLowerCase());
        for (let i = 0; i < bars15.length; i++) { const c = bars15[i].close, pc = i ? bars15[i - 1].close : NaN, okb = !q.R[i] && Number.isFinite(q.H[i]) && i > 0;
          const up = okb && c > q.H[i] && pc <= q.H[i], dn = okb && c < q.Lo[i] && pc >= q.Lo[i], want = d === 'either' ? up || dn : d === 'above' ? up : dn; if (!!(v[i] && !Number.isNaN(v[i])) !== want) n++; } }
      return n; };
    for (const rb of rngB) ok(refRange(rb).H.some(Number.isFinite), f, `${rb.id}: the 15-minute bars have windows (not vacuous)`);
    ok(bad(e15) === 0, f, `range / breakout values equal the reference on every 15-minute bar (${bad(e15)} differ)`);
    rangeChecked += rngB.length;
    const bos = recipe.blocks.filter(x => x.type === 'signal.breakout' && rngB.some(r => r.id === x.params?.range));
    for (const bb of bos) { const n = e15.get(`s_${bb.id}`.toLowerCase()).filter(v => v && !Number.isNaN(v)).length; ok(n > 0, f, `${bb.id}: breakouts fire on the 15-minute bars (${n})`); breakoutsSeen += n; }
    let pd = 0; for (let n = 1200; n <= 4000; n += 151) { const ep = evalAfl(stmts, bars15.slice(0, n), { plots: [], alerts: [] }); for (const rb of rngB) for (const k of rb.params.track) if (!same(ep.get(`v_${rb.id}_${k}`.toLowerCase())[n - 1], e15.get(`v_${rb.id}_${k}`.toLowerCase())[n - 1])) pd++; }
    ok(pd === 0, f, `range prefix runs give the same last-bar value (no lookahead; ${pd} differ)`);
    for (const [mn, from, to] of [['window never resets', /HighestSince\(W_(\w+), High\)/, 'HighestSince(BarIndex() == 0, High)'], ['breakout without the close before', / AND Ref\(Close, -1\) <= V_\w+_high;/, ';']]) {
      if (mn.startsWith('breakout') && !bos.length) continue;
      const mc = code.replace(from, to); if (mc === code) { ok(false, f, `mutant could not be built: ${mn}`); continue; }
      const caught = bad(evalAfl(parse(tokenize(mc)), bars15, { plots: [], alerts: [] })) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++;
    }
  }
  // pivots, sweeps and divergences on the 15-minute bars: an independent bar-by-bar reference (pivot confirmed `right` bars later,
  // strictly beyond the left bars, at least as far as the right ones; last pivot held); sweep and divergence use the evaluator's
  // ATR / oscillator (checked against their own reference above) and are compared after warm-up; mutants must be caught
  const pivB = recipe.blocks.filter(b => b.type === 'structure.pivot' && new RegExp(`^P_${b.id}_h = `, 'm').test(code));
  if (pivB.length) {
    const by = byId(recipe), N15 = bars15.length, px15 = (k) => bars15.map(b => b[k]);
    const refPiv = (pb) => { const q = pb.params, [hk, lk] = (q.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], H = px15(hk), Lo = px15(lk), out = { h: [], l: [], ph: [], pl: [], H, Lo };
      let vh = NaN, vl = NaN; for (let i = 0; i < N15; i++) { const j = i - q.right; let up = false, dn = false;
        if (j - q.left >= 0) { up = true; dn = true; for (let n = j - q.left; n <= i; n++) { if (n === j) continue; if (n < j ? !(H[j] > H[n]) : !(H[j] >= H[n])) up = false; if (n < j ? !(Lo[j] < Lo[n]) : !(Lo[j] <= Lo[n])) dn = false; } }
        if (up) { vh = H[j]; out.ph.push(j); } if (dn) { vl = Lo[j]; out.pl.push(j); } out.h.push(vh); out.l.push(vl); } return out; };
    const same = (a, b) => a === b || (Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-9, tr = (v) => !!(v && !Number.isNaN(v));
    const sigB = recipe.blocks.filter(b => /^signal\.(liquidity_sweep|divergence)$/.test(b.type) && pivB.some(x => x.id === b.params?.pivot));
    const bad = (env) => { let n = 0; for (const pb of pivB) { const q = refPiv(pb); for (let i = 0; i < N15; i++) { if (!same(env.get(`v_${pb.id}_high`)[i], q.h[i])) n++; if (!same(env.get(`v_${pb.id}_low`)[i], q.l[i])) n++; } }
      for (const sb of sigB) { const pb = by[sb.params.pivot], q = refPiv(pb), v = env.get(`s_${sb.id}`), from = 400;
        if (sb.type === 'signal.liquidity_sweep') { const A = env.get(`v_${sb.params.atr}`), fr = Number(sb.params.minAtrFraction || 0);
          for (let i = from; i < N15; i++) { const b = bars15[i], ph = q.h[i - 1], pl = q.l[i - 1]; const w = Number.isFinite(A[i]) && ((Number.isFinite(ph) && b.high > ph && b.high - ph >= fr * A[i] && b.close < ph) || (Number.isFinite(pl) && b.low < pl && pl - b.low >= fr * A[i] && b.close > pl)); if (tr(v[i]) !== w) n++; } }
        else { const O = env.get(`v_${sb.params.oscillator}`), d = sb.params.direction || 'both', w = new Array(N15).fill(false), R = pb.params.right;
          if (d !== 'bullish') for (let k = 1; k < q.ph.length; k++) { const a = q.ph[k - 1], j = q.ph[k]; if (q.H[j] > q.H[a] && O[j] < O[a]) w[j + R] = true; }
          if (d !== 'bearish') for (let k = 1; k < q.pl.length; k++) { const a = q.pl[k - 1], j = q.pl[k]; if (q.Lo[j] < q.Lo[a] && O[j] > O[a]) w[j + R] = true; }
          for (let i = from; i < N15; i++) if (tr(v[i]) !== w[i]) n++; } }
      return n; };
    const e15 = evalAfl(stmts, bars15, { plots: [], alerts: [] });
    ok(bad(e15) === 0, f, `pivot / sweep / divergence values equal the reference on the 15-minute bars (${bad(e15)} differ)`);
    for (const sb of sigB) { const c = e15.get(`s_${sb.id}`).slice(400).filter(tr).length; ok(c > 0, f, `${sb.id}: fires on the 15-minute bars (${c}; not vacuous)`); pivSigSeen += c; }
    let pd = 0; for (let n = 1200; n <= 4000; n += 151) { const ep = evalAfl(stmts, bars15.slice(0, n), { plots: [], alerts: [] }); for (const pb of pivB) for (const k of ['high', 'low']) if (!same(ep.get(`v_${pb.id}_${k}`)[n - 1], e15.get(`v_${pb.id}_${k}`)[n - 1])) pd++; for (const sb of sigB) if (tr(ep.get(`s_${sb.id}`)[n - 1]) !== tr(e15.get(`s_${sb.id}`)[n - 1])) pd++; }
    ok(pd === 0, f, `pivot prefix runs give the same last-bar values (no lookahead; ${pd} differ)`);
    for (const [mn, from, to, need] of [['pivot without the right-side test', / AND Ref\((\w+), -(\d+)\) >= HHV\(\1, \2\);/, ';', null], ['sweep without the close back inside', / AND Close < Ref\(V_\w+_high, -1\)\)/, ')', 'signal.liquidity_sweep'], ['divergence oscillator test flipped', /\) < ValueWhen\(P_(\w+)_h, Ref\(V_/, ') > ValueWhen(P_$1_h, Ref(V_', 'signal.divergence']]) {
      if (need && !sigB.some(b => b.type === need)) continue;
      const mc = code.replace(from, to); if (mc === code) { ok(false, f, `mutant could not be built: ${mn}`); continue; }
      const caught = bad(evalAfl(parse(tokenize(mc)), bars15, { plots: [], alerts: [] })) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++;
    }
  }
  // replay: bars 300..399 arrive one by one; AlertIf sees the last `lookback` bars; flag 8 = no repeat for the same bar time
  // value panels (visual.table): printf lines for the last completed bar; expected fields decided here independently
  const tables = recipe.blocks.filter(b => b.type === 'visual.table');
  if (tables.length) {
    const by = Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
    const OKT = /^(indicator\.(ema|sma|rsi|atr)|signal\.(cross|threshold|combine|breakout)|filter\.session|structure\.range)$/;
    const deps = (b) => { const q = b.params || {}; return b.type === 'signal.cross' ? [q.left, q.right] : b.type === 'signal.threshold' ? [q.left] : b.type === 'signal.combine' ? (q.signals || []) : b.type === 'structure.range' ? [q.during] : b.type === 'signal.breakout' ? [q.range] : []; };
    const shown = (r, seen = new Set()) => { if (!by[r]) return !!pxOf[r]; if (seen.has(r)) return true; seen.add(r); const b = by[r]; if (!OKT.test(b.type) || ((b.params || {}).timeframeRef && !htfReadable(b))) return false; return deps(b).filter(Boolean).every(x => shown(x, seen)); };
    const expect = []; let skipped = 0, shownPanels = 0;
    for (const t of tables) {
      const fs2 = (t.params?.fields || []).filter(x => shown(x)); skipped += (t.params?.fields || []).length - fs2.length + (fs2.length ? 0 : 1);
      if (!fs2.length) continue; shownPanels++;
      expect.push(String(t.params?.title || t.id) + '\\n');
      for (const x0 of fs2) for (const x of by[x0].type === 'structure.range' ? by[x0].params.track.map(k => x0 + '_' + k) : [x0]) { const isB = /^(signal|filter)\./.test(by[x]?.type || ''); const at = env.get(((isB ? 'S_' : 'V_') + x).toLowerCase())[bars.length - 2]; expect.push(x + ': ' + (isB ? (at ? 'true' : 'false') : (Number.isNaN(at) ? '{EMPTY}' : at.toFixed(6))) + '\\n'); }
    }
    ok(JSON.stringify(sink.prints || []) === JSON.stringify(expect), f, `value panel printf ${JSON.stringify(sink.prints)} expected ${JSON.stringify(expect)}`);
    ok((code.match(/TODO [A-Za-z0-9_]+: visual\.table /g) || []).length === skipped && !/TODO unsupported block visual\.table/.test(code), f, `panel TODO lines (${skipped})`);
    panelsSeen += shownPanels;
  }
  sink.alerts.forEach((a, k) => {
    const fired = new Set(); let bad = 0;
    for (let n = 300; n <= 400; n++) {
      const s2 = { plots: [], alerts: [] }; evalAfl(stmts, bars.slice(0, n), s2);
      const al = s2.alerts[k];
      for (let i = Math.max(0, n - al.lookback); i < n; i++) if (al.cond[i] && !Number.isNaN(al.cond[i])) { if (i === n - 1) bad++; if (!fired.has(i)) fired.add(i); }
    }
    const full = sink.alerts[k].cond, expect = []; for (let i = 298; i < 399; i++) if (full[i]) expect.push(i); // completed bars seen while replaying (first replay: bar 298)
    alertsSeen += fired.size;
    ok(bad === 0, f, `alert ${k}: fired on a forming bar (${bad})`);
    ok(JSON.stringify([...fired].sort((x, y) => x - y)) === JSON.stringify(expect), f, `alert ${k}: fired ${[...fired]} expected ${expect}`);
  });
}
console.log(JSON.stringify({ target: 'amibroker', recipes: files, checks, failures, replay_alerts: alertsSeen, panels: panelsSeen, htf_values: htfChecked, ranges: rangeChecked, breakouts_15m: breakoutsSeen, zones: zonesSeen, sweep_divergence_15m: pivSigSeen, mutants_caught: mutantsCaught, note: 'BSV AFL-subset parser/evaluator, not AmiBroker' }));
process.exit(failures ? 1 : 0);
