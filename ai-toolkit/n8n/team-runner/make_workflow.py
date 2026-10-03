#!/usr/bin/env python3
# BSV n8n team runner — ORIGINAL BSV STARTER (MIT). Not runtime tested by BSV.
# Builds one importable n8n workflow per BSV Library AI Team task:
#   Manual Trigger -> Task input -> Local model (HTTP, OpenAI-compatible) -> Section check -> Review (no-op)
# The workflow only runs when you click "Test workflow". It saves nothing, sends nothing and calls no paid API:
# you read the result in the execution view and copy it yourself (that is the approval step).
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASKS = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))

CHECK_JS = r"""// BSV section check: compares the model answer with the OUTPUT list of the system prompt.
const inp = $('Task input').first().json;
const required = JSON.parse(inp.required_sections || '[]');
const res = $input.first().json;
const draft = (((res.choices || [])[0] || {}).message || {}).content || '';
const low = draft.toLowerCase();
const missing = required.filter(s => {
  const words = s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(w => w.length > 2).slice(0, 3);
  return words.length && !words.every(w => low.includes(w));
});
return [{ json: {
  task: inp.task,
  draft,
  missing,
  all_sections_present: missing.length === 0,
  next_step: missing.length ? 'Sections missing: run again or edit the input.' : 'Review the draft. Nothing was saved or sent; copy it yourself if you approve it.'
} }];"""


def clean_prompt(text: str) -> str:
    m = re.search(r"## Full system prompt[^\n]*\n(.*?)(?:\n## |\Z)", text, re.S)
    return (m.group(1) if m else text).strip()


def required_sections(system_prompt: str):
    out, on = [], False
    for line in system_prompt.splitlines():
        if re.match(r"^\s*OUTPUT\s*:", line, re.I):
            on = True
            continue
        if on:
            m = re.match(r"^\s*\d+[.)]\s*(.+?)\s*$", line)
            if m:
                out.append(m.group(1).rstrip("\u2026").strip())
            elif line.strip():
                break
    return out


def node(i, name, typ, ver, x, params):
    return {"parameters": params, "id": "bsv-%d" % i, "name": name, "type": typ, "typeVersion": ver, "position": [x, 0]}


def build(task: str, system: str, base_url: str, model: str) -> dict:
    t = TASKS["tasks"][task]
    sections = required_sections(system)

    def a(i, name, value):
        return {"id": "a%d" % i, "name": name, "value": value, "type": "string"}
    body = ("={{ JSON.stringify({ model: '%s', temperature: 0.3, messages: ["
            "{ role: 'system', content: $json.system }, { role: 'user', content: $json.user_input } ] }) }}") % model.replace("'", "")
    nodes = [
        node(1, "Manual Trigger", "n8n-nodes-base.manualTrigger", 1, 0, {}),
        node(2, "Task input", "n8n-nodes-base.set", 3.4, 240, {"mode": "manual", "assignments": {"assignments": [
            a(1, "task", task), a(2, "system", system), a(3, "user_input", "PASTE THE TASK INPUT HERE"),
            a(4, "required_sections", json.dumps(sections, ensure_ascii=False))]}, "options": {}}),
        node(3, "Local model", "n8n-nodes-base.httpRequest", 4.2, 480, {
            "method": "POST", "url": base_url.rstrip("/") + "/chat/completions", "sendBody": True,
            "specifyBody": "json", "jsonBody": body, "options": {"timeout": 300000}}),
        node(4, "Section check", "n8n-nodes-base.code", 2, 720, {"jsCode": CHECK_JS}),
        node(5, "Review (nothing is saved or sent)", "n8n-nodes-base.noOp", 1, 960, {}),
    ]
    names = [n["name"] for n in nodes]
    conns = {names[k]: {"main": [[{"node": names[k + 1], "type": "main", "index": 0}]]} for k in range(len(names) - 1)}
    return {"name": "BSV team runner \u2014 " + t["title"], "nodes": nodes, "connections": conns, "settings": {},
            "pinData": {}, "active": False,
            "meta": {"botshelf_job": task, "safety": "manual-trigger-only; no write, send or paid nodes",
                     "status": "UNTESTED_RUNTIME", "source": TASKS["origin"] + t["full_text_page"]}}


def self_test() -> int:
    system = "Test team.\nOUTPUT:\n1) Pass/fail for publish\n2) Blockers\u2026"
    wf = build("doc-review", system, "http://localhost:1234/v1", "local-model")
    types = [n["type"] for n in wf["nodes"]]
    bad = [x for x in types if re.search(r"writeBinaryFile|readWriteFile|executeCommand|emailSend|gmail|slack|openAi|schedule|cron|webhook", x, re.I)]
    secs = json.loads(wf["nodes"][1]["parameters"]["assignments"]["assignments"][3]["value"])
    ok = (not bad and types[0].endswith("manualTrigger") and secs == ["Pass/fail for publish", "Blockers"]
          and len(wf["connections"]) == 4 and wf["active"] is False)
    print(json.dumps({"self_test": "pass" if ok else "fail", "nodes": len(types), "required_sections": secs}))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an importable n8n workflow for one BSV Library AI Team task.")
    ap.add_argument("--task", choices=sorted(TASKS["tasks"]))
    ap.add_argument("--prompt", help="system prompt file (default: prompts/<task>.txt)")
    ap.add_argument("--base-url", default="http://localhost:1234/v1", help="OpenAI-compatible base URL (Ollama: http://localhost:11434/v1)")
    ap.add_argument("--model", default="local-model")
    ap.add_argument("--out", help="output file (default: out/<task>.workflow.json)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.task:
        ap.error("--task is required")
    t = TASKS["tasks"][a.task]
    pf = pathlib.Path(a.prompt) if a.prompt else HERE / "prompts" / (a.task + ".txt")
    if not pf.exists():
        print("Missing %s.\nCopy the system prompt from %s%s (free email verification) into that file." % (pf, TASKS["origin"], t["full_text_page"]))
        return 2
    wf = build(a.task, clean_prompt(pf.read_text(encoding="utf-8")), a.base_url, a.model)
    out = pathlib.Path(a.out) if a.out else HERE / "out" / (a.task + ".workflow.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote %s (%d required sections). Import it in n8n: Workflows > Import from file." % (out, len(required_sections(wf["nodes"][1]["parameters"]["assignments"]["assignments"][1]["value"]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
