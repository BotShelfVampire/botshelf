# BSV Transparency & Trust OS

Updated: 2026-10-03
Status: core brand and conversion principle

## Brand principle

**Keep the operator individual low-profile. Make the business unusually transparent.**

BSV should not rely on founder personality, face, biography or lifestyle to create trust.

Trust should come from inspectable mechanics.

## What must be transparent

### Buying

Publicly explain:
- free vs paid
- price before purchase
- payment network
- what starts access
- access duration
- renewal behavior
- product type
- prerequisites
- verification status
- support/recovery path

### Selling

Publicly explain:
- free and paid listing options
- seller revenue share
- BSV share
- payout timing
- payout states
- hold categories
- seller public-contact opt-in
- what BSV reviews
- what BSV does not guarantee

### Verification

Every asset should expose one scoped status:
- UNTESTED
- STRUCTURAL / SOURCE PREPARED
- PARTIAL
- VERIFIED
- BLOCKED

Never use a generic trust badge that hides the exact evidence.

Where practical, link the evidence type:
- source revision
- CI result
- runtime/platform version
- live URL
- test date
- limitation

### Reliability

Maintain a public status/history surface for material incidents once the underlying incident facts are verified.

Do not hide outages that materially affected registration, payment, entitlement, or seller payout.

A useful incident record:
- started
- resolved
- affected surface
- customer impact
- root cause
- corrective action
- whether customer action is required

### Commercial mechanics

Keep one public canonical statement for:
- payment network
- access model
- seller split
- payout timing
- support
- refund/dispute policy
- fee types

Do not let homepage, seller guide, checkout and old articles drift into conflicting rules.

## What remains private

Do not publish merely for "transparency":
- operator legal/private identity unless legally required
- account credentials
- internal security design that increases attack risk
- customer private data
- seller private wallet/contact data
- private moderation notes
- private pilot/session evidence
- unpublished fraud signals

Transparency is not indiscriminate disclosure.

## Current business facts to keep consistent

- Free content: email registration/access flow; no USDT required.
- Paid access: product-specific price shown before payment.
- Payment rail currently used by BSV commerce: USDT on TRC20 where current product checkout specifies it.
- Recurring-access products: rolling 30-day access from confirmed payment.
- Seller product-sale split: seller 80% / BSV 20%.
- Eligible seller payout: within 7 business days after confirmed sale, subject to documented holds.
- Support: support@botshelfvampire.com.
- Verification claims must remain evidence-scoped.

Always fresh-read current production before rendering these facts.

## Transparency Center

Create one canonical public page, eventually:

`/transparency/`

Recommended sections:

1. How BSV makes money
2. How buyer access works
3. How seller payouts work
4. Verification labels
5. Current platform/runtime coverage
6. Known limitations
7. Recent material changes
8. Incident history
9. Support and dispute path
10. Privacy: what BSV does and does not publish about operators/users

This page should be useful enough that a skeptical buyer or seller can inspect BSV without needing to trust a founder persona.

## Machine-readable trust manifest

Publish a public machine-readable manifest generated from current config/source, for example:

`/.well-known/bsv-trust.json`

It may expose:
- brand
- canonical domain
- support address
- payment rails
- seller split
- payout rule
- access rule
- verification vocabulary
- status/change URLs
- last updated timestamp

Do not include secrets or customer/seller private data.

## Growth effect

Transparency is a conversion system.

Measure:
- buyer guide → checkout conversion
- seller guide → first listing
- transparency page views → purchase/listing conversion
- support questions reduced
- payment duplicate rate
- payout support tickets
- dispute rate

The principle succeeds only if it increases trust while preserving operator privacy.
