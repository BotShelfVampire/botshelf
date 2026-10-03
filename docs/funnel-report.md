# Offline funnel evidence report

This tool aggregates a private, normalized export. It does not install tracking,
fetch customer records, verify a blockchain, execute an AI Team, send messages or
deploy anything. Source authenticity, consent, customer classification and export
completeness must be checked by an authorized operator before normalization.

Tested locally with Node.js 22.16.0. Uses only Node built-ins, with no packages.

```sh
node --test scripts/funnel-report.test.mjs
node scripts/funnel-report.mjs /private/normalized-snapshot.json > /private/report.json
```

Keep both snapshots and reports outside this public repository. Never commit
customer emails, IPs, keys, transactions, raw forms or private business metrics.
Opaque IDs are not proof of anonymization; do not make customer-level exports public.
CLI errors deliberately omit raw JSON, identifiers and filesystem paths.

## Example input: SYNTHETIC, not customer or sales evidence

```json
{
  "schema_version": 1,
  "window": {
    "start": "2026-09-01T00:00:00Z",
    "end": "2026-10-01T00:00:00Z",
    "timezone": "Asia/Tokyo"
  },
  "coverage": {
    "registrations": "complete",
    "runs": "partial",
    "payments": "missing"
  },
  "events": [
    {
      "event_id": "synthetic-registration-1",
      "kind": "registration",
      "at": "2026-09-02T12:00:00Z",
      "actor_id": "synthetic-person-1",
      "actor_kind": "customer",
      "environment": "production"
    }
  ]
}
```

All timestamps must be UTC ISO strings ending in Z, with either whole seconds or
exactly three fractional digits. The reporting interval is [start, end). The IANA
timezone is used only for counting distinct usage days.

### Common event fields

`event_id`, `kind`, `at`, `actor_id`, `actor_kind`, `environment` are required.
IDs and evidence references are 1-128 ASCII alphanumeric/hyphen/underscore
characters, beginning with an alphanumeric character. Do not use email addresses.
Actor classification is one of `customer`, `test`, `internal`, `unknown`, `vendor`.
The environment is `production` or `test`. Only explicitly classified customers
in production can contribute to business metrics. A registration alone does not
establish genuine use; leave uncertain actors `unknown` until checked.

### Additional fields by kind

- `registration`: none. Distinct actor IDs are counted once within the period.
- `payment_submitted`: optional opaque `order_id`. This event is never a sale.
- `run_completed`: `run_id`, `execution_kind` (`runtime`, `structural`, `sample`),
  boolean `accepted`, and `evidence_ref` for an accepted runtime run. Only accepted
  real-runtime records with evidence references count. The tool does not inspect
  the evidence itself. Input/output/task acceptance and approval-boundary checks
  must be completed before marking a run accepted.
- `payment_verified`: `order_id`, positive decimal-string `amount` (up to six
  decimal places), uppercase `currency`, `verification_source` exactly
  `server_ledger`, and opaque `evidence_ref`. A browser claim, submitted transaction
  ID or a QC record is not server confirmation. Currency format does not prove an
  asset is valid. Verify the actual asset and payment in the authoritative ledger.

Unsupported fields cause validation failure, helping prevent accidental raw-form
processing. Conflicting event IDs, actor labels or order amounts fail closed.
Repeated order IDs and run IDs are counted once. Supply a single normalized final
record per business event. Run IDs must identify one execution, not an entire
session. Source exports should be normalized before use; this is not an audit of
status-transition histories or events outside the reporting interval.

## Reading the result

`observed` contains eligible observations in the supplied export, not a claim that
all activity was captured. `totals` contains a value only when its source coverage
is `complete`; `partial` and `missing` give `null`, not invented zeros. Marking a
source `complete` is an operator assertion; a form export is not automatically a
complete commerce or runtime ledger. An entirely absent source cannot contain
eligible observations. Excluded records are counted separately.

Usage metrics are period activity, not first-ever activation or cohort retention.
Returning use requires distinct run IDs on at least two local calendar days.
No conversion percentage is calculated because period counts are not necessarily
one cohort. `gross_collected_by_currency` never combines currencies and uses exact
integer arithmetic. It is gross confirmed receipts, not net revenue, profit, MRR,
renewals or marketplace commission. Refunds, chargebacks, seller settlements and
accounting recognition require separate authoritative ledgers. This tool must not
be used to claim those metrics.

No production adapter, analytics endpoint or automated verification is included.
These tests exercise aggregation rules with synthetic fixtures; they do not prove
live integration, product runtime quality or customer demand.
