# n8n team runner

Status: **UNTESTED_RUNTIME**. Original BSV starter (MIT). `--self-test` checks the generated structure. BSV imported the 10 generated workflows into n8n 2.41.6 with the CLI and executed one against a local stub OpenAI-compatible server (success, section check ran). Smoke test (2026-10-04, `scripts/site/smoke_team_runners.py`, repeatable): this file unchanged builds the workflow, the n8n 2.41.6 CLI imports and executes it against a local stub with scripted replies: 1 request with the pasted system prompt and your input; the section check flags a missing section and passes a complete answer; nothing is written; with the proxy pointed at a local recorder, no outside call was seen. That checks the wiring with the real n8n only, not answer quality on a real model. It has not been run against a real model, so it is not runtime verified.

`make_workflow.py` builds one importable n8n workflow per BSV Library AI Team task:

```
Manual Trigger -> Task input -> Local model (HTTP, OpenAI-compatible) -> Section check -> Review
```

- Runs only when you click **Test workflow** (manual trigger, workflow inactive).
- Calls a **local** OpenAI-compatible server (LM Studio `http://localhost:1234/v1` by default, or Ollama `http://localhost:11434/v1`). No cloud LLM node, no API key in the JSON.
- The Code node compares the answer with the prompt's `OUTPUT:` list and reports missing sections.
- No write, email, chat, shell or schedule nodes. You read the result in the execution view and copy it yourself — that is the approval step.

## Use

1. Pick a task id from `tasks.json` (10 tasks = the 10 Library AI Teams).
2. Open its `full_text_page` (the n8n version of the team, free email verification) and paste the page text, or just the system prompt, into `prompts/<task>.txt`.
3. Build and import:

```bash
python make_workflow.py --self-test
python make_workflow.py --task doc-review --model <model id shown by your server>
# n8n UI: Workflows > Import from file > out/doc-review.workflow.json
# n8n CLI: n8n import:workflow --input=out/doc-review.workflow.json
```

4. In n8n, edit **Task input → user_input**, then click **Test workflow**. If n8n runs in Docker, use `http://host.docker.internal:1234/v1` as `--base-url`.

## References

- n8n HTTP Request node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/
- n8n Code node: https://docs.n8n.io/code/code-node/
- n8n import/export of workflows: https://docs.n8n.io/workflows/export-import/
