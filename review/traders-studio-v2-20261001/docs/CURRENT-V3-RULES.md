# Current Traders Library rules — v3

These rules supersede conflicting v2 wording, especially the one-time purchase selector. This repository is a review workspace, not the complete production website.

## Author-controlled publication

Keep three independent fields:

- Page visibility: public or private. Private pages must be excluded from search/catalogue and restricted to the author and explicitly allowed verified users; an obscure URL is not authorization.
- Source/access: source-visible, protected, or invite-only. The author chooses the source license or custom terms. Do not force free or paid original work to be open source. Protected and invite-only source must never be delivered to customers, including paying subscribers. Invite-only requires author permission, with grant, expiry and revocation controls.
- Price model: free or monthly subscription. No one-time or annual paid offers.

A TradingView-like interface does not establish a Pine runtime or native account-management integration. Source protection must be supported by an actual native/server mechanism with verified expiry/revocation; never CSS hiding, obfuscation or a downloadable source described as protected. BSV page visibility is distinct from native TradingView script visibility, and native vendor/publishing rules still apply.

## Commercial terms — unchanged

The creator sets the monthly price. All payments use USDT on TRC20. Seller receives 80%; BSV receives a 20% fee. Do not add another payment network, currency, wallet or payment processor.

Preserve the existing BSV rolling-30-day contract: initial access starts at confirmed payment; early renewal adds 30 days to active expiry; late renewal starts a new 30 days at confirmation. Do not reset at a calendar-month boundary. A monthly offer does not authorize automatic wallet debits or automatic seller payouts.

Use fixed-precision micro-USDT, not floating-point settlement. Floor BSV's 20% fee to the micro-unit and give the residual to the seller, so shares exactly conserve gross. The server pins creator price, seller, product/revision, currency/network and 20/80 terms on every order. Price edits do not rewrite paid orders or shorten active access. Changes to renewal pricing require clear disclosure and confirmation.

Only verified, uniquely consumed payment receipts can activate/extend access and create revenue ledger entries. Payment submission is not payment confirmation. Duplicate events must not produce duplicate months or commissions. Keep existing payout approval and reconciliation processes.

## Free originals versus commercial remakes

BSV's collected, unchanged free sources remain free. A user may not simply relabel an unchanged free item as paid.

A user's independently modified remake of free material may be sold as a monthly subscription when the original grant permits the modification, commercial use and chosen delivery mode. Require upstream URL, applicable license/permission, notices and an explanation of substantive modifications. The review adapter must affirm commercial rights and substantive changes; self-declared originality or a renamed file is not proof.

Source visibility does not override third-party license conditions. Permissive licensing can coexist with source protection. Potential GPL/MPL disclosure obligations require a specific review of the grant and distribution model; do not make a blanket claim that any license can be removed or that all server-side use requires disclosure. Copies already delivered and their license rights cannot be remotely withdrawn when a subscription expires.

## Registration

Verified email registration remains mandatory for code retrieval, protected use, publishing and purchase. Keep public summaries source-free. Native invite-only paid use requires BOTH author authorization and a valid paid subscription. Invitations do not bypass billing. Registration is not marketing consent.

## Local implementation and integration status

The complete local v3 artifact is BSV-Traders-Studio-v3.zip, 2538909 bytes, SHA256 874a92310e46f4d0fdb60b90885a860eabd50caa3a6232aca8ce1a6b6e0d68f5. It includes updated UI, private/source access, invitation controls, monthly pricing and policy modules. Local checks: 66 Node tests, 325 static checks, 23 in-memory Chromium checks with fake APIs. No real payment, native invitation, platform compilation, trade or production deployment was performed.

The full v3 UI/service artifact is not yet incorporated into this review tree. This document and the separately committed subscription-policy module are integration inputs, not proof of a completed production upgrade. Do not deploy the old v2 one-time interface. Keep PR #3 draft and integrate into the CURRENT COMPLETE production source with verified auth, durable storage/outbox, genuine rights/security review, protected/native delivery and the existing commerce adapters. Preserve all unrelated BSV routes, functions, edge rules, headers, registration, payments and BSV-R02.

Before production DONE, verify registered free access, unchanged-free resale rejection, qualified paid remakes, private guessed URLs, protected-source denial even for payers, invite grant/expiry/revoke, subscription expiry, payment finality/idempotency, 20/80 conservation, cache/HEAD/Range/old-alias denial, real deployed version and rollback. A local test, SENT label, ACK or HTTP 200 is not production acceptance.
