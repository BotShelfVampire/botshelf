#!/usr/bin/env python3
# BSV CrewAI team runner — ORIGINAL BSV STARTER (MIT). Not runtime tested by BSV.
# Runs one BSV Library AI Team task as a two-agent crew (lead + checker) on a local model,
# then a deterministic section check, then YOUR approval before anything is written to ./out.
# No keys in source. Nothing is published, sent or spent.
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
# "openai/<model id>" + base_url talks to any OpenAI-compatible server:
# LM Studio http://localhost:1234/v1 (default) or Ollama http://localhost:11434/v1
BASE_URL = os.environ.get("BSV_LLM_BASE_URL", "http://localhost:1234/v1")
MODEL = os.environ.get("BSV_LLM_MODEL", "openai/local-model")
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


def crew_once(title: str, system: str, user_input: str, extra: str = "") -> str:
    from crewai import Agent, Crew, LLM, Process, Task  # pip install crewai
    llm = LLM(model=MODEL, base_url=BASE_URL, api_key=API_KEY, temperature=0.2)
    lead = Agent(role="%s lead" % title, goal="Do exactly the job in the system prompt, then stop.",
                 backstory=system, llm=llm, allow_delegation=False, verbose=False)
    checker = Agent(role="%s checker" % title, goal="Return the lead's answer with every required section present and nothing invented.",
                    backstory="Careful reviewer. Never adds facts that are not in the input.", llm=llm, allow_delegation=False, verbose=False)
    sections = required_sections(system)
    produce = Task(description="Input:\n" + user_input + extra, agent=lead,
                   expected_output="An answer with these sections in order: " + "; ".join(sections))
    review = Task(description="Check the lead's answer. Fix missing sections using only the input. Return the final answer only.",
                  agent=checker, context=[produce], expected_output="The final answer with sections: " + "; ".join(sections))
    # No inputs= on purpose: prompt text may contain braces and must not be template-interpolated.
    result = Crew(agents=[lead, checker], tasks=[produce, review], process=Process.sequential, verbose=False).kickoff()
    return str(getattr(result, "raw", result))


def run(task: str, system: str, user_input: str, ask, crew_fn=crew_once) -> dict:
    title = TASKS["tasks"][task]["title"]
    sections = required_sections(system)
    draft, extra, revisions = "", "", 0
    while True:
        draft = crew_fn(title, system, user_input, extra)
        missing = missing_sections(draft, sections)
        if missing and revisions < MAX_REVISIONS:
            revisions += 1
            extra = "\n\nThe previous answer missed: " + "; ".join(missing) + ". Include every section.\nPrevious answer:\n" + draft
            continue
        answer = str(ask({"task": task, "draft": draft, "missing": missing})).strip()
        if answer.lower() == "yes":
            out = HERE / "out"
            out.mkdir(exist_ok=True)
            p = out / ("%s-%s.md" % (task, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
            p.write_text(draft, encoding="utf-8")
            return {"approved": True, "saved": str(p), "revisions": revisions, "missing": missing}
        if answer.lower().startswith("revise:") and revisions < MAX_REVISIONS:
            revisions += 1
            extra = "\n\nReviewer feedback: " + answer[7:].strip() + "\nPrevious answer:\n" + draft
            continue
        return {"approved": False, "saved": None, "revisions": revisions, "missing": missing}


def ask_cli(v: dict) -> str:
    print("\n===== DRAFT (%s) =====\n%s\n" % (v["task"], v["draft"]))
    if v["missing"]:
        print("Still missing sections: " + "; ".join(v["missing"]))
    return input("Approve and save? yes / no / revise: <feedback> > ")


def self_test() -> int:
    # Control-flow test with a fake crew and scripted answers: no crewai, no model, no network.
    system = 'SYSTEM = """Test team.\nOUTPUT:\n1) Pass/fail for publish\n2) Blockers"""'
    calls = []

    def fake(title, sys_prompt, user, extra):
        calls.append(extra)
        return "Pass/fail for publish: pass" if len(calls) == 1 else "Pass/fail for publish: pass\nBlockers: none"
    answers = iter(["revise: shorter", "yes"])
    r = run("doc-review", clean_prompt(system), "hello", lambda v: next(answers), fake)
    ok = r["approved"] and r["saved"] and len(calls) == 3 and not r["missing"]
    if r["saved"]:
        pathlib.Path(r["saved"]).unlink()
    print(json.dumps({"self_test": "pass" if ok else "fail", "crew_calls": len(calls), "revisions": r["revisions"]}))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Run one BSV Library AI Team task with CrewAI and a local model.")
    ap.add_argument("--task", choices=sorted(TASKS["tasks"]))
    ap.add_argument("--input", help="file with the task input (default: stdin)")
    ap.add_argument("--prompt", help="SYSTEM prompt file (default: prompts/<task>.txt)")
    ap.add_argument("--dry-run", action="store_true", help="show the plan and parsed sections; no model call")
    ap.add_argument("--self-test", action="store_true", help="control-flow test with a fake crew")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.task:
        ap.error("--task is required")
    t = TASKS["tasks"][a.task]
    pf = pathlib.Path(a.prompt) if a.prompt else HERE / "prompts" / (a.task + ".txt")
    if not pf.exists():
        print("Missing %s.\nCopy the SYSTEM block from %s%s (free email verification) into that file." % (pf, TASKS["origin"], t["full_text_page"]))
        return 2
    system = clean_prompt(pf.read_text(encoding="utf-8"))
    if a.dry_run:
        print(json.dumps({"task": a.task, "title": t["title"], "model": MODEL, "base_url": BASE_URL,
                          "required_sections": required_sections(system), "flow": "lead -> checker -> section check -> your approval -> save"}, indent=1))
        return 0
    user_input = pathlib.Path(a.input).read_text(encoding="utf-8") if a.input else sys.stdin.read()
    r = run(a.task, system, user_input, ask_cli)
    print("Saved: " + r["saved"] if r["saved"] else "Not saved (not approved).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
