# Registration-to-first-use reconciliation

Status: **REVIEW — copy and behavior specification only; production source required**  
Task: **BSV acquisition / first real use**  
Public pages and Netlify form counts checked: **2026-09-30 JST**

This document reconciles the current email-registration promise with the publicly reachable free Switchboard. It does not classify the behavior as a vulnerability, change production, submit a form, create an account, contact a user, or claim a verified registration or product use.

## Observed funnel evidence

### Aggregate form state

The authorized Netlify read returned:

- `register`: 5 submissions; last submission 2026-09-11;
- `txid`: 2 submissions; last submission 2026-09-11;
- `contact`: 1 submission; last submission 2026-09-26.

There is no increase from the previously audited counts. Existing evidence classifies one register entry as explicit QC, both txid entries as QC dry runs, and the contact entry as vendor solicitation. The four other register records have not been proven to be genuine customers, verified email owners, or product users. Visitor count and registration conversion rate remain unknown.

### Public promise

Source: <https://botshelfvampire.com/register.html>

The registration page says:

- a six-digit code is emailed;
- free teams unlock only after entering that code;
- the same page directly links to the free Switchboard.

Source: <https://botshelfvampire.com/switchboard-cos.html>

The free Switchboard page is publicly readable without a registration action in the observed session. It exposes the stated deliverable, approval boundary, setup location, blanks, and copyable body. The page footer also says the free body unlocks after email registration.

Bobby separately reported that `/registered.html` exposes free content. That route could not be independently read through the available public reader, so its exact contents remain unverified here.

## Diagnosis

The current funnel presents two incompatible behaviors:

1. registration is described as mandatory to unlock free teams;
2. the free Switchboard body is publicly reachable from the registration page without evidence of code entry.

This is a trust and measurement problem, regardless of whether public access is intentional:

- a user may register for an unlock that was not required;
- a user may skip registration and use the free body, so form counts cannot measure first use;
- a form submission does not prove that the email code was entered;
- a code entry does not prove that Switchboard was set up or used;
- gating the already-public body later would add friction before the first real job.

Do not call the direct access a security issue until the product owner and authoritative source establish the intended access model.

## Recommended product decision

Use **free-first, evidence-backed optional registration** for the first experiment:

- keep the free Switchboard free and directly usable without payment or a key;
- stop claiming that registration unlocks a different free body;
- invite registration after the user understands the job, using a truthful reason;
- keep registration separate from marketing consent;
- measure registration, code confirmation, setup, accepted first use, later-day return, and payment as separate stages.

This decision prioritizes the first proven job over collecting low-intent form rows. It does not remove the registration form or change paid terms.

## Minimum replacement copy

Use only after the production source and actual code-confirmation behavior are verified in a preview.

### Register page introduction

English:

> Try the free Switchboard without payment or a key. Registration records your buyer or seller role and the AI tools you use. If the six-digit email code is active in the reviewed implementation, enter it to complete registration. Registration does not subscribe you to marketing and does not prove that Switchboard was used.

Japanese:

> 無料Switchboardは、支払いや鍵なしで試せます。登録では、買い手・売り手の区分と利用中のAIツールを記録します。レビュー済み実装で6桁メールコードが有効な場合は、コード入力で登録を完了します。登録だけでマーケティング配信には同意されず、Switchboardの利用完了にもなりません。

Remove every statement that says free teams unlock only after registration unless a tested access check actually prevents anonymous access.

### Free Switchboard: next action after the body

English:

> Use one real backlog first. If the next action is useful and you want to record interest in future access or seller tools, register separately. Registration is optional for this free body and is not marketing consent.

Japanese:

> まず一つの実案件で試してください。次の一手が役立ち、今後のアクセス案内や出品機能に関心がある場合だけ、別途登録してください。この無料本文の利用に登録は必須ではなく、登録はマーケティング配信への同意でもありません。

Do not promise saved history, account persistence, product updates, access notices, or email ownership verification unless each behavior is present and tested.

## Alternative if registration is intentionally mandatory

If the owner instead confirms that registration must gate every free body, a copy-only change is insufficient. The implementation must:

1. prevent anonymous access to the body at every canonical and alternate route;
2. require a server-validated, short-lived confirmation state rather than a client-only redirect;
3. define expiry, replay, duplicate-email, and failure behavior;
4. avoid exposing secrets or private customer data in URLs or static HTML;
5. retain a no-payment free path;
6. pass preview tests for direct URLs, refresh, back navigation, alternate paths, and failed/expired codes;
7. provide an accessible recovery path without silently subscribing the user to marketing.

This route requires the authoritative production source and security review. It must not be implemented in the public evidence repository.

## Preview acceptance checks

Before any production change:

- confirm whether the six-digit code is actually sent and server-validated;
- confirm whether `/registered.html`, `/switchboard-cos.html`, redirects, and alternate paths expose the same body;
- select one explicit access model and make all English/Japanese copy match it;
- preserve free access and existing paid price/terms;
- do not create a production test registration;
- verify that no form submission is labeled email-confirmed without a successful code-validation event;
- verify that registration success never counts as setup or first use;
- verify that first use requires a real runtime result and participant acceptance;
- review a preview URL and rollback procedure before deployment.

## Measurement after an approved implementation

Report aggregate stages separately:

1. form opened — only if an authoritative event exists;
2. form submitted;
3. email code confirmed — only if server evidence exists;
4. Switchboard setup reached;
5. first real job accepted;
6. later-day accepted reuse;
7. server-confirmed payment.

Do not calculate a registration rate without an authoritative visitor or form-open denominator. Do not infer first use from page access, registration, or code confirmation.

## Current decision

- Aggregate form change: **NONE OBSERVED**
- Genuine new email registrations: **UNKNOWN**
- Email ownership confirmations: **UNKNOWN**
- First real uses: **UNKNOWN**
- Public free body access: **OBSERVED**
- Intended access model: **UNKNOWN**
- Copy/behavior reconciliation: **REVIEW**
- Production patch/deploy: **BLOCKED — authoritative source, preview, rollback, and explicit approval required**
