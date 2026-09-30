# Paid order / license integrity check

Status: **REVIEW**. This is an offline consistency check for a private, normalized snapshot. It is not connected to production, does not repair a license, does not verify a customer payment by itself, and does not establish revenue.

Use it to detect the core failure class where an authoritative server-ledger payment, order state, and required license disagree. It also detects orphan records, amount/currency mismatch, duplicate verified payments, product mismatch, and active licenses attached to non-active orders.

Run:

```sh
node scripts/order-license-integrity.mjs /private/order-license-snapshot.json
```

The private JSON must contain `schema_version: 1`, explicit `complete` / `partial` / `missing` coverage for `orders`, `payments`, and `licenses`, plus normalized arrays. Use opaque IDs only. Do not put emails, txids, wallet addresses, keys, cookies, IPs, or raw customer records in the input, repository, test logs, or report.

A result is:

- `FAIL` when any inconsistency is observed, even with incomplete coverage;
- `PASS` only when all three sources are declared complete and no inconsistency is observed;
- `UNKNOWN` when no inconsistency is observed but one or more sources are incomplete.

For a real incident, keep the input private and retain separate evidence of source coverage, server-ledger verification, the production version, recovery action, and post-recovery order/license behavior. A local PASS is not production repair acceptance.
