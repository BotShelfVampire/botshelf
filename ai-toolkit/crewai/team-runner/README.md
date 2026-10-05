# CrewAI team runner

Status: **UNTESTED_RUNTIME**. Original BSV starter (MIT). BSV has not run it against a real model; `--self-test` only checks the control flow with a fake crew. Smoke test (2026-10-04): BSV ran this file unchanged on crewai 1.15.23 against a local stub server with scripted replies (`scripts/site/smoke_team_runners.py`; no model, no paid API, no external network): lead then checker, a second round when a section is missing, checker answer saved after `yes`; `no` saves nothing. That checks the wiring with the real library only, not answer quality on a real model.

Runs one BSV Library AI Team task as a two-agent crew on a local model:

```
lead (does the job) -> checker (fills gaps from the input only) -> section check -> your approval -> save to ./out
```

- Missing sections trigger at most two automatic rewrites.
- Nothing is saved unless you type `yes`. Nothing is published, sent or spent.
- The prompt is never passed as `inputs=` to `kickoff()`, so braces in the prompt are not template-interpolated.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python crew_runner.py --self-test       # control-flow test, no model needed
```

1. Pick a task id from `tasks.json` (10 tasks = the 10 Library AI Teams).
2. Open its `full_text_page` (free email verification) and paste the SYSTEM block into `prompts/<task>.txt`.
3. Start a local model server.

## Run

```bash
# LM Studio
export BSV_LLM_BASE_URL=http://localhost:1234/v1 BSV_LLM_MODEL=openai/<model id>
# Ollama (OpenAI-compatible endpoint)
# export BSV_LLM_BASE_URL=http://localhost:11434/v1 BSV_LLM_MODEL=openai/<model>
python crew_runner.py --task doc-review --dry-run
python crew_runner.py --task doc-review --input notes.md
```

## Evidence record (optional)

```bash
python crew_runner.py --task doc-review --input notes.md --eval-record evidence/doc-review.json
```

Each run adds one case and one run to that file in the BSV eval record format ([schema 1.0](https://github.com/BotShelfVampire/botshelf/blob/main/docs/eval-run.schema.json)). Check it with `node scripts/validate-eval-run.mjs evidence/doc-review.json` from the BSV repository.

- A run is `passed` only if every required section is present and you typed `yes`. A missing section or `no` is recorded as `failed`.
- Only what the runner can check is recorded: the section check, revisions and your answer. The task input and the draft are stored as sha256 only.
- Facts, numbers, dates and quotes are **not** checked. Compare the saved output with your source (Regression Checklist evidence check) before you rely on it, and fill in `summary.human_reviewer` yourself.
- Use one file per task, runner and prompt. A file for another task, runner or prompt text is refused before the model is called.
- `eval_record.py` is standard library only and identical in the LangGraph, CrewAI and OpenAI Agents SDK runners. Smoke test (2026-10-05): records from all three runners pass the validator on the local stub server (`scripts/site/smoke_team_runners.py`). Not a real model run.

## References

- CrewAI LLM connections: https://docs.crewai.com/concepts/llms
- Ollama OpenAI compatibility: https://github.com/ollama/ollama/blob/main/docs/openai.md
- LM Studio OpenAI-compatible server: https://lmstudio.ai/docs/app/api/endpoints/openai
