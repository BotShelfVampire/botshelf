"use strict";
/**
 * Request Market intake (Issue #6, tranche 1). Schema: /schemas/demand-request-v0.1.json.
 * - Submitting needs an email-verified session (same server-side session as gated sources). Auth is not changed.
 * - Stored in Netlify Blobs (store "demand_requests"), keyed by request id; the account email is never copied
 *   into the record and is never public. Contact goes through BSV only, if the requester asked for it.
 * - Every request starts "pending". Nothing is public until a reviewer approves a request whose author chose
 *   PUBLIC. PRIVATE requests are never listed.
 * - The public list and counts are read from the store only: no seeded, sample or estimated requests.
 *   Willingness-to-pay is what the requester typed; it is not escrow, a payment or a promise.
 * - No wallet, price, split, payout, auth or entitlement logic here.
 * Installed into <deploy>/netlify/functions/ by scripts/site/install_compile_report_fn.py.
 */
var blobs = require("./_lib/blobs");
var http = require("./_lib/http");
var session = require("./_lib/session");
var identity = require("./_lib/identity");
var crypto = require("crypto");

var STORE = "demand_requests";
var DOMAINS = ["trading", "ai-workflows", "robotics", "space", "quantum", "biotech", "bci", "medical", "industrial",
  "data-workflows", "robot-pilot", "other"];
var DECISIONS = ["approve", "reject", "needs-info", "claimed", "fulfilled", "closed"];
var PER_DAY = 5;
var ORIGINS = ["https://botshelfvampire.com", "https://www.botshelfvampire.com"];

function E(code, status) { var e = new Error(code); e.code = code; e.status = status; return e; }
function clean(v, max) {
  return String(v == null ? "" : v).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}
function list(v, maxN, maxLen) {
  if (v == null) return [];
  if (!Array.isArray(v)) throw E("bad_list", 400);
  return v.slice(0, maxN).map(function (x) { return clean(x, maxLen); }).filter(Boolean);
}
function num(v) {
  if (v == null || v === "") return null;
  var n = Number(v);
  if (!isFinite(n) || n < 0 || n > 1000000) throw E("bad_wtp", 400);
  return Math.round(n * 100) / 100;
}

function validate(b) {
  if (!b || typeof b !== "object" || Array.isArray(b)) throw E("bad_body", 400);
  var allowed = { job: 1, domains: 1, platforms: 1, desiredInputs: 1, desiredOutputs: 1, freeSolutionAcceptable: 1,
    willingnessToPay: 1, deadline: 1, visibility: 1, contactViaBsv: 1 };
  Object.keys(b).forEach(function (k) { if (!allowed[k]) throw E("unknown_field", 400); });
  var r = {
    job: clean(b.job, 2000),
    domains: list(b.domains, 4, 40),
    platforms: list(b.platforms, 8, 60),
    desiredInputs: list(b.desiredInputs, 8, 120),
    desiredOutputs: list(b.desiredOutputs, 8, 120),
    freeSolutionAcceptable: b.freeSolutionAcceptable === true ? true : b.freeSolutionAcceptable === false ? false : null,
    willingnessToPay: null,
    deadline: null,
    visibility: String(b.visibility || ""),
    contactViaBsv: b.contactViaBsv === true
  };
  if (r.job.length < 20) throw E("job_too_short", 400);
  if (!r.domains.length || r.domains.some(function (d) { return DOMAINS.indexOf(d) < 0; })) throw E("bad_domain", 400);
  if (["PUBLIC", "PRIVATE"].indexOf(r.visibility) < 0) throw E("bad_visibility", 400);
  if (b.willingnessToPay != null) {
    var w = b.willingnessToPay;
    if (typeof w !== "object" || Array.isArray(w)) throw E("bad_wtp", 400);
    Object.keys(w).forEach(function (k) { if (["min", "max", "currency"].indexOf(k) < 0) throw E("bad_wtp", 400); });
    var mn = num(w.min), mx = num(w.max);
    if (w.currency != null && w.currency !== "USDT") throw E("bad_wtp", 400);
    if (mn != null && mx != null && mx < mn) throw E("bad_wtp", 400);
    if (mn != null || mx != null) r.willingnessToPay = { min: mn, max: mx, currency: "USDT" };
  }
  if (b.deadline != null && b.deadline !== "") {
    var d = String(b.deadline);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d) || isNaN(Date.parse(d + "T00:00:00Z"))) throw E("bad_deadline", 400);
    r.deadline = d + "T00:00:00Z";
  }
  return r;
}

async function perUserLimit(userId) {
  var store = await blobs.getStore("rate_limits");
  var key = "demand_request:" + userId;
  var now = Date.now();
  var rec = await blobs.getJSON(store, key);
  if (!rec || rec.reset < now) rec = { n: 0, reset: now + 24 * 3600 * 1000 };
  if (rec.n >= PER_DAY) throw E("rate_limited", 429);
  rec.n += 1;
  await blobs.putJSON(store, key, rec);
}

// Public shape = schema bsv-demand-request v0.1 (no user id, no email, no review notes).
function publicView(r) {
  return {
    schemaVersion: "0.1", requestId: r.id, job: r.record.job, domains: r.record.domains, platforms: r.record.platforms,
    desiredInputs: r.record.desiredInputs, desiredOutputs: r.record.desiredOutputs,
    freeSolutionAcceptable: r.record.freeSolutionAcceptable, willingnessToPay: r.record.willingnessToPay,
    deadline: r.record.deadline, visibility: "PUBLIC", status: r.status, createdAt: r.created_at,
    fulfilledByCapabilityId: r.fulfilled_by || null
  };
}

async function submit(event) {
  var origin = http.header(event, "origin");
  if (origin && ORIGINS.indexOf(origin) < 0) throw E("bad_origin", 403);
  if (!/application\/json/i.test(http.header(event, "content-type"))) throw E("json_required", 415);
  var ctx = await session.requireUser(event); // email-verified session or 401
  var rec = validate(http.parseBody(event));
  var store = await blobs.getStore(STORE);
  var dupKey = "dup:" + ctx.user.id + ":" + identity.hmacHex("bsv-demand-request", rec.job.toLowerCase()).slice(0, 24);
  var dup = await blobs.getJSON(store, dupKey);
  if (dup && dup.id) return http.json(200, { ok: true, id: dup.id, duplicate: true, state: "pending_or_reviewed", public: false });
  await perUserLimit(ctx.user.id);
  var id = identity.newId("req");
  var r = { id: id, user_id: ctx.user.id, created_at: new Date().toISOString(), state: "pending", status: "OPEN",
    record: rec, public: false, review: null, fulfilled_by: null };
  await blobs.putJSON(store, "req:" + id, r);
  await blobs.putJSON(store, dupKey, { id: id });
  return http.json(201, { ok: true, id: id, state: "pending", public: false, visibility: rec.visibility });
}

async function all(store) {
  var keys = (await blobs.listKeys(store)).filter(function (k) { return k.indexOf("req:") === 0; });
  var rows = [];
  for (var i = 0; i < keys.length; i++) { var r = await blobs.getJSON(store, keys[i]); if (r) rows.push(r); }
  rows.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
  return rows;
}

async function publicList() {
  var store = await blobs.getStore(STORE);
  var rows = await all(store);
  var pub = rows.filter(function (r) { return r.public === true && r.record.visibility === "PUBLIC" && r.state === "approved"; });
  var received = rows.filter(function (r) { return r.state !== "rejected"; }).length;
  return http.json(200, {
    ok: true, schema: "https://botshelfvampire.com/schemas/demand-request-v0.1.json", generatedAt: new Date().toISOString(),
    counts: { received: received, published: pub.length,
      publishedOpen: pub.filter(function (r) { return r.status === "OPEN"; }).length,
      publishedWithStatedBudget: pub.filter(function (r) { return !!r.record.willingnessToPay; }).length },
    note: "Real requests only. Counts are read from the request store; nothing is seeded or estimated. A stated budget is not escrow or a payment.",
    requests: pub.map(publicView)
  }, { "Cache-Control": "public, max-age=60" });
}

// Builder opportunity signals = schema bsv-opportunity-signal v0.1, aggregated from APPROVED PUBLIC requests only.
// One signal per (first domain, first platform) group; FULFILLED requests form FULFILLED_REQUEST signals. No user ids,
// no emails, no estimates: count/uniqueActors are counted rows, explicitWtp only from budgets the requesters stated.
function signalSlug(s) { return String(s || "any").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "any"; }
async function signals() {
  var store = await blobs.getStore(STORE);
  var rows = (await all(store)).filter(function (r) { return r.public === true && r.record.visibility === "PUBLIC" && r.state === "approved"; });
  var now = new Date().toISOString(), groups = {};
  rows.forEach(function (r) {
    var type = r.status === "FULFILLED" ? "FULFILLED_REQUEST" : "REQUEST";
    var dom = r.record.domains[0], plat = (r.record.platforms || [])[0] || null;
    var key = type + "|" + dom + "|" + (plat || "");
    var g = groups[key] || (groups[key] = { type: type, dom: dom, plat: plat, rows: [] });
    g.rows.push(r);
  });
  var out = Object.keys(groups).sort().map(function (k) {
    var g = groups[k], actors = {}, w = g.rows.filter(function (r) { return !!r.record.willingnessToPay; });
    g.rows.forEach(function (r) { actors[r.user_id] = 1; });
    var mins = w.map(function (r) { return r.record.willingnessToPay.min; }).filter(function (v) { return v != null; });
    var maxs = w.map(function (r) { return r.record.willingnessToPay.max; }).filter(function (v) { return v != null; });
    var start = g.rows.map(function (r) { return r.created_at; }).sort()[0];
    return {
      schemaVersion: "0.1",
      signalId: "sig_" + (g.type === "REQUEST" ? "req" : "ful") + "_" + signalSlug(g.dom) + "_" + signalSlug(g.plat),
      signalType: g.type,
      jobKey: "domain:" + g.dom + (g.plat ? " platform:" + g.plat : ""),
      sector: g.dom, platform: g.plat,
      count: g.rows.length, uniqueActors: Object.keys(actors).length,
      windowStart: start, windowEnd: now, publicEligible: true,
      explicitWtp: w.length ? { count: w.length, currency: "USDT", min: mins.length ? Math.min.apply(null, mins) : null, max: maxs.length ? Math.max.apply(null, maxs) : null } : null,
      sourceRefs: g.rows.map(function (r) { return "https://botshelfvampire.com/requests/#" + r.id; }),
      privacyNotes: ["Aggregated from approved public requests only; no account ids or emails.", "A stated budget is not escrow or a payment."]
    };
  });
  return http.json(200, {
    ok: true, schema: "https://botshelfvampire.com/schemas/opportunity-signal-v0.1.json", generatedAt: now,
    collected: { REQUEST: true, FULFILLED_REQUEST: true, NO_RESULT_SEARCH: false, MISSING_PLATFORM_VARIANT: false, REMIX: false },
    note: "Signals are counted from approved public requests. Searches, page views, platform-variant demand and remixes are not logged on this site, so those signal types are not produced.",
    signals: out
  }, { "Cache-Control": "public, max-age=60" });
}

async function mine(event) {
  var ctx = await session.requireUser(event);
  var store = await blobs.getStore(STORE);
  var rows = (await all(store)).filter(function (r) { return r.user_id === ctx.user.id; });
  return http.json(200, { ok: true, requests: rows.map(function (r) {
    return { id: r.id, state: r.state, status: r.status, created_at: r.created_at, public: r.public === true, record: r.record,
      review_note: r.review && r.review.note_to_requester ? r.review.note_to_requester : null };
  }) }, { "Cache-Control": "no-store" });
}

function header(event, name) {
  var h = event.headers || {};
  for (var k in h) if (k.toLowerCase() === name) return String(h[k] || "");
  return "";
}
function sameSecret(a, b) {
  var x = crypto.createHash("sha256").update(String(a)).digest(), y = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(x, y);
}
async function requireReviewer(event) {
  var key = header(event, "x-bsv-reviewer-key");
  if (key) {
    var want = String(process.env.COMPILE_REVIEWER_KEY || "");
    if (want.length >= 32 && sameSecret(key, want)) return { role: "reviewer", actor: "reviewer:new-bobby" };
    throw E("unauthorized", 401);
  }
  if (header(event, "x-admin-secret")) {
    var admin = await session.requireAdmin(event);
    return { role: "owner", actor: admin.actor || "owner" };
  }
  throw E("unauthorized", 401);
}

async function queue(event) {
  var who = await requireReviewer(event);
  var want = String((event.queryStringParameters || {}).state || "pending");
  var store = await blobs.getStore(STORE);
  var rows = (await all(store)).filter(function (r) { return want === "all" || r.state === want; });
  return http.json(200, { ok: true, role: who.role, state: want, count: rows.length, requests: rows.map(function (r) {
    return { id: r.id, user_id: r.user_id, state: r.state, status: r.status, created_at: r.created_at, public: r.public === true,
      record: r.record, review: r.review };
  }), note: "Review only. Approve publishes only requests whose author chose PUBLIC." }, { "Cache-Control": "no-store" });
}

async function review(event) {
  var who = await requireReviewer(event);
  var b = http.parseBody(event);
  var id = String(b.id || "");
  if (!/^req_[a-z0-9]{8,64}$/.test(id)) throw E("bad_id", 400);
  var d = String(b.decision || "");
  if (DECISIONS.indexOf(d) < 0) throw E("bad_decision", 400);
  var store = await blobs.getStore(STORE);
  var r = await blobs.getJSON(store, "req:" + id);
  if (!r) throw E("not_found", 404);
  if (d === "approve") { r.state = "approved"; r.public = r.record.visibility === "PUBLIC"; }
  else if (d === "reject") { r.state = "rejected"; r.public = false; }
  else if (d === "needs-info") { r.state = "needs-info"; r.public = false; }
  else {
    if (r.state !== "approved") throw E("not_approved", 409);
    r.status = d === "claimed" ? "CLAIMED" : d === "fulfilled" ? "FULFILLED" : "CLOSED";
    if (d === "fulfilled") r.fulfilled_by = clean(b.capabilityId, 120) || null;
  }
  r.review = { at: new Date().toISOString(), by: who.actor, note: clean(b.note, 500), note_to_requester: clean(b.noteToRequester, 500) || null };
  await blobs.putJSON(store, "req:" + id, r);
  return http.json(200, { ok: true, id: id, state: r.state, status: r.status, public: r.public });
}

exports.handler = async function (event) {
  blobs.connectLambda(event);
  var method = (event.httpMethod || "GET").toUpperCase();
  var op = String((event.queryStringParameters || {}).op || "");
  try {
    if (method === "OPTIONS") return { statusCode: 204, headers: { "Cache-Control": "no-store" }, body: "" };
    if (method === "POST" && !op) return await submit(event);
    if (method === "GET" && op === "public") return await publicList();
    if (method === "GET" && op === "signals") return await signals();
    if (method === "GET" && op === "mine") return await mine(event);
    if (method === "GET" && op === "queue") return await queue(event);
    if (method === "POST" && op === "review") return await review(event);
    return http.json(405, { ok: false, reason: "method_not_allowed" });
  } catch (e) {
    var code = (e && e.code) || "error";
    var status = (e && e.status) || (code === "unauthorized" ? 401 : code === "admin-unconfigured" ? 501 : code === "durable_storage_unavailable" ? 503 : 400);
    return http.json(status, { ok: false, reason: code });
  }
};
exports._test = { validate: validate, DOMAINS: DOMAINS, DECISIONS: DECISIONS, publicView: publicView };
