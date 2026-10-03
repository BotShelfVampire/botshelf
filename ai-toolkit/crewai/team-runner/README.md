# CrewAI team runner

Status: **UNTESTED_RUNTIME**. Original BSV starter (MIT). BSV has not run it against a real model; `--self-test` only checks the control flow with a fake crew.

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

## References

- CrewAI LLM connections: https://docs.crewai.com/concepts/llms
- Ollama OpenAI compatibility: https://github.com/ollama/ollama/blob/main/docs/openai.md
- LM Studio OpenAI-compatible server: https://lmstudio.ai/docs/app/api/endpoints/openai
