# OWNER WAKE DIRECTIVE

Status: ACTIVE P0.

Do not idle or wait for another routine instruction.

If no work is currently running, resume now from the highest-value unfinished LIVE Trader/AI integration item. Continue implementation → test → deploy → live verify → fix → next item.

A local source commit is not completion. A plan is not completion. A test-only result is not completion. The current milestone is live category expansion.

Only stop for a true owner-only approval/access gate.

---

# Status 2026-10-03 22:45 JST (New Bobby) — cycle 10 LIVE

LIVE deploy: `6ac0f92445051fe09bf6fdbb` (21:46 JST). Commits `d030472`, `6b33e59`.

Shipped: (a) ATAS on recipe pages (16 pre-generated starters) and in platform lists / hub counts (owner approval 21:33); (b) AmiBroker AFL builder target with a BSV AFL-subset parser/evaluator check; builder 17 tabs, parity 238/238; (c) CI patch adds `check_amibroker_afl.mjs`.

Proposals (not done): AmiBroker on recipe pages and in platform lists / compatibility table / README (needs owner OK on wording).

Hourly routine: `python3 /workspace/newbobby-mail/compile_reports_digest.py digest --email`.

---

# Status 2026-10-03 21:33 JST (New Bobby) — cycle 9 LIVE

LIVE deploy: `6ac0efbe410eb1a190e44728` (email_configured:true before/after). Chain: `6ac0ee67` (intake reviewer credential) → `6ac0efbe` (ATAS). Commits `16930eb`, `dda6c0a`, `3b195ce`.

Shipped: (a) compile-result review by owner + New Bobby (reviewer key) + ChatGPT (hourly digest), account ids only, never verified; box tool `/workspace/newbobby-mail/compile_reports_digest.py`; QA record rejected; (b) ATAS C# indicator target, builder-only, .NET 8 stub compile 14/14; builder 16 tabs, parity 224/224; (c) EasyLanguage now evaluates blocks in dependency order; (d) CI patch adds setup-dotnet 8.0.x + `check_atas_stubs.sh`.

Hourly routine: run `python3 /workspace/newbobby-mail/compile_reports_digest.py digest --email` (mails ChatGPT only when there are new pending submissions).

Owner rule (20:46 JST): no brand-image changes, and no further platform-list copy changes; list ideas as proposals.

Proposals (not done): ATAS in recipe-page starters; ATAS in platform-list copy / hub counts / README lists.

Next queue: one more verified platform target (builder-only), owner applies CI patch (workflow scope), then continue Trader/AI LIVE items.

---

# Status 2026-10-03 20:45 JST (New Bobby) — cycle 8 LIVE

LIVE deploy: `6ac0e60e0dc0bad36673a1d4` (email_configured:true before/after). Chain: `6ac0e283` (intake) → `6ac0e4b6` (JForex) → `6ac0e60e` (EasyLanguage). Commits `5ce2fc6`, `453c0a0`, `4edf5be`.

Shipped: (a) compile-result intake with the owner's most conservative answers (DECISIONS.md, design doc "implemented"); (b) JForex generator target (stub compile 14/14); (c) TradeStation EasyLanguage target (structural check 447/0); builder 15 tabs, parity 210/210; (d) `qa/c6-workflow-runner-checks.patch` now also runs MotiveWave/JForex stub compiles (setup-java 21), Vela engine test and EasyLanguage check, and triggers on `scripts/site/**`.

Owner rule (20:46 JST): no brand-image changes (colors, logo, tone, taglines, visual design, hero copy) without owner approval; #bad4b7 stays as is.

LIVE checks at the end: health OK, toolkit 56/81, trader gate 72/0, library gate 879/0, full CSP sweep 929/0, builder 15 tabs with 0 CSP violations.

Next queue (in order):
1. Owner: apply `qa/c6-workflow-runner-checks.patch` (needs `workflow` scope). `git apply --check` passes on the branch.
2. Owner: review/reject QA report `crp_a7eb9f9cf32f2dd59b6f6ec9` in the intake queue (x-admin-secret); BSV has no admin secret.
3. Real-platform evidence when available (JForex compile/demo, TradeStation Verify, MotiveWave SDK build, Lipi editor) — BSV evidence only if BSV ran it.
4. Next generator ideas after API check: ATAS (C#), cTrader/NT order-free extras; owner to choose.

---

# Status 2026-10-03 20:00 JST (New Bobby) — cycle 7 LIVE

LIVE deploy: `6ac0df169b77b9322b9ef9f4` (19:55 JST, email_configured:true before/after). Chain: `6ac0d65d` (gold→green) → `6ac0dad0` (Lipi) → `6ac0dcc9` (MotiveWave) → `6ac0df16` (Vela). Commits `65f2c89`, `e5f88af`, `f11b7f8`, `d240f67`, `b46f441`.

Shipped: (a) base CSS gold → green (`recolor_accent.py`, hashed CSS names, 9 files, LIVE CSP 929/0); (b) Node 24 + n8n 2.41.6 on the box, 10 workflows imported, 1 executed against a stub (not runtime evidence); (c) generator targets GoCharting Lipi, MotiveWave (javac stub compile 14/14), Vela (offline 137 checks + headless smoke 7 recipes); builder 13 tabs, parity 182/182; (d) intake design doc only.

Next queue (in order):
1. Owner: apply `qa/c6-workflow-runner-checks.patch` (needs `workflow` scope); also add `check_motivewave_stubs.sh` + `test_vela_engine.mjs` to CI in the same edit.
2. Owner decision on `compile-result-intake-design.md` open questions before any implementation (never auto-promote).
3. Real-platform evidence when available: Lipi editor check, MotiveWave SDK build, Vela with a real data feed — record as BSV evidence only if BSV ran it.
4. Gold remains in raster images (hero photo lettering, logo): owner decision whether to re-export them.
5. Next generator ideas: JForex (Java), TradeStation EasyLanguage — research APIs first.

---

# Status 2026-10-03 19:10 JST (New Bobby) — cycle 6 LIVE

LIVE deploy: `6ac0d372e4bf16de31470b3e` (production, email_configured:true before/after). Chain: `6ac0c6e9` (cycle 5) → `6ac0ce75` (cycle 6) → `6ac0d372` (6b refs fix). Source commit `fb89023`. Single implementer: the hourly mail routine is mail-only.

Shipped this cycle (all four queued items):
1. Library CSP fix: inline `<style>`/`style=""` on 925 pages → hashed CSS (`externalize_inline_styles.py`, pipeline last step), gold hover → green. LIVE real-browser sweep 929 pages: 0 violations.
2. Builder compile record: per-step checkboxes + self-reported result (localStorage only, fingerprint-tied, `bsv_verified:false`, .md export). No BSV verification claim.
3. Generator targets Sierra Chart ACSIL (`sierra-acsil`) and ProRealTime (`prorealtime`); builder 10 tabs, parity 140/140. Docs updated. Not compiled by BSV (no compiler/platform on box).
4. AI team runners: n8n (`ai-toolkit/n8n/team-runner/`) and OpenAI Agents SDK (`ai-toolkit/openai-agents/team-runner/`). `--self-test` pass; Agents SDK wiring checked with openai-agents 0.23.1 against a local stub server (1 request, system+user) — not runtime evidence.

Tests (pass): parity 140; share/lint/checklist/record 683; toolkit local+LIVE 56/81; LIVE trader gate 72/0; LIVE library gate 879/0; runner sources anon 302 / session 200 byte-match; LIVE CSP sweep 929/0; builder CDP 0 violations; runner CDP 4×10.

Next queue (in order):
1. Owner: apply `qa/c6-workflow-runner-checks.patch` (needs `workflow` scope) so CI runs the new runner self-tests.
2. Owner decision: recolor base site CSS gold accent (`--gold` in shelf.css / trading library.css) to green, with cache-busted filenames (CSS is cached immutable 1 year).
3. Next generator targets: GoCharting (Lipi), MotiveWave (Java SDK), then Vela.
4. Compile-record follow-up: optional owner-reviewed submission path (still never auto-marks "runtime tested").
5. n8n import check on a Node ≥24 host when available.

# GrokBot — execute now

Use this as the current BSV execution directive.

## Read first

- ops/token-efficiency/BSV_STATE.md
- ops/token-efficiency/DECISIONS.md
- ops/token-efficiency/BIONIC_DELEGATION.md
- trader-toolkit/catalog.json
- ai-toolkit/catalog.json

## Trader

Expand the EXISTING Trader category. Do not create a duplicate.

Integrate the current Trader catalog into the live site:
- Build your own chart tool
- BSV Trader Recipe
- code generator
- TradingView
- MT5
- MT4
- cTrader (C# + Python)
- Bookmap
- NinjaTrader
- Quantower
- Sierra Chart
- GoCharting
- ProRealTime
- MotiveWave
- Vela
- JForex
- TradeStation EasyLanguage
- OpenMarkets

Required UX:
- clear Build your own chart tool entry
- platform/type/test-status filters
- useful detail pages
- honest tested/unverified labels
- mobile + desktop usable

## AI

Expand the EXISTING AI category. Do not create a duplicate.

Integrate the current AI catalog:
- Dots
- Hugging Face
- Bionic
- smolagents
- Letta
- OpenAI Agents SDK

Preserve existing:
- Ollama
- LM Studio
- Open WebUI
- n8n
- CrewAI
- LangGraph
- MCP

Organize by job and runtime/framework.

## Bionic

Use Bionic for low-risk parallel work:
- indexing
- metadata
- dedupe
- link checks
- content normalization
- simple transformations
- test scaffolding

Do not use Bionic as final authority for security/auth/payment/licensing or production verification.

## Execution

Fresh-read current source and live site before editing.
Integrate.
Test.
Deploy.
Verify mobile and desktop.
Fix regressions.
Continue the next tranche.

Do not stop at planning.
Do not send routine progress chatter.
Report after a meaningful live tranche is deployed or when a real owner-only blocker remains.
