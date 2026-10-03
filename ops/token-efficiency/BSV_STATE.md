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

## LIVE integration status (New Bobby, 2026-10-03 16:45 JST)

- Production deploy: `6ac0b1259b77b94c2b9efa8c` (context `production`). Chain from `6abefaf5`: drafts `6ac0a8ff` → `6ac0a9e0` → `6ac0aa87` → `6ac0ab20` (published as drafts), then `--prod` deploys `6ac0ad52` (context fix) → `6ac0af32` (Library gate) → `6ac0b125` (builder + cross-links). Nothing was rolled back. The unpublished `6abf02a9` (skipped for credits) was **not** included. The never-published draft `6ac0a8e4` was deleted.
- Incident (fixed): published drafts ran in `deploy-preview` context, so production-only env (SMTP, operator email) was missing from 16:04 to 16:23 JST. OTP registration/verify returned `error` and the operator digest paused. `--prod` redeploy fixed it; `/api/commerce/health` shows `email_configured:true` and the digest ran again at 16:25 JST.
- Trader (existing category): https://botshelfvampire.com/trading/build/ is the "Build your own chart tool" hub.
  - It holds 32 assets: 20 catalog entries and 12 recipes, plus the recipe builder.
  - It has filters for 11 platforms, type and test status. Vela is a first-class path. OpenMarkets is shown as data/agent integration.
  - Recipe builder: public summary https://botshelfvampire.com/trading/tools/bsv-builder.html; gated tool `/trading/items/bsv-builder.html` (edits blocks, renders Pine v6 / MQL5 / cTrader in the browser). Browser port output = `render.mjs` output for 36/36 cases.
- AI (existing Library): https://botshelfvampire.com/library/toolkit/ has 12 items by job and framework (Dots, Hugging Face, Bionic, smolagents, Letta, OpenAI Agents SDK). Cross-linked both ways with the 10 Library AI Teams (`/library/teams/`).
- Library team implementations (70): explanation/files/examples public; full prompt/config/code only at `/library/source/team-<runtime>-<team>.html` behind the verified session; still labelled free. `items.json` has no bodies. `*.bak*` backups (some held gated pages) and library generator scripts no longer deployed.
- Gated paths: `/trading/items|sources|downloads/*`, `/library/source/*`, `/registered`, `/switchboard-cos`.
- LIVE tests (all pass): `test_live_toolkit.py --live` (47 public + 66 gated); `test_library_gate.py --live --cookies` (70 bodies: anonymous no body + 302, test session 200 with exact body; items.json/search/sitemap/llms clean); gated 84 files anonymous 302 vs test session 200 byte-identical; builder rendered logged-in in headless Chrome.
- Logged-in QA: operator test account `support@botshelfvampire.com` (name `OTP test`, classified test). Runtime-tested by BSV = 0.
- Open (owner decision): the bodies are also in public GitHub repos (`botshelf-ai-team-registry`, `botshelf/packs`) that the pages link to; `/cross-ai/kits/research-desk-local/` (separate free kit) is public and overlaps two Open WebUI bodies; ~809 other Library items (skills, kimi, gemini, …) still show bodies publicly.
