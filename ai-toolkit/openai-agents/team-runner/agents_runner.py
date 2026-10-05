#!/usr/bin/env python3
# BSV OpenAI Agents SDK team runner — ORIGINAL BSV STARTER (MIT). Not runtime tested by BSV.
# Runs one BSV Library AI Team task with the OpenAI Agents SDK on a LOCAL OpenAI-compatible model
# (LM Studio by default), checks the required sections, and writes ./out only after you type "yes".
# Tracing is disabled so nothing is uploaded. No keys in source. Nothing is published, sent or spent.
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
from typing import List

HERE = pathlib.Path(__file__).resolve().parent
TASKS = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
BASE_URL = os.environ.get("BSV_LLM_BASE_URL", "http://localhost:1234/v1")  # Ollama: http://localhost:11434/v1
MODEL = os.environ.get("BSV_LLM_MODEL", "local-model")
API_KEY = os.environ.get("BSV_LLM_API_KEY", "not-needed-for-local")
MAX_REVISIONS = 2


def clean_prompt(text: str) -> str:
    m = re.search(r'"""(.*?)"""', text, re.S)
    return (m.group(1) if m else text).strip()


def required_sections(system_prompt: str) -> List[str]:
    out, on = [], False
    for line in system_prompt.splitlines():
        if re.match(r"^\s*OUTPUT\s*:", line, re.I):
            on = True
            continue
        if on:
            m = re.match(r"^\s*\d+[.)]\s*(.+?)\s*$", line)
            if m:
                out.append(m.group(1).rstrip('"').strip())
            elif line.strip():
                break
    return out


def missing_sections(text: str, sections: List[str]) -> List[str]:
    low = text.lower()
    miss = []
    for s in sections:
        words = [w for w in re.sub(r"[^a-z0-9 ]", " ", s.lower()).split() if len(w) > 2][:3]
        if words and not all(w in low for w in words):
            miss.append(s)
    return miss


def agent_once(title: str, system: str, user_input: str) -> str:
    from openai import AsyncOpenAI  # pip install openai-agents
    from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
    set_tracing_disabled(True)
    model = OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY))
    agent = Agent(name="%s (BSV team runner)" % title, instructions=system, model=model)  # no tools on purpose
    return str(Runner.run_sync(agent, user_input).final_output or "")


def run(task: str, system: str, user_input: str, ask, agent_fn=agent_once) -> dict:
    title = TASKS["tasks"][task]["title"]
    sections = required_sections(system)
    prompt, revisions = user_input, 0
    while True:
        draft = agent_fn(title, system, prompt)
        missing = missing_sections(draft, sections)
        if missing and revisions < MAX_REVISIONS:
            revisions += 1
            prompt = user_input + "\n\n---\nPrevious answer:\n" + draft + "\n\nIt missed: " + "; ".join(missing) + ". Rewrite it with every section."
            continue
        answer = str(ask({"task": task, "draft": draft, "missing": missing})).strip()
        if answer.lower() == "yes":
            out = HERE / "out"
            out.mkdir(exist_ok=True)
            p = out / ("%s-%s.md" % (task, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
            p.write_text(draft, encoding="utf-8")
            return {"approved": True, "saved": str(p), "revisions": revisions, "missing": missing, "draft": draft}
        if answer.lower().startswith("revise:") and revisions < MAX_REVISIONS:
            revisions += 1
            prompt = user_input + "\n\n---\nPrevious answer:\n" + draft + "\n\nReviewer feedback: " + answer[7:].strip()
            continue
        return {"approved": False, "saved": None, "revisions": revisions, "missing": missing, "draft": draft}


def ask_cli(v: dict) -> str:
    print("\n===== DRAFT (%s) =====\n%s\n" % (v["task"], v["draft"]))
    if v["missing"]:
        print("Still missing sections: " + "; ".join(v["missing"]))
    return input("Approve and save? yes / no / revise: <feedback> > ")


def self_test() -> int:
    # Control-flow test with a fake agent and scripted answers: no SDK, no model, no network.
    system = "Test team.\nOUTPUT:\n1) Pass/fail for publish\n2) Blockers"
    calls = []

    def fake(title, sys_prompt, user):
        calls.append(user)
        return "Pass/fail for publish: pass" if len(calls) == 1 else "Pass/fail for publish: pass\nBlockers: none"
    answers = iter(["revise: shorter", "yes"])
    r = run("doc-review", system, "hello", lambda v: next(answers), fake)
    ok = r["approved"] and r["saved"] and len(calls) == 3 and not r["missing"]
    if r["saved"]:
        pathlib.Path(r["saved"]).unlink()
    print(json.dumps({"self_test": "pass" if ok else "fail", "agent_calls": len(calls), "revisions": r["revisions"]}))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Run one BSV Library AI Team task with the OpenAI Agents SDK and a local model.")
    ap.add_argument("--task", choices=sorted(TASKS["tasks"]))
    ap.add_argument("--input", help="file with the task input (default: stdin)")
    ap.add_argument("--prompt", help="system prompt file (default: prompts/<task>.txt)")
    ap.add_argument("--dry-run", action="store_true", help="show the plan and parsed sections; no model call")
    ap.add_argument("--self-test", action="store_true", help="control-flow test with a fake agent")
    ap.add_argument("--eval-record", metavar="PATH", help="also add this run to an eval record (BSV schema 1.0 JSON; created if missing)")
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
    system = clean_prompt(pf.read_text(encoding="utf-8"))
    if a.dry_run:
        print(json.dumps({"task": a.task, "title": t["title"], "model": MODEL, "base_url": BASE_URL, "tracing": "disabled",
                          "required_sections": required_sections(system), "flow": "agent (no tools) -> section check -> your approval -> save"}, indent=1))
        return 0
    user_input = pathlib.Path(a.input).read_text(encoding="utf-8") if a.input else sys.stdin.read()
    if a.eval_record:
        import eval_record  # same folder; standard library only
        try:
            eval_record.precheck(a.eval_record, "openai-agents", a.task, system, __file__)
        except ValueError as e:
            print("Eval record problem, nothing run: %s" % e)
            return 2
    r = run(a.task, system, user_input, ask_cli)
    print("Saved: " + r["saved"] if r["saved"] else "Not saved (not approved).")
    if a.eval_record:
        try:
            _, er = eval_record.append(a.eval_record, "openai-agents", a.task, MODEL, BASE_URL, {"tracing": "disabled"}, system, user_input, required_sections(system), r, __file__)
        except ValueError as e:
            print("Eval record not written: %s" % e)
            return 2
        print("Eval record: %s (%s %s; facts not checked)" % (a.eval_record, er["run_id"], er["result"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
