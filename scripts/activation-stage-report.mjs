#!/usr/bin/env node
/** Private, aggregate-only activation-stage report. No network or production writes. */
import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const COVERAGE = ['activations', 'runs', 'payments'];
const KINDS = ['activation_accepted', 'run_accepted', 'payment_submitted', 'payment_verified'];
const COMMON = ['event_id', 'kind', 'at', 'actor_id', 'actor_kind', 'environment'];
const EXTRA = {
  activation_accepted: ['activation_id', 'evidence_gate', 'accepted_by_participant', 'evidence_ref'],
  run_accepted: ['run_id', 'execution_kind', 'accepted', 'evidence_ref'],
  payment_submitted: ['order_id'],
  payment_verified: ['order_id', 'amount', 'currency', 'verification_source', 'evidence_ref'],
};
const ensure = (condition, message) => { if (!condition) throw new Error(message); };
const plain = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const opaque = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value);
const canonical = value => JSON.stringify(value, Object.keys(value).sort());

function strictKeys(value, allowed, label) {
  ensure(plain(value), `${label}: expected object`);
  ensure(Object.keys(value).every(key => allowed.includes(key)), `${label}: unsupported field`);
}
function utc(value) {
  ensure(typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(value), 'Expected UTC ISO timestamp');
  const time = Date.parse(value);
  ensure(Number.isFinite(time), 'Invalid timestamp');
  ensure(new Date(time).toISOString() === value.replace(/(?<!\.\d{3})Z$/, '.000Z'), 'Invalid calendar date');
  return time;
}
function micros(value) {
  ensure(typeof value === 'string' && /^(0|[1-9]\d*)(\.\d{1,6})?$/.test(value), 'Amount must be a nonnegative decimal string, up to 6 places');
  const [whole, fraction = ''] = value.split('.');
  const result = BigInt(whole) * 1000000n + BigInt(fraction.padEnd(6, '0'));
  ensure(result > 0n, 'Payment amount must be positive');
  return result;
}
const decimal = value => `${value / 1000000n}.${(value % 1000000n).toString().padStart(6, '0')}`.replace(/\.?0+$/, '');
const complete = (coverage, ...sources) => sources.every(source => coverage[source] === 'complete');

export function buildActivationStageReport(input) {
  strictKeys(input, ['schema_version', 'window', 'coverage', 'events'], 'snapshot');
  ensure(input.schema_version === 1, 'Unsupported schema_version');
  strictKeys(input.window, ['start', 'end', 'timezone'], 'window');
  const start = utc(input.window.start), end = utc(input.window.end);
  ensure(start < end, 'Window must be nonempty');
  ensure(typeof input.window.timezone === 'string', 'Timezone required');
  const day = new Intl.DateTimeFormat('en-CA', { timeZone: input.window.timezone, year: 'numeric', month: '2-digit', day: '2-digit' });
  strictKeys(input.coverage, COVERAGE, 'coverage');
  for (const source of COVERAGE) ensure(['complete', 'partial', 'missing'].includes(input.coverage[source]), 'Declare every coverage source');
  ensure(Array.isArray(input.events), 'events must be an array');

  const seenEvents = new Map(), actorKinds = new Map(), activationIds = new Map(), runIds = new Map(), orderIds = new Map();
  const activations = new Map(), runTimes = new Map(), payments = new Map(), amounts = new Map();
  const eligibleBySource = { activations: 0, runs: 0, payments: 0 };
  const excluded = {
    noncustomer_or_test: 0,
    unverified_or_unaccepted: 0,
    outside_window: 0,
    duplicate_events: 0,
    duplicate_business_records: 0,
    before_or_same_day_as_activation: 0,
  };

  for (const event of input.events) {
    ensure(plain(event) && KINDS.includes(event.kind), 'Unsupported event kind');
    strictKeys(event, [...COMMON, ...EXTRA[event.kind]], 'event');
    ensure(opaque(event.event_id) && opaque(event.actor_id), 'Use opaque event and actor IDs; no email addresses');
    const at = utc(event.at);
    ensure(['customer', 'test', 'internal', 'unknown', 'vendor'].includes(event.actor_kind), 'Explicit actor classification required');
    ensure(['production', 'test'].includes(event.environment), 'Explicit environment required');
    ensure(!actorKinds.has(event.actor_id) || actorKinds.get(event.actor_id) === event.actor_kind, 'Conflicting actor classification');
    actorKinds.set(event.actor_id, event.actor_kind);
    const fingerprint = canonical(event);
    if (seenEvents.has(event.event_id)) {
      ensure(seenEvents.get(event.event_id) === fingerprint, 'Conflicting duplicate event');
      excluded.duplicate_events++;
      continue;
    }
    seenEvents.set(event.event_id, fingerprint);
    if (at < start || at >= end) { excluded.outside_window++; continue; }
    if (event.environment !== 'production' || event.actor_kind !== 'customer') { excluded.noncustomer_or_test++; continue; }

    if (event.kind === 'payment_submitted') { excluded.unverified_or_unaccepted++; continue; }
    if (event.kind === 'activation_accepted') {
      ensure(opaque(event.activation_id), 'activation_id required');
      if (event.evidence_gate !== 'PASS' || event.accepted_by_participant !== true) { excluded.unverified_or_unaccepted++; continue; }
      ensure(opaque(event.evidence_ref), 'Accepted activation requires opaque evidence reference');
      const signature = event.actor_id;
      if (activationIds.has(event.activation_id)) {
        ensure(activationIds.get(event.activation_id) === signature, 'Conflicting duplicate activation');
        excluded.duplicate_business_records++; continue;
      }
      activationIds.set(event.activation_id, signature);
      eligibleBySource.activations++;
      if (!activations.has(event.actor_id) || at < activations.get(event.actor_id)) activations.set(event.actor_id, at);
      continue;
    }
    if (event.kind === 'run_accepted') {
      ensure(opaque(event.run_id), 'run_id required');
      if (event.execution_kind !== 'runtime' || event.accepted !== true) { excluded.unverified_or_unaccepted++; continue; }
      ensure(opaque(event.evidence_ref), 'Accepted runtime run requires opaque evidence reference');
      const signature = event.actor_id;
      if (runIds.has(event.run_id)) {
        ensure(runIds.get(event.run_id) === signature, 'Conflicting duplicate run');
        excluded.duplicate_business_records++; continue;
      }
      runIds.set(event.run_id, signature);
      eligibleBySource.runs++;
      if (!runTimes.has(event.actor_id)) runTimes.set(event.actor_id, []);
      runTimes.get(event.actor_id).push(at);
      continue;
    }
    ensure(opaque(event.order_id) && opaque(event.evidence_ref), 'Verified payment requires order ID and evidence reference');
    ensure(event.verification_source === 'server_ledger', 'Payment requires authoritative server-ledger provenance');
    ensure(typeof event.currency === 'string' && /^[A-Z]{3,8}$/.test(event.currency), 'Explicit currency required');
    const amount = micros(event.amount);
    const signature = `${event.actor_id}|${event.currency}|${amount}`;
    if (orderIds.has(event.order_id)) {
      ensure(orderIds.get(event.order_id) === signature, 'Conflicting duplicate order');
      excluded.duplicate_business_records++; continue;
    }
    orderIds.set(event.order_id, signature);
    eligibleBySource.payments++;
    if (!payments.has(event.actor_id)) payments.set(event.actor_id, []);
    payments.get(event.actor_id).push({ at, currency: event.currency, amount });
  }

  for (const source of COVERAGE) {
    if (input.coverage[source] === 'missing') ensure(eligibleBySource[source] === 0, 'Missing source conflicts with eligible observations');
  }

  const activated = new Set(activations.keys()), returned = new Set(), paid = new Set();
  let verifiedOrders = 0;
  for (const [actor, activationAt] of activations) {
    const activationDay = day.format(new Date(activationAt));
    for (const runAt of runTimes.get(actor) || []) {
      if (runAt > activationAt && day.format(new Date(runAt)) > activationDay) returned.add(actor);
      else excluded.before_or_same_day_as_activation++;
    }
    for (const payment of payments.get(actor) || []) {
      if (payment.at < activationAt) { excluded.before_or_same_day_as_activation++; continue; }
      paid.add(actor); verifiedOrders++;
      const key = payment.currency;
      amounts.set(key, (amounts.get(key) || 0n) + payment.amount);
    }
  }
  const both = [...activated].filter(actor => returned.has(actor) && paid.has(actor)).length;
  const observed = {
    eligible_activated_users: activated.size,
    activated_users_returning_on_later_day: returned.size,
    activated_users_with_verified_payment: paid.size,
    activated_users_returning_and_paying: both,
    verified_orders_by_activated_users: verifiedOrders,
    gross_collected_from_activated_users_by_currency: Object.fromEntries([...amounts].sort().map(([currency, amount]) => [currency, decimal(amount)])),
  };
  const requirements = {
    eligible_activated_users: ['activations'],
    activated_users_returning_on_later_day: ['activations', 'runs'],
    activated_users_with_verified_payment: ['activations', 'payments'],
    activated_users_returning_and_paying: ['activations', 'runs', 'payments'],
    verified_orders_by_activated_users: ['activations', 'payments'],
    gross_collected_from_activated_users_by_currency: ['activations', 'payments'],
  };
  return {
    schema_version: 1,
    window: { ...input.window },
    coverage: { ...input.coverage },
    observed,
    totals: Object.fromEntries(Object.entries(observed).map(([metric, value]) => [metric, complete(input.coverage, ...requirements[metric]) ? value : null])),
    excluded,
    limitations: [
      'Input provenance and source coverage are caller assertions, not independently verified.',
      'Activation requires a PASS evidence gate and explicit participant acceptance; this report does not inspect private evidence contents.',
      'Return use requires an accepted runtime run on a later local calendar day than first accepted activation.',
      'Payment requires authoritative server-ledger verification; a submitted transaction ID is never payment proof.',
      'Gross collected is not net revenue, profit, MRR, renewal or seller-adjusted revenue.',
      'No actor, activation, run, order or evidence identifiers are returned. Keep input and output private.',
    ],
  };
}

const main = process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (main) {
  try {
    ensure(process.argv.length === 3, 'Usage: node scripts/activation-stage-report.mjs /private/snapshot.json');
    const raw = readFileSync(process.argv[2], 'utf8');
    ensure(Buffer.byteLength(raw, 'utf8') <= 8 * 1024 * 1024, 'Snapshot exceeds 8 MiB');
    console.log(JSON.stringify(buildActivationStageReport(JSON.parse(raw)), null, 2));
  } catch {
    console.error('Invalid snapshot. Check schema, coverage, timestamps, duplicates and provenance using docs/activation-stage-report.md. No report produced.');
    process.exitCode = 1;
  }
}
