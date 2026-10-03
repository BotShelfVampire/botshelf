# Platform compatibility

Status is about the current BSV Trader Tool Blocks implementation, not the platform's overall capability.

| Platform | Extensibility path | Current BSV asset | Status |
| --- | --- | --- | --- |
| TradingView | Pine Script | recipe generator target | Structurally generated; runtime test required |
| MT5 | MQL5 | recipe generator starter | Structurally generated; runtime test required |
| cTrader | C# Automate API | recipe generator starter | Structurally generated; runtime test required |
| Vela | JavaScript/TypeScript chart library + plugin/scripting engines | custom web-chart starter | Source prepared; runtime test required |
| MT4 | MQL4 | planned renderer | Not implemented |
| NinjaTrader | NinjaScript/C# | research + planned starter | Not implemented |
| Quantower | C# extensions/indicators | research + planned starter | Not implemented |
| Sierra Chart | ACSIL/C++ | research + planned starter | Not implemented |
| Bookmap | Java API/add-ons | research + planned starter | Not implemented |
| GoCharting | platform-specific extensibility | verify current public developer path first | Unverified |
| MotiveWave | SDK/Java | research + planned starter | Not implemented |
| ProRealTime | ProBuilder/ProOrder | research + planned starter | Not implemented |
| OpenMarkets | REST/WebSocket/MCP data APIs, not a chart-script replacement | data/agent recipe candidate | API confirmed; no BSV runtime asset yet |

## Vela

Vela is especially relevant to the BSV goal of letting a user build a custom chart surface rather than only paste an indicator into a closed charting UI.

Official project/docs:
- https://github.com/LuxAlgo/Vela
- https://docs.luxalgo.com/vela/user/quickstart

Vela itself is published under Apache-2.0. Its optional Pine engine has separate licensing; inspect the dependency license before redistributing a bundled runtime.

## OpenMarkets

The current OpenMarkets developer surface exposes market data through REST/WebSocket/MCP. BSV should treat it as a data/agent integration building block, not falsely label it as a chart scripting language.

Official developer surface:
- https://openmarkets.ai/developers
- https://app.openmarkets.ai/developers/mcp
