# Compile-result intake — design (owner-confirmable, never auto-verified)

Status: IMPLEMENTED (conservative), cycle 8, 2026-10-03. The owner answered the open questions with the most conservative option; see "Implemented (cycle 8)" at the end. The flow below is the original proposal; where it differs, the cycle-8 section wins.

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

## Open questions for the owner (answered 2026-10-03, see below)

1. Is "User-reported" wording acceptable on public pages, or should approved reports stay internal only?
2. Should failed-compile reports be public?
3. Retention period for rejected reports (proposal: 30 days, then delete).

## Implemented (cycle 8) — owner answers, most conservative option

| Question | Answer |
|---|---|
| Who may send | Email-verified accounts only (`requireUser`, `botshelf_sid` session). Anonymous → 401, foreign `Origin` → 403. |
| Where stored | Server-side in the existing Netlify Blobs setup, store `compile_reports`, key `rep:<id>`, record keyed to the account id. |
| PII | None beyond the existing account email. The report holds `user_id` only; the review queue looks up the email from the account at read time. No IP, no user agent, no name. |
| Who reviews | ~~Owner only~~ superseded 2026-10-03 20:57 JST (cycle 9): owner, BSV ops and ChatGPT. See "Reviewers (cycle 9)" below. |
| Auto-promotion | Never. States: `pending` → `approved-user-reported` / `rejected` / `needs-info`. There is no `verified` state, and every stored report has `self_reported:true, bsv_verified:false, public:false`. No code path reads reports into a page, catalog or count. |
| Public display (Q1) | None. Approved reports stay internal. |
| Failed compiles public (Q2) | No. Not shown anywhere. |
| Retention (Q3) | Rejected reports are deleted 30 days after review (lazy purge when the owner opens the queue). |
| Limits | 10 reports per account per day; same account + recipe + target + fp + status is merged (`duplicate:true`). Whitelisted fields only: `recipe` ≤120, `target` (builder target list), `status` (5 values), `platform` ≤120, `notes` ≤1000 (HTML stripped), `steps` ≤12 booleans, `fp` `^[0-9a-f]{8}$`, optional `builder` file name. Any other field → 400. |
| Messages | No email is sent to anyone when a report arrives or is reviewed. |

Source: `site-functions/compile-report.js` (installed into `<deploy root>/netlify/functions/` by
`scripts/site/install_compile_report_fn.py`). Test: `node scripts/site/test_compile_report_fn.js <root>` (in-memory store).
Builder: "Send to BSV (owner review)" button under "Record your result"; the browser copy (localStorage) works as before.

Owner review, example:

```
curl -s -H "x-admin-secret: $LICENSE_ADMIN_SECRET" 'https://botshelfvampire.com/.netlify/functions/compile-report?op=queue&state=pending'
curl -s -X POST -H "x-admin-secret: $LICENSE_ADMIN_SECRET" -H 'Content-Type: application/json' \
  -d '{"id":"crp_...","decision":"rejected","note":"QA"}' 'https://botshelfvampire.com/.netlify/functions/compile-report?op=review'
```

## Reviewers (cycle 9, owner order 2026-10-03 20:57 JST)

Review is no longer owner-only. Three reviewers:

| Reviewer | How | Sees |
|---|---|---|
| Owner | header `x-admin-secret` (`LICENSE_ADMIN_SECRET`) | report + account id + account email (looked up at read time) |
| BSV ops (on the box) | header `x-bsv-reviewer-key` = Netlify env `COMPILE_REVIEWER_KEY` (functions scope, production, secret). Box copy: `box-local reviewer-key file (chmod 600, never committed)`, chmod 600, never committed | report + account id only |
| ChatGPT | hourly digest email from support@ (BSV ops's Gmail routine), new pending submissions only | report + account id only; email-like strings in free text redacted |

Endpoints (both roles): `GET ?op=queue[&state=pending]`, `GET ?op=get&id=crp_...`, `POST ?op=review` with `{"id","decision","note"}`.
Decisions: `approved-user-reported`, `rejected`, `needs-info`. There is no `verified` decision; every response carries `bsv_verified:false, public:false`.
A missing or wrong key returns 401 (key compared as sha256 with a constant-time check; keys under 32 characters are refused).

Box tool (not in the repo, because it sits next to the SMTP scripts): `box-local digest tool (not in the repo)`

```
python3 compile_reports_digest.py digest                 # write digests/compile-reports-<ts>.md (pending)
python3 compile_reports_digest.py digest --email         # hourly: mail NEW pending ones to ChatGPT, none if nothing new
python3 compile_reports_digest.py get crp_...
python3 compile_reports_digest.py reject crp_... --note "spam/test"
python3 compile_reports_digest.py decide crp_... needs-info --note "..."
```

Reviewers may reject spam/test records, fix issues a report reveals, and turn useful reports into improvements. Public status text still changes only through a reviewed commit, and "Runtime-tested by BSV" only with BSV's own run.
