// Offline test of netlify/functions/demand-request.js with the in-memory store (COMMERCE_TEST=1).
// Usage: node scripts/site/test_demand_request_fn.js <deploy root>
process.env.COMMERCE_TEST = "1";
process.env.COMPILE_REVIEWER_KEY = "test-reviewer-key-0123456789abcdef0123456789";
const path = require("path");
const root = path.resolve(process.argv[2]);
const fn = require(path.join(root, "netlify/functions/demand-request.js"));
const session = require(path.join(root, "netlify/functions/_lib/session.js"));
let checks = 0, failures = 0;
const ok = (c, m) => { checks++; if (!c) { failures++; console.error("FAIL", m); } };
const ev = (method, opts = {}) => ({ httpMethod: method, path: "/.netlify/functions/demand-request", queryStringParameters: opts.q || {},
  headers: Object.assign({ "content-type": "application/json" }, opts.h || {}), body: opts.body === undefined ? undefined : (typeof opts.body === "string" ? opts.body : JSON.stringify(opts.body)) });
const J = r => JSON.parse(r.body);
const good = { job: "Alert me when a session high breaks on two timeframes at once", domains: ["trading"], platforms: ["TradingView"],
  desiredInputs: ["OHLC"], desiredOutputs: ["alert"], freeSolutionAcceptable: true, willingnessToPay: { min: 20, max: 50, currency: "USDT" },
  deadline: "2026-12-31", visibility: "PUBLIC", contactViaBsv: true };
const RK = { "x-bsv-reviewer-key": process.env.COMPILE_REVIEWER_KEY };
(async () => {
  let r = await fn.handler(ev("GET", { q: { op: "public" } }));
  let j = J(r);
  ok(r.statusCode === 200 && j.requests.length === 0 && j.counts.received === 0 && j.counts.published === 0, "empty store -> real zero counts, no seeded rows");
  r = await fn.handler(ev("POST", { body: good }));
  ok(r.statusCode === 401, "anonymous POST -> 401 (" + r.statusCode + ")");
  const u = await session.upsertUser({ email: "req1@example.com" });
  let threw = false; try { await session.createSession(u); } catch (e) { threw = e.code === "email_unverified"; }
  ok(threw, "unverified account gets no session");
  u.email_verified = true; await session.putUser(u);
  const ck = { cookie: "botshelf_sid=" + (await session.createSession(u)).id };
  r = await fn.handler(ev("POST", { body: good, h: Object.assign({ "content-type": "text/plain" }, ck) }));
  ok(r.statusCode === 415, "non-JSON -> 415");
  r = await fn.handler(ev("POST", { body: good, h: Object.assign({ origin: "https://evil.example" }, ck) }));
  ok(r.statusCode === 403, "foreign origin -> 403");
  for (const [k, v] of [["email", "x@y"], ["job", "too short"], ["domains", ["nope"]], ["domains", []], ["visibility", "OPEN"],
    ["willingnessToPay", { min: 50, max: 10 }], ["willingnessToPay", { min: -1 }], ["willingnessToPay", { min: 1, currency: "BTC" }],
    ["deadline", "tomorrow"], ["platforms", "TradingView"]]) {
    r = await fn.handler(ev("POST", { body: Object.assign({}, good, { [k]: v }), h: ck }));
    ok(r.statusCode === 400, "bad " + k + " rejected (" + r.statusCode + ")");
  }
  r = await fn.handler(ev("POST", { body: Object.assign({}, good, { job: good.job + " <script>x</script>" }), h: ck }));
  j = J(r); ok(r.statusCode === 201 && /^req_[a-z0-9]+$/.test(j.id) && j.state === "pending" && j.public === false, "verified submit -> 201 pending, not public");
  const id1 = j.id;
  r = await fn.handler(ev("POST", { body: Object.assign({}, good, { job: good.job + " <script>x</script>" }), h: ck }));
  ok(J(r).duplicate === true && J(r).id === id1, "duplicate job -> same id");
  r = await fn.handler(ev("POST", { body: Object.assign({}, good, { job: "Private: a robot teleop checklist for my own lab only", domains: ["robot-pilot"], visibility: "PRIVATE", willingnessToPay: null }), h: ck }));
  const id2 = J(r).id; ok(r.statusCode === 201, "private submit -> 201");
  r = await fn.handler(ev("GET", { q: { op: "public" } })); j = J(r);
  ok(j.requests.length === 0 && j.counts.received === 2 && j.counts.published === 0, "pending requests are counted as received but not listed");
  r = await fn.handler(ev("GET", { q: { op: "queue" } })); ok(r.statusCode === 401, "queue without key -> 401");
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: { "x-bsv-reviewer-key": "wrong-key-wrong-key-wrong-key-wrong" } })); ok(r.statusCode === 401, "queue wrong key -> 401");
  r = await fn.handler(ev("GET", { q: { op: "queue" }, h: RK })); j = J(r); ok(r.statusCode === 200 && j.count === 2, "reviewer queue lists 2 pending");
  ok(!JSON.stringify(j).includes("req1@example.com"), "queue never contains the account email");
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id: id1, decision: "fulfilled" } })); ok(r.statusCode === 409, "cannot fulfil before approval");
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id: id1, decision: "verified" } })); ok(r.statusCode === 400, "unknown decision rejected");
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id: id1, decision: "approve" } })); ok(J(r).public === true, "approve PUBLIC -> public");
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id: id2, decision: "approve" } })); ok(J(r).public === false, "approve PRIVATE -> still not public");
  r = await fn.handler(ev("GET", { q: { op: "public" } })); j = J(r);
  ok(j.requests.length === 1 && j.requests[0].requestId === id1 && j.counts.published === 1 && j.counts.publishedWithStatedBudget === 1, "public list = only the approved PUBLIC request");
  const pv = j.requests[0], s = JSON.stringify(j);
  ok(!s.includes("req1@example.com") && !s.includes(u.id) && !("user_id" in pv) && !("review" in pv), "public view has no email, user id or review notes");
  ok(!/<script>/i.test(pv.job), "markup stripped from job text");
  ok(pv.schemaVersion === "0.1" && pv.visibility === "PUBLIC" && pv.status === "OPEN" && pv.deadline === "2026-12-31T00:00:00Z", "public view follows schema v0.1");
  ok(!s.includes("robot teleop checklist"), "private request text never public");
  const fs = require("fs"), schemaP = path.join(root, "site/schemas/demand-request-v0.1.json");
  if (fs.existsSync(schemaP)) {
    const sc = JSON.parse(fs.readFileSync(schemaP, "utf8"));
    for (const k of sc.required) ok(k in pv, "public view has required schema field " + k);
    for (const k of Object.keys(pv)) ok(k in sc.properties, "public view field in schema: " + k);
    ok(/^req_[a-z0-9_-]+$/.test(pv.requestId) && pv.job.length >= 20, "requestId/job match schema pattern/length");
  }
  r = await fn.handler(ev("POST", { q: { op: "review" }, h: RK, body: { id: id1, decision: "fulfilled", capabilityId: "bsv-recipe-session-breakout" } }));
  ok(J(r).status === "FULFILLED", "fulfilled status after approval");
  r = await fn.handler(ev("GET", { q: { op: "mine" } })); ok(r.statusCode === 401, "mine without session -> 401");
  r = await fn.handler(ev("GET", { q: { op: "mine" }, h: ck })); j = J(r); ok(j.requests.length === 2, "mine lists own 2 requests");
  const u2 = await session.upsertUser({ email: "req2@example.com" }); u2.email_verified = true; await session.putUser(u2);
  const ck2 = { cookie: "botshelf_sid=" + (await session.createSession(u2)).id };
  r = await fn.handler(ev("GET", { q: { op: "mine" }, h: ck2 })); ok(J(r).requests.length === 0, "other user sees none of them");
  let last = 0; for (let i = 0; i < 6; i++) { r = await fn.handler(ev("POST", { body: Object.assign({}, good, { job: "Rate limit probe number " + i + " for the daily cap" }), h: ck2 })); last = r.statusCode; }
  ok(last === 429, "6th request in a day -> 429");
  console.log(JSON.stringify({ fn: "demand-request", checks, failures }));
  process.exit(failures ? 1 : 0);
})();
