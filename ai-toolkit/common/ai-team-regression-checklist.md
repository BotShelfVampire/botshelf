# AI Team Regression Checklist

Use this before shipping a changed AI team, workflow, or agent configuration.

The goal is simple: prove that a useful workflow still works after prompts, models, tools, routing, or memory rules change.

## Test record

```text
Workflow:
Version:
Changed:
Model/runtime:
Tools enabled:
Test date:
Tester:
```

## 1. Golden tasks

Pick 3 to 10 representative tasks that the workflow must continue to handle.

For each task record:

```text
Input:
Expected result:
Must include:
Must not include:
Pass condition:
Observed result:
PASS / FAIL:
```

Prefer exact acceptance criteria over subjective ratings.

## 2. Tool routing

Check that each tool is used only for the job it is meant to perform.

- Read-only tasks do not accidentally call write actions.
- Search is used before answering when the task depends on current external facts.
- File tasks use the intended file/source instead of guessing from partial context.
- Tool failures are surfaced instead of being rewritten as success.
- Duplicate tool calls are avoided when the result is already available.

## 3. Handoff integrity

When one worker hands work to another, verify that the handoff contains:

- goal;
- current verified state;
- completed work;
- remaining work;
- evidence or references;
- the next concrete action;
- anything that must not be repeated.

The receiver should be able to continue without reconstructing the whole project.

## 4. Failure cases

Include at least three negative tests.

Examples:

- missing input;
- stale identifier;
- unavailable tool;
- contradictory instructions;
- malformed structured output;
- empty search result;
- duplicate request.

The expected behavior should be explicit.

## 5. Evidence check

A passing run should have enough evidence to distinguish:

- source prepared;
- structurally checked;
- runtime executed;
- externally verified.

Do not promote a workflow to a stronger verification label than the evidence supports.

## 6. Regression rule

A change fails regression when:

- a previous golden task now fails;
- the same task requires materially more manual repair;
- the workflow reports success without evidence;
- structured output no longer matches its schema;
- a tool is called outside its intended job;
- the handoff loses information needed by the next worker.

## 7. Compact result

```text
Golden tasks: __ / __ PASS
Negative tests: __ / __ PASS
Tool-routing checks: __ / __ PASS
Handoff checks: __ / __ PASS
Known limitations:
Decision: SHIP / FIX / HOLD
```

---

**BSV status:** SOURCE_PREPARED. This is a framework-neutral checklist and does not claim runtime verification of any external AI framework.
