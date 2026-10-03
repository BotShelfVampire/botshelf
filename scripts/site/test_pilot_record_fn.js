// Offline test of netlify/functions/pilot-record.js (COMMERCE_TEST=1 in-memory store).
// Usage: node scripts/site/test_pilot_record_fn.js <deploy root>
process.env.COMMERCE_TEST = "1";
process.env.COMPILE_REVIEWER_KEY = "test-reviewer-key-0123456789abcdef0123456789";
const path = require("path"), fs = require("fs");
const root = path.resolve(process.argv[2]);
const fn = require(path.join(root, "netlify/functions/pilot-record.js"));
const session = require(path.join(root, "netlify/functions/_lib/session.js"));
const P = require(path.join(__dirname, "robot_pilot_record.js"));
const cur = JSON.parse(fs.readFileSync(path.join(__dirname, "../../robot-pilot/curricula/isaac-teleop-so101-sim-v1.json"), "utf8"));
let checks = 0, failures = 0; const ok = (c, m) => { checks++; if (!c) { failures++; console.error("FAIL", m); } };
function typeOf(v) { return v === null ? "null" : Array.isArray(v) ? "array" : Number.isInteger(v) ? "integer" : typeof v; }
function validate(s, v, p = "$", errs = []) {
  if (s.const !== undefined && v !== s.const) errs.push(p + " const");
  if (s.enum && !s.enum.includes(v)) errs.push(p + " enum");
  if (s.type) { const ts = [].concat(s.type), t = typeOf(v); if (!ts.some(x => x === t || (x === "number" && t === "integer"))) { errs.push(p + " type"); return errs; } }
  if (typeof v === "string" && s.pattern && !new RegExp(s.pattern).test(v)) errs.push(p + " pattern");
  if (typeof v === "string" && s.maxLength && v.length > s.maxLength) errs.push(p + " maxLength");
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
const sch = n => JSON.parse(fs.readFileSync(path.join(__dirname, "../../schemas", n), "utf8"));
const EV = sch("bsv-teleop-session-evidence.schema.json"), PR = sch("bsv-robot-pilot-profile.schema.json");
const ev = (method, opts = {}) => ({ httpMethod: method, path: "/.netlify/functions/pilot-record", queryStringParameters: opts.q || {},
  headers: Object.assign({ "content-type": "application/json" }, opts.h || {}), body: opts.body === undefined ? undefined : (typeof opts.body === "string" ? opts.body : JSON.stringify(opts.body)) });
const J = r => JSON.parse(r.body);
const RK = { "x-bsv-reviewer-key": process.env.COMPILE_REVIEWER_KEY };
const built = P.build({ taskId: "IsaacContrib-Stack-Cube-SO101-IK-Abs-v0", runtime: cur.runtime, embodiment: cur.embodiment, startedAt: "2026-10-03T10:00:00Z",
  endedAt: "2026-10-03T10:40:00Z", attempted: "10", successful: "7", failed: "3", recovery: "1", safetyEvents: "reset once", artifactRef: "so101_run1.hdf5", note: "<b>drop</b> at stack", pilotId: "pilot_spoof", curriculumId: cur.curriculumId }, cur.modules, { "preflight:0": true });
ok(built.errors.length === 0, "browser builder output ok");
(async () => {
  let r = await fn.handler(ev("GET", { q: { op: "stats" } }));
  ok(r.statusCode === 200 && J(r).counts.received === 0 && J(r).counts.reviewed === 0 && J(r).records === "private", "empty store -> real zero counts, no records");
  r = await fn.handler(ev("POST", { body: { evidence: built.evidence } })); ok(r.statusCode === 401, "anonymous -> 401");
  const u = await session.upsertUser({ email: "pilot1@example.com" });
  let threw = false; try { await session.createSession(u); } catch (e) { threw = e.code === "email_unverified"; } ok(threw, "unverified -> no session");
  u.email_verified = true; await session.putUser(u);
  const ck = { cookie: "botshelf_sid=" + (await session.createSession(u)).id };
  r = await fn.handler(ev("POST", { body: { evidence: built.evidence }, h: Object.assign({ origin: "https://evil.example" }, ck) })); ok(r.statusCode === 403, "foreign origin -> 403");
  r = await fn.handler(ev("POST", { body: { evidence: built.evidence }, h: Object.assign({ "content-type": "text/plain" }, ck) })); ok(r.statusCode === 415, "non-JSON -> 415");
  const bad = [["environment", "REAL_HARDWARE"], ["evidenceId", "x"], ["schemaVersion", "9"], ["episodes", { attempted: 1, successful: 2, failed: 0 }], ["episodes", { attempted: -1, successful: 0, failed: 0 }],
    ["startedAt", "yesterday"], ["taskId", ""], ["email", "a@b.c"], ["dataArtifacts", [{ type: "x", uriOrRef: "y", sha256: "zz" }]], ["endedAt", "2026-10-03T09:00:00Z"]];
  for (const [k, v] of bad) { r = await fn.handler(ev("POST", { body: { evidence: Object.assign({}, built.evidence, { [k]: v }) }, h: ck })); ok(r.statusCode === 400, "bad " + k + " rejected (" + r.statusCode + " " + r.body + ")"); }
  r = await fn.handler(ev("POST", { body: { evidence: built.evidence, profile: {} }, h: ck })); ok(r.statusCode === 400, "extra top-level field rejected");
  r = await fn.handler(ev("POST", { body: { evidence: Object.assign({}, built.evidence, { review: { status: "REVIEWED", note: "self-approve" } }) }, h: ck }));
  let j = J(r); ok(r.statusCode === 201 && j.state === "pending" && j.status === "SELF_REPORTED" && j.public === false && /Not a licence/.test(j.note), "submit -> 201 pending SELF_REPORTED private");
  ok(/^pilot_[0-9a-f]{20}$/.test(j.pilotId) && j.pilotId !== "pilot_spoof", "pilot id replaced by server-side pseudonym");
  const id = j.id;
  r = await fn.handler(ev("POST", { body: { evidence: built.evidence }, h: ck })); ok(J(r).duplicate === true, "same evidenceId -> duplicate");
  const u2 = await session.upsertUser({ email: "pilot2@example.com" }); u2.email_verified = true; await session.putUser(u2);
  const ck2 = { cookie: "botshelf_sid=" + (await session.createSession(u2)).id };
  r = await fn.handler(ev("POST", { body: { evidence: built.evidence }, h: ck2 })); ok(r.statusCode === 409, "other account cannot reuse an evidenceId");
  r = await fn.handler(ev("GET", { q: { op: "mine" }, h: ck })); j = J(r);
  ok(j.records.length === 1 && j.records[0].evidence.review.status === "UNREVIEWED", "self-set REVIEWED ignored -> UNREVIEWED");
  ok(validate(EV, j.records[0].evidence).length === 0, "stored evidence validates against schema: " + validate(EV, j.records[0].evidence).join(","));
  ok(validate(PR, j.records[0].practiceRecord).length === 0 && j.records[0].practiceRecord.practiceRecords[0].status === "SELF_REPORTED", "practice record validates, SELF_REPORTED");
  ok(!/<b>/.test(JSON.stringify(j.records[0].evidence)), "markup stripped");
  r = await fn.handler(ev("GET", { q: { op: "mine" }, h: ck2 })); ok(J(r).records.length === 0, "other account sees nothing");
  r = await fn.handler(ev("GET", { q: { op: "queue" } })); ok(r.statusCode === 401, "queue anon -> 401");
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: { "x-bsv-reviewer-key": "nope-nope-nope-nope-nope-nope-nope-nope" } })); ok(r.statusCode === 401, "queue wrong key -> 401");
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: RK })); j = J(r);
  ok(j.count === 1 && !JSON.stringify(j).includes("pilot1@example.com"), "reviewer queue: 1, no email");
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id, decision: "verified" } })); ok(r.statusCode === 400, "no verified decision");
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id, decision: "certified" } })); ok(r.statusCode === 400, "no certified decision");
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id, decision: "reviewed", note: "counts consistent" } }));
  j = J(r); ok(j.state === "reviewed" && j.record_status === "SELF_REPORTED" && j.public === false, "reviewed keeps SELF_REPORTED, private");
  r = await fn.handler(ev("GET", { q: { op: "mine" }, h: ck })); j = J(r).records[0];
  ok(j.evidence.review.status === "REVIEWED" && validate(EV, j.evidence).length === 0 && j.practiceRecord.practiceRecords[0].status === "SELF_REPORTED", "after review: evidence REVIEWED, record still SELF_REPORTED");
  ok(/not verified by a BSV run/.test(j.practiceRecord.practiceRecords[0].limitations[0]), "limitation says not verified");
  r = await fn.handler(ev("GET", { q: { op: "stats" } })); j = J(r);
  ok(j.counts.received === 1 && j.counts.reviewed === 1 && !("records" in j && Array.isArray(j.records)), "stats: real counts only, no rows");
  let last = 0; for (let i = 0; i < 11; i++) { const b = P.build({ taskId: "t", runtime: "r", embodiment: "e", startedAt: "2026-10-03T10:00:00Z", attempted: "1", successful: "1", failed: "0" }, [], {}); r = await fn.handler(ev("POST", { body: { evidence: b.evidence }, h: ck2 })); last = r.statusCode; }
  ok(last === 429, "11th record in a day -> 429");
  r = await fn.handler(ev("POST", { body: "x".repeat(41000), h: ck })); ok(r.statusCode === 413, "oversized -> 413");
  console.log(JSON.stringify({ fn: "pilot-record", checks, failures }));
  process.exit(failures ? 1 : 0);
})();
