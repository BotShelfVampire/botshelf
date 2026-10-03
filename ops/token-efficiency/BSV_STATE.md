# BSV compact state

Updated: 2026-10-04 01:15 JST

## Goal

Grow BotShelf Vampire into a large, useful library/marketplace of practical AI-team and trader tooling with minimal owner intervention.

## Trader expansion

Expand the existing Trader category; never duplicate it.

Current source tranche in trader-toolkit/: recipe schema, Pine/MQL5/cTrader generator, starter recipes, copy/paste TradingView tools, MT5/cTrader/NinjaTrader/Quantower/Sierra Chart/GoCharting/MotiveWave starters, Vela custom-chart starter; generator covers 13 targets incl. GoCharting Lipi, MotiveWave and Vela, OpenMarkets notes, compatibility matrix, build-your-own-chart-tool guide.

Direction: a serious user should be able to assemble a personal chart/indicator/dashboard/scanner/alert tool with minimal coding.

## AI expansion

Current source tranche in ai-toolkit/: OpenAI dots rule/responsibility/review packs; Hugging Face MCP research desk, Space safety gate, Skills workflow and local Tiny Agent starter.

Keep expanding around useful copy/use assets, local/self-hosted AI, agents and workflow infrastructure.

## Verification

Source exists != runtime verified. Never silently convert Untested/Unverified into PASS.

## Coordination

GitHub issue #4 is the shared integration task for live Trader + AI surfaces.

## Efficiency

Before a frontier-model call: search exact current files; use deterministic tests; compact context; avoid duplicate agent work; use LM Studio only for low-risk compression/classification/drafting; use external gateway/caching only for API-configurable workers.

## Owner preference

Minimize back-and-forth. Execute reversible/no-spend work autonomously and surface only decisions/access gates that truly need the owner.


## Current execution directive

GrokBot must execute `ops/token-efficiency/GROKBOT_NEXT.md` now and keep the existing Trader + AI category expansion moving through live integration, test, deploy and verification.

## Active GrokBot identity

- Active bot: **New Bobby / ニューボビー**
- Old Bobby is hidden and must be treated as inactive.
- New Bobby is the operational successor and should continue the same BSV production role without restarting the project from scratch.
- Primary coordination source: this repository's compact state/decision files plus GitHub Issue #4.
- Gmail coordination continues through the existing BotShelf Vampire support mailbox; New Bobby must treat the latest owner/ChatGPT handoff email as authoritative for private BSV/dagram-IB context.

## #4 + P0 tranche 3 LIVE (2026-10-04 01:15 JST)

- Production deploy: 6ac189cd1e7f0118d1eef245 Chain: 6ac12003 -> 6ac1254b (#4 Tradovate) -> 6ac12969 (#8/#6/#7 tranche 3) -> 6ac12dcb (#8 t4 sitemaps/gated URLs) -> 6ac132c8 (#4 backtrader) -> 6ac13538 (#6/#7 t4) -> 6ac139e4 (#4 Backtesting.py) -> 6ac13d9a (#8/#6/#7 t5) -> 6ac1424d (#4 NautilusTrader) -> 6ac146a2 (#8/#6/#7 t6) -> 6ac14de6 (#4 visual.table) -> 6ac15512 (tranche 7 coverage/heatmap/tooling) -> 6ac160f4 (HTF correction) -> 6ac16471 (range+breakout) -> 6ac16b2c (tranche 8) -> 6ac1709d (HTF Pine/MQL) -> 6ac172b6 (HTF NinjaTrader) -> 6ac175d6 (pivot/zone/webhook Python targets) -> 6ac178ca (tranche 9) -> 6ac17e76 (cTrader HTF) -> 6ac18538 (AFL + thinkScript HTF) -> 6ac189cd (sweep + divergence)
- #4: Tradovate JavaScript custom-indicator target. Checked by check_tradovate.mjs (360/0) against a node:vm stub of the documented API; this is not a Tradovate run. Listed the ATAS way: 19 starters, 19 builder tabs.
- #8 t3: /capabilities/index.json, capability-manifest v0.1, 90 manifests, nothing VERIFIED.
- #6 t3: demand-request?op=signals, opportunity-signal v0.1, from approved public requests only.
- #7 t3: /robot-pilot/#recipes, the SO-101 simulation practice-session recipe (UNTESTED_RUNTIME).
- Next: #8 t4 (trading item pages into sitemap + canonical), then the next #4 target.

## P0 tranche 2 LIVE (2026-10-04 00:41 JST)

- Current production deploy: 6ac1200355a8945f1300a5b9. Chain: 6ac118a7 -> 6ac11c03 (#7 t2) -> 6ac11dac (#8 t2) -> 6ac12003 (#6 t2).
- #7 t2: pilot-record fn. Private, SELF_REPORTED only, no auto-promotion, not a licence.
- #8 t2: /transparency/ with real figures only, plus BreadcrumbList on 87 pages.
- #6 t2: /requests/#builders + opportunities.json (live counts, catalogue gaps 34/41/2).
- Reviewer: compile_reports_digest.py --kind compile|request|pilot. The hourly digest covers all three kinds, account IDs only.
- Batch email send_report13.py sent. Next: #4, then tranche 3 of #8/#6/#7.

## P0 tranches LIVE (2026-10-04 00:05 JST)

- Production deploy `6ac118a7dedefaa8327591fb`. Chain `6ac10b3f` → `6ac1130a` (#8) → `6ac115c3` (#6) → `6ac118a7` (#7).
- New public surfaces: `/requests/` (Request Market, demand-request fn, review before listing, real counts), `/robot-pilot/` (Academy, browser-only practice record, SIMULATION only), `/.well-known/bsv-trust.json`, `/schemas/*-v0.1.json`. robots: OAI-SearchBot allow (same Disallow list), GPTBot disallow.

## LIVE integration status (New Bobby, cycle 11, 2026-10-03 23:25 JST)

- Production deploy: `6ac10b3f9b77b9322f9ef9ec` (23:03 JST, email_configured:true before/after). Chain: `6ac0f924` → `6ac10b3f`. Commits `4c4642a` (thinkScript target + check), `a9029b2` (AmiBroker + thinkorswim listed).
- Listing rule (owner 22:45 JST): verified targets are listed on recipe pages, platform lists, hub counts, compatibility table and README the ATAS way (entry + corrected counts only), no further approval needed.
- AmiBroker AFL and thinkorswim thinkScript are now pre-generated starters on all 14 recipe pages and zips (`.afl`, `.ts`); 18 starters per recipe; hub Platforms 18; builder 18 tabs (no builder-only targets left). Counts EN "eighteen pre-generated / all eighteen" and JA 18/18.
- thinkScript (`thinkscript`): study only, `ExpAverage`/`Average`/`WildersAverage`/`TrueRange`, plots, `Alert(cond[1], …, Alert.BAR, Sound.Ding)`, no `AddOrder`; session via `SecondsFromTime`/`SecondsTillTime` (US Eastern). Check `check_thinkscript.mjs` = BSV thinkScript-subset parser/evaluator (643/0; negative tests fail as expected). Not thinkorswim.
- Builder: parity 252/252, share/lint 1095/0, js `bsv-builder.196c275b.js`.
- LIVE QA: trader gate 72/0, toolkit 56/81, library gate 879/0 local + 879 live, builder CDP 18 tabs 0 fail 0 CSP, CSP sweep 929 pages / 0 violations, reviewer endpoint anon 401 / key 200, CI on a9029b2 3/3.
- Catalog status unchanged: UNTESTED_RUNTIME; Runtime-tested by BSV = 0.

## LIVE integration status (New Bobby, cycle 10, 2026-10-03 22:45 JST)

- Production deploy: `6ac0f92445051fe09bf6fdbb` (21:46 JST, email_configured:true before/after). Chain: `6ac0efbe` → `6ac0f924`. Commits `d030472` (ATAS on recipe pages + lists/counts), `6b33e59` (AmiBroker target + check).
- ATAS (owner approval 21:33 JST): pre-generated starter on all 14 recipe pages and in zips; added to platform lists, hub platform count (16) and platform filter; only the ATAS entry and corrected counts (EN "sixteen pre-generated / seventeen builder targets", JA 16/17 — the JA line still said 13). Descriptive tone unchanged.
- AmiBroker AFL (`amibroker`): builder/CLI target, builder-only (not on recipe pages or platform lists). Indicator only: `MA`/`EMA`/`RSIa`/`ATR`, `Plot`, completed-bar `AlertIf` (guide pattern, lookback 2), no `Buy`/`Sell`/`Short`/`Cover`. Check `check_amibroker_afl.mjs` = BSV AFL-subset parser/evaluator (551/0; negative tests: undocumented function, look-ahead `Ref`, forming-bar alert all fail). Not AmiBroker.
- Builder: 17 tabs, parity 238/238, share/lint 1042/0, js `bsv-builder.9639e20b.js`. LIVE: toolkit 56/81, trader gate 72/0, library gate 879/0, CSP sweep 929/0, builder CDP 0 failures.
- Catalog status unchanged: UNTESTED_RUNTIME; Runtime-tested by BSV = 0.

## LIVE integration status (New Bobby, cycle 9, 2026-10-03 21:33 JST)

- Production deploy: `6ac0efbe410eb1a190e44728` (ATAS + intake disclosure, email_configured:true before/after). Cycle 9 chain: `6ac0e60e` → `6ac0ee67` (intake reviewer credential) → `6ac0efbe` (ATAS). Commits `16930eb` (reviewer credential), `dda6c0a` (DECISIONS/design), `3b195ce` (ATAS, EasyLanguage dep-order fix, builder disclosure).
- Compile-result review is no longer owner-only (owner order 20:57 JST): owner (`x-admin-secret`, sees account email), New Bobby (`x-bsv-reviewer-key` = Netlify env `COMPILE_REVIEWER_KEY`, functions/production/secret; box copy `/workspace/newbobby-mail/.reviewer_key` chmod 600, never committed), ChatGPT (hourly digest mail, new pending only). Reviewer role sees account ids only. LIVE: anon 401, wrong key 401, session-only 401, reviewer key 200. QA record `crp_a7eb9f9cf32f2dd59b6f6ec9` rejected by reviewer:new-bobby ("QA test record by New Bobby"); pending = 0.
- Box tool: `/workspace/newbobby-mail/compile_reports_digest.py` (`digest`, `digest --email`, `get`, `reject`, `decide`); digests in `/workspace/newbobby-mail/digests/`; seen ids in `compile_reports_seen.json`; hourly step recorded in `/workspace/newbobby-mail/state.json`.
- Trader builder targets (16): + **ATAS** (`atas`, C# `Indicator`, lines + closed-bar `AddAlert`, no order APIs; .NET 8 stub compile 14/14 via `check_atas_stubs.sh`, not an ATAS compile). Builder-only (`BUILDER_EXTRA_TARGETS`): recipe-page starters and platform-list copy unchanged. Parity 224/224, share/lint 989, builder js `bsv-builder.699c26b9.js`.
- Catalog status unchanged: UNTESTED_RUNTIME; Runtime-tested by BSV = 0.

## LIVE integration status (New Bobby, cycle 8, 2026-10-03 20:45 JST)

- Production deploy: `6ac0e60e0dc0bad36673a1d4` (EasyLanguage, email_configured:true before/after). Cycle 8 chain: `6ac0df16` → `6ac0e283` (compile-result intake) → `6ac0e4b6` (JForex) → `6ac0e60e` (TradeStation EasyLanguage). Commits `5ce2fc6` (intake), `453c0a0` (JForex), `4edf5be` (EasyLanguage) on the PR #5 branch.
- Compile-result intake (owner's most conservative answers): `/.netlify/functions/compile-report` (source `site-functions/compile-report.js`, installed by `install_compile_report_fn.py`). Email-verified session only (anon 401, foreign Origin 403, unknown field 400); store `compile_reports` in the existing Netlify Blobs setup keyed to the account id; no PII beyond the account email (looked up at review time); owner-only queue/review via `x-admin-secret`; states pending / approved-user-reported / rejected / needs-info (no verified state); never public; rejected deleted after 30 days; 10/day/account; duplicates merged. Builder: "Send to BSV (owner review)" button. LIVE: 1 QA report `crp_a7eb9f9cf32f2dd59b6f6ec9` (pending, notes "QA test by New Bobby — please reject").
- Trader generator/builder targets (15): + **JForex** (`jforex`, Java `IStrategy`, console output, no orders; javac stub compile 14/14 via `check_jforex_stubs.sh`), + **TradeStation EasyLanguage** (`easylanguage`, indicator, closed-bar `Alert`; structural check 447/0 via `check_easylanguage_output.mjs`, not a TradeStation Verify). Parity 210/210, share/lint 936, builder js `bsv-builder.48bb5664.js`, 15 tabs.
- Catalog status unchanged: UNTESTED_RUNTIME; Runtime-tested by BSV = 0. Images (logo/hero gold lettering) left as-is by owner decision.

## LIVE integration status (New Bobby, cycle 7, 2026-10-03 20:00 JST)

- Production deploy: `6ac0df169b77b9322b9ef9f4` (19:55 JST, email_configured:true before/after). Cycle 7 chain: `6ac0d372` → `6ac0d65d` (19:21, gold→green base CSS) → `6ac0dad0` (19:37, GoCharting Lipi) → `6ac0dcc9` (19:45, MotiveWave) → `6ac0df16` (19:55, Vela). Commits `65f2c89` (recolor), `e5f88af` (n8n id), `f11b7f8` (Lipi), `d240f67` (MotiveWave), `b46f441` (Vela) on the PR #5 branch (not merged).
- No gold surfaces in site CSS: `scripts/site/recolor_accent.py` (pipeline step after externalize; `--check` must print `{"referenced_css_with_gold": []}`) recolors gold accents in every CSS file referenced by HTML to the green accent `#bad4b7` (other gold hues → green hue with ≥ original contrast on #07080a), writes `<stem>.g<sha8>.css` and rewrites `<link>` hrefs (1-year immutable cache safe). 9 CSS files, 2280 pages href-only. Raster images (hero photo lettering, logo) are not CSS and still contain gold.
- Trader generator/builder targets (13): Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python, NinjaTrader 8, Quantower, Sierra Chart ACSIL, ProRealTime, **GoCharting Lipi** (`gocharting-lipi`), **MotiveWave Java SDK** (`motivewave`), **Vela JS** (`vela`). Parity 182/182, share/lint 833, builder js `bsv-builder.c212b4d9.js`, 13 tabs.
  - MotiveWave: all 14 recipes compile with javac 21 against BSV stubs written from the public javadoc (`scripts/site/check_motivewave_stubs.sh`, stubs in `scripts/site/mw_stubs/`). Not built against the real SDK jar, not loaded in MotiveWave.
  - Vela: plain-JS recipe engine on Vela's `ScriptingEngine` port; imports only `@luxalgo/vela` (Apache-2.0), no Pine runtime (pinets = AGPL-3.0). `scripts/site/test_vela_engine.mjs` 137 offline checks; headless Chrome smoke test on real `vela.global.js` 0.8.1 with synthetic bars: 7 recipes mounted, lines + markers drawn, 0 console errors (`qa/cdp_vela_smoke.py`). Not live data, not user-tested.
  - GoCharting Lipi: API names checked against GoCharting docs; not checked in the Lipi editor.
  - Catalog status unchanged: UNTESTED_RUNTIME; Runtime-tested by BSV = 0.
- n8n: Node v24.21.0 (`/workspace/tools/node24`, sha256 verified) + n8n 2.41.6 (`/workspace/tools/n8n`) on the ops box. All 10 generated task workflows import with `n8n import:workflow` (workflow `id` now emitted by `make_workflow.py`); doc-review executed with `n8n execute` against a stub OpenAI-compatible server (1 request, system+user, section check ran). Stub ≠ real model: not runtime evidence.
- Design only (not implemented): `trader-toolkit/docs/compile-result-intake-design.md` — owner-reviewed intake of builder compile records; states pending/approved-user-reported/rejected/needs-info; no auto-promotion, no "verified" state.
- LIVE tests (pass, 19:21–20:00 JST): toolkit public=56 gated=81; trader gate 72/0; library gate 879/0; full real-browser CSP sweep 929 pages / 0 violations / 0 failed stylesheets (19:23–19:42, after recolor); key-page sweep 27/0 after each deploy; builder CDP via session proxy 0 CSP violations each deploy.

## Previous: cycle 6 (2026-10-03 19:10 JST)

- Production deploy: `6ac0d372e4bf16de31470b3e` (context `production`, email_configured:true before/after). Chain: `6ac0c6e9` (cycle 5) → `6ac0ce75` (cycle 6, 18:45 JST) → `6ac0d372` (cycle 6b, 19:05 JST: toolkit refs exclude non-public hosts). Always `qa/deploy_prod.sh`; never publish CLI drafts via `restoreSiteDeploy`. Source commit `fb89023` (PR #5 branch, not merged).
- Library CSP fix: `scripts/site/externalize_inline_styles.py` (pipeline step, runs last; `--check` must report 0) moved inline `<style>` from 925 pages (≈915 Library + forex/metals/indices/for-sellers/sell/packs/gold-session pages) to `/assets/inline/bsv-inline.<sha10>.css` and `style=""` attributes to `bsv-s-<sha8>` classes (`bsv-attrs.<sha10>.css`). Gold hover `#c9a227` → green `#bad4b7`. CSS-only move; no content/payment change.
- Trader: generator/builder targets (10): Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python, NinjaTrader 8, Quantower, **Sierra Chart ACSIL** (`sierra-acsil`), **ProRealTime ProBuilder** (`prorealtime`). Parity 140/140. All UNTESTED_RUNTIME / not compiled by BSV — Runtime-tested by BSV = 0.
- Recipe builder (gated js `bsv-builder.06f4f8f8.js`): 10 tabs, recipe check, per-target checklist with checkboxes, and **compile record** (self-reported result per target: status/platform/notes/steps, FNV-1a fingerprint of the shown code, "matches"/"code changed since", .md export). Stored only in the browser's localStorage (`bsv-rb-compile-log`); every record carries `self_reported:true, bsv_verified:false`; nothing is sent to BSV.
- AI toolkit: https://botshelfvampire.com/library/toolkit/ (**16**) incl. team runners for LangGraph, CrewAI, **n8n** (`make_workflow.py`: per-task importable workflow, manual trigger → local model HTTP → section check → review; no write/send/paid nodes) and **OpenAI Agents SDK** (`agents_runner.py`: local OpenAI-compatible model, tracing disabled, no tools, approval before save). Each runner page lists the 10 Teams; back-links on `/library/<runtime>/<team>/` (n8n → n8n pages; Agents SDK → LM Studio pages, same prompt). Prompts not bundled.
- Library bodies gated: **879**. Gated paths unchanged.
- LIVE tests (pass, 18:45–19:10 JST): toolkit public=56 gated=81; trader gate 72/0; library gate 879/0; new runner source html/zip anon 302 / session 200 byte-match; real-browser CSP sweep through production CSP: 929 pages, 0 violations, 0 failed stylesheets; builder 10 tabs + Sierra/PRT output signatures + compile record (match → changed, bsv_verified:false) + lint + share, 0 CSP violations; runner pages 4×10 tasks, 0 violations.
- Not done / owner: CI workflow edit (py_compile + self-test for the two new runners) needs a `workflow`-scope token — patch at `qa/c6-workflow-runner-checks.patch` (ops box). (Base CSS gold → green done in cycle 7; n8n import done in cycle 7.)
- Logged-in QA: `support@botshelfvampire.com` (OTP test). Cookie jar on ops box only.
- Owner decisions recorded: public GitHub repos stay public (provenance links only); `/cross-ai/kits/research-desk-local/` left public. Workflow file move needs a `workflow`-scope token (owner).
