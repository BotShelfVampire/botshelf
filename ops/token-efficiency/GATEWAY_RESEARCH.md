# BSV gateway / token-reduction research

Updated: 2026-10-03

## What actually reduces frontier token spend

1. Do not resend irrelevant project history.
2. Reuse provider prompt caches by preserving stable prefixes.
3. Use exact response caching for genuinely identical deterministic requests.
4. Route low-risk repetitive work to a cheaper/local model.
5. Use deterministic tools instead of LLMs where possible.
6. Compress long context only when the task tolerates compression and the result is checked.

## Prism

There are multiple unrelated projects named Prism. Do not bind BSV to a name alone.

One open-source Prism gateway (Zshnreza/prism) provides an OpenAI-compatible front door, multi-provider routing, cost tracking, exact response caching, rate limiting and fallback, including local Ollama.

Another Prism implementation has measured a useful warning: exact/prefix caching can save heavily, but its semantic cache produced unacceptable false-hit behavior on its own benchmark and was shipped disabled. BSV adopts that lesson: semantic response caching is OFF by default for correctness-sensitive work.

Prism is a candidate where the worker/client supports a custom base URL. It does not transparently reroute a normal ChatGPT product conversation.

## LiteLLM

LiteLLM is currently the strongest generic gateway candidate for BSV API-driven worker traffic because it exposes an OpenAI-compatible gateway, supports many providers including OpenAI/xAI/local providers, supports routing/fallback and response caching, and can enforce token/cost budgets when configured with its required persistent backing store.

Do not claim a LiteLLM budget is enforced in a DB-less proxy; current docs explicitly warn otherwise.

## Native provider prompt caching

### xAI / Grok API

xAI automatically prompt-caches matching starting messages. For API-driven Grok workers:
- keep earlier messages byte-stable and append new ones
- use x-grok-conv-id for Chat Completions or prompt_cache_key for Responses when supported
- monitor cached token counters
- do not edit/reorder the shared prefix

This is preferable to sending the same giant rewritten prompt each turn.

### OpenAI API

OpenAI prompt caching also works on reusable prompt prefixes. For API-driven OpenAI workers:
- place stable rules/tools/reference material first
- keep volatile task data late
- preserve conversation/tool-definition stability
- use cache controls/cache keys supported by the chosen model/API
- measure cached input rather than assuming reuse

Regular ChatGPT UI traffic is a separate product path; BSV cannot force the current interactive chat through our own proxy. We reduce its token footprint through compact state, exact file retrieval, tooling and shared artifacts instead.

## LM Studio

LM Studio exposes OpenAI-compatible local endpoints, including /v1/responses and /v1/chat/completions, and can therefore serve low-risk local worker steps without rewriting every client.

BSV local-use policy:
- log compression
- file classification
- metadata/TODO extraction
- duplicate copy detection
- first-pass context compaction

Not sole authority for production PASS, security/payment/auth, licensing/legal judgments or destructive changes.

## LLMLingua

LLMLingua/LLMLingua-2 is a credible optional prompt-compression layer and reports large compression in its research/examples. BSV should benchmark it on our own context packs before using it for engineering-critical prompts.

Safe candidate tasks:
- long meeting/log prose
- redundant historical narrative
- RAG/context excerpts where exact code is not required

Do not run source code, exact error logs, cryptographic/payment details, binding commercial rules or license text through lossy compression by default.

## Recommended BSV topology

API-configurable worker
  -> deterministic context pack
  -> optional local compactor (LM Studio)
  -> gateway (LiteLLM or evaluated Prism)
       -> local LM Studio for low-risk
       -> cheap cloud worker for repetitive synthesis
       -> Grok/OpenAI frontier only for high-value reasoning

Interactive ChatGPT / fixed-client GrokBot
  -> BSV_STATE.md + DECISIONS.md
  -> exact current diffs/files
  -> GitHub issue coordination
  -> no replay of full project history

## Adoption order

NOW:
- compact shared state
- deterministic context-pack builder
- LM Studio compactor script
- xAI cache discipline for any Grok API worker
- exact cache only where input is truly identical
- stop duplicate ChatGPT/Grok discovery

NEXT, only when a configurable API worker actually needs it:
- run LiteLLM or a vetted Prism locally
- connect LM Studio as free/local fallback
- add provider API keys through environment/secrets only
- measure hit rate, cached tokens, cost and failures

LATER:
- evaluate LLMLingua on a BSV golden set
- semantic cache remains off until measured false-hit risk is acceptable

## Success metrics

- frontier input tokens per completed task
- cached-token ratio
- number of duplicate model calls
- local/deterministic completion share
- task lead time
- rework/defect rate
- owner interruptions per completed deliverable
