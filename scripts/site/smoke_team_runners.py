#!/usr/bin/env python3
"""Smoke test: the LangGraph and CrewAI team runners, unchanged, on the real libraries against a local
OpenAI-compatible STUB server (127.0.0.1, scripted replies). No model, no paid API, no external network
(HTTPS_PROXY points at a closed local port). Checks the wiring only: the requests the runner sends, the
revision loop, the approval gate and what is saved. It says nothing about answer quality on a real model.
usage: python smoke_team_runners.py  (needs langgraph + openai, crewai in the running interpreter)"""
import http.server, importlib.metadata as md, json, os, pathlib, shutil, subprocess, sys, tempfile, threading

REPO = pathlib.Path(__file__).resolve().parents[2]
SYSTEM = "BSV smoke team. Review the input.\nOUTPUT:\n1) Pass/fail for publish\n2) Blockers"
INPUT = "Draft: release notes for version 2."
FAILS, CHECKS = [], [0]
MUTATE = []


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


def run_runner(sub, script, stub, answers, model):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="bsv-smoke-"))
    d = tmp / "runner"; shutil.copytree(REPO / "ai-toolkit" / sub, d, ignore=shutil.ignore_patterns("out", "__pycache__"))
    for old, new in MUTATE:  # mutant runs only: break the copied runner, never the repo file
        f = d / script; t = f.read_text(); assert old in t, old; f.write_text(t.replace(old, new, 1))
    (tmp / "prompt.txt").write_text('SYSTEM = """%s"""' % SYSTEM); (tmp / "input.txt").write_text(INPUT)
    env = dict(os.environ, BSV_LLM_BASE_URL=stub.url, BSV_LLM_MODEL=model, BSV_LLM_API_KEY="stub", HOME=str(tmp),
               HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9", NO_PROXY="127.0.0.1,localhost",
               CREWAI_DISABLE_TELEMETRY="true", CREWAI_TRACING_ENABLED="false", OTEL_SDK_DISABLED="true")
    p = subprocess.run([sys.executable, str(d / script), "--task", "doc-review", "--prompt", str(tmp / "prompt.txt"), "--input", str(tmp / "input.txt")],
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


MUTANTS = [("langgraph", langgraph, "runner.py", [('user += "\\n\\nReviewer feedback: " + state["feedback"]', 'pass')]),
           ("langgraph", langgraph, "runner.py", [('return "produce" if state["missing"] and', 'return "produce" if False and')]),
           ("crewai", crewai, "crew_runner.py", [('if answer.lower() == "yes":', 'if answer:')]),
           ("crewai", crewai, "crew_runner.py", [("if missing and revisions < MAX_REVISIONS:", "if False:")])]


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
    out = {"test": "team-runner smoke (local stub server)", "langgraph": langgraph(), "crewai": crewai(), "mutants_caught": mutants()}
    out.update({"checks": CHECKS[0], "failures": len(FAILS), "fail": FAILS,
                "versions": {k: md.version(k) for k in ("langgraph", "openai", "crewai")},
                "note": "real libraries, scripted local stub replies; wiring only, not a real model run (UNTESTED_RUNTIME stays)"})
    print(json.dumps(out, indent=1))
    sys.exit(1 if FAILS else 0)
