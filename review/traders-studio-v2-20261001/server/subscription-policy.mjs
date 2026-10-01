/** Pure commercial policy. No wallets, chain calls, charging or payouts. */
export const COMMERCIAL_TERMS = Object.freeze({
  currency: 'USDT', network: 'TRC20', billingInterval: 'month',
  term: 'rolling-30-days', accessDays: 30, platformFeeBps: 2000, sellerShareBps: 8000,
  autoDebit: false
});
const minor = v => {
  if (typeof v !== 'string' || !/^\d+$/.test(v)) throw new Error('invalid_minor_amount');
  return BigInt(v);
};
export function parseMonthlyPrice(v) {
  if (typeof v !== 'string' || !/^\d{1,18}(?:\.\d{1,6})?$/.test(v)) throw new Error('invalid_price');
  const [whole, fraction=''] = v.split('.');
  const amount = BigInt(whole) * 1000000n + BigInt(fraction.padEnd(6, '0'));
  if (amount <= 0n) throw new Error('paid_price_must_be_positive');
  return amount.toString();
}
export function splitMonthlyReceipt(grossMinor) {
  const gross = minor(grossMinor);
  if (gross <= 0n) throw new Error('paid_price_must_be_positive');
  // USDT micro-unit rounding: round the 20% fee down, give the residual to seller.
  const platform = gross * 2000n / 10000n;
  return {grossMinor:gross.toString(),platformMinor:platform.toString(),sellerMinor:(gross-platform).toString(),...COMMERCIAL_TERMS};
}
function time(value) {const n=Date.parse(value);if(!Number.isFinite(n))throw new Error('invalid_timestamp');return n;}
export function renewAccess({confirmedAt, currentExpiresAt=null}) {
  const confirmed = time(confirmedAt);
  const base = currentExpiresAt ? Math.max(confirmed,time(currentExpiresAt)) : confirmed;
  return {confirmedAt:new Date(confirmed).toISOString(),extendsFrom:new Date(base).toISOString(),expiresAt:new Date(base+30*86400000).toISOString()};
}
export function subscriptionIsActive(record, expected, now=new Date().toISOString()) {
  if (!record || record.status!=='ACTIVE' || record.paymentStatus!=='CONFIRMED' || record.currency!=='USDT' || record.network!=='TRC20') return false;
  if(!record.confirmationRef || !record.orderId || record.actorId!==expected.actorId || record.listingId!==expected.listingId || record.productId!==expected.productId || record.contentHash!==expected.contentHash || record.revision!==expected.revision) return false;
  try{return time(record.startsAt)<=time(now) && time(now)<time(record.expiresAt);}catch{return false;}
}
export function productMatches(product, expected) {
  return !!product?.id && ['listingId','ownerId','revision','contentHash','priceMinor','currency','network','billingInterval','term','accessDays','platformFeeBps','sellerShareBps','type'].every(k=>product[k]===expected[k]);
}
