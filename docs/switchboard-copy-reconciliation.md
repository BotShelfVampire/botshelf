# Switchboard free/paid copy reconciliation

Status: **REVIEW — source handoff required before implementation**  
Task: **BSV-R01-C**  
Public pages checked: **2026-09-30 JST**

This document defines the smallest safe copy correction visible from the current
public pages. It does not identify the production repository, prove the payment
backend, modify the live site, or authorize a deployment. The current production
source, backup, and deployed-version relationship remain unknown.

## Observed public evidence

### Free Switchboard

URL: <https://botshelfvampire.com/switchboard-cos.html>

- The page labels the product free and says it stays free with no key.
- It describes the job as one short next-action proposal with a human `Yes` stop.
- The transition copy says the free version proves the job “runs once,” which can
  be read as a one-time free allowance even though the same page says it stays free.
- The English transition says Desk confirms after txid review and the Japanese
  transition says Desk manually issues access after checking the txid.

### Monthly Switchboard

URL: <https://botshelfvampire.com/paid-switchboard.html>

- The listed price is 20 USDT for rolling 30-day access on TRON / TRC20.
- The page describes a server order moving through `SUBMITTED`, `VERIFYING`, and
  `ACTIVE`, with My purchases showing the key after the server marks it active.
- The free Switchboard is separately linked and described as free with no key.

### Checkout

URL: <https://botshelfvampire.com/checkout.html?amount=20&team=Switchboard&term=month>

- The page says chain verification is server-side and the server order grants
  access; the Netlify form is only an optional backup notice.
- The same page later says Desk checks the txid by hand and that confirmation is
  not automatic.
- Both statements cannot safely describe the confirmation mechanism without
  inspecting the authoritative production code and operational procedure.

## User-facing risks

| Risk | Current ambiguity | Required correction |
|---|---|---|
| Free scope | “runs once” can sound like one-time free access | State that the free version stays free; describe one backlog as the recommended first test, not an access limit |
| Payment confirmation | Server-side verification and manual Desk review are both asserted | Describe only the observable order-state boundary until the implementation is verified |
| Access grant | Email, backup form, server order, and manual review appear in the same flow | State that only `ACTIVE` in the server order grants access |
| Duplicate payment | A user may retry while waiting | Retain the explicit no-second-payment warning |

## Minimal replacement copy

These replacements preserve the existing price, network, 30-day term, no-refund
policy, free/paid separation, and user-managed setup. They deliberately avoid
claiming whether verification is automated or manual.

### Free page: transition to monthly

English:

> Free Switchboard stays free and uses no key. Start with one real backlog to see
> whether the job is useful. The optional monthly Switchboard is a separate
> 20 USDT / 30-day rental for the same job behind an active key. Payment is never
> required for the free version.

Japanese:

> 無料Switchboardは無料のままで、鍵は使いません。まず一つの実案件で、この仕事が役立つか確認してください。月額Switchboardは同じ仕事を有効な鍵で使う別商品です。20 USDTで30日間。無料版に支払いは不要です。

Remove the phrases that say the free version proves the job “runs once” or that
“無料は一回動くことの確認.” One real backlog remains the validation method, not
an access limit.

### Paid page: after payment

English:

> Create the server order, send the exact 20 USDT on TRON / TRC20, and submit the
> txid once. Access begins only when the order status is `ACTIVE`. My purchases
> then shows the 30-day expiry and key. A backup notice or email does not grant
> access. If the status is still pending, do not pay or submit the same txid again.

Japanese:

> サーバー注文を作成し、TRON / TRC20で20 USDTちょうどを送金して、txidを一度だけ提出してください。注文状態が`ACTIVE`になった時点でアクセス開始です。My purchasesに30日間の期限と鍵が表示されます。控え通知やメールだけではアクセスは付与されません。保留中でも、再送金や同じtxidの再提出はしないでください。

### Checkout: confirmation mechanism

English:

> The server order is the authoritative access record. After txid submission,
> wait for `SUBMITTED` → `VERIFYING` → `ACTIVE`. Access is not granted until
> `ACTIVE`. The optional Netlify form is a backup notice only. Do not pay twice.

Japanese:

> アクセスの正式記録はサーバー注文です。txid提出後は`SUBMITTED` →
> `VERIFYING` → `ACTIVE`の順に確認してください。`ACTIVE`になるまでアクセスは
> 付与されません。Netlifyフォームは任意の控え通知のみです。二度払わないでください。

Remove both implementation claims — “Chain verify is server-side” and “Desk
checks by hand — not automatic” — until the production source and operating path
show which is true. The state transition and grant boundary can remain because
they are already presented consistently across the product and checkout pages.

## Source handoff required

Before editing, record privately:

1. authoritative production source location and revision;
2. relationship to deploy `6ab49003e165d1d40fdd9ada`;
3. a restorable backup or rollback procedure;
4. code path that creates orders and changes payment status;
5. whether any human decision is required before `ACTIVE`;
6. code path that exposes the key and 30-day expiry;
7. whether email and the Netlify form are notifications only.

Do not assume `BotShelfVampire/botshelf` is the production source. Do not copy raw
orders, txids, email addresses, wallet data, keys, or customer records into GitHub.

## Patch acceptance checks

After the authoritative source is identified and a preview-only patch exists:

- all three pages use the same `ACTIVE` access boundary;
- no page claims manual or automatic verification without matching code evidence;
- the free page says free stays free and never asks for payment;
- one real backlog is described as a first validation job, not a usage limit;
- 20 USDT, TRON / TRC20, rolling 30 days, no card, no refund, and user-managed
  setup remain unchanged;
- the optional backup form cannot be mistaken for an access grant;
- duplicate txid submission and second payment remain explicitly discouraged;
- English and Japanese describe the same behavior;
- preview links and exact changed files are reviewed before any deployment.

Status stays `BLOCKED` for implementation and `REVIEW` for this copy package until
the production-source handoff is received. No production deployment is requested.
