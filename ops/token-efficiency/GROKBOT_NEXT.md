# OWNER WAKE DIRECTIVE

Status: ACTIVE P0.

Do not idle or wait for another routine instruction.

If no work is currently running, resume now from the highest-value unfinished LIVE Trader/AI integration item. Continue implementation → test → deploy → live verify → fix → next item.

A local source commit is not completion. A plan is not completion. A test-only result is not completion. The current milestone is live category expansion.

Only stop for a true owner-only approval/access gate.

---

# Status 2026-10-03 18:07 JST (New Bobby) — cycle 5 LIVE

LIVE deploy: `6ac0c5791377cbb24d114800` (production, email_configured:true before/after). Chain: `6ac0c0f4` (cycle 4) → `6ac0c579` (NT8 + Quantower + LangGraph/CrewAI). Deploy tree `/workspace/bsv-live/deploy` (ops box). Commit `ba29ba1`.

Shipped this cycle:
1. Generator: NinjaTrader 8 (NinjaScript C#) and Quantower C# targets compute indicators/signals/plots/closed-bar alerts (TODO over 14 recipes: NT8 19, Quantower 19). Honest UNTESTED_RUNTIME; Runtime-tested by BSV = 0.
2. Builder: 8 target tabs (Pine/MQL5/MQL4/cTrader C#/Python/Bookmap/NinjaTrader/Quantower) + compile checklists for NT8/Quantower.
3. AI toolkit: LangGraph team-runner and CrewAI team-runner starters (local model, per-task); catalog 12→14; cross-links updated.

Tests (pass): parity 112/112 (14×8); share/sanitizer/hints 541 checks; local+LIVE toolkit public=54 gated=77; LIVE trader gate 72/0; gated builder session confirms 8 tabs + renderNinja/renderQuantower; health email_configured:true.

Next queue (in order):
1. Builder: per-target "compile checklist" panel polish and recipe-level lint UX (unused blocks, refs to later ids) — scaffolding already present; expand coverage.
2. Remaining platforms after NT8/Quantower: Sierra Chart, GoCharting, ProRealTime, MotiveWave, Vela, OpenMarkets (starters already in platforms/; generator targets as needed).
3. AI toolkit: more runnable starters / team job wiring as catalog grows.
4. Move `scripts/site/site-integration-check.workflow.yml` into `.github/workflows/` and extend trader CI to 8 targets (needs a token with `workflow` scope — owner).
5. Owner decisions already made (do not reopen): public GitHub repos stay public (provenance only); `/cross-ai/kits/research-desk-local/` left as is. No SNS/Discord/external posts.

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
