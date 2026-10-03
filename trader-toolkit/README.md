# BSV Trader Tool Blocks

A free, original starter toolkit for building custom chart tools from reusable blocks.

The goal is practical: choose a platform, copy a starter, edit one recipe, and turn it into your own indicator, dashboard, scanner, alert workflow, or lightweight chart app.

## Start here

1. Read [Build your own chart tool](docs/build-your-own-chart-tool.md).
2. Pick a starter recipe in [recipes](recipes/).
3. Generate a supported starter with `node generator/render.mjs <recipe.json> --target pine-v6|mql5|ctrader`.
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
- MT5 / MQL5 — generator starter target
- cTrader / C# — generator starter target
- Vela — custom web-chart starter
- MT4, NinjaTrader, Quantower, Sierra Chart, Bookmap, GoCharting, MotiveWave, ProRealTime and others — compatibility/research queue; only publish platform-specific code after an implementation path is verified

See [compatibility](docs/compatibility.md).

## Status labels

Everything in this directory is **ORIGINAL BSV source** unless stated otherwise.

- **Structurally generated** does not mean runtime-tested.
- A platform/version is **Verified** only after that exact source is compiled or executed on that platform/version.
- Generated TODO markers are intentional when a recipe contains a block the target renderer does not support yet.

## License

This repository is MIT licensed. Platform names belong to their respective owners. This toolkit is independent and is not an official TradingView, MetaQuotes, Spotware, or LuxAlgo product.
