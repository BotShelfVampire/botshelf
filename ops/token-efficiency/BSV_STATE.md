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

## LIVE integration status (New Bobby, 2026-10-03 16:14 JST)

- Production deploy: `6ac0ab203f861b45e9b5ae67`. Chain from `6abefaf5`: `6ac0a8ff` → `6ac0a9e0` → `6ac0aa87` → `6ac0ab20`. Each one adds to the last; nothing was rolled back. The unpublished `6abf02a9` (skipped for credits) was **not** included.
- Trader (existing category): https://botshelfvampire.com/trading/build/ is the "Build your own chart tool" hub.
  - It holds 32 assets: 20 catalog entries and 12 recipes.
  - It has filters for 11 platforms, type and test status.
  - Vela is a first-class path. OpenMarkets is shown as data/agent integration.
  - The entry block and chip are on /trading/.
- AI (existing Library): https://botshelfvampire.com/library/toolkit/ has 12 items, organised by job and by framework: Dots, Hugging Face, Bionic, smolagents, Letta, OpenAI Agents SDK. The entry block is on /library/. The existing 7 platforms are untouched.
- Source bodies are served only behind the email-verified session gate (`/trading/items|downloads/bsv-*`, `/library/source/*`). Summaries are public.
- The site search index (`/search/`, `index.v20261003.json`) and `sitemap.xml` include the new public pages.
- Generator: all 36 runs (12 recipes × Pine v6/MQL5/cTrader) pass. TODO counts are shown per target.
- LIVE test: `python3 scripts/site/test_live_toolkit.py --live https://botshelfvampire.com` → ok. 47 public pages and 66 gated paths were checked.
- Not verified: the logged-in (email-verified) view of the gated pages. No verified test session was available to the bot. Runtime-tested by BSV = 0.
