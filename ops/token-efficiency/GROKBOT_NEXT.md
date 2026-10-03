# OWNER WAKE DIRECTIVE

Status: ACTIVE P0.

Do not idle or wait for another routine instruction.

If no work is currently running, resume now from the highest-value unfinished LIVE Trader/AI integration item. Continue implementation → test → deploy → live verify → fix → next item.

A local source commit is not completion. A plan is not completion. A test-only result is not completion. The current milestone is live category expansion.

Only stop for a true owner-only approval/access gate.

---

# Status 2026-10-03 17:50 JST (New Bobby) — cycle 4 LIVE

LIVE deploy: `6ac0c0f48e544dc4923b42da` (production, email_configured:true before/after). Chain: `6ac0b8e6` (cycle 3) → `6ac0bff1` (builder v2) → `6ac0c0f4` (MQL5/cTrader C# upgrade). Do not rebuild from scratch; deploy tree `/workspace/bsv-live/deploy` (ops box).

Shipped this cycle:
1. Builder v2 (gated `/trading/items/bsv-builder.html`): per-block TODO badges + EN/JA hints for the selected target; share link (`#r=` sanitized config / `#s=<starter>`), JSON file import, sanitized JSON download, "restore previous draft"; share survives email verification via a 24h browser-only stash on the public page. Config only — no generated code or BSV source in links.
2. Fix: builder CSS was inline `<style>` and blocked by production CSP (`style-src 'self'`) → now `/trading/assets/bsv-builder.<hash>.css`.
3. Generator: MQL5 and cTrader C# targets now compute indicators/signals/plots/closed-bar alerts (TODO markers MQL5 90→33, cTrader C# 52→19 over 14 recipes). Still UNTESTED_RUNTIME.
4. Team pages: GitHub registry path shown as neutral provenance (no "link after verification" claim).

Tests (pass): parity 84/84; share/sanitizer/hints 406 checks; local+LIVE toolkit public=52 gated=73; LIVE trader gate 72/0; LIVE library gate 879/0 (at `6ac0b8e6`; library unchanged since); LIVE builder via CSP-forwarding proxy: grid layout, 6 tabs, hints, share→load, public stash→load, 0 CSP violations.

Next queue (in order):
1. NinjaTrader 8 (NinjaScript C#) generator target + builder tab (same computing pattern), then Quantower.
2. Builder: per-target "compile checklist" panel and recipe-level lint (unused blocks, refs to later ids) before render.
3. AI toolkit: add runnable starters for LangGraph/CrewAI jobs that link to the gated Library Teams (catalog → build_live_toolkit → crosslinks).
4. Move `scripts/site/site-integration-check.workflow.yml` into `.github/workflows/` and extend trader CI to 6 targets (needs a token with `workflow` scope — owner).
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
