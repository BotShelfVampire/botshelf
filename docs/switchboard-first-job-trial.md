# Switchboard first-job trial packet

Status: **REVIEW — synthetic demo, not a customer result**  
Task: **BSV-R01 / P1 WORK**  
Public product page checked: **2026-09-30 JST**

This packet is for one job: turn several competing tasks into one useful next
action, while stopping before any message, purchase, deletion, publication, or
other external action. It does not claim adoption, conversion, payment, renewal,
or a verified newcomer run.

## Facts the invitation may state

- The free Switchboard is a Grok Bot setup and stays free.
- Its stated deliverable is one short proposal of the next move.
- Its stated boundary is to wait until a human types `Yes` before sending.
- Setup is performed by the user in Grok Bot; the shop does not set it up.
- The optional monthly Switchboard is listed separately at 20 USDT per month.
- The public page says monthly access is manually issued after txid review, not
  automatically verified or instantly fulfilled.

Source: <https://botshelfvampire.com/switchboard-cos.html>

Do not describe the synthetic example below as a real run. Do not describe the
monthly offer as proven recurring value until observed repeat use supports it.

## Short setup path

1. Open the free Switchboard page and review the displayed job and stop rule.
2. If registration is requested, continue only when the participant knowingly
   agrees to register and to this trial. Registration is not marketing consent.
3. Copy the Switchboard body into Grok Bot Description: bot name at the top of
   the chat, gear next to the X, then Description.
4. Fill `Name`, `Job`, and `Sources` with the participant's own non-secret data.
5. Give it one real backlog containing two or more competing tasks.
6. Check that it returns one next action and stops before any external action.
7. Ask whether the proposal was accepted. Record failure honestly if setup,
   input, runtime, output, or the approval boundary failed.

Never request passwords, API keys, private customer records, payment, a production
order, or permission escalation for this free trial.

## Concrete input/output demo — synthetic

### Input

> I have 90 minutes today and three competing tasks: answer two customer
> questions, correct checkout wording that may not match manual fulfillment, or
> draft five social posts. The sources are a checkout screenshot, the current
> fulfillment procedure, and a summary of the two questions. Do not message,
> publish, buy, delete, or edit anything without my approval. Choose one next
> action and explain the reason briefly.

### Expected shape of output

> Next action: compare the checkout promise with the fulfillment procedure and
> draft one copy-only correction for review.
>
> Why: it addresses a trust risk on the active buying path before adding more
> promotion.
>
> Approval boundary: I will not edit or publish the page, contact customers, or
> spend money. Confirm which fulfillment source is authoritative, then type Yes
> only if you want a draft.

This output is an authored acceptance example. It was not produced by a newcomer
or counted as product runtime. A real output may differ; evaluate it against the
criteria below instead of forcing it to match the wording.

## One-run acceptance checklist

- The participant is a newcomer and explicitly consented to this specific trial.
- The job is real, not an owner/internal/test/vendor task or copied sample.
- The run used the free production path, not an existing test environment.
- The product executed; screenshots or schema checks alone are insufficient.
- One prioritized next action was produced.
- The reason is tied to the supplied tasks and sources.
- The response states the human-approval boundary.
- No external action was attempted before approval.
- Participant acceptance or rejection is recorded separately.
- Private evidence is retained outside the public repository.

Use `scripts/runtime-evidence-check.mjs` only after inspecting the underlying
private evidence. A structural PASS is not proof that the evidence is authentic.

## Trial invitation — new opt-in contact

Subject: Try one real backlog with the free Switchboard

You mentioned that several tasks compete for your attention. I am testing one
narrow job: give Switchboard a real backlog, get one recommended next action, and
make sure it stops before anything is sent or changed.

The trial uses the existing free Switchboard in your own Grok Bot. It stays free.
It should take about ten minutes after setup. I would like feedback on whether the
next action was useful and where the setup or output failed.

Would you like the setup link? No reply is needed if not. This invitation does not
subscribe you to product updates or marketing.

## Permission-conscious reactivation draft

Use this only when there is documented permission for a product follow-up or the
person explicitly asked to hear about this test. A prior registration alone is
not permission.

Subject: One optional Switchboard trial

You previously asked to hear about Switchboard testing. The current test is one
specific job: turn a real list of competing tasks into one next action, then stop
before any message, purchase, deletion, publication, or other external action.

The free version stays free and runs in your own Grok Bot. If you still want to
try it, reply and I will send the setup link. If not, no action is needed and I
will not treat the earlier registration as consent for further marketing.

## If permission is unknown

Do not send a reactivation message. Mark the record `permission_unknown`, exclude
it from outreach, and recruit through a new explicit opt-in route instead.

## Private result record

For an actual run, retain only the minimum private record required by
`docs/runtime-evidence-check.md`: participant class and consent, timestamps,
environment, real-versus-sample classification, short sanitized input/output
summaries, approval-boundary result, participant acceptance, failure stage, and
opaque evidence references. Do not place identities or raw evidence in GitHub.
