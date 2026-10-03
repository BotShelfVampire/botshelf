#!/usr/bin/env node
import fs from 'node:fs';

const argv = process.argv.slice(2);
const inputIndex = argv.indexOf('--input');
const outputIndex = argv.indexOf('--out');
const modelIndex = argv.indexOf('--model');

const inputPath = inputIndex >= 0 ? argv[inputIndex + 1] : '';
const outputPath = outputIndex >= 0 ? argv[outputIndex + 1] : '';
const model = modelIndex >= 0 ? argv[modelIndex + 1] : process.env.LM_STUDIO_MODEL;
const baseUrl = process.env.LM_STUDIO_BASE_URL || 'http://127.0.0.1:1234/v1';

if (!inputPath || !model) {
  console.error('Usage: LM_STUDIO_MODEL=<id> node scripts/lmstudio-compact-context.mjs --input pack.json [--out compact.txt]');
  process.exit(1);
}

const raw = fs.readFileSync(inputPath, 'utf8');

const system = [
  'Compress project context for another engineering model.',
  'Preserve binding requirements, exact numbers, filenames, failures, TODOs, verification state, and contradictions.',
  'Do not invent facts or upgrade Untested/Unverified to PASS.',
  'Remove repetition, greetings, progress narration, and duplicated explanation.',
  'Return only these headings: GOAL, BINDING, STATE, FILES, FAILURES, DELIVERABLE, VERIFY.'
].join(' ');

const response = await fetch(baseUrl + '/chat/completions', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({
    model,
    temperature: 0,
    max_tokens: 1400,
    messages: [
      { role: 'system', content: system },
      { role: 'user', content: raw }
    ]
  })
});

if (!response.ok) {
  throw new Error('LM Studio request failed: ' + response.status + ' ' + await response.text());
}

const data = await response.json();
const text = data?.choices?.[0]?.message?.content;
if (!text) throw new Error('LM Studio response contained no message content');

if (outputPath) {
  fs.writeFileSync(outputPath, text.trim() + '\n');
  process.stdout.write(outputPath + '\n');
} else {
  process.stdout.write(text.trim() + '\n');
}
