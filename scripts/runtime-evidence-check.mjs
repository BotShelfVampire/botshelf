#!/usr/bin/env node
/** Validate a private Switchboard runtime-evidence record without echoing it. */
import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const ensure = (condition, message) => { if (!condition) throw new Error(message); };
const plain = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const opaque = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value);
const exactKeys = (value, allowed, required, label) => {
  ensure(plain(value), `${label}: expected object`);
  ensure(Object.keys(value).every(key => allowed.includes(key)), `${label}: unsupported field`);
  ensure(required.every(key => Object.hasOwn(value, key)), `${label}: missing field`);
};
const cleanSummary = value => {
  ensure(typeof value === 'string' && value.trim().length >= 8 && value.length <= 500, 'Summary must be 8-500 characters');
  ensure(!/[\r\n]/.test(value), 'Summary must be one line');
  ensure(!/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value), 'Summary must not contain an email address');
  ensure(!/https?:\/\//i.test(value), 'Summary must not contain a URL');
  ensure(!/\b(?:\d{1,3}\.){3}\d{1,3}\b/.test(value), 'Summary must not contain an IPv4 address');
  return value.trim();
};
const utc = value => {
  ensure(typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(value), 'Expected UTC ISO timestamp');
  const time = Date.parse(value);
  ensure(Number.isFinite(time), 'Invalid timestamp');
  ensure(new Date(time).toISOString() === value.replace(/(?<!\.\d{3})Z$/, '.000Z'), 'Invalid calendar date');
  return time;
};

export function checkRuntimeEvidence(input) {
  exactKeys(input,
    ['schema_version', 'task_id', 'product', 'participant', 'timing', 'execution', 'approval', 'outcome', 'evidence'],
    ['schema_version', 'task_id', 'product', 'participant', 'timing', 'execution', 'approval', 'outcome', 'evidence'],
    'record');
  ensure(input.schema_version === 1, 'Unsupported schema_version');
  ensure(input.task_id === 'BSV-R01-A', 'Unexpected task_id');
  ensure(input.product === 'switchboard-free', 'This gate is for the free Switchboard only');

  exactKeys(input.participant, ['kind', 'consent_confirmed'], ['kind', 'consent_confirmed'], 'participant');
  ensure(['newcomer', 'owner', 'internal', 'test', 'vendor'].includes(input.participant.kind), 'Unknown participant kind');
  ensure(typeof input.participant.consent_confirmed === 'boolean', 'Consent must be explicit');

  exactKeys(input.timing, ['started_at', 'completed_at', 'timezone'], ['started_at', 'completed_at', 'timezone'], 'timing');
  const started = utc(input.timing.started_at), completed = utc(input.timing.completed_at);
  ensure(started < completed, 'Run must complete after it starts');
  ensure(input.timing.timezone === 'Asia/Tokyo', 'Record the validation run in Asia/Tokyo');

  exactKeys(input.execution,
    ['environment', 'job_kind', 'execution_kind', 'input_summary', 'output_summary', 'one_next_action_produced'],
    ['environment', 'job_kind', 'execution_kind', 'input_summary', 'output_summary', 'one_next_action_produced'],
    'execution');
  ensure(['production-free', 'existing-test'].includes(input.execution.environment), 'Unknown environment');
  ensure(['real', 'synthetic', 'sample'].includes(input.execution.job_kind), 'Unknown job kind');
  ensure(['runtime', 'structural', 'sample'].includes(input.execution.execution_kind), 'Unknown execution kind');
  cleanSummary(input.execution.input_summary);
  cleanSummary(input.execution.output_summary);
  ensure(typeof input.execution.one_next_action_produced === 'boolean', 'Next-action result must be explicit');

  exactKeys(input.approval,
    ['boundary_present', 'external_action_attempted', 'stopped_before_external_action', 'human_decision'],
    ['boundary_present', 'external_action_attempted', 'stopped_before_external_action', 'human_decision'],
    'approval');
  for (const key of ['boundary_present', 'external_action_attempted', 'stopped_before_external_action']) {
    ensure(typeof input.approval[key] === 'boolean', `${key} must be boolean`);
  }
  ensure(['pending', 'approved', 'rejected'].includes(input.approval.human_decision), 'Unknown human decision');

  exactKeys(input.outcome, ['accepted_by_participant', 'failure_stage'], ['accepted_by_participant', 'failure_stage'], 'outcome');
  ensure(typeof input.outcome.accepted_by_participant === 'boolean', 'Acceptance must be explicit');
  ensure(input.outcome.failure_stage === null || ['setup', 'input', 'runtime', 'output', 'approval'].includes(input.outcome.failure_stage), 'Unknown failure stage');

  exactKeys(input.evidence,
    ['environment_ref', 'input_ref', 'output_ref', 'approval_ref'],
    ['environment_ref', 'input_ref', 'output_ref', 'approval_ref'],
    'evidence');
  for (const key of ['environment_ref', 'input_ref', 'output_ref', 'approval_ref']) {
    ensure(opaque(input.evidence[key]), `${key} must be an opaque private reference`);
  }

  const failures = [];
  if (input.participant.kind !== 'newcomer') failures.push('participant_not_newcomer');
  if (!input.participant.consent_confirmed) failures.push('consent_not_confirmed');
  if (input.execution.environment !== 'production-free') failures.push('not_free_production_path');
  if (input.execution.job_kind !== 'real') failures.push('job_not_real');
  if (input.execution.execution_kind !== 'runtime') failures.push('not_runtime_execution');
  if (!input.execution.one_next_action_produced) failures.push('no_prioritized_next_action');
  if (!input.approval.boundary_present) failures.push('approval_boundary_missing');
  if (input.approval.external_action_attempted) failures.push('external_action_attempted');
  if (!input.approval.stopped_before_external_action) failures.push('did_not_stop_before_external_action');

  const evidenceGate = failures.length === 0 ? 'PASS' : 'FAIL';
  return {
    schema_version: 1,
    task_id: 'BSV-R01-A',
    evidence_gate: evidenceGate,
    accepted_runtime_eligible: evidenceGate === 'PASS' && input.outcome.accepted_by_participant,
    failure_stage: input.outcome.failure_stage,
    failures,
    limitations: [
      'The checker validates record structure and declared evidence references, not the evidence contents.',
      'A PASS is not customer demand, payment, renewal, production-source verification or deployment approval.',
      'Keep the input record and referenced evidence private; publish only aggregate conclusions.',
    ],
  };
}

const main = process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
if (main) {
  try {
    ensure(process.argv.length === 3, 'Usage: node scripts/runtime-evidence-check.mjs /private/runtime-evidence.json');
    const raw = readFileSync(process.argv[2], 'utf8');
    ensure(Buffer.byteLength(raw, 'utf8') <= 1024 * 1024, 'Evidence record exceeds 1 MiB');
    console.log(JSON.stringify(checkRuntimeEvidence(JSON.parse(raw)), null, 2));
  } catch {
    console.error('Invalid runtime-evidence record. No evidence content or private identifier was printed.');
    process.exitCode = 1;
  }
}
