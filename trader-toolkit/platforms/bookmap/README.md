# Bookmap / Python API

Status: **UNTESTED_RUNTIME**. This is source prepared by BSV; it has not been run by BSV. Bookmap's Python API is in open beta and may change.

Starter: `bsv_trade_ema.py` (EMA of trade prices drawn on the main heatmap; no order placement).

Generate a Bookmap add-on from any recipe:

```bash
node ../../generator/render.mjs ../../recipes/mtf-trend-panel.json --target bookmap-python
```

Bookmap is order-flow based and has no classic OHLC bar loop, so the generated add-on builds time bars from trades (`BAR_SECONDS`, default 60) and evaluates the recipe when each bar closes. Overlay recipes draw on the main chart (`PRIMARY`), others on a sub-chart (`BOTTOM`). Session filters use UTC and are marked TODO. Alerts are printed to the add-on log.

Load: Bookmap → Settings → API plugins configuration → Python add-on (see the official guide for your version).

Official docs: https://github.com/BookmapAPI/python-api (MIT)
