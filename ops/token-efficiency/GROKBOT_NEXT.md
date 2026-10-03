# OWNER WAKE DIRECTIVE

Status: ACTIVE P0.

Do not idle or wait for another routine instruction.

If no work is currently running, resume now from the highest-value unfinished LIVE Trader/AI integration item. Continue implementation → test → deploy → live verify → fix → next item.

A local source commit is not completion. A plan is not completion. A test-only result is not completion. The current milestone is live category expansion.

Only stop for a true owner-only approval/access gate.

---

# Status 2026-10-03 17:18 JST (New Bobby) — cycle 3 LIVE

LIVE deploy: `6ac0b8e61e7f01df9ceef1db` (production, email_configured:true). Prior: pack-gate batches through `6ac0b458`, then this cycle adds MT4 / Bookmap / cTrader Python + 2 recipes + 6 generator targets. Do not rebuild from scratch.

Shipped this cycle:
1. Library pack body gate generalised: 809 pack items (skills, kimi-*, gemini, deepseek, cursor, claude-code, dify, flowise, autogen, openrouter, agentswarm, mcp, …) + 70 teams = 879 gated; title/summary public; full body at `/library/source/item-*` / `team-*` behind email session. Free labels kept. `*.bak*` pruned earlier.
2. Trader: MT4 (MQL4), Bookmap (Python API), cTrader Python — catalog → build pages → filters → recipe builder (6 targets: pine-v6, mql5, mql4, ctrader, ctrader-python, bookmap-python). +2 recipes (golden-cross-alert, ema-cross-rsi-filter). Hub = 37 assets, 13 platform filters. Honest UNTESTED_RUNTIME / STRUCTURAL labels only.

LIVE URLs:
- https://botshelfvampire.com/trading/build/ (37 assets; MT4 + Bookmap filters)
- https://botshelfvampire.com/trading/tools/bsv-mt4-ema-atr.html
- https://botshelfvampire.com/trading/tools/bsv-bookmap-trade-ema.html
- https://botshelfvampire.com/trading/tools/bsv-ctrader-python-ema-atr.html
- https://botshelfvampire.com/trading/tools/bsv-builder.html (6 targets)
- https://botshelfvampire.com/library/toolkit/
- Pack example (gated): /library/source/item-skills-accessibility-audit-skill.html → 302 anonymous

Tests (pass): builder parity 84/84; local toolkit ok; local gate 879/0 err; LIVE toolkit public=52 gated=73; LIVE gate 879 logged-in 0 err; health email_configured:true before/after --prod.

Next queue (in order):
1. Builder v2: per-target TODO hints and shareable recipe JSON links (no server storage).
2. Move `scripts/site/site-integration-check.workflow.yml` into `.github/workflows/` (needs token with `workflow` scope — owner).
3. Owner-only leftovers (do not invent): public GitHub repos still hold bodies (`botshelf-ai-team-registry`, `botshelf/packs`); `/cross-ai/kits/research-desk-local/` overlaps two Open WebUI bodies (left as-is per prior owner). No SNS/Discord/external posts.

---

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
