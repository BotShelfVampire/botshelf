#!/usr/bin/env node
// Parity: the gated browser port must produce byte-identical output to trader-toolkit/generator/render.mjs.
// Usage: node scripts/site/test_builder_parity.mjs <site tree>
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm'; import { execFileSync } from 'node:child_process';
const site = process.argv[2]; const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const js = fs.readdirSync(path.join(site, 'trading/sources')).filter(f => /^bsv-builder\.[0-9a-f]{8}\.js$/.test(f));
if (js.length !== 1) { console.error('expected one builder js, got', js); process.exit(1); }
const ctx = { globalThis: {} }; ctx.window = ctx; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(site, 'trading/sources', js[0]), 'utf8'), ctx);
const R = ctx.BSVRender; let n = 0, bad = 0;
for (const f of fs.readdirSync(path.join(repo, 'trader-toolkit/recipes')).filter(f => f.endsWith('.json'))) {
  const p = path.join(repo, 'trader-toolkit/recipes', f);
  for (const t of ['pine-v6', 'mql5', 'ctrader', 'mql4', 'ctrader-python', 'bookmap-python']) {
    const want = execFileSync('node', [path.join(repo, 'trader-toolkit/generator/render.mjs'), p, '--target', t], { encoding: 'utf8' });
    const got = R.render(JSON.parse(fs.readFileSync(p, 'utf8')), t); n++;
    if (got !== want) { bad++; console.log('MISMATCH', f, t); }
  }
}
// invalid recipe must be rejected the same way
try { R.render({ schemaVersion: '0.1', name: 'x', blocks: [{ id: 'a', type: 'signal.cross', params: { left: 'nope', right: 'close' } }] }, 'pine-v6'); bad++; console.log('invalid recipe accepted'); } catch (e) {}
console.log(JSON.stringify({ file: js[0], cases: n, mismatches: bad, recipes: R.recipes.length, types: R.types.length }));
process.exit(bad ? 1 : 0);
