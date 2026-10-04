#!/usr/bin/env node
// BSV Pine Script v6 SUBSET parser / evaluator for the generator's pine-v6 output (Issue #4). Not TradingView: a small
// BSV-written model of the documented functions the generator emits (Pine v6 reference manual, tradingview.com/pine-script-reference/v6),
// evaluated as series over synthetic bars. Checks: documented functions / constants only, names assigned before use, positive
// history offsets, request.security only with expr[1] + lookahead = barmerge.lookahead_on (the manual's non-repainting idiom),
// indicator values against an independent reference (after warm-up: seeds may differ), signals / sessions / plots / alerts
// against an independent recomputation, prefix runs (no lookahead), the higher timeframe = previous closed hour on 15-minute
// bars, the runtime.error guard on a too-coarse chart, and mutants that must be caught. UNTESTED_RUNTIME on TradingView.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
const FN = { 'ta.ema': [2, 2], 'ta.sma': [2, 2], 'ta.rsi': [2, 2], 'ta.atr': [1, 1], 'ta.crossover': [2, 2], 'ta.crossunder': [2, 2], time: [3, 3], na: [1, 1],
  'request.security': [3, 4], 'timeframe.in_seconds': [0, 1], 'runtime.error': [1, 1], plot: [1, 2], alertcondition: [1, 3], indicator: [1, 2],
  'ta.highest': [2, 2], 'ta.lowest': [2, 2], 'ta.barssince': [1, 1], 'ta.valuewhen': [3, 3] };
const NAMED = new Set(['title', 'message', 'overlay', 'lookahead', 'color']);
const CONSTS = new Set(['na', 'bar_index', 'color.red', 'color.green', 'open', 'high', 'low', 'close', 'hl2', 'hlc3', 'ohlc4', 'true', 'false', 'syminfo.tickerid', 'timeframe.period', 'barmerge.lookahead_on']);
const KW = new Set(['and', 'or', 'not', 'if', 'else', 'for', 'while', 'var', 'varip', 'import', 'export', 'switch', 'true', 'false', 'method', 'type', 'continue', 'break', 'in', 'to', 'by', 'enum']);
let checks = 0, failures = 0, files = 0, QUIET = false;
const fail = (f, m) => { failures++; if (!QUIET) console.error('FAIL', f, m); };
const ok = (c, f, m) => { checks++; if (!c) fail(f, m); };

function stripComment(line) { let s = false; for (let i = 0; i < line.length; i++) { if (line[i] === '"' && line[i - 1] !== '\\') s = !s; if (!s && line[i] === '/' && line[i + 1] === '/') return line.slice(0, i); } return line; }
function tokenize(src) {
  const t = []; let i = 0;
  while (i < src.length) {
    const c = src[i]; let m;
    if (/\s/.test(c)) { i++; continue; }
    if (c === '"') { let e = i + 1; while (e < src.length && (src[e] !== '"' || src[e - 1] === '\\')) e++; if (e >= src.length) throw new Error('unclosed string'); t.push({ k: 'str', v: src.slice(i + 1, e).replace(/\\"/g, '"') }); i = e + 1; continue; }
    if ((m = /^\d+(\.\d+)?/.exec(src.slice(i)))) { t.push({ k: 'num', v: Number(m[0]) }); i += m[0].length; continue; }
    if ((m = /^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*/.exec(src.slice(i)))) { t.push({ k: 'id', v: m[0] }); i += m[0].length; continue; }
    if ((m = /^(:=|==|!=|>=|<=|[-+*\/()<>=,\[\]?:])/.exec(src.slice(i)))) { t.push({ k: 'op', v: m[0] }); i += m[0].length; continue; }
    throw new Error(`unexpected character ${JSON.stringify(c)}`);
  }
  return t;
}
function parseExpr(tokens) {
  let i = 0; const peek = () => tokens[i], next = () => tokens[i++];
  const isOp = (v) => peek() && peek().k === 'op' && peek().v === v, isKw = (v) => peek() && peek().k === 'id' && peek().v === v;
  const expect = (v) => { const x = next(); if (!x || x.v !== v) throw new Error(`expected ${v}, got ${x ? x.v : 'end'}`); };
  const post = (e) => { while (isOp('[')) { next(); const n = next(); if (!n || n.k !== 'num') throw new Error('offset must be a number'); expect(']'); e = { t: 'off', e, n: n.v }; } return e; };
  const primary = () => {
    const x = next(); if (!x) throw new Error('unexpected end');
    if (x.k === 'num') return post({ t: 'num', v: x.v });
    if (x.k === 'str') return { t: 'str', v: x.v };
    if (x.k === 'op' && x.v === '(') { const e = tern(); expect(')'); return post(e); }
    if (x.k === 'op' && x.v === '-') return { t: 'neg', e: primary() };
    if (x.k === 'id') {
      if (x.v === 'not') return { t: 'not', e: cmp() };
      if (KW.has(x.v) && x.v !== 'true' && x.v !== 'false') throw new Error(`unexpected keyword ${x.v}`);
      if (isOp('(')) { next(); const args = []; const arg = () => (peek() && peek().k === 'id' && tokens[i + 1] && tokens[i + 1].v === '=') ? (() => { const n = next().v; next(); return { t: 'named', n, e: tern() }; })() : tern();
        if (!isOp(')')) { args.push(arg()); while (isOp(',')) { next(); args.push(arg()); } } expect(')'); return post({ t: 'call', f: x.v, args }); }
      return post({ t: 'id', v: x.v });
    }
    throw new Error(`unexpected ${x.v}`);
  };
  const bin = (sub, ops, kw) => () => { let l = sub(); for (;;) { const o = kw ? ops.find(isKw) : ops.find(isOp); if (!o) return l; next(); l = { t: 'bin', o, l, r: sub() }; } };
  const mul = bin(primary, ['*', '/']), add = bin(mul, ['+', '-']), cmp = bin(add, ['==', '!=', '>=', '<=', '>', '<']);
  const andE = bin(cmp, ['and'], true), orE = bin(andE, ['or'], true);
  const tern = () => { const c = orE(); if (isOp('?')) { next(); const a = tern(); expect(':'); return { t: 'if', c, a, b: tern() }; } return c; };
  const e = tern(); if (i !== tokens.length) throw new Error(`trailing ${tokens[i].v}`); return e;
}
function parse(code) {
  const lines = code.split('\n'), stmts = []; let cur = stmts;
  if (lines[0] !== '//@version=6') throw new Error('first line must be //@version=6');
  for (const raw of lines) {
    const s = stripComment(raw); if (!s.trim()) continue;
    const ind = /^ */.exec(s)[0].length, body = s.trim();
    if (ind === 0) cur = stmts; else if (cur === stmts) throw new Error('indented line outside a block');
    let m;
    if (ind === 0 && (m = /^if (.+)$/.exec(body))) { const st = { t: 'if', c: parseExpr(tokenize(m[1])), body: [] }; stmts.push(st); cur = st.body; continue; }
    if ((m = /^(?:(float|bool) )?([A-Za-z_][A-Za-z0-9_]*) = (.+)$/.exec(body))) { cur.push({ t: 'def', n: m[2], ty: m[1] || null, e: parseExpr(tokenize(m[3])) }); continue; }
    if (/:=/.test(body)) throw new Error('reassignment (:=) is outside the BSV subset');
    cur.push({ t: 'expr', e: parseExpr(tokenize(body)) });
  }
  return stmts;
}
const walk = (e, fn) => { if (!e) return; fn(e); if (e.t === 'call') e.args.forEach(a => walk(a, fn)); else if (e.t === 'named' || e.t === 'neg' || e.t === 'not' || e.t === 'off') walk(e.e, fn); else if (e.t === 'bin') { walk(e.l, fn); walk(e.r, fn); } else if (e.t === 'if') { walk(e.c, fn); walk(e.a, fn); walk(e.b, fn); } };
function statics(f, stmts) {
  const defined = new Set(); let indicators = 0;
  const chk = (e) => walk(e, (x) => {
    if (x.t === 'id') ok(defined.has(x.v) || CONSTS.has(x.v), f, `undefined or undocumented name ${x.v}`);
    if (x.t === 'off') ok(Number.isInteger(x.n) && x.n >= 1, f, `offset [${x.n}] must look back`);
    if (x.t === 'named') ok(NAMED.has(x.n), f, `named argument ${x.n}`);
    if (x.t === 'call') { const s = FN[x.f]; ok(!!s, f, `undocumented function ${x.f}`); const pos = x.args.filter(a => a.t !== 'named').length; if (s) ok(pos >= s[0] && pos <= s[1], f, `${x.f} arg count ${pos}`);
      if (x.f === 'request.security') { const la = x.args.find(a => a.t === 'named' && a.n === 'lookahead'), ex = x.args[2];
        ok(x.args[0].t === 'id' && x.args[0].v === 'syminfo.tickerid' && x.args[1].t === 'str' && ex && ex.t === 'off' && ex.n === 1 && la && la.e.t === 'id' && la.e.v === 'barmerge.lookahead_on', f, 'request.security only as (syminfo.tickerid, tf, expr[1], lookahead = barmerge.lookahead_on): closed higher bars');
        walk(ex, y => { if (y.t === 'call') ok(y.f !== 'request.security', f, 'nested request.security'); }); }
      if (x.f === 'time') { const tz = x.args[2]; let good = tz && tz.t === 'str'; try { if (good) new Intl.DateTimeFormat('en-US', { timeZone: tz.v }); } catch { good = false; } ok(x.args[0].t === 'id' && x.args[0].v === 'timeframe.period' && x.args[1].t === 'str' && /^\d{4}-\d{4}$/.test(x.args[1].v) && good, f, 'time(timeframe.period, "HHMM-HHMM", <valid IANA time zone>)'); }
      if (x.f === 'indicator') indicators++; }
  });
  for (const s of stmts) {
    if (s.t === 'def') { chk(s.e); if (s.e.t === 'id' && s.e.v === 'na') ok(s.ty === 'float', f, `${s.n} = na needs a declared type (float ${s.n} = na)`); ok(!defined.has(s.n) && !KW.has(s.n) && !CONSTS.has(s.n) && !FN[s.n], f, `redeclares or shadows ${s.n}`); defined.add(s.n); }
    else if (s.t === 'if') { chk(s.c); ok(s.body.length === 1 && s.body[0].t === 'expr' && s.body[0].e.t === 'call' && s.body[0].e.f === 'runtime.error', f, 'if blocks only guard with runtime.error'); s.body.forEach(b => chk(b.e)); }
    else { chk(s.e); ok(s.e.t === 'call' && ['indicator', 'plot', 'alertcondition'].includes(s.e.f), f, `bare expression statement ${s.e.f || s.e.t}`); }
  }
  ok(indicators === 1, f, 'exactly one indicator() declaration (no strategy, no orders)');
}
// --- evaluator (series as arrays; NaN = na) ---
const N = (n, v) => new Array(n).fill(v), fin = Number.isFinite;
const smaA = (x, p) => x.map((_, i) => { if (i < p - 1) return NaN; let s = 0; for (let j = i - p + 1; j <= i; j++) s += x[j]; return s / p; });
function rmaA(x, p) { const o = N(x.length, NaN); let r = NaN, k = 0, s = 0; for (let i = 0; i < x.length; i++) { if (!fin(x[i])) continue; if (!fin(r)) { s += x[i]; k++; if (k === p) { r = s / p; o[i] = r; } continue; } r = (x[i] + (p - 1) * r) / p; o[i] = r; } return o; } // ta.rma: first value = SMA(length)
function emaA(x, p) { const a = 2 / (p + 1), o = N(x.length, NaN); let e = NaN, k = 0, s = 0; for (let i = 0; i < x.length; i++) { if (!fin(x[i])) continue; if (!fin(e)) { s += x[i]; k++; if (k === p) { e = s / p; o[i] = e; } continue; } e = a * x[i] + (1 - a) * e; o[i] = e; } return o; } // seeded with SMA(length)
const tfMs = (s) => /^\d+$/.test(s) ? Number(s) * 60e3 : (/^(\d*)D$/.test(s) ? (Number(s.slice(0, -1)) || 1) * 86400e3 : NaN);
function compress(bars, ms) { const out = [], gidx = []; let key = null; bars.forEach(b => { const k = Math.floor(b.time / ms); if (k !== key) { key = k; out.push({ time: k * ms, open: b.open, high: b.high, low: b.low, close: b.close }); } else { const o = out[out.length - 1]; o.high = Math.max(o.high, b.high); o.low = Math.min(o.low, b.low); o.close = b.close; } gidx.push(out.length - 1); }); return { bars: out, gidx }; }
const minuteIn = (t, tz) => { const p = new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(t)); return +p.find(x => x.type === 'hour').value * 60 + +p.find(x => x.type === 'minute').value; };
class PineRuntimeError extends Error {}
function evalPine(stmts, bars, sink) {
  const env = new Map(), spacing = bars.length > 1 ? (bars[1].time - bars[0].time) / 1000 : NaN;
  const ctxOf = (bs) => ({ n: bs.length, bars: bs, px: { open: bs.map(b => b.open), high: bs.map(b => b.high), low: bs.map(b => b.low), close: bs.map(b => b.close) } });
  const top = ctxOf(bars);
  const run = (e, c, local) => {
    const n = c.n, arr = (v) => Array.isArray(v) ? v : N(n, v), r = (x) => run(x, c, local);
    switch (e.t) {
      case 'num': return e.v; case 'str': return e.v;
      case 'id': { const k = e.v, px = c.px;
        if (local && env.has(k)) throw new Error('chart variable inside request.security');
        if (env.has(k)) return env.get(k); if (px[k]) return px[k];
        if (k === 'hl2') return px.high.map((h, i) => (h + px.low[i]) / 2); if (k === 'hlc3') return px.high.map((h, i) => (h + px.low[i] + px.close[i]) / 3); if (k === 'ohlc4') return px.open.map((o, i) => (o + px.high[i] + px.low[i] + px.close[i]) / 4);
        if (k === 'true') return 1; if (k === 'false') return 0; if (k === 'na') return NaN; if (k === 'bar_index') return c.bars.map((_, i) => i); return k; }
      case 'off': { const x = arr(r(e.e)); return x.map((_, i) => i - e.n >= 0 ? x[i - e.n] : NaN); }
      case 'neg': return arr(r(e.e)).map(v => -v);
      case 'not': return arr(r(e.e)).map(v => fin(v) ? +!v : NaN);
      case 'if': { const cc = arr(r(e.c)), a = arr(r(e.a)), b = arr(r(e.b)); return cc.map((v, i) => fin(v) ? (v ? a[i] : b[i]) : NaN); }
      case 'bin': { const a = arr(r(e.l)), b = arr(r(e.r)), F = { '+': (x, y) => x + y, '-': (x, y) => x - y, '*': (x, y) => x * y, '/': (x, y) => x / y, '>': (x, y) => fin(x) && fin(y) ? +(x > y) : 0, '<': (x, y) => fin(x) && fin(y) ? +(x < y) : 0,
        '>=': (x, y) => fin(x) && fin(y) ? +(x >= y) : 0, '<=': (x, y) => fin(x) && fin(y) ? +(x <= y) : 0, '==': (x, y) => fin(x) && fin(y) ? +(x === y) : 0, '!=': (x, y) => fin(x) && fin(y) ? +(x !== y) : 0,
        and: (x, y) => +(!!x && !!y && fin(x) && fin(y)), or: (x, y) => +((!!x && fin(x)) || (!!y && fin(y))) }[e.o]; return a.map((v, i) => F(v, b[i])); }
      case 'call': {
        const f = e.f, pos = e.args.filter(a => a.t !== 'named');
        if (f === 'request.security') { const ms = tfMs(pos[1].v); if (!(ms > spacing * 1000)) throw new Error('higher timeframe not higher'); const g = compress(c.bars, ms), v = arr(run(pos[2], ctxOf(g.bars), true)); return g.gidx.map(j => v[j]); } // lookahead_on: the containing higher bar's value of expr[1] = previous closed higher bar
        if (f === 'timeframe.in_seconds') return pos.length ? tfMs(pos[0].v) / 1000 : spacing;
        const A = pos.map(r);
        if (f === 'ta.ema') return emaA(arr(A[0]), A[1]); if (f === 'ta.sma') return smaA(arr(A[0]), A[1]);
        if (f === 'ta.rsi') { const x = arr(A[0]), up = rmaA(x.map((v, i) => i ? Math.max(v - x[i - 1], 0) : NaN), A[1]), dn = rmaA(x.map((v, i) => i ? Math.max(x[i - 1] - v, 0) : NaN), A[1]); return up.map((u, i) => !fin(u) || !fin(dn[i]) ? NaN : dn[i] === 0 ? 100 : u === 0 ? 0 : 100 - 100 / (1 + u / dn[i])); }
        if (f === 'ta.atr') { const px = c.px, tr = px.high.map((h, i) => i === 0 ? h - px.low[i] : Math.max(h, px.close[i - 1]) - Math.min(px.low[i], px.close[i - 1])); return rmaA(tr, A[0]); } // ta.tr(true)
        if (f === 'ta.crossover' || f === 'ta.crossunder') { const a = arr(A[0]), b = arr(A[1]), up = f === 'ta.crossover'; return a.map((v, i) => i && fin(v) && fin(b[i]) && fin(a[i - 1]) && fin(b[i - 1]) ? +(up ? v > b[i] && a[i - 1] <= b[i - 1] : v < b[i] && a[i - 1] >= b[i - 1]) : 0); }
        if (f === 'time') { const [s0, s1] = A[1].split('-').map(x => +x.slice(0, 2) * 60 + +x.slice(2, 4)); return c.bars.map(b => { const m = minuteIn(b.time, A[2]); return (s0 <= s1 ? m >= s0 && m < s1 : m >= s0 || m < s1) ? b.time : NaN; }); }
        if (f === 'na') return arr(A[0]).map(v => +!fin(v));
        if (f === 'ta.highest' || f === 'ta.lowest') { const x = arr(A[0]), L = arr(A[1]), g = f === 'ta.highest' ? Math.max : Math.min; return x.map((_, i) => { const p = L[i]; if (!fin(p) || p < 1 || i - p + 1 < 0) return NaN; const w = x.slice(i - p + 1, i + 1); return w.every(fin) ? g(...w) : NaN; }); } // series length allowed (v6)
        if (f === 'ta.barssince') { const x = arr(A[0]); let last = -1; return x.map((v, i) => { if (v && fin(v)) last = i; return last < 0 ? NaN : i - last; }); }
        if (f === 'ta.valuewhen') { const cnd = arr(A[0]), src = arr(A[1]), occ = A[2], hits = []; return cnd.map((v, i) => { if (v && fin(v)) hits.push(i); const j = hits[hits.length - 1 - occ]; return j === undefined ? NaN : src[j]; }); }
        if (f === 'runtime.error') throw new PineRuntimeError(A[0]);
        if (f === 'plot') { sink.plots.push({ v: arr(A[0]) }); return 0; }
        if (f === 'alertcondition') { sink.alerts.push({ cond: arr(A[0]), message: (e.args.find(a => a.t === 'named' && a.n === 'message') || {}).e?.v }); return 0; }
        if (f === 'indicator') return 0;
      }
    }
    throw new Error('cannot evaluate ' + e.t);
  };
  for (const s of stmts) {
    if (s.t === 'def') env.set(s.n, run(s.e, top));
    else if (s.t === 'if') { const cnd = run(s.c, top); if ((Array.isArray(cnd) ? cnd : [cnd]).some(v => v && fin(v))) run(s.body[0].e, top); }
    else run(s.e, top);
  }
  return env;
}
// --- independent reference (standard formulas, mean-seeded) and synthetic bars (same as the AFL / thinkScript checks) ---
const refSma = (x, p) => x.map((_, i) => i < p - 1 ? NaN : x.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p);
function refEma(x, p) { const a = 2 / (p + 1); let e = NaN; return x.map((v, i) => { if (i === p - 1) e = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) e = a * v + (1 - a) * e; return i >= p - 1 ? e : NaN; }); }
function refRma(x, p) { let r = NaN; return x.map((v, i) => { if (i === p - 1) r = x.slice(0, p).reduce((s, w) => s + w, 0) / p; else if (i >= p) r = (r * (p - 1) + v) / p; return i >= p - 1 ? r : NaN; }); }
const mkBars = (n, ms, f) => { const out = []; let q = 100; const t0 = Date.UTC(2026, 0, 5); for (let i = 0; i < n; i++) { const o = q; q = f(i); out.push({ time: t0 + i * ms, open: o, high: Math.max(o, q) + 0.5 + 0.3 * Math.abs(Math.sin(i)), low: Math.min(o, q) - 0.5, close: q }); } return out; };
const bars60 = mkBars(1200, 3600e3, i => 100 + 10 * Math.sin(i / 15) + 3 * Math.sin(i * 1.7));
const bars15 = mkBars(4000, 900e3, i => 100 + 10 * Math.sin(i / 37) + 2 * Math.sin(i * 1.3));
const srcOf = (bs, s) => bs.map(b => s === 'hl2' ? (b.high + b.low) / 2 : s === 'hlc3' ? (b.high + b.low + b.close) / 3 : s === 'ohlc4' ? (b.open + b.high + b.low + b.close) / 4 : b[s || 'close']);
const refInd = (bs, b) => { const p = b.params || {}, x = srcOf(bs, p.source);
  if (b.type === 'indicator.sma') return refSma(x, p.length); if (b.type === 'indicator.ema') return refEma(x, p.length);
  if (b.type === 'indicator.rsi') { const G = refRma(x.slice(1).map((w, i) => Math.max(w - x[i], 0)), p.length), L = refRma(x.slice(1).map((w, i) => Math.max(x[i] - w, 0)), p.length); return [NaN, ...G.map((u, i) => 100 * u / (u + L[i]))]; }
  const tr = bs.map((h, i) => i === 0 ? h.high - h.low : Math.max(h.high, bs[i - 1].close) - Math.min(h.low, bs[i - 1].close)); return [NaN, ...refRma(tr.slice(1), p.length)]; };
const same = (a, b) => a === b || (Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-9, tr = (v) => !!(v && fin(v));
let todoLines = 0, indChecked = 0, sigChecked = 0, htfChecked = 0, mutantsCaught = 0, alertsSeen = 0, rangeChecked = 0, breakoutsSeen = 0, zonesSeen = 0, pivSigSeen = 0;
for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')), by = Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
  const code = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), path.join(dir, f), '--target', 'pine-v6'], { encoding: 'utf8' });
  files++; todoLines += (code.match(/TODO unsupported block /g) || []).length;
  let stmts; try { stmts = parse(code); checks++; } catch (e) { fail(f, 'parse: ' + e.message); continue; }
  const before = failures; statics(f, stmts); if (failures > before) continue;
  const htf = recipe.blocks.filter(b => b.params?.timeframeRef && new RegExp(`^${b.id} = request\\.security\\(`, 'm').test(code));
  // a recipe with a 60-minute higher timeframe stops with runtime.error on an hourly chart and runs on 15-minute bars
  if (htf.length) { let stopped = false; try { evalPine(stmts, bars60, { plots: [], alerts: [] }); } catch (e) { stopped = e instanceof PineRuntimeError; } ok(stopped, f, 'runtime.error stops the script when the chart is not lower than the higher timeframe'); }
  const bs = htf.length || recipe.blocks.some(b => b.type === 'filter.session') ? bars15 : bars60, sink = { plots: [], alerts: [] };
  let env; try { env = evalPine(stmts, bs, sink); checks++; } catch (e) { fail(f, 'evaluate: ' + e.message); continue; }
  const hourly = compress(bars15, 3600e3).bars, gix = compress(bars15, 3600e3).gidx;
  for (const b of recipe.blocks) {
    const v = env.get(b.id), p = b.params || {};
    if (/^indicator\./.test(b.type)) {
      if (!v) { ok(code.includes(`// TODO unsupported block ${b.type}: ${b.id}`), f, `${b.id}: rendered or TODO`); continue; }
      if (htf.includes(b)) { const R = refInd(hourly, b), from = 4 * (15 * p.length + 2); let worst = 0, early = 0;
        for (let i = 0; i < bs.length; i++) { const h = gix[i], want = h >= 1 ? R[h - 1] : NaN; if (i >= from) worst = Math.max(worst, Math.abs(v[i] - want) / Math.max(1, Math.abs(want))); if (h === 0 && fin(v[i])) early++; }
        ok(worst < 1e-6 && early === 0, f, `${b.id}: 15-minute value = previous closed hour of the reference (worst ${worst}, first hour non-empty ${early})`); htfChecked++; continue; }
      const R = refInd(bs, b), from = b.type === 'indicator.sma' ? p.length : Math.min(bs.length - 1, 15 * p.length); let worst = 0;
      for (let i = from; i < bs.length; i++) worst = Math.max(worst, Math.abs(v[i] - R[i]) / Math.max(1, Math.abs(R[i])));
      ok(worst < 1e-6, f, `${b.id} (${b.type}) matches the reference from bar ${from}: worst ${worst}`); indChecked++;
    }
    if (/^(signal\.(cross|threshold|combine)|filter\.session)$/.test(b.type)) {
      const n = bs.length, g = (r) => env.get(r) || srcOf(bs, r), want = N(n, false);
      if (b.type === 'signal.cross') { const a = g(p.left), c = g(p.right); for (let i = 1; i < n; i++) want[i] = [a[i], c[i], a[i - 1], c[i - 1]].every(fin) && (p.direction === 'below' ? a[i] < c[i] && a[i - 1] >= c[i - 1] : a[i] > c[i] && a[i - 1] <= c[i - 1]); }
      if (b.type === 'signal.threshold') { const a = g(p.left), x = Number(p.value), op = ['>', '>=', '<', '<=', '==', '!='].includes(p.op) ? p.op : '>='; for (let i = 0; i < n; i++) want[i] = fin(a[i]) && { '>': a[i] > x, '>=': a[i] >= x, '<': a[i] < x, '<=': a[i] <= x, '==': a[i] === x, '!=': a[i] !== x }[op]; }
      if (b.type === 'signal.combine') { const S = (p.signals || []).map(r => env.get(r)); for (let i = 0; i < n; i++) want[i] = S.length > 0 && (p.mode === 'any' ? S.some(s => tr(s[i])) : S.every(s => tr(s[i]))); }
      if (b.type === 'filter.session') { const [s0, s1] = String(p.session || '0000-2359').split('-').map(x => +x.slice(0, 2) * 60 + +x.slice(2, 4)), tz = String(p.timezone || 'Etc/UTC');
        for (let i = 0; i < n; i++) { const d = new Date(bs[i].time).toLocaleString('en-US', { timeZone: tz, hour12: false, hour: 'numeric', minute: 'numeric' }).split(':').map(Number), m = (d[0] % 24) * 60 + d[1]; want[i] = s0 <= s1 ? m >= s0 && m < s1 : m >= s0 || m < s1; }
        ok(want.some(Boolean) && !want.every(Boolean), f, `${b.id}: the session is open on some bars and closed on others (not vacuous)`); }
      let bad = 0; for (let i = 0; i < n; i++) if (tr(v[i]) !== want[i]) bad++;
      ok(v && bad === 0, f, `${b.id} (${b.type}) equals the independent recomputation on every bar (${bad} differ)`); sigChecked++;
    }
  }
  for (const b of recipe.blocks.filter(b => code.includes(`// TODO unsupported block ${b.type}: ${b.id}\n`) && env.has(b.id))) ok(env.get(b.id) === 0 || Number.isNaN(env.get(b.id)), f, `${b.id}: TODO stub is never true / na`);
  const plotsB = recipe.blocks.filter(b => b.type === 'visual.plot'), alertsB = recipe.blocks.filter(b => b.type === 'alert.condition');
  const zoneB = recipe.blocks.filter(b => b.type === 'visual.zone' && code.includes(`plot(${b.params?.source}_high, `));
  ok(sink.plots.length === plotsB.length + 2 * zoneB.length, f, 'one plot per visual.plot, two per rendered zone');
  zoneB.forEach((z, k) => { const n0 = sink.plots.length - 2 * zoneB.length + 2 * k, hv = env.get(`${z.params.source}_high`), lv = env.get(`${z.params.source}_low`);
    ok(sink.plots[n0].v.every((x, i) => same(x, hv[i])) && sink.plots[n0 + 1].v.every((x, i) => same(x, lv[i])) && hv.some(fin), f, `${z.id}: zone lines are the source high / low (not vacuous)`); zonesSeen++; });
  recipe.blocks.filter(b => b.type === 'visual.zone' && !zoneB.includes(b)).forEach(b => ok(code.includes(`// TODO unsupported block visual.zone: ${b.id}`), f, `${b.id}: zone left as TODO`));
  // ranges / breakouts: an independent window reference from the recipe session (its own time zone), every bar compared
  const inside = (sb) => { const q = sb.params || {}, [a, z] = String(q.session || '0000-2359').split('-').map(x => +x.slice(0, 2) * 60 + +x.slice(2, 4)), tz = String(q.timezone || 'Etc/UTC'); return bs.map(b => { const d = new Date(b.time).toLocaleString('en-US', { timeZone: tz, hour12: false, hour: 'numeric', minute: 'numeric' }).split(':').map(Number), m = (d[0] % 24) * 60 + d[1]; return a <= z ? m >= a && m < z : m >= a || m < z; }); };
  const rngB = recipe.blocks.filter(b => b.type === 'structure.range' && new RegExp(`^${b.id}_in = `, 'm').test(code)), bos = recipe.blocks.filter(x => x.type === 'signal.breakout' && rngB.some(r => r.id === x.params?.range));
  const refRange = (rb) => { const R = inside(by[rb.params.during]), H = [], Lo = []; let h = NaN, l = NaN; bs.forEach((b, i) => { if (R[i]) { const fresh = i === 0 || !R[i - 1]; h = fresh ? b.high : Math.max(h, b.high); l = fresh ? b.low : Math.min(l, b.low); } H.push(h); Lo.push(l); }); return { R, H, Lo }; };
  const badR = (e) => { let n = 0; for (const rb of rngB) { const q = refRange(rb); for (const k of rb.params.track) { const v = e.get(`${rb.id}_${k}`), w = k === 'high' ? q.H : q.Lo; for (let i = 0; i < bs.length; i++) if (!same(v[i], w[i])) n++; } }
    for (const bb of bos) { const q = refRange(by[bb.params.range]), d = bb.params.direction || 'either', v = e.get(bb.id); for (let i = 0; i < bs.length; i++) { const c = bs[i].close, pc = i ? bs[i - 1].close : NaN, okb = !q.R[i] && fin(q.H[i]) && i > 0, up = okb && c > q.H[i] && pc <= q.H[i], dn = okb && c < q.Lo[i] && pc >= q.Lo[i]; if (tr(v[i]) !== (d === 'either' ? up || dn : d === 'above' ? up : dn)) n++; } }
    return n; };
  if (rngB.length) { for (const rb of rngB) ok(refRange(rb).H.some(fin), f, `${rb.id}: windows occur on the test bars (not vacuous)`); ok(badR(env) === 0, f, `range / breakout equal the reference on every bar (${badR(env)} differ)`); rangeChecked += rngB.length;
    for (const bb of bos) { const c = env.get(bb.id).filter(tr).length; ok(c > 0, f, `${bb.id}: breakouts fire (${c})`); breakoutsSeen += c; }
    for (const [mn, from, to, need] of [['window never resets', /ta\.barssince\(\w+_new\) \+ 1/g, 'bar_index + 1', 0], ['breakout without the close before', / and close\[1\] <= \w+_high$/m, '', 1]]) { if (need && !bos.length) continue;
      const mc = code.replace(from, to), caught = mc !== code && badR(evalPine(parse(mc), bs, { plots: [], alerts: [] })) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++; } }
  // pivots / sweeps / divergences: independent bar-by-bar pivot reference; sweep and divergence use the evaluator's ATR / oscillator (checked above) after warm-up
  const pivB = recipe.blocks.filter(b => b.type === 'structure.pivot' && new RegExp(`^${b.id}_ph = `, 'm').test(code)), sigB = recipe.blocks.filter(b => /^signal\.(liquidity_sweep|divergence)$/.test(b.type) && pivB.some(x => x.id === b.params?.pivot));
  const refPiv = (pb) => { const q = pb.params, [hk, lk] = (q.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], H = bs.map(b => b[hk]), Lo = bs.map(b => b[lk]), out = { h: [], l: [], ph: [], pl: [], H, Lo }; let vh = NaN, vl = NaN;
    for (let i = 0; i < bs.length; i++) { const j = i - q.right; let up = false, dn = false; if (j - q.left >= 0) { up = true; dn = true; for (let n = j - q.left; n <= i; n++) { if (n === j) continue; if (n < j ? !(H[j] > H[n]) : !(H[j] >= H[n])) up = false; if (n < j ? !(Lo[j] < Lo[n]) : !(Lo[j] <= Lo[n])) dn = false; } }
      if (up) { vh = H[j]; out.ph.push(j); } if (dn) { vl = Lo[j]; out.pl.push(j); } out.h.push(vh); out.l.push(vl); } return out; };
  const badP = (e) => { let n = 0; for (const pb of pivB) { const q = refPiv(pb); for (let i = 0; i < bs.length; i++) { if (!same(e.get(`${pb.id}_high`)[i], q.h[i])) n++; if (!same(e.get(`${pb.id}_low`)[i], q.l[i])) n++; } }
    for (const sb of sigB) { const pb = by[sb.params.pivot], q = refPiv(pb), v = e.get(sb.id), from = 400;
      if (sb.type === 'signal.liquidity_sweep') { const A = e.get(sb.params.atr), fr = Number(sb.params.minAtrFraction || 0); for (let i = from; i < bs.length; i++) { const b = bs[i], ph = q.h[i - 1], pl = q.l[i - 1], w = fin(A[i]) && ((fin(ph) && b.high > ph && b.high - ph >= fr * A[i] && b.close < ph) || (fin(pl) && b.low < pl && pl - b.low >= fr * A[i] && b.close > pl)); if (tr(v[i]) !== w) n++; } }
      else { const O = e.get(sb.params.oscillator), d = sb.params.direction || 'both', w = N(bs.length, false), R = pb.params.right;
        if (d !== 'bullish') for (let k = 1; k < q.ph.length; k++) { const a = q.ph[k - 1], j = q.ph[k]; if (q.H[j] > q.H[a] && O[j] < O[a]) w[j + R] = true; }
        if (d !== 'bearish') for (let k = 1; k < q.pl.length; k++) { const a = q.pl[k - 1], j = q.pl[k]; if (q.Lo[j] < q.Lo[a] && O[j] > O[a]) w[j + R] = true; }
        for (let i = from; i < bs.length; i++) if (tr(v[i]) !== w[i]) n++; } }
    return n; };
  if (pivB.length) { ok(badP(env) === 0, f, `pivot / sweep / divergence equal the reference (${badP(env)} differ)`); for (const pb of pivB) ok(refPiv(pb).ph.length > 0 && refPiv(pb).pl.length > 0, f, `${pb.id}: pivots occur (not vacuous)`);
    for (const sb of sigB) { const c = env.get(sb.id).slice(400).filter(tr).length; ok(c > 0, f, `${sb.id}: fires (${c}; not vacuous)`); pivSigSeen += c; }
    for (const [mn, from, to, need] of [['pivot without the right-side test', / and (\w+)\[(\d+)\] >= ta\.highest\(\1, \2\)$/m, '', null], ['sweep without the close back inside', / and close < \w+_high\[1\]\)/, ')', 'signal.liquidity_sweep'], ['divergence oscillator test flipped', /\] < ta\.valuewhen\((\w+)_ph, (\w+)\[(\d+)\], 1\)/, '] > ta.valuewhen($1_ph, $2[$3], 1)', 'signal.divergence']]) {
      if (need && !sigB.some(b => b.type === need)) continue; const mc = code.replace(from, to), caught = mc !== code && badP(evalPine(parse(mc), bs, { plots: [], alerts: [] })) > 0; ok(caught, f, `mutant caught: ${mn}`); if (caught) mutantsCaught++; } }
  ok(sink.plots.length >= plotsB.length && plotsB.every((b, k) => sink.plots[k].v.every((x, i) => same(x, (env.get(b.params.source) || srcOf(bs, b.params.source))[i]))), f, 'one plot per visual.plot, plotting its source');
  ok(sink.alerts.length === alertsB.length && alertsB.every((b, k) => sink.alerts[k].cond.every((x, i) => tr(x) === tr(env.get(b.params.when)[i])) && sink.alerts[k].message === (b.params.message || b.id)), f, 'one alertcondition per alert.condition, on its signal, with its message');
  sink.alerts.forEach(a => { alertsSeen += a.cond.filter(tr).length; });
  // prefix runs: every variable's last value equals the full run (nothing reads future bars)
  let pd = 0; for (let n = 1000; n <= bs.length; n += 97) { const ep = evalPine(stmts, bs.slice(0, n), { plots: [], alerts: [] }); for (const [k, v] of env) if (Array.isArray(v) && !same(ep.get(k)[n - 1], v[n - 1])) pd++; }
  ok(pd === 0, f, `prefix runs give the same last-bar values (no lookahead; ${pd} differ)`);
  // mutants: the shift-0 higher timeframe (repaints / looks ahead) must fail the static rule AND the prefix test; a flipped cross must be caught
  if (htf.length) { const mc = code.replace(/(request\.security\(syminfo\.tickerid, "[^"]+", .+)\[1\](, lookahead = barmerge\.lookahead_on\))/, '$1$2'), ms = parse(mc);
    const fb = failures, cb = checks; QUIET = true; statics('mutant', ms); QUIET = false; const st = failures > fb; failures = fb; checks = cb;
    const full = evalPine(ms, bars15, { plots: [], alerts: [] }); let caught = false; for (let n = 3001; n <= 3200 && !caught; n++) { const ep = evalPine(ms, bars15.slice(0, n), { plots: [], alerts: [] }); for (const b of htf) if (!same(ep.get(b.id)[n - 1], full.get(b.id)[n - 1])) caught = true; }
    ok(mc !== code && st && caught, f, `shift-0 higher-timeframe mutant caught by the static rule (${st}) and the prefix test (${caught})`); if (st && caught) mutantsCaught++; }
  const cx = recipe.blocks.find(b => b.type === 'signal.cross' && env.get(b.id) && env.get(b.id).some(tr));
  if (cx) { const mc = code.replace(new RegExp(`^${cx.id} = ta\\.cross(over|under)\\(`, 'm'), (m0, d) => `${cx.id} = ta.cross${d === 'over' ? 'under' : 'over'}(`), e2 = evalPine(parse(mc), bs, { plots: [], alerts: [] });
    const caught = mc !== code && e2.get(cx.id).some((x, i) => tr(x) !== tr(env.get(cx.id)[i])); ok(caught, f, `flipped-cross mutant caught (${cx.id})`); if (caught) mutantsCaught++; }
  else if (recipe.blocks.some(b => b.type === 'signal.cross' && env.get(b.id))) ok(false, f, 'crosses never fire on the test bars (vacuous)');
}
console.log(JSON.stringify({ target: 'pine-v6', recipes: files, checks, failures, indicators: indChecked, signals: sigChecked, htf_values: htfChecked, alert_bars: alertsSeen, ranges: rangeChecked, breakouts: breakoutsSeen, zones: zonesSeen, sweep_divergence: pivSigSeen, todo_lines: todoLines, mutants_caught: mutantsCaught, note: "BSV Pine-subset parser/evaluator, not TradingView" }));
process.exit(failures ? 1 : 0);
