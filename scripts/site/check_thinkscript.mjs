#!/usr/bin/env node
// Check of the generator's thinkorswim thinkScript output for every recipe, with a small BSV-written
// thinkScript-subset parser and array evaluator. NOT thinkorswim: it only covers the statements BSV generates
// and follows the thinkScript reference on tlc.thinkorswim.com (ExpAverage, Average, WildersAverage, Max,
// TrueRange, SecondsFromTime, SecondsTillTime, Alert, plot, declare lower, if/then/else, [n] past offsets).
// Checks: every statement parses and ends with ';', only these documented functions/constants are used,
// names are defined before use, offsets only look back, no AddOrder, declare lower iff not overlay,
// indicator values match an independent JS reference once warmed up, and a bar-by-bar replay shows
// alerts only for closed bars (the forming bar cannot change them), once per bar, with no misses.
// Secondary aggregation (manual "Referencing Secondary Aggregation"): open/high/low/close(period = AggregationPeriod.X)
// give that aggregation; an expression made only of such variables and constants keeps it (offsets [n] count its bars);
// any chart-period price or time function makes it chart-period (offsets count chart bars). The evaluator models exactly
// that (UTC-aligned periods; a secondary value shown on a chart bar = the secondary bar containing it, which in history is
// complete = lookahead unless an offset was taken). Statically, a secondary variable may reach the chart (plot, Alert,
// AddLabel, chart-period def) only if it is closed: an offset >= 1 taken in its own aggregation, or built only from closed
// ones. Dynamically, on 15-minute bars the values equal an independent hourly reference of the previous closed hour, prefix
// runs agree at their last bar (no lookahead), the no-offset mutant is caught, and on hourly charts the values stay NaN.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
const FN = { expaverage: [2, 2], average: [2, 2], wildersaverage: [2, 2], max: [2, 2], truerange: [3, 3], secondsfromtime: [1, 1], secondstilltime: [1, 1], alert: [2, 4], addlabel: [2, 6], getaggregationperiod: [0, 0], highest: [2, 2], lowest: [2, 2], min: [2, 2], isnan: [1, 1], compoundvalue: [3, 3] };
// a variable may refer to itself only as CompoundValue(1, <visible data using X[1]>, <historical data without X>) (thinkScript
// reference: CompoundValue; Referencing Historical Data); anything else that names itself is an undefined name
const hasSelf = (e, k) => !!e && ((e.t === 'id' && e.v.toLowerCase() === k) || (e.t === 'named' && hasSelf(e.e, k)) || (e.t === 'call' && e.args.some(a => hasSelf(a, k))) || (e.t === 'bin' && (hasSelf(e.l, k) || hasSelf(e.r, k))) || (e.t === 'neg' && hasSelf(e.e, k)) || (e.t === 'if' && (hasSelf(e.c, k) || hasSelf(e.a, k) || hasSelf(e.b, k))));
const selfOffsOk = (e, k) => !e ? true : e.t === 'id' ? (e.v.toLowerCase() !== k || e.off === 1) : e.t === 'named' ? selfOffsOk(e.e, k) : e.t === 'call' ? e.args.every(a => selfOffsOk(a, k)) : e.t === 'bin' ? selfOffsOk(e.l, k) && selfOffsOk(e.r, k) : e.t === 'neg' ? selfOffsOk(e.e, k) : e.t === 'if' ? selfOffsOk(e.c, k) && selfOffsOk(e.a, k) && selfOffsOk(e.b, k) : true;
const selfHold = (s) => { const k = s.n.toLowerCase(), e = s.e; return s.t === 'def' && e && e.t === 'call' && e.f.toLowerCase() === 'compoundvalue' && e.args.length === 3 && e.args[0].t === 'num' && e.args[0].v === 1 && hasSelf(e.args[1], k) && !hasSelf(e.args[2], k) && selfOffsOk(e.args[1], k); };
const AGG = { MIN: 60e3, TWO_MIN: 120e3, THREE_MIN: 180e3, FOUR_MIN: 240e3, FIVE_MIN: 300e3, TEN_MIN: 600e3, FIFTEEN_MIN: 900e3, TWENTY_MIN: 1200e3, THIRTY_MIN: 1800e3,
  HOUR: 3600e3, TWO_HOURS: 7200e3, FOUR_HOURS: 14400e3, DAY: 86400e3, TWO_DAYS: 172800e3, THREE_DAYS: 259200e3, FOUR_DAYS: 345600e3 };
const FUND = new Set(['open', 'high', 'low', 'close']);
const CONST = new Set(['open', 'high', 'low', 'close', 'yes', 'no']);
const DOTTED = { color: new Set(['BLACK', 'BLUE', 'CYAN', 'DARK_GRAY', 'DARK_GREEN', 'DARK_ORANGE', 'DARK_RED', 'GRAY', 'GREEN', 'LIGHT_GRAY', 'LIGHT_GREEN', 'LIGHT_ORANGE', 'LIGHT_RED', 'LIME', 'MAGENTA', 'ORANGE', 'PINK', 'PLUM', 'RED', 'VIOLET', 'WHITE', 'YELLOW']),
  alert: new Set(['BAR', 'ONCE', 'TICK']), aggregationperiod: new Set(Object.keys(AGG)), sound: new Set(['NoSound', 'Bell', 'Ding', 'Ring', 'Chimes']), double: new Set(['NaN']) };
const KW = new Set(['def', 'plot', 'declare', 'if', 'then', 'else', 'and', 'or']);
let checks = 0, failures = 0, files = 0;
let QUIET = false;
const fail = (f, m) => { failures++; if (!QUIET) console.error('FAIL', f, m); };
const ok = (c, f, m) => { checks++; if (!c) fail(f, m); };

function tokenize(src) {
  const t = []; let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (/\s/.test(c)) { i++; continue; }
    if (c === '#') { while (i < src.length && src[i] !== '\n') i++; continue; }
    if (c === '"') { const e = src.indexOf('"', i + 1); if (e < 0 || src.slice(i, e).includes('\n')) throw new Error('unclosed string'); t.push({ k: 'str', v: src.slice(i + 1, e) }); i = e + 1; continue; }
    let m;
    if ((m = /^\d+(\.\d+)?/.exec(src.slice(i)))) { t.push({ k: 'num', v: Number(m[0]), raw: m[0] }); i += m[0].length; continue; }
    if ((m = /^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?/.exec(src.slice(i)))) { t.push({ k: 'id', v: m[0] }); i += m[0].length; continue; }
    if ((m = /^(==|!=|>=|<=|[-+*\/()<>=,;\[\]])/.exec(src.slice(i)))) { t.push({ k: 'op', v: m[0] }); i += m[0].length; continue; }
    throw new Error(`unexpected character ${JSON.stringify(c)}`);
  }
  return t;
}

function parse(tokens) {
  let i = 0; const peek = () => tokens[i], next = () => tokens[i++];
  const isOp = (v) => peek() && peek().k === 'op' && peek().v === v;
  const isKw = (v) => peek() && peek().k === 'id' && peek().v.toLowerCase() === v;
  const expect = (v) => { const x = next(); if (!x || x.v !== v) throw new Error(`expected ${v}, got ${x ? x.v : 'end'}`); };
  const bin = (sub, ops, kw) => () => { let l = sub(); for (;;) { const o = kw ? ops.find(isKw) : ops.find(isOp); if (!o) return l; next(); l = { t: 'bin', o, l, r: sub() }; } };
  const primary = () => {
    const x = next(); if (!x) throw new Error('unexpected end');
    if (x.k === 'num') return { t: 'num', v: x.v };
    if (x.k === 'str') return { t: 'str', v: x.v };
    if (x.k === 'op' && x.v === '(') { const e = ifE(); expect(')'); return e; }
    if (x.k === 'op' && x.v === '-') return { t: 'neg', e: primary() };
    if (x.k === 'id') {
      if (KW.has(x.v.toLowerCase())) throw new Error(`unexpected keyword ${x.v}`);
      if (isOp('(')) { next(); const args = []; const arg = () => (peek() && peek().k === 'id' && tokens[i + 1] && tokens[i + 1].v === '=') ? (() => { const nm = next().v; next(); return { t: 'named', n: nm, e: ifE() }; })() : ifE();
        if (!isOp(')')) { args.push(arg()); while (isOp(',')) { next(); args.push(arg()); } } expect(')'); return { t: 'call', f: x.v, args }; }
      if (isOp('[')) { next(); const n = next(); if (!n || n.k !== 'num') throw new Error('offset must be a number'); expect(']'); return { t: 'id', v: x.v, off: n.v, offOk: Number.isInteger(n.v) && n.v >= 1 }; }
      return { t: 'id', v: x.v, off: 0 };
    }
    throw new Error(`unexpected ${x.v}`);
  };
  const mul = bin(primary, ['*', '/']), add = bin(mul, ['+', '-']), cmp = bin(add, ['==', '!=', '>=', '<=', '>', '<']);
  const andE = bin(cmp, ['and'], true), orE = bin(andE, ['or'], true);
  const ifE = () => { if (isKw('if')) { next(); const c = ifE(); if (!isKw('then')) throw new Error('expected then'); next(); const a = ifE(); if (!isKw('else')) throw new Error('expected else'); next(); return { t: 'if', c, a, b: ifE() }; } return orE(); };
  const stmts = [];
  while (i < tokens.length) {
    if (isKw('declare')) { next(); const d = next(); stmts.push({ t: 'declare', v: d && d.v }); }
    else if (isKw('def') || isKw('plot')) { const kind = next().v.toLowerCase(); const n = next(); if (!n || n.k !== 'id' || n.v.includes('.')) throw new Error('bad name'); expect('='); stmts.push({ t: kind, n: n.v, e: ifE() }); }
    else if (peek().k === 'id' && /\.SetDefaultColor$/i.test(peek().v)) { const n = next().v; expect('('); const c = next(); expect(')'); stmts.push({ t: 'color', n: n.split('.')[0], c: c && c.v }); }
    else stmts.push({ t: 'expr', e: ifE() });
    expect(';');
  }
  return stmts;
}

// context of an expression: 'P' (chart period), an AggregationPeriod name, or '' (constants only); closed = secondary and safe on the chart
function ctxInfo(e, vars) {
  const S = new Set(); let open = false;
  const w = (x, inSec) => {
    if (!x) return;
    if (x.t === 'id') { const k = x.v.toLowerCase(); if (FUND.has(k)) S.add('P'); else if (vars.has(k)) { const v = vars.get(k); if (v.ctx) S.add(v.ctx); if (v.ctx && v.ctx !== 'P' && !v.closed && !(x.off >= 1)) open = true; } return; }
    if (x.t === 'call') { const f = x.f.toLowerCase();
      if (FUND.has(f)) { const pa = x.args.find(a => a.t === 'named' && a.n.toLowerCase() === 'period'); const g = pa && pa.e.t === 'id' && /^AggregationPeriod\./.test(pa.e.v) ? pa.e.v.split('.')[1] : null; S.add(g || 'P?'); open = true; return; }
      if (f === 'secondsfromtime' || f === 'secondstilltime') S.add('P');
      x.args.forEach(a => w(a.t === 'named' ? a.e : a)); return; }
    if (x.t === 'bin') { w(x.l); w(x.r); } if (x.t === 'neg') w(x.e); if (x.t === 'if') { w(x.c); w(x.a); w(x.b); }
  };
  w(e);
  const secs = [...S].filter(x => x !== 'P'); const ctx = S.has('P') ? 'P' : (secs[0] || '');
  // an offset of a secondary variable taken inside its own aggregation closes it
  const closed = ctx !== 'P' && ctx !== '' && !open;
  return { ctx, secs, mixed: S.has('P') && secs.length > 0, many: new Set(secs).size > 1, closed, bad: S.has('P?') };
}
function statics(f, stmts, recipe) {
  const defined = new Set(), plots = new Set(), vars = new Map();
  const walk = (e) => {
    if (!e) return;
    if (e.t === 'named') { ok(e.n.toLowerCase() === 'period', f, `named argument ${e.n}`); walk(e.e); return; }
    if (e.t === 'id') {
      const k = e.v.toLowerCase(), dot = e.v.split('.');
      if (dot.length === 2) ok(DOTTED[dot[0].toLowerCase()] && DOTTED[dot[0].toLowerCase()].has(dot[1]), f, `undocumented constant ${e.v}`);
      else ok(defined.has(k) || CONST.has(k), f, `undefined name ${e.v}`);
      if (e.off) ok(e.offOk, f, `offset [${e.off}] must look back (positive integer)`);
    }
    if (e.t === 'call' && FUND.has(e.f.toLowerCase())) { ok(e.args.length === 1 && e.args[0].t === 'named' && e.args[0].e.t === 'id' && /^AggregationPeriod\./.test(e.args[0].e.v), f, `${e.f}(...) only with period = AggregationPeriod.X`); e.args.forEach(walk); return; }
    if (e.t === 'call') { const s = FN[e.f.toLowerCase()]; ok(!!s, f, `undocumented function ${e.f}`); if (s) ok(e.args.length >= s[0] && e.args.length <= s[1], f, `${e.f} arg count ${e.args.length}`); e.args.forEach(walk); }
    if (e.t === 'bin') { walk(e.l); walk(e.r); }
    if (e.t === 'neg') walk(e.e);
    if (e.t === 'if') { walk(e.c); walk(e.a); walk(e.b); }
  };
  const declares = stmts.filter(s => s.t === 'declare');
  ok(declares.length === (recipe.overlay ? 0 : 1) && declares.every(d => d.v === 'lower'), f, 'declare lower only for separate-pane recipes');
  const toChart = (e, what) => { const c = ctxInfo(e, vars); ok(!c.bad && !c.many, f, `${what}: one secondary aggregation per expression`); if (c.ctx && c.ctx !== 'P') ok(c.closed, f, `${what}: secondary value reaches the chart without a closed-bar offset`);
    if (c.mixed) { const leak = []; const w = (x) => { if (!x) return; if (x.t === 'id' && vars.has(x.v.toLowerCase())) { const v = vars.get(x.v.toLowerCase()); if (v.ctx && v.ctx !== 'P' && !v.closed) leak.push(x.v); } if (x.t === 'call') x.args.forEach(a => w(a.t === 'named' ? a.e : a)); if (x.t === 'bin') { w(x.l); w(x.r); } if (x.t === 'neg') w(x.e); if (x.t === 'if') { w(x.c); w(x.a); w(x.b); } }; w(e); ok(!leak.length && !ctxInfo(e, vars).secs.some(g => g !== 'P'), f, `${what}: chart-period expression mixes in secondary aggregation ${leak.join(',')}`); } };
  for (const s of stmts) {
    const hold = s.n && selfHold(s) && !defined.has(s.n.toLowerCase()); if (hold) defined.add(s.n.toLowerCase());
    if (s.e) walk(s.e);
    if (hold) defined.delete(s.n.toLowerCase());
    if (s.t === 'def' || s.t === 'plot') { const c = ctxInfo(s.e, vars); ok(!c.bad && !c.many, f, `${s.n}: one aggregation per variable`); if (c.ctx === 'P' && c.secs.length) toChart(s.e, s.n); if (s.t === 'plot') toChart(s.e, s.n); vars.set(s.n.toLowerCase(), { ctx: c.ctx, closed: c.closed }); }
    if (s.t === 'expr' && s.e.t === 'call') s.e.args.forEach(a => toChart(a.t === 'named' ? a.e : a, s.e.f));
    if (s.t === 'def' || s.t === 'plot') { const k = s.n.toLowerCase(); ok(!defined.has(k) && !CONST.has(k) && !FN[k], f, `redefines ${s.n}`); defined.add(k); if (s.t === 'plot') plots.add(k); }
    if (s.t === 'color') { ok(plots.has(s.n.toLowerCase()), f, `SetDefaultColor on unknown plot ${s.n}`); ok(/^Color\./.test(s.c || '') && DOTTED.color.has((s.c || '').split('.')[1]), f, `color ${s.c}`); }
    if (s.t === 'expr') {
      ok(s.e.t === 'call' && ['alert', 'addlabel'].includes(s.e.f.toLowerCase()), f, 'bare expression statement');
      if (s.e.t === 'call' && s.e.f.toLowerCase() === 'alert' && s.e.args[2]) ok(s.e.args[2].t === 'id' && s.e.args[2].v === 'Alert.BAR', f, 'alerts use Alert.BAR');
    }
  }
}

// --- evaluator (arrays; NaN for missing) ---
const N = (n, v) => new Array(n).fill(v);
const fin = Number.isFinite;
function avgA(x, p) { return x.map((_, i) => { if (i < p - 1) return NaN; let s = 0; for (let j = i - p + 1; j <= i; j++) s += x[j]; return s / p; }); }
function expA(x, p) { const a = 2 / (p + 1), o = N(x.length, NaN); let e = NaN; for (let i = 0; i < x.length; i++) { if (!fin(x[i])) { o[i] = e; continue; } e = fin(e) ? a * x[i] + (1 - a) * e : x[i]; o[i] = e; } return o; } // EMA1 = price1 (reference)
function wildA(x, p) { const o = N(x.length, NaN); let w = NaN; for (let i = 0; i < x.length; i++) { if (!fin(w)) { if (i >= p - 1 && x.slice(i - p + 1, i + 1).every(fin)) { w = x.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p; o[i] = w; } continue; } w = x[i] / p + (1 - 1 / p) * w; o[i] = w; } return o; } // first value = SMA(length)
const EST = -5 * 3600e3;
const secOfDay = (t) => { const d = new Date(t + EST); return d.getUTCHours() * 3600 + d.getUTCMinutes() * 60 + d.getUTCSeconds(); };
const hhmmSec = (v) => Math.floor(v / 100) * 3600 + (v % 100) * 60;
function compressTs(bars, ms) {
  const out = [], gidx = []; let key = null;
  bars.forEach(b => { const k = Math.floor(b.time / ms); if (k !== key) { key = k; out.push({ open: b.open, high: b.high, low: b.low, close: b.close }); } else { const o = out[out.length - 1]; o.high = Math.max(o.high, b.high); o.low = Math.min(o.low, b.low); o.close = b.close; } gidx.push(out.length - 1); });
  return { price: { open: out.map(b => b.open), high: out.map(b => b.high), low: out.map(b => b.low), close: out.map(b => b.close) }, n: out.length, gidx };
}
function evalTs(stmts, bars, sink) {
  const env = new Map(), vctx = new Map(), comps = new Map();
  const comp = (g) => { if (!comps.has(g)) comps.set(g, compressTs(bars, AGG[g])); return comps.get(g); };
  const base = { n: bars.length, price: { open: bars.map(b => b.open), high: bars.map(b => b.high), low: bars.map(b => b.low), close: bars.map(b => b.close) } };
  let cur = base, curG = 'P';
  const arr = (v) => Array.isArray(v) ? v : N(cur.n, v);
  const shift = (x, k) => x.map((_, i) => i - k >= 0 ? x[i - k] : NaN);
  const toChartArr = (v, g) => (!Array.isArray(v) || !g || g === 'P') ? v : comp(g).gidx.map(j => v[j]);  // secondary bar containing each chart bar
  const vars = new Map();
  const ev = (e) => {
    const n = cur.n, price = cur.price;
    switch (e.t) {
      case 'num': return e.v; case 'str': return e.v;
      case 'id': {
        const k = e.v.toLowerCase(); let v;
        if (env.has(k)) { v = env.get(k); const g = vctx.get(k); if (g && g !== curG && Array.isArray(v)) { if (curG !== 'P') throw new Error('chart value in a secondary expression'); v = toChartArr(v, g); } }
        else if (price[k]) v = price[k]; else if (k === 'yes') v = 1; else if (k === 'no') v = 0; else if (k === 'double.nan') v = NaN; else if (/^aggregationperiod\./.test(k)) v = AGG[e.v.split('.')[1]]; else return e.v;
        return e.off ? shift(arr(v), e.off) : v;
      }
      case 'neg': return arr(ev(e.e)).map(v => -v);
      case 'if': { const c = arr(ev(e.c)), a = arr(ev(e.a)), b = arr(ev(e.b)); return c.map((v, i) => fin(v) ? (v ? a[i] : b[i]) : NaN); }
      case 'bin': {
        const a = arr(ev(e.l)), b = arr(ev(e.r)), F = { '+': (x, y) => x + y, '-': (x, y) => x - y, '*': (x, y) => x * y, '/': (x, y) => x / y,
          '>': (x, y) => +(x > y), '<': (x, y) => +(x < y), '>=': (x, y) => +(x >= y), '<=': (x, y) => +(x <= y), '==': (x, y) => +(x === y), '!=': (x, y) => (fin(x) && fin(y)) ? +(x !== y) : 0,
          and: (x, y) => +(!!x && !!y && fin(x) && fin(y)), or: (x, y) => +((!!x && fin(x)) || (!!y && fin(y))) }[e.o.toLowerCase()];
        return a.map((v, i) => F(v, b[i]));
      }
      case 'call': {
        const f = e.f.toLowerCase();
        if (FUND.has(f)) { const g = e.args[0].e.v.split('.')[1]; if (curG !== g) throw new Error('secondary price outside its context'); return comp(g).price[f]; }
        if (f === 'getaggregationperiod') return bars.length > 1 ? bars[1].time - bars[0].time : NaN;
        const A = e.args.map(ev);
        if (f === 'expaverage') return expA(arr(A[0]), A[1]); if (f === 'average') return avgA(arr(A[0]), A[1]); if (f === 'wildersaverage') return wildA(arr(A[0]), A[1]);
        if (f === 'max') { const a = arr(A[0]), b = arr(A[1]); return a.map((v, i) => (fin(v) && fin(b[i])) ? Math.max(v, b[i]) : NaN); }
        if (f === 'min') { const a = arr(A[0]), b = arr(A[1]); return a.map((v, i) => (fin(v) && fin(b[i])) ? Math.min(v, b[i]) : NaN); }
        if (f === 'highest' || f === 'lowest') { const a = arr(A[0]), p = A[1], g = f === 'highest' ? Math.max : Math.min; return a.map((_, i) => { if (i < p - 1) return NaN; const w = a.slice(i - p + 1, i + 1); return w.every(fin) ? g(...w) : NaN; }); }
        if (f === 'isnan') return arr(A[0]).map(v => +!fin(v));
        if (f === 'compoundvalue') { const vis = arr(A[1]), hist = arr(A[2]); return vis.map((v, i) => i < A[0] ? hist[i] : v); }
        if (f === 'truerange') { const h = arr(A[0]), c = arr(A[1]), l = arr(A[2]); return h.map((v, i) => i === 0 ? v - l[i] : Math.max(v, c[i - 1]) - Math.min(l[i], c[i - 1])); }
        if ((f === 'secondsfromtime' || f === 'secondstilltime') && curG !== 'P') throw new Error('time function in secondary context');
        if (f === 'secondsfromtime') return bars.map(b => secOfDay(b.time) - hhmmSec(A[0]));
        if (f === 'secondstilltime') return bars.map(b => hhmmSec(A[0]) - secOfDay(b.time));
        if (f === 'alert') { sink.alerts.push({ text: A[1], cond: arr(A[0]) }); return 0; }
        if (f === 'addlabel') { (sink.labels || (sink.labels = [])).push({ text: arr(A[1]) }); return 0; }
      }
    }
    throw new Error('cannot evaluate ' + e.t);
  };
  // self-referencing hold, bar by bar: parts without the variable are evaluated as arrays first; X[1] is the value one bar back
  const BIN = { '+': (x, y) => x + y, '-': (x, y) => x - y, '*': (x, y) => x * y, '/': (x, y) => x / y, '>': (x, y) => +(x > y), '<': (x, y) => +(x < y), '>=': (x, y) => +(x >= y), '<=': (x, y) => +(x <= y), '==': (x, y) => +(x === y), '!=': (x, y) => (fin(x) && fin(y)) ? +(x !== y) : 0,
    and: (x, y) => +(!!x && !!y && fin(x) && fin(y)), or: (x, y) => +((!!x && fin(x)) || (!!y && fin(y))) };
  const evalHold = (s) => { const k = s.n.toLowerCase(), out = N(base.n, NaN);
    const prep = (e) => { if (!hasSelf(e, k)) { const a = arr(ev(e)); return (i) => a[i]; }
      if (e.t === 'id') return (i) => i >= 1 ? out[i - 1] : NaN;
      if (e.t === 'if') { const c = prep(e.c), a = prep(e.a), b = prep(e.b); return (i) => { const v = c(i); return fin(v) ? (v ? a(i) : b(i)) : NaN; }; }
      if (e.t === 'bin') { const l = prep(e.l), r = prep(e.r), F = BIN[e.o.toLowerCase()]; return (i) => F(l(i), r(i)); }
      if (e.t === 'neg') { const x = prep(e.e); return (i) => -x(i); }
      if (e.t === 'call' && ['max', 'min'].includes(e.f.toLowerCase()) && e.args.length === 2) { const a = prep(e.args[0]), b = prep(e.args[1]), g = e.f.toLowerCase() === 'max' ? Math.max : Math.min; return (i) => { const x = a(i), y = b(i); return fin(x) && fin(y) ? g(x, y) : NaN; }; }
      throw new Error('self reference in an unsupported form'); };
    const vis = prep(s.e.args[1]), hist = arr(ev(s.e.args[2]));
    for (let i = 0; i < base.n; i++) out[i] = i < 1 ? hist[i] : vis(i);
    return out; };
  const chartEnv = new Map();
  for (const s of stmts) {
    if (s.t === 'def' || s.t === 'plot') {
      const c = ctxInfo(s.e, vars); curG = c.ctx && c.ctx !== 'P' ? c.ctx : 'P'; cur = curG === 'P' ? base : comp(curG);
      if (selfHold(s) && curG !== 'P') throw new Error('self reference in a secondary aggregation');
      const v = selfHold(s) ? evalHold(s) : ev(s.e); cur = base; const g = c.ctx === '' ? '' : curG; curG = 'P';
      env.set(s.n.toLowerCase(), v); vctx.set(s.n.toLowerCase(), g); vars.set(s.n.toLowerCase(), { ctx: c.ctx, closed: c.closed });
      const cv = toChartArr(v, g); chartEnv.set(s.n.toLowerCase(), cv);
      if (s.t === 'plot') sink.plots.push({ name: s.n, v: Array.isArray(cv) ? cv : N(base.n, cv) });
    }
    else if (s.t === 'expr') {
      if (s.e.t === 'call' && ['alert', 'addlabel'].includes(s.e.f.toLowerCase())) {  // the condition/text is evaluated in its own context, then shown on chart bars
        const parts = s.e.args.map(a => { const c = ctxInfo(a, vars); curG = c.ctx && c.ctx !== 'P' ? c.ctx : 'P'; cur = curG === 'P' ? base : comp(curG); const v = ev(a); const g = curG; cur = base; curG = 'P'; const cv = toChartArr(v, g); return Array.isArray(cv) || typeof cv !== 'number' ? cv : N(base.n, cv); });
        const A = parts.map(v => Array.isArray(v) ? v : (typeof v === 'number' ? N(base.n, v) : v));
        if (s.e.f.toLowerCase() === 'alert') sink.alerts.push({ text: A[1], cond: A[0] }); else (sink.labels || (sink.labels = [])).push({ text: Array.isArray(A[1]) ? A[1] : N(base.n, A[1]) });
      } else ev(s.e);
    }
  }
  return chartEnv;
}

// --- independent reference (standard formulas, mean-seeded) ---
const refSma = (x, p) => x.map((_, i) => i < p - 1 ? NaN : x.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p);
function refEma(x, p) { const a = 2 / (p + 1); let e = NaN; return x.map((v, i) => { if (i === p - 1) e = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) e = a * v + (1 - a) * e; return i >= p - 1 ? e : NaN; }); }
function refRma(x, p) { let r = NaN; return x.map((v, i) => { if (i === p - 1) r = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) r = (r * (p - 1) + v) / p; return i >= p - 1 ? r : NaN; }); }
const bars = []; let p0 = 100; const t0 = Date.UTC(2026, 0, 5);
const NB = 1200, R0 = NB - 100; // long history so first-value-seeded EMAs converge
for (let i = 0; i < NB; i++) { const o = p0; p0 = 100 + 10 * Math.sin(i / 15) + 3 * Math.sin(i * 1.7); bars.push({ time: t0 + i * 3600e3, open: o, high: Math.max(o, p0) + 0.5 + 0.3 * Math.abs(Math.sin(i)), low: Math.min(o, p0) - 0.5, close: p0 }); }
const C = bars.map(b => b.close);
const TR = bars.map((b, i) => i === 0 ? b.high - b.low : Math.max(b.high, bars[i - 1].close) - Math.min(b.low, bars[i - 1].close));
const pxOf = { close: C, open: bars.map(b => b.open), high: bars.map(b => b.high), low: bars.map(b => b.low) };
pxOf.hl2 = bars.map(b => (b.high + b.low) / 2); pxOf.hlc3 = bars.map(b => (b.high + b.low + b.close) / 3); pxOf.ohlc4 = bars.map(b => (b.open + b.high + b.low + b.close) / 4);
let sigRecomputed = 0; const lookBackAlerts = {}; // recipe -> bars where the alert condition holds, for recipes that use signal.recent
let alertsSeen = 0, panelsSeen = 0, htfChecked = 0, rangeChecked = 0, breakoutsSeen = 0, mutantsCaught = 0, zonesSeen = 0, pivSigSeen = 0;
const TS_MIN = { 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 10: 1, 15: 1, 20: 1, 30: 1, 60: 1, 120: 1, 240: 1, 1440: 1, 2880: 1, 4320: 1, 5760: 1 };
function htfReadable(recipe, b) {
  const d = recipe.blocks.find(x => x.id === (b.params || {}).timeframeRef), t = String(d?.params?.timeframe ?? '').toUpperCase();
  const m = /^\d+$/.test(t) ? Number(t) : (/^(\d*)D$/.test(t) ? (Number(t.slice(0, -1)) || 1) * 1440 : null);
  return !!d && d.type === 'data.higher_timeframe' && /^indicator\.(ema|sma|rsi|atr)$/.test(b.type) && !!TS_MIN[m];
}
const bars15 = []; { let q = 100; const t1 = Date.UTC(2026, 0, 5); for (let i = 0; i < 4000; i++) { const o = q; q = 100 + 10 * Math.sin(i / 37) + 2 * Math.sin(i * 1.3); bars15.push({ time: t1 + i * 900e3, open: o, high: Math.max(o, q) + 0.2 + 0.1 * Math.abs(Math.sin(i)), low: Math.min(o, q) - 0.2, close: q }); } }
const hourly = []; for (let h = 0; h < bars15.length / 4; h++) { const g = bars15.slice(4 * h, 4 * h + 4); hourly.push({ open: g[0].open, high: Math.max(...g.map(b => b.high)), low: Math.min(...g.map(b => b.low)), close: g[3].close }); }
function hourlyRef(b) {
  const p = b.params || {}, src = p.source || 'close', x = hourly.map(h => src === 'hl2' ? (h.high + h.low) / 2 : src === 'hlc3' ? (h.high + h.low + h.close) / 3 : src === 'ohlc4' ? (h.open + h.high + h.low + h.close) / 4 : h[src]);
  if (b.type === 'indicator.sma') return refSma(x, p.length);
  if (b.type === 'indicator.ema') return refEma(x, p.length);
  if (b.type === 'indicator.rsi') { const g = x.map((w, i) => i ? Math.max(w - x[i - 1], 0) : 0), l = x.map((w, i) => i ? Math.max(x[i - 1] - w, 0) : 0), G = refRma(g.slice(1), p.length), Lo = refRma(l.slice(1), p.length); return [NaN, ...G.map((u, i) => 100 * u / (u + Lo[i]))]; }
  const tr = hourly.map((h, i) => i === 0 ? h.high - h.low : Math.max(h.high, hourly[i - 1].close) - Math.min(h.low, hourly[i - 1].close)); return [NaN, ...refRma(tr.slice(1), p.length)];
}
for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
  const code = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), path.join(dir, f), '--target', 'thinkscript'], { encoding: 'utf8' });
  files++;
  let stmts;
  try { stmts = parse(tokenize(code)); checks++; } catch (e) { fail(f, 'parse: ' + e.message); continue; }
  ok(/^# End BSV generated starter\.\s*$/m.test(code), f, 'end marker');
  ok(!/\bAddOrder\b/.test(code.replace(/#.*$/gm, '')), f, 'no AddOrder');
  const before = failures; statics(f, stmts, recipe);
  if (failures > before) continue; // do not evaluate code that failed the static checks
  const sink = { plots: [], alerts: [] };
  const env = evalTs(stmts, bars, sink);
  const zoneB = recipe.blocks.filter(b => b.type === 'visual.zone' && new RegExp(`^plot ZH\\d+ = V_${b.params?.source}_high;`, 'm').test(code));
  ok(sink.plots.length === recipe.blocks.filter(b => b.type === 'visual.plot').length + 2 * zoneB.length, f, 'one plot per visual.plot, two per rendered zone');
  zoneB.forEach((z, k) => { const n0 = sink.plots.length - 2 * zoneB.length + 2 * k, hv = env.get(`v_${z.params.source}_high`), lv = env.get(`v_${z.params.source}_low`);
    const z15 = evalTs(stmts, bars15, { plots: [], alerts: [] }); ok(sink.plots[n0].v === hv && sink.plots[n0 + 1].v === lv && z15.get(`v_${z.params.source}_high`).some(Number.isFinite), f, `${z.id}: zone lines are the source high / low (not vacuous on the 15-minute bars)`); zonesSeen++; });
  recipe.blocks.filter(b => b.type === 'visual.zone' && !zoneB.includes(b)).forEach(b => ok(code.includes(`# TODO unsupported block visual.zone: ${b.id}`), f, `${b.id}: zone left as TODO`));
  ok(sink.alerts.length === recipe.blocks.filter(b => b.type === 'alert.condition').length, f, 'one Alert per alert.condition');
  for (const b of recipe.blocks) {
    const v = env.get(('V_' + b.id).toLowerCase()), p = b.params || {}, x = pxOf[p.source || 'close'];
    if (p.timeframeRef) { const arr = Array.isArray(v) ? v : [v]; ok(v !== undefined && arr.every(x => !Number.isFinite(x)), f, `${b.id}: higher-timeframe value stays NaN when the chart (hourly here) is not shorter than the higher timeframe`); continue; }
    let want = null;
    if (b.type === 'indicator.sma') want = refSma(x, p.length);
    if (b.type === 'indicator.ema') want = refEma(x, p.length);
    if (b.type === 'indicator.rsi') { const g = x.map((w, i) => i ? Math.max(w - x[i - 1], 0) : 0), l = x.map((w, i) => i ? Math.max(x[i - 1] - w, 0) : 0), G = refRma(g.slice(1), p.length), Lo = refRma(l.slice(1), p.length); want = [NaN, ...G.map((u, i) => 100 * u / (u + Lo[i]))]; }
    if (b.type === 'indicator.atr') want = [NaN, ...refRma(TR.slice(1), p.length)];
    if (!want) continue;
    const from = b.type === 'indicator.sma' ? p.length : Math.min(NB - 1, 15 * p.length); // seeds differ only while warming up
    let worst = 0; for (let i = from; i < NB; i++) worst = Math.max(worst, Math.abs(v[i] - want[i]) / Math.max(1, Math.abs(want[i])));
    ok(v && worst < 1e-6, f, `${b.id} (${b.type}) matches reference from bar ${from}: worst ${worst}`);
  }
  // threshold / look-back / combine signals: recomputed here from the block's own inputs (independent of the generator's
  // expression), compared on every bar after the first 100; the look-back counts the previous bars only
  { const tb = (x) => !!x && !Number.isNaN(x), get = (r) => env.get(('S_' + r).toLowerCase()) || env.get(('V_' + r).toLowerCase()) || pxOf[r];
    for (const b of recipe.blocks.filter(b => /^signal\.(threshold|recent|combine)$/.test(b.type))) { const p = b.params || {}, v = env.get(('S_' + b.id).toLowerCase()); if (!v) continue; const want = [];
      for (let i = 0; i < NB; i++) {
        if (b.type === 'signal.threshold') { const a = get(p.left)[i], x = typeof p.right === 'string' && p.right ? get(p.right)[i] : Number(p.value); want.push(Number.isFinite(a) && Number.isFinite(x) && { '>': a > x, '>=': a >= x, '<': a < x, '<=': a <= x, '==': a === x, '!=': a !== x }[p.op || '>=']); }
        if (b.type === 'signal.recent') { const sg = get(p.signal); let h = false; for (let k = 1; k <= p.bars && i - k >= 0; k++) if (tb(sg[i - k])) h = true; want.push(h); }
        if (b.type === 'signal.combine') { const L = (p.signals || []).map(get); want.push(L.length > 0 && L.every(Boolean) && (p.mode === 'any' ? L.some(s => tb(s[i])) : L.every(s => tb(s[i])))); } }
      let bad = 0; for (let i = 100; i < NB; i++) if (tb(v[i]) !== want[i]) bad++;
      ok(bad === 0 && (b.type !== 'signal.recent' || want.some(Boolean)), f, `${b.id} (${b.type}) equals the recomputation from its inputs (${bad} differ)`); sigRecomputed++; }
    if (recipe.blocks.some(b => b.type === 'signal.recent')) for (const al of recipe.blocks.filter(b => b.type === 'alert.condition')) { const w = get(al.params.when) || []; let c = 0; for (let i = 0; i < NB; i++) if (tb(w[i])) c++; lookBackAlerts[f.replace('.json', '')] = c; ok(c > 0, f, `${al.id}: alert condition with a look-back holds on the test bars (${c} bars)`); } }
  // value panels (visual.table): one title label + one label per field the generator can show; the label text on the
  // last real bar carries the value of the bar that just closed ([1]). Expected fields are decided here independently.
  const tables = recipe.blocks.filter(b => b.type === 'visual.table');
  if (tables.length) {
    const by = Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
    const OKT = /^(indicator\.(ema|sma|rsi|atr)|signal\.(cross|threshold|combine|breakout)|filter\.session|structure\.range)$/;
    const deps = (b) => { const q = b.params || {}; return b.type === 'signal.cross' ? [q.left, q.right] : b.type === 'signal.threshold' ? [q.left, typeof q.right === 'string' ? q.right : null] : b.type === 'signal.recent' ? [q.signal] : b.type === 'signal.combine' ? (q.signals || []) : b.type === 'structure.range' ? [q.during] : b.type === 'signal.breakout' ? [q.range] : []; };
    const shown = (r, seen = new Set()) => { if (!by[r]) return !!pxOf[r]; if (seen.has(r)) return true; seen.add(r); const b = by[r]; if (!OKT.test(b.type) || ((b.params || {}).timeframeRef && !htfReadable(recipe, b))) return false; return deps(b).filter(Boolean).every(x => shown(x, seen)); };
    // a field built only from higher-timeframe values is shown without [1] (it is already the previous closed higher bar)
    const htfOnly = (r, seen = new Set()) => { const b = by[r]; if (!b) return false; if ((b.params || {}).timeframeRef) return true; if (seen.has(r)) return true; seen.add(r); const d = deps(b).filter(Boolean); return d.length > 0 && d.every(x => htfOnly(x, seen)); };
    const want = [], labels = (sink.labels || []).map(l => l.text[NB - 1]); let skipped = 0;
    for (const t of tables) { const fs2 = (t.params?.fields || []).filter(x => shown(x)); skipped += (t.params?.fields || []).length - fs2.length + (fs2.length ? 0 : 1); if (fs2.length) want.push([t.params?.title || t.id, fs2]); }
    const expect = [];
    for (const [title, fs2] of want) { expect.push(String(title)); for (const x0 of fs2) for (const x of by[x0].type === 'structure.range' ? by[x0].params.track.map(k => x0 + '_' + k) : [x0]) { const isB = /^(signal|filter)\./.test(by[x]?.type || ''); const v = env.get(((isB ? 'S_' : 'V_') + x).toLowerCase()); const at = v[htfOnly(x) ? NB - 1 : NB - 2]; expect.push(x + ': ' + (isB ? (at ? 'true' : 'false') : String(at))); } }
    ok(JSON.stringify(labels) === JSON.stringify(expect), f, `value panel labels ${JSON.stringify(labels)} expected ${JSON.stringify(expect)}`);
    for (const [, fs2] of want) for (const x of fs2) if (/^indicator\./.test(by[x]?.type || '')) { const lab = labels.find(l => l.startsWith(x + ': ')); const v = Number(lab.slice(x.length + 2)); const r = env.get(('V_' + x).toLowerCase())[htfOnly(x) ? NB - 1 : NB - 2]; ok(htfOnly(x) ? (!fin(v) && !fin(r)) : (fin(v) && Math.abs(v - r) < 1e-12 * Math.max(1, Math.abs(r))), f, `panel ${x} shows the closed bar's value (higher timeframe: empty on this hourly chart)`); }
    ok((code.match(/TODO [A-Za-z0-9_]+: visual\.table /g) || []).length === skipped && !/TODO unsupported block visual\.table/.test(code), f, `panel TODO lines (${skipped})`);
    panelsSeen += want.length;
  }
  // higher timeframe on 15-minute bars: previous closed hour = reference; prefix runs agree; the no-offset mutant is caught
  const htfB = recipe.blocks.filter(b => (b.params || {}).timeframeRef && htfReadable(recipe, b) && String(recipe.blocks.find(x => x.id === b.params.timeframeRef).params.timeframe) === '60');
  if (htfB.length) {
    const e15 = evalTs(stmts, bars15, { plots: [], alerts: [] });
    for (const b of htfB) {
      const v = e15.get(('V_' + b.id).toLowerCase()), R = hourlyRef(b), from = 4 * (15 * b.params.length + 2);
      let worst = 0, bad = 0; for (let i = 0; i < bars15.length; i++) { const h = Math.floor(i / 4), want = h >= 1 ? R[h - 1] : NaN; if (i >= from) worst = Math.max(worst, Math.abs(v[i] - want) / Math.max(1, Math.abs(want))); if (i < 4) bad += fin(v[i]) ? 1 : 0; }
      ok(worst < 1e-6 && bad === 0, f, `${b.id}: 15-minute chart value = previous closed hour of the reference (worst ${worst}, first hour non-empty ${bad})`);
      let diff = 0; for (let n = 3000; n <= 4000; n += 37) { const a = evalTs(stmts, bars15.slice(0, n), { plots: [], alerts: [] }).get(('V_' + b.id).toLowerCase())[n - 1], c = v[n - 1]; if (!(a === c || (Number.isNaN(a) && Number.isNaN(c)))) diff++; }
      ok(diff === 0, f, `${b.id}: prefix runs give the same last-bar value (no lookahead; ${diff} differ)`);
      htfChecked++;
    }
    const m = code.replace(/^def (H_\w+) = (E_\w+)\[1\];/gm, 'def $1 = $2;');
    if (m !== code) { const ms = parse(tokenize(m)); const sb = failures, cb = checks; QUIET = true; statics('mutant', ms, recipe); QUIET = false; checks = cb; const staticCaught = failures > sb; failures = sb; checks -= 0;
      const full = evalTs(ms, bars15, { plots: [], alerts: [] }); let caught = 0;
      for (const b of htfB) for (let n = 3001; n <= 3400; n++) { const a = evalTs(ms, bars15.slice(0, n), { plots: [], alerts: [] }).get(('V_' + b.id).toLowerCase())[n - 1], c = full.get(('V_' + b.id).toLowerCase())[n - 1]; if (a !== c) { caught++; break; } }
      ok(caught === htfB.length && staticCaught, f, `no-offset mutant caught by the prefix test (${caught}/${htfB.length}) and by the static closed-bar rule (${staticCaught})`); }
  }
  // ranges and breakouts (structure.range / signal.breakout) on the 15-minute bars: an independent window reference written
  // here from the recipe's session (bar times read in EST, as the evaluator's SecondsFromTime does), every bar compared,
  // breakouts must fire (not vacuous), prefix runs agree (no lookahead), and two mutants must be caught
  const byId = Object.fromEntries(recipe.blocks.map(b => [b.id, b])), same = (a, b) => a === b || (Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-9, tr = (v) => !!(v && !Number.isNaN(v));
  const rngB = recipe.blocks.filter(b => b.type === 'structure.range' && new RegExp(`^def R_${b.id} = `, 'm').test(code));
  if (rngB.length) {
    const by = byId, e15 = evalTs(stmts, bars15, { plots: [], alerts: [] });
    const inside = (sb) => { const q = sb.params || {}, [a, z] = String(q.session || '0000-2359').split('-').map(x => +x.slice(0, 2) * 60 + +x.slice(2, 4)); return bars15.map(b => { const d = new Date(b.time + EST), m = d.getUTCHours() * 60 + d.getUTCMinutes(); return a <= z ? m >= a && m < z : m >= a || m < z; }); };
    const refRange = (rb) => { const R = inside(by[rb.params.during]), H = [], Lo = []; let h = NaN, l = NaN;
      bars15.forEach((b, i) => { if (R[i]) { const fresh = i === 0 || !R[i - 1]; h = fresh ? b.high : Math.max(h, b.high); l = fresh ? b.low : Math.min(l, b.low); } H.push(h); Lo.push(l); }); return { R, H, Lo }; };
    const bos = recipe.blocks.filter(x => x.type === 'signal.breakout' && rngB.some(r => r.id === x.params?.range));
    const bad = (env) => { let n = 0; for (const rb of rngB) { const q = refRange(rb); for (const k of (rb.params.track || [])) { const v = env.get(`v_${rb.id}_${k}`.toLowerCase()), w = k === 'high' ? q.H : q.Lo; for (let i = 0; i < bars15.length; i++) if (!same(v[i], w[i])) n++; } }
      for (const bb of bos) { const q = refRange(by[bb.params.range]), d = bb.params.direction || 'either', v = env.get(`s_${bb.id}`.toLowerCase());
        for (let i = 0; i < bars15.length; i++) { const c = bars15[i].close, pc = i ? bars15[i - 1].close : NaN, okb = !q.R[i] && Number.isFinite(q.H[i]) && i > 0;
          const up = okb && c > q.H[i] && pc <= q.H[i], dn = okb && c < q.Lo[i] && pc >= q.Lo[i], want = d === 'either' ? up || dn : d === 'above' ? up : dn; if (tr(v[i]) !== want) n++; } }
      return n; };
    for (const rb of rngB) ok(refRange(rb).H.some(Number.isFinite), f, `${rb.id}: the 15-minute bars have windows (not vacuous)`);
    ok(bad(e15) === 0, f, `range / breakout values equal the reference on every 15-minute bar (${bad(e15)} differ)`);
    rangeChecked += rngB.length;
    for (const bb of bos) { const n = e15.get(`s_${bb.id}`.toLowerCase()).filter(tr).length; ok(n > 0, f, `${bb.id}: breakouts fire on the 15-minute bars (${n})`); breakoutsSeen += n; }
    let pd = 0; for (let n = 1200; n <= 4000; n += 151) { const ep = evalTs(stmts, bars15.slice(0, n), { plots: [], alerts: [] }); for (const rb of rngB) for (const k of rb.params.track) if (!same(ep.get(`v_${rb.id}_${k}`.toLowerCase())[n - 1], e15.get(`v_${rb.id}_${k}`.toLowerCase())[n - 1])) pd++; for (const bb of bos) if (tr(ep.get(`s_${bb.id}`.toLowerCase())[n - 1]) !== tr(e15.get(`s_${bb.id}`.toLowerCase())[n - 1])) pd++; }
    ok(pd === 0, f, `range prefix runs give the same last-bar value (no lookahead; ${pd} differ)`);
    for (const [mn, from, to] of [['window never resets', /if W_\w+ then (high|low) else /g, ''], ['breakout without the close before', / and close\[1\] <= V_\w+_high;/, ';']]) {
      if (mn.startsWith('breakout') && !bos.length) continue;
      const mc = code.replace(from, to); if (mc === code) { ok(false, f, `mutant could not be built: ${mn}`); continue; }
      const caught = bad(evalTs(parse(tokenize(mc)), bars15, { plots: [], alerts: [] })) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++;
    }
  }
  // pivots, sweeps and divergences on the 15-minute bars: an independent bar-by-bar reference (pivot confirmed `right` bars later,
  // strictly beyond the left bars, at least as far as the right ones; last pivot held); sweep and divergence use the evaluator's
  // ATR / oscillator (checked against their own reference above) and are compared after warm-up; mutants must be caught
  const pivB = recipe.blocks.filter(b => b.type === 'structure.pivot' && new RegExp(`^def P_${b.id}_h = `, 'm').test(code));
  if (pivB.length) {
    const by = byId, N15 = bars15.length, px15 = (k) => bars15.map(b => b[k]);
    const refPiv = (pb) => { const q = pb.params, [hk, lk] = (q.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], H = px15(hk), Lo = px15(lk), out = { h: [], l: [], ph: [], pl: [], H, Lo };
      let vh = NaN, vl = NaN; for (let i = 0; i < N15; i++) { const j = i - q.right; let up = false, dn = false;
        if (j - q.left >= 0) { up = true; dn = true; for (let n = j - q.left; n <= i; n++) { if (n === j) continue; if (n < j ? !(H[j] > H[n]) : !(H[j] >= H[n])) up = false; if (n < j ? !(Lo[j] < Lo[n]) : !(Lo[j] <= Lo[n])) dn = false; } }
        if (up) { vh = H[j]; out.ph.push(j); } if (dn) { vl = Lo[j]; out.pl.push(j); } out.h.push(vh); out.l.push(vl); } return out; };
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
    const e15 = evalTs(stmts, bars15, { plots: [], alerts: [] });
    ok(bad(e15) === 0, f, `pivot / sweep / divergence values equal the reference on the 15-minute bars (${bad(e15)} differ)`);
    for (const pb of pivB) ok(refPiv(pb).ph.length > 0 && refPiv(pb).pl.length > 0, f, `${pb.id}: pivots occur on the 15-minute bars (not vacuous)`);
    for (const sb of sigB) { const c = e15.get(`s_${sb.id}`).slice(400).filter(tr).length; ok(c > 0, f, `${sb.id}: fires on the 15-minute bars (${c}; not vacuous)`); pivSigSeen += c; }
    let pd = 0; for (let n = 1200; n <= 4000; n += 151) { const ep = evalTs(stmts, bars15.slice(0, n), { plots: [], alerts: [] }); for (const pb of pivB) for (const k of ['high', 'low']) if (!same(ep.get(`v_${pb.id}_${k}`)[n - 1], e15.get(`v_${pb.id}_${k}`)[n - 1])) pd++; for (const sb of sigB) if (tr(ep.get(`s_${sb.id}`)[n - 1]) !== tr(e15.get(`s_${sb.id}`)[n - 1])) pd++; }
    ok(pd === 0, f, `pivot prefix runs give the same last-bar values (no lookahead; ${pd} differ)`);
    for (const [mn, from, to, need] of [['pivot without the right-side test', / and (\w+)\[(\d+)\] >= Highest\(\1, \2\);/, ';', null], ['sweep without the close back inside', / and close < V_\w+_high\[1\]\)/, ')', 'signal.liquidity_sweep'], ['divergence oscillator test flipped', / < OH_(\w+)\[1\];/, ' > OH_$1[1];', 'signal.divergence']]) {
      if (need && !sigB.some(b => b.type === need)) continue;
      const mc = code.replace(from, to); if (mc === code) { ok(false, f, `mutant could not be built: ${mn}`); continue; }
      const caught = bad(evalTs(parse(tokenize(mc)), bars15, { plots: [], alerts: [] })) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++;
    }
  }
  // a self reference outside the documented CompoundValue form must fail the static check (the evaluator never guesses)
  if (/CompoundValue\(1, if P_\w+_h then/.test(code)) { const mc = code.replace(/def (V_\w+_high) = CompoundValue\(1, (if P_\w+_h then [^,]+ else \1\[1\]), Double\.NaN\);/, 'def $1 = $2;');
    const sb = failures, cb = checks; QUIET = true; statics('mutant', parse(tokenize(mc)), recipe); QUIET = false; const caught = failures > sb; failures = sb; checks = cb;
    ok(mc !== code && caught, f, 'a bare self reference (no CompoundValue) is rejected by the static check'); if (caught) mutantsCaught++; }
  // replay: the last 100 bars arrive one by one; Alert() reads its condition at the last real bar (still forming); Alert.BAR = once per bar.
  sink.alerts.forEach((a, k) => {
    const fired = []; let forming = 0;
    for (let n = R0; n <= NB; n++) {
      const live = bars.slice(0, n), s2 = { plots: [], alerts: [] }; evalTs(stmts, live, s2);
      const now = s2.alerts[k].cond[n - 1];
      // the forming bar must not change the decision: move its prices and evaluate again
      const moved = live.map((b, i) => i === n - 1 ? { ...b, open: b.open + 7, high: b.high + 9, low: b.low - 9, close: b.close - 8 } : b), s3 = { plots: [], alerts: [] }; evalTs(stmts, moved, s3);
      if (!!s3.alerts[k].cond[n - 1] !== !!now) forming++;
      if (now && fin(now)) fired.push(n - 2); // the bar that just closed
    }
    const full = a.cond, expect = []; for (let i = R0 - 2; i < NB - 1; i++) if (full[i + 1]) expect.push(i); // full-history value one bar later = closed bar i
    alertsSeen += fired.length;
    ok(forming === 0, f, `alert ${k}: depends on the forming bar (${forming})`);
    ok(new Set(fired).size === fired.length, f, `alert ${k}: more than once per bar`);
    ok(JSON.stringify(fired) === JSON.stringify(expect), f, `alert ${k}: fired ${fired} expected ${expect}`);
  });
}
console.log(JSON.stringify({ target: 'thinkscript', recipes: files, checks, failures, replay_alerts: alertsSeen, panels: panelsSeen, htf_values: htfChecked, ranges: rangeChecked, breakouts_15m: breakoutsSeen, zones: zonesSeen, sweep_divergence_15m: pivSigSeen, mutants_caught: mutantsCaught, signals_recomputed: sigRecomputed, look_back_alert_bars: lookBackAlerts, note: 'BSV thinkScript-subset parser/evaluator, not thinkorswim' }));
process.exit(failures ? 1 : 0);
