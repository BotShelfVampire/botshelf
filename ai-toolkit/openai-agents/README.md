# OpenAI Agents SDK — guarded worker starter

The Agents SDK provides agents, tools, handoffs/agents-as-tools, guardrails, sessions and tracing.

BSV starts with a deliberately small pattern:

- `guarded-worker.py`
- no side-effect tools
- explicit UNVERIFIED behavior
- add tools only after their permission boundary is understood

Useful expansion paths:
- turn one worker into a manager that calls specialized agents-as-tools
- add structured outputs
- add input/output guardrails
- add sessions for state
- add sandbox agents when a real isolated workspace is needed

Official docs:
- https://openai.github.io/openai-agents-python/
- https://openai.github.io/openai-agents-python/agents/

Status: source prepared. Runtime execution depends on the configured model/API and is not implied by file presence.
