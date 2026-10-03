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

## LIVE integration status (New Bobby, 2026-10-03 17:50 JST)

- Production deploy: `6ac0c0f48e544dc4923b42da` (context `production`, email_configured:true before/after). Always `qa/deploy_prod.sh` (`--prod` + health check before/after); never publish CLI drafts via `restoreSiteDeploy`.
- Trader: https://botshelfvampire.com/trading/build/ — **37** assets (23 catalog + 14 recipes) + recipe builder; 13 platform filters incl. MT4 and Bookmap. Generator/builder targets: Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python (parity 84/84). MQL5 and cTrader C# now compute indicators/signals/plots/alerts. All UNTESTED_RUNTIME / STRUCTURAL — Runtime-tested by BSV = 0.
- Recipe builder v2: https://botshelfvampire.com/trading/tools/bsv-builder.html (public) → gated `/trading/items/bsv-builder.html`: per-block TODO hints, config-only share link / JSON import-export. CSS external (CSP).
- AI toolkit: https://botshelfvampire.com/library/toolkit/ (12) cross-linked with Library Teams.
- Library bodies gated: **879** (70 teams + 809 packs); full text at `/library/source/team-*` / `item-*` behind verified session; free labels kept; items.json / search / sitemap / llms carry no bodies; `*.bak*` pruned.
- Gated paths: `/trading/items|sources|downloads/*`, `/library/source/*`, `/registered`, `/switchboard-cos`.
- LIVE tests (pass): toolkit public=52 gated=73; trader gate 72 files anon 302 / session 200 byte-match; library gate 879/0; builder parity 84; builder share/hints 406 checks; health email_configured:true.
- Logged-in QA: `support@botshelfvampire.com` (OTP test). Cookie jar on ops box only.
- Owner decisions recorded: public GitHub repos stay public (provenance links only); `/cross-ai/kits/research-desk-local/` left public. Workflow file move needs a `workflow`-scope token (owner).
