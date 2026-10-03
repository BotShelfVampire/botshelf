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
const site = process.argv[2];
if (site) {
  const src = fs.readFileSync(path.join(site, 'library/source/ai-team-handoff.html'), 'utf8'), pub = fs.readFileSync(path.join(site, 'library/toolkit/ai-team-handoff/index.html'), 'utf8');
  const js = fs.readdirSync(path.join(site, 'library/source')).filter(f => /^handoff-check\.[0-9a-f]{8}\.js$/.test(f));
  ok(js.length === 1 && src.includes(`src="/library/source/${js[0]}"`) && src.includes('id="ho-text"') && /nothing is uploaded/.test(src), 'checker on the gated source page, script from /library/source/');
  ok(!pub.includes('handoff-check') && !pub.includes('id="ho-text"'), 'checker not on the public summary page');
  const others = fs.readdirSync(path.join(site, 'library/source')).filter(f => f.endsWith('.html') && f !== 'ai-team-handoff.html');
  ok(others.every(f => !fs.readFileSync(path.join(site, 'library/source', f), 'utf8').includes('handoff-check')), 'checker only on that packet');
  ok(js.length === 1 && fs.readFileSync(path.join(site, 'library/source', js[0]), 'utf8') === fs.readFileSync(path.join(root, 'scripts/site/handoff_check.js'), 'utf8'), 'served file equals the repo module');
  ok(!/style="/.test(src.slice(src.indexOf('id="ho-checker"'), src.indexOf('</section>', src.indexOf('id="ho-checker"')))), 'no inline styles (CSP)');
}
console.log(JSON.stringify({ test: 'handoff-check', checks, failures }));
process.exit(failures ? 1 : 0);
