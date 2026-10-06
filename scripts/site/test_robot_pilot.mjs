// Issue #7 checks: practice-record builder output validates against the published schemas (BSV mini JSON-Schema
// validator: type/const/enum/required/properties/additionalProperties/items/minimum/pattern/minLength/maxLength/format date-time),
// curriculum validates, page claims stay inside the boundary. Usage: node test_robot_pilot.mjs <site>
import fs from "fs"; import path from "path"; import { createRequire } from "module";
const require = createRequire(import.meta.url);
const site = path.resolve(process.argv[2]);
let checks = 0, failures = 0; const ok = (c, m) => { checks++; if (!c) { failures++; console.error("FAIL", m); } };
function typeOf(v) { return v === null ? "null" : Array.isArray(v) ? "array" : Number.isInteger(v) ? "integer" : typeof v; }
function validate(s, v, p = "$", errs = []) {
  if (s.const !== undefined && v !== s.const) errs.push(p + " const");
  if (s.enum && !s.enum.includes(v)) errs.push(p + " enum " + v);
  if (s.type) { const ts = [].concat(s.type), t = typeOf(v); if (!ts.some(x => x === t || (x === "number" && t === "integer"))) { errs.push(p + " type " + t); return errs; } }
  if (typeof v === "string") {
    if (s.pattern && !new RegExp(s.pattern).test(v)) errs.push(p + " pattern");
    if (s.minLength && v.length < s.minLength) errs.push(p + " minLength");
    if (s.maxLength && v.length > s.maxLength) errs.push(p + " maxLength");
    if (s.format === "date-time" && !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/.test(v)) errs.push(p + " date-time");
  }
  if (typeof v === "number" && s.minimum !== undefined && v < s.minimum) errs.push(p + " minimum");
  if (typeOf(v) === "object") {
    for (const r of s.required || []) if (!(r in v)) errs.push(p + " required " + r);
    for (const [k, x] of Object.entries(v)) {
      if (s.properties && s.properties[k]) validate(s.properties[k], x, p + "." + k, errs);
      else if (s.additionalProperties === false) errs.push(p + " extra " + k);
      else if (typeof s.additionalProperties === "object") validate(s.additionalProperties, x, p + "." + k, errs);
    }
  }
  if (Array.isArray(v) && s.items) v.forEach((x, i) => validate(s.items, x, p + "[" + i + "]", errs));
  return errs;
}
const sch = n => JSON.parse(fs.readFileSync(path.join(site, "schemas", n), "utf8"));
const EV = sch("teleop-session-evidence-v0.1.json"), PR = sch("robot-pilot-profile-v0.1.json"), CU = sch("robot-pilot-curriculum-v0.1.json");
// validator self-test
ok(validate(EV, {}).length > 5, "validator rejects empty evidence");
const cur = JSON.parse(fs.readFileSync(path.join(site, "robot-pilot/curricula/isaac-teleop-so101-sim-v1.json"), "utf8"));
ok(validate(CU, cur).length === 0, "curriculum validates: " + validate(CU, cur).join(","));
ok(cur.environment === "SIMULATION" && cur.completion.practiceRecordStatus === "SELF_REPORTED", "curriculum is simulation + self-reported");
const jsf = fs.readdirSync(path.join(site, "robot-pilot")).filter(f => /^robot-pilot\.[0-9a-f]{8}\.js$/.test(f));
ok(jsf.length === 1, "one hashed record JS");
const P = require(path.join(site, "robot-pilot", jsf[0]));
const base = { taskId: "IsaacContrib-Stack-Cube-SO101-IK-Abs-v0", runtime: cur.runtime, embodiment: cur.embodiment, startedAt: "2026-10-03T10:00:00Z", endedAt: "2026-10-03T10:40:00Z", attempted: "10", successful: "7", failed: "3", recovery: "", curriculumId: cur.curriculumId };
const cases = [
  ["minimal", {}],
  ["full", { runtimeVersion: "Isaac Lab 3.0.0", sourceRevision: "abc123", inputDevice: "XR controller", pilotId: "pilot_me", recovery: "2", safetyEvents: "reset after gripper stall\n\nsim crash", artifactType: "HDF5", artifactRef: "datasets/so101_run1.hdf5", artifactSha: "a".repeat(64), note: "two drops at the stack" }],
  ["zero", { attempted: "0", successful: "0", failed: "0" }],
];
for (const [name, extra] of cases) {
  const o = P.build(Object.assign({}, base, extra), cur.modules, { "preflight:0": true, "record10:2": true });
  ok(o.errors.length === 0, name + ": no builder errors " + o.errors.join(";"));
  const e1 = validate(EV, o.evidence), e2 = validate(PR, o.profile);
  ok(e1.length === 0, name + ": evidence validates " + e1.join(","));
  ok(e2.length === 0, name + ": profile validates " + e2.join(","));
  ok(o.evidence.environment === "SIMULATION" && o.evidence.review.status === "UNREVIEWED" && o.profile.practiceRecords[0].status === "SELF_REPORTED" && o.profile.visibility === "PRIVATE", name + ": sim / unreviewed / self-reported / private");
  ok(o.profile.practiceRecords[0].evidenceIds[0] === o.evidence.evidenceId, name + ": record references evidence");
  ok(o.evidence.metrics["module.preflight.criterion1"] === true && o.evidence.metrics["module.control.criterion1"] === false, name + ": ticked criteria in metrics");
}
for (const [name, extra, want] of [["over", { successful: "8", failed: "3" }, /more than attempted/], ["neg", { failed: "-1" }, /failed/], ["notask", { taskId: "" }, /task id/],
  ["nostart", { startedAt: "" }, /start time/], ["order", { endedAt: "2026-10-03T09:00:00Z" }, /before start/], ["sha", { artifactRef: "x", artifactSha: "zz" }, /sha256/],
  ["hw", { environment: "REAL_HARDWARE" }, null]]) {
  const o = P.build(Object.assign({}, base, extra), cur.modules, {});
  if (want) ok(o.errors.some(e => want.test(e)), name + ": rejected (" + o.errors.join(";") + ")");
  else ok(o.evidence.environment === "SIMULATION", name + ": environment cannot be switched to real hardware");
}
const html = fs.readFileSync(path.join(site, "robot-pilot/index.html"), "utf8");
ok(!/REAL_HARDWARE/.test(html), "page offers no real-hardware option");
ok(/id="rp-c-received">–</.test(html) && /id="rp-c-reviewed">–</.test(html), "page: counts not hard-coded (filled from the stats API)");
ok(/never a licence, a certification or permission to operate real hardware/.test(html) && /stays SELF_REPORTED/.test(html), "page: send note keeps SELF_REPORTED / not a licence");
ok(/pilot-record\?op=stats|pilot-record' \+ '\?op=stats|API \+ '\?op=stats'/.test(fs.readFileSync(path.join(site, "robot-pilot", jsf[0]), "utf8")), "record JS reads real counts from stats");
ok(/BSV has not run this curriculum itself yet/.test(html) && /Not a government licence/.test(html) && /Not permission to operate real hardware/.test(html) && /never upgrades the record/.test(html), "page: boundary statements");
ok(!/certified pilot|licensed pilot|BSV verified/i.test(html), "page: no licence/certification claims");
// Check a saved file (#7 tranche 5): in-browser validator agrees with this test's validator; boundary notes; no upload
{
  const good = P.build(Object.assign({}, base), cur.modules, {});
  const cd = P.checkDoc(good.evidence, { evidence: EV });
  ok(cd.kind === "evidence" && cd.errors.length === 0 && cd.notes.length === 0, "check file: built evidence is valid, no notes (" + cd.errors.join(";") + ")");
  const cp = P.checkDoc(good.profile, { profile: PR });
  ok(cp.kind === "profile" && cp.errors.length === 0 && cp.notes.length === 0, "check file: built practice record is valid (" + cp.errors.join(";") + ")");
  const docs = [{}, { evidenceId: 5 }, Object.assign({}, good.evidence, { extra: 1 }), Object.assign({}, good.evidence, { startedAt: "yesterday" }), Object.assign({}, good.evidence, { episodes: "x" })];
  ok(docs.every(d => P.validate(EV, d).length === validate(EV, d).length), "check file: browser validator finds the same number of problems as the test validator");
  const hw = P.checkDoc(Object.assign({}, good.evidence, { environment: "REAL_HARDWARE" }), { evidence: EV });
  ok(hw.errors.length === 0 && hw.notes.some(n => /no permission to operate real hardware/.test(n)), "check file: REAL_HARDWARE flagged by a boundary note");
  const rv = P.checkDoc(Object.assign({}, good.evidence, { review: { status: "REVIEWED" } }), { evidence: EV });
  ok(rv.notes.some(n => /Only a BSV review sets this/.test(n)), "check file: self-raised review status flagged");
  const pr = JSON.parse(JSON.stringify(good.profile)); pr.practiceRecords[0].status = "REVIEWED";
  ok(P.checkDoc(pr, { profile: PR }).notes.some(n => /SELF_REPORTED/.test(n)), "check file: self-raised practice status flagged");
  ok(P.checkDoc({ hello: 1 }, {}).kind === "" && P.checkDoc([], {}).errors.length === 1, "check file: unknown files rejected");
  const js = fs.readFileSync(path.join(site, "robot-pilot", jsf[0]), "utf8");
  const blk = js.slice(js.indexOf("var cf = $('#rp-check-file')"), js.indexOf("var ul = $('#rp-missions')"));
  ok(blk.length > 200 && !/innerHTML/.test(blk) && !/method\s*:/.test(blk) && /credentials: 'omit'/.test(blk), "check file: textContent only, GET of the public schema only, nothing uploaded");
  ok(/id="rp-check-file"/.test(html) && /nothing is uploaded/.test(html) && /href="#check"/.test(html), "page: check-a-file section, no-upload note, chip");
}
// Open missions board (#7 tranche 4): approved PUBLIC robot-pilot requests only, counts not hard-coded, text-only rendering
{
  const rows = [
    { requestId: "req_a", job: "Collect 50 SO-101 pick-and-place episodes in simulation", domains: ["robot-pilot"], platforms: ["Isaac Lab"], visibility: "PUBLIC", status: "OPEN", willingnessToPay: { min: 20, max: 40, currency: "USDT" }, deadline: "2026-12-01T00:00:00Z", createdAt: "2026-10-04T01:00:00Z" },
    { requestId: "req_b", job: "TradingView indicator for session ranges please", domains: ["trading"], platforms: ["TradingView"], visibility: "PUBLIC", status: "OPEN", createdAt: "2026-10-04T01:00:00Z" },
    { requestId: "req_c", job: "Private robot request should never show", domains: ["robot-pilot"], visibility: "PRIVATE", status: "OPEN", createdAt: "2026-10-04T01:00:00Z" },
    { requestId: "req_d", job: "<img src=x onerror=alert(1)> teleop dataset", domains: ["robotics", "robot-pilot"], visibility: "PUBLIC", status: "CLAIMED", createdAt: "2026-10-04T02:00:00Z" }];
  const ms = P.missions(rows);
  ok(ms.length === 2 && ms[0].id === "req_a" && ms[1].id === "req_d", "missions: only PUBLIC rows whose areas include robot-pilot");
  ok(/stated, not escrow/.test(ms[0].budget) && ms[1].budget === "" && ms[0].deadline === "2026-12-01", "missions: budget only when stated, marked not escrow");
  ok(P.missions(null).length === 0 && P.missions([{}]).length === 0, "missions: empty / malformed input gives no rows");
  const js = fs.readFileSync(path.join(site, "robot-pilot", jsf[0]), "utf8");
  const blk = js.slice(js.indexOf("demand-request?op=public"), js.indexOf("?op=stats"));
  ok(blk.length > 100 && !/innerHTML/.test(blk) && /textContent/.test(blk), "missions: rendered with textContent only");
  ok(/id="missions"/.test(html) && /id="rp-c-missions">–</.test(html) && /href="#missions"/.test(html) && /href="#recipes"/.test(html), "page: missions section, count not hard-coded, Teleop recipes + Open missions chips");
  ok(/no escrow, no contract and no permission to operate real hardware/.test(html) && /Nothing is seeded or estimated/.test(html), "page: missions boundary text");
}
ok(/href="\/requests\/\?area=robot-pilot&amp;kind=mission"/.test(html), "page: mission request link");
ok(!/<script(?![^>]*\bsrc=)(?![^>]*application\/(ld\+)?json)[^>]*>/.test(html), "page: no inline executable script");
for (const m of cur.modules) ok(html.includes('id="mod-' + m.id + '"'), "page: module " + m.id);
for (const u of ["https://nvidia.github.io/IsaacCapture/main/getting_started/lerobot/data_collection_sim.html", "https://github.com/NVIDIA/IsaacCapture"]) ok(html.includes(u), "page links " + u);
const sm = fs.readFileSync(path.join(site, "sitemap.xml"), "utf8");
ok(sm.includes("<loc>https://botshelfvampire.com/robot-pilot/</loc>"), "sitemap has /robot-pilot/");
for (const n of ["teleop-session-evidence-v0.1.json", "robot-pilot-profile-v0.1.json", "robot-pilot-curriculum-v0.1.json"]) ok(sch(n).$id === "https://botshelfvampire.com/schemas/" + n, "schema at $id " + n);
const rq = fs.readdirSync(path.join(site, "requests")).filter(f => f.endsWith(".js")).map(f => fs.readFileSync(path.join(site, "requests", f), "utf8")).join("");
ok(/kind'\)==='mission'/.test(rq) && /area/.test(rq), "request market handles ?area=robot-pilot&kind=mission");
// Teleop recipe library (#7 tranche 3)
{
  const rel = "robot-pilot/teleop-recipes/so101-sim-practice-session-v1.json";
  const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
  const pub = fs.readFileSync(path.join(site, rel), "utf8"), r = JSON.parse(pub);
  ok(pub === fs.readFileSync(path.join(repoRoot, rel), "utf8"), "teleop recipe published byte-identical");
  ok(r.environment === "SIMULATION" && r.status === "UNTESTED_RUNTIME" && /not run/i.test(r.statusNote), "teleop recipe: simulation only, untested status stated");
  const ids = r.failureTaxonomy.map(t => t.id);
  ok(ids.length >= 5 && new Set(ids).size === ids.length && ids.every(x => /^[a-z]+(-[a-z]+)*$/.test(x)), "teleop recipe: unique kebab-case failure ids");
  const ev = sch("teleop-session-evidence-v0.1.json");
  ok(Object.values(r.dataExport.fieldMap).every(v => v.split(".")[0] in ev.properties), "teleop recipe: export map points at real evidence fields");
  ok(r.dataExport.schema === ev.$id, "teleop recipe: export schema is the published evidence schema");
  ok(r.notIncluded.some(x => /controller mapping/i.test(x)) && r.notIncluded.some(x => /real-hardware/i.test(x)), "teleop recipe: device mapping and hardware steps explicitly not included");
  ok(!/certif|licensed pilot|verified by bsv|official nvidia procedure(?! )/i.test(JSON.stringify(r).replace("Not an official NVIDIA procedure", "")), "teleop recipe: no certification or official claims");
  const html = fs.readFileSync(path.join(site, "robot-pilot/index.html"), "utf8");
  ok(html.includes('id="recipes"') && html.includes(rel) && ids.every(x => html.includes("<code>" + x + "</code>")), "Academy lists the teleop recipe with its taxonomy");
}
// practice log (#7 tranche 6): totals from saved evidence only, inconsistencies flagged
{
  const mk = (id, task, a, s, f, r, env, se) => ({ evidenceId: id, taskId: task, environment: env || "SIMULATION", episodes: { attempted: a, successful: s, failed: f, recoveryEpisodes: r }, safetyEvents: se || [] });
  const S = P.summarize([mk("e1", "T1", 10, 7, 3, 1), mk("e2", "T1", 5, 5, 0, 0, "SIMULATION", ["x"]), mk("e3", "T2", 4, 3, 3, 0, "REAL_HARDWARE"), null, { evidenceId: "e4" }]);
  ok(S.sessions === 3 && S.attempted === 19 && S.successful === 15 && S.failed === 6 && S.recovery === 1 && S.safetyEvents === 1, "practice log: totals from saved sessions only");
  ok(Math.abs(S.successRate - 15 / 19) < 1e-12 && S.byTask.T1.sessions === 2 && S.byTask.T1.successful === 12 && S.byTask.T2.attempted === 4, "practice log: rate and per-task totals");
  ok(S.inconsistent.length === 1 && S.inconsistent[0] === "e3" && S.nonSimulation === 1, "practice log: counts that do not add up and non-simulation sessions are flagged");
  const E = P.summarize([]); ok(E.sessions === 0 && E.successRate === null, "practice log: empty log has no rate");
  const N = P.summarize([mk("n", "T", -3, "2", 1.9, 0)]); ok(N.attempted === 0 && N.successful === 0 && N.failed === 1, "practice log: negative or non-number counts are not counted");
  const Tm = P.summarize([{ ...mk("t1", "T", 1, 1, 0, 0), startedAt: "2026-10-04T10:00:00Z", endedAt: "2026-10-04T09:00:00Z" }, { ...mk("t2", "T", 1, 1, 0, 0), startedAt: "2026-10-04T10:00:00Z", endedAt: "2026-10-04T11:00:00Z" }, { ...mk("t3", "T", 1, 1, 0, 0), startedAt: "bad", endedAt: "2026-10-04T11:00:00Z" }]);
  ok(Tm.endBeforeStart.length === 1 && Tm.endBeforeStart[0] === "t1" && Tm.sessions === 3, "practice log: a session that ends before it starts is flagged, not corrected; unparseable times are not flagged");
  const Dp = P.summarize([mk("d1", "T", 1, 1, 0, 0), mk("d1", "T", 1, 1, 0, 0), mk("d1", "T", 1, 1, 0, 0), mk("d2", "T", 1, 1, 0, 0)]);
  ok(Dp.duplicateIds.length === 1 && Dp.duplicateIds[0] === "d1" && Dp.sessions === 4, "practice log: an evidence id saved more than once is listed once and still counted (flag only)");
  ok(html.includes('id="rp-log"') && html.includes('id="rp-log-clear"') && /not reviewed|nothing is uploaded, estimated or reviewed/.test(html), "practice log section on the Academy page");
}
// tooling opportunities (#7 tranche 7): all seven kinds, counts equal the recipe file, no demand numbers, request + publish links
{
  const h = fs.readFileSync(path.join(site, "robot-pilot/index.html"), "utf8");
  const rdir = path.join(site, "robot-pilot/teleop-recipes");
  const rs = fs.readdirSync(rdir).filter(f => f.endsWith(".json")).map(f => JSON.parse(fs.readFileSync(path.join(rdir, f), "utf8")));
  ok(rs.length >= 2, "tooling: at least two teleop recipe files on the site");
  const n = k => rs.reduce((a, r) => a + r[k].length, 0);
  const nf = rs.reduce((a, r) => a + Object.keys(r.dataExport.fieldMap).length, 0);
  const sec = (h.match(/<section[^>]*id="tooling"[\s\S]*?<\/section>/) || [""])[0];
  const kinds = ["controller-mapping", "retargeting", "dashboards", "annotation-qa", "replay", "simulation-scenes", "data-conversion"];
  ok(sec && kinds.every(k => sec.includes(`id="tool-${k}"`)) && (sec.match(/<tr id="tool-/g) || []).length === kinds.length, "tooling: seven kinds listed once each");
  ok(sec.includes(`${n("failureTaxonomy")} failure ids`) && sec.includes(`${n("annotationLabels")} annotation labels`) && sec.includes(`${n("episodeAcceptance")} episode-acceptance`) && sec.includes(`(${n("replayChecklist")} items)`) && sec.includes(`(${nf} fields)`), "tooling: counts equal the teleop recipe files");
  ok(rs.some(r => r.notIncluded.some(x => /controller mapping/i.test(x))) && /Not included/.test(sec), "tooling: controller mapping shown as not included, as the recipe says");
  ok(sec.includes('href="/requests/?area=robot-pilot"') && sec.includes('href="/for-sellers.html"'), "tooling: request and publish links");
  ok(!/\b\d+\s*(requests?|people|users|buyers|demand)\b|projected|forecast|\$\d/i.test(sec.replace(/<[^>]+>/g, " ")) && /not a demand figure/.test(sec), "tooling: no demand numbers, says so");
}
// practice-log CSV (#7 tranche 8): one row per saved session, values as saved, formula cells neutralised
{
  const P = require(path.join(site, "robot-pilot", jsf[0]));
  const e1 = { evidenceId: "e1", taskId: "T1", environment: "SIMULATION", runtimeVersion: "1.0", inputDevice: "=HYPERLINK(\"x\")", episodes: { attempted: 5, successful: 4, failed: 1, recoveryEpisodes: 0 }, safetyEvents: ["a, b"], review: { status: "UNREVIEWED" } };
  const csv = P.toCsv([e1, null, { evidenceId: "e2", episodes: {} }]), rows = csv.trim().split("\r\n");
  ok(rows.length === 3 && rows[0].split(",").length === 16 && rows[0].startsWith("evidenceId,taskId,environment") && rows[0].endsWith(",criteriaMet,criteriaTotal"), "csv: header + one row per saved session (non-objects skipped)");
  ok(rows[1].includes(`"'=HYPERLINK(""x"")"`) && rows[1].includes(",5,4,1,0,1,UNREVIEWED"), "csv: formula cell neutralised and quoted; counts as saved");
  ok(P.toCsv([]) === rows[0] + "\r\n", "csv: empty log is the header only");
  const e3 = Object.assign({}, e1, { metrics: { "module.preflight.criterion1": true, "module.preflight.criterion2": false, "module.control.criterion1": true, curriculumId: "x", "module.bad": true } });
  ok(P.toCsv([e3]).trim().split("\r\n")[1].endsWith(",UNREVIEWED,2,3") && rows[1].endsWith(",UNREVIEWED,,"), "csv: criteria met / total counted from saved metrics only (#7 tranche 13); blank when none recorded");
  const h = fs.readFileSync(path.join(site, "robot-pilot/index.html"), "utf8");
  ok(h.includes('id="rp-log-csv"') && /nothing uploaded/.test(h), "csv: download button on the Academy page, says nothing is uploaded");
}
// practice-log import (#7 tranche 9): valid evidence only, dedupe by evidenceId, last 20 kept, nothing else touched
{
  const P = require(path.join(site, "robot-pilot", jsf[0])), EVS = sch("teleop-session-evidence-v0.1.json");
  const mkE = id => { const o = P.build(Object.assign({}, base), cur.modules, {}, { evidenceId: id, pilotId: "pilot_t" }); return o.evidence; };
  const a = mkE("teleop_" + "a".repeat(16)), b = mkE("teleop_" + "b".repeat(16));
  ok(validate(EV, a).length === 0, "import: fixture evidence is valid");
  const bad = Object.assign({}, b, { evidenceId: "teleop_" + "c".repeat(16), episodes: "x" });
  const r = P.mergeLog([a], [a, b, bad, { practiceRecords: [] }, 7, null], EVS);
  ok(r.added === 1 && r.skipped === 1 && r.rejected.length === 4 && r.list.length === 2 && r.list[1] === b, "import: adds valid new evidence, skips same evidenceId, rejects invalid/profile/non-objects");
  ok(/schema problem/.test(r.rejected[0].reason) && /not a session-evidence/.test(r.rejected[1].reason), "import: rejection reasons name the cause");
  ok(P.mergeLog([], [a], null).added === 0, "import: nothing is added without the schema");
  const many = Array.from({ length: 25 }, (_, i) => mkE("teleop_" + String(i).padStart(16, "0")));
  // Save keeps 20 and reports what fell out (#7 tranche 12)
  const twenty = Array.from({ length: P.LOG_MAX }, (_, i) => ({ evidenceId: 'e' + i }));
  const s1 = P.appendLog(twenty.slice(0, 5), { evidenceId: 'new' }), s2 = P.appendLog(twenty, { evidenceId: 'new' });
  ok(P.LOG_MAX === 20 && s1.dropped === 0 && s1.list.length === 6 && s2.dropped === 1 && s2.list.length === 20 && s2.list[0].evidenceId === 'e1' && s2.list[19].evidenceId === 'new', 'save: appendLog keeps 20 and reports the dropped count');
  ok(P.appendLog(null, { evidenceId: 'x' }).list.length === 1 && P.appendLog([null, 7, []], { evidenceId: 'x' }).list.length === 1, 'save: appendLog ignores non-objects');
  ok(/var r = appendLog\(a, o\.evidence\)/.test(fs.readFileSync(path.join(site, "robot-pilot", jsf[0]), "utf8")) && !/a\.slice\(-20\)/.test(fs.readFileSync(path.join(site, "robot-pilot", jsf[0]), "utf8")), 'save button uses appendLog (no silent slice)');
  const r2 = P.mergeLog([a], many, EVS);
  ok(r2.list.length === 20 && r2.dropped === 6 && r2.list[19] === many[24] && !r2.list.includes(a), "import: log keeps the last 20, oldest dropped and counted");
  // backup (#7 tranche 10): the JSON backup round-trips through the import, unchanged
  const bk = P.toJson([a, b, null, [1], "x"]), back = JSON.parse(bk);
  ok(Array.isArray(back) && back.length === 2 && JSON.stringify(back[0]) === JSON.stringify(a) && JSON.stringify(back[1]) === JSON.stringify(b), "backup: JSON array of the evidence documents only, unchanged");
  const r3 = P.mergeLog([], back, EVS);
  ok(r3.added === 2 && r3.rejected.length === 0 && JSON.stringify(r3.list) === JSON.stringify([a, b]), "backup: re-import into an empty log restores it");
  ok(P.mergeLog([a, b], back, EVS).skipped === 2 && JSON.parse(P.toJson([])).length === 0, "backup: re-import into the same log adds nothing; empty log backs up as []");
  const h = fs.readFileSync(path.join(site, "robot-pilot/index.html"), "utf8");
  ok(h.includes('id="rp-log-json"') && /re-importable/.test(h), "backup: button on the Academy page");
  ok(/<input type="file" id="rp-log-import" multiple/.test(h) && h.includes('id="rp-log-import-msg"') && /nothing uploaded/.test(h), "import: multi-file input on the Academy page, says nothing is uploaded");
}
console.log(JSON.stringify({ test: "robot-pilot", checks, failures }));
process.exit(failures ? 1 : 0);
