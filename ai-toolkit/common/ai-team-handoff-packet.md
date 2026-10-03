# AI Team Handoff Packet

A compact BSV template for handing work between AI workers, frameworks, or human reviewers without repeating completed work.

```text
JOB
- id:
- objective:
- owner-visible outcome:
- status: NOT_STARTED | IN_PROGRESS | BLOCKED | READY_FOR_REVIEW | DONE

SCOPE
- must do:
- must not do:
- budget:
- external actions allowed:
- approval boundaries:

CURRENT STATE
- authoritative source:
- branch / revision:
- live deploy / environment:
- changed paths:
- verified facts:

WORK COMPLETED
- actions:
- tests:
- results:
- fixes:

EVIDENCE
- source revision:
- check name:
- live URL or artifact:
- verification time:
- limitations:

NEXT ACTION
- highest-value next step:
- exact starting point:
- stop condition:
- owner approval needed: YES | NO

DO NOT REPEAT
- research already done:
- rejected approaches:
- duplicate work to avoid:
```

Rules:
- Use exact revisions, paths, check names, URLs, IDs, and counts.
- Mark DONE only when the requested result exists in the intended environment.
- Keep SOURCE_PREPARED, structural checks, runtime tests, and LIVE verification distinct.
- Do not guess missing results.
- Keep one highest-value next action.
- Preserve existing approval boundaries.

This is original BSV workflow material. It does not prove that any underlying runtime has been tested.
