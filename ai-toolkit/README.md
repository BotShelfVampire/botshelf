# BSV AI Expansion Toolkit

Original, practical source packs for newer AI-agent surfaces and agent infrastructure.

Current first tranche:
- OpenAI dots: ongoing-responsibility design, custom-rule starter, activity-review checklist
- Hugging Face Agents/MCP: research/operator workflow that uses the official MCP setup path rather than hard-coding credentials

These are copy/use foundations. They do not claim that BotShelf Vampire itself hosts or controls the external product.

## Status

- Dots materials: source prepared from current official product/help documentation; **Untested on a user account unless separately evidenced**
- Hugging Face materials: source prepared against current official Agents/MCP documentation; **Untested until the exact client/config/run is evidenced**

Keep external permissions, spending, sending, publishing, destructive changes and account actions behind the controls of the external product and the user's explicit authorization.


## Hugging Face expansion paths

- `hugging-face/hf-mcp-research-desk.md` — inspectable Hub research workflow
- `hugging-face/space-tool-safety-gate.md` — trust/data gate before using community Spaces as MCP tools
- `hugging-face/hf-skills-workflow.md` — scope and approval pattern for Hugging Face Skills
- `hugging-face/local-tiny-agent/` — local-reasoning + selective MCP template for Tiny Agents

The local Tiny Agent path is deliberately useful for BSV's broader local/self-hosted direction: model inference can remain local while external MCP tools remain explicit, separate trust boundaries.

## OpenAI dots expansion paths

- `dots/custom-rules-starter.md`
- `dots/ongoing-responsibility-template.md`
- `dots/activity-review-checklist.md`

These are practical rule/responsibility templates for an always-on dot. They do not override built-in safeguards or turn a draft instruction into permission for consequential actions.

## Additional current agent surfaces

- **LM Studio Bionic** — project-worker and context-compressor templates for local/open-model work
- **Hugging Face smolagents** — LM Studio local ToolCallingAgent starter with no tools enabled by default
- **Letta** — durable project-memory layout for stateful agents
- **OpenAI Agents SDK** — guarded no-side-effect worker starter that can later be extended with tools, handoffs, guardrails and sandbox agents

These are intentionally different patterns: Bionic is an agent harness/app, smolagents is a lightweight Python framework, Letta focuses on persistent state/memory, and the OpenAI Agents SDK provides managed agent orchestration primitives. BSV should help users choose by job instead of pretending every agent framework is interchangeable.
