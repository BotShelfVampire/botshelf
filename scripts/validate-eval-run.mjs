#!/usr/bin/env node

import { readFile } from "node:fs/promises";

const path = process.argv[2];
if (!path) {
  console.error("Usage: node scripts/validate-eval-run.mjs <eval-run.json>");
  process.exit(2);
}

let data;
try {
  data = JSON.parse(await readFile(path, "utf8"));
} catch (error) {
  console.error(`FAIL: cannot read valid JSON: ${error.message}`);
  process.exit(1);
}

const errors = [];
const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const requireObject = (value, label) => {
  if (!isObject(value)) errors.push(`${label} must be an object`);
};
const requireArray = (value, label) => {
  if (!Array.isArray(value)) errors.push(`${label} must be an array`);
};

if (data.schema_version !== "1.0") errors.push("schema_version must be 1.0");
requireObject(data.workflow, "workflow");
requireObject(data.acceptance, "acceptance");
requireArray(data.cases, "cases");
requireArray(data.runs, "runs");
requireObject(data.baseline_comparison, "baseline_comparison");
requireObject(data.summary, "summary");

if (Array.isArray(data.cases)) {
  const ids = new Set();
  for (const [index, item] of data.cases.entries()) {
    if (!isObject(item)) {
      errors.push(`cases[${index}] must be an object`);
      continue;
    }
    if (!item.case_id) errors.push(`cases[${index}].case_id is required`);
    if (item.case_id && ids.has(item.case_id)) errors.push(`duplicate case_id: ${item.case_id}`);
    ids.add(item.case_id);
    for (const key of ["expected_facts", "forbidden_claims", "required_fields"]) {
      if (!Array.isArray(item[key])) errors.push(`cases[${index}].${key} must be an array`);
    }
  }

  if (Array.isArray(data.runs)) {
    const runIds = new Set();
    for (const [index, run] of data.runs.entries()) {
      if (!isObject(run)) {
        errors.push(`runs[${index}] must be an object`);
        continue;
      }
      if (run.run_id && runIds.has(run.run_id)) errors.push(`duplicate run_id: ${run.run_id}`);
      if (run.run_id) runIds.add(run.run_id);
      if (run.case_id && !ids.has(run.case_id)) errors.push(`runs[${index}] references unknown case_id: ${run.case_id}`);
      if (!["not_run", "passed", "failed"].includes(run.result)) errors.push(`runs[${index}].result is invalid`);
      if (!Array.isArray(run.blocking_failures_observed)) errors.push(`runs[${index}].blocking_failures_observed must be an array`);
      if (run.result === "passed" && run.blocking_failures_observed?.length) {
        errors.push(`runs[${index}] cannot pass with blocking failures`);
      }
    }
  }
}

if (isObject(data.summary) && Array.isArray(data.runs)) {
  const completed = data.runs.filter((run) => run?.result === "passed" || run?.result === "failed");
  const passed = completed.filter((run) => run.result === "passed").length;
  const failed = completed.filter((run) => run.result === "failed").length;
  if (data.summary.total_runs !== completed.length) errors.push(`summary.total_runs must equal ${completed.length}`);
  if (data.summary.passed_runs !== passed) errors.push(`summary.passed_runs must equal ${passed}`);
  if (data.summary.failed_runs !== failed) errors.push(`summary.failed_runs must equal ${failed}`);
  if (failed > 0 && data.summary.status === "limited_pass") errors.push("limited_pass is invalid while failed runs remain");
  if (completed.length === 0 && data.summary.status !== "design_only") errors.push("status must be design_only when no runs are complete");
}

if (errors.length) {
  console.error("FAIL");
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log("PASS: structure and cross-field checks completed");
console.log("Note: this validator does not judge factual quality or prove model reliability.");
