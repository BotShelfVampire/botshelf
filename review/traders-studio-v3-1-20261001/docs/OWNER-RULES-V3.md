# Traders Library / Creator Studio — current publication and subscription rules

This revision replaces any earlier one-time sale, registration-free access, mandatory-open-source, or blanket ban on commercial remakes. It changes the local implementation; it is not a production-deployment statement.

## Author choices

Page visibility: **Public** (listed/searchable) or **Private** (owner and explicitly allowed verified users only). Private is an authorization rule, not an obscure URL.

Source and usage: **Source visible**, **Source protected**, or **Invite-only**. The latter two do not return source files to customers, even to paying subscribers. The author retains access to their own code. Invite-only requires an active author grant in addition to any paid subscription. Expiry and revocation are supported in the BSV ACL, with a durable outbox for native-platform revocation. An outbox entry is not evidence that TradingView or another platform has processed revocation.

The author chooses the license or custom usage terms; free work need not be open source. Source visibility and open-source licensing are not the same thing. Existing third-party conditions are not overwritten by a visibility selector. Permissive licensing can be consistent with protected delivery. Potential GPL/MPL source-disclosure obligations require an explicit review of the actual grant and delivery model; checking a box or renaming a file cannot waive those obligations.

TradingView is a UX reference, not a claim that BSV executes arbitrary Pine or controls TradingView accounts. Public/private on BSV is distinct from public/private on a native platform. A native integration must follow that platform's current publishing and vendor rules. Protection publication requires a pinned-source attestation that source stays private and that native expiry/revocation and platform requirements are satisfied. A missing bridge fails closed; CSS, JavaScript hiding and obfuscation are not source protection.

## Free collection versus paid remakes

BSV's collection of unchanged third-party free code stays free. An unchanged free item cannot be assigned a paid price by either the browser form or the server. The source library is not silently converted into subscription inventory.

Creators may publish their own substantial remakes of freely available work as paid monthly subscriptions when modification, commercial use and the selected distribution/protection method are permitted. Collect the upstream URL, applicable grant, permission evidence when needed, notices and an explanation of actual changes. Rights review must affirm commercial permission and substantive changes before releasing a paid remake. Name/color/description-only relabeling does not automatically qualify. Source scanning and a rights reviewer must detect misclassified unchanged copies; self-declared originality alone is not proof.

## Commercial contract (unchanged BSV economics)

| Field | Required value |
|---|---|
| Paid model | Monthly subscription only; no one-time or annual purchase |
| Price | Set by the creator; positive fixed-precision USDT |
| Payment currency | USDT only |
| Network | TRC20 only |
| Seller share | 80% |
| BSV fee | 20% |
| Access duration | 30 rolling days from confirmed payment, not a calendar-month reset |
| Early renewal | Existing active expiry plus 30 days |
| Late renewal | New confirmed-payment time plus 30 days |
| Automatic debit | Not implemented or represented as authorized |

Amounts use integer micro-USDT, never binary floating-point settlement. Rounding follows a documented conservation rule: floor the 20% BSV fee at one micro-USDT and allocate the remaining amount to the seller. Seller plus BSV exactly equals the receipt. This sub-micro rounding convention does not add a fee. The UI calculator is illustrative; the server and existing ledger determine actual amounts.

Keep the existing official destination wallet, token identity, chain verification/finality and seller-payout process. Do not invent a wallet or automatically send payouts. A user-submitted transaction ID is not proof of payment. Confirmation, unique receipt consumption, revenue ledger entries and subscription extension must be atomic/idempotent in the existing commerce adapter. Repeated events must never extend a subscription twice or create duplicate fees. The pure renewal and split functions do not themselves verify or consume payment.

Order terms include the creator's price, listing/release, source hash, USDT/TRC20, 30-day term and 20/80 split. Subsequent edits never rewrite an existing order or shorten active paid access. Renewal repricing must be disclosed and confirmed, not retroactively charged. The existing product/entitlement adapter must map subscription updates to eligible revisions without requiring a second subscription just because the author publishes a new version. Prior paid versions and obligations remain after an item is delisted.

A monthly source-visible offer describes its continuing updates/access/support. Stopping BSV downloads on expiry does not revoke copies already received or rights granted by their license.

## Mandatory registration

Code retrieval, protected use, publishing and purchase require a verified server session and confirmed email ownership. A public catalogue summary does not carry source bytes. Inviting a user requires lookup of an already verified account by the trusted account adapter. No invitation email is sent by this implementation. Registration is separate from consent to marketing.

## Implemented locally in v3

- Publishing form: independent visibility/access selectors, upstream/remake details, monthly-only price, TRC20 and 80/20 display.
- Fixed-precision revenue preview, price parsing, receipt split and rolling-period calculations.
- Server-side enforcement of product terms, protected-source denial, private metadata, active subscription checks and author-controlled ACLs.
- A separate invitation revision avoids changing a paid product merely because access is granted/revoked.
- Source-free public metadata and standalone preview. All 39 curated items remain free and in private source storage for authenticated retrieval.

Production adapters for verified authentication, durable storage/outbox, real rights/security decisions, native/source-protected delivery and the existing commerce ledger are not connected here. No payment, native invitation, platform compilation, brokerage trade or production deployment was performed. Test adapters must never be installed as production services.

## Acceptance tests

Check positive and negative cases: registered free retrieval; monthly-only fee/price/currency/network; unchanged free resale rejection; eligible paid remake; private guessed URLs; protected source even for a payer; invite expiry/revoke; invite alone cannot unlock paid use; subscription expiry; unconfirmed/refunded/wrong-network/wrong-version payments; frontend price and authentication tampering; HEAD/Range/cache and old static aliases. Independently verify native revocation/expiry and recurring payment idempotency after integration, rather than inferring them from local tests.
