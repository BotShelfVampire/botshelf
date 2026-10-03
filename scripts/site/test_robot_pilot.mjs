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
ok(/Practice records reviewed by BSV<\/span><span[^>]*>[^<]*<\/span><b>0<\/b>/.test(html), "page: reviewed records = 0");
ok(/BSV has not run this curriculum itself yet/.test(html) && /Not a government licence/.test(html) && /Not permission to operate real hardware/.test(html), "page: boundary statements");
ok(!/certified pilot|licensed pilot|BSV verified/i.test(html), "page: no licence/certification claims");
ok(/href="\/requests\/\?area=robot-pilot&amp;kind=mission"/.test(html), "page: mission request link");
ok(!/<script(?![^>]*\bsrc=)(?![^>]*application\/(ld\+)?json)[^>]*>/.test(html), "page: no inline executable script");
for (const m of cur.modules) ok(html.includes('id="mod-' + m.id + '"'), "page: module " + m.id);
for (const u of ["https://nvidia.github.io/IsaacCapture/main/getting_started/lerobot/data_collection_sim.html", "https://github.com/NVIDIA/IsaacCapture"]) ok(html.includes(u), "page links " + u);
const sm = fs.readFileSync(path.join(site, "sitemap.xml"), "utf8");
ok(sm.includes("<loc>https://botshelfvampire.com/robot-pilot/</loc>"), "sitemap has /robot-pilot/");
for (const n of ["teleop-session-evidence-v0.1.json", "robot-pilot-profile-v0.1.json", "robot-pilot-curriculum-v0.1.json"]) ok(sch(n).$id === "https://botshelfvampire.com/schemas/" + n, "schema at $id " + n);
const rq = fs.readdirSync(path.join(site, "requests")).filter(f => f.endsWith(".js")).map(f => fs.readFileSync(path.join(site, "requests", f), "utf8")).join("");
ok(/kind'\)==='mission'/.test(rq) && /area/.test(rq), "request market handles ?area=robot-pilot&kind=mission");
console.log(JSON.stringify({ test: "robot-pilot", checks, failures }));
process.exit(failures ? 1 : 0);
