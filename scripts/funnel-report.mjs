#!/usr/bin/env node
/** Aggregate-only, offline funnel report. No network, tracking or payments. */
import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const COVERAGE = ['registrations', 'runs', 'payments'];
const KINDS = ['registration', 'run_completed', 'payment_submitted', 'payment_verified'];
const COMMON = ['event_id', 'kind', 'at', 'actor_id', 'actor_kind', 'environment'];
const EXTRA = {
  registration: [],
  run_completed: ['run_id', 'execution_kind', 'accepted', 'evidence_ref'],
  payment_submitted: ['order_id'],
  payment_verified: ['order_id', 'amount', 'currency', 'verification_source', 'evidence_ref'],
};
const ensure = (condition, message) => { if (!condition) throw new Error(message); };
const plain = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const opaque = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value);
const canonical = value => JSON.stringify(value, Object.keys(value).sort());

function keys(value, allowed, label) {
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

export function buildReport(input) {
  keys(input, ['schema_version', 'window', 'coverage', 'events'], 'snapshot');
  ensure(input.schema_version === 1, 'Unsupported schema_version');
  keys(input.window, ['start', 'end', 'timezone'], 'window');
  const start = utc(input.window.start), end = utc(input.window.end);
  ensure(start < end, 'Window must be nonempty');
  ensure(typeof input.window.timezone === 'string', 'Timezone required');
  const dayFormat = new Intl.DateTimeFormat('en-CA', { timeZone: input.window.timezone, year: 'numeric', month: '2-digit', day: '2-digit' });
  keys(input.coverage, COVERAGE, 'coverage');
  for (const key of COVERAGE) ensure(['complete', 'partial', 'missing'].includes(input.coverage[key]), 'Declare every coverage source');
  ensure(Array.isArray(input.events), 'events must be an array');

  const seen = new Map(), actors = new Map(), orders = new Map(), runs = new Map();
  const registered = new Set(), payers = new Set(), runDays = new Map(), amounts = new Map();
  const excluded = { noncustomer_or_test: 0, unverified_or_unaccepted: 0, outside_window: 0, duplicate_events: 0, duplicate_business_records: 0 };
  for (const e of input.events) {
    ensure(plain(e) && KINDS.includes(e.kind), 'Unsupported event kind');
    keys(e, [...COMMON, ...EXTRA[e.kind]], 'event');
    ensure(opaque(e.event_id) && opaque(e.actor_id), 'Use opaque event and actor IDs; no email addresses');
    const at = utc(e.at);
    ensure(['customer', 'test', 'internal', 'unknown', 'vendor'].includes(e.actor_kind), 'Explicit actor classification required');
    ensure(['production', 'test'].includes(e.environment), 'Explicit environment required');
    ensure(!actors.has(e.actor_id) || actors.get(e.actor_id) === e.actor_kind, 'Conflicting actor classification');
    actors.set(e.actor_id, e.actor_kind);
    const fingerprint = canonical(e);
    if (seen.has(e.event_id)) {
      ensure(seen.get(e.event_id) === fingerprint, 'Conflicting duplicate event');
      excluded.duplicate_events++; continue;
    }
    seen.set(e.event_id, fingerprint);
    if (at < start || at >= end) { excluded.outside_window++; continue; }
    if (e.environment !== 'production' || e.actor_kind !== 'customer') { excluded.noncustomer_or_test++; continue; }
    if (e.kind === 'registration') { registered.add(e.actor_id); continue; }
    if (e.kind === 'payment_submitted') { excluded.unverified_or_unaccepted++; continue; }
    if (e.kind === 'run_completed') {
      ensure(opaque(e.run_id), 'run_id required');
      ensure(['runtime', 'structural', 'sample'].includes(e.execution_kind) && typeof e.accepted === 'boolean', 'Explicit run classification required');
      if (e.execution_kind !== 'runtime' || !e.accepted) { excluded.unverified_or_unaccepted++; continue; }
      ensure(opaque(e.evidence_ref), 'Accepted runtime run requires opaque evidence reference');
      const signature = e.actor_id;
      if (runs.has(e.run_id)) {
        ensure(runs.get(e.run_id) === signature, 'Conflicting duplicate run');
        excluded.duplicate_business_records++; continue;
      }
      runs.set(e.run_id, signature);
      if (!runDays.has(e.actor_id)) runDays.set(e.actor_id, new Set());
      runDays.get(e.actor_id).add(dayFormat.format(new Date(at)));
      continue;
    }
    ensure(opaque(e.order_id) && opaque(e.evidence_ref), 'Verified payment requires order ID and evidence reference');
    ensure(e.verification_source === 'server_ledger', 'Payment requires authoritative server-ledger provenance');
    ensure(typeof e.currency === 'string' && /^[A-Z]{3,8}$/.test(e.currency), 'Explicit currency required');
    const amount = micros(e.amount);
    const signature = `${e.actor_id}|${e.currency}|${amount}`;
    if (orders.has(e.order_id)) {
      ensure(orders.get(e.order_id) === signature, 'Conflicting duplicate order');
      excluded.duplicate_business_records++; continue;
    }
    orders.set(e.order_id, signature); payers.add(e.actor_id);
    amounts.set(e.currency, (amounts.get(e.currency) || 0n) + amount);
  }
  const observed = {
    registered_users: registered.size,
    users_with_accepted_runs: runDays.size,
    users_with_runs_on_multiple_days: [...runDays.values()].filter(days => days.size >= 2).length,
    accepted_runs: runs.size,
    verified_orders: orders.size,
    paying_users: payers.size,
    gross_collected_by_currency: Object.fromEntries([...amounts].sort().map(([c, n]) => [c, decimal(n)])),
  };
  const source = { registered_users: 'registrations', users_with_accepted_runs: 'runs', users_with_runs_on_multiple_days: 'runs', accepted_runs: 'runs', verified_orders: 'payments', paying_users: 'payments', gross_collected_by_currency: 'payments' };
  for (const [metric, value] of Object.entries(observed)) {
    if (input.coverage[source[metric]] === 'missing') ensure(plain(value) ? Object.keys(value).length === 0 : value === 0, 'Missing source conflicts with eligible observations');
  }
  return {
    schema_version: 1,
    window: { ...input.window },
    coverage: { ...input.coverage },
    observed,
    totals: Object.fromEntries(Object.entries(observed).map(([key, value]) => [key, input.coverage[source[key]] === 'complete' ? value : null])),
    excluded,
    limitations: ['Input provenance and coverage are caller assertions, not independently verified.', 'Runs are period activity, not first-ever activation or cohort retention.', 'Gross collected is not net revenue, profit, MRR or seller-adjusted revenue.', 'No customer IDs or evidence contents are returned. Keep input and output private.'],
  };
}

const main = process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (main) {
  try {
    ensure(process.argv.length === 3, 'Usage: node scripts/funnel-report.mjs /private/snapshot.json');
    const raw = readFileSync(process.argv[2], 'utf8');
    ensure(Buffer.byteLength(raw, 'utf8') <= 8 * 1024 * 1024, 'Snapshot exceeds 8 MiB');
    console.log(JSON.stringify(buildReport(JSON.parse(raw)), null, 2));
  } catch {
    // Do not echo raw input, paths, JSON parser excerpts, IDs or private values.
    console.error('Invalid snapshot. Check schema, coverage, timestamps, duplicates and provenance using docs/funnel-report.md. No report produced.');
    process.exitCode = 1;
  }
}
