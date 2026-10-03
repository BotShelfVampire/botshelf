# Hugging Face Skills Workflow Starter

Hugging Face Skills are reusable task instructions for coding agents. Use them as targeted context, not as blanket permission to change repositories or launch paid jobs.

## Practical workflow

1. Decide the job: dataset inspection, evaluation, model training, paper lookup, Gradio UI, Hub operations, etc.
2. Install only the Skill needed for that job using the current official Hugging Face Skills flow.
3. Give the coding agent a scoped task.
4. Add an explicit budget/compute boundary before any job that can create paid compute.
5. Require a dry-run or plan for destructive Hub operations.
6. Require the agent to report the exact Skill used, files changed, commands run, remote jobs started, and resulting URLs/IDs.

## Copyable task frame

GOAL
[one concrete Hugging Face task]

USE
Use the relevant Hugging Face Skill only for this task.

ALLOWED
- inspect local project files
- inspect Hub metadata needed for the task
- prepare configuration/code
- run local validation

ASK BEFORE
- starting paid compute
- pushing or deleting Hub repositories
- making a private artifact public
- replacing an existing model/dataset revision
- exposing tokens or credentials

REPORT
- Skill used
- files changed
- commands run
- remote jobs created
- result
- blockers

Official reference:
https://huggingface.co/docs/hub/agents-skills
