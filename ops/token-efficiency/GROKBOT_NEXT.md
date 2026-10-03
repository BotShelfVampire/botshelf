# OWNER WAKE DIRECTIVE

Status: ACTIVE P0.

Do not idle or wait for another routine instruction.

If no work is currently running, resume now from the highest-value unfinished LIVE Trader/AI integration item. Continue implementation → test → deploy → live verify → fix → next item.

A local source commit is not completion. A plan is not completion. A test-only result is not completion. The current milestone is live category expansion.

Only stop for a true owner-only approval/access gate.

---

# Status 2026-10-03 16:14 JST (New Bobby)

Tranches 1–4 are LIVE. See BSV_STATE.md "LIVE integration status" and scripts/site/README.md.
Do not rebuild these surfaces from scratch. Re-run `scripts/site/build_live_toolkit.py` on a fresh production tree when the catalogs change.

Next queue (in order):
1. A gated in-browser recipe builder at /trading/items/bsv-builder.html. It edits blocks and renders Pine/MQL5/cTrader in the browser, using a browser port of generator/render.mjs.
2. Logged-in QA of the gated pages, using an owner-provided verified test session.
3. A Library teams/registry cross-link for the AI toolkit items (registry.json, /library/teams/).
4. More trader platforms and recipes from ChatGPT source (MT4 renderer, Bookmap, cTrader Python), using the same pipeline.

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
- cTrader
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
