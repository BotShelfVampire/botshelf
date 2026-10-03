#!/usr/bin/env node
// Check of the generator's AmiBroker AFL output for every recipe, with a small BSV-written AFL-subset
// parser and array evaluator. NOT AmiBroker: it only covers the statements BSV generates and follows the
// AFL function reference on amibroker.com/guide (MA, EMA, RSIa, ATR, Ref, TimeNum, BarIndex, LastValue,
// Plot, AlertIf). Checks: comments/strings/parentheses parse, every statement ends with ';', only these
// documented functions and constants are used, names are assigned before use, Ref only looks back, no Buy/Sell/Short/Cover,
// indicator values match an independent JS reference once warmed up, and replayed alerts fire only on
// completed bars, once per bar, with no misses.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
const FN = { ema: [2, 2], ma: [2, 2], rsia: [1, 2], atr: [1, 1], ref: [2, 2], timenum: [0, 0], barindex: [0, 0], lastvalue: [1, 1], plot: [2, 9], alertif: [2, 6], printf: [1, 9], numtostr: [1, 4], writeif: [3, 3] };
const CONST = new Set(['open', 'high', 'low', 'close', 'true', 'false', 'null', 'styleline',
  'colorblue', 'colorred', 'colorgreen', 'colororange', 'colorviolet', 'colorteal', 'colorbrown', 'colorgrey50']);
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

function statics(f, stmts) {
  const defined = new Set();
  const walk = (e) => {
    if (!e) return;
    if (e.t === 'id') ok(defined.has(e.v.toLowerCase()) || CONST.has(e.v.toLowerCase()), f, `undefined name ${e.v}`);
    if (e.t === 'call') { const s = FN[e.f.toLowerCase()]; ok(!!s, f, `undocumented function ${e.f}`); if (s) ok(e.args.length >= s[0] && e.args.length <= s[1], f, `${e.f} arg count ${e.args.length}`); if (e.f.toLowerCase() === 'ref') ok(e.args[1] && e.args[1].t === 'neg' && e.args[1].e.t === 'num' && e.args[1].e.v > 0, f, 'Ref must look back (negative constant), never ahead'); e.args.forEach(walk); }
    if (e.t === 'bin') { walk(e.l); walk(e.r); }
    if (e.t === 'not' || e.t === 'neg') walk(e.e);
  };
  for (const s of stmts) {
    walk(s.e);
    if (s.t === 'set') { ok(!ORDER.has(s.n.toLowerCase()) && !CONST.has(s.n.toLowerCase()) && !FN[s.n.toLowerCase()], f, `assigns reserved/order name ${s.n}`); defined.add(s.n.toLowerCase()); }
    else ok(s.e.t === 'call' && ['plot', 'alertif', 'printf'].includes(s.e.f.toLowerCase()), f, 'bare expression statement');
  }
}

// --- evaluator (arrays; Null = NaN) ---
const N = (n, v) => new Array(n).fill(v);
function maA(x, p) { const o = N(x.length, NaN); let s = 0; for (let i = 0; i < x.length; i++) { s += x[i]; if (i >= p) s -= x[i - p]; if (i >= p - 1) o[i] = s / p; } return o; }
function emaA(x, p) { const o = N(x.length, NaN), a = 2 / (p + 1); for (let i = p - 1; i < x.length; i++) o[i] = i === p - 1 ? x.slice(0, p).reduce((s, v) => s + v, 0) / p : a * x[i] + (1 - a) * o[i - 1]; return o; }
function rsiA(x, p) { const o = N(x.length, NaN); let P = 0, M = 0; for (let i = 1; i < x.length; i++) { const d = x[i] - x[i - 1], W = d > 0 ? d : 0, S = d < 0 ? -d : 0; P = ((p - 1) * P + W) / p; M = ((p - 1) * M + S) / p; if (i >= p) o[i] = 100 * P / (P + M); } return o; } // AFL guide: built-in RSI equivalent
function wilders(x, p) { const o = N(x.length, NaN); for (let i = 0; i < x.length; i++) o[i] = i === 0 ? x[0] : (o[i - 1] * (p - 1) + x[i]) / p; return o; }
function evalAfl(stmts, bars, sink) {
  const n = bars.length, env = new Map(), arr = (v) => Array.isArray(v) ? v : N(n, v);
  const price = { open: bars.map(b => b.open), high: bars.map(b => b.high), low: bars.map(b => b.low), close: bars.map(b => b.close) };
  const tr = bars.map((b, i) => i === 0 ? b.high - b.low : Math.max(b.high, bars[i - 1].close) - Math.min(b.low, bars[i - 1].close));
  const ev = (e) => {
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
let alertsSeen = 0, panelsSeen = 0;
for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
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
  ok(sink.plots.length === recipe.blocks.filter(b => b.type === 'visual.plot').length, f, 'one Plot per visual.plot');
  ok(sink.alerts.length === recipe.blocks.filter(b => b.type === 'alert.condition').length, f, 'one AlertIf per alert.condition');
  for (const b of recipe.blocks) {
    const v = env.get(('V_' + b.id).toLowerCase()), p = b.params || {};
    if (p.timeframeRef) { const arr = Array.isArray(v) ? v : [v]; ok(v !== undefined && arr.every(x => !Number.isFinite(x)), f, `${b.id}: higher-timeframe block left empty, not computed on the chart timeframe`); continue; }
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
  // replay: bars 300..399 arrive one by one; AlertIf sees the last `lookback` bars; flag 8 = no repeat for the same bar time
  // value panels (visual.table): printf lines for the last completed bar; expected fields decided here independently
  const tables = recipe.blocks.filter(b => b.type === 'visual.table');
  if (tables.length) {
    const by = Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
    const OKT = /^(indicator\.(ema|sma|rsi|atr)|signal\.(cross|threshold|combine)|filter\.session)$/;
    const deps = (b) => { const q = b.params || {}; return b.type === 'signal.cross' ? [q.left, q.right] : b.type === 'signal.threshold' ? [q.left] : b.type === 'signal.combine' ? (q.signals || []) : []; };
    const shown = (r, seen = new Set()) => { if (!by[r]) return !!pxOf[r]; if (seen.has(r)) return true; seen.add(r); const b = by[r]; if (!OKT.test(b.type) || (b.params || {}).timeframeRef) return false; return deps(b).filter(Boolean).every(x => shown(x, seen)); };
    const expect = []; let skipped = 0, shownPanels = 0;
    for (const t of tables) {
      const fs2 = (t.params?.fields || []).filter(x => shown(x)); skipped += (t.params?.fields || []).length - fs2.length + (fs2.length ? 0 : 1);
      if (!fs2.length) continue; shownPanels++;
      expect.push(String(t.params?.title || t.id) + '\\n');
      for (const x of fs2) { const isB = /^(signal|filter)\./.test(by[x].type); const at = env.get(((isB ? 'S_' : 'V_') + x).toLowerCase())[bars.length - 2]; expect.push(x + ': ' + (isB ? (at ? 'true' : 'false') : (Number.isNaN(at) ? '{EMPTY}' : at.toFixed(6))) + '\\n'); }
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
console.log(JSON.stringify({ target: 'amibroker', recipes: files, checks, failures, replay_alerts: alertsSeen, panels: panelsSeen, note: 'BSV AFL-subset parser/evaluator, not AmiBroker' }));
process.exit(failures ? 1 : 0);
