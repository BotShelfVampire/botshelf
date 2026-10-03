#!/usr/bin/env node
// Offline check of the generator's `vela` target: renders every recipe, swaps the two Vela imports
// for local stand-ins (no npm install, no browser), runs the BSV engine over synthetic bars and checks
// the model shape, stable ids, labels-on-signals and closed-bar alerts. Not a Vela runtime test.
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const gen = path.join(root, 'trader-toolkit/generator/render.mjs');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bsv-vela-'));
const bars = []; let p = 100; const t0 = Date.UTC(2026, 0, 1);
for (let i = 0; i < 400; i++) { const o = p; p = 100 + 10 * Math.sin(i / 15) + Math.sin(i * 1.7); bars.push({ time: t0 + i * 3600e3, open: o, high: Math.max(o, p) + 0.5, low: Math.min(o, p) - 0.5, close: p, volume: 1 }); }
let checks = 0, failures = 0; const fail = (m) => { failures++; console.error('FAIL', m); }; const ok = (c, m) => { checks++; if (!c) fail(m); };
for (const f of fs.readdirSync(path.join(root, 'trader-toolkit/recipes')).filter(x => x.endsWith('.json')).sort()) {
  let code = execFileSync('node', [gen, path.join(root, 'trader-toolkit/recipes', f), '--target', 'vela'], { encoding: 'utf8' });
  ok(code.includes("from '@luxalgo/vela'") && code.includes("from '@luxalgo/vela/plugin'"), `${f}: imports`);
  code = code.replace(/^import \{ Vela \} from .*$/m, 'const Vela = null;')
    .replace(/^import \{ stableSeriesId \} from .*$/m, "const stableSeriesId = (x) => `${x.instanceId}:${x.kind}:${x.title.trim().toLowerCase().replace(/\\s+/g, '-')}#${x.ordinal}`;");
  const file = path.join(dir, f.replace('.json', '.mjs')); fs.writeFileSync(file, code);
  const { bsvRecipeEngine: E } = await import(file);
  const prep = await E.prepare('x', 'inst');
  ok(prep.language === 'bsv-recipe' && prep.meta && typeof prep.meta.overlay === 'boolean', `${f}: prepare`);
  let live = bars.slice(0, 300); const models = [], alerts = [], errors = [];
  const s = E.execute({ prepared: prep, market: { symbol: 'T', timeframe: '60' }, bars: live, getBars: () => live, mode: 'static' }, { onModel: m => models.push(m), onAlert: a => alerts.push(a), onError: e => errors.push(e) });
  await new Promise(r => setTimeout(r, 5));
  for (let i = 300; i < 400; i++) { live = bars.slice(0, i + 1); s.notifyBars(); }
  s.notifyBars('backfill'); s.stop(); s.notifyBars();
  ok(errors.length === 0, `${f}: no engine errors ${errors[0] || ''}`);
  ok(models.length === 101, `${f}: one model per run (${models.length})`);
  const a = models[0], b = models.at(-1);
  ok(a && a.id === 'inst' && Array.isArray(a.series) && Array.isArray(a.labels) && a.paneHint === (a.overlay ? 'price' : 'new'), `${f}: model shape`);
  ok(JSON.stringify(a.series.map(x => x.id)) === JSON.stringify(b.series.map(x => x.id)), `${f}: stable series ids`);
  ok(b.series.every(x => x.points.length === 400 && x.points.every(pt => pt.value === null || Number.isFinite(pt.value))), `${f}: points aligned, finite or null`);
  const marks = new Set(b.labels.map(l => l.tooltip + '@' + l.x));
  ok(alerts.every(al => al.barIndex >= 299 && al.barIndex < 399), `${f}: alerts only on newly closed bars`);
  if (a.overlay) ok(alerts.every(al => marks.has(al.message + '@' + al.time)), `${f}: every alert has a chart marker`);
  ok(new Set(alerts.map(al => al.id + al.time)).size === alerts.length, `${f}: no duplicate alerts`);
}
fs.rmSync(dir, { recursive: true, force: true });
console.log(JSON.stringify({ target: 'vela', checks, failures }));
process.exit(failures ? 1 : 0);
