#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const argv = process.argv.slice(2);
const goalIndex = argv.indexOf('--goal');
const filesIndex = argv.indexOf('--files');
const outIndex = argv.indexOf('--out');

const goal = goalIndex >= 0 ? argv[goalIndex + 1] : '';
const fileList = filesIndex >= 0 ? argv[filesIndex + 1].split(',').map(x => x.trim()).filter(Boolean) : [];
const outPath = outIndex >= 0 ? argv[outIndex + 1] : '';

if (!goal || fileList.length === 0) {
  console.error('Usage: node scripts/build-context-pack.mjs --goal "..." --files a,b,c [--out pack.json]');
  process.exit(1);
}

function git(...args) {
  try {
    return execFileSync('git', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

const maxPerFile = 12000;
const files = [];

for (const p of fileList) {
  const normalized = path.normalize(p);
  if (normalized.startsWith('..') || path.isAbsolute(normalized)) {
    throw new Error('Only repository-relative paths are allowed: ' + p);
  }
  if (!fs.existsSync(normalized) || !fs.statSync(normalized).isFile()) {
    throw new Error('Missing file: ' + normalized);
  }

  const raw = fs.readFileSync(normalized, 'utf8');
  const content = raw.length > maxPerFile
    ? raw.slice(0, maxPerFile) + '\n...[TRUNCATED BY CONTEXT PACK BUILDER]'
    : raw;

  const revision = git('log', '-1', '--format=%H', '--', normalized);

  files.push({
    path: normalized,
    revision: revision || 'unknown',
    chars_original: raw.length,
    chars_included: content.length,
    content
  });
}

const changed = git('status', '--short').split('\n').filter(Boolean).slice(0, 80);
const head = git('rev-parse', 'HEAD') || 'unknown';

const pack = {
  schema: 'bsv-context-pack-0.1',
  generated_at: new Date().toISOString(),
  repo_head: head,
  goal,
  working_tree_changes: changed,
  files
};

const json = JSON.stringify(pack, null, 2) + '\n';
if (outPath) {
  fs.writeFileSync(outPath, json);
  process.stdout.write(outPath + '\n');
} else {
  process.stdout.write(json);
}
