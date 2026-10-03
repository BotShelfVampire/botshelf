# OWNER WAKE DIRECTIVE

Status: ACTIVE P0.

Do not idle or wait for another routine instruction.

If no work is currently running, resume now from the highest-value unfinished LIVE Trader/AI integration item. Continue implementation → test → deploy → live verify → fix → next item.

A local source commit is not completion. A plan is not completion. A test-only result is not completion. The current milestone is live category expansion.

Only stop for a true owner-only approval/access gate.

---

# Status 2026-10-03 18:15 JST (New Bobby) — cycle 5 LIVE

LIVE deploy: `6ac0c6e9cbb08b40513ed4c8` (production, email_configured:true before/after). Chain: `6ac0c0f4` (cycle 4) → `6ac0c579` (cycle 5) → `6ac0c6e9` (refs fix). Deploy tree `/workspace/bsv-live/deploy` (ops box). Commits `ba29ba1`, state commits after it.

Shipped this cycle (all three queued items):
1. Generator: NinjaTrader 8 (NinjaScript) and Quantower C# targets compute indicators/signals/plots/closed-bar alerts; builder has 8 tabs. Docs: trader README, compatibility, build guide, platforms/ninjatrader|quantower READMEs. UNTESTED_RUNTIME.
2. Builder recipe check (lint) + per-target compile checklist (advisory; never blocks rendering). Fixes: "Fix order" (stable dependency reorder) and "Remove <id>" for unused blocks.
3. AI toolkit: `ai-toolkit/langgraph/team-runner/` (StateGraph produce → section check → `interrupt` approval → save) and `ai-toolkit/crewai/team-runner/` (lead + checker → section check → approval → save). Per-task links to the 10 gated Library Teams both ways. `--self-test` passed in a box venv (langgraph 1.2.12; crewai 1.15.23 object construction with patched kickoff) — wiring only, not runtime evidence.

Tests (pass): parity 112/112; share/hints/lint/checklist 541; toolkit local+LIVE public=54 gated=77; LIVE trader gate 72/0; LIVE library gate 879/0; LIVE runner source anon 302 / session 200 byte-match; LIVE real-browser render via CSP-forwarding proxy (`qa/cdp_builder_v3.py`, `qa/cdp_ai_runners.py`): builder 0 CSP violations; runner pages 0 own violations (the 2 seen come from the pre-existing inline `<style>` on Library runtime pages).

Next queue (in order):
1. Library CSP cleanup: move the shared inline `<style>` on ~915 Library pages to a hashed CSS file, gold hover → green accent; verify LIVE in a real browser (0 CSP violations).
2. Compile-checklist evidence capture: a place to attach owner/user compile results per target without claiming BSV runtime tests.
3. Next generator targets: Sierra Chart (ACSIL C++), then ProRealTime (ProBuilder); GoCharting/MotiveWave/Vela after.
4. AI toolkit: per-task runners for more frameworks (n8n / OpenAI Agents SDK) using the same gated-prompt pattern.
5. Move `scripts/site/site-integration-check.workflow.yml` into `.github/workflows/`, extend trader CI to 8 targets and py_compile the team runners (needs a `workflow`-scope token — owner).
6. Owner decisions already made (do not reopen): public GitHub repos stay public (provenance only); `/cross-ai/kits/research-desk-local/` left as is. No SNS/Discord/external posts.

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
