# Bionic Context Compressor

Use this with a local model when another agent is about to receive a long BSV/project context.

## Prompt

Compress the supplied project material for another engineering agent.

PRESERVE EXACTLY
- binding decisions
- filenames/paths
- numbers/prices/dates
- test failures
- verification status
- unresolved TODOs
- contradictions
- owner approval gates

REMOVE
- greetings
- emotional repetition
- duplicate explanations
- progress narration that does not change state
- already superseded suggestions

NEVER
- invent missing facts
- upgrade Untested/Unverified to PASS
- reinterpret a commercial rule
- omit a known failure because it looks unimportant

OUTPUT ONLY
GOAL:
BINDING:
CURRENT STATE:
FILES:
FAILURES:
TODO:
VERIFY:

Then compare the compressed result against the source for any dropped binding requirement before using it downstream.
