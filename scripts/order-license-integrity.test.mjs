import test from 'node:test';
import assert from 'node:assert/strict';
import { checkOrderLicenseIntegrity as check } from './order-license-integrity.mjs';

const order = (extra = {}) => ({ order_id: 'order-1', product_code: 'switchboard', expected_amount: '20', currency: 'USDT', status: 'ACTIVE', requires_license: true, ...extra });
const payment = (extra = {}) => ({ payment_id: 'payment-1', order_id: 'order-1', amount: '20.00', currency: 'USDT', verification_source: 'server_ledger', evidence_ref: 'ledger-1', ...extra });
const license = (extra = {}) => ({ license_id: 'license-1', order_id: 'order-1', product_code: 'switchboard', state: 'active', starts_at: '2026-09-01T00:00:00Z', expires_at: '2026-10-01T00:00:00Z', evidence_ref: 'license-ledger-1', ...extra });
const snapshot = (extra = {}) => ({ schema_version: 1, coverage: { orders: 'complete', payments: 'complete', licenses: 'complete' }, orders: [order()], payments: [payment()], licenses: [license()], ...extra });

test('complete consistent snapshot passes', () => assert.equal(check(snapshot()).integrity_status, 'PASS'));
test('incomplete clean snapshot is unknown', () => assert.equal(check(snapshot({ coverage: { orders: 'complete', payments: 'partial', licenses: 'complete' } })).integrity_status, 'UNKNOWN'));
test('active licensed order without license fails', () => assert.equal(check(snapshot({ licenses: [] })).observed.anomalies.active_licensed_order_without_license, 1));
test('active order without payment fails', () => assert.equal(check(snapshot({ payments: [] })).observed.anomalies.active_order_without_verified_payment, 1));
test('verified payment without order fails', () => assert.equal(check(snapshot({ orders: [], licenses: [] })).observed.anomalies.verified_payment_without_order, 1));
test('license without order fails', () => assert.equal(check(snapshot({ orders: [], payments: [] })).observed.anomalies.license_without_order, 1));
test('amount mismatch fails', () => assert.equal(check(snapshot({ payments: [payment({ amount: '199.5' })] })).observed.anomalies.verified_payment_amount_or_currency_mismatch, 1));
test('currency mismatch fails', () => assert.equal(check(snapshot({ payments: [payment({ currency: 'USD' })] })).observed.anomalies.verified_payment_amount_or_currency_mismatch, 1));
test('verified payment for pending order fails', () => assert.equal(check(snapshot({ orders: [order({ status: 'VERIFYING' })], licenses: [] })).observed.anomalies.verified_payment_for_nonactive_order, 1));
test('active license for pending order fails', () => assert.equal(check(snapshot({ orders: [order({ status: 'VERIFYING' })], payments: [] })).observed.anomalies.active_license_for_nonactive_order, 1));
test('license product mismatch fails', () => assert.equal(check(snapshot({ licenses: [license({ product_code: 'other-product' })] })).observed.anomalies.license_product_mismatch, 1));
test('multiple payments for one order fail', () => assert.equal(check(snapshot({ payments: [payment(), payment({ payment_id: 'payment-2', evidence_ref: 'ledger-2' })] })).observed.anomalies.multiple_verified_payments_for_order, 1));
test('multiple active licenses for one order fail', () => assert.equal(check(snapshot({ licenses: [license(), license({ license_id: 'license-2', evidence_ref: 'license-ledger-2' })] })).observed.anomalies.multiple_active_licenses_for_order, 1));
test('exact duplicates count once', () => { const p = payment(); const r = check(snapshot({ payments: [p, { ...p }] })); assert.equal(r.observed.unique_verified_payments, 1); assert.equal(r.excluded.exact_duplicates, 1); });
test('conflicting duplicate payment fails closed', () => assert.throws(() => check(snapshot({ payments: [payment(), payment({ amount: '21' })] }))));
test('non-server verification is rejected', () => assert.throws(() => check(snapshot({ payments: [payment({ verification_source: 'browser' })] }))));
test('numeric or zero amount is rejected', () => { for (const value of [20, '0', '-1', '1e2']) assert.throws(() => check(snapshot({ payments: [payment({ amount: value })] }))); });
test('invalid license interval is rejected', () => assert.throws(() => check(snapshot({ licenses: [license({ expires_at: '2026-08-01T00:00:00Z' })] }))));
test('unsupported fields are rejected', () => assert.throws(() => check({ ...snapshot(), email: 'private@example.com' })));
test('output omits opaque identifiers', () => { const output = JSON.stringify(check(snapshot())); for (const id of ['order-1', 'payment-1', 'license-1', 'ledger-1']) assert.equal(output.includes(id), false); });
