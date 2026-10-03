# OpenMarkets — BSV data/agent starter

OpenMarkets is treated here as a **market-data / agent integration surface**, not as a replacement for Pine/MQL chart scripting.

Current public developer surfaces expose REST, WebSocket, and MCP. Use the exact official docs and current account scopes.

## High-value BSV use cases

- normalized market snapshot collector
- price/history research assistant
- cross-venue comparison
- event/market monitor
- MCP-powered research desk
- feed into a custom Vela chart app after you build the adapter

## Safe starting point

Use read-only market-data permissions first.
Do not enable live execution merely to test a research/chart workflow.
Keep API keys outside committed source.

## Agent prompt

See market-monitor-prompt.md.

Official references:
- https://openmarkets.ai/developers
- https://app.openmarkets.ai/developers/mcp
