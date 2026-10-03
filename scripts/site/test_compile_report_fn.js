// Offline test of netlify/functions/compile-report.js with the in-memory store (COMMERCE_TEST=1).
// Usage: node scripts/site/test_compile_report_fn.js <deploy root>
process.env.COMMERCE_TEST = "1";
process.env.COMPILE_REVIEWER_KEY = "test-reviewer-key-0123456789abcdef0123456789";
const path = require("path");
const root = path.resolve(process.argv[2]);
const fn = require(path.join(root, "netlify/functions/compile-report.js"));
const session = require(path.join(root, "netlify/functions/_lib/session.js"));
let checks = 0, failures = 0;
const ok = (c, m) => { checks++; if (!c) { failures++; console.error("FAIL", m); } };
const ev = (method, opts = {}) => ({ httpMethod: method, path: "/.netlify/functions/compile-report", queryStringParameters: opts.q || {},
  headers: Object.assign({ "content-type": "application/json" }, opts.h || {}), body: opts.body === undefined ? undefined : (typeof opts.body === "string" ? opts.body : JSON.stringify(opts.body)) });
const good = { recipe: "Golden Cross Alert", target: "motivewave", status: "compiled", platform: "MotiveWave 7", notes: "<b>ok</b>", steps: [true, false], fp: "0a1b2c3d", builder: "bsv-builder.c212b4d9.js" };
(async () => {
  let r = await fn.handler(ev("POST", { body: good }));
  ok(r.statusCode === 401, "anonymous POST -> 401 (" + r.statusCode + ")");
  const unverified = await session.upsertUser({ email: "u1@example.com" });
  let threw = false; try { await session.createSession(unverified); } catch (e) { threw = e.code === "email_unverified"; }
  ok(threw, "unverified account gets no session");
  unverified.email_verified = true; await session.putUser(unverified);
  const s = await session.createSession(unverified);
  const ck = { cookie: "botshelf_sid=" + s.id };
  r = await fn.handler(ev("POST", { body: good, h: Object.assign({ "content-type": "text/plain" }, ck) }));
  ok(r.statusCode === 415, "non-JSON -> 415");
  r = await fn.handler(ev("POST", { body: Object.assign({}, good, { email: "x@y" }), h: ck }));
  ok(r.statusCode === 400 && /unknown_field/.test(r.body), "extra field (PII) rejected");
  for (const [k, v] of [["target", "nope"], ["status", "verified"], ["fp", "XYZ"], ["builder", "evil.js"], ["recipe", ""]]) {
    r = await fn.handler(ev("POST", { body: Object.assign({}, good, { [k]: v }), h: ck }));
    ok(r.statusCode === 400, "bad " + k + " rejected");
  }
  r = await fn.handler(ev("POST", { body: good, h: ck }));
  const b = JSON.parse(r.body);
  ok(r.statusCode === 201 && b.state === "pending" && b.bsv_verified === false && b.public === false, "valid POST -> 201 pending, not verified, not public");
  r = await fn.handler(ev("POST", { body: good, h: ck }));
  ok(JSON.parse(r.body).duplicate === true && JSON.parse(r.body).id === b.id, "duplicate merged");
  for (let i = 0; i < 12; i++) r = await fn.handler(ev("POST", { body: Object.assign({}, good, { fp: (0x10000000 + i).toString(16) }), h: ck }));
  ok(r.statusCode === 429, "per-account daily limit -> 429");
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: ck }));
  ok(r.statusCode === 401, "user cannot read queue");
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: { "x-admin-secret": "test-admin-secret" } }));
  const qb = JSON.parse(r.body);
  ok(r.statusCode === 200 && qb.count === 10 && qb.reports[0].account_email === "u1@example.com", "owner queue lists pending with account email lookup (" + qb.count + ")");
  ok(qb.reports.every(x => x.record.notes.indexOf("<") < 0 && !("email" in x.record)), "notes sanitised; no email stored in record");
  r = await fn.handler(ev("POST", { q: { op: "review" }, body: { id: b.id, decision: "verified" }, h: { "x-admin-secret": "test-admin-secret" } }));
  ok(r.statusCode === 400, "no 'verified' decision exists");
  r = await fn.handler(ev("POST", { q: { op: "review" }, body: { id: b.id, decision: "approved-user-reported", note: "ok" }, h: ck }));
  ok(r.statusCode === 401, "user cannot review");
  r = await fn.handler(ev("POST", { q: { op: "review" }, body: { id: b.id, decision: "approved-user-reported", note: "ok" }, h: { "x-admin-secret": "test-admin-secret" } }));
  const rb = JSON.parse(r.body);
  ok(r.statusCode === 200 && rb.state === "approved-user-reported" && rb.bsv_verified === false && rb.public === false, "approval stays not verified, not public");
  const RK = { "x-bsv-reviewer-key": "test-reviewer-key-0123456789abcdef0123456789" };
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: { "x-bsv-reviewer-key": "wrong-key-0123456789abcdef0123456789abcd" } }));
  ok(r.statusCode === 401, "wrong reviewer key -> 401");
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: Object.assign({}, RK, ck) }));
  const rq = JSON.parse(r.body);
  ok(r.statusCode === 200 && rq.role === "reviewer" && rq.count === 9, "reviewer key lists pending (" + r.statusCode + ")");
  ok(rq.reports.every(x => !("account_email" in x) && /^usr_|^[A-Za-z0-9_-]+$/.test(x.user_id)), "reviewer view has account ids, no submitter email");
  r = await fn.handler(ev("GET", { q: { op: "get", id: b.id }, h: RK }));
  ok(r.statusCode === 200 && JSON.parse(r.body).report.id === b.id && !("account_email" in JSON.parse(r.body).report), "reviewer can read one report without email");
  r = await fn.handler(ev("POST", { q: { op: "review" }, body: { id: rq.reports[1].id, decision: "verified" }, h: RK }));
  ok(r.statusCode === 400, "reviewer cannot set verified either");
  r = await fn.handler(ev("POST", { q: { op: "review" }, body: { id: rq.reports[1].id, decision: "rejected", note: "test" }, h: RK }));
  const rr = JSON.parse(r.body);
  ok(r.statusCode === 200 && rr.state === "rejected" && rr.bsv_verified === false, "reviewer can reject");
  r = await fn.handler(ev("GET", { q: { op: "get", id: rq.reports[1].id }, h: RK }));
  ok(JSON.parse(r.body).report.review.by === "reviewer:new-bobby", "review records reviewer actor");
  delete process.env.COMPILE_REVIEWER_KEY;
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: RK }));
  ok(r.statusCode === 401, "reviewer key without server env -> 401");
  process.env.COMPILE_REVIEWER_KEY = "short";
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: { "x-bsv-reviewer-key": "short" } }));
  ok(r.statusCode === 401, "too-short server key is never accepted");
  r = await fn.handler(ev("POST", { body: good, h: Object.assign({ origin: "https://evil.example" }, ck) }));
  ok(r.statusCode === 403, "foreign origin -> 403");
  console.log(JSON.stringify({ fn: "compile-report", checks, failures }));
  process.exit(failures ? 1 : 0);
})();
