# Platform compatibility

Status is about the current BSV Trader Tool Blocks implementation, not the platform's overall capability.

| Platform | Extensibility path | Current BSV asset | Status |
| --- | --- | --- | --- |
| TradingView | Pine Script | generator target + 6 copy/paste Pine starters | Source prepared; runtime compile still required |
| MT5 | MQL5 | generator starter + EMA/ATR overlay source | Source prepared; runtime compile still required |
| cTrader | C# or Python custom indicators in cTrader Algo | C# and Python generator targets + EMA/ATR (C# and Python) + RSI source | Source prepared; runtime build still required |
| Vela | JavaScript/TypeScript chart library + optional scripting engines | runnable custom web-chart starter | Source prepared; runtime test required |
| NinjaTrader | NinjaScript/C# | EMA/ATR overlay source | Source prepared; runtime compile still required |
| Quantower | C# Quantower Algo | simple SMA source | Source prepared; runtime compile still required |
| Sierra Chart | ACSIL/C++ | EMA overlay custom-study source | Source prepared; runtime build still required |
| GoCharting | Lipi scripting | dual-EMA Lipi source | Source prepared; Lipi-editor validation still required |
| MT4 | MQL4 | generator target (`mql4`) + EMA/ATR overlay source | Source prepared; runtime compile still required |
| Bookmap | Python API (open beta) and Java add-ons/API | Python generator target (`bookmap-python`, time bars built from trades) + trade-EMA add-on source; order-flow blocks still planned | Source prepared; runtime test still required |
| MotiveWave | Java SDK | EMA custom-study source | Source prepared; SDK/build verification required |
| ProRealTime | ProBuilder | dual-EMA copy/paste indicator | Source prepared; runtime validation required |
| ATAS | platform extensibility research | planned | Unverified |
| JForex | Java strategy/indicator APIs | planned | Unverified |
| OpenMarkets | REST/WebSocket/MCP data APIs, not a chart-script replacement | data/agent integration notes | API surface confirmed; no BSV runtime adapter yet |

## Vela

Vela is especially relevant to the BSV goal of letting a user build a custom chart surface rather than only paste an indicator into a closed charting UI.

Official project/docs:
- https://github.com/LuxAlgo/Vela
- https://docs.luxalgo.com/vela/user/quickstart
- https://docs.luxalgo.com/vela/user/scripting-engines

Vela itself is a charting library and does not ship a scripting engine. Engines are opt-in. Review the license of any scripting-engine dependency before bundling or redistributing it.

## cTrader

Current cTrader Algo supports custom indicators in C# and Python on Windows/Mac. Python indicators keep parameters/outputs in a C# attribute file and the logic in `<Name>_main.py` (`initialize` / `calculate`). BSV ships C# starters plus a Python target (`ctrader-python`) that prints the attribute file in its header comments, and a two-file EMA/ATR Python starter. None of these has been built in cTrader by BSV yet.

Official docs:
- https://help.ctrader.com/ctrader-algo/documentation/indicators/
- https://help.ctrader.com/ctrader-algo/how-tos/indicators/create-an-indicator/
- https://help.ctrader.com/ctrader-algo/documentation/python-basics/
- Official Python samples (MIT): https://github.com/spotware/ctrader-python-algo-samples

## MT4

MQL4 custom indicators use series-indexed buffers (`SetIndexBuffer`) and built-in indicator functions (`iMA`, `iRSI`, `iATR`). The `mql4` target computes EMA/SMA/RSI/ATR, cross/threshold/combine signals, plots and once-per-closed-bar `Alert()`; session filters use broker server time and stay marked TODO for timezone conversion.

Official docs:
- https://docs.mql4.com/customind

## Bookmap

Bookmap's Python API (open beta, MIT) exposes trade/depth handlers, a 0.1-second interval handler and custom indicator lines (`register_indicator` / `add_point`). Bookmap has no classic OHLC bar loop, so the `bookmap-python` target builds time bars from trades and evaluates the recipe when each bar closes. Depth/heatmap-specific order-flow blocks are not implemented yet.

Official docs:
- https://github.com/BookmapAPI/python-api

## Quantower

Quantower Algo custom indicators derive from `Indicator`, can add line series, access chart prices and publish values from `OnUpdate`.

Official starter:
- https://help.quantower.com/quantower/quantower-algo/simple-indicator

## Sierra Chart

ACSIL custom studies expose `sc.Input` settings and `sc.Subgraph` output arrays; BSV's first starter is intentionally read-only/visual.

Official reference:
- https://www.sierrachart.com/index.php?page=doc/AdvancedCustomStudyInterfaceAndLanguage.php

## GoCharting

GoCharting's Lipi language is a real indicator/chart scripting path. BSV should exploit it for lightweight copy/paste indicators while respecting its current scope.

Official docs:
- https://gocharting.com/docs/scripting

## OpenMarkets

The current OpenMarkets developer surface exposes market data through REST/WebSocket/MCP. BSV should treat it as a data/agent integration building block, not falsely label it as a chart scripting language.

Official developer surface:
- https://openmarkets.ai/developers
- https://app.openmarkets.ai/developers/mcp

## Rule

Never mark a platform implementation Verified merely because the source exists or CI parsed it. Runtime/build evidence must identify the exact platform/version and exact source revision.
