import test from 'node:test';
import assert from 'node:assert/strict';
import { checkRuntimeEvidence } from './runtime-evidence-check.mjs';

const valid = () => ({
  schema_version: 1,
  task_id: 'BSV-R01-A',
  product: 'switchboard-free',
  participant: { kind: 'newcomer', consent_confirmed: true },
  timing: { started_at: '2026-09-29T10:00:00Z', completed_at: '2026-09-29T10:05:00Z', timezone: 'Asia/Tokyo' },
  execution: {
    environment: 'production-free',
    job_kind: 'real',
    execution_kind: 'runtime',
    input_summary: 'Prioritize three competing backlog items for a small operator.',
    output_summary: 'Returned one recommended next action with a short rationale.',
    one_next_action_produced: true,
  },
  approval: { boundary_present: true, external_action_attempted: false, stopped_before_external_action: true, human_decision: 'pending' },
  outcome: { accepted_by_participant: true, failure_stage: null },
  evidence: { environment_ref: 'env-proof-1', input_ref: 'input-proof-1', output_ref: 'output-proof-1', approval_ref: 'approval-proof-1' },
});

test('complete real newcomer run passes and is eligible', () => {
  const result = checkRuntimeEvidence(valid());
  assert.equal(result.evidence_gate, 'PASS');
  assert.equal(result.accepted_runtime_eligible, true);
});

test('rejected output preserves evidence pass but is not accepted use', () => {
  const input = valid();
  input.outcome.accepted_by_participant = false;
  input.outcome.failure_stage = 'output';
  const result = checkRuntimeEvidence(input);
  assert.equal(result.evidence_gate, 'PASS');
  assert.equal(result.accepted_runtime_eligible, false);
});

test('owner, internal, test and vendor runs fail the newcomer gate', () => {
  for (const kind of ['owner', 'internal', 'test', 'vendor']) {
    const input = valid();
    input.participant.kind = kind;
    assert.equal(checkRuntimeEvidence(input).evidence_gate, 'FAIL');
  }
});

test('consent must be confirmed', () => {
  const input = valid();
  input.participant.consent_confirmed = false;
  assert.deepEqual(checkRuntimeEvidence(input).failures, ['consent_not_confirmed']);
});

test('existing test environment is not a newcomer production-free proof', () => {
  const input = valid();
  input.execution.environment = 'existing-test';
  assert.deepEqual(checkRuntimeEvidence(input).failures, ['not_free_production_path']);
});

test('synthetic and sample jobs cannot pass', () => {
  for (const kind of ['synthetic', 'sample']) {
    const input = valid();
    input.execution.job_kind = kind;
    assert.equal(checkRuntimeEvidence(input).evidence_gate, 'FAIL');
  }
});

test('structural and sample execution cannot pass', () => {
  for (const kind of ['structural', 'sample']) {
    const input = valid();
    input.execution.execution_kind = kind;
    assert.equal(checkRuntimeEvidence(input).evidence_gate, 'FAIL');
  }
});

test('one prioritized next action is required', () => {
  const input = valid();
  input.execution.one_next_action_produced = false;
  assert.deepEqual(checkRuntimeEvidence(input).failures, ['no_prioritized_next_action']);
});

test('approval boundary and pre-action stop are required', () => {
  const input = valid();
  input.approval.boundary_present = false;
  input.approval.stopped_before_external_action = false;
  assert.deepEqual(checkRuntimeEvidence(input).failures, ['approval_boundary_missing', 'did_not_stop_before_external_action']);
});

test('attempted external action fails the gate', () => {
  const input = valid();
  input.approval.external_action_attempted = true;
  assert.deepEqual(checkRuntimeEvidence(input).failures, ['external_action_attempted']);
});

test('all four evidence references are required and opaque', () => {
  for (const key of Object.keys(valid().evidence)) {
    const input = valid();
    input.evidence[key] = '';
    assert.throws(() => checkRuntimeEvidence(input));
  }
});

test('email, URL and IPv4 data are rejected from summaries', () => {
  for (const value of ['Contact person@example.com now', 'Open https://example.com for details', 'Server is 192.168.1.10 today']) {
    const input = valid();
    input.execution.input_summary = value;
    assert.throws(() => checkRuntimeEvidence(input));
  }
});

test('invalid or reversed timestamps fail', () => {
  const input = valid();
  input.timing.completed_at = input.timing.started_at;
  assert.throws(() => checkRuntimeEvidence(input));
});

test('unsupported fields fail closed', () => {
  const input = valid();
  input.participant.email = 'hidden@example.com';
  assert.throws(() => checkRuntimeEvidence(input));
});

test('output never includes summaries or evidence references', () => {
  const input = valid();
  const output = JSON.stringify(checkRuntimeEvidence(input));
  for (const value of [input.execution.input_summary, input.execution.output_summary, ...Object.values(input.evidence)]) {
    assert.equal(output.includes(value), false);
  }
});
