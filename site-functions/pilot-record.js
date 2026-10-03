"use strict";
/**
 * Robot Pilot practice-record intake (Issue #7; owner decision 2026-10-04 00:09 JST, conservative):
 * - email-verified session only (same session as gated sources); auth unchanged;
 * - private storage (Netlify Blobs store "pilot_records"); no public route returns a record, only aggregate counts;
 * - the pilot id is replaced server-side by a stable pseudonymous id derived from the account (HMAC), the account
 *   email is never copied into the record;
 * - SIMULATION only; review status starts UNREVIEWED; the practice-record status is SELF_REPORTED and stays
 *   SELF_REPORTED whatever the review says (no auto-promotion); a review is not a licence, a certification or
 *   permission to operate real hardware;
 * - reviewers: owner (x-admin-secret) or New Bobby (x-bsv-reviewer-key = env COMPILE_REVIEWER_KEY). ChatGPT sees the
 *   digest only.
 * Installed into <deploy>/netlify/functions/ by scripts/site/install_compile_report_fn.py.
 */
var blobs = require("./_lib/blobs");
var http = require("./_lib/http");
var session = require("./_lib/session");
var identity = require("./_lib/identity");
var crypto = require("crypto");

var STORE = "pilot_records";
var DECISIONS = ["reviewed", "needs-info", "rejected"];
var PER_DAY = 10;
var ORIGINS = ["https://botshelfvampire.com", "https://www.botshelfvampire.com"];
var NOT_A_LICENCE = "Self-reported practice record. Not a licence, a certification or permission to operate real hardware.";

function E(code, status) { var e = new Error(code); e.code = code; e.status = status; return e; }
function clean(v, max) {
  return String(v == null ? "" : v).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f<>]/g, " ").trim().slice(0, max);
}
function opt(v, max) { var s = clean(v, max); return s ? s : null; }
function int0(v, name) { if (!Number.isInteger(v) || v < 0 || v > 100000) throw E("bad_" + name, 400); return v; }
function dt(v, name, required) {
  if (v == null || v === "") { if (required) throw E("bad_" + name, 400); return null; }
  var s = String(v);
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/.test(s) || isNaN(Date.parse(s))) throw E("bad_" + name, 400);
  return s;
}

function validate(b) {
  if (!b || typeof b !== "object" || Array.isArray(b)) throw E("bad_body", 400);
  Object.keys(b).forEach(function (k) { if (k !== "evidence") throw E("unknown_field", 400); });
  var e = b.evidence;
  if (!e || typeof e !== "object" || Array.isArray(e)) throw E("bad_evidence", 400);
  var allowed = { schemaVersion: 1, evidenceId: 1, pilotId: 1, taskId: 1, environment: 1, runtime: 1, runtimeVersion: 1, sourceRevision: 1,
    embodiment: 1, inputDevice: 1, startedAt: 1, endedAt: 1, episodes: 1, safetyEvents: 1, dataArtifacts: 1, metrics: 1, review: 1 };
  Object.keys(e).forEach(function (k) { if (!allowed[k]) throw E("unknown_field", 400); });
  if (e.schemaVersion !== "0.1") throw E("bad_schemaVersion", 400);
  if (!/^teleop_[a-z0-9_-]{8,64}$/.test(String(e.evidenceId || ""))) throw E("bad_evidenceId", 400);
  if (e.environment !== "SIMULATION") throw E("simulation_only", 400);
  var ep = e.episodes;
  if (!ep || typeof ep !== "object" || Array.isArray(ep)) throw E("bad_episodes", 400);
  Object.keys(ep).forEach(function (k) { if (["attempted", "successful", "failed", "recoveryEpisodes"].indexOf(k) < 0) throw E("bad_episodes", 400); });
  var episodes = { attempted: int0(ep.attempted, "episodes"), successful: int0(ep.successful, "episodes"), failed: int0(ep.failed, "episodes") };
  if (ep.recoveryEpisodes != null) episodes.recoveryEpisodes = int0(ep.recoveryEpisodes, "episodes");
  if (episodes.successful + episodes.failed > episodes.attempted) throw E("bad_episodes", 400);
  var r = {
    schemaVersion: "0.1", evidenceId: String(e.evidenceId), taskId: clean(e.taskId, 160), environment: "SIMULATION",
    runtime: clean(e.runtime, 160), runtimeVersion: opt(e.runtimeVersion, 80), sourceRevision: opt(e.sourceRevision, 120),
    embodiment: clean(e.embodiment, 160), inputDevice: opt(e.inputDevice, 160),
    startedAt: dt(e.startedAt, "startedAt", true), endedAt: dt(e.endedAt, "endedAt", false), episodes: episodes,
    safetyEvents: (Array.isArray(e.safetyEvents) ? e.safetyEvents : []).slice(0, 50).map(function (x) { return clean(x, 300); }).filter(Boolean),
    dataArtifacts: (Array.isArray(e.dataArtifacts) ? e.dataArtifacts : []).slice(0, 5).map(function (a) {
      if (!a || typeof a !== "object") throw E("bad_dataArtifacts", 400);
      var sha = a.sha256 == null ? null : String(a.sha256).toLowerCase();
      if (sha !== null && !/^[0-9a-f]{64}$/.test(sha)) throw E("bad_dataArtifacts", 400);
      var ref = clean(a.uriOrRef, 500); if (!ref) throw E("bad_dataArtifacts", 400);
      return { type: clean(a.type, 40) || "HDF5", uriOrRef: ref, sha256: sha };
    }),
    metrics: {},
    review: { status: "UNREVIEWED", reviewerId: null, reviewedAt: null, note: opt(e.review && e.review.note, 2000) }
  };
  if (!r.taskId || !r.runtime || !r.embodiment) throw E("missing_required", 400);
  if (r.endedAt && r.endedAt < r.startedAt) throw E("bad_endedAt", 400);
  var m = e.metrics && typeof e.metrics === "object" && !Array.isArray(e.metrics) ? e.metrics : {};
  Object.keys(m).slice(0, 80).forEach(function (k) {
    var key = clean(k, 80), v = m[k];
    if (!/^[A-Za-z0-9_.:-]+$/.test(key)) return;
    if (typeof v === "boolean" || v === null || (typeof v === "number" && isFinite(v))) r.metrics[key] = v;
    else if (typeof v === "string") r.metrics[key] = clean(v, 120);
  });
  return r;
}

function pilotIdFor(userId) { return "pilot_" + identity.hmacHex("bsv-pilot-id", String(userId)).slice(0, 20); }

async function perUserLimit(userId) {
  var store = await blobs.getStore("rate_limits");
  var key = "pilot_record:" + userId, now = Date.now();
  var rec = await blobs.getJSON(store, key);
  if (!rec || rec.reset < now) rec = { n: 0, reset: now + 24 * 3600 * 1000 };
  if (rec.n >= PER_DAY) throw E("rate_limited", 429);
  rec.n += 1;
  await blobs.putJSON(store, key, rec);
}

function practiceRecord(r) {
  var e = r.evidence;
  return { schemaVersion: "0.1", pilotId: e.pilotId, visibility: "PRIVATE", practiceRecords: [{
    recordId: "rec_" + e.evidenceId.slice(7), taskId: e.taskId, runtime: e.runtime, runtimeVersion: e.runtimeVersion, embodiment: e.embodiment,
    inputDevice: e.inputDevice, environment: "SIMULATION", status: "SELF_REPORTED", evidenceIds: [e.evidenceId],
    limitations: ["Self-reported; " + (e.review.status === "REVIEWED" ? "evidence looked at by a BSV reviewer, not verified by a BSV run" : "not reviewed by BSV"),
      "Simulation only; no permission to operate real hardware", "Not a government licence or manufacturer certification"] }] };
}

async function submit(event) {
  var origin = http.header(event, "origin");
  if (origin && ORIGINS.indexOf(origin) < 0) throw E("bad_origin", 403);
  if (!/application\/json/i.test(http.header(event, "content-type"))) throw E("json_required", 415);
  if (String(event.body || "").length > 40000) throw E("too_large", 413);
  var ctx = await session.requireUser(event);
  var ev = validate(http.parseBody(event));
  ev.pilotId = pilotIdFor(ctx.user.id);
  var store = await blobs.getStore(STORE);
  var key = "rec:" + ev.evidenceId;
  var have = await blobs.getJSON(store, key);
  if (have) {
    if (have.user_id !== ctx.user.id) throw E("evidence_id_taken", 409);
    return http.json(200, { ok: true, id: ev.evidenceId, duplicate: true, state: have.state, status: "SELF_REPORTED", public: false });
  }
  await perUserLimit(ctx.user.id);
  var r = { id: ev.evidenceId, user_id: ctx.user.id, created_at: new Date().toISOString(), state: "pending", evidence: ev,
    record_status: "SELF_REPORTED", public: false, review: null };
  await blobs.putJSON(store, key, r);
  return http.json(201, { ok: true, id: ev.evidenceId, pilotId: ev.pilotId, state: "pending", status: "SELF_REPORTED", public: false, note: NOT_A_LICENCE });
}

async function all(store) {
  var keys = (await blobs.listKeys(store)).filter(function (k) { return k.indexOf("rec:") === 0; });
  var rows = [];
  for (var i = 0; i < keys.length; i++) { var r = await blobs.getJSON(store, keys[i]); if (r) rows.push(r); }
  rows.sort(function (a, b) { return a.created_at < b.created_at ? -1 : 1; });
  return rows;
}

async function stats() {
  var rows = await all(await blobs.getStore(STORE));
  return http.json(200, { ok: true, counts: { received: rows.filter(function (r) { return r.state !== "rejected"; }).length,
    reviewed: rows.filter(function (r) { return r.state === "reviewed"; }).length }, records: "private",
    note: "Aggregate counts only, read from the store. Reviewed means a BSV reviewer looked at the evidence; the record stays SELF_REPORTED. " + NOT_A_LICENCE },
    { "Cache-Control": "public, max-age=60" });
}

async function mine(event) {
  var ctx = await session.requireUser(event);
  var rows = (await all(await blobs.getStore(STORE))).filter(function (r) { return r.user_id === ctx.user.id; });
  return http.json(200, { ok: true, records: rows.map(function (r) { return { id: r.id, state: r.state, created_at: r.created_at, evidence: r.evidence,
    practiceRecord: practiceRecord(r), review_note: r.review && r.review.note_to_pilot ? r.review.note_to_pilot : null }; }) }, { "Cache-Control": "no-store" });
}

function header(event, name) { var h = event.headers || {}; for (var k in h) if (k.toLowerCase() === name) return String(h[k] || ""); return ""; }
function sameSecret(a, b) { var x = crypto.createHash("sha256").update(String(a)).digest(), y = crypto.createHash("sha256").update(String(b)).digest(); return crypto.timingSafeEqual(x, y); }
async function requireReviewer(event) {
  var key = header(event, "x-bsv-reviewer-key");
  if (key) {
    var want = String(process.env.COMPILE_REVIEWER_KEY || "");
    if (want.length >= 32 && sameSecret(key, want)) return { role: "reviewer", actor: "reviewer:new-bobby" };
    throw E("unauthorized", 401);
  }
  if (header(event, "x-admin-secret")) { var admin = await session.requireAdmin(event); return { role: "owner", actor: admin.actor || "owner" }; }
  throw E("unauthorized", 401);
}

async function queue(event) {
  var who = await requireReviewer(event);
  var want = String((event.queryStringParameters || {}).state || "pending");
  var rows = (await all(await blobs.getStore(STORE))).filter(function (r) { return want === "all" || r.state === want; });
  return http.json(200, { ok: true, role: who.role, state: want, count: rows.length, records: rows.map(function (r) {
    return { id: r.id, user_id: r.user_id, state: r.state, created_at: r.created_at, evidence: r.evidence, record_status: "SELF_REPORTED", review: r.review };
  }), note: "Private review only. Decisions: reviewed / needs-info / rejected. Record status stays SELF_REPORTED. " + NOT_A_LICENCE }, { "Cache-Control": "no-store" });
}

async function review(event) {
  var who = await requireReviewer(event);
  var b = http.parseBody(event);
  var id = String(b.id || "");
  if (!/^teleop_[a-z0-9_-]{8,64}$/.test(id)) throw E("bad_id", 400);
  if (DECISIONS.indexOf(String(b.decision || "")) < 0) throw E("bad_decision", 400);
  var store = await blobs.getStore(STORE);
  var r = await blobs.getJSON(store, "rec:" + id);
  if (!r) throw E("not_found", 404);
  var now = new Date().toISOString();
  r.state = b.decision;
  r.evidence.review = { status: b.decision === "reviewed" ? "REVIEWED" : b.decision === "needs-info" ? "NEEDS_INFO" : "REJECTED",
    reviewerId: who.actor, reviewedAt: now.replace(/\.\d{3}Z$/, "Z"), note: r.evidence.review && r.evidence.review.note || null };
  r.record_status = "SELF_REPORTED"; r.public = false;
  r.review = { at: now, by: who.actor, note: clean(b.note, 500), note_to_pilot: clean(b.noteToPilot, 500) || null };
  await blobs.putJSON(store, "rec:" + id, r);
  return http.json(200, { ok: true, id: id, state: r.state, record_status: "SELF_REPORTED", public: false });
}

exports.handler = async function (event) {
  blobs.connectLambda(event);
  var method = (event.httpMethod || "GET").toUpperCase();
  var op = String((event.queryStringParameters || {}).op || "");
  try {
    if (method === "OPTIONS") return { statusCode: 204, headers: { "Cache-Control": "no-store" }, body: "" };
    if (method === "POST" && !op) return await submit(event);
    if (method === "GET" && op === "stats") return await stats();
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
exports._test = { validate: validate, practiceRecord: practiceRecord, DECISIONS: DECISIONS };
