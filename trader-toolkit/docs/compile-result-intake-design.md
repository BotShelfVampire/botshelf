# Compile-result intake — design (owner-confirmable, never auto-verified)

Status: DESIGN ONLY. Nothing here is implemented or deployed. No new endpoint, form, email or storage exists yet.

## Why

The browser recipe builder already lets a signed-in user keep a **compile record** per target in their own browser
(`localStorage` key `bsv-rb-compile-log`, max 200, also downloadable as `<recipe>.<target>.compile-record.md`).
Each record carries `status` (`not-tried`, `compiled`, `compiled-warnings`, `compile-failed`, `ran-replay`),
platform/version text, notes, checklist steps, an 8-hex fingerprint of the generated code (`fp`),
`self_reported: true` and `bsv_verified: false`. Today those records never leave the user's browser.

The goal is to let a user **send** a record to BSV so the owner can review it, while keeping every public status honest:
a user report is evidence for the owner to weigh, not a verification.

## Hard rules

1. **No auto-promotion.** No code path changes a catalog/compatibility status, a "Runtime-tested by BSV" count, or a page badge
   because a report arrived. Only an explicit owner action (a reviewed commit) can change public status text.
2. **Two different words.** "User-reported" (with count and date) is the most a report can produce on the site, and only after owner
   approval. "Verified by BSV" stays reserved for checks BSV itself ran, with evidence in the repo.
3. **Real session only.** Intake requires the existing server-verified email session (same cookie/session check as gated sources).
   No anonymous intake, no client-side-only gate.
4. **Data minimisation.** Accept only the record fields above plus `recipe` name, `target`, `fp`, builder js hash. No generated code,
   no account numbers, no broker logins, no screenshots in v1. Notes are capped (1000 chars) and treated as untrusted text.
5. **No payment coupling.** Intake never touches checkout, USDT/TRC20 split, entitlement or gates.
6. **Fingerprint honesty.** A report applies only to the exact code with that `fp`. If the generator output for that recipe/target
   changes, the report is shown as "for an earlier version" and does not count for the current one.

## Proposed flow

```
builder (signed in) ──"Send this record to BSV"──▶ POST /api/compile-report  (session required, rate-limited)
                                                    │  validate schema, strip HTML, cap sizes
                                                    ▼
                                         pending store (Netlify Blobs, key per report id)
                                                    │
owner review page (/ops, owner session only) ◀──────┘   list pending → Approve as user-reported / Reject / Need info
                                                    │
                                   Approve = writes a reviewed entry to an export file the owner
                                   commits by hand (trader-toolkit/reports/user-reports.json); site build
                                   reads that file to show "User-reported: N (latest YYYY-MM-DD, fp xxxxxxxx)".
```

- **Rate limit:** e.g. 10 reports per account per day; duplicates (same account+recipe+target+fp+status) are merged.
- **States:** `pending` → `approved-user-reported` | `rejected` | `needs-info`. There is no `verified` state in this system.
- **What approval shows:** next to the target on the recipe page and in compatibility.md — "User-reported compile: 2 (latest 2026-10-xx)
  — not verified by BSV". `compile-failed` reports are shown too (honest negative evidence), with the platform/version text.
- **Contact:** no automatic email to the reporter in v1 (sending messages needs owner approval). The review page can show a
  "copy reply draft" helper only.

## Validation checklist for a future implementation

- [ ] Endpoint rejects requests without a valid session (401) and with foreign origins (CSP/Origin check).
- [ ] Schema: `status` in the 5 known values, `target` in the builder's target list, `fp` matches `^[0-9a-f]{8}$`, sizes capped.
- [ ] No status/badge text changes until `user-reports.json` is edited in a reviewed commit.
- [ ] `test_live_toolkit.py` gains a check that no page says "verified" for a target whose only evidence is user reports.
- [ ] Gate tests, CSP sweep and payment/health checks unchanged.

## Open questions for the owner

1. Is "User-reported" wording acceptable on public pages, or should approved reports stay internal only?
2. Should failed-compile reports be public?
3. Retention period for rejected reports (proposal: 30 days, then delete).
