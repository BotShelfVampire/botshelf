# Letta Project Memory Template

Letta is designed for stateful agents with persistent memory. Use that memory for durable project facts, not a dumping ground for every chat message.

## Memory hierarchy

### identity.md
What this agent owns:
- role
- scope
- what it must never do

### project.md
Stable project truth:
- product purpose
- architecture that rarely changes
- canonical repositories/surfaces

### decisions.md
Only binding decisions:
- pricing
- access rules
- approval gates
- naming/positioning constraints

### current-state.md
Short operational state:
- latest deployed revision
- open blockers
- current milestone
- next verified action

### failures.md
Failures worth preventing from recurring:
- what failed
- exact condition
- fix or guard

## Maintenance

When memory grows:
- deduplicate repeated facts
- move temporary state out of durable files
- preserve superseded decisions only when needed for audit
- keep system-prompt/memory token usage inspectable

Do not store credentials/secrets just because memory persists.

Official references:
- https://docs.letta.com/concepts/stateful-agents
- https://docs.letta.com/configuration/memory
