# BSV Token-Efficiency Operating Layer

Purpose: keep BSV work moving to completion while reducing repeated frontier-model context and duplicate reasoning between ChatGPT and GrokBot.

## Core rule

Use the cheapest reliable mechanism that can complete a step without lowering correctness:

1. Deterministic tools — GitHub search/read, CI, parsers, linters, tests, structured extraction.
2. Cached/retrieved context — read only files/lines/diffs relevant to the current task.
3. Local LM Studio — low-risk compression, classification, metadata extraction, draft normalization.
4. External OpenAI-compatible gateway — caching, routing, budgets and usage tracking for API-driven worker tasks.
5. Frontier ChatGPT/Grok — architecture, ambiguous reasoning, adversarial review, important synthesis and final judgment.

Do not send the same large raw context independently to ChatGPT and GrokBot.

## Client limitation

A gateway only reduces tokens/cost for clients that can point their API/base URL through that gateway.

- API/CLI workers can use Prism/LiteLLM-style gateways.
- Regular ChatGPT conversations are not transparently rerouted through a local proxy.
- When a client cannot be rerouted, use compact shared-state/context packs so it receives much less repeated context.

## Shared-state contract

Both ChatGPT and GrokBot should use:

- ops/token-efficiency/BSV_STATE.md — compact current truth
- ops/token-efficiency/DECISIONS.md — binding decisions only
- GitHub issues — coordination and executable integration tasks
- Git diffs/exact files — implementation context

Do not paste full historical conversations when these artifacts are sufficient.

## Task routing

### Tier 0 — no model

Use for file discovery, exact string/route/license checks, JSON/schema validation, link checking, code syntax/compile CI, changed-file lists, duplicate detection and status extraction.

### Tier 1 — LM Studio / small local model

Use for compressing logs, classifying files, extracting TODOs/prerequisites, deduplicating near-identical descriptions, first-pass copy cleanup and compacting already-trusted context.

Do not let a local model be the sole authority for payment/auth/security architecture, license/legal conclusions, deployment correctness, destructive changes, final verification or Verified claims.

### Tier 2 — external gateway worker

Use an OpenAI-compatible gateway for repetitive API-driven model work when the client supports custom base URLs.

Desired features:
- exact response/prefix caching where safe
- provider prompt caching support
- model routing
- token/cost accounting
- per-task budgets/rate limits
- fallback to local LM Studio or cheaper cloud worker
- traceability of which model actually answered

Keep semantic response caching OFF for correctness-sensitive BSV work unless an eval on that exact task proves an acceptable false-hit rate.

### Tier 3 — frontier reasoning

Use ChatGPT/Grok for architecture, ambiguous platform research, nontrivial code review, security/reliability review, final cross-check and ship/no-ship decisions.

Frontier models receive the compact state + relevant changed files/diffs + decision/evidence, not the full project history.

## Provider-cache discipline

For xAI/Grok API clients: preserve a stable prompt prefix, append new messages instead of editing earlier ones, use a stable conversation/cache key when supported, and measure cached-token usage.

For any provider cache: keep large static instructions/reference material stable at the beginning and volatile task-specific content late.

## Dedupe discipline

Before delegating:
1. Check if the result already exists.
2. Check if another agent is already doing the same task.
3. Pass a narrow deliverable, not 'audit everything'.
4. Reuse the result artifact rather than make the second model rediscover it.

## Output contract

Worker/model outputs should be dense:

RESULT:
EVIDENCE:
FILES_CHANGED:
BLOCKERS:
NEXT:

No progress diary unless it changes a decision.

## Cost/quality guard

Optimization succeeds only if frontier input falls while throughput stays equal/improves and rework/defects do not rise. If compressed context causes misses, raise the retained-context budget for that task class.

## Current BSV policy

- Work/Codex/frontier workers only when concretely useful.
- LM Studio is an accelerator, not project lead.
- External gateways are infrastructure, not a reason to add extra model calls.
- Human/owner interruption should decrease, not increase.
