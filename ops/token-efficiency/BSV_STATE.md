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

## LIVE integration status (New Bobby, 2026-10-03 18:20 JST)

- Production deploy: `6ac0c6e9cbb08b40513ed4c8` (context `production`, email_configured:true before/after). Chain: `6ac0c0f4` (cycle 4) → `6ac0c579` (cycle 5: NT8/Quantower, lint/checklist, LangGraph/CrewAI runners) → `6ac0c6e9` (refs fix: no localhost/self links in "Official references"). Always `qa/deploy_prod.sh`; never publish CLI drafts via `restoreSiteDeploy`.
- Trader: https://botshelfvampire.com/trading/build/ — **37** assets (23 catalog + 14 recipes) + recipe builder. Generator/builder targets (8): Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python, **NinjaTrader 8**, **Quantower** (parity 112/112). MQL5/cTrader C#/NT8/Quantower compute indicators/signals/plots/alerts. All UNTESTED_RUNTIME / STRUCTURAL — Runtime-tested by BSV = 0.
- Recipe builder: https://botshelfvampire.com/trading/tools/bsv-builder.html (public) → gated `/trading/items/bsv-builder.html` (`bsv-builder.19ed3a1d.js`): 8 tabs, per-block TODO hints, **recipe check** (self-ref/session-format/cycle errors; forward-ref with "Fix order", unused block with "Remove", alert/combine/cross/RSI-range warnings), **per-target compile checklist** (8 targets + 3 common items, EN/JA), config-only share / JSON import-export. CSS external (CSP).
- AI toolkit: https://botshelfvampire.com/library/toolkit/ (**14**) incl. `langgraph-team-runner` + `crewai-team-runner` (per-task, local OpenAI-compatible model, section check, human approval before save). Runner pages list the 10 Library Teams (public runtime page + gated full prompt `/library/source/team-<runtime>-<team>.html`); all 20 `/library/langgraph|crewai/<team>/` pages link back ("Run this task locally"). Prompts are not bundled in the runners.
- Library bodies gated: **879** (70 teams + 809 packs).
- Gated paths: `/trading/items|sources|downloads/*`, `/library/source/*`, `/registered`, `/switchboard-cos`.
- LIVE tests (pass, 18:12–18:20 JST): toolkit public=54 gated=77; trader gate 72 files anon 302 / session 200 byte-match; runner source html/zip anon 302 / session 200 byte-match; library gate 879/0; parity 112; share/hints/lint/checklist 541 checks; real-browser render through production CSP: builder 8 tabs + NT/Quantower output + lint reorder/remove + checklist per tab + share, 0 CSP violations; runner pages 10/10 tasks; health email_configured:true.
- Known pre-existing issue: 915 Library pages (and a few others) carry an inline `<style>` that production CSP blocks (also before this cycle); it contains a gold hover colour. Queued: externalize with the green accent.
- Logged-in QA: `support@botshelfvampire.com` (OTP test). Cookie jar on ops box only.
- Owner decisions recorded: public GitHub repos stay public (provenance links only); `/cross-ai/kits/research-desk-local/` left public. Workflow file move needs a `workflow`-scope token (owner).
