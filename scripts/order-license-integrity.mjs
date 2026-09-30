#!/usr/bin/env node
/** Offline, aggregate-only paid-order/license integrity check. No network or writes. */
import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const COVERAGE = ['orders', 'payments', 'licenses'];
const ORDER_KEYS = ['order_id', 'product_code', 'expected_amount', 'currency', 'status', 'requires_license'];
const PAYMENT_KEYS = ['payment_id', 'order_id', 'amount', 'currency', 'verification_source', 'evidence_ref'];
const LICENSE_KEYS = ['license_id', 'order_id', 'product_code', 'state', 'starts_at', 'expires_at', 'evidence_ref'];
const ensure = (condition, message) => { if (!condition) throw new Error(message); };
const plain = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const opaque = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value);
const canonical = value => JSON.stringify(value, Object.keys(value).sort());

function strict(value, allowed, label) {
  ensure(plain(value), `${label}: expected object`);
  ensure(Object.keys(value).every(key => allowed.includes(key)), `${label}: unsupported field`);
  ensure(allowed.every(key => Object.hasOwn(value, key)), `${label}: missing field`);
}
function amount(value) {
  ensure(typeof value === 'string' && /^(0|[1-9]\d*)(\.\d{1,6})?$/.test(value), 'Amount must be a decimal string with up to 6 places');
  const [whole, fraction = ''] = value.split('.');
  const result = BigInt(whole) * 1000000n + BigInt(fraction.padEnd(6, '0'));
  ensure(result > 0n, 'Amount must be positive');
  return result;
}
function utc(value) {
  ensure(typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(value), 'Expected UTC timestamp');
  const time = Date.parse(value);
  ensure(Number.isFinite(time), 'Invalid timestamp');
  return time;
}
function addUnique(map, id, value, label, excluded) {
  ensure(opaque(id), `${label}: opaque ID required`);
  const fingerprint = canonical(value);
  if (map.has(id)) {
    ensure(map.get(id).fingerprint === fingerprint, `${label}: conflicting duplicate ID`);
    excluded.exact_duplicates++;
    return false;
  }
  map.set(id, { value, fingerprint });
  return true;
}

export function checkOrderLicenseIntegrity(input) {
  strict(input, ['schema_version', 'coverage', 'orders', 'payments', 'licenses'], 'snapshot');
  ensure(input.schema_version === 1, 'Unsupported schema_version');
  strict(input.coverage, COVERAGE, 'coverage');
  for (const source of COVERAGE) ensure(['complete', 'partial', 'missing'].includes(input.coverage[source]), 'Invalid coverage');
  for (const source of COVERAGE) ensure(Array.isArray(input[source]), `${source} must be an array`);

  const excluded = { exact_duplicates: 0 };
  const orders = new Map(), payments = new Map(), licenses = new Map();
  for (const order of input.orders) {
    strict(order, ORDER_KEYS, 'order');
    ensure(opaque(order.product_code), 'order: product_code required');
    ensure(/^[A-Z]{3,8}$/.test(order.currency), 'order: explicit currency required');
    amount(order.expected_amount);
    ensure(['PENDING', 'SUBMITTED', 'VERIFYING', 'ACTIVE', 'CANCELLED', 'EXPIRED', 'REFUNDED'].includes(order.status), 'order: invalid status');
    ensure(typeof order.requires_license === 'boolean', 'order: requires_license must be boolean');
    addUnique(orders, order.order_id, order, 'order', excluded);
  }
  for (const payment of input.payments) {
    strict(payment, PAYMENT_KEYS, 'payment');
    ensure(opaque(payment.order_id) && opaque(payment.evidence_ref), 'payment: opaque order/evidence reference required');
    ensure(/^[A-Z]{3,8}$/.test(payment.currency), 'payment: explicit currency required');
    amount(payment.amount);
    ensure(payment.verification_source === 'server_ledger', 'payment: server-ledger verification required');
    addUnique(payments, payment.payment_id, payment, 'payment', excluded);
  }
  for (const license of input.licenses) {
    strict(license, LICENSE_KEYS, 'license');
    ensure(opaque(license.order_id) && opaque(license.product_code) && opaque(license.evidence_ref), 'license: opaque references required');
    ensure(['active', 'expired', 'revoked'].includes(license.state), 'license: invalid state');
    ensure(utc(license.starts_at) < utc(license.expires_at), 'license: expiry must follow start');
    addUnique(licenses, license.license_id, license, 'license', excluded);
  }

  const anomalies = {
    verified_payment_without_order: 0,
    verified_payment_amount_or_currency_mismatch: 0,
    multiple_verified_payments_for_order: 0,
    verified_payment_for_nonactive_order: 0,
    active_order_without_verified_payment: 0,
    active_licensed_order_without_license: 0,
    license_without_order: 0,
    license_product_mismatch: 0,
    active_license_for_nonactive_order: 0,
    multiple_active_licenses_for_order: 0,
  };
  const paymentsByOrder = new Map(), licensesByOrder = new Map();
  for (const { value: payment } of payments.values()) {
    if (!paymentsByOrder.has(payment.order_id)) paymentsByOrder.set(payment.order_id, []);
    paymentsByOrder.get(payment.order_id).push(payment);
    const order = orders.get(payment.order_id)?.value;
    if (!order) { anomalies.verified_payment_without_order++; continue; }
    if (amount(payment.amount) !== amount(order.expected_amount) || payment.currency !== order.currency) anomalies.verified_payment_amount_or_currency_mismatch++;
    if (order.status !== 'ACTIVE') anomalies.verified_payment_for_nonactive_order++;
  }
  for (const list of paymentsByOrder.values()) if (list.length > 1) anomalies.multiple_verified_payments_for_order++;

  for (const { value: license } of licenses.values()) {
    if (!licensesByOrder.has(license.order_id)) licensesByOrder.set(license.order_id, []);
    licensesByOrder.get(license.order_id).push(license);
    const order = orders.get(license.order_id)?.value;
    if (!order) { anomalies.license_without_order++; continue; }
    if (license.product_code !== order.product_code) anomalies.license_product_mismatch++;
    if (license.state === 'active' && order.status !== 'ACTIVE') anomalies.active_license_for_nonactive_order++;
  }
  for (const list of licensesByOrder.values()) if (list.filter(item => item.state === 'active').length > 1) anomalies.multiple_active_licenses_for_order++;

  for (const { value: order } of orders.values()) {
    if (order.status !== 'ACTIVE') continue;
    if ((paymentsByOrder.get(order.order_id) || []).length === 0) anomalies.active_order_without_verified_payment++;
    if (order.requires_license && (licensesByOrder.get(order.order_id) || []).length === 0) anomalies.active_licensed_order_without_license++;
  }

  const observedCount = Object.values(anomalies).reduce((sum, value) => sum + value, 0);
  const complete = COVERAGE.every(source => input.coverage[source] === 'complete');
  return {
    schema_version: 1,
    coverage: { ...input.coverage },
    integrity_status: observedCount > 0 ? 'FAIL' : complete ? 'PASS' : 'UNKNOWN',
    observed: {
      unique_orders: orders.size,
      unique_verified_payments: payments.size,
      unique_licenses: licenses.size,
      anomaly_count: observedCount,
      anomalies,
    },
    totals: complete ? {
      unique_orders: orders.size,
      unique_verified_payments: payments.size,
      unique_licenses: licenses.size,
      anomaly_count: observedCount,
    } : null,
    excluded,
    limitations: [
      'Input provenance and declared coverage are caller assertions; this checker does not access production systems.',
      'A PASS requires complete order, server-ledger payment, and license snapshots, but does not prove delivery, use, revenue recognition, or renewal.',
      'Output is aggregate only. Keep the input private and use opaque identifiers instead of emails, transaction IDs, wallet addresses, or license keys.',
    ],
  };
}

const main = process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (main) {
  try {
    ensure(process.argv.length === 3, 'Usage: node scripts/order-license-integrity.mjs /private/snapshot.json');
    const raw = readFileSync(process.argv[2], 'utf8');
    ensure(Buffer.byteLength(raw, 'utf8') <= 8 * 1024 * 1024, 'Snapshot exceeds 8 MiB');
    console.log(JSON.stringify(checkOrderLicenseIntegrity(JSON.parse(raw)), null, 2));
  } catch {
    console.error('Invalid snapshot. No report produced. Keep private records out of GitHub and use the documented normalized schema.');
    process.exitCode = 1;
  }
}
