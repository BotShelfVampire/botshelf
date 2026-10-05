#!/usr/bin/env node
// Tests of the AI Team Handoff Packet checker (scripts/site/handoff_check.js) against the owner's template, and of
// where it is served: only from the gated /library/source/ path and only on that packet's source page.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const H = require(path.join(root, 'scripts/site/handoff_check.js'));
let checks = 0, failures = 0;
const ok = (c, m) => { checks++; if (!c) { failures++; console.error('FAIL', m); } };
const tpl = fs.readFileSync(path.join(root, 'ai-toolkit/common/ai-team-handoff-packet.md'), 'utf8');
const r0 = H.checkHandoff(tpl);
ok(!r0.ok && r0.errors.some(e => /status must be exactly one/.test(e)) && r0.errors.some(e => /YES or NO/.test(e)) && !r0.errors.some(e => /Missing section/.test(e)), 'blank template: all sections found; status and approval not chosen yet');
const fill = (t, kv) => Object.entries(kv).reduce((s, [k, v]) => s.replace(new RegExp('^(- ' + k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ':).*$', 'm'), '$1 ' + v), t);
const done = fill(tpl, { 'id': 'job-42', 'objective': 'Ship the changes feed', 'status': 'DONE', 'must not do': 'no force-push', 'approval boundaries': 'deploys need owner approval',
  'verified facts': 'deploy 6ac18dae is published', 'results': 'discovery 3937/0', 'source revision': '1425679', 'check name': 'test_discovery.py', 'live URL or artifact': 'https://botshelfvampire.com/transparency/changes.json',
  'verification time': '2026-10-04 08:20 JST', 'limitations': 'not runtime tested', 'highest-value next step': 'tranche 11', 'owner approval needed': 'NO' });
const r1 = H.checkHandoff(done);
ok(r1.ok && r1.status === 'DONE' && r1.warnings.length === 0, 'filled DONE packet with evidence: no problems ' + JSON.stringify(r1.errors.concat(r1.warnings)));
const r2 = H.checkHandoff(fill(done, { 'check name': '', 'verification time': '' }));
ok(!r2.ok && r2.errors.some(e => /DONE needs evidence: check name, verification time/.test(e)), 'DONE without evidence is a problem');
ok(H.checkHandoff(fill(done, { 'status': 'IN_PROGRESS', 'check name': '' })).ok, 'IN_PROGRESS may lack evidence');
const r3 = H.checkHandoff(done.replace(/^DO NOT REPEAT$/m, ''));
ok(!r3.ok && r3.errors.some(e => /Missing section\(s\): DO NOT REPEAT/.test(e)), 'missing section named');
ok(H.checkHandoff(fill(done, { 'results': 'probably passes' })).warnings.some(w => /sounds like a guess/.test(w)), 'guessed result warned');
ok(H.checkHandoff(fill(done, { 'highest-value next step': 'deploy; then email; then tranche 12' })).warnings.some(w => /Keep one/.test(w)), 'several next actions warned');
ok(H.checkHandoff(fill(done, { 'must not do': '' })).warnings.some(w => /must not do/.test(w)), 'empty boundary warned');
ok(!H.checkHandoff(fill(done, { 'owner approval needed': 'maybe' })).ok, 'approval must be YES or NO');
ok(!H.checkHandoff('').ok && H.checkHandoff('').errors[0].includes('JOB'), 'empty text: every section missing');
// startPacket: fills only catalog facts, keeps every section and leaves owner approval for the user
const block = tpl.match(/```text\n([\s\S]*?)```/)[1];
const item = { id: 'letta-memory', path: 'ai-toolkit/letta/memory-blocks.md', framework: 'Letta', status: 'UNTESTED_RUNTIME' };
const sp = H.startPacket(block, item), rp = H.checkHandoff(sp), pp = H.parse(sp);
ok(rp.status === 'NOT_STARTED' && !rp.errors.some(e => /Missing section|status must/.test(e)) && rp.errors.some(e => /YES or NO/.test(e)), 'started packet: all sections, NOT_STARTED, approval still to choose ' + JSON.stringify(rp.errors));
ok(pp.sections.JOB.id === 'toolkit:letta-memory' && pp.sections['CURRENT STATE']['authoritative source'] === 'BotShelfVampire/botshelf ai-toolkit/letta/memory-blocks.md' && /UNTESTED_RUNTIME/.test(pp.sections.EVIDENCE.limitations) && /Not runtime-tested by BSV/.test(pp.sections.EVIDENCE.limitations), 'started packet: id, source and status filled from the item');
const filledKeys = Object.values(pp.sections).reduce((n, s) => n + Object.values(s).filter(Boolean).length, 0);
ok(filledKeys === 7 && pp.sections['NEXT ACTION']['owner approval needed'] === 'YES | NO' && !pp.sections.JOB.objective && !pp.sections.EVIDENCE['source revision'] && !pp.sections['WORK COMPLETED'].results, 'started packet: only the 6 catalog facts filled (+ the template\'s YES | NO left as is), results/evidence blank (' + filledKeys + ')');

const ex = JSON.parse(fs.readFileSync(path.join(root, 'docs/eval-run-example-failed.json'), 'utf8'));
const er0 = H.checkEvalRun(ex);
ok(er0.ok && er0.summary && er0.summary.status === 'evaluation_failed', 'example failed eval record: structure OK ' + JSON.stringify(er0.errors));
ok(H.checkEvalRun(Object.assign({}, ex, { schema_version: '0.9' })).errors.some(e => /schema_version/.test(e)), 'bad schema_version caught');
ok(H.checkEvalRun(Object.assign({}, ex, { summary: Object.assign({}, ex.summary, { total_runs: 99 }) })).errors.some(e => /total_runs/.test(e)), 'wrong total_runs caught');
const badPass = JSON.parse(JSON.stringify(ex)); badPass.runs[0].result = 'passed'; badPass.runs[0].blocking_failures_observed = ['x'];
ok(H.checkEvalRun(badPass).errors.some(e => /cannot pass with blocking/.test(e)), 'passed with blocking failures caught');
const tr = H.startPacket(block, { id: 'langgraph-team-runner', path: 'ai-toolkit/langgraph/team-runner', framework: 'LangGraph', status: 'UNTESTED_RUNTIME' });
ok(/optional --eval-record PATH/.test(H.parse(tr).sections.EVIDENCE.limitations) && /facts, numbers and quotes are not checked/.test(H.parse(tr).sections.EVIDENCE.limitations), 'team-runner startPacket names --eval-record and facts-not-checked');
const n8 = H.startPacket(block, { id: 'n8n-team-runner', path: 'ai-toolkit/n8n/team-runner', framework: 'n8n', status: 'UNTESTED_RUNTIME' });
ok(/no --eval-record/.test(H.parse(n8).sections.EVIDENCE.limitations), 'n8n startPacket says no --eval-record');

ok(sp.split('\n').length === block.split('\n').length && H.startPacket(sp, item) === sp, 'started packet: same lines as the template, idempotent');
const site = process.argv[2];
if (site) {
  const src = fs.readFileSync(path.join(site, 'library/source/ai-team-handoff.html'), 'utf8'), pub = fs.readFileSync(path.join(site, 'library/toolkit/ai-team-handoff/index.html'), 'utf8');
  const js = fs.readdirSync(path.join(site, 'library/source')).filter(f => /^handoff-check\.[0-9a-f]{8}\.js$/.test(f));
  ok(js.length === 1 && src.includes(`src="/library/source/${js[0]}"`) && src.includes('id="ho-text"') && src.includes('id="ho-eval"') && /validate-eval-run/.test(src) && /nothing is uploaded/.test(src), 'checker on the gated source page with eval box, script from /library/source/');
  ok(!pub.includes('handoff-check') && !pub.includes('id="ho-text"'), 'checker not on the public summary page');
  const others = fs.readdirSync(path.join(site, 'library/source')).filter(f => f.endsWith('.html') && f !== 'ai-team-handoff.html');
  ok(others.every(f => !fs.readFileSync(path.join(site, 'library/source', f), 'utf8').includes('handoff-check')), 'checker only on that packet');
  ok(js.length === 1 && fs.readFileSync(path.join(site, 'library/source', js[0]), 'utf8') === fs.readFileSync(path.join(root, 'scripts/site/handoff_check.js'), 'utf8'), 'served file equals the repo module');
  const cat = JSON.parse(fs.readFileSync(path.join(root, 'ai-toolkit/catalog.json'), 'utf8')).entries;
  const opts = [...src.matchAll(/<option value="([a-z0-9-]+)" data-path="([^"]+)" data-fw="([^"]+)" data-st="([A-Z_]+)">/g)].map(m => m.slice(1).join('|'));
  ok(JSON.stringify(opts) === JSON.stringify(cat.map(e => [e.id, e.path, e.platform, e.status].join('|').replace(/&/g, '&amp;'))), `start-from-item: one option per catalog entry with its path, framework and status (${opts.length})`);
  const dt = (src.match(/id="ho-start" data-ho-tpl="([^"]*)"/) || [])[1] || '';
  ok(dt.replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&') === block && src.includes('id="ho-item"'), 'start-from-item: template on the button equals the packet');
  ok(!/style="/.test(src.slice(src.indexOf('id="ho-checker"'), src.indexOf('</section>', src.indexOf('id="ho-checker"')))), 'no inline styles (CSP)');

  const lg = fs.readFileSync(path.join(site, 'library/toolkit/langgraph-team-runner/index.html'), 'utf8');
  ok(/--eval-record/.test(lg) && /schema 1.0/.test(lg), 'public langgraph summary names --eval-record');
  const ho = fs.readFileSync(path.join(site, 'library/toolkit/ai-team-handoff/index.html'), 'utf8');
  ok(/eval-run schema 1.0/.test(ho) || /eval-run JSON/.test(ho), 'public handoff summary names eval-run check');
}

console.log(JSON.stringify({ test: 'handoff-check', checks, failures }));
process.exit(failures ? 1 : 0);
