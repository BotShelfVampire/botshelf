# BSV Trader Tool Blocks

A free, original starter toolkit for building custom chart tools from reusable blocks.

The goal is practical: choose a platform, copy a starter, edit one recipe, and turn it into your own indicator, dashboard, scanner, alert workflow, or lightweight chart app.

## Start here

1. Read [Build your own chart tool](docs/build-your-own-chart-tool.md).
2. Pick a starter recipe in [recipes](recipes/).
3. Generate a supported starter with `node generator/render.mjs <recipe.json> --target pine-v6|mql5|ctrader|mql4|ctrader-python|bookmap-python|ninjatrader|quantower|sierra-acsil|prorealtime|gocharting-lipi|motivewave|vela|jforex|easylanguage`.
4. Paste/import it into the target platform.
5. Compile and inspect it yourself.
6. Record the exact platform/version you tested.

## Current block families

- moving averages: EMA, SMA
- momentum: RSI
- volatility: ATR
- session filters
- cross/threshold signals
- combined conditions
- visual plots
- alert conditions
- webhook-ready alert messages

## Platforms

- TradingView / Pine Script v6 — generator target
- MT5 / MQL5 — generator target (indicator handles + CopyBuffer, signals, plots, closed-bar alerts; not runtime tested)
- cTrader / C# — generator target (built-in indicators, signals, plots, closed-bar alerts; not runtime tested)
- MT4 / MQL4 — generator target + EMA/ATR starter (not runtime tested)
- cTrader / Python — generator target + two-file EMA/ATR starter (not runtime tested)
- Bookmap / Python API (open beta) — generator target (time bars built from trades) + trade-EMA add-on (not runtime tested)
- Vela — generator target (`vela`: plain-JS recipe engine on Vela's engine port, line series, signal markers, closed-bar alerts; Apache-2.0 Vela only, no Pine runtime) + custom web-chart starter (headless-browser smoke test with synthetic bars only)
- NinjaTrader 8 / NinjaScript — generator target (`ninjatrader`: built-in EMA/SMA/RSI/ATR, signals, plots, `Alert()` on closed bars) + EMA/ATR starter (not runtime tested)
- Quantower / C# — generator target (`quantower`: built-in indicators via `Core.Indicators.BuiltIn`, signals, line series, closed-bar log alerts) + SMA starter (not runtime tested)
- Sierra Chart / ACSIL — generator target (`sierra-acsil`: `sc.ExponentialMovAvg`/`SimpleMovAvg`/`RSI`/`ATR`, subgraph plots, closed-bar `sc.AddAlertLine` alerts) + EMA starter (not compiled by BSV)
- ProRealTime / ProBuilder — generator target (`prorealtime`: `ExponentialAverage`/`Average`/`RSI`/`AverageTrueRange`, `CROSSES OVER/UNDER`, `RETURN` lines; overlay recipes draw arrow markers) + dual-EMA starter (not validated by BSV)
- GoCharting / Lipi — generator target (`gocharting-lipi`: `talib.ema/sma/rsi/atr`, `talib.crossover/crossunder`, plots, `alertcondition` + closed-bar `alert()`, markers on overlays) + dual-EMA starter (not checked in the Lipi editor by BSV)
- MotiveWave / Java SDK — generator target (`motivewave`: `Study` class, `DataSeries.ema/sma/atr`, Wilder RSI via `smma`, paths, closed-bar `ctx.signal`) + EMA starter (compiles against BSV stubs from the SDK javadoc; not built with the real SDK or loaded in MotiveWave by BSV)
- JForex / Dukascopy (Java `IStrategy`) — generator target (`jforex`: `IIndicators.ema/sma/rsi/atr`, closed-bar `onBar`, console values and notifications, no orders; compiles against BSV stubs from the JForex API javadoc; not compiled in JForex or run by BSV)
- TradeStation / EasyLanguage — generator target (`easylanguage`: indicator with `XAverage`/`Average`/`RSI`/`AvgTrueRange`, `PlotN`, closed-bar `Alert`; structural check only, not verified in TradeStation by BSV)
- ATAS and others — compatibility/research queue; only publish platform-specific code after an implementation path is verified

See [compatibility](docs/compatibility.md).

## Status labels

Everything in this directory is **ORIGINAL BSV source** unless stated otherwise.

- **Structurally generated** does not mean runtime-tested.
- A platform/version is **Verified** only after that exact source is compiled or executed on that platform/version.
- Generated TODO markers are intentional when a recipe contains a block the target renderer does not support yet.

## License

This repository is MIT licensed. Platform names belong to their respective owners. This toolkit is independent and is not an official TradingView, MetaQuotes, Spotware, Bookmap, or LuxAlgo product.

## Copy-paste TradingView starters

If you do not want to run the generator yet, open `platforms/tradingview/` and paste one of the original Pine v6 starters directly into Pine Editor:

- session range dashboard
- liquidity sweep candidate alert
- volatility regime map
- ATR risk overlay
- higher-timeframe trend panel
- webhook alert router

They are source starters, not profitability claims. Runtime verification is separate from structural/source review.

## Structural CI

The repository workflow `.github/workflows/trader-toolkit-check.yml` checks generator syntax, parses every recipe, exercises the original three generator targets (Pine v6, MQL5, cTrader C#; the MQL4, cTrader Python, Bookmap Python, NinjaTrader, Quantower, Sierra Chart ACSIL, ProRealTime, GoCharting Lipi, MotiveWave Java, Vela JavaScript, JForex Java and TradeStation EasyLanguage targets are covered by `scripts/site/test_builder_parity.mjs` and a local py_compile check until the workflow is updated), and verifies that unsupported advanced blocks remain explicit instead of silently disappearing.
