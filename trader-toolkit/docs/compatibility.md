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
| ATAS | C# indicator API (`ATAS.Indicators`) | generator target (`atas`: `Indicator` with `OnCalculate`, `GetCandle`, `ValueDataSeries` lines, closed-bar `AddAlert`; EMA/SMA/RSI/ATR computed in the code; no orders) | Compiles with the .NET 8 C# compiler against BSV stubs written from the ATAS API reference; ATAS build and chart test still required |
| AmiBroker | AFL (AmiBroker Formula Language) | generator target (`amibroker`: indicator formula with `MA`/`EMA`/`RSIa`/`ATR`, explicit cross comparisons with `Ref`, `Plot`, completed-bar `AlertIf`; no `Buy`/`Sell`/`Short`/`Cover`) | Checked by a BSV AFL-subset parser/evaluator (`check_amibroker_afl.mjs`); AmiBroker verification still required |
| thinkorswim | thinkScript | generator target (`thinkscript`: study with `ExpAverage`/`Average`/`WildersAverage`/`TrueRange`, explicit cross comparisons, plots, `Alert(cond[1], …, Alert.BAR)`; no `AddOrder`) | Checked by a BSV thinkScript-subset parser/evaluator (`check_thinkscript.mjs`); thinkorswim verification still required |
| Tradovate | Custom indicators (JavaScript) | generator target (`tradovate`: `module.exports` indicator, `Calculator.init`/`map(d, index)`, EMA/SMA/RSI/ATR computed in the generated code, `predef.plotters.singleline`/`dots`, closed-bar alert dots via `shifts`; no orders, no network calls) | Checked by running the output in node:vm against a BSV stub of the documented API (`check_tradovate.mjs`); Tradovate verification still required |
| backtrader | Python library (backtesting / research) | generator target (`backtrader`: `bt.Indicator` with plot and alert lines, `bt.ind.EMA`/`SMA`/`RSI(safediv=True)`/`ATR`, `BsvAlerts` strategy printing ALERT lines on completed bars, `GenericCSVData` loader; no orders, no network calls) | Executed by BSV in the backtrader library (1.9.78.123) on synthetic bars (`check_backtrader.py`); not a broker or live-feed run, runtime verification still required |
| Backtesting.py | Python library (backtesting / research) | generator target (`backtesting-py`: alert-only `Strategy`, indicators and signals computed in `init()` with numpy from bars 0..i only, `next()` prints ALERT lines on completed bars, pandas CSV loader; no orders, no network calls) | Executed by BSV in the Backtesting.py library (0.6.6) on synthetic bars (`check_backtesting_py.py`); not a broker or live-feed run, runtime verification still required |
| NautilusTrader | Python library (backtesting / live framework, 1.x API) | generator target (`nautilus`: alert-only `Strategy` + frozen `StrategyConfig`, pure-Python EMA/SMA/RSI/ATR updated in `on_bar()` from bars 0..i, ALERT lines on completed bars, csv-module CSV loader, `BacktestEngine` on the test EUR/USD instrument; no orders, no network calls) | Executed by BSV in the NautilusTrader library (1.231.0) on synthetic bars (`check_nautilus.py`); not a broker, venue or live-feed run, runtime verification still required |
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

## ATAS

ATAS custom indicators are C# classes that derive from `ATAS.Indicators.Indicator` and override `OnCalculate(int bar, decimal value)`, which runs for every history bar and then on every tick of the last bar. `GetCandle(bar)` returns the candle (Open/High/Low/Close, `Time` = candle open time), `CurrentBar` is the bar count, lines are `ValueDataSeries` in `DataSeries`, a separate pane is `Panel = IndicatorDataProvider.NewPanel`, and `AddAlert(soundFile, message)` raises an alert.

The `atas` target (builder, CLI and a pre-generated starter on every recipe page since cycle 10) writes one `Indicator` class. EMA/SMA/RSI/ATR are computed in the generated code (EMA and Wilder RMA seeded with the simple mean, as in Pine), because the reference documents the core API but BSV could not confirm the built-in technical indicator classes there. Plots fill `ValueDataSeries`; alerts fire once per closed bar, only for bars that close after the indicator was loaded. Session filters treat the candle time as UTC and convert it to the recipe time zone (TODO in the code). It never calls order or strategy APIs.

Checked by BSV: all 14 recipe outputs compile with the .NET 8 C# compiler (nullable on, warnings as errors) against stub classes written from the public API reference (`scripts/site/check_atas_stubs.sh`, stubs in `scripts/site/atas_stubs/`). A one-off replay on the box against those stubs with 300 synthetic bars matched a JavaScript reference for EMA/RSI/ATR. Not built against the real ATAS assemblies and not loaded in ATAS.

- https://docs.atas.net/en/md_DataFeedsCore_2Docs_2en_20010__BasicIndicator.html
- https://docs.atas.net/en/classATAS_1_1Indicators_1_1BaseIndicator.html
- https://docs.atas.net/en/classATAS_1_1Indicators_1_1ExtendedIndicator.html
- https://docs.atas.net/en/classATAS_1_1Indicators_1_1IndicatorCandle.html
- https://docs.atas.net/en/md_DataFeedsCore_2Docs_2en_20050__Dataseries.html

## AmiBroker

Generator target since cycle 10 (`amibroker`): builder and CLI, and since cycle 11 a pre-generated starter on every recipe page and in the platform lists. Status: UNTESTED_RUNTIME.

The target writes one AFL indicator formula, using only functions checked in the AFL function reference: `MA`, `EMA`, `RSIa`, `ATR`, `Ref`, `TimeNum`, `BarIndex`, `LastValue`, `Plot`, `AlertIf`. Crosses are explicit comparisons with `Ref(x, -1)`, the same cross rule as the other targets. Alerts follow the guide's completed-bar pattern (`BarIndex() < LastValue(BarIndex())`), with `lookback = 2` so the most recent completed bar is checked, and they go to the Alert Output window. It never assigns `Buy`/`Sell`/`Short`/`Cover` and places no orders. Session filters use `TimeNum()` in the database time zone (TODO in the code).

Checked by BSV: `scripts/site/check_amibroker_afl.mjs` parses every recipe's output with a small BSV-written AFL-subset parser. It checks that only the documented functions/constants are used, that names are assigned before use, that `Ref` only looks back, and that there are no order arrays. It then evaluates the formula over 400 synthetic bars: MA/EMA/RSI/ATR match an independent JS reference once warmed up, and a bar-by-bar replay shows alerts only on completed bars, once each, with no misses. This is not AmiBroker: nothing was verified or run in AmiBroker by BSV.

Sources:
- https://www.amibroker.com/guide/afl/ma.html, ema.html, rsi.html, atr.html, ref.html, timenum.html, plot.html, alertif.html
- https://www.amibroker.com/guide/h_alerts.html (completed-bar alerts)
- https://www.amibroker.com/guide/a_language.html (operators, identifiers, colors)
- https://www.amibroker.com/guide/h_indbuilder.html (Formula Editor, Apply indicator)

## thinkorswim (thinkScript)

Generator target since cycle 11 (`thinkscript`): builder, CLI and a pre-generated starter on every recipe page. Status: UNTESTED_RUNTIME.

The target writes one thinkScript study, using only functions and constants checked in the thinkScript reference: `ExpAverage`, `Average`, `WildersAverage`, `Max`, `TrueRange`, `SecondsFromTime`, `SecondsTillTime`, `Alert`, `Alert.BAR`, `Sound.Ding`, `Color.*`, `Double.NaN`, `yes`/`no`, `def`, `plot`, `declare lower`, `if … then … else` and `[n]` past offsets. RSI is Wilder's RSI built from `WildersAverage` of gains and losses, and ATR is `WildersAverage(TrueRange(high, close, low), n)`. Crosses are explicit comparisons with `[1]`, the same cross rule as the other targets. `Alert()` reads its condition at the last real bar, which is still forming, so the generated alerts use `condition[1]` (the bar that just closed) with `Alert.BAR` (at most once per bar). It never calls `AddOrder`, so it is a study, not a strategy. Session filters use `SecondsFromTime`/`SecondsTillTime`, which count in US Eastern time (EST in the reference) and return 0 on daily or higher charts (TODO in the code). Separate-pane recipes use `declare lower`.

Checked by BSV: `scripts/site/check_thinkscript.mjs` parses every recipe's output with a small BSV-written thinkScript-subset parser. It checks that only the documented functions/constants are used, that names are defined before use, that offsets only look back, that there is no `AddOrder`, and that `declare lower` is present only for separate-pane recipes. It then evaluates the study over 1,200 synthetic bars, following the reference formulas (`ExpAverage` seeded with the first value, `WildersAverage` with the first SMA): EMA/SMA/RSI/ATR match an independent JS reference once warmed up. A bar-by-bar replay of the last 100 bars shows alerts only for closed bars (moving the forming bar's prices never changes them), once per bar, with no misses. Negative tests (an undocumented function, a forward offset, an alert on the forming bar, a wrong `declare lower`) all fail. This is not thinkorswim: nothing was verified or run in thinkorswim by BSV.

Sources:
- https://tlc.thinkorswim.com/center/reference/thinkScript/Functions/Tech-Analysis/ExpAverage (also Average, WildersAverage, TrueRange)
- https://tlc.thinkorswim.com/center/reference/thinkScript/Functions/Others/Alert, …/Constants/Alert/Alert-BAR, …/Constants/Sound
- https://tlc.thinkorswim.com/center/reference/thinkScript/Functions/Date---Time/SecondsFromTime (also SecondsTillTime)
- https://tlc.thinkorswim.com/center/reference/thinkScript/Reserved-Words/plot (also def, declare, if, yes, no, crosses), …/Declarations/lower
- https://toslc.thinkorswim.com/center/howToTos/thinkManual/charts/Using-Studies-and-Strategies (Edit studies… > Create… / Import…)

## Tradovate (JavaScript custom indicators)

Generator target since 2026-10-04 (`tradovate`): builder, CLI and a pre-generated starter on every recipe page. Status: UNTESTED_RUNTIME.

The target writes one custom indicator as documented at tradovate.github.io/custom-indicators: `module.exports` with `name`, `description`, `calculator`, `params`, `inputType: "bars"`, `areaChoice`, `tags`, `plots`, `plotter`, `shifts` and `schemeStyles`, and a calculator class with `init()` and `map(d, index)` that reads `d.open()`/`high()`/`low()`/`close()`/`timestamp()`. EMA, SMA, RSI (Wilder) and ATR are computed in the generated code, seeded with the simple average of the first bars, so the only `require` is `./tools/predef` for `plotters.singleline`/`dots`. State is kept per bar index, so a repeated `map()` call for the forming bar recomputes that bar from the closed one before it. The published API has no alert call, so each alert condition is a dot plot (`A1`, `A2`, …) shifted onto the bar that just closed; notifications are left to the user. Session filters convert the bar time with `Intl.DateTimeFormat` to the recipe time zone. No orders, no network calls.

Checked by BSV: `scripts/site/check_tradovate.mjs` runs every recipe's output in a bare node:vm context against a BSV stub of the documented API. It checks the exported fields and values, that only predef is required, that there are no network, eval, timer or order calls, that EMA/SMA/RSI/ATR equal an independent reference on every bar (and stay empty while warming up), that signals and session filters equal an independent reference, that re-running the forming bar with other prices changes nothing, and that alert dots appear only on closed bars, once per bar, with no misses. Deliberately broken outputs (alert on the forming bar, wrong Wilder average, inclusive session end) all fail. This is not Tradovate: nothing was verified or run in Tradovate by BSV.

Sources:
- https://tradovate.github.io/custom-indicators/ (Indicator, Calculator, BarInputEntity, Plots, ParameterDefinitions interfaces)
- https://tradovate.github.io/custom-indicators/pages/Tutorial/ExponentialMovingAverage.html, …/DoubleEMA.html, …/SignalingATR.html, …/Alligator.html (shifts)
- https://community.tradovate.com/t/is-it-possible-creating-own-indicators-like-in-tv/3050 (Code Explorer module)

## backtrader (Python)

Generator target since 2026-10-04 (`backtrader`): builder, CLI and a pre-generated starter on every recipe page. Status: UNTESTED_RUNTIME.

The target writes one Python file for the open-source backtrader library: an indicator class (`bt.Indicator`) with one line per plot (`p1`, `p2`, …) and one line per alert condition (`a1`, `a2`, …; the close when the condition holds, NaN otherwise), built from `bt.ind.EMA`, `bt.ind.SMA`, `bt.ind.RSI` (Wilder smoothing, `safediv=True`) and `bt.ind.ATR`. Signals, crosses and session filters are evaluated in `next()` (also during warm-up via `prenext()`); session filters read the bar time as UTC and convert it with `zoneinfo` to the recipe time zone. A `BsvAlerts` strategy prints `ALERT <bar time> <message>` for each completed bar where an alert condition holds and places no orders. `main()` loads a CSV with a header row (`datetime,open,high,low,close,volume`, time as `YYYY-MM-DD HH:MM:SS` in UTC) through `GenericCSVData` and runs bar by bar (`runonce=False`); `--plot` draws the lines with matplotlib. Only `math`, `sys`, `datetime`, `zoneinfo` and `backtrader` are imported. No orders, no network calls.

Checked by BSV: `scripts/site/check_backtrader.py` imports every recipe's output and runs it inside backtrader 1.9.78.123 on 1200 synthetic 15-minute bars. It checks the imports, that there are no order calls (`buy`, `sell`, `close`, `order_target_*`, brackets) and no eval/exec/file/network calls, one `next()` per bar, that EMA/SMA/RSI/ATR equal an independent reference on every bar (and stay NaN while warming up), that signals and session filters equal an independent reference, that the plot lines carry the referenced values, that the output lines are identical with `runonce=True` and `runonce=False`, and that running the file as a script on a CSV prints exactly one ALERT line per completed bar where the condition holds, with no misses. A deliberately broken output (SMA in place of EMA) fails. This is a library run on made-up data: nothing was run against a broker, a live feed or real market data by BSV.

Sources:
- https://www.backtrader.com/docu/inddev/ (developing an indicator: lines, `next()`, `prenext()`)
- https://www.backtrader.com/docu/indautoref/ (ExponentialMovingAverage, SimpleMovingAverage, RSI `safediv`, AverageTrueRange)
- https://www.backtrader.com/docu/datafeed/ (GenericCSVData parameters)

## Backtesting.py (Python)

Generator target since 2026-10-04 (`backtesting-py`): builder, CLI and a pre-generated starter on every recipe page. Status: UNTESTED_RUNTIME.

The target writes one Python file for the open-source Backtesting.py library: a `Strategy` subclass whose `init()` computes EMA, SMA, RSI (Wilder, seeded with the simple average; 100 with no down moves, 50 when flat) and ATR (Wilder) with numpy, then the crosses, thresholds, combines and session filters as arrays in which bar i only uses bars 0..i. Plot lines are registered with `self.I()`; alert conditions are registered as scatter markers. `next()` prints `ALERT <bar time> <message>` for the bar that just completed and places no orders. Backtesting.py itself starts calling `next()` once every plotted line has a value and never on the first bar, so alerts on earlier bars are not printed; the starter says so in its header. Session filters read the bar time as UTC and convert it with pandas to the recipe time zone. `main()` reads a CSV with a header row (`datetime,open,high,low,close,volume`, time as `YYYY-MM-DD HH:MM:SS` in UTC) and runs `Backtest(...).run()`; `--plot` writes the Bokeh HTML chart. Only `sys`, `numpy`, `pandas` and `backtesting` are imported. No orders, no network calls.

Checked by BSV: `scripts/site/check_backtesting_py.py` imports every recipe's output and runs it inside Backtesting.py 0.6.6 on 1200 synthetic 15-minute bars. It checks the imports, that there are no order or position calls and no eval/exec/file/network calls, that the run makes 0 trades, that EMA/SMA/RSI/ATR equal an independent reference on every bar (shared with the backtrader check, `bsv_py_reference.py`), that signals and session filters equal the reference, that the plot lines carry the referenced values, that a run on the first 700 bars gives exactly the prefix of the full run (no look-ahead), that `next()` is called once per bar from Backtesting.py's warm-up start, and that running the file as a script on a CSV prints exactly one ALERT line per qualifying completed bar from that start, with no misses. A deliberately broken output that reads the next bar fails the look-ahead check. This is a library run on made-up data: nothing was run against a broker, a live feed or real market data by BSV.

Sources:
- https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html (Strategy.init, Strategy.I, Strategy.next, Backtest.run)
- https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html (data format, indicators, warm-up)

## NautilusTrader (Python)

Generator target since 2026-10-04 (`nautilus`): builder, CLI and a pre-generated starter on every recipe page. Status: UNTESTED_RUNTIME.

The target writes one Python file for the open-source NautilusTrader 1.x Python API: a frozen `StrategyConfig` with the bar type and a `Strategy` subclass that subscribes to bars in `on_start()`. EMA, SMA, RSI (Wilder, seeded with the simple average; 100 with no down moves, 50 when flat) and ATR (Wilder) are small pure-Python classes updated once per bar in `on_bar()`, so the values for bar i only use bars 0..i; crosses, thresholds, combines and session filters are evaluated on the same completed bar. `on_bar()` prints `ALERT <bar time> <message>` and places no orders. NautilusTrader has no chart in this setup: plot blocks are kept as values in the strategy. Session filters read the bar time as UTC and convert it with zoneinfo to the recipe time zone. `main()` reads a CSV with a header row (`datetime,open,high,low,close,volume`, time as `YYYY-MM-DD HH:MM:SS` in UTC) with the csv module, builds `Bar` objects for NautilusTrader's test EUR/USD instrument (5 price decimals) and a 15-minute bar type, and runs a `BacktestEngine` on a simulated venue; replace `INSTRUMENT` / `BAR_SPEC` for your own data. Only `csv`, `math`, `sys`, `collections`, `datetime`, `zoneinfo` and `nautilus_trader` are imported; the only file access is reading the CSV you pass. No orders, no network calls. Written for NautilusTrader 1.x (`pip install "nautilus_trader<2"`); the 2.0 release candidates change the `StrategyConfig` API and are not checked.

Checked by BSV: `scripts/site/check_nautilus.py` imports every recipe's output and runs it inside NautilusTrader 1.231.0's `BacktestEngine` on 1200 synthetic 15-minute bars (rounded to 5 decimals). It checks the imports, that there are no order or position calls and no eval/exec/network calls, that the run creates 0 orders, that `on_bar()` runs once per bar and receives the prices unchanged, that EMA/SMA/RSI/ATR equal an independent reference on every bar (shared with the backtrader and Backtesting.py checks, `bsv_py_reference.py`), that signals and session filters equal the reference, that plot values carry the referenced values, that a run on the first 700 bars gives exactly the prefix of the full run (no look-ahead), and that running the file as a script on a CSV prints exactly one ALERT line per qualifying completed bar, with no misses. A deliberately broken EMA fails the reference check. This is a library run on made-up data: nothing was run against a broker, a venue, a live feed or real market data by BSV.

Sources:
- https://nautilustrader.io/docs/latest/concepts/strategies (Strategy, on_start, on_bar, StrategyConfig)
- https://nautilustrader.io/docs/latest/concepts/backtesting (BacktestEngine, venues, data)
- https://pypi.org/project/nautilus_trader/ (1.231.0 stable; 2.0 release candidates)
