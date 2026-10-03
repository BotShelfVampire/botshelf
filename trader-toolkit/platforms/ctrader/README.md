# cTrader / C#

Generate a starter:

```bash
node ../../generator/render.mjs ../../recipes/mtf-trend-panel.json --target ctrader
```

The current renderer targets the cTrader Automate indicator model and keeps unsupported logic visible as TODO comments.

Build it inside cTrader Automate before use. Keep live order execution out of indicator examples unless a separate sandbox/demo execution path is explicitly tested.
