# Hugging Face local Tiny Agent starter

This starter is for people who want a local model to remain the reasoning engine while selectively connecting MCP tools.

## Setup

1. Run an OpenAI-compatible local model server (for example a supported local Hugging Face/Transformers or llama.cpp path).
2. Copy `agent.template.json` to `agent.json`.
3. Replace `YOUR_LOCAL_MODEL_ID`.
4. Replace the example MCP URL only with a Space/server you actually trust.
5. Run the Tiny Agent with the current Hugging Face tiny-agents command for your installation.
6. Start with synthetic/non-sensitive input.

The important design idea is separation:
- model inference can stay local
- tools may still be remote
- each remote MCP server is a separate data boundary

Official references:
- https://huggingface.co/docs/hub/agents-libraries
- https://huggingface.co/docs/hub/en/agents-local
- https://huggingface.co/docs/hub/en/agents-sdk

Status: template/source prepared. Exact local model and MCP server combination is untested until evidenced.
