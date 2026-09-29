# Switchboard paid-value audit

Status: **REVIEW — public evidence only; production source and runtime evidence required**  
Task: **BSV-R01 / P1 WORK**  
Public pages checked: **2026-09-30 JST**

This audit asks one narrow question: what recurring value, beyond access expiry, is actually supported for the existing 20 USDT / 30-day Switchboard? It does not change the price, invent features, claim a sale, or authorize payment, outreach, merge, or deployment.

## Confirmed public facts

Sources:

- <https://botshelfvampire.com/paid-switchboard.html>
- <https://botshelfvampire.com/switchboard-cos.html>

| Area | Confirmed statement | Evidence boundary |
|---|---|---|
| Core job | Switchboard sorts supplied information into one short next-action proposal and stops before sending | Described on both free and monthly pages; no newcomer runtime evidence yet |
| Free offer | Free Switchboard stays free and uses no key | Public copy only |
| Monthly offer | 20 USDT buys rolling 30-day access over TRON / TRC20 | Public copy only; no confirmed production payment supplied |
| Monthly implementation shape | A short paste/client is downloadable; the protected job body remains server-side and requires active access | Public description; authoritative production code not supplied |
| Access boundary | Public flow shows `SUBMITTED` → `VERIFYING` → `ACTIVE`; key and expiry appear after `ACTIVE` | Public description; actual state transition and fulfillment mechanism unverified |
| Setup | The buyer uses an existing Grok Bot, Claude Code, or ChatGPT and performs setup | Public description; no setup service promised |
| Stated recurring rationale | One window for repeated work, avoiding several chats for the same job | Positioning claim, not measured repeat value |

## What the current evidence does not support

Do not claim any of the following until the authoritative implementation or real accepted runtime evidence establishes it:

- better output quality than the free Switchboard;
- saved history, cross-session memory, synchronization, automation, integrations, monitoring, team collaboration, priority support, SLA, or setup service;
- faster payment confirmation or automatic fulfillment;
- unlimited usage, a specific usage quota, model/API costs, or guaranteed availability;
- customer adoption, repeat use, conversion, renewal, time saved, or willingness to pay;
- that the key or 30-day expiry is itself recurring customer value.

## Current value conclusion

The only defensible paid-value hypothesis is:

> A user who repeatedly performs the same prioritization job may prefer one keyed, server-backed Switchboard window over recreating or managing the free setup.

This is a hypothesis, not a proven benefit. The public pages describe the free and paid products as the same job. Until production code shows a meaningful protected implementation difference, or real users demonstrate repeat value, the monthly offer must not be marketed as functionally superior to free.

## Evidence required before a paid-value claim

| Claim gate | Required private evidence | Accept when | Reject or keep unknown when |
|---|---|---|---|
| Protected implementation | Authoritative production source and revision for the thin client, protected job body, key check, and expiry | Source relationship to current deploy is proved and reviewed | Public docs repository, screenshots, or unlinked code only |
| Recurring use | Accepted runtime events from the same consented customer on distinct JST days | Real job, production path, evidence gate PASS, participant accepted | Same-day repeats, samples, QC, internal/vendor activity, structural checks |
| Paid access | Server-ledger-confirmed order tied privately to the activated customer | Order is authoritative, deduplicated, and `ACTIVE` after confirmation | txid submission, browser claim, backup form, test order, production test payment |
| Incremental value | Sanitized comparison of free and paid outcomes or workflow burden | User identifies a specific repeated benefit attributable to paid implementation | Access expiry alone, seller-authored promise, or unmeasured convenience |
| Renewal | A second independently confirmed paid term after continued use | Renewal payment and continued accepted use are separately evidenced | Early renewal promise, access extension test, or first payment only |

## First paid-value interview after a real free run

Ask only after the participant has completed and accepted one real free job. Do not pitch payment first.

1. Would you use this same prioritization job again within seven days? Why?
2. What part of setup or reuse would make you stop using it?
3. Did one window reduce repeated context setup, or was the free version already enough?
4. What specific recurring capability would justify 20 USDT for 30 days?
5. Would you choose the monthly version today? Record `yes`, `no`, or `uncertain` without persuasion.

The answer is research evidence, not payment evidence. Do not infer willingness to pay from praise, registration, link clicks, or completion of the free run.

## Decision rule for the first experiment

- Keep the free version free regardless of the result.
- Do not change the existing 20 USDT / 30-day price in this task.
- Do not send a production payment or create a production test order.
- Do not increase traffic based on page views or registrations alone.
- Continue the paid hypothesis only when at least one real newcomer accepts the free result, later returns for the same job, and states a specific paid recurring benefit.
- Count a paying customer only after authoritative server-ledger confirmation; count renewal separately.
- If users return but the free version is sufficient, improve or change the paid value proposition instead of presenting key expiry as value.

## Source handoff questions

BSV-R01-C must answer these from the authoritative production source before paid copy is strengthened:

1. What exactly differs between the free body and protected monthly job body?
2. What does the thin client send, store, and receive?
3. How are keys checked, expired, renewed, and revoked?
4. Which system changes an order to `ACTIVE`, and is human review involved?
5. What usage or runtime evidence exists without exposing customer identities or secrets?
6. What behavior remains available after expiry?

Until these are answered, status remains `REVIEW`; recurring value, production payments, active licenses, use, return use, and renewal remain unknown.
