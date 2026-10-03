"""
BSV smolagents + LM Studio starter.

Uses an OpenAI-compatible local endpoint and a ToolCallingAgent.
No network tool, file-write tool, or shell tool is enabled by default.

Install:
  pip install smolagents openai

Set:
  LM_STUDIO_MODEL=<model id loaded in LM Studio>
  LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1

Run:
  python lm-studio-local-agent.py "Summarize the tradeoffs in these notes: ..."
"""

import os
import sys
from smolagents import OpenAIServerModel, ToolCallingAgent

model_id = os.environ.get("LM_STUDIO_MODEL")
base_url = os.environ.get("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")

if not model_id:
    raise SystemExit("Set LM_STUDIO_MODEL to the exact model id exposed by LM Studio.")

task = " ".join(sys.argv[1:]).strip()
if not task:
    raise SystemExit("Pass one task as command-line text.")

model = OpenAIServerModel(
    model_id=model_id,
    api_base=base_url,
    api_key="lm-studio",
)

agent = ToolCallingAgent(
    tools=[],
    model=model,
    instructions=(
        "You are a local analysis worker. "
        "Do not claim access to files, web, shell, accounts, or external tools. "
        "Do not invent missing facts. Mark uncertainty explicitly. "
        "Return a concise result that a human or stronger agent can verify."
    ),
    max_steps=4,
)

result = agent.run(task)
print(result)
