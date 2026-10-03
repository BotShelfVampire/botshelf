#!/usr/bin/env node
// Check of the generator's thinkorswim thinkScript output for every recipe, with a small BSV-written
// thinkScript-subset parser and array evaluator. NOT thinkorswim: it only covers the statements BSV generates
// and follows the thinkScript reference on tlc.thinkorswim.com (ExpAverage, Average, WildersAverage, Max,
// TrueRange, SecondsFromTime, SecondsTillTime, Alert, plot, declare lower, if/then/else, [n] past offsets).
// Checks: every statement parses and ends with ';', only these documented functions/constants are used,
// names are defined before use, offsets only look back, no AddOrder, declare lower iff not overlay,
// indicator values match an independent JS reference once warmed up, and a bar-by-bar replay shows
// alerts only for closed bars (the forming bar cannot change them), once per bar, with no misses.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
const FN = { expaverage: [2, 2], average: [2, 2], wildersaverage: [2, 2], max: [2, 2], truerange: [3, 3], secondsfromtime: [1, 1], secondstilltime: [1, 1], alert: [2, 4], addlabel: [2, 6] };
const CONST = new Set(['open', 'high', 'low', 'close', 'yes', 'no']);
const DOTTED = { color: new Set(['BLACK', 'BLUE', 'CYAN', 'DARK_GRAY', 'DARK_GREEN', 'DARK_ORANGE', 'DARK_RED', 'GRAY', 'GREEN', 'LIGHT_GRAY', 'LIGHT_GREEN', 'LIGHT_ORANGE', 'LIGHT_RED', 'LIME', 'MAGENTA', 'ORANGE', 'PINK', 'PLUM', 'RED', 'VIOLET', 'WHITE', 'YELLOW']),
  alert: new Set(['BAR', 'ONCE', 'TICK']), sound: new Set(['NoSound', 'Bell', 'Ding', 'Ring', 'Chimes']), double: new Set(['NaN']) };
const KW = new Set(['def', 'plot', 'declare', 'if', 'then', 'else', 'and', 'or']);
let checks = 0, failures = 0, files = 0;
const fail = (f, m) => { failures++; console.error('FAIL', f, m); };
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
      if (isOp('(')) { next(); const args = []; if (!isOp(')')) { args.push(ifE()); while (isOp(',')) { next(); args.push(ifE()); } } expect(')'); return { t: 'call', f: x.v, args }; }
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

function statics(f, stmts, recipe) {
  const defined = new Set(), plots = new Set();
  const walk = (e) => {
    if (!e) return;
    if (e.t === 'id') {
      const k = e.v.toLowerCase(), dot = e.v.split('.');
      if (dot.length === 2) ok(DOTTED[dot[0].toLowerCase()] && DOTTED[dot[0].toLowerCase()].has(dot[1]), f, `undocumented constant ${e.v}`);
      else ok(defined.has(k) || CONST.has(k), f, `undefined name ${e.v}`);
      if (e.off) ok(e.offOk, f, `offset [${e.off}] must look back (positive integer)`);
    }
    if (e.t === 'call') { const s = FN[e.f.toLowerCase()]; ok(!!s, f, `undocumented function ${e.f}`); if (s) ok(e.args.length >= s[0] && e.args.length <= s[1], f, `${e.f} arg count ${e.args.length}`); e.args.forEach(walk); }
    if (e.t === 'bin') { walk(e.l); walk(e.r); }
    if (e.t === 'neg') walk(e.e);
    if (e.t === 'if') { walk(e.c); walk(e.a); walk(e.b); }
  };
  const declares = stmts.filter(s => s.t === 'declare');
  ok(declares.length === (recipe.overlay ? 0 : 1) && declares.every(d => d.v === 'lower'), f, 'declare lower only for separate-pane recipes');
  for (const s of stmts) {
    if (s.e) walk(s.e);
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
function evalTs(stmts, bars, sink) {
  const n = bars.length, env = new Map(), arr = (v) => Array.isArray(v) ? v : N(n, v);
  const price = { open: bars.map(b => b.open), high: bars.map(b => b.high), low: bars.map(b => b.low), close: bars.map(b => b.close) };
  const shift = (x, k) => x.map((_, i) => i - k >= 0 ? x[i - k] : NaN);
  const ev = (e) => {
    switch (e.t) {
      case 'num': return e.v; case 'str': return e.v;
      case 'id': {
        const k = e.v.toLowerCase(); let v;
        if (env.has(k)) v = env.get(k); else if (price[k]) v = price[k]; else if (k === 'yes') v = 1; else if (k === 'no') v = 0; else if (k === 'double.nan') v = NaN; else return e.v;
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
        const f = e.f.toLowerCase(), A = e.args.map(ev);
        if (f === 'expaverage') return expA(arr(A[0]), A[1]); if (f === 'average') return avgA(arr(A[0]), A[1]); if (f === 'wildersaverage') return wildA(arr(A[0]), A[1]);
        if (f === 'max') { const a = arr(A[0]), b = arr(A[1]); return a.map((v, i) => (fin(v) && fin(b[i])) ? Math.max(v, b[i]) : NaN); }
        if (f === 'truerange') { const h = arr(A[0]), c = arr(A[1]), l = arr(A[2]); return h.map((v, i) => i === 0 ? v - l[i] : Math.max(v, c[i - 1]) - Math.min(l[i], c[i - 1])); }
        if (f === 'secondsfromtime') return bars.map(b => secOfDay(b.time) - hhmmSec(A[0]));
        if (f === 'secondstilltime') return bars.map(b => hhmmSec(A[0]) - secOfDay(b.time));
        if (f === 'alert') { sink.alerts.push({ text: A[1], cond: arr(A[0]) }); return 0; }
        if (f === 'addlabel') { (sink.labels || (sink.labels = [])).push({ text: arr(A[1]) }); return 0; }
      }
    }
    throw new Error('cannot evaluate ' + e.t);
  };
  for (const s of stmts) {
    if (s.t === 'def' || s.t === 'plot') { const v = ev(s.e); env.set(s.n.toLowerCase(), v); if (s.t === 'plot') sink.plots.push({ name: s.n, v: arr(v) }); }
    else if (s.t === 'expr') ev(s.e);
  }
  return env;
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
let alertsSeen = 0, panelsSeen = 0;
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
  ok(sink.plots.length === recipe.blocks.filter(b => b.type === 'visual.plot').length, f, 'one plot per visual.plot');
  ok(sink.alerts.length === recipe.blocks.filter(b => b.type === 'alert.condition').length, f, 'one Alert per alert.condition');
  for (const b of recipe.blocks) {
    const v = env.get(('V_' + b.id).toLowerCase()), p = b.params || {}, x = pxOf[p.source || 'close'];
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
  // value panels (visual.table): one title label + one label per field the generator can show; the label text on the
  // last real bar carries the value of the bar that just closed ([1]). Expected fields are decided here independently.
  const tables = recipe.blocks.filter(b => b.type === 'visual.table');
  if (tables.length) {
    const by = Object.fromEntries(recipe.blocks.map(b => [b.id, b]));
    const OKT = /^(indicator\.(ema|sma|rsi|atr)|signal\.(cross|threshold|combine)|filter\.session)$/;
    const deps = (b) => { const q = b.params || {}; return b.type === 'signal.cross' ? [q.left, q.right] : b.type === 'signal.threshold' ? [q.left] : b.type === 'signal.combine' ? (q.signals || []) : []; };
    const shown = (r, seen = new Set()) => { if (!by[r]) return !!pxOf[r]; if (seen.has(r)) return true; seen.add(r); const b = by[r]; if (!OKT.test(b.type) || (b.params || {}).timeframeRef) return false; return deps(b).filter(Boolean).every(x => shown(x, seen)); };
    const want = [], labels = (sink.labels || []).map(l => l.text[NB - 1]); let skipped = 0;
    for (const t of tables) { const fs2 = (t.params?.fields || []).filter(x => shown(x)); skipped += (t.params?.fields || []).length - fs2.length + (fs2.length ? 0 : 1); if (fs2.length) want.push([t.params?.title || t.id, fs2]); }
    const expect = [];
    for (const [title, fs2] of want) { expect.push(String(title)); for (const x of fs2) { const isB = /^(signal|filter)\./.test(by[x]?.type || ''); const v = env.get(((isB ? 'S_' : 'V_') + x).toLowerCase()); const at = v[NB - 2]; expect.push(x + ': ' + (isB ? (at ? 'true' : 'false') : String(at))); } }
    ok(JSON.stringify(labels) === JSON.stringify(expect), f, `value panel labels ${JSON.stringify(labels)} expected ${JSON.stringify(expect)}`);
    for (const [, fs2] of want) for (const x of fs2) if (/^indicator\./.test(by[x].type)) { const lab = labels.find(l => l.startsWith(x + ': ')); const v = Number(lab.slice(x.length + 2)); const r = env.get(('V_' + x).toLowerCase())[NB - 2]; ok(fin(v) && Math.abs(v - r) < 1e-12 * Math.max(1, Math.abs(r)), f, `panel ${x} shows the closed bar's value`); }
    ok((code.match(/TODO [A-Za-z0-9_]+: visual\.table /g) || []).length === skipped && !/TODO unsupported block visual\.table/.test(code), f, `panel TODO lines (${skipped})`);
    panelsSeen += want.length;
  }
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
console.log(JSON.stringify({ target: 'thinkscript', recipes: files, checks, failures, replay_alerts: alertsSeen, panels: panelsSeen, note: 'BSV thinkScript-subset parser/evaluator, not thinkorswim' }));
process.exit(failures ? 1 : 0);
