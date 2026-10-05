#!/usr/bin/env python3
# BSV n8n team runner — evidence record — ORIGINAL BSV STARTER (MIT). Standard library only.
# Adds ONE n8n execution of a BSV team-runner workflow to an eval record (BSV schema 1.0;
# check it with: node scripts/validate-eval-run.mjs <file>). n8n itself writes no record, so:
#   1. n8n execute --id=<workflow id> --rawOutput > exec.json      (the n8n CLI; prints the execution JSON)
#   2. read the draft (Section check output), decide yes / no
#   3. python record_execution.py --execution exec.json --approved yes --eval-record record.json
# What it records is only what the workflow checked by itself (the required-section keyword check) and
# your yes/no. It does NOT check facts, numbers, dates or quotes. The task input and the draft are stored
# only as sha256. It calls nothing, sends nothing and changes nothing but the record file.
import argparse
import json
import pathlib
import sys

import eval_record  # same folder; the identical file ships with the LangGraph, CrewAI and OpenAI Agents SDK runners

HERE = pathlib.Path(__file__).resolve().parent
PLACEHOLDER = "PASTE THE TASK INPUT HERE"
BOUNDARIES = ["manual trigger only; the workflow saves nothing and sends nothing",
              "approved = the user's --approved yes after reading the draft in the execution view"]
ACTION = "The workflow has no write, send or spend node; approval is the user's --approved yes given to record_execution.py."


def node_json(run, name):
    try:
        return run[name][0]["data"]["main"][0][0]["json"]
    except (KeyError, IndexError, TypeError):
        return None


def read_execution(path):
    """The JSON printed by `n8n execute --rawOutput` (text before the first '{' line, if any, is skipped)."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    k = text.find("{")
    if k < 0:
        raise ValueError("no JSON in %s" % path)
    ex = json.loads(text[k:])
    rd = (ex.get("data") or {}).get("resultData") or {}
    if ex.get("status") != "success" or ex.get("finished") is not True or rd.get("error"):
        raise ValueError("the execution did not finish successfully (status %r); nothing recorded" % ex.get("status"))
    run = rd.get("runData") or {}
    inp, chk = node_json(run, "Task input"), node_json(run, "Section check")
    if not inp or not chk or "Review (nothing is saved or sent)" not in run:
        raise ValueError("not an execution of a BSV team-runner workflow (Task input / Section check / Review missing)")
    if (inp.get("user_input") or "").strip() in ("", PLACEHOLDER):
        raise ValueError("the task input is still the placeholder; nothing recorded")
    try:
        sections = json.loads(inp.get("required_sections") or "[]")
    except ValueError:
        sections = None
    if not isinstance(sections, list) or not sections or not isinstance(chk.get("missing"), list):
        raise ValueError("the Section check output or the required sections are missing; nothing recorded")
    model = node_json(run, "Local model") or {}
    return inp, chk, sections, (model.get("model") or "not recorded")


def main():
    ap = argparse.ArgumentParser(description="Add one n8n team-runner execution to a BSV eval record (schema 1.0).")
    ap.add_argument("--execution", required=True, help="file with the output of: n8n execute --id=<id> --rawOutput")
    ap.add_argument("--approved", required=True, choices=["yes", "no"], help="your decision after reading the draft")
    ap.add_argument("--eval-record", required=True, metavar="PATH", help="eval record JSON (created if missing)")
    ap.add_argument("--base-url", default="not recorded", help="the --base-url the workflow was built with (optional)")
    a = ap.parse_args()
    try:
        inp, chk, sections, model = read_execution(a.execution)
        builder = HERE / "make_workflow.py"
        eval_record.precheck(a.eval_record, "n8n", inp.get("task"), inp.get("system") or "", builder)
        result = {"missing": chk["missing"], "approved": a.approved == "yes", "saved": "", "draft": chk.get("draft") or "", "revisions": 0}
        rec, run = eval_record.append(a.eval_record, "n8n", inp.get("task"), model, a.base_url, {"temperature": 0.3},
                                      inp.get("system") or "", inp["user_input"], sections, result, builder)
    except ValueError as e:
        print("Not recorded: %s" % e)
        return 2
    rec["workflow"]["approval_boundaries"] = list(BOUNDARIES)
    for c in rec["acceptance"]["criteria"]:
        if c.get("id") == "action_boundary":
            c["description"] = ACTION
    run["trace_reference"] = "n8n execution JSON (%s); not stored in the record" % pathlib.Path(a.execution).name
    p = pathlib.Path(a.eval_record)
    p.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print("Eval record: %s (%s %s; facts not checked)" % (p, run["run_id"], run["result"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
