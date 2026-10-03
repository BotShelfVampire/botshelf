# Platform compatibility

Status is about the current BSV Trader Tool Blocks implementation, not the platform's overall capability.

| Platform | Extensibility path | Current BSV asset | Status |
| --- | --- | --- | --- |
| TradingView | Pine Script | generator target + 6 copy/paste Pine starters | Source prepared; runtime compile still required |
| MT5 | MQL5 | generator target (`mql5`: computes EMA/SMA/RSI/ATR, cross/threshold/combine, plots, closed-bar alerts) + EMA/ATR overlay source | Source prepared; runtime compile still required |
| cTrader | C# or Python custom indicators in cTrader Algo | C# and Python generator targets (both compute indicators, signals, plots and closed-bar alerts) + EMA/ATR (C# and Python) + RSI source | Source prepared; runtime build still required |
| Vela | JavaScript/TypeScript chart library + optional scripting engines | generator target (`vela`: a small BSV `ScriptingEngine` in plain JS, line series, signal markers, closed-bar alerts) + runnable custom web-chart starter | Generated starters for 7 recipes mounted without errors in headless Chrome against @luxalgo/vela 0.8.1 with synthetic bars (smoke test only); not tested with live data or by users |
| NinjaTrader | NinjaScript/C# | generator target (`ninjatrader`: built-in EMA/SMA/RSI/ATR, cross/threshold/combine, plots, closed-bar `Alert()`) + EMA/ATR overlay source | Source prepared; runtime compile still required |
| Quantower | C# Quantower Algo | generator target (`quantower`: built-in indicators, cross/threshold/combine, line series, closed-bar log alerts) + simple SMA source | Source prepared; runtime compile still required |
| Sierra Chart | ACSIL/C++ | generator target (`sierra-acsil`: ACSIL moving averages/RSI/ATR, cross/threshold/combine, subgraphs, closed-bar `sc.AddAlertLine`) + EMA overlay custom-study source | Source prepared; runtime build still required |
| GoCharting | Lipi scripting | generator target (`gocharting-lipi`: talib indicators, cross/threshold/combine, plots, `alertcondition` + closed-bar `alert()`) + dual-EMA Lipi source | Source prepared; Lipi-editor validation still required |
| MT4 | MQL4 | generator target (`mql4`) + EMA/ATR overlay source | Source prepared; runtime compile still required |
| Bookmap | Python API (open beta) and Java add-ons/API | Python generator target (`bookmap-python`, time bars built from trades) + trade-EMA add-on source; order-flow blocks still planned | Source prepared; runtime test still required |
| MotiveWave | Java SDK | generator target (`motivewave`: `Study` with `DataSeries.ema/sma/atr`, Wilder RSI via `smma`, paths, closed-bar `ctx.signal`) + EMA custom-study source | Compiles with javac 21 against BSV stubs written from the SDK javadoc; real SDK build and MotiveWave load still required |
| JForex (Dukascopy) | JForex API (Java `IStrategy`) | generator target (`jforex`: `IIndicators.ema/sma/rsi/atr` at bar shifts, closed-bar `onBar`, console values and notifications; no `IEngine`/orders) | Compiles with javac 21 against BSV stubs written from the JForex API javadoc; JForex platform compile and demo run still required |
| TradeStation | EasyLanguage | generator target (`easylanguage`: indicator with `XAverage`/`Average`/`RSI`/`AvgTrueRange`, explicit cross comparisons, `PlotN`, `Alert` on `BarStatus(1) = 2`; no orders) | Structural check by BSV only (`check_easylanguage_output.mjs`); TradeStation Verify and chart test still required |
| ProRealTime | ProBuilder | generator target (`prorealtime`: built-in averages/RSI/ATR, `CROSSES OVER/UNDER`, `RETURN` lines, arrow markers on overlays) + dual-EMA copy/paste indicator | Source prepared; runtime validation required |
| ATAS | platform extensibility research | planned | Unverified |
| OpenMarkets | REST/WebSocket/MCP data APIs, not a chart-script replacement | data/agent integration notes | API surface confirmed; no BSV runtime adapter yet |

## Vela

Vela is especially relevant to the BSV goal of letting a user build a custom chart surface rather than only paste an indicator into a closed charting UI.

Official project/docs:
- https://github.com/LuxAlgo/Vela
- https://docs.luxalgo.com/vela/user/quickstart
- https://docs.luxalgo.com/vela/user/scripting-engines

Vela itself is a charting library and does not ship a scripting engine. Engines are opt-in. Review the license of any scripting-engine dependency before bundling or redistributing it.

The `vela` generator target avoids the Pine addon (whose runtime, `pinets`, is AGPL-3.0). It writes one ES module with the recipe compiled to plain JavaScript (SMA-seeded EMA, SMA, Wilder RSI/ATR, crosses, thresholds, combines, `Intl` session filters in the recipe time zone) and a minimal engine on Vela's `ScriptingEngine` port (`language: 'bsv-recipe'`, static runs, ids from `stableSeriesId`). Plots become line series; overlay signals become triangle label markers; alerts go to `handle.on('alert')` only for bars that close after the first run. Only `@luxalgo/vela` (Apache-2.0) is imported. No network requests, no orders.

Checked by BSV: `scripts/site/test_vela_engine.mjs` (offline, all 14 recipes: model shape, stable ids, markers, closed-bar alerts) and a headless Chrome smoke test that mounted 7 generated starters on the real `vela.global.js` 0.8.1 with synthetic bars (lines and markers drew, 0 console errors). Not tested with live data feeds.

- https://docs.luxalgo.com/vela/contributing/adding-an-engine

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

## NinjaTrader 8

NinjaScript indicators derive from `Indicator`, declare plots with `AddPlot` in `State.SetDefaults`, create built-in indicators (`EMA`, `SMA`, `RSI`, `ATR`) in `State.DataLoaded` and compute in `OnBarUpdate` with `Calculate.OnBarClose`. The `ninjatrader` target follows that layout; `Alert()` only fires in real time (State.Realtime), and session filters use the chart's time zone setting, so they stay marked TODO. Not compiled in NinjaTrader by BSV yet.

- https://ninjatrader.com/support/helpguides/nt8/indicator.htm
- https://ninjatrader.com/support/helpguides/nt8/alert.htm

## Quantower

Quantower Algo custom indicators derive from `Indicator`, can add line series, access chart prices and publish values from `OnUpdate`.

Official starter:
- https://help.quantower.com/quantower/quantower-algo/simple-indicator
- https://help.quantower.com/quantower/quantower-algo/built-in-indicators
- https://api.quantower.com/docs/TradingPlatform.BusinessLayer.BuiltInIndicators.html

The `quantower` target creates built-in indicators with `Core.Indicators.BuiltIn` (`EMA`, `SMA`, `RSI`, `ATR`) and `AddIndicator`, publishes line series with `SetValue`, and logs once per closed bar on `UpdateReason.NewBar`. Not compiled in Quantower by BSV yet.

## Sierra Chart

ACSIL custom studies expose `sc.Input` settings and `sc.Subgraph` output arrays; BSV's first starter is intentionally read-only/visual.

The `sierra-acsil` target writes one `SCSFExport` study function with `AutoLoop = 1`: visible plot subgraphs first, hidden (`DRAWSTYLE_IGNORE`) indicator subgraphs computed with `sc.ExponentialMovAvg`, `sc.SimpleMovAvg`, `sc.RSI` and `sc.ATR`, and alerts on the last closed bar via `sc.AddAlertLine`, de-duplicated with a persistent int. Session filters use bar time in the chart's time zone and stay marked TODO. Not compiled in Sierra Chart by BSV yet.

- https://www.sierrachart.com/index.php?page=doc/ACSIL_Members_Functions.html
- https://www.sierrachart.com/index.php?page=doc/ACSILProgrammingConcepts.html

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

## ProRealTime

ProBuilder personal indicators are created in ProRealTime (Indicators > New > Creation by programming) and validated in the editor.

The `prorealtime` target writes a ProBuilder personal indicator with underscore-free variable names, built-in `ExponentialAverage`, `Average`, `RSI` and `AverageTrueRange`, `CROSSES OVER/UNDER`, and ends with `RETURN ... COLOURED(r,g,b) AS "..."`. Recipes drawn on the price chart show signals with `DRAWARROWUP`/`DRAWARROWDOWN` markers; ProRealTime alerts are created in the platform on an indicator line, so a second indicator that returns 0/1 is suggested in a TODO. Not validated in ProRealTime by BSV yet.

- https://www.prorealcode.com/documentation/probuilder/
- https://www.prorealtime.com/en/pdf/probuilder.pdf

## GoCharting

Lipi is GoCharting's chart scripting language: indicators only (no orders, no other symbols or timeframes). Blocks use braces, `static` (not `var`) persists values, and chart-output calls must be at the top level.

The `gocharting-lipi` target declares `indicator(title, "BSV", overlay)`, computes `talib.ema`, `talib.sma`, `talib.rsi` and `talib.atr`, uses `talib.crossover/crossunder` for crosses, and draws `plot` lines. Each alert block becomes an `alertcondition` (offered in the alert dialog) plus `if <signal>[1] { alert(...) }`, which fires on realtime bars once per closed bar; overlays add `plotshape` markers. Session filters compute minutes of day with `hour(time, tz)` / `minute(time, tz)` in the recipe time zone. Not checked in the Lipi editor by BSV yet.

- https://gocharting.com/docs/scripting
- https://gocharting.com/docs/scripting/automation/alerts
- https://gocharting.com/docs/scripting/reference/function-index

## MotiveWave

MotiveWave custom studies are Java classes that extend `Study`, carry a `@StudyHeader`, declare settings and paths in `initialize(Defaults)` and fill values in `calculate(int index, DataContext ctx)`.

The `motivewave` target writes one `Study` class: `DataSeries.ema/sma(index, period, Enums.BarInput.*)` and `atr(index, period)` for indicators (hl2 = `MIDPOINT`, hlc3 = `TP`, ohlc4 = `WP`), a Wilder RSI from per-bar gains/losses smoothed with `smma`, one `PathDescriptor` + `declarePath` per plot, and one `declareSignal` + `ctx.signal(...)` per alert, raised only when `isBarComplete(index)`. Session filters convert the bar start time with `java.time` in the recipe time zone. No orders.

Checked by BSV: all 14 recipes compile with javac 21 against stub classes written from the public javadoc signatures. Not built against the real SDK jar and not loaded in MotiveWave yet.

- https://www.motivewave.com/sdk/javadoc/com/motivewave/platform/sdk/study/Study.html
- https://www.motivewave.com/sdk/javadoc/com/motivewave/platform/sdk/common/DataSeries.html
- https://www.motivewave.com/sdk/javadoc/com/motivewave/platform/sdk/common/DataContext.html

## JForex (Dukascopy)

JForex strategies are Java classes that implement `IStrategy` (`onStart`, `onTick`, `onBar`, `onMessage`, `onAccount`, `onStop`). Indicator values come from `IContext.getIndicators()`; `IIndicators.ema/sma/rsi(instrument, period, side, AppliedPrice, timePeriod, shift)` and `atr(instrument, period, side, timePeriod, shift)` return the value for a bar `shift` back (0 = forming bar).

The `jforex` target writes one `IStrategy` class with `@Configurable` instrument (default EURUSD), period (default 1 hour) and offer side (default BID). In `onBar` it filters to that instrument/period and evaluates the recipe at shift 1 (the bar that just closed) and shift 2 (for crosses). Plots are printed to the console (`IConsole.getOut()`, switchable), alerts go to `IConsole.getNotif()`. Price sources hl2/hlc3 map to `MEDIAN_PRICE`/`TYPICAL_PRICE`; `AppliedPrice` has no OHLC/4, so indicators on ohlc4 are left as a visible TODO. Session filters read the bar start time (`IBar.getTime()`) with `java.time` in the recipe time zone. The strategy never calls `IEngine` and places no orders.

Checked by BSV: all 14 recipes compile with javac 21 against stub classes written from the public JForex API javadoc (`scripts/site/check_jforex_stubs.sh`, stubs in `scripts/site/jf_stubs/`). Not compiled in the JForex platform and not run on a demo account yet.

- https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IStrategy.html
- https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IIndicators.html
- https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IHistory.html
- https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IConsole.html

## TradeStation (EasyLanguage)

EasyLanguage indicators are plain text documents created in the TradeStation Development Environment (New > Indicator) and checked with Verify. Each statement runs once per bar (and per tick on the last bar); `Vars:` declares series variables, `XAverage(Price, Length)`, `Average(Price, Length)`, `RSI(Price, Length)` and `AvgTrueRange(Length)` are built-in functions, `PlotN(Value, "Name")` draws plots 1–99, and `Alert("text")` raises an alert when alerts are enabled in the indicator properties (only on the last bar).

The `easylanguage` target writes one indicator: one typed variable per block (`double V_<id>`, `bool S_<id>`), the four built-in functions for indicators (hl2/hlc3/ohlc4 written as price formulas), crosses as explicit comparisons with the previous bar (`a > b and a[1] <= b[1]`, the same rule as the other targets; EasyLanguage's `Crosses Over` treats flat stretches differently), thresholds/combines as boolean expressions, one `PlotN` per plot and one `if BarStatus(1) = 2 and ... then Alert(...)` per alert, so alerts fire on the closing tick. Session filters compare `Time` (bar close time, HHMM, chart time zone) and keep a TODO to convert the recipe time zone. Unsupported blocks stay as visible TODO comments. It is an indicator: no strategy order words are generated.

Checked by BSV: `scripts/site/check_easylanguage_output.mjs` checks all 14 recipe outputs for balanced comments/parentheses, statement terminators, declared variables, documented function names, plot numbers and alert length. That is a structural check, not a TradeStation Verify; the code has not been verified or run in TradeStation.

- https://help.tradestation.com/10_00/eng/tsdevhelp/elword/function/XAverage_function_.htm
- https://help.tradestation.com/10_00/eng/tsdevhelp/elword/function/RSI_Function_.htm
- https://help.tradestation.com/10_00/eng/tsdevhelp/elword/function/AvgTrueRange_Function_.htm
- https://help.tradestation.com/10_00/eng/tsdevhelp/elword/word/plot_reserved_word_.htm
- https://help.tradestation.com/10_00/eng/tsdevhelp/elword/word/alert_reserved_word_.htm
- https://help.tradestation.com/10_00/eng/tsdevhelp/elword/word/barstatus_reserved_word_.htm
