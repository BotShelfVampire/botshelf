# Hugging Face smolagents + LM Studio

This starter keeps the model local through LM Studio's OpenAI-compatible endpoint and starts with **no tools**.

Source:
- `lm-studio-local-agent.py`

Why start with no tools:
- local inference is cheap
- the output is easy to inspect
- file/shell/web permissions are not silently granted
- you can add one tool at a time after deciding its trust boundary

smolagents supports OpenAI-compatible servers and model/tool abstractions, including local model paths.

Official references:
- https://huggingface.co/docs/smolagents/
- https://huggingface.co/docs/smolagents/reference/models

Status: source prepared. Exact smolagents + LM Studio model combination must be runtime-tested before marking Verified.
