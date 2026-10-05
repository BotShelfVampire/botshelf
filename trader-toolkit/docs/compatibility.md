# Platform compatibility

Status is about the current BSV Trader Tool Blocks implementation, not the platform's overall capability.

| Platform | Extensibility path | Current BSV asset | Status |
| --- | --- | --- | --- |
| TradingView | Pine Script | generator target + 6 copy/paste Pine starters | Source prepared; runtime compile still required. Since 2026-10-04 the generator output is checked by a BSV Pine-subset evaluator (`check_pine.mjs`, not TradingView; see the TradingView section) |
| MT5 | MQL5 | generator target (`mql5`: computes EMA/SMA/RSI/ATR, cross/threshold/combine, ranges, breakouts, plots, closed-bar alerts; checked in a BSV model of the MT5 API, see below) + EMA/ATR overlay source | Source prepared; runtime compile still required |
| cTrader | C# or Python custom indicators in cTrader Algo | C# and Python generator targets (both compute indicators, signals, plots and closed-bar alerts) + EMA/ATR (C# and Python) + RSI source | Source prepared; runtime build still required |
| Vela | JavaScript/TypeScript chart library + optional scripting engines | generator target (`vela`: a small BSV `ScriptingEngine` in plain JS, line series, signal markers, closed-bar alerts) + runnable custom web-chart starter | Generated starters for 7 recipes mounted without errors in headless Chrome against @luxalgo/vela 0.8.1 with synthetic bars (smoke test only); not tested with live data or by users |
| NinjaTrader | NinjaScript/C# | generator target (`ninjatrader`: built-in EMA/SMA/RSI/ATR, cross/threshold/combine, pivots/sweep/divergence/zones, plots, closed-bar `Alert()`, symbol scan) + EMA/ATR overlay source | Source prepared; runtime compile still required |
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

## Higher timeframe (data.higher_timeframe + timeframeRef)

Correction (2026-10-04): earlier outputs on every target computed indicators marked with a higher timeframe on the chart timeframe, without saying so. Now:

- backtrader, Backtesting.py and NautilusTrader compute them from **closed higher-timeframe bars only**. Periods are aligned to UTC and bar times are read as bar-open times; a period is used only after a chart bar of the next period has arrived, so values never repaint or look ahead (a value can trail the period close by one chart bar). The script stops with an error if chart bars are not shorter than the higher timeframe. Timeframes: minutes (`"60"`) or days (`"D"`, up to `"7D"`).
- Pine v6, MQL5, MQL4, NinjaTrader 8, cTrader, AmiBroker and thinkorswim read the **last closed higher-timeframe bar** with the platform's officially documented idiom: Pine `request.security(syminfo.tickerid, tf, expr[1], lookahead = barmerge.lookahead_on)` ([manual: repainting](https://www.tradingview.com/pine-script-docs/concepts/repainting/)); MQL5 `CopyBuffer(handle, 0, iBarShift(...) + 1, 1, v)` on a handle created on the higher PERIOD ([iBarShift](https://www.mql5.com/en/docs/series/ibarshift), [CopyBuffer](https://www.mql5.com/en/docs/series/copybuffer)); MQL4 `iMA/iRSI/iATR(NULL, PERIOD_H1, ..., iBarShift(...) + 1)` ([iBarShift](https://docs.mql4.com/series/ibarshift), [iMA](https://docs.mql4.com/indicators/ima)); NinjaTrader 8 `AddDataSeries(BarsPeriodType.Minute, 60)` in State.Configure with `Calculate = Calculate.OnBarClose` forced there, the indicator on `Closes[1]`, stored per chart bar in BarsInProgress 0 ([Multi-Time Frame & Instruments](https://ninjatrader.com/support/helpGuides/nt8/multi-time_frame__instruments.htm), [AddDataSeries](https://ninjatrader.com/support/helpGuides/nt8/adddataseries.htm)); cTrader `MarketData.GetBars(TimeFrame.Hour)` with the indicator on that series, read at `k - 1` where `k = GetIndexByTime(chart bar open)` stepped back with `OpenTimes[k]` until that bar opened at or before the chart bar — the [reference](https://help.ctrader.com/ctrader-algo/references/Collections/DataSeries/TimeSeries/) does not say how GetIndexByTime rounds, so this is closed under any rounding (worst case one extra bar of lag); values stay empty unless the chart TimeFrame is strictly lower ([MarketData.GetBars](https://help.ctrader.com/ctrader-algo/references/MarketData/MarketData/), [TimeFrame](https://help.ctrader.com/ctrader-algo/references/Period/TimeFrame/)); the cTrader output is also compiled against BSV stubs (`check_ctrader_stubs.sh`); AmiBroker `TimeFrameSet(3600); H_x = Ref(EMA(Close, 50), -1); TimeFrameRestore(); TimeFrameExpand(H_x, 3600, expandFirst)` — the [guide's](https://www.amibroker.com/guide/h_timeframe.html) negative-shift construction — Null unless the chart interval is shorter, evaluated by BSV's AFL-subset checker against an hourly reference with a prefix (no-lookahead) test; thinkScript `def C_x = close(period = AggregationPeriod.HOUR); def E_x = ExpAverage(C_x, 50); def H_x = E_x[1];` — an expression of only secondary-aggregation variables keeps that aggregation, so `[1]` is the previous higher bar ([manual](https://toslc.thinkorswim.com/center/reference/thinkScript/tutorials/Advanced/Chapter-11---Referencing-Secondary-Aggregation): `High(period = AggregationPeriod.DAY)[1]` is the previous day) — empty unless `GetAggregationPeriod()` is shorter; BSV's thinkScript-subset checker models secondary contexts and runs the same reference and prefix tests. 45 minutes has no AggregationPeriod constant and stays a TODO there. The others stop with an error when the chart timeframe is not lower. Higher-timeframe bars follow TradingView's session / the broker's server time. MT4 accepts only its standard periods (M1, M5, M15, M30, H1, H4, D1, W1); MT5 its ENUM_TIMEFRAMES list; another timeframe stays a TODO stub there. BSV checks this pattern statically (`check_htf.py`) but cannot compile or run these platforms: **UNTESTED_RUNTIME**.
- Tradovate computes them the same way (closed bars only, UTC-aligned periods, bar-open times) in per-bar JavaScript state (`this.bars[i]`), so `map()` re-running for the forming bar changes nothing. If chart bars are not shorter than the higher timeframe, or bar times do not increase, the value stays empty (a custom indicator cannot stop with an error). `check_tradovate.mjs` (node:vm stub of the documented API, not Tradovate) compares every bar with an independent reference, catches a mutant that reads the forming higher-timeframe bar, and checks that a 15-minute "higher" timeframe on 15-minute bars gives no value. UNTESTED_RUNTIME.
- Every other target leaves those blocks as unsupported stubs with a TODO line (empty value, false signal). They are never computed on the chart timeframe.
- Weekly and monthly timeframes are unsupported on every target.

Checks: `check_backtrader.py`, `check_backtesting_py.py` and `check_nautilus.py` (every bar equals an independent reference; a run cut in the middle of a period prints the full-data values; coarse bars stop the script; three deliberately broken helpers are caught) and `check_htf.py` (all 22 targets; for Pine v6 / MQL5 / MQL4 a static closed-bar pattern check that must also catch 20 broken variants).

## Ranges and breakouts (structure.range, signal.breakout)

Since 2026-10-04 these are rendered on backtrader, Backtesting.py and NautilusTrader (the targets where a BSV library check runs them) and on Tradovate (per-bar state `this.bars[i]`; check_tradovate.mjs compares both range lines and the breakout with an independent run-by-run reference on every bar and catches a window-never-resets mutant; node:vm stub of the documented API, not Tradovate, UNTESTED_RUNTIME); every other target keeps the TODO line.

- `structure.range` (`track: ["high", "low"]`, `during`: a session or signal block): during each window where `during` is true, the high and low of the window's bars so far (including the bar that just closed); when a new window starts the values reset; after a window they keep the finished window's values until the next window starts. NaN before the first window.
- AmiBroker (since 2026-10-04): `R_<id>` = inside the window, `W_<id>` = its first bar, `V_<id>_high = ValueWhen(R_<id>, HighestSince(W_<id>, High))` (low likewise), breakout with `Ref(Close, -1)`; functions from the AFL guide. check_amibroker_afl.mjs (BSV AFL-subset evaluator, not AmiBroker) compares every 15-minute bar with a window reference written from the recipe session (bar times read as UTC, like the session TODO says), requires breakouts to fire, checks prefix runs (no lookahead) and catches a window-never-resets and a breakout-without-previous-close mutant. The range zone is drawn as two Plot lines (see the pivots and zones section).
- thinkorswim (since 2026-10-04): `R_<id>` = inside the window, `W_<id> = CompoundValue(1, R_<id> and R_<id>[1] == 0, R_<id>)`, `V_<id>_high = CompoundValue(1, if W_<id> then high else if R_<id> then Max(V_<id>_high[1], high) else V_<id>_high[1], if R_<id> then high else Double.NaN)` (low likewise with `Min`), breakout with `close[1]`. check_thinkscript.mjs (BSV thinkScript-subset evaluator, not thinkorswim) compares every 15-minute bar with a window reference written from the recipe session (bar times read in EST, like the session TODO says), requires breakouts to fire, checks prefix runs and catches a window-never-resets and a breakout-without-previous-close mutant. The evaluator accepts a variable that refers to itself only in this documented `CompoundValue` form with `[1]`; a bare self reference fails the static check (a mutant proves it).
- `signal.breakout` (`direction`: either / above / below): true on a closed bar outside the window whose close is beyond the finished window's high (or low) while the previous close was not. It can fire again if price comes back inside and crosses again; nothing fires during the window.
- Checks: every bar's range values and breakout signals equal an independent reference, alerts and value panels included.

## Pivots, zones and webhooks (structure.pivot, visual.zone, alert.webhook)

Since 2026-10-04 rendered on backtrader, Backtesting.py and NautilusTrader; `structure.pivot`, `visual.zone` (pivot or range source) and `alert.webhook` also on Tradovate (per-bar state, see below). `structure.pivot`, `visual.zone`, `signal.liquidity_sweep` and `signal.divergence` also on thinkorswim (since 2026-10-04: `P_<id>_h = X[right] > Highest(X[right + 1], left) and X[right] >= Highest(X, right)`, the held level with `CompoundValue(1, if P_<id>_h then X[right] else V_<id>_high[1], Double.NaN)`, the previous pivot is `V_<id>_high[1]` on the confirming bar, the oscillator at the previous pivot held the same way, a zone as two plots; check_thinkscript.mjs compares every 15-minute bar with the same independent reference as AmiBroker, checks prefix runs and catches 3 mutants; BSV thinkScript-subset evaluator, not thinkorswim) and on AmiBroker (since 2026-10-04: `P_<id>_h = Ref(X, -right) > Ref(HHV(X, left), -right - 1) AND Ref(X, -right) >= HHV(X, right)`, the held level with `ValueWhen`, the previous pivot with `ValueWhen(..., 2)`, a zone as two `Plot` lines; check_amibroker_afl.mjs compares every 15-minute bar with an independent reference, checks prefix runs and catches 3 mutants; BSV AFL-subset evaluator, not AmiBroker). Every other target keeps the TODO line.

- `structure.pivot` (`left`, `right`: 1–50; `source`: `close` or `high_low`): a pivot high is a bar whose value is strictly above the `left` bars before it and at least as high as the `right` bars after it (a flat top counts once, at its first bar); pivot lows mirror this. A pivot is published only on the bar `right` bars later (no lookahead) and the last confirmed pivot high / low is held (`<id>.high`, `<id>.low`).
- `visual.zone` (`source`: a pivot or a high/low range): two lines with the source's high and low (NautilusTrader: values only, no chart). Tradovate: a pivot zone is two lines `Z<n>H` / `Z<n>L` with the last confirmed pivot high / low (no box); check_tradovate.mjs compares them with its reference on every bar and catches a swapped-lines mutant.
- `alert.webhook` (`when`: a signal; `payload`: a flat JSON object): on each completed bar where `when` is true, the starter prints `WEBHOOK <time> <json>` with `{{symbol}}`, `{{timeframe}}`, `{{time}}`, `{{open}}`, `{{high}}`, `{{low}}`, `{{close}}` filled in (set `BSV_SYMBOL` / `BSV_TIMEFRAME`). It never sends anything; posting the payload is up to you. Other placeholders or nested payloads stay TODO. Tradovate (the indicator makes no network calls and has no print): the condition is drawn as dots `W<n>` on the bar that just closed, and that bar's JSON text is built in `this.bars[i - 1].J_<id>` with the same placeholders filled in (`{{time}}` as UTC `YYYY-MM-DDTHH:MM:SS`); check_tradovate.mjs compares every bar's payload and dots with a separately written fill and catches three mutants (close read from the open, payload from the bar before, dots on the forming bar).
- Checks: every bar's pivot values and zone lines equal an independent reference; the printed payloads equal the expected ones bar by bar; the 700-bar runs equal the prefix of the full run (no lookahead).

## Liquidity sweep and divergence (signal.liquidity_sweep, signal.divergence)

Since 2026-10-04 rendered on backtrader, Backtesting.py, NautilusTrader and Tradovate; every other target keeps the TODO line. Both are candidates for you to review, not trade signals.

- `signal.liquidity_sweep` (`pivot`: a structure.pivot; `atr`: an indicator.atr on the chart timeframe; `minAtrFraction`: 0–10, default 0): true on a completed bar whose high goes above the last pivot high known before this bar by at least `minAtrFraction` × this bar's ATR and whose close is back below that level, or the mirror for the last pivot low. False while the ATR or the level has no value. It can fire again on the same level.
- `signal.divergence` (`pivot`: a structure.pivot whose `left` / `right` / `source` define the price pivots; `oscillator`: an EMA, SMA, RSI or ATR on the chart timeframe; `price`: omitted or equal to the pivot's source; `direction`: `both`, `bearish` or `bullish`): regular divergence. Bearish = a newly confirmed pivot high above the previous pivot high while the oscillator at the new pivot bar is lower than at the previous one; bullish = a lower pivot low with a higher oscillator. True only on the bar that confirms the new pivot (`right` bars after it), so it never looks ahead.
- Checks: every bar of both signals equals an independent reference (pivots listed over the whole series, then compared pair by pair); the 700-bar runs equal the prefix of the full run; both fire on the synthetic bars; four helper mutants (no close back inside, no ATR distance, flipped oscillator test, dropped price test) are caught. Not run on a broker or live feed (UNTESTED_RUNTIME).
- Tradovate: each bar's pivot, sweep and divergence state is computed from the closed bars before it and the bar itself (`this.bars[i]`), so `map()` running again for the forming bar changes nothing already closed, and the alert dot reads the closed bar. check_tradovate.mjs (BSV stub of the documented API in node:vm, not Tradovate) compares pivot values and both signals with its own reference on every bar, replays live updates, and catches the same four mutants. `visual.zone` stays TODO on Tradovate.

## Value panels (visual.table)

Since 2026-10-04 the generator renders `visual.table` (a value panel: the listed fields' values on the latest completed bar) on 7 of the 22 targets. These are the targets where a BSV check covers the output:

| Target | How the panel is shown | What BSV checked |
| --- | --- | --- |
| backtrader | `stop()` prints `TABLE <title>` and one line per field for the last bar | executed in backtrader 1.9.78.123 on synthetic bars; values equal the shared Python reference (`check_backtrader.py`) |
| Backtesting.py | `main()` prints the panels for the last bar from `stats._strategy` | executed in Backtesting.py 0.6.6; values equal the reference (`check_backtesting_py.py`) |
| NautilusTrader | `run_backtest()` prints the panels after `engine.run()` | executed in NautilusTrader 1.231.0; values equal the reference (`check_nautilus.py`) |
| thinkorswim | one `AddLabel` per field; `[1]` because labels use the last real (forming) bar | BSV thinkScript-subset evaluator: label text carries the closed bar's value (`check_thinkscript.mjs`); not thinkorswim |
| AmiBroker | `printf` to the Interpretation window with `LastValue(Ref(x, -1))` and `NumToStr(…, 1.6, False)` | BSV AFL-subset evaluator: printed values for the last completed bar (`check_amibroker_afl.mjs`); not AmiBroker |
| Tradovate | not drawn: the published custom-indicator API has no panel or label call, so the fields are kept in per-bar state (`this.bars[i - 1].T_<id>` = the bar that just closed) | BSV stub of the documented API in node:vm: every bar's field values equal the reference, unchanged by forming-bar updates, and a panel that reads the bar before is caught (`check_tradovate.mjs`); not Tradovate |
| JForex | one console line per closed bar (shift 1), switch `logPanels` | compiles with javac 21 against the BSV JForex stubs only; not run |

A field is shown only when it and every block it depends on is rendered by the generator. A field that depends on a block that is not rendered yet, or on a higher timeframe, gets a TODO line instead of a value that would be wrong. When no field can be shown, the panel is left out with a TODO line. Of the 4 recipes with a panel, the panels that are not left out (counted from the generator output on 2026-10-04, after ranges, breakouts and closed-bar higher timeframes were added): backtrader, Backtesting.py, NautilusTrader, Tradovate and AmiBroker 4 (AmiBroker since ranges and breakouts were added there); thinkorswim 2; JForex 1. (Correction: this paragraph said earlier that only Volatility Regime Map could be shown; that was out of date.) On the other 15 targets `visual.table` is still a TODO (Pine, MQL5/MQL4 and the C# platforms have no BSV check for panel output yet). Runtime-tested by BSV: 0.

While adding the AmiBroker panel check, BSV found and fixed a bug in its own AFL-subset evaluator: `Ref(x, -1)` was evaluated as missing values, so earlier cross checks did not exercise crosses. Replayed alerts went from 8 to 13 after the fix, with no failures.

## Look-back and value-to-value thresholds (signal.recent, signal.threshold right)

Added 2026-10-04 (batch 25) for the trend-pullback-composite fix. Both render on all 22 targets with no TODO.
- `signal.threshold` takes an optional `right` (a block id or a price name) instead of `value`, so a trend **state** such as `EMA 21 > EMA 89` holds on every bar of the trend, not only on the cross bar.
- `signal.recent {signal, bars}` is true when `signal` was true on one of the previous `bars` bars (1-50). The current bar is not counted. `signal` must be an earlier signal or filter block, not an alert, scanner or another `signal.recent`.
- Series and index targets (Pine, MQL5 / MQL4, cTrader, NinjaTrader, Quantower, Sierra Chart, ProRealTime, GoCharting, MotiveWave, Vela, JForex, EasyLanguage, ATAS, AmiBroker, thinkScript, Tradovate) OR the signal over offsets 1..N; index targets guard the first bars, AmiBroker wraps `Ref` in `Nz` (no value before the first bar = false).
- Bar-by-bar Python targets (Bookmap, backtrader, NautilusTrader) keep a bars-since counter per block; Backtesting.py uses a vectorised `bsv_recent` helper emitted only when the recipe needs it. MQL5 copies `bars` more history for the look-back.
- Checked by the Pine, MQL5, thinkScript, AmiBroker, Tradovate, backtrader, Backtesting.py and NautilusTrader checks against independent recomputations, plus a "look-back includes the current bar" mutant (Pine, MQL5). Other targets: source checks only. UNTESTED_RUNTIME on every platform.

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

MQL4 custom indicators use series-indexed buffers (`SetIndexBuffer`) and built-in indicator functions (`iMA`, `iRSI`, `iATR`). The `mql4` target computes EMA/SMA/RSI/ATR, cross/threshold/combine signals, plots, pivots, liquidity-sweep candidates, pivot zones and once-per-closed-bar `Alert()`; session filters use broker server time and stay marked TODO for timezone conversion.

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

## TradingView (Pine Script v6) — BSV check

Checked by BSV since 2026-10-04: `scripts/site/check_pine.mjs` parses every recipe's `pine-v6` output with a small BSV-written Pine-subset parser and evaluates it as series over synthetic bars. It checks that only documented functions and constants are used (`ta.ema`, `ta.sma`, `ta.rsi`, `ta.atr`, `ta.crossover`, `ta.crossunder`, `time`, `na`, `request.security`, `timeframe.in_seconds`, `runtime.error`, `plot`, `alertcondition`), that every name is declared before use, that history offsets look back, and that `request.security` is only used as `(syminfo.tickerid, tf, expr[1], lookahead = barmerge.lookahead_on)`. EMA / SMA / RSI / ATR values equal an independent reference after warm-up (seeds may differ while warming up); crosses, thresholds, combines and sessions (time zones through `Intl`, 15-minute bars) equal an independent recomputation on every bar; plots and `alertcondition` use their blocks; prefix runs give the same last-bar values (no lookahead); a 60-minute higher-timeframe value equals the previous closed hour on 15-minute bars and the `runtime.error` guard stops the script on an hourly chart. Mutants that must be caught: the shift-0 higher timeframe (static rule and prefix test) and a flipped cross.

Found and fixed while adding it: a recipe whose alert used a block the Pine generator does not render yet (liquidity sweep, divergence, opening-range breakout) referenced a name that was never declared, so that Pine output would not compile. TODO blocks are now declared as stubs that are never true (`name = false`) or empty (`float name = na`), as on the other targets.

Since 2026-10-04 (batch 22) also rendered on Pine v6 and checked the same way: `structure.range` (`ta.valuewhen(in, ta.highest(high, ta.barssince(new) + 1), 0)`, low likewise), `signal.breakout` (`close[1]`), `structure.pivot` (written with `ta.highest` / `ta.lowest` so the tie rule is explicit: strictly beyond the left bars, at least as far as the right ones; held with `ta.valuewhen(..., 0)`), `signal.liquidity_sweep` (pivot known before the bar, `[1]`), `signal.divergence` (`ta.valuewhen(..., 1)` = the pivot before) and `visual.zone` (two plots). The checker compares every bar with independent references (sessions in the recipe time zone), requires windows, breakouts, pivots and signals to occur, checks prefix runs and catches 5 more mutants. Since batch 23 also on Pine v6: value panels (`visual.table`: `var table` + `table.new`, filled with `table.cell` under `if barstate.islast`; `[1]` shows the bar that just closed because the last bar may still be forming; higher-timeframe fields are the `request.security` values already checked) and `alert.webhook` (`alert(json, alert.freq_once_per_bar_close)` inside `if <condition>`: completed bars only; `{{symbol}}` = `syminfo.ticker`, `{{timeframe}}` = `timeframe.period`, `{{time}}` = bar open time in UTC, prices with `str.tostring(x, "#.########")`). TradingView sends the JSON only after you create an alert on the script with "Any alert() function call" and your webhook URL; never put secrets in it. The checker compares every panel cell with the series checked above, on the full run and on prefix runs (no lookahead), parses every webhook message as JSON and compares it with the recipe payload filled from the bar, and catches 6 more mutants (panel without `[1]`, price from the open, condition one bar late, `alert.freq_all` rejected). Still TODO on Pine: `scanner.symbol_set` only (TODO on every target).

Not TradingView: the evaluator models the documented behaviour; compile and run the script on your TradingView version before relying on it (UNTESTED_RUNTIME).

## MetaTrader 5 (MQL5) — BSV check

Since 2026-10-04 (batch 24) the `mql5` output is checked by `scripts/site/check_mql5.mjs`: a BSV-written translator for the generated MQL5 subset (types dropped; casts, inputs, statics, classes, integer division and any other construct outside the subset are rejected) run in node:vm against a BSV model of the documented MT5 custom-indicator API: `OnInit` / `OnCalculate` with `rates_total` / `prev_calculated`, `iMA` / `iRSI` / `iATR` handles with `CopyBuffer`, `ArraySetAsSeries`, `SetIndexBuffer`, `iTime` / `iHigh` / `iLow` / `iClose` / `iBarShift` / `Bars`, `TimeToStruct`, `Alert`. Not MetaTrader 5 and not MetaEditor: compile in MetaEditor before use (UNTESTED_RUNTIME).

- **Undeclared-name audit:** every identifier must be declared in the file or be one of the documented MQL5 names the model implements (no trade, web or file calls). A mutant that turns a referenced TODO stub into a comment (the bug found in the Pine output in batch 21) must fail.
- **Out-of-range reads:** arrays are bounds-checked, because MT5 stops an indicator on "array out of range".
- **Built-in values follow the MT5 example sources** (Indicators/Examples): the MA EMA starts from the first price, RSI is Wilder-smoothed, and **ATR is a simple moving average of the true range** (ATR.mq5), not Wilder's smoothing used by `ta.atr` in Pine and by the other BSV targets. An ATR threshold (for example `atr > 2`) can therefore switch on different bars on MT5. EMA / SMA / RSI / ATR are compared with independent references after warm-up.
- **Bar by bar:** signals, sessions (broker server time; the output keeps its TODO to convert from the recipe time zone), the higher timeframe (previous closed higher bar; `INIT_FAILED` on a too-coarse chart), ranges and breakouts are compared with independent references.
- **Incremental calls:** `OnCalculate` is called the way MT5 does it: history first, then each new bar as a first tick and then its final tick. Plot buffers must equal one full calculation, and alerts must fire once per **closed** bar on the condition, never from the forming bar.
- **Mutants caught:** an alert from the forming bar, no `limit++`, a flipped cross, a look-back that includes the current bar (`signal.recent`), a pivot without the right-side test, a sweep without the close back inside, a flipped divergence oscillator test, the higher timeframe reading the forming higher bar, a window starting one bar too old, a breakout without the close before, and a comment-only TODO.
- `structure.range` / `signal.breakout` render on MQL5 since batch 24. They scan back from bar i to the latest window bar, then to the start of that window.
- **Pivots, sweeps, divergence and zones render on MQL5 since batch 26** (same rules as Pine). `S_<pivot>_ph(i)` is true when bar i confirms a pivot at bar i + right (above the left bars before it, at least as high as the right bars after it; a flat top counts once). The last confirmed pivot is found by scanning back from bar i, so there is no state and no lookahead. A sweep compares bar i with the pivot known at bar i + 1. Divergence compares the new pivot with the one before it and reads the oscillator at both, so OnCalculate copies the **whole** oscillator buffer on every call for that recipe (slower on long histories). A zone is two extra line buffers (high red, low green) after the plots.
- Checked in the BSV MQL5 model: pivot highs / lows, sweeps and divergences equal an independent chronological reference on every calculated bar from bar 400; zone buffers equal the pivot / window high and low, and incremental calls equal one full calculation. Mutants caught: pivot without the right-side test, sweep without the close back inside, divergence with the oscillator test flipped. MQL5 TODO lines across the 14 recipes: from 12 to 6.
- **Value panels render on MQL5 since batch 27** with `Comment()` (top-left corner of the chart), one line per field, at shift 1 = the bar that just closed (the newest bar may still be forming); `n/a` = no value yet; `OnDeinit` clears it. Fields that depend on a block this target does not render keep their TODO line. Checked in the BSV MQL5 model: the panel text equals the fields at the closed bar on **every** incremental call (first tick and final tick of each new bar); a shift-0 mutant is caught.
- **Webhooks on MQL5 (batch 27): the JSON is built, not sent.** The MQL5 reference says `WebRequest()` "is not available for calls from indicators" (only Expert Advisors and scripts; error 4014). So the indicator prints `BSV webhook {...}` to the Experts journal once per closed bar where the condition holds; to send it, call `WebRequest` from your own EA and add the URL to Tools > Options > Expert Advisors. `{{time}}` = bar open time in broker server time (`TimeToString`, yyyy.mm.dd hh:mi), `{{timeframe}}` = e.g. `H1`, prices with `_Digits` decimals. Checked: printed JSON = the recipe payload filled from that bar, on exactly the closed bars where the condition holds; mutants caught: price from the open, webhook from the forming bar.
- MQL5 now renders every block type the 14 recipes use, including `scanner.symbol_set` since batch 28 (see Symbol scans below).

### Symbol scans (`scanner.symbol_set`, batch 28)

Real multi-symbol scans are generated only where the platform can read other symbols from one script; everywhere else the output says so instead of a silent TODO.

- **Pine v6:** one `input.symbol()` per listed symbol and one `request.security(symbol, timeframe.period, signal[1], lookahead = barmerge.lookahead_on)` per symbol, i.e. the signal at that symbol's bar that just closed (the TradingView docs give `[1]` with `lookahead_on` as the non-repainting form). One `alert()` per bar lists the symbols that hit (create the alert with "Any alert() function call"). Up to **40 symbols**: TradingView allows 40 unique `request.*()` calls per script (64 on Ultimate).
- **MQL5:** `InpScan_<id>` = comma-separated list (no spaces); empty = every Market Watch symbol (at most 100). `OnInit` calls `SymbolSelect` and creates one indicator handle per symbol; once per closed chart bar `OnCalculate` evaluates the signal on each symbol at shift 1, then restores the chart symbol, prints how many symbols had no data yet, and raises one `Alert()` listing the hits. Chart plots and chart alerts are unchanged.
- **backtrader, Backtesting.py, NautilusTrader:** `bsv_scan_<id>(data)` takes a dict `{symbol: bars}` and returns the symbols whose signal held on their last completed bar; from the command line: `python file.py --scan EURUSD=eurusd.csv GBPUSD=gbpusd.csv` prints `SCAN <id> <symbol> <bar time>` per hit, then `SCAN <id> done <n>`.
- **NinjaTrader 8 (batch 30):** one `AddDataSeries("SYMBOL")` per listed symbol in `State.Configure` (chart bar type and period; the NT8 manual says the arguments must be hard-coded, so the list is edited in the code or the Builder, and every name must be an instrument NinjaTrader knows). Each symbol is evaluated in **its own** `OnBarUpdate` (`BarsInProgress` k, barsAgo 0 = that symbol's bar that just closed), so the manual's rule that bars sharing a timestamp run the chart series first does not change the result; one `Alert()` per symbol and closed bar (`Alert()` only fires in real time). `MaximumBarsLookBack.Infinite` because pivots look back further than 256 bars. An unknown instrument stops the indicator from loading (NinjaTrader behaviour, not modelled).
- **cTrader (batch 30):** `[Parameter]` list (comma-separated); `Initialize` loads `MarketData.GetBars(TimeFrame, symbol)` and the indicators on those bars; a symbol the broker does not know is skipped with a Print. Live only (last bar): once per new chart bar, each symbol at its last bar that opened before the chart bar's open (the `OpenTimes` index is stepped back, because the reference does not say how `GetIndexByTime` rounds); one `Print` listing the hits and one with the number of symbols skipped.
- **MQL4 (batch 32):** `InpScan_<id>` = comma-separated list (no spaces); empty = every Market Watch symbol (at most 100). `OnInit` calls `SymbolSelect` for each (an unknown name is printed and then skipped). The block functions read `g_sym`, so the built-in calls (`iRSI(g_sym, 0, ...)`, `iClose(g_sym, 0, ...)`, `iBars`) read the scanned symbol; once per closed chart bar each symbol is evaluated at shift 1 (its bar that just closed), then the chart symbol is restored, one `Print` gives the number of symbols without enough history yet (the terminal starts loading it), and one `Alert()` lists the hits. Chart alerts are unchanged.
- On NinjaTrader and cTrader, pivots, liquidity-sweep candidates, regular divergence and pivot zones render on every recipe (batch 36). MQL4 does the same from batch 37: pivots read the chart symbol (`NULL`) outside a scan and `g_sym` inside one; the pivot zone is two extra indicator buffers (high / low). Ranges, breakouts, tables and webhooks stay TODO on MQL4.
- Checked by `scripts/site/check_cs_scan.py`: all 14 NinjaTrader outputs compile (.NET 8, warnings as errors) against BSV's NinjaScript stand-in (cTrader: `check_ctrader_stubs.sh`); the divergence-scanner output of both is **run** on the BSV synthetic bars with a functional stand-in (chart + three later-start symbols, plus one unknown symbol on cTrader). Every Alert / Print equals the independent Python reference (cTrader: 18 symbol hits from bar 300 on; NinjaTrader: 23 symbol alerts and 8 chart alerts), with cTrader `GetIndexByTime` modelled both ways and NinjaTrader shared timestamps in both orders; 8 scan mutants caught. Batch 36: pivots, liquidity-sweep candidates, regular divergence and pivot zones also render on every NinjaTrader / cTrader recipe (not only scanners); MQL4 stays scan-only for pivots. `liquidity-sweep-alert` is run chart-only on both stand-ins against the Python reference (ATR from that reference); 6 sweep mutants caught. Not NinjaTrader or cTrader, UNTESTED_RUNTIME.
- MQL4 is checked by `scripts/site/check_mql4.mjs`, a BSV MQL4-subset translator run in node:vm against a BSV model of the documented MT4 indicator API (all 14 recipes: name audit, values against independent references, incremental calls, alerts once per closed bar). The scan output runs on the chart plus three symbols with their own bars (one starting 370 bars later, so it is skipped until it has enough history), a Market Watch-only symbol and an unknown symbol: every scan `Alert` and skip `Print` equals the expected list built from each symbol run as its own chart, and the pivots / divergence equal a chronological reference. On liquidity-sweep-alert the sweep candidates and both zone buffers equal a chronological reference on every calculated bar (sweep mutants caught: no close-back-inside test, ATR fraction ignored, pivot read including the bar itself, high / low swapped; zone low holding the pivot high). Scan mutants caught: shift 0, symbol ignored, oscillator on the chart symbol, pivot on the chart prices, no history check, chart symbol not restored. Not MetaTrader 4, UNTESTED_RUNTIME.
- **Other 14 targets:** the block line reads `TODO unsupported block scanner.symbol_set: <id> - unsupported for this target: run one chart per symbol (this script reads only the chart symbol)`. Coverage and the Builder still count it as a gap. Some of these platforms do have their own multi-symbol APIs (AmiBroker Exploration `Filter`); BSV does not generate those yet.
- Not generated with a higher-timeframe block in the same recipe, or when the scanned signal itself is not rendered on that target (the TODO line then gives the reason).
- Checked: Pine (BSV Pine model, scanned symbols with different bars than the chart; mutants: no `[1]`, symbol 2 reading the chart), MQL5 (BSV MQL5 model with per-symbol bars, list and Market Watch variants, unknown symbol; mutants: shift 0, symbol ignored, chart buffer copied, chart symbol not restored), the 3 Python targets (each library run on 4 symbol files against the BSV reference; one mutant each). Not TradingView, not MetaTrader 5, UNTESTED_RUNTIME.
- **trend-pullback-composite, functional fix (2026-10-04, batch 25).** The old condition needed the EMA 21 / 89 cross-up event AND RSI <= 45 on the same bar, which never happened on either BSV test bar set (batch 24 reported it as `alerts_vacuous`). It now uses the standard trend-pullback form: trend state `EMA 21 > EMA 89` (a `signal.threshold` with `right`), pullback = RSI <= 45 on one of the previous 5 bars (`signal.recent`, `bars` editable in the Builder), trigger = RSI crosses back above 45 on a closed bar (RSI > 45 now, RSI <= 45 on the bar before). The recipe has no short side, so there is nothing to mirror. With both levels at 45 the cross already implies the pullback; lower `rsi_pullback_level` to require a deeper dip. The alert condition now holds on 35 / 10 closed bars of the two MQL5 60-minute test sets and on 41 bars of the Pine test set; `alerts_vacuous` is empty.
- **Follow-up (batch 26):** with both levels at 45 the pullback was redundant (the trigger already needs RSI <= 45 on the bar before). The pullback level (`rsi_pullback_level`, its own Builder parameter) is now **40**; the trigger stays at 45, so the recipe means a real dip, then recovery. Bars where the alert condition holds at 40: MQL5 8 / 6 (two 60-minute sets), Pine 8, thinkScript 9, Tradovate 8, AmiBroker 1 (400-bar set), Python reference 8 (backtrader, Backtesting.py, NautilusTrader); every one of these checks now asserts at least one. 42 and 45 were not needed.
