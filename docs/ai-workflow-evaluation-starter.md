# AI workflow evaluation starter

A workflow that runs without crashing is not necessarily useful or safe. Evaluate the exact version, model, runtime, prompts, tools, and approval rules that a user will receive.

This starter is platform-neutral. Use it for Grok Bot, Claude Code, ChatGPT, local models, MCP tools, and multi-step workflows. It does not turn a test result into a guarantee.

## 1. Define success before running

Write one job and the decisions the output may influence. Then define measurable acceptance criteria.

Use at least these dimensions:

- **Source fidelity:** every factual claim, number, date, quote, and named entity is supported by the supplied input.
- **Missing information:** unknown facts remain unknown instead of being guessed.
- **Instruction handling:** untrusted content cannot change the workflow's authority, permissions, or destination.
- **Action boundary:** sending, publishing, spending, deleting, deploying, and access changes stop at the required approval point.
- **Task usefulness:** the output completes the stated job in a form the intended user can inspect.
- **Operational behavior:** tool errors, timeouts, missing files, and non-zero exits are surfaced rather than converted into success.

Define blocking failures separately. For a source-based workflow, an invented number or false approval should fail the case even if the writing is polished.

## 2. Build a small case set

Start with cases that resemble the real job:

1. A normal case with complete inputs.
2. A case with exact numbers, dates, and similar names.
3. A case with conflicting sources.
4. A case with required information missing.
5. A case containing instructions inside untrusted source text.
6. A case where a tool, model, or handoff fails.
7. A repeated or near-duplicate request.
8. A case that reaches a send, publish, spend, or delete boundary.

Write expected facts, forbidden claims, approval boundaries, and required output fields **before** running the workflow. Do not create the answer key after seeing the model output.

Use the machine-readable [evaluation run template](eval-run-template.json) to keep cases, criteria, raw outputs, and results together.

Start with the eight synthetic records in [evaluation test cases](eval-test-cases.jsonl). They cover exact values, conflicting sources, missing information, untrusted instructions, approval boundaries, dependency failure, and duplicate external actions. Replace or extend them with cases from the real job before drawing conclusions.

Validate saved records against the [JSON Schema](eval-run.schema.json). The dependency-free repository checker adds duplicate-ID, case-reference, blocking-failure, and summary-total checks:

```bash
node scripts/validate-eval-run.mjs path/to/eval-run.json
```

A validator confirms record structure and internal consistency. It does not judge factual quality or prove model reliability.

See the [synthetic failed run](eval-run-example-failed.json) for a complete record. It deliberately contains altered facts and a false approval, is marked `evaluation_failed`, and did not call a model or external tool.

## 3. Record the exact run

For every run, retain:

- workflow revision or commit;
- model name, provider, version or digest;
- runtime and relevant settings;
- original input and source files;
- generated prompts for each step;
- raw model outputs;
- tool calls, errors, handoffs, and exit codes;
- grader version and rubric;
- human decisions, clearly separated from model decisions.

Redact secrets and personal data. A screenshot of a final answer is not enough to reconstruct a multi-step run.

## 4. Grade in the safest order

Use deterministic checks first when the rule can be expressed exactly:

- required fields exist and are non-empty;
- numbers and dates match allowed source values;
- cited text exists in the named source;
- a send or publish action did not occur;
- a failed dependency produced a failed run;
- output is valid against the declared schema.

Then use a human or model grader for judgments that need context, such as relevance or clarity. Validate an LLM grader against known good and known bad examples before scaling it.

A grader must not award a pass to an empty object, an output with the wrong source, or a response that merely says “HOLD” while inventing its reason. Store the grader's evidence, not only its label.

## 5. Compare against a baseline

Test the workflow against a simpler baseline that can perform the same job, such as one model with the same source material and restrictions.

Keep the workflow only when it provides a measurable benefit: better source fidelity, safer action handling, clearer output, lower cost, lower latency, or another criterion defined in advance. Extra agents and handoffs are not benefits by themselves.

Use repeated runs for variable outputs. Report the case count and failures; do not turn a small test into a universal reliability claim.

## 6. Publish the honest status

Use plain status labels:

- **Design only:** instructions exist; no recorded model run.
- **Runs:** at least one real run is preserved.
- **Evaluation failed:** the workflow ran but missed blocking criteria.
- **Limited pass:** named cases passed under the recorded setup; limitations remain.
- **Production claim:** requires evidence from the actual production version, delivery path, permissions, and user-facing experience.

Keep failed evidence. If prompts, models, tools, or grader logic change, record a new evaluation instead of rewriting the old result.

Marketplace products and Build Library materials remain separate. A local experiment is not automatically a ready-to-use Marketplace product.

## Report a reproducible failure

Use the [workflow quality report](https://github.com/BotShelfVampire/botshelf/issues/new?template=workflow-quality-report.yml) for a public, redacted report. Do not include credentials, private prompts, customer data, wallet information, or personal records.

## Primary references

- [OpenAI: Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals)
- [OpenAI: Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
- [Anthropic: Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)

OpenAI recommends using traces to inspect model calls, tool calls, guardrails, and handoffs, then moving stable cases into datasets and eval runs. Anthropic recommends specific, measurable, task-relevant success criteria, real-world cases and edge cases, deterministic grading where possible, and validating model-based graders.

BotShelf Vampire is independent of OpenAI, Anthropic, and xAI.
