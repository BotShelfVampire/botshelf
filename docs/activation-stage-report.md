# BSV activation-stage report (private/offline)

Status: **REVIEW**. This is a local reporting utility, not a live integration, production runtime result, payment proof, deployment, or customer claim.

## Purpose

Measure one evidence-backed experiment sequence without exposing participant data:

1. first accepted activation of a real customer in production;
2. an accepted runtime use by that same customer on a later local calendar day;
3. a server-ledger-verified payment by that same activated customer.

Same-day repeats are not return use. A submitted transaction ID, browser claim, test/QC activity, owner/internal use, vendor activity, structural check, sample output, or unaccepted result does not count.

## Run

```sh
node scripts/activation-stage-report.mjs /private/activation-snapshot.json
node --test scripts/activation-stage-report.test.mjs
```

Keep both the input and generated report private. Use opaque IDs only; email addresses and extra fields are rejected. The CLI suppresses parser details and paths on error.

## Input contract

Top level:

- `schema_version`: `1`
- `window`: UTC `start`, exclusive UTC `end`, and an IANA `timezone` such as `Asia/Tokyo`
- `coverage`: `activations`, `runs`, and `payments`, each declared `complete`, `partial`, or `missing`
- `events`: strict event objects

Accepted event kinds:

- `activation_accepted`: requires `evidence_gate: "PASS"`, `accepted_by_participant: true`, opaque `activation_id`, and opaque `evidence_ref`
- `run_accepted`: requires `execution_kind: "runtime"`, `accepted: true`, opaque `run_id`, and opaque `evidence_ref`
- `payment_verified`: requires opaque `order_id`, positive decimal-string `amount`, explicit `currency`, `verification_source: "server_ledger"`, and opaque `evidence_ref`
- `payment_submitted`: retained only to make explicit that submission is excluded

Every event also requires UTC `at`, opaque `event_id` and `actor_id`, explicit `actor_kind`, and explicit `environment`. Only `actor_kind: "customer"` in `environment: "production"` is eligible.

## Output semantics

`observed` reports eligible records found in the supplied snapshot. `totals` reports a metric only when every required source is declared complete; otherwise that total is `null`, even if observations exist. A source declared missing cannot contain an eligible observation.

The report returns only aggregate counts and currency-separated gross amounts. It never returns actor, activation, run, order, or evidence identifiers. Gross collected is not net revenue, profit, MRR, renewal, or seller-adjusted revenue.

Exact duplicate events and business records count once. Material conflicts on reused event, activation, run, or order IDs fail closed and produce no report.

## Acceptance boundary

Passing local tests establishes only deterministic offline behavior for sanitized input. Before any business metric is accepted, the private adapter and export must establish authoritative production provenance, deduplication scope, coverage completeness, timezone, test exclusions, and evidence acceptance. Do not publish this report or merge/deploy the Draft PR without review.
