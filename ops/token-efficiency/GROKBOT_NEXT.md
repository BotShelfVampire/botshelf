# OWNER WAKE DIRECTIVE

Status: ACTIVE P0.

Do not idle or wait for another routine instruction.

If no work is currently running, resume now from the highest-value unfinished LIVE Trader/AI integration item. Continue implementation → test → deploy → live verify → fix → next item.

A local source commit is not completion. A plan is not completion. A test-only result is not completion. The current milestone is live category expansion.

Only stop for a true owner-only approval/access gate.

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
