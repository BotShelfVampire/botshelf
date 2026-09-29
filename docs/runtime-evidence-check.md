# BSV-R01-A runtime evidence gate

This offline checker decides whether a private evidence record is structurally
complete enough for review. It is for one real free Switchboard job performed by
a consented newcomer. It does not execute Switchboard, inspect screenshots, verify
an account, contact a participant, publish evidence, or connect to production.

```sh
node --test scripts/runtime-evidence-check.test.mjs
node scripts/runtime-evidence-check.mjs /private/runtime-evidence.json
```

Keep the input and every referenced artifact private. Do not commit emails, names,
IP addresses, keys, raw chats, screenshots, customer identifiers, or business data.
The output intentionally omits input/output summaries and evidence references.

## Required private record

```json
{
  "schema_version": 1,
  "task_id": "BSV-R01-A",
  "product": "switchboard-free",
  "participant": {
    "kind": "newcomer",
    "consent_confirmed": true
  },
  "timing": {
    "started_at": "2026-09-29T10:00:00Z",
    "completed_at": "2026-09-29T10:05:00Z",
    "timezone": "Asia/Tokyo"
  },
  "execution": {
    "environment": "production-free",
    "job_kind": "real",
    "execution_kind": "runtime",
    "input_summary": "Prioritize three competing backlog items for a small operator.",
    "output_summary": "Returned one recommended next action with a short rationale.",
    "one_next_action_produced": true
  },
  "approval": {
    "boundary_present": true,
    "external_action_attempted": false,
    "stopped_before_external_action": true,
    "human_decision": "pending"
  },
  "outcome": {
    "accepted_by_participant": true,
    "failure_stage": null
  },
  "evidence": {
    "environment_ref": "env-proof-1",
    "input_ref": "input-proof-1",
    "output_ref": "output-proof-1",
    "approval_ref": "approval-proof-1"
  }
}
```

The example is synthetic schema documentation, not a customer run or product
result. Replace it only in a private workspace after inspecting the underlying
runtime evidence. References must be opaque private identifiers, not public URLs.

## Interpretation

- `evidence_gate: PASS` means the record describes a consented newcomer, a real
  job on the free production path, a runtime execution, one prioritized next
  action, and a stop before external action.
- `accepted_runtime_eligible: true` additionally means the participant accepted
  the result. It is one observed run, not a returning user, payment, or renewal.
- `FAIL` keeps the run out of activation counts and lists explicit reasons.
- Structural validation never replaces inspection of the private artifacts.
- Do not treat a sample, local test, owner run, or existing test environment as
  evidence that a newcomer completed the product job.
