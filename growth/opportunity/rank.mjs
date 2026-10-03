#!/usr/bin/env node
import fs from 'node:fs';

const inputPath = process.argv[2];
if (!inputPath) {
  console.error('Usage: node growth/opportunity/rank.mjs <input.json>');
  process.exit(1);
}

const rows = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
if (!Array.isArray(rows)) throw new Error('Input must be a JSON array.');

const FORMULA_VERSION = '0.1';

function int(v, name) {
  if (!Number.isInteger(v) || v < 0) throw new Error(name + ' must be a non-negative integer');
  return v;
}

function score(row) {
  const uniqueRequesters = int(row.uniqueRequesters ?? 0, 'uniqueRequesters');
  const openRequests = int(row.openRequests ?? 0, 'openRequests');
  const noResultSearches = int(row.noResultSearches ?? 0, 'noResultSearches');
  const missingVariantSignals = int(row.missingVariantSignals ?? 0, 'missingVariantSignals');
  const remixSignals = int(row.remixSignals ?? 0, 'remixSignals');
  const explicitWtpActors = int(row.explicitWtpActors ?? 0, 'explicitWtpActors');
  const fulfilledRequests = int(row.fulfilledRequests ?? 0, 'fulfilledRequests');

  const components = {
    requesterDiversity: Math.min(uniqueRequesters, 10) * 8,
    openRequestPressure: Math.min(openRequests, 20) * 2,
    noResultPressure: Math.min(noResultSearches, 25),
    missingVariantPressure: Math.min(missingVariantSignals, 10) * 2,
    remixInterest: Math.min(remixSignals, 10),
    explicitWtpSignal: Math.min(explicitWtpActors, 5) * 6,
    fulfillmentRelief: -Math.min(fulfilledRequests, 10) * 2
  };

  const raw = Object.values(components).reduce((a, b) => a + b, 0);

  return {
    formulaVersion: FORMULA_VERSION,
    demandEvidenceScore: Math.max(0, raw),
    components,
    counts: {
      uniqueRequesters,
      openRequests,
      noResultSearches,
      missingVariantSignals,
      remixSignals,
      explicitWtpActors,
      fulfilledRequests
    }
  };
}

const ranked = rows.map((row, index) => {
  if (!row.jobKey || typeof row.jobKey !== 'string') throw new Error('row ' + index + ' missing jobKey');
  return {
    jobKey: row.jobKey,
    sector: row.sector ?? null,
    platform: row.platform ?? null,
    ...score(row)
  };
}).sort((a, b) =>
  b.demandEvidenceScore - a.demandEvidenceScore ||
  b.counts.explicitWtpActors - a.counts.explicitWtpActors ||
  b.counts.uniqueRequesters - a.counts.uniqueRequesters ||
  a.jobKey.localeCompare(b.jobKey)
);

process.stdout.write(JSON.stringify({
  schemaVersion: '0.1',
  note: 'Evidence ranking only. Not a revenue or market-size forecast.',
  ranked
}, null, 2) + '\n');
