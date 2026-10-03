"use strict";
/**
 * Compile-result intake (owner decision 2026-10-03, most conservative options):
 * - email-verified session only (same server-side session as gated sources);
 * - stored server-side in Netlify Blobs (store "compile_reports"), keyed by account id — no PII beyond the
 *   existing account email, which is NOT copied into the report (the owner queue looks it up);
 * - review queue for the owner (x-admin-secret) and BSV reviewers (owner change 2026-10-03 20:57 JST: New Bobby on the
 *   ops box and ChatGPT via New Bobby's digest) with header x-bsv-reviewer-key = env COMPILE_REVIEWER_KEY.
 *   Reviewers see account ids only, never the submitter email; only the owner view looks up the email;
 * - states: pending / approved-user-reported / rejected / needs-info. There is NO verified state and nothing
 *   here changes any catalog, compatibility or "Runtime-tested by BSV" status;
 * - no public display: no public route reads this store.
 * Installed into <deploy>/netlify/functions/ by scripts/site/install_compile_report_fn.py.
 */
var blobs = require("./_lib/blobs");
var http = require("./_lib/http");
var session = require("./_lib/session");
var identity = require("./_lib/identity");
var crypto = require("crypto");

var STORE = "compile_reports";
var TARGETS = ["pine-v6", "mql5", "ctrader", "mql4", "ctrader-python", "bookmap-python", "ninjatrader", "quantower",
  "sierra-acsil", "prorealtime", "gocharting-lipi", "motivewave", "vela", "jforex", "easylanguage", "atas", "amibroker", "thinkscript", "tradovate", "backtrader"];
var STATUSES = ["not-tried", "compiled", "compiled-warnings", "compile-failed", "ran-replay"];
var DECISIONS = ["approved-user-reported", "rejected", "needs-info"];
var PER_DAY = 10;
var REJECTED_TTL_MS = 30 * 24 * 3600 * 1000;
var ORIGINS = ["https://botshelfvampire.com", "https://www.botshelfvampire.com"];

function E(code, status) { var e = new Error(code); e.code = code; e.status = status; return e; }
function clean(v, max) {
  return String(v == null ? "" : v).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f<>]/g, " ").trim().slice(0, max);
}

function validate(b) {
  if (!b || typeof b !== "object" || Array.isArray(b)) throw E("bad_body", 400);
  var allowed = { recipe: 1, target: 1, status: 1, platform: 1, notes: 1, steps: 1, fp: 1, builder: 1 };
  Object.keys(b).forEach(function (k) { if (!allowed[k]) throw E("unknown_field", 400); });
  var r = {
    recipe: clean(b.recipe, 120),
    target: String(b.target || ""),
    status: String(b.status || ""),
    platform: clean(b.platform, 120),
    notes: clean(b.notes, 1000),
    steps: Array.isArray(b.steps) ? b.steps.slice(0, 12).map(function (x) { return x === true; }) : [],
    fp: String(b.fp || ""),
    builder: String(b.builder || "")
  };
  if (!r.recipe) throw E("recipe_required", 400);
  if (TARGETS.indexOf(r.target) < 0) throw E("bad_target", 400);
  if (STATUSES.indexOf(r.status) < 0) throw E("bad_status", 400);
  if (!/^[0-9a-f]{8}$/.test(r.fp)) throw E("bad_fp", 400);
  if (r.builder && !/^bsv-builder\.[0-9a-f]{8}\.js$/.test(r.builder)) throw E("bad_builder", 400);
  return r;
}

async function perUserLimit(userId) {
  var store = await blobs.getStore("rate_limits");
  var key = "compile_report:" + userId;
  var now = Date.now();
  var rec = await blobs.getJSON(store, key);
  if (!rec || rec.reset < now) rec = { n: 0, reset: now + 24 * 3600 * 1000 };
  if (rec.n >= PER_DAY) throw E("rate_limited", 429);
  rec.n += 1;
  await blobs.putJSON(store, key, rec);
}

async function submit(event) {
  var origin = http.header(event, "origin");
  if (origin && ORIGINS.indexOf(origin) < 0) throw E("bad_origin", 403);
  if (!/application\/json/i.test(http.header(event, "content-type"))) throw E("json_required", 415);
  var ctx = await session.requireUser(event); // email-verified session or 401
  var rec = validate(http.parseBody(event));
  var store = await blobs.getStore(STORE);
  var dupKey = "dup:" + ctx.user.id + ":" + identity.hmacHex("bsv-compile-report", [rec.recipe, rec.target, rec.fp, rec.status].join("|")).slice(0, 24);
  var dup = await blobs.getJSON(store, dupKey);
  if (dup && dup.id) return http.json(200, { ok: true, id: dup.id, duplicate: true, state: "pending_or_reviewed", public: false, bsv_verified: false });
  await perUserLimit(ctx.user.id);
  var id = identity.newId("crp");
  var report = {
    id: id, user_id: ctx.user.id, created_at: new Date().toISOString(), state: "pending",
    record: rec, self_reported: true, bsv_verified: false, public: false, review: null
  };
  await blobs.putJSON(store, "rep:" + id, report);
  await blobs.putJSON(store, dupKey, { id: id });
  return http.json(201, { ok: true, id: id, state: "pending", public: false, bsv_verified: false });
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
// Owner (x-admin-secret) or BSV reviewer (x-bsv-reviewer-key). Anything else: 401.
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
function view(r, who, email) {
  var o = { id: r.id, user_id: r.user_id, state: r.state, created_at: r.created_at, updated_at: r.updated_at, record: r.record,
    review: r.review || null, self_reported: true, bsv_verified: false, public: false };
  if (who.role === "owner") o.account_email = email;
  return o;
}

async function queue(event) {
  var who = await requireReviewer(event);
  var want = String((event.queryStringParameters || {}).state || "pending");
  var store = await blobs.getStore(STORE);
  var keys = (await blobs.listKeys(store)).filter(function (k) { return k.indexOf("rep:") === 0; });
  var rows = [], now = Date.now();
  for (var i = 0; i < keys.length; i++) {
    var r = await blobs.getJSON(store, keys[i]);
    if (!r) continue;
    if (r.state === "rejected" && r.review && Date.parse(r.review.at) + REJECTED_TTL_MS < now) { await store.delete(keys[i]); continue; }
    if (want !== "all" && r.state !== want) continue;
    var u = who.role === "owner" ? await session.getUserById(r.user_id) : null;
    rows.push(view(Object.assign({ id: keys[i].slice(4) }, r), who, u ? u.email : null));
  }
  rows.sort(function (a, b) { return a.created_at < b.created_at ? -1 : 1; });
  return http.json(200, { ok: true, role: who.role, state: want, count: rows.length, reports: rows,
    note: "Review only (owner / BSV reviewers). Not public. Approval never means verified by BSV." });
}

async function getOne(event) {
  var who = await requireReviewer(event);
  var id = String((event.queryStringParameters || {}).id || "");
  if (!/^crp_[A-Za-z0-9_-]{4,64}$/.test(id)) throw E("bad_id", 400);
  var store = await blobs.getStore(STORE);
  var r = await blobs.getJSON(store, "rep:" + id);
  if (!r) throw E("not_found", 404);
  var u = who.role === "owner" ? await session.getUserById(r.user_id) : null;
  return http.json(200, { ok: true, role: who.role, report: view(Object.assign({ id: id }, r), who, u ? u.email : null) });
}

async function review(event) {
  var who = await requireReviewer(event);
  var b = http.parseBody(event);
  var id = String(b.id || "");
  if (!/^crp_[A-Za-z0-9_-]{4,64}$/.test(id)) throw E("bad_id", 400);
  if (DECISIONS.indexOf(String(b.decision || "")) < 0) throw E("bad_decision", 400); // no "verified" decision exists
  var store = await blobs.getStore(STORE);
  var r = await blobs.getJSON(store, "rep:" + id);
  if (!r) throw E("not_found", 404);
  r.state = b.decision;
  r.review = { at: new Date().toISOString(), by: who.actor, note: clean(b.note, 500) };
  r.bsv_verified = false; r.public = false;
  await blobs.putJSON(store, "rep:" + id, r);
  return http.json(200, { ok: true, id: id, state: r.state, bsv_verified: false, public: false });
}

exports.handler = async function (event) {
  blobs.connectLambda(event);
  var method = (event.httpMethod || "GET").toUpperCase();
  var op = String((event.queryStringParameters || {}).op || "");
  try {
    if (method === "OPTIONS") return { statusCode: 204, headers: { "Cache-Control": "no-store" }, body: "" };
    if (method === "POST" && !op) return await submit(event);
    if (method === "GET" && op === "queue") return await queue(event);
    if (method === "GET" && op === "get") return await getOne(event);
    if (method === "POST" && op === "review") return await review(event);
    return http.json(405, { ok: false, reason: "method_not_allowed" });
  } catch (e) {
    var code = (e && e.code) || "error";
    var status = (e && e.status) || (code === "unauthorized" ? 401 : code === "admin-unconfigured" ? 501 : code === "durable_storage_unavailable" ? 503 : 400);
    return http.json(status, { ok: false, reason: code });
  }
};
exports._test = { validate: validate, TARGETS: TARGETS, STATUSES: STATUSES, DECISIONS: DECISIONS };
