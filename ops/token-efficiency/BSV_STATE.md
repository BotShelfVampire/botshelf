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

## LIVE integration status (New Bobby, 2026-10-03 17:18 JST)

- Production deploy: `6ac0b8e61e7f01df9ceef1db` (context `production`, email_configured:true). Chain includes pack-gate batches (`6ac0b458` …) then cycle-3 trader platforms. Always deploy with `--prod`; never publish CLI drafts via `restoreSiteDeploy`.
- Trader: https://botshelfvampire.com/trading/build/ — **37** assets (23 catalog + 14 recipes) + recipe builder; filters include **MT4** and **Bookmap** (13 platform options). Generator / builder targets: Pine v6, MQL5, MQL4, cTrader C#, cTrader Python, Bookmap Python (parity 84/84). New pages: `bsv-mt4-ema-atr`, `bsv-bookmap-trade-ema`, `bsv-ctrader-python-ema-atr`, recipes `golden-cross-alert`, `ema-cross-rsi-filter`. All UNTESTED_RUNTIME / STRUCTURAL — Runtime-tested by BSV = 0.
- AI toolkit: https://botshelfvampire.com/library/toolkit/ (12) cross-linked with Library Teams.
- Library bodies gated: **879** (70 teams + 809 packs). Public keeps title/summary/explanation; full text at `/library/source/team-*` and `/library/source/item-*` behind verified session; free labels kept. items.json / search / sitemap / llms have no bodies. `*.bak*` pruned.
- Gated paths: `/trading/items|sources|downloads/*`, `/library/source/*`, `/registered`, `/switchboard-cos`.
- LIVE tests (pass): toolkit public=52 gated=73; library gate 879 anonymous 302 + logged-in body match; builder parity 84; health email_configured:true.
- Logged-in QA: `support@botshelfvampire.com` (OTP test). Cookie jar on ops box only.
- UNVERIFIED / owner leftovers: public GitHub repos still expose bodies; `/cross-ai/kits/research-desk-local/` left public (prior owner); workflow file move needs `workflow` scope token.
