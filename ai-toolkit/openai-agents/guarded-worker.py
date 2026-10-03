"""
BSV guarded worker starter for the OpenAI Agents SDK.

This example intentionally has no external side-effect tools.
It is a pattern for structured first-pass work before adding tools.

Install:
  pip install openai-agents

Set OPENAI_API_KEY, then:
  python guarded-worker.py "Review this requirement: ..."
"""

import sys
from agents import Agent, Runner

task = " ".join(sys.argv[1:]).strip()
if not task:
    raise SystemExit("Pass one task as command-line text.")

agent = Agent(
    name="BSV Guarded Worker",
    instructions=(
        "Work only from information in the user's task. "
        "Do not pretend to browse, edit files, send messages, spend money, or run commands. "
        "Separate facts from assumptions. "
        "If evidence is insufficient, say UNVERIFIED. "
        "Return: RESULT, ASSUMPTIONS, RISKS, NEXT CHECK."
    ),
)

result = Runner.run_sync(agent, task)
print(result.final_output)
