# cTrader / C#

Generate a starter:

```bash
node ../../generator/render.mjs ../../recipes/mtf-trend-panel.json --target ctrader
```

The C# renderer targets the cTrader Algo indicator model: built-in indicators (with the recipe's price source), cross / threshold / combine signals, `[Output]` plots and a `Print` once per closed bar (no auto-trading). Bar times are UTC via the `TimeZone` attribute; session filters and unsupported blocks stay visible as TODO comments. For Python, see `python/`.

Build it inside cTrader Automate before use. Keep live order execution out of indicator examples unless a separate sandbox/demo execution path is explicitly tested.
