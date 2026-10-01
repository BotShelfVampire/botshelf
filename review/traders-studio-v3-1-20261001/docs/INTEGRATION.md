# Traders Library v2 — registration and creator publishing

## Delivery status
Implemented: public catalogue and details, creator form and dashboard, server-side
publication/delivery domain service, a private curated-source loader, and local
checks. NOT completed: connection to the current BSV authentication, persistent
store, review workers and commerce system; live deployment; platform compilation
or trading. No real email verification, purchase, payout or trade is performed
by this review build. Earlier "no email gate" text is superseded.

## Accepted product behavior
- Catalogue summaries are discoverable. Code retrieval and creator operations
  require registered, email-verified accounts. Registration is NOT consent to
  promotional email. Reuse the current BSV verification/session mechanism.
- Users publish their own original indicators, strategies, EAs/cBots and related
  tools. They choose free or paid distribution, platform/version, files, author,
  explanations and usage terms. Original paid code need not become open source.
- Rights and security clearance is required. A clean submission can pass the
  approved automated review and be published by its creator without an operator
  manually constructing a page. Unresolved rights, risky IO, secrets and unknown
  formats must remain private/pending or be rejected, not auto-approved.
- Creators can save, preview, publish, edit a draft for a new version, and stop
  new distribution. A new draft must not alter an existing published release.
  Existing purchase records and version-bound entitlements remain separate.
- Author ownership is checked server-side. Clients cannot edit another owner's
  work, set review outcomes, fabricate verification or confirm a payment.
- Additional platform metadata is extensible. Names in the publishing selector
  are not claims of collected content, universal compatibility or successful
  runtime testing. Unknown named platforms require a real name and review.
- The spoken name "オープンマーケット" has not been identified as a specific
  product. Do not invent a platform or silently relabel a different product.

## Public/private layout — essential
Only public/ is a candidate static publish directory for the additive section.
private/ holds source bodies, ZIPs, full provenance and pending-directory data.
server/ and tests/ are NOT public static files. Do not upload this archive as the
entire site. Do not blindly overlay v2 onto v1: old /trading/sources/,
/trading/downloads/, source-containing item HTML, embedded BSV_DETAILS/BSV_ZIPS
and old standalone preview files must not remain anonymously served. Build a
fresh staging trading/ from public/trading/, keep rollback copies outside the
publish directory, and verify the final manifest for forbidden assets.

The earlier GitHub review branch and downloaded open-source copies were public.
Adding a BSV registration gate cannot revoke already-granted open-source rights
or hide upstream copies. This is access control for BSV service delivery, not a
new restrictive license. Do not impose an NDA, redistribution ban or trademark
claim on third-party open-source material.

## Adapters to connect in the current BSV implementation
1. resolveSession(Request): server-verified session -> {id, emailVerified,
   disabled, displayName}. Ignore user JSON, browser storage and email strings.
   Bind account suspension, expiry and verification to current server records.
2. store.transaction(fn): durable, serializable transaction. tx.get, tx.set,
   tx.list and tx.audit. Isolate tenant reads and immutable release records.
   Use database indexes/page limits for production; the in-memory test adapter
   is not production persistence. Never log source text or private evidence.
3. review(snapshot): trusted scanner/rights service. Return fingerprint equal to
   contentHash, security/rights verdicts, evidenceRef, and explicitly resolved
   findings. No default PASS implementation. Include dependency licensing,
   permission scope (commercial distribution where relevant), expiry and
   territory in rights review; inspect full source without executing it.
   Scan secrets/malware/dependencies before publication. Example regex findings
   are only intake signals, never complete malware or legal clearance.
4. commerce.registerProduct(snapshot): current BSV product flow, idempotent by
   listing/version/hash. Return matching product ID, price, currency and version.
   Reuse the existing approved seller split, settlement, renewal/refund terms
   and ledger. Do not invent a new wallet, fee, payment service or automatic
   real-money payout. Publishing is not permission to make a real purchase.
5. commerce.hasEntitlement(snapshot): server-verified entitlement for this buyer,
   product and immutable version. No access from a transaction claim or UI flag.
   Define version upgrades and 30-day access consistently with existing terms.
   Already downloaded source cannot be remotely revoked.
6. commerce.beginCheckout(snapshot): existing BSV checkout URL, same origin.
   This step only opens checkout. Never charge a saved method without the
   user's confirmation. Handle double-clicks/idempotency in existing checkout.
7. allowRequest(Request,actor,operation): existing rate/abuse/quota controls.
   No no-op allow-all adapter in production. The handler requires exact Origin
   and JSON for state-changing calls; integrate existing CSRF defenses too.
8. curatedAccess: createCuratedAccess(privateDirectory), or equivalent existing
   private-store adapter. Verify session on every source/ZIP request. Strip
   caching and block anonymous direct, alternate and Range/HEAD paths too.

## API routing
GET /api/traders/session; GET /api/traders/catalogue (metadata only)
GET /api/traders/mine; GET /api/traders/listings/:id (owner only)
POST /api/traders/listings; PUT /api/traders/listings/:id
POST /api/traders/listings/:id/publish
POST /api/traders/listings/:id/unpublish
GET /api/traders/listings/:id/source?revision=N
POST /api/traders/listings/:id/checkout
GET /api/traders/curated/:id?format=json (verified email only)
GET /api/traders/curated/:id (verified email only, original ZIP)

Serve the function via the established Netlify routing configuration and
preserve existing functions, edge middleware, headers, redirects and BSV-R02.
No security-header relaxation. Verify no direct static route or alternate host
serves the source bytes. The standalone preview shows forms only; it is never
an authenticated session and contains no source packages.

## Required release checks
Anonymous and unverified requests: no source; no create/edit/publish/checkout.
Verified user: free source and own-draft operations work; no other-owner edits.
Paid: payment unconfirmed denied; confirmed correct entitlement allowed; wrong
product/version/owner denied. Test refunds/expiry according to existing policy.
Stale revisions, double submits, scan outages, reviewer mismatches, licence
conflicts, oversized files, malicious filenames and private keys fail closed.
Public catalogue, HTML, JS, JSON and caches contain no source or private evidence.
Recheck actual URLs and deployed manifest, registration, normal existing paid
flows and rollback reference before calling the release complete.

## Natural public copy
「掲載・配布の権利を確認したコードを、使い方の解説付きで提供します。」
「作者名と利用条件を明記しています。」
「コードの取得・作品の公開にはメール登録が必要です。」
「自分の作品を公開する（無料・有料）」
Keep actual LICENSE/NOTICE and author notices in delivered files; changing
public wording does not remove legal notices or recipient rights.

## V3 is authoritative over earlier sections

Read `OWNER-RULES-V3.md` first. There is no one-time paid option. All paid offers are monthly USDT/TRC20 subscriptions with the fixed 20% BSV / 80% seller split. Visibility and source access are independent author choices. Do not reinterpret source protection as JavaScript hiding.

New dependencies: `server/subscription-policy.mjs`, `server/publishing-policy.mjs`.
`createCreatorService` and `buildTradersEndpoint` now accept `protection` and `accounts` adapters in addition to existing store/review/commerce.

- `accounts.resolveVerifiedUser(email)` returns a verified local account record or null; it does not send mail or create an account.
- `protection.checkPublication(snapshot)` binds source hash and adapter identity to verified source privacy, expiry/revocation capability and native-platform rules. An unimplemented runtime cannot return a passing attestation.
- `protection.authorizeUse(context)` returns `state: ready|pending` and an opaque reference. Extra adapter fields are discarded. Native permissions are not granted by merely recording a BSV invitation.
- `tx.outbox(event)` must persist a revoke job in the same serializable transaction as the ACL revocation. A production worker must reconcile native permission and expiration separately. Never mark the native result completed while queued.
- `commerce.getSubscription(expected)` returns the server-verified ACTIVE record with actor, listing, product, revision/hash, CONFIRMED payment, confirmation reference, order, USDT/TRC20 and valid start/expiry. A boolean entitlement is insufficient.
- `commerce.registerProduct` must echo the pinned price and all required commercial terms; mismatches prevent release. The `PROTECTED_ACCESS` boundary type denotes native/server-protected use, not a raw download. Map it explicitly into the existing product system; do not send an unsupported type to the live ledger.
- `commerce.beginCheckout` receives only pinned server terms. Use the existing trusted checkout and wallet. New orders must not trigger real charges or payouts during testing.

New routes: GET `/api/traders/listings/:id/details`; GET/POST `/api/traders/listings/:id/invitations`; POST `/api/traders/listings/:id/revoke-invitation`; POST `/api/traders/listings/:id/use`. Mutation routes require origin and session validation. Invitation `expectedRevision` is the returned access-list revision, not the content revision.

The existing `review` decision additionally must affirm `commercialUseAllowed` and `substantiveChanges` for paid remakes. Potential copyleft-protected offers need a reviewed `closedSourceAllowed: true` and `sourceDisclosureRequired: false` decision; this is an actual rights finding, not user input. If source disclosure is required, supply an appropriate disclosure route/design rather than claiming wholly hidden source.

Native and paid integration is unfinished. Do not deploy the standalone preview, the test fixture store, private source directory, or permissive fake review/commerce adapters to public production. Preserve existing BSV auth, commerce and BSV-R02 protections. Commit review code into the authoritative source only after matching current production and securing rollback.
