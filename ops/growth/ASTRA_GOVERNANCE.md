# BSV delivery responsibilities

The owner directed on 2026-10-06 JST that Astra is the highest decision-maker
within this work team after the owner, and that Astra issues instructions.
This records work coordination; it grants no account, credential, security,
spending, or system permissions and does not override platform requirements.

- Owner: objectives, constraints and final authority.
- Astra (`gpt-6-astra`): priorities, assignments, conflict resolution and release review.
- GrokBot: current production source, implementation, integration and sole production deployment.
- Codex implementation/QA worker: independent checks, focused proposed patches and evidence for Astra.

Current directive: https://github.com/BotShelfVampire/botshelf/issues/4#issuecomment-6017081899
Integration branch: `new-bobby/live-toolkit-integration` (PR #5).
The public repository is not the complete production source. Do not deploy it
over the live site or overwrite concurrent GrokBot work. Existing deploy-budget
and production-context rules continue to apply. Independent QA changes target
the integration branch for review; merging them is not proof of deployment.

## Delivery sequence

1. Fresh-read Issue #4, PR #5 and the current Netlify production deploy.
2. Astra determines the next coherent batch. Preserve the owner's eight peer
   categories and natural EN/JA UI and content localization. Prompts, code and
   identifiers retain their correct syntax.
3. GrokBot implements against current production. Independent QA checks the
   precise revision and avoids simultaneous edits to generators/i18n/homepage.
4. Give Astra the commit, diff, tests, browser evidence, known limitations and
   production integration/rollback plan. Astra decides release readiness.
5. GrokBot deploys within the existing budget. Verify the published deploy,
   changed public pages and existing source/access gates before calling it LIVE.

## Continuity

While work is active, review meaningful Issue/PR updates. After publication,
run a lightweight public-page/release check daily and a deeper eight-domain,
EN/JA, listing/detail/body and mobile/desktop review weekly. Continue useful
improvements under Astra's instructions, not repetitive breadth for its own sake.
Keep routine unchanged results quiet; notify only meaningful completion,
failure, or newly required owner action. Avoid duplicate monitors.

Run `python3 scripts/site/audit_growth_readiness.py --output <local-report.json>`
for anonymous HTTP/static checks. This is supplemental to existing tests.
It deliberately never grants rendered-UX or release approval. Read the
unverified browser matrix and complete it against the actual candidate deploy.
The JSON contract is an acceptance inventory, not a record of completed tests.

Do not publish customer data or session material in evidence. Authentication,
payments, prices, wallets and entitlements are outside this growth batch.
No customer email or social publication is authorized by this file.
