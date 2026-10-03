# Hugging Face Space Tool Safety Gate

Use before enabling or calling a community Space as an agent tool through MCP.

## Gate

1. Identify the exact Space and owner.
2. Read its current description/card and inputs.
3. Check whether it handles sensitive data.
4. Check whether it performs only computation/content generation or can trigger external effects.
5. Check cost/compute requirements.
6. Do not pass secrets, private source, customer data or credentials unless the Space is explicitly trusted for that data.
7. Start with a synthetic test input.
8. Inspect the output before adding the Space to a recurring workflow.
9. Record the exact Space revision/config used if the result matters operationally.

Dynamic discovery is convenient; it is not a substitute for reviewing the tool you are about to call.

Official reference:
https://huggingface.co/docs/hub/en/agents-mcp
