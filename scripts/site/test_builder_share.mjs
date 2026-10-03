#!/usr/bin/env node
// Builder v2 checks: share links / JSON export carry only the user's block config (never generated code or
// gated BSV bodies), import is whitelisted, and per-block TODO hints map TODO lines to block ids.
// Usage: node scripts/site/test_builder_share.mjs <site tree>
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm';
const site = process.argv[2];
const js = fs.readdirSync(path.join(site, 'trading/sources')).filter(f => /^bsv-builder\.[0-9a-f]{8}\.js$/.test(f));
const ctx = { globalThis: {}, TextEncoder, TextDecoder, btoa, atob }; ctx.window = ctx; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(site, 'trading/sources', js[0]), 'utf8'), ctx);
const R = ctx.BSVRender, B = ctx.BSVBuilder; let n = 0, bad = 0;
const ok = (c, msg) => { n++; if (!c) { bad++; console.log('FAIL', msg); } };
const CODE = [/\/\/@version/, /#property/, /import bookmap/, /cAlgo/, /indicator\(/, /OnCalculate/, /TODO/];
// 1) unchanged starters are shared by name only
for (const r of R.recipes) { const p = B.sharePayload(JSON.parse(JSON.stringify(r))); ok(/^s=[a-z0-9-]+$/.test(p), 'starter by name: ' + r.name + ' -> ' + p.slice(0, 30)); ok(JSON.stringify(B.readPayload(p)) === JSON.stringify(r), 'starter roundtrip ' + r.name); }
// 2) modified recipe: config only, starter description dropped, no code, roundtrip == sanitized
for (const r of R.recipes) {
  const m = JSON.parse(JSON.stringify(r)); m.name = 'My ' + r.name; m.code = R.render(JSON.parse(JSON.stringify(r)), 'pine-v6'); m.blocks[0].body = 'SECRET'; m.blocks[0].params.evil = { nested: 1 };
  const p = B.sharePayload(m); ok(/^r=[A-Za-z0-9_-]+$/.test(p), 'custom payload form');
  const dec = B.b64d(p.slice(2)); ok(!CODE.some(re => re.test(dec)), 'no generated code in share: ' + r.name);
  ok(!/SECRET|evil|"code"|"body"/.test(dec), 'unknown keys dropped: ' + r.name);
  ok(!(r.description && dec.includes(JSON.stringify(r.description).slice(1, -1))), 'starter description not shared: ' + r.name);
  const back = B.readPayload(p); const want = B.sanitize(m).recipe; delete want.description;
  ok(JSON.stringify(back) === JSON.stringify(want), 'custom roundtrip ' + r.name);
  for (const t of ['pine-v6', 'mql5', 'ctrader', 'mql4', 'ctrader-python', 'bookmap-python', 'ninjatrader', 'quantower', 'sierra-acsil', 'prorealtime', 'gocharting-lipi', 'motivewave', 'vela', 'jforex']) ok(R.render(JSON.parse(JSON.stringify(back)), t).length > 0, 'shared recipe renders ' + t);
}
// 3) sanitizer rejects bad input
for (const [x, why] of [[[], 'array'], [{ blocks: 'x' }, 'blocks string'], [{ blocks: [{ id: 'Bad Id', type: 'indicator.ema', params: {} }] }, 'bad id'], [{ blocks: [{ id: 'a', type: 'evil.type', params: {} }] }, 'bad type'], [{ blocks: Array.from({ length: 41 }, (_, i) => ({ id: 'b' + i, type: 'indicator.ema', params: {} })) }, 'too many']]) {
  let threw = false; try { B.sanitize(x); } catch (e) { threw = true; } ok(threw, 'reject ' + why);
}
let big = false; try { B.sharePayload({ schemaVersion: '0.1', name: 'x', overlay: true, blocks: Array.from({ length: 40 }, (_, i) => ({ id: 'b' + i, type: 'alert.condition', params: { when: 'close', message: 'm'.repeat(200) } })) }); } catch (e) { big = true; } ok(big, 'oversized share rejected');
ok(B.sanitize({ __proto__: { x: 1 }, blocks: [] }).recipe.x === undefined, 'proto ignored');
// 4) TODO hints: every TODO line of every starter maps to a block id or is reported as general; counts add up
for (const r of R.recipes) for (const t of ['pine-v6', 'mql5', 'ctrader', 'mql4', 'ctrader-python', 'bookmap-python', 'ninjatrader', 'quantower', 'sierra-acsil', 'prorealtime', 'gocharting-lipi', 'motivewave', 'vela', 'jforex']) {
  const out = R.render(JSON.parse(JSON.stringify(r)), t); const tm = B.todoMap(out, r.blocks);
  const mapped = Object.values(tm.map).reduce((a, v) => a + v.length, 0);
  ok(mapped + tm.general.length === tm.total, 'todo count ' + r.name + ' ' + t);
  for (const id of Object.keys(tm.map)) ok(r.blocks.some(b => b.id === id), 'todo id exists ' + id);
}
{ const tm = B.todoMap('   // alert: TODO add deduplicated alert for divergence\n// TODO unsupported block structure.pivot: pivot\n# TODO session: bar times are UTC', [{ id: 'divergence' }, { id: 'alert' }, { id: 'pivot' }, { id: 'session' }]);
  ok(tm.map.alert && tm.map.alert.length === 1 && tm.map.pivot.length === 1 && tm.map.session.length === 1 && !tm.map.divergence, 'todo line owner by prefix'); }
for (const t of Object.keys(B.hints)) ok(B.hints[t].length === 2 && B.hints[t].every(s => s.length > 20), 'hint en/ja ' + t);
// 5) recipe lint + reorder + compile checklist
const T8 = ['pine-v6', 'mql5', 'ctrader', 'mql4', 'ctrader-python', 'bookmap-python', 'ninjatrader', 'quantower', 'sierra-acsil', 'prorealtime', 'gocharting-lipi', 'motivewave', 'vela', 'jforex'];
const lintSummary = {};
for (const r of R.recipes) { const L = B.lint(JSON.parse(JSON.stringify(r))); ok(!L.some(x => x.level === 'error' || x.code === 'forward-ref'), 'starter lint clean of errors/forward refs: ' + r.name); lintSummary[r.name] = L.map(x => x.code + ':' + x.id).join(','); }
const fwd = { schemaVersion: '0.1', name: 'fwd', overlay: true, blocks: [
  { id: 'x', type: 'signal.cross', params: { left: 'fast', right: 'slow', direction: 'above' } },
  { id: 'fast', type: 'indicator.ema', params: { source: 'close', length: 9 } },
  { id: 'slow', type: 'indicator.ema', params: { source: 'close', length: 21 } },
  { id: 'lonely', type: 'indicator.rsi', params: { source: 'close', length: 14 } },
  { id: 'a', type: 'alert.condition', params: { when: 'x', message: 'm' } },
  { id: 'a2', type: 'alert.condition', params: { when: 'fast', message: 'm' } }] };
const Lf = B.lint(fwd);
ok(Lf.filter(x => x.code === 'forward-ref').length === 2, 'forward refs flagged');
ok(Lf.some(x => x.code === 'unused' && x.id === 'lonely'), 'unused flagged');
ok(Lf.some(x => x.code === 'alert-value' && x.id === 'a2'), 'alert on value flagged');
ok(!Lf.some(x => x.code === 'unused' && (x.id === 'fast' || x.id === 'x')), 'used blocks not flagged');
const ro = B.reorder(fwd); ok(ro.cycle.length === 0, 'no cycle');
const fixed = Object.assign({}, fwd, { blocks: ro.blocks }); ok(!B.lint(fixed).some(x => x.code === 'forward-ref'), 'reorder removes forward refs');
ok(ro.blocks.map(b => b.id).join() === 'fast,slow,x,lonely,a,a2', 'reorder is stable: ' + ro.blocks.map(b => b.id).join());
for (const t of T8) ok(R.render(JSON.parse(JSON.stringify(fixed)), t).length > 0, 'reordered renders ' + t);
const cyc = { schemaVersion: '0.1', name: 'c', overlay: true, blocks: [{ id: 'p', type: 'signal.combine', params: { mode: 'all', signals: ['q', 'p'] } }, { id: 'q', type: 'signal.combine', params: { mode: 'all', signals: ['p'] } }] };
const Lc = B.lint(cyc); ok(Lc.some(x => x.code === 'self-ref') && Lc.some(x => x.code === 'cycle'), 'cycle/self-ref flagged');
ok(B.lint({ schemaVersion: '0.1', name: 'e', overlay: true, blocks: [] }).some(x => x.code === 'no-output'), 'no output flagged');
ok(B.lint({ schemaVersion: '0.1', name: 'r', overlay: true, blocks: [{ id: 'r', type: 'indicator.rsi', params: { source: 'close', length: 14 } }, { id: 't', type: 'signal.threshold', params: { left: 'r', op: '>', value: 150 } }, { id: 'pl', type: 'visual.plot', params: { source: 'r', title: 'RSI' } }, { id: 'al', type: 'alert.condition', params: { when: 't', message: 'm' } }] }).filter(x => ['rsi-range', 'scale'].includes(x.code)).length === 2, 'rsi range + overlay scale flagged');
for (const t of T8) ok(Array.isArray(B.checklist[t]) && B.checklist[t].length >= 2 && B.checklist[t].every(p => p.length === 2 && p[0] && p[1]), 'checklist ' + t);
ok(B.common.length === 3, 'common checklist');
// 6) compile result records (self-reported, never a BSV verification claim)
ok(B.fp('abc') === B.fp('abc') && B.fp('abc') !== B.fp('abd') && /^[0-9a-f]{8}$/.test(B.fp('')), 'fingerprint stable/8 hex');
for (const t of T8) {
  const rec = B.makeRecord('Golden <b>', t, 'code-' + t, { status: 'compiled', platform: 'X 1.0', notes: 'n'.repeat(5000), steps: [true, false, true] });
  ok(rec && rec.target === t && rec.status === 'compiled' && rec.self_reported === true && rec.bsv_verified === false, 'record fields ' + t);
  ok(rec.notes.length === 1000 && rec.fp === B.fp('code-' + t), 'record clipped + fp ' + t);
  const md = B.recordMarkdown(rec);
  ok(/Not verified by BSV/.test(md) && /self-reported/.test(md) && md.includes('- [x] ') && md.includes('- [ ] '), 'markdown disclaimer + steps ' + t);
  ok(!/runtime[- ]tested by BSV|verified by BSV:/i.test(md.replace('Not verified by BSV', '')), 'markdown makes no BSV verification claim ' + t);
}
ok(B.cleanRecord({ target: 'evil', status: 'compiled' }) === null, 'unknown target rejected');
const forged = B.cleanRecord({ target: 'mql5', status: 'VERIFIED', bsv_verified: true, fp: 'zz<script>', at: 'x' });
ok(forged.status === 'not-tried' && forged.bsv_verified === false && forged.fp === '', 'forged record neutralised');
console.log(JSON.stringify({ starter_lint: lintSummary }));
console.log(JSON.stringify({ file: js[0], checks: n, failures: bad }));
process.exit(bad ? 1 : 0);
