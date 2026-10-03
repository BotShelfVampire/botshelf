# BSV Bionic Delegation Protocol

Use LM Studio Bionic as a **low-cost parallel worker**, not as the final authority.

Bionic can work with a selected codebase folder, run commands, edit files, use Git, and keep multiple focused sessions in one project. Choose local inference for routine work when the available model is capable enough; switch to stronger compute only when the task actually needs it.

Official docs:
- https://lmstudio.ai/docs/bionic
- https://lmstudio.ai/docs/bionic/quick-start
- https://lmstudio.ai/docs/bionic/models

## Project setup

Project folder: the current BSV working tree.

Before each Bionic session, give it:
- `ops/token-efficiency/BSV_STATE.md`
- `ops/token-efficiency/DECISIONS.md`
- the exact relevant files only
- one concrete deliverable
- one verification command

Do not paste full historical chats.

## Good Bionic jobs

- scan a directory and classify assets
- find duplicated or stale copy
- generate metadata/index entries from already-approved files
- convert a known content pattern to another file format
- check broken relative links
- write tests around already-defined behavior
- normalize README sections
- compare two file trees
- extract TODOs from current source
- prepare first-pass platform adapters that are then reviewed by CI/frontier model

## Jobs that require frontier review

- security/payment/auth changes
- production PASS/Verified verdict
- licensing/legal interpretation
- irreversible/destructive changes
- architecture with ambiguous trade-offs
- public claims not directly supported by evidence

## Session prompt template

GOAL
[one concrete deliverable]

READ FIRST
- ops/token-efficiency/BSV_STATE.md
- ops/token-efficiency/DECISIONS.md
- [exact relevant files]

DO
- inspect current files before editing
- preserve newer work
- make the smallest coherent implementation
- run deterministic validation/tests
- keep Unverified/Untested labels honest
- save the result in the repo

DO NOT
- redesign unrelated BSV surfaces
- touch payment/auth/security without explicit scope
- copy proprietary third-party code
- claim runtime verification without runtime evidence
- spend money or call paid cloud inference unless explicitly authorized

RETURN
RESULT:
FILES_CHANGED:
TESTS:
UNVERIFIED:
BLOCKERS:

## Parallelization rule

Use separate Bionic sessions only for independent deliverables. Do not let two sessions edit the same files concurrently.

Preferred split for current BSV expansion:
- Bionic session A: Trader metadata/index/filter ingestion from existing `trader-toolkit/`
- Bionic session B: AI metadata/index ingestion from existing `ai-toolkit/`
- GrokBot: live-site integration and visual QA
- ChatGPT: architecture, current-platform research, source review, shared-state coordination
