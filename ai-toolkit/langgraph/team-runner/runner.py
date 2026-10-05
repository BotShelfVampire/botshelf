#!/usr/bin/env python3
# BSV LangGraph team runner — ORIGINAL BSV STARTER (MIT). Not runtime tested by BSV.
# Runs one BSV Library AI Team task as a LangGraph graph:
#   produce (local model) -> check required sections -> human approval (interrupt) -> save
# The model is any OpenAI-compatible endpoint: LM Studio (default) or Ollama. No keys in source.
# Nothing is published, sent or spent; output is written to ./out only after you type "yes".
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
from typing import List, TypedDict

HERE = pathlib.Path(__file__).resolve().parent
TASKS = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
BASE_URL = os.environ.get("BSV_LLM_BASE_URL", "http://localhost:1234/v1")  # Ollama: http://localhost:11434/v1
MODEL = os.environ.get("BSV_LLM_MODEL", "local-model")
API_KEY = os.environ.get("BSV_LLM_API_KEY", "not-needed-for-local")
MAX_REVISIONS = 2


def clean_prompt(text: str) -> str:
    # Accept either the bare prompt or the whole `SYSTEM = """..."""` line pasted from the page.
    m = re.search(r'"""(.*?)"""', text, re.S)
    return (m.group(1) if m else text).strip()


def required_sections(system_prompt: str) -> List[str]:
    # The Library team prompts end with an OUTPUT: list such as "1) Pass/fail for publish".
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


class State(TypedDict, total=False):
    task: str
    system: str
    user_input: str
    draft: str
    missing: List[str]
    revisions: int
    approved: bool
    feedback: str
    saved: str


def chat(system: str, user: str) -> str:
    from openai import OpenAI  # pip install openai
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    r = client.chat.completions.create(model=MODEL, temperature=0.2,
                                       messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return r.choices[0].message.content or ""


def build(chat_fn=chat):
    from langgraph.graph import StateGraph, START, END  # pip install langgraph
    from langgraph.types import interrupt

    def produce(state: State) -> State:
        user = state["user_input"]
        if state.get("draft") and (state.get("missing") or state.get("feedback")):
            user += "\n\n---\nPrevious answer:\n" + state["draft"]
            if state.get("missing"):
                user += "\n\nIt is missing these required sections: " + "; ".join(state["missing"]) + ". Rewrite it with every section."
            if state.get("feedback"):
                user += "\n\nReviewer feedback: " + state["feedback"]
        rev = state.get("revisions", 0) + (1 if state.get("draft") else 0)
        return {"draft": chat_fn(state["system"], user), "revisions": rev, "feedback": ""}

    def check(state: State) -> State:
        return {"missing": missing_sections(state["draft"], required_sections(state["system"]))}

    def after_check(state: State) -> str:
        return "produce" if state["missing"] and state["revisions"] < MAX_REVISIONS else "approve"

    def approve(state: State) -> State:
        answer = str(interrupt({"task": state["task"], "draft": state["draft"], "missing": state["missing"],
                                "question": "Approve and save? yes / no / revise: <feedback>"})).strip()
        if answer.lower() == "yes":
            return {"approved": True}
        if answer.lower().startswith("revise:") and state["revisions"] < MAX_REVISIONS:
            return {"approved": False, "feedback": answer[7:].strip()}
        return {"approved": False, "feedback": ""}

    def after_approve(state: State) -> str:
        if state.get("approved"):
            return "save"
        return "produce" if state.get("feedback") else END

    def save(state: State) -> State:
        out = HERE / "out"
        out.mkdir(exist_ok=True)
        p = out / ("%s-%s.md" % (state["task"], datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        p.write_text(state["draft"], encoding="utf-8")
        return {"saved": str(p)}

    g = StateGraph(State)
    g.add_node("produce", produce)
    g.add_node("check", check)
    g.add_node("approve", approve)
    g.add_node("save", save)
    g.add_edge(START, "produce")
    g.add_edge("produce", "check")
    g.add_conditional_edges("check", after_check, {"produce": "produce", "approve": "approve"})
    g.add_conditional_edges("approve", after_approve, {"save": "save", "produce": "produce", END: END})
    g.add_edge("save", END)
    return g


def checkpointer():
    try:
        from langgraph.checkpoint.memory import InMemorySaver
    except ImportError:  # older langgraph
        from langgraph.checkpoint.memory import MemorySaver as InMemorySaver
    return InMemorySaver()


def run(task: str, system: str, user_input: str, ask, chat_fn=chat) -> State:
    from langgraph.types import Command
    app = build(chat_fn).compile(checkpointer=checkpointer())
    config = {"configurable": {"thread_id": "%s-%s" % (task, datetime.datetime.now().strftime("%H%M%S%f"))}}
    app.invoke({"task": task, "system": system, "user_input": user_input, "revisions": 0}, config)
    while app.get_state(config).next:  # paused at the human approval interrupt
        values = app.get_state(config).values
        app.invoke(Command(resume=ask(values)), config)
    return app.get_state(config).values


def ask_cli(values: State) -> str:
    print("\n===== DRAFT (%s) =====\n%s\n" % (values["task"], values["draft"]))
    if values.get("missing"):
        print("Still missing sections: " + "; ".join(values["missing"]))
    return input("Approve and save? yes / no / revise: <feedback> > ")


def self_test() -> int:
    # Wiring test with a fake model and scripted answers: no model server, no network.
    system = "Test team.\nOUTPUT:\n1) Pass/fail for publish\n2) Blockers"
    calls = []

    def fake(sys_prompt, user):
        calls.append(user)
        return "Pass/fail for publish: pass" if len(calls) == 1 else "Pass/fail for publish: pass\nBlockers: none"
    answers = iter(["revise: shorter", "yes"])
    final = run("doc-review", system, "hello", lambda v: next(answers), fake)
    ok = final.get("approved") is True and final.get("saved") and len(calls) == 3 and not final.get("missing")
    if final.get("saved"):
        pathlib.Path(final["saved"]).unlink()
    print(json.dumps({"self_test": "pass" if ok else "fail", "model_calls": len(calls), "revisions": final.get("revisions")}))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Run one BSV Library AI Team task with LangGraph and a local model.")
    ap.add_argument("--task", choices=sorted(TASKS["tasks"]))
    ap.add_argument("--input", help="file with the task input (default: stdin)")
    ap.add_argument("--prompt", help="SYSTEM prompt file (default: prompts/<task>.txt)")
    ap.add_argument("--dry-run", action="store_true", help="show the plan and parsed sections; no model call")
    ap.add_argument("--self-test", action="store_true", help="graph wiring test with a fake model")
    ap.add_argument("--eval-record", metavar="PATH", help="also add this run to an eval record (BSV schema 1.0 JSON; created if missing)")
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
    sections = required_sections(system)
    if a.dry_run:
        print(json.dumps({"task": a.task, "title": t["title"], "model": MODEL, "base_url": BASE_URL, "required_sections": sections,
                          "graph": "produce -> check -> approve (interrupt) -> save"}, indent=1))
        return 0
    user_input = pathlib.Path(a.input).read_text(encoding="utf-8") if a.input else sys.stdin.read()
    if a.eval_record:
        import eval_record  # same folder; standard library only
        try:
            eval_record.precheck(a.eval_record, "langgraph", a.task, system, __file__)
        except ValueError as e:
            print("Eval record problem, nothing run: %s" % e)
            return 2
    final = run(a.task, system, user_input, ask_cli)
    print("Saved: " + final["saved"] if final.get("saved") else "Not saved (not approved).")
    if a.eval_record:
        try:
            _, er = eval_record.append(a.eval_record, "langgraph", a.task, MODEL, BASE_URL, {"temperature": 0.2}, system, user_input, sections, final, __file__)
        except ValueError as e:
            print("Eval record not written: %s" % e)
            return 2
        print("Eval record: %s (%s %s; facts not checked)" % (a.eval_record, er["run_id"], er["result"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
