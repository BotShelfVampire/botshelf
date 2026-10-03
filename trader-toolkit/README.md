# BSV Trader Tool Blocks

A free, original starter toolkit for building custom chart tools from reusable blocks.

The goal is practical: choose a platform, copy a starter, edit one recipe, and turn it into your own indicator, dashboard, scanner, alert workflow, or lightweight chart app.

## Start here

1. Read [Build your own chart tool](docs/build-your-own-chart-tool.md).
2. Pick a starter recipe in [recipes](recipes/).
3. Generate a supported starter with `node generator/render.mjs <recipe.json> --target pine-v6|mql5|ctrader|mql4|ctrader-python|bookmap-python|ninjatrader|quantower`.
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
- Vela — custom web-chart starter
- NinjaTrader 8 / NinjaScript — generator target (`ninjatrader`: built-in EMA/SMA/RSI/ATR, signals, plots, `Alert()` on closed bars) + EMA/ATR starter (not runtime tested)
- Quantower / C# — generator target (`quantower`: built-in indicators via `Core.Indicators.BuiltIn`, signals, line series, closed-bar log alerts) + SMA starter (not runtime tested)
- Sierra Chart, GoCharting, MotiveWave, ProRealTime — hand-written starters (not runtime tested)
- ATAS, JForex and others — compatibility/research queue; only publish platform-specific code after an implementation path is verified

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

The repository workflow `.github/workflows/trader-toolkit-check.yml` checks generator syntax, parses every recipe, exercises the original three generator targets (Pine v6, MQL5, cTrader C#; the MQL4, cTrader Python, Bookmap Python, NinjaTrader and Quantower targets are covered by `scripts/site/test_builder_parity.mjs` and a local py_compile check until the workflow is updated), and verifies that unsupported advanced blocks remain explicit instead of silently disappearing.
