#!/usr/bin/env node
/** Local unit test: TradingView Marketplace rule in traders.js (no network). */
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import path from "node:path";
const root = process.argv[2] || "/workspace/bsv-live/deploy";
const require = createRequire(pathToFileURL(path.join(root, "package.json")));
const t = require(path.join(root, "netlify/functions/_lib/traders.js"));
const fails = [];
const ok = (c, m) => { if (!c) fails.push(m); };
const src = "//@version=5\nindicator('x')\n";
const base = { title: "a", description: "b", setup: "c", terms: "MIT", rights_confirmed: true, origin: "original", platform: "tradingview", filename: "x.pine" };
ok(t.staticChecks({ ...base, listing_type: "PAID", source_mode: "invite_only" }, src).some((x) => x.id === "tv_marketplace_required"), "staticChecks blocks paid invite-only TV");
ok(t.staticChecks({ ...base, listing_type: "PAID", source_mode: "protected" }, src).some((x) => x.id === "tv_marketplace_required"), "staticChecks blocks paid protected TV");
ok(!t.staticChecks({ ...base, listing_type: "FREE", source_mode: "invite_only" }, src).some((x) => /^tv_/.test(x.id)), "free invite-only TV stays allowed before perk rules");
ok(t.checkoutGateProbe(Date.parse("2026-10-31T23:59:59.000Z")) == null, "checkoutGate allows paid invite TV before cutoff");
ok(t.checkoutGateProbe(Date.parse("2026-11-01T00:00:00.000Z")) === "tv_marketplace_required", "checkoutGate rejects paid invite TV at cutoff");
ok(t.checkoutGateProbe(Date.parse("2026-11-01T00:00:00.001Z")) === "tv_marketplace_required", "checkoutGate rejects after cutoff");
process.env.BSV_TV_RULE_NOW = "2026-11-01T00:00:00.000Z";
// Re-require won't reload; call tvInvitePerkBlocked via staticChecks with env already read at nowMs — nowMs reads env each call
ok(t.staticChecks({ ...base, listing_type: "FREE", source_mode: "invite_only", ib_url: "https://example.com/ib", ib_broker: "X" }, src).some((x) => x.id === "tv_invite_perk_blocked"), "after cutoff, invite-only TV + IB link blocked");
delete process.env.BSV_TV_RULE_NOW;
ok(t.TV_RULE_AT_UTC === "2026-11-01T00:00:00.000Z", "cutoff constant");
console.log(JSON.stringify({ test: "tv-rule", checks: 8 - fails.length + fails.length, failures: fails.length, fail: fails }));
process.exit(fails.length ? 1 : 0);
