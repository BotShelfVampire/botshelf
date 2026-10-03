# cTrader / Python

Status: **UNTESTED_RUNTIME**. This is source prepared by BSV; it has not been built or run by BSV.

cTrader Algo Python indicators have two files: a C# attribute file (parameters / outputs) and a `<Name>_main.py` file (logic in `initialize` / `calculate`).

Starter: `BsvEmaAtrOverlayPy.cs` + `BsvEmaAtrOverlayPy_main.py` (EMA line with ATR bands; no order placement).

Generate a Python indicator from any recipe:

```bash
node ../../../generator/render.mjs ../../../recipes/mtf-trend-panel.json --target ctrader-python
```

The generated file starts with the attribute file contents in comments; paste that part into `<Name>.cs` and the rest into `<Name>_main.py`. Bar times are UTC (`TimeZone = TimeZones.UTC`); session filters are marked TODO for timezone conversion. Alerts are printed to the log once per closed bar.

Official docs: https://help.ctrader.com/ctrader-algo/how-tos/indicators/create-an-indicator/ (Python basics: https://help.ctrader.com/ctrader-algo/documentation/python-basics/)
Official samples (MIT): https://github.com/spotware/ctrader-python-algo-samples
