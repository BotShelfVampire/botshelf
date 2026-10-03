# BSV compact state

Updated: 2026-10-03

## Goal

Grow BotShelf Vampire into a large, useful library/marketplace of practical AI-team and trader tooling with minimal owner intervention.

## Trader expansion

Expand the existing Trader category; never duplicate it.

Current source tranche in trader-toolkit/: recipe schema, Pine/MQL5/cTrader generator, starter recipes, copy/paste TradingView tools, MT5/cTrader/NinjaTrader/Quantower/Sierra Chart/GoCharting starters, Vela custom-chart starter, OpenMarkets notes, compatibility matrix, build-your-own-chart-tool guide.

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

## LIVE integration status (New Bobby, 2026-10-03 19:10 JST)

- Production deploy: `6ac0d372e4bf16de31470b3e` (context `production`, email_configured:true before/after). Chain: `6ac0c6e9` (cycle 5) → `6ac0ce75` (cycle 6, 18:45 JST) → `6ac0d372` (cycle 6b, 19:05 JST: toolkit refs exclude non-public hosts). Always `qa/deploy_prod.sh`; never publish CLI drafts via `restoreSiteDeploy`. Source commit `fb89023` (PR #5 branch, not merged).
- Library CSP fix: `scripts/site/externalize_inline_styles.py` (pipeline step, runs last; `--check` must report 0) moved inline `<style>` from 925 pages (≈915 Library + forex/metals/indices/for-sellers/sell/packs/gold-session pages) to `/assets/inline/bsv-inline.<sha10>.css` and `style=""` attributes to `bsv-s-<sha8>` classes (`bsv-attrs.<sha10>.css`). Gold hover `#c9a227` → green `#bad4b7`. CSS-only move; no content/payment change.
- Trader: generator/builder targets (10): Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python, NinjaTrader 8, Quantower, **Sierra Chart ACSIL** (`sierra-acsil`), **ProRealTime ProBuilder** (`prorealtime`). Parity 140/140. All UNTESTED_RUNTIME / not compiled by BSV — Runtime-tested by BSV = 0.
- Recipe builder (gated js `bsv-builder.06f4f8f8.js`): 10 tabs, recipe check, per-target checklist with checkboxes, and **compile record** (self-reported result per target: status/platform/notes/steps, FNV-1a fingerprint of the shown code, "matches"/"code changed since", .md export). Stored only in the browser's localStorage (`bsv-rb-compile-log`); every record carries `self_reported:true, bsv_verified:false`; nothing is sent to BSV.
- AI toolkit: https://botshelfvampire.com/library/toolkit/ (**16**) incl. team runners for LangGraph, CrewAI, **n8n** (`make_workflow.py`: per-task importable workflow, manual trigger → local model HTTP → section check → review; no write/send/paid nodes) and **OpenAI Agents SDK** (`agents_runner.py`: local OpenAI-compatible model, tracing disabled, no tools, approval before save). Each runner page lists the 10 Teams; back-links on `/library/<runtime>/<team>/` (n8n → n8n pages; Agents SDK → LM Studio pages, same prompt). Prompts not bundled.
- Library bodies gated: **879**. Gated paths unchanged.
- LIVE tests (pass, 18:45–19:10 JST): toolkit public=56 gated=81; trader gate 72/0; library gate 879/0; new runner source html/zip anon 302 / session 200 byte-match; real-browser CSP sweep through production CSP: 929 pages, 0 violations, 0 failed stylesheets; builder 10 tabs + Sierra/PRT output signatures + compile record (match → changed, bsv_verified:false) + lint + share, 0 CSP violations; runner pages 4×10 tasks, 0 violations.
- Not done / owner: CI workflow edit (py_compile + self-test for the two new runners) needs a `workflow`-scope token — patch at `qa/c6-workflow-runner-checks.patch` (ops box). n8n workflows not imported in n8n (n8n 2.x needs Node ≥24 + native build; not on box). Base site CSS (`/css/shelf.css` `--gold:#d4b45a`, `trading/assets/library.css` `--gold:#dfc583`) still uses a gold accent site-wide — owner decision needed before a site-wide recolor.
- Logged-in QA: `support@botshelfvampire.com` (OTP test). Cookie jar on ops box only.
- Owner decisions recorded: public GitHub repos stay public (provenance links only); `/cross-ai/kits/research-desk-local/` left public. Workflow file move needs a `workflow`-scope token (owner).
