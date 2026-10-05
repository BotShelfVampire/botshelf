#!/usr/bin/env python3
"""Smoke test: the LangGraph, CrewAI, OpenAI Agents SDK and n8n team runners, unchanged, on the real
libraries / the real n8n CLI against a local OpenAI-compatible STUB server (127.0.0.1, scripted replies).
No model, no paid API, no external network: HTTP(S)_PROXY points at a local recorder that answers nothing
and counts every attempt (must stay 0). Checks the wiring only: the requests the runner sends, the revision
loop, the approval gate and what is saved. It says nothing about answer quality on a real model.
usage: python smoke_team_runners.py  (langgraph + openai, crewai in the running interpreter)
  env BSV_SMOKE_AGENTS_PY = python with openai-agents (separate venv: it needs openai 3, crewai pins openai 2)
  env BSV_SMOKE_NODE + BSV_SMOKE_N8N = node binary + n8n CLI script (npm package n8n)
Also: the --eval-record option of the 3 Python runners and n8n record_execution.py (eval_record.py) write records that pass
scripts/validate-eval-run.mjs and say what happened (section check, yes/no). Facts are not checked by it."""
import http.server, importlib.metadata as md, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, threading

REPO = pathlib.Path(__file__).resolve().parents[2]
SYSTEM = "BSV smoke team. Review the input.\nOUTPUT:\n1) Pass/fail for publish\n2) Blockers"
INPUT = "Draft: release notes for version 2."
FAILS, CHECKS = [], [0]
MUTATE = []
AGENTS_PY = os.environ.get("BSV_SMOKE_AGENTS_PY", "/workspace/tools/agentsvenv/bin/python")
NODE = os.environ.get("BSV_SMOKE_NODE", "/workspace/tools/node24/bin/node")
N8N = os.environ.get("BSV_SMOKE_N8N", "/workspace/tools/n8n/node_modules/n8n/bin/n8n")


class Recorder:
    """Stands in for the proxy: accepts, records the first bytes (CONNECT host), closes. Any hit = an outside call."""
    def __init__(self):
        self.hits = []
        self.sock = socket.socket(); self.sock.bind(("127.0.0.1", 0)); self.sock.listen(16)
        self.url = "http://127.0.0.1:%d" % self.sock.getsockname()[1]
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            c, _ = self.sock.accept()
            try:
                c.settimeout(2); self.hits.append(c.recv(200).split(b"\r\n")[0].decode("latin-1"))
            except Exception:
                self.hits.append("?")
            c.close()


PROXY = Recorder()


def ok(c, msg):
    CHECKS[0] += 1
    if not c:
        FAILS.append(msg)


class Stub:
    def __init__(self, reply):
        self.reqs, self.reply = [], reply
        stub = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                stub.reqs.append({"path": self.path, "body": body})
                text = stub.reply(stub, body)
                out = json.dumps({"id": "stub-%d" % len(stub.reqs), "object": "chat.completion", "created": 0, "model": body.get("model", ""),
                                  "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                                  "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

            def do_GET(self):
                stub.reqs.append({"path": self.path, "body": None}); self.send_response(404); self.end_headers()
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = "http://127.0.0.1:%d/v1" % self.srv.server_address[1]


def msgs(b):
    return {m["role"]: (m["content"] if isinstance(m["content"], str) else json.dumps(m["content"])) for m in b.get("messages", [])}


def run_runner(sub, script, stub, answers, model, py=None, extra_env=None, record=None):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="bsv-smoke-"))
    d = tmp / "runner"; shutil.copytree(REPO / "ai-toolkit" / sub, d, ignore=shutil.ignore_patterns("out", "__pycache__"))
    for m in MUTATE:  # mutant runs only: break the copied runner, never the repo file
        fn, old, new = m if len(m) == 3 else (script,) + tuple(m)
        f = d / fn; t = f.read_text(); assert old in t, old; f.write_text(t.replace(old, new, 1))
    (tmp / "prompt.txt").write_text('SYSTEM = """%s"""' % SYSTEM); (tmp / "input.txt").write_text(INPUT)
    env = dict(os.environ, BSV_LLM_BASE_URL=stub.url, BSV_LLM_MODEL=model, BSV_LLM_API_KEY="stub", HOME=str(tmp),
               HTTPS_PROXY=PROXY.url, HTTP_PROXY=PROXY.url, NO_PROXY="127.0.0.1,localhost",
               CREWAI_DISABLE_TELEMETRY="true", CREWAI_TRACING_ENABLED="false", OTEL_SDK_DISABLED="true", **(extra_env or {}))
    p = subprocess.run([py or sys.executable, str(d / script), "--task", "doc-review", "--prompt", str(tmp / "prompt.txt"), "--input", str(tmp / "input.txt")]
                       + (["--eval-record", str(record)] if record else []),
                       input="\n".join(answers) + "\n", capture_output=True, text=True, env=env, timeout=300, cwd=tmp)
    saved = sorted((d / "out").glob("*.md")) if (d / "out").exists() else []
    extra = sorted(str(q.relative_to(d)) for q in d.rglob("*") if q.is_file() and "__pycache__" not in q.parts and q.parent.name != "out"
                   and not (REPO / "ai-toolkit" / sub / q.relative_to(d)).exists())
    res = {"rc": p.returncode, "stdout": p.stdout[-1500:], "stderr": p.stderr[-1500:], "saved": [s.read_text() for s in saved], "extra_files": extra}
    shutil.rmtree(tmp, ignore_errors=True)
    return res


PART = "Pass/fail for publish: pass"
FULL = "Pass/fail for publish: pass\nBlockers: none"


def langgraph():
    def reply(st, b):
        n = len([r for r in st.reqs if r["body"]])
        return PART if n == 1 else FULL + ("" if n == 2 else "\nShorter.")
    st = Stub(reply)
    r = run_runner("langgraph/team-runner", "runner.py", st, ["revise: shorter", "yes"], "local-model")
    cc = [x for x in st.reqs if x["path"].endswith("/chat/completions")]
    ok(r["rc"] == 0 and "Saved:" in r["stdout"], "langgraph: run ends saved (rc %s) %s" % (r["rc"], r["stderr"][-300:]))
    ok(len(cc) == 3 and len(cc) == len(st.reqs), "langgraph: 3 chat requests (draft, missing-section rewrite, reviewer revise), nothing else; got %d / %d" % (len(cc), len(st.reqs)))
    ok(all(msgs(x["body"]).get("system") == SYSTEM and INPUT in msgs(x["body"]).get("user", "") and x["body"].get("model") == "local-model" for x in cc), "langgraph: each request = pasted SYSTEM prompt + task input, model from env")
    ok(len(cc) > 1 and "missing these required sections: Blockers" in msgs(cc[1]["body"]).get("user", ""), "langgraph: missing section sent back for a rewrite")
    ok(len(cc) > 2 and "Reviewer feedback: shorter" in msgs(cc[2]["body"]).get("user", ""), "langgraph: reviewer feedback sent back")
    ok(r["saved"] == [FULL + "\nShorter."], "langgraph: saved file = the approved draft, exactly")
    st2 = Stub(lambda s, b: FULL); r2 = run_runner("langgraph/team-runner", "runner.py", st2, ["no"], "local-model")
    ok(r2["rc"] == 0 and r2["saved"] == [] and "Not saved" in r2["stdout"] and len(st2.reqs) == 1, "langgraph: answer no = nothing saved, 1 request")
    return {"requests": len(cc), "rc": r["rc"]}


def crewai():
    def reply(st, b):
        m = msgs(b); chk = "checker" in m.get("system", "")
        nchk = len([r for r in st.reqs if r["body"] and "checker" in msgs(r["body"]).get("system", "")])
        body = (PART if nchk == 1 else FULL) if chk else "Lead draft. " + PART
        fa = "Final Answer" in json.dumps(b)
        return ("Thought: I now can give a great answer\nFinal Answer: " + body) if fa else body
    st = Stub(reply)
    r = run_runner("crewai/team-runner", "crew_runner.py", st, ["yes"], "openai/local-model")
    cc = [x for x in st.reqs if x["path"].endswith("/chat/completions")]
    lead = [x for x in cc if "checker" not in msgs(x["body"]).get("system", "")]; chk = [x for x in cc if x not in lead]
    ok(r["rc"] == 0 and "Saved:" in r["stdout"], "crewai: run ends saved (rc %s) %s" % (r["rc"], (r["stderr"] or r["stdout"])[-400:]))
    ok(len(lead) == 2 and len(chk) == 2 and len(cc) == len(st.reqs), "crewai: 2 rounds x (lead, checker) because round 1 missed a section, nothing else; got lead %d checker %d other %d" % (len(lead), len(chk), len(st.reqs) - len(cc)))
    ok(all(SYSTEM.splitlines()[0] in msgs(x["body"]).get("system", "") for x in lead) and all(INPUT in msgs(x["body"]).get("user", "") for x in lead), "crewai: lead gets the pasted SYSTEM prompt (backstory) and the task input")
    ok(len(lead) > 1 and "previous answer missed: Blockers" in msgs(lead[1]["body"]).get("user", ""), "crewai: missing section sent back in round 2")
    ok(len(chk) > 0 and "Lead draft." in msgs(chk[0]["body"]).get("user", ""), "crewai: checker receives the lead answer as context")
    ok(all(x["body"].get("model") == "local-model" for x in cc), "crewai: model id sent without the openai/ prefix")
    ok(r["saved"] == [FULL], "crewai: saved file = the checker final answer, exactly; got %r" % r["saved"])
    st2 = Stub(lambda s, b: ("Thought: done\nFinal Answer: " + FULL) if "Final Answer" in json.dumps(b) else FULL)
    r2 = run_runner("crewai/team-runner", "crew_runner.py", st2, ["no"], "openai/local-model")
    ok(r2["rc"] == 0 and r2["saved"] == [] and "Not saved" in r2["stdout"] and len(st2.reqs) == 2, "crewai: answer no = nothing saved, 1 round (2 requests)")
    return {"requests": len(cc), "rc": r["rc"]}


def openai_agents():
    def reply(st, b):
        n = len([r for r in st.reqs if r["body"]])
        return PART if n == 1 else FULL + ("" if n == 2 else "\nShorter.")
    # OPENAI_API_KEY is set (a dummy) on purpose: with tracing left on, the SDK would then try to upload
    # traces to api.openai.com, which the proxy recorder would see. The runner turns tracing off.
    env = {"OPENAI_API_KEY": "sk-bsv-smoke-dummy"}
    st = Stub(reply); h0 = len(PROXY.hits)
    r = run_runner("openai-agents/team-runner", "agents_runner.py", st, ["revise: shorter", "yes"], "local-model", AGENTS_PY, env)
    cc = [x for x in st.reqs if x["path"].endswith("/chat/completions")]
    ok(r["rc"] == 0 and "Saved:" in r["stdout"], "openai-agents: run ends saved (rc %s) %s" % (r["rc"], r["stderr"][-300:]))
    ok(len(cc) == 3 and len(cc) == len(st.reqs), "openai-agents: 3 chat requests (draft, missing-section rewrite, reviewer revise), nothing else; got %d / %d" % (len(cc), len(st.reqs)))
    ok(all(msgs(x["body"]).get("system") == SYSTEM and INPUT in msgs(x["body"]).get("user", "") and x["body"].get("model") == "local-model" for x in cc), "openai-agents: each request = pasted SYSTEM prompt (instructions) + task input, model from env")
    ok(all(not x["body"].get("tools") for x in cc), "openai-agents: no tools offered to the model")
    ok(len(cc) > 1 and "It missed: Blockers" in msgs(cc[1]["body"]).get("user", ""), "openai-agents: missing section sent back for a rewrite")
    ok(len(cc) > 2 and "Reviewer feedback: shorter" in msgs(cc[2]["body"]).get("user", ""), "openai-agents: reviewer feedback sent back")
    ok(r["saved"] == [FULL + "\nShorter."], "openai-agents: saved file = the approved draft, exactly")
    st2 = Stub(lambda s, b: FULL); r2 = run_runner("openai-agents/team-runner", "agents_runner.py", st2, ["no"], "local-model", AGENTS_PY, env)
    ok(r2["rc"] == 0 and r2["saved"] == [] and "Not saved" in r2["stdout"] and len(st2.reqs) == 1, "openai-agents: answer no = nothing saved, 1 request")
    ok(len(PROXY.hits) == h0, "openai-agents: no outside call (tracing upload) through the proxy; got %r" % PROXY.hits[h0:])
    v = subprocess.run([AGENTS_PY, "-c", "import importlib.metadata as m;print(m.version('openai-agents'), m.version('openai'))"], capture_output=True, text=True).stdout.split()
    return {"requests": len(cc), "rc": r["rc"], "openai_agents": v[0] if v else None, "openai": v[1] if len(v) > 1 else None}


def n8n_once(reply):
    """make_workflow.py (unchanged, from a copy) builds the workflow; the user step (paste the task input into
    Task input -> user_input) is done on the JSON; then the real n8n CLI imports and executes it."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="bsv-smoke-n8n-"))
    d = tmp / "runner"; shutil.copytree(REPO / "ai-toolkit" / "n8n" / "team-runner", d, ignore=shutil.ignore_patterns("out", "__pycache__"))
    for m in MUTATE:
        if len(m) == 3:
            continue  # record_execution.py / eval_record.py mutants: applied in n8n_evidence
        old, new = m; f = d / "make_workflow.py"; t = f.read_text(); assert old in t, old; f.write_text(t.replace(old, new, 1))
    st = Stub(lambda s, b: reply)
    (tmp / "prompt.txt").write_text(SYSTEM)
    env = dict(os.environ, HOME=str(tmp), N8N_USER_FOLDER=str(tmp / "n8n"), N8N_DIAGNOSTICS_ENABLED="false", N8N_VERSION_NOTIFICATIONS_ENABLED="false",
               N8N_TEMPLATES_ENABLED="false", HTTPS_PROXY=PROXY.url, HTTP_PROXY=PROXY.url, NO_PROXY="127.0.0.1,localhost",
               PATH=str(pathlib.Path(NODE).parent) + os.pathsep + os.environ.get("PATH", ""))
    res = {"stub": st}
    b = subprocess.run([sys.executable, str(d / "make_workflow.py"), "--task", "doc-review", "--prompt", str(tmp / "prompt.txt"), "--base-url", st.url,
                        "--model", "local-model", "--out", str(tmp / "wf.json")], capture_output=True, text=True, env=env, timeout=60, cwd=tmp)
    res["build"] = b.returncode == 0 and "(2 required sections)" in b.stdout
    try:
        wf = json.loads((tmp / "wf.json").read_text())
        asg = wf["nodes"][1]["parameters"]["assignments"]["assignments"]
        [x for x in asg if x["name"] == "user_input"][0]["value"] = INPUT
        (tmp / "wf.json").write_text(json.dumps(wf))
        res["types"] = [n["type"] for n in wf["nodes"]]
        i = subprocess.run([NODE, N8N, "import:workflow", "--input=" + str(tmp / "wf.json")], capture_output=True, text=True, env=env, timeout=240, cwd=tmp)
        res["import"] = i.returncode == 0 and "Successfully imported 1 workflow" in (i.stdout + i.stderr)
        e = subprocess.run([NODE, N8N, "execute", "--id=" + wf["id"], "--rawOutput"], capture_output=True, text=True, env=env, timeout=240, cwd=tmp)
        k = e.stdout.find("{\n"); out = json.loads(e.stdout[k:]) if k >= 0 else {}; res["raw"] = e.stdout
        run = out.get("data", {}).get("resultData", {}).get("runData", {})
        res["status"] = (out.get("status"), out.get("finished"), out.get("data", {}).get("resultData", {}).get("lastNodeExecuted"))
        res["check"] = run.get("Section check", [{}])[0].get("data", {}).get("main", [[{}]])[0][0].get("json", {})
        res["files"] = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file() and not (REPO / "ai-toolkit" / "n8n" / "team-runner" / p.relative_to(d)).exists())
        res["err"] = (e.stderr or i.stderr)[-300:]
    except Exception as x:
        res["err"] = repr(x)
    shutil.rmtree(tmp, ignore_errors=True)
    return res


def n8n():
    h0 = len(PROXY.hits)
    r = n8n_once(PART)
    cc = [x for x in r["stub"].reqs if x["path"].endswith("/chat/completions")]
    ok(r.get("build") and r.get("import"), "n8n: make_workflow.py builds (2 sections) and the n8n CLI imports it; %s" % r.get("err", ""))
    ok(r.get("types", [""])[0].endswith("manualTrigger") and not any(t.split(".")[-1] in ("emailSend", "gmail", "slack", "executeCommand", "readWriteFile", "webhook", "scheduleTrigger") for t in r.get("types", [])),
       "n8n: manual trigger, no write / send / shell / schedule node")
    ok(r.get("status") == ("success", True, "Review (nothing is saved or sent)"), "n8n: execution success through to the Review node; got %r %s" % (r.get("status"), r.get("err", "")))
    ok(len(cc) == 1 and len(cc) == len(r["stub"].reqs), "n8n: exactly 1 chat request; got %d / %d" % (len(cc), len(r["stub"].reqs)))
    ok(len(cc) == 1 and msgs(cc[0]["body"]) == {"system": SYSTEM, "user": INPUT} and cc[0]["body"].get("model") == "local-model", "n8n: request = pasted SYSTEM prompt + task input, model from --model")
    ok(r.get("check", {}).get("missing") == ["Blockers"] and r["check"].get("all_sections_present") is False and r["check"].get("draft") == PART, "n8n: Section check flags the missing section; got %r" % r.get("check"))
    ok(r.get("files") == [], "n8n: the run writes nothing into the runner folder; got %r" % r.get("files"))
    r2 = n8n_once(FULL)
    ok(r2.get("check", {}).get("missing") == [] and r2["check"].get("all_sections_present") is True and r2["check"].get("draft") == FULL
       and "Nothing was saved or sent" in r2["check"].get("next_step", ""), "n8n: complete answer = no missing section, review step; got %r" % r2.get("check"))
    ok(len(PROXY.hits) == h0, "n8n: no outside call through the proxy; got %r" % PROXY.hits[h0:])
    N8N_RAW.update(part=r.get("raw", ""), full=r2.get("raw", ""))
    v = subprocess.run([NODE, N8N, "--version"], capture_output=True, text=True, timeout=120).stdout.strip().splitlines()
    return {"requests": len(cc), "n8n": v[-1] if v else None}


N8N_RAW = {}


def n8n_evidence():
    """record_execution.py (n8n has no --eval-record): the JSON printed by the real `n8n execute --rawOutput` runs above
    (PART and FULL replies) -> eval record; validated like the Python runners' records; refusals leave the record untouched."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="bsv-smoke-n8nrec-")); d = tmp / "runner"
    shutil.copytree(REPO / "ai-toolkit" / "n8n" / "team-runner", d, ignore=shutil.ignore_patterns("out", "__pycache__"))
    for m in MUTATE:
        if len(m) == 3:
            fn, old, new = m; f = d / fn; t = f.read_text(); assert old in t, old; f.write_text(t.replace(old, new, 1))
    before = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file())
    (tmp / "part.json").write_text(N8N_RAW.get("part", "")); (tmp / "full.json").write_text(N8N_RAW.get("full", ""))
    rec_p = tmp / "record.json"; h0 = len(PROXY.hits)
    rr = lambda ex, ap, rp=rec_p: subprocess.run([sys.executable, str(d / "record_execution.py"), "--execution", str(ex), "--approved", ap, "--eval-record", str(rp)],
                                                 capture_output=True, text=True, timeout=60, cwd=tmp, env=dict(os.environ, HTTPS_PROXY=PROXY.url, HTTP_PROXY=PROXY.url))
    try:
        r1, r2, r3 = rr(tmp / "full.json", "yes"), rr(tmp / "part.json", "yes"), rr(tmp / "full.json", "no")
        ok([x.returncode for x in (r1, r2, r3)] == [0, 0, 0] and "run-001 passed" in r1.stdout and "run-002 failed" in r2.stdout and "run-003 failed" in r3.stdout,
           "n8n evidence: 3 executions recorded with run id + result; got %r" % [(x.returncode, x.stdout[-120:], x.stderr[-200:]) for x in (r1, r2, r3)])
        rec = json.loads(rec_p.read_text()) if rec_p.exists() else {}
        v = subprocess.run([NODE, str(REPO / "scripts" / "validate-eval-run.mjs"), str(rec_p)], capture_output=True, text=True, timeout=60)
        ok(v.returncode == 0 and v.stdout.startswith("PASS"), "n8n evidence: record passes scripts/validate-eval-run.mjs; got %s" % (v.stdout + v.stderr)[-300:])
        ok(schema_keys(rec) == [], "n8n evidence: record has every key the schema requires, nothing extra; got %r" % schema_keys(rec))
        runs = rec.get("runs", []); ch = [x.get("deterministic_checks", {}) for x in runs]
        ok([x.get("result") for x in runs] == ["passed", "failed", "failed"]
           and [x.get("blocking_failures_observed") for x in runs] == [[], ["missing_required_section"], ["not_approved_by_user"]]
           and [c.get("missing_sections") for c in ch] == [[], ["Blockers"], []] and [c.get("approved_by_user") for c in ch] == [True, True, False]
           and all(c.get("saved") is False and c.get("revisions") == 0 for c in ch),
           "n8n evidence: passed only when complete AND --approved yes; got %r" % [(x.get("result"), x.get("blocking_failures_observed")) for x in runs])
        w, txt = rec.get("workflow", {}), rec_p.read_text() if rec_p.exists() else ""
        ok(w.get("runtime") == "n8n" and w.get("job") == "doc-review" and w.get("tools") == [] and any("saves nothing" in b for b in w.get("approval_boundaries", []))
           and not any("./out" in b for b in w.get("approval_boundaries", [])) and "./out" not in json.dumps(rec.get("acceptance"))
           and rec.get("summary", {}).get("status") == "evaluation_failed" and (rec["summary"]["total_runs"], rec["summary"]["passed_runs"]) == (3, 1)
           and rec["summary"]["human_reviewer"] == "" and all(x.get("external_action_occurred") is False for x in runs)
           and INPUT not in txt and FULL not in txt and SYSTEM not in txt,
           "n8n evidence: n8n boundaries (no ./out claim), summary 3/1/2, input / draft / prompt only as sha256; got %r" % w.get("approval_boundaries"))
        snap = rec_p.read_text() if rec_p.exists() else ""
        ex = json.loads(N8N_RAW.get("full", "{")[N8N_RAW.get("full", "{").find("{\n"):] or "{}")
        bad1 = json.loads(json.dumps(ex)); bad1["data"]["resultData"]["runData"]["Task input"][0]["data"]["main"][0][0]["json"]["user_input"] = "PASTE THE TASK INPUT HERE"
        bad2 = json.loads(json.dumps(ex)); bad2["status"] = "error"; bad2["finished"] = False
        (tmp / "b1.json").write_text(json.dumps(bad1)); (tmp / "b2.json").write_text(json.dumps(bad2))
        q1, q2 = rr(tmp / "b1.json", "yes"), rr(tmp / "b2.json", "yes")
        other = json.loads(snap or "{}"); other.setdefault("workflow", {})["runtime"] = "langgraph"; (tmp / "other.json").write_text(json.dumps(other)); q3 = rr(tmp / "full.json", "yes", tmp / "other.json")
        ok([q1.returncode, q2.returncode, q3.returncode] == [2, 2, 2] and all("Not recorded" in q.stdout for q in (q1, q2, q3)) and rec_p.read_text() == snap
           and json.loads((tmp / "other.json").read_text()) == other,
           "n8n evidence: placeholder input / failed execution / another runner's record = refused, records untouched; got %r" % [(q.returncode, q.stdout[-100:]) for q in (q1, q2, q3)])
        after = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file() and "__pycache__" not in str(p))
        ok(after == [x for x in before if "__pycache__" not in x], "n8n evidence: nothing written into the runner folder; got %r" % sorted(set(after) - set(before)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok(len(PROXY.hits) == h0, "n8n evidence: no outside call through the proxy; got %r" % PROXY.hits[h0:])
    return {"runs_recorded": len(runs) if rec else 0, "validator": "PASS" if v.returncode == 0 else "FAIL"}


RUNNERS = {"langgraph": ("langgraph/team-runner", "runner.py", "local-model", None, None),
           "crewai": ("crewai/team-runner", "crew_runner.py", "openai/local-model", None, None),
           "openai-agents": ("openai-agents/team-runner", "agents_runner.py", "local-model", AGENTS_PY, {"OPENAI_API_KEY": "sk-bsv-smoke-dummy"})}
SCHEMA = json.loads((REPO / "docs" / "eval-run.schema.json").read_text())


def fixed(text, crew):
    return (lambda s, b: ("Thought: done\nFinal Answer: " + text) if "Final Answer" in json.dumps(b) else text) if crew else (lambda s, b: text)


def schema_keys(rec):
    """Required keys of docs/eval-run.schema.json, at every level the schema names (the .mjs validator checks the rest)."""
    miss = [k for k in SCHEMA["required"] if k not in rec]
    for k in ("workflow", "acceptance", "baseline_comparison", "summary"):
        miss += ["%s.%s" % (k, x) for x in SCHEMA["properties"][k]["required"] if x not in (rec.get(k) or {})]
    for k in ("cases", "runs"):
        for i, item in enumerate(rec.get(k) or []):
            miss += ["%s[%d].%s" % (k, i, x) for x in SCHEMA["properties"][k]["items"]["required"] if x not in item]
    for i, m in enumerate((rec.get("workflow") or {}).get("models") or []):
        miss += ["models[%d].%s" % (i, x) for x in SCHEMA["properties"]["workflow"]["properties"]["models"]["items"]["required"] if x not in m]
    extra = [k for k in rec if k not in SCHEMA["properties"]]
    return miss + ["extra:" + k for k in extra]


def evidence_one(name):
    sub, script, model, py, env = RUNNERS[name]
    crew = name == "crewai"
    rd = pathlib.Path(tempfile.mkdtemp(prefix="bsv-smoke-rec-")); rec_p = rd / "record.json"
    h0 = len(PROXY.hits)
    try:
        r0 = run_runner(sub, script, Stub(fixed(FULL, crew)), ["no"], model, py, env)
        ok(r0["extra_files"] == [] and not rec_p.exists(), "%s: without --eval-record nothing extra is written; got %r" % (name, r0["extra_files"]))
        r1 = run_runner(sub, script, Stub(fixed(FULL, crew)), ["yes"], model, py, env, rec_p)
        r2 = run_runner(sub, script, Stub(fixed(PART, crew)), ["yes"], model, py, env, rec_p)
        r3 = run_runner(sub, script, Stub(fixed(FULL, crew)), ["no"], model, py, env, rec_p)
        ok(all(x["rc"] == 0 for x in (r1, r2, r3)) and "Eval record: " in r1["stdout"] and "run-001 passed" in r1["stdout"]
           and "run-002 failed" in r2["stdout"] and "run-003 failed" in r3["stdout"], "%s: 3 runs with --eval-record report run id + result; got %r" % (name, [(x["rc"], x["stdout"][-160:], x["stderr"][-200:]) for x in (r1, r2, r3)]))
        ok(r1["saved"] == [FULL] and r2["saved"] == [PART] and r3["saved"] == [], "%s: --eval-record does not change what is saved" % name)
        rec = json.loads(rec_p.read_text()) if rec_p.exists() else {}
        v = subprocess.run([NODE, str(REPO / "scripts" / "validate-eval-run.mjs"), str(rec_p)], capture_output=True, text=True, timeout=60)
        ok(v.returncode == 0 and v.stdout.startswith("PASS"), "%s: record passes scripts/validate-eval-run.mjs; got %s" % (name, (v.stdout + v.stderr)[-300:]))
        ok(schema_keys(rec) == [], "%s: record has every key the schema requires, nothing extra; missing %r" % (name, schema_keys(rec)))
        runs = rec.get("runs", []); ch = [x.get("deterministic_checks", {}) for x in runs]
        ok([x.get("result") for x in runs] == ["passed", "failed", "failed"]
           and [x.get("blocking_failures_observed") for x in runs] == [[], ["missing_required_section"], ["not_approved_by_user"]],
           "%s: passed only when complete AND approved; missing section / no = failed; got %r" % (name, [(x.get("result"), x.get("blocking_failures_observed")) for x in runs]))
        ok([c.get("missing_sections") for c in ch] == [[], ["Blockers"], []] and [c.get("approved_by_user") for c in ch] == [True, True, False]
           and [c.get("revisions") for c in ch] == [0, 2, 0] and [c.get("required_sections") for c in ch] == [2, 2, 2],
           "%s: deterministic_checks = what the runner saw; got %r" % (name, ch))
        ok(rec.get("summary", {}).get("status") == "evaluation_failed" and (rec["summary"]["total_runs"], rec["summary"]["passed_runs"], rec["summary"]["failed_runs"]) == (3, 1, 2)
           and rec["summary"]["human_reviewer"] == "" and any("NOT checked" in k for k in rec["summary"]["known_limitations"]),
           "%s: summary 3/1/2 evaluation_failed, no reviewer claimed, facts-not-checked limitation; got %r" % (name, rec.get("summary")))
        w = rec.get("workflow", {})
        ok(w.get("runtime") == name and w.get("job") == "doc-review" and w.get("tools") == [] and w.get("models", [{}])[0].get("name") == model
           and all(x.get("external_action_occurred") is False and x.get("exit_code") == 0 for x in runs)
           and all(c.get("required_fields") == ["Pass/fail for publish", "Blockers"] and c.get("input_or_redacted_reference") == "sha256:" + __import__("hashlib").sha256(INPUT.encode()).hexdigest() for c in rec.get("cases", []))
           and runs[0]["raw_output_reference"].endswith(".md") and runs[2]["raw_output_reference"].startswith("not saved")
           and INPUT not in rec_p.read_text() and FULL not in rec_p.read_text(),
           "%s: workflow / cases / refs recorded, input and draft only as sha256" % name)
        # a record for another runner must be refused BEFORE any model call
        other = json.loads(rec_p.read_text()); other["workflow"]["runtime"] = "other"; rec_p.write_text(json.dumps(other))
        st4 = Stub(fixed(FULL, crew)); r4 = run_runner(sub, script, st4, ["yes"], model, py, env, rec_p)
        ok(r4["rc"] == 2 and len(st4.reqs) == 0 and r4["saved"] == [] and "nothing run" in r4["stdout"] and json.loads(rec_p.read_text()) == other,
           "%s: record of another runner/prompt = refused before the run, record untouched; got rc %s reqs %d" % (name, r4["rc"], len(st4.reqs)))
    finally:
        shutil.rmtree(rd, ignore_errors=True)
    ok(len(PROXY.hits) == h0, "%s evidence: no outside call through the proxy; got %r" % (name, PROXY.hits[h0:]))
    return {"runs_recorded": len(runs) if rec else 0, "validator": "PASS" if v.returncode == 0 else "FAIL"}


def evidence():
    copies = {n: (REPO / "ai-toolkit" / RUNNERS[n][0] / "eval_record.py").read_bytes() for n in RUNNERS}
    copies["n8n"] = (REPO / "ai-toolkit" / "n8n" / "team-runner" / "eval_record.py").read_bytes()
    ok(len(set(copies.values())) == 1, "eval_record.py: the 4 runner copies (LangGraph, CrewAI, OpenAI Agents SDK, n8n) are byte-identical")
    ok(all(not __import__("re").search(rb"^\s*(import|from)\s+(?!(datetime|hashlib|json|os|pathlib)\b)", c, __import__("re").M) for c in copies.values()), "eval_record.py: standard library only")
    out = {n: evidence_one(n) for n in RUNNERS}; out["n8n"] = n8n_evidence(); return out


MUTANTS = [("langgraph", langgraph, "runner.py", [('user += "\\n\\nReviewer feedback: " + state["feedback"]', 'pass')]),
           ("langgraph", langgraph, "runner.py", [('return "produce" if state["missing"] and', 'return "produce" if False and')]),
           ("crewai", crewai, "crew_runner.py", [('if answer.lower() == "yes":', 'if answer:')]),
           ("crewai", crewai, "crew_runner.py", [("if missing and revisions < MAX_REVISIONS:", "if False:")]),
           ("openai-agents", openai_agents, "agents_runner.py", [('if answer.lower() == "yes":', 'if answer:')]),
           ("openai-agents", openai_agents, "agents_runner.py", [('"\\n\\nIt missed: "', '"\\n\\n"')]),
           ("openai-agents", openai_agents, "agents_runner.py", [("set_tracing_disabled(True)", "set_tracing_disabled(False)")]),
           ("n8n", n8n, "make_workflow.py", [("return words.length && !words.every(", "return words.length && words.every(")]),
           ("n8n", n8n, "make_workflow.py", [("{ role: 'user', content: $json.user_input }", "{ role: 'user', content: $json.task }")]),
           ("evidence", lambda: evidence_one("langgraph"), "eval_record.py", [("eval_record.py", '(["missing_required_section"] if missing else [])', "([])")]),
           ("evidence", lambda: evidence_one("langgraph"), "eval_record.py", [("eval_record.py", '([] if approved else ["not_approved_by_user"])', "([])")]),
           ("evidence", lambda: evidence_one("langgraph"), "eval_record.py", [("eval_record.py", '("evaluation_failed" if failed else "runs")', '"runs"')]),
           ("evidence", lambda: evidence_one("langgraph"), "eval_record.py", [("eval_record.py", '"total_runs": len(done)', '"total_runs": len(rec["runs"]) + 1')]),
           ("evidence", lambda: evidence_one("langgraph"), "eval_record.py", [("eval_record.py", "    if (w.get(\"job\"), w.get(\"runtime\"), w.get(\"revision\")) != ", "    if (w.get(\"job\"), w.get(\"runtime\"), w.get(\"revision\")) == ")]),
           ("evidence", lambda: evidence_one("crewai"), "crew_runner.py", [('"missing": missing, "draft": draft}', '"missing": [], "draft": draft}')]),
           ("n8n-evidence", n8n_evidence, "record_execution.py", [("record_execution.py", '"approved": a.approved == "yes"', '"approved": True')]),
           ("n8n-evidence", n8n_evidence, "record_execution.py", [("record_execution.py", 'result = {"missing": chk["missing"]', 'result = {"missing": []')]),
           ("n8n-evidence", n8n_evidence, "record_execution.py", [("record_execution.py", 'in ("", PLACEHOLDER)', 'in ("",)')]),
           ("n8n-evidence", n8n_evidence, "record_execution.py", [("record_execution.py", 'if ex.get("status") != "success" or ex.get("finished") is not True or', 'if')]),
           ("n8n-evidence", n8n_evidence, "record_execution.py", [("record_execution.py", '    rec["workflow"]["approval_boundaries"] = list(BOUNDARIES)', '    pass')]),
           ("evidence", lambda: evidence_one("openai-agents"), "agents_runner.py", [('            eval_record.precheck(a.eval_record, "openai-agents", a.task, system, __file__)', "            pass")])]


def mutants():
    caught = 0
    for name, fn, script, mut in MUTANTS:
        global FAILS
        keep, FAILS, n0 = FAILS, [], CHECKS[0]
        MUTATE[:] = mut
        try:
            fn()
        except Exception:
            FAILS.append("crash")
        caught += bool(FAILS)
        ok_ = bool(FAILS); FAILS = keep; MUTATE[:] = []; CHECKS[0] = n0
        ok(ok_, "%s mutant not caught: %s" % (name, mut[0][0][:60]))
    return caught


if __name__ == "__main__":
    out = {"test": "team-runner smoke (local stub server)", "langgraph": langgraph(), "crewai": crewai(), "openai_agents": openai_agents(), "n8n": n8n(), "evidence": evidence()}
    ok(len(PROXY.hits) == 0, "no outside call through the proxy in any run; got %r" % PROXY.hits)
    out["proxy_hits"] = len(PROXY.hits); out["mutants"] = len(MUTANTS); out["mutants_caught"] = mutants()
    out.update({"checks": CHECKS[0], "failures": len(FAILS), "fail": FAILS,
                "versions": {k: md.version(k) for k in ("langgraph", "openai", "crewai")},
                "note": "real libraries, scripted local stub replies; wiring only, not a real model run (UNTESTED_RUNTIME stays)"})
    print(json.dumps(out, indent=1))
    sys.exit(1 if FAILS else 0)
