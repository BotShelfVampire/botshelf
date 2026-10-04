# LangGraph team runner

Status: **UNTESTED_RUNTIME**. Original BSV starter (MIT). BSV has not run it against a real model; `--self-test` only checks the graph wiring with a fake model. Smoke test (2026-10-04): BSV ran this file unchanged on langgraph 1.2.12 + openai 2.54.0 against a local stub server with scripted replies (`scripts/site/smoke_team_runners.py`; no model, no paid API, no external network): 3 requests: draft, missing-section rewrite, reviewer revise; approval interrupt; saved file = approved draft; `no` saves nothing. That checks the wiring with the real library only, not answer quality on a real model.

Runs one BSV Library AI Team task (doc review, coding review, deep research, …) as a LangGraph graph with a local model:

```
produce (local model) -> check required sections -> human approval (interrupt) -> save to ./out
```

- Model: any OpenAI-compatible server. LM Studio is the default (`http://localhost:1234/v1`); for Ollama use `http://localhost:11434/v1`.
- Missing sections trigger at most two automatic rewrites.
- Nothing is saved unless you type `yes`. Nothing is published, sent or spent.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python runner.py --self-test            # wiring test, no model needed
```

1. Pick a task id from `tasks.json` (10 tasks = the 10 Library AI Teams).
2. Open its `full_text_page` (free email verification) and paste the SYSTEM block into `prompts/<task>.txt`.
3. Start a local model server (LM Studio → Developer → Start server, or `ollama serve`).

## Run

```bash
export BSV_LLM_BASE_URL=http://localhost:1234/v1   # Ollama: http://localhost:11434/v1
export BSV_LLM_MODEL=<model id shown by your server>
python runner.py --task doc-review --dry-run       # parsed sections and plan
python runner.py --task doc-review --input notes.md
```

At the approval step answer `yes`, `no`, or `revise: <feedback>`.

## References

- LangGraph human-in-the-loop (interrupt): https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
- LM Studio OpenAI-compatible server: https://lmstudio.ai/docs/app/api/endpoints/openai
- Ollama OpenAI compatibility: https://github.com/ollama/ollama/blob/main/docs/openai.md
