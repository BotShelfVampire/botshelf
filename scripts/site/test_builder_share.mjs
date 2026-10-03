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
  for (const t of ['pine-v6', 'mql5', 'ctrader', 'mql4', 'ctrader-python', 'bookmap-python']) ok(R.render(JSON.parse(JSON.stringify(back)), t).length > 0, 'shared recipe renders ' + t);
}
// 3) sanitizer rejects bad input
for (const [x, why] of [[[], 'array'], [{ blocks: 'x' }, 'blocks string'], [{ blocks: [{ id: 'Bad Id', type: 'indicator.ema', params: {} }] }, 'bad id'], [{ blocks: [{ id: 'a', type: 'evil.type', params: {} }] }, 'bad type'], [{ blocks: Array.from({ length: 41 }, (_, i) => ({ id: 'b' + i, type: 'indicator.ema', params: {} })) }, 'too many']]) {
  let threw = false; try { B.sanitize(x); } catch (e) { threw = true; } ok(threw, 'reject ' + why);
}
let big = false; try { B.sharePayload({ schemaVersion: '0.1', name: 'x', overlay: true, blocks: Array.from({ length: 40 }, (_, i) => ({ id: 'b' + i, type: 'alert.condition', params: { when: 'close', message: 'm'.repeat(200) } })) }); } catch (e) { big = true; } ok(big, 'oversized share rejected');
ok(B.sanitize({ __proto__: { x: 1 }, blocks: [] }).recipe.x === undefined, 'proto ignored');
// 4) TODO hints: every TODO line of every starter maps to a block id or is reported as general; counts add up
for (const r of R.recipes) for (const t of ['pine-v6', 'mql5', 'ctrader', 'mql4', 'ctrader-python', 'bookmap-python']) {
  const out = R.render(JSON.parse(JSON.stringify(r)), t); const tm = B.todoMap(out, r.blocks);
  const mapped = Object.values(tm.map).reduce((a, v) => a + v.length, 0);
  ok(mapped + tm.general.length === tm.total, 'todo count ' + r.name + ' ' + t);
  for (const id of Object.keys(tm.map)) ok(r.blocks.some(b => b.id === id), 'todo id exists ' + id);
}
{ const tm = B.todoMap('   // alert: TODO add deduplicated alert for divergence\n// TODO unsupported block structure.pivot: pivot\n# TODO session: bar times are UTC', [{ id: 'divergence' }, { id: 'alert' }, { id: 'pivot' }, { id: 'session' }]);
  ok(tm.map.alert && tm.map.alert.length === 1 && tm.map.pivot.length === 1 && tm.map.session.length === 1 && !tm.map.divergence, 'todo line owner by prefix'); }
for (const t of Object.keys(B.hints)) ok(B.hints[t].length === 2 && B.hints[t].every(s => s.length > 20), 'hint en/ja ' + t);
console.log(JSON.stringify({ file: js[0], checks: n, failures: bad }));
process.exit(bad ? 1 : 0);
