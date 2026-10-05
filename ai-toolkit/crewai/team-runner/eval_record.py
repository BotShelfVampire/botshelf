# BSV team-runner evidence record — ORIGINAL BSV STARTER (MIT). Standard library only.
# Writes one run of a team runner into an eval record in the BSV schema 1.0 format
# (docs/eval-run.schema.json; check it with: node scripts/validate-eval-run.mjs <file>).
# What it records is only what the runner can check by itself: the required-section keyword check,
# the revision count and your yes/no. It does NOT check facts, numbers, dates or quotes against the source.
# The same file is shipped in the LangGraph, CrewAI and OpenAI Agents SDK runners (kept identical).
import datetime
import hashlib
import json
import os
import pathlib

BLOCKING = ["missing_required_section", "not_approved_by_user"]
LIMITS = [
    "Deterministic checks only: required-section keywords from the prompt OUTPUT list, revision count, your yes/no.",
    "Facts, numbers, dates, quotes and citations are NOT checked. Compare the saved output with the source (Regression Checklist evidence check) and record a human review.",
    "The task input and draft text are not stored here, only their sha256.",
    "Model version or digest is not recorded by the runner.",
]


def sha(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_record(workflow):
    return {
        "schema_version": "1.0",
        "workflow": workflow,
        "acceptance": {
            "criteria_defined_before_runs": True,
            "blocking_failures": list(BLOCKING),
            "criteria": [
                {"id": "required_sections", "description": "Every section in the prompt OUTPUT list is present (keyword check).", "method": "deterministic_section_check"},
                {"id": "action_boundary", "description": "Output is saved to ./out only after the user types yes. The runner has no publish, send or spend step.", "method": "runner_control_flow"},
                {"id": "source_fidelity", "description": "Facts, numbers, dates and quotes match the supplied source.", "method": "human_review_not_done_by_runner"},
            ],
        },
        "cases": [],
        "runs": [],
        "baseline_comparison": {"baseline_description": "No baseline run recorded by this runner.", "same_inputs_and_restrictions": None,
                                "results_reference": "", "measurable_improvement": None},
        "summary": {},
    }


def summarize(rec):
    done = [r for r in rec["runs"] if r.get("result") in ("passed", "failed")]
    passed = len([r for r in done if r["result"] == "passed"])
    failed = len(done) - passed
    old = rec.get("summary") or {}
    rec["summary"] = {"total_runs": len(done), "passed_runs": passed, "failed_runs": failed,
                      "status": "design_only" if not done else ("evaluation_failed" if failed else "runs"),
                      "known_limitations": list(LIMITS), "human_reviewer": old.get("human_reviewer", ""),
                      "reviewed_at_utc": old.get("reviewed_at_utc", "")}
    return rec


def revision(system, runner_file):
    return "runner %s; prompt %s" % (sha(pathlib.Path(runner_file).read_text(encoding="utf-8"))[:19], sha(system)[:19])


def precheck(path, framework, task, system, runner_file):
    """Call BEFORE the run: returns the existing record (or None) and raises ValueError if it cannot take this run."""
    p = pathlib.Path(path)
    if not p.exists():
        return None
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        raise ValueError("%s is not valid JSON" % p)
    if not isinstance(rec, dict) or rec.get("schema_version") != "1.0" or not isinstance(rec.get("runs"), list) or not isinstance(rec.get("cases"), list):
        raise ValueError("%s is not a schema 1.0 eval record" % p)
    w = rec.get("workflow") or {}
    if (w.get("job"), w.get("runtime"), w.get("revision")) != (task, framework, revision(system, runner_file)):
        raise ValueError("%s records another task, runner or prompt revision. Use one record file per task, runner and prompt." % p)
    return rec


def append(path, framework, task, model, base_url, settings, system, user_input, sections, result, runner_file):
    """Add one case + one run to the record at path (created if missing). Returns (record, run)."""
    p = pathlib.Path(path)
    workflow = {"name": "BSV %s team runner: %s" % (framework, task), "job": task,
                "revision": revision(system, runner_file),
                "runtime": framework,
                "models": [{"provider": "openai-compatible", "name": model, "version_or_digest": "not recorded", "settings": dict(settings, base_url=base_url)}],
                "tools": [],
                "approval_boundaries": ["save to ./out only after the user types yes", "no publish, send or spend step in the runner"]}
    rec = precheck(path, framework, task, system, runner_file) or new_record(workflow)
    n = len(rec["runs"]) + 1
    while any(r.get("run_id") == "run-%03d" % n for r in rec["runs"]) or any(c.get("case_id") == "case-%03d" % n for c in rec["cases"]):
        n += 1
    missing = list(result.get("missing") or [])
    approved = result.get("approved") is True
    saved = result.get("saved") or ""
    failures = (["missing_required_section"] if missing else []) + ([] if approved else ["not_approved_by_user"])
    ref_in = sha(user_input)
    rec["cases"].append({"case_id": "case-%03d" % n, "category": "normal", "input_or_redacted_reference": ref_in,
                         "expected_facts": [], "forbidden_claims": [], "required_fields": list(sections), "expected_action_state": "draft_only"})
    run = {"run_id": "run-%03d" % n, "case_id": "case-%03d" % n,
           "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "raw_input_reference": ref_in,
           "raw_output_reference": saved if saved else "not saved (draft %s)" % sha(result.get("draft") or ""),
           "trace_reference": "none (the runner keeps no trace)",
           "exit_code": 0, "external_action_occurred": False,
           "deterministic_checks": {"required_sections": len(sections), "missing_sections": missing, "revisions": int(result.get("revisions") or 0),
                                    "approved_by_user": approved, "saved": bool(saved)},
           "grader": {"type": "deterministic_section_check", "version": "1", "rubric_reference": "prompt OUTPUT list",
                      "evidence": "missing: " + ("; ".join(missing) if missing else "none") + "; approved: " + ("yes" if approved else "no")},
           "blocking_failures_observed": failures,
           "result": "failed" if failures else "passed"}
    rec["runs"].append(run)
    summarize(rec)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(p))
    return rec, run
