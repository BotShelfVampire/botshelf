#!/usr/bin/env python3
"""Smoke test: the LangGraph, CrewAI, OpenAI Agents SDK and n8n team runners, unchanged, on the real
libraries / the real n8n CLI against a local OpenAI-compatible STUB server (127.0.0.1, scripted replies).
No model, no paid API, no external network: HTTP(S)_PROXY points at a local recorder that answers nothing
and counts every attempt (must stay 0). Checks the wiring only: the requests the runner sends, the revision
loop, the approval gate and what is saved. It says nothing about answer quality on a real model.
usage: python smoke_team_runners.py  (langgraph + openai, crewai in the running interpreter)
  env BSV_SMOKE_AGENTS_PY = python with openai-agents (separate venv: it needs openai 3, crewai pins openai 2)
  env BSV_SMOKE_NODE + BSV_SMOKE_N8N = node binary + n8n CLI script (npm package n8n)"""
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


def run_runner(sub, script, stub, answers, model, py=None, extra_env=None):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="bsv-smoke-"))
    d = tmp / "runner"; shutil.copytree(REPO / "ai-toolkit" / sub, d, ignore=shutil.ignore_patterns("out", "__pycache__"))
    for old, new in MUTATE:  # mutant runs only: break the copied runner, never the repo file
        f = d / script; t = f.read_text(); assert old in t, old; f.write_text(t.replace(old, new, 1))
    (tmp / "prompt.txt").write_text('SYSTEM = """%s"""' % SYSTEM); (tmp / "input.txt").write_text(INPUT)
    env = dict(os.environ, BSV_LLM_BASE_URL=stub.url, BSV_LLM_MODEL=model, BSV_LLM_API_KEY="stub", HOME=str(tmp),
               HTTPS_PROXY=PROXY.url, HTTP_PROXY=PROXY.url, NO_PROXY="127.0.0.1,localhost",
               CREWAI_DISABLE_TELEMETRY="true", CREWAI_TRACING_ENABLED="false", OTEL_SDK_DISABLED="true", **(extra_env or {}))
    p = subprocess.run([py or sys.executable, str(d / script), "--task", "doc-review", "--prompt", str(tmp / "prompt.txt"), "--input", str(tmp / "input.txt")],
                       input="\n".join(answers) + "\n", capture_output=True, text=True, env=env, timeout=300, cwd=tmp)
    saved = sorted((d / "out").glob("*.md")) if (d / "out").exists() else []
    res = {"rc": p.returncode, "stdout": p.stdout[-1500:], "stderr": p.stderr[-1500:], "saved": [s.read_text() for s in saved]}
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
    for old, new in MUTATE:
        f = d / "make_workflow.py"; t = f.read_text(); assert old in t, old; f.write_text(t.replace(old, new, 1))
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
        k = e.stdout.find("{\n"); out = json.loads(e.stdout[k:]) if k >= 0 else {}
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
    v = subprocess.run([NODE, N8N, "--version"], capture_output=True, text=True, timeout=120).stdout.strip().splitlines()
    return {"requests": len(cc), "n8n": v[-1] if v else None}


MUTANTS = [("langgraph", langgraph, "runner.py", [('user += "\\n\\nReviewer feedback: " + state["feedback"]', 'pass')]),
           ("langgraph", langgraph, "runner.py", [('return "produce" if state["missing"] and', 'return "produce" if False and')]),
           ("crewai", crewai, "crew_runner.py", [('if answer.lower() == "yes":', 'if answer:')]),
           ("crewai", crewai, "crew_runner.py", [("if missing and revisions < MAX_REVISIONS:", "if False:")]),
           ("openai-agents", openai_agents, "agents_runner.py", [('if answer.lower() == "yes":', 'if answer:')]),
           ("openai-agents", openai_agents, "agents_runner.py", [('"\\n\\nIt missed: "', '"\\n\\n"')]),
           ("openai-agents", openai_agents, "agents_runner.py", [("set_tracing_disabled(True)", "set_tracing_disabled(False)")]),
           ("n8n", n8n, "make_workflow.py", [("return words.length && !words.every(", "return words.length && words.every(")]),
           ("n8n", n8n, "make_workflow.py", [("{ role: 'user', content: $json.user_input }", "{ role: 'user', content: $json.task }")])]


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
    out = {"test": "team-runner smoke (local stub server)", "langgraph": langgraph(), "crewai": crewai(), "openai_agents": openai_agents(), "n8n": n8n()}
    ok(len(PROXY.hits) == 0, "no outside call through the proxy in any run; got %r" % PROXY.hits)
    out["proxy_hits"] = len(PROXY.hits); out["mutants"] = len(MUTANTS); out["mutants_caught"] = mutants()
    out.update({"checks": CHECKS[0], "failures": len(FAILS), "fail": FAILS,
                "versions": {k: md.version(k) for k in ("langgraph", "openai", "crewai")},
                "note": "real libraries, scripted local stub replies; wiring only, not a real model run (UNTESTED_RUNTIME stays)"})
    print(json.dumps(out, indent=1))
    sys.exit(1 if FAILS else 0)
