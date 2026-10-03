# TradingView / Pine Script v6

Generate a starter:

```bash
node ../../generator/render.mjs ../../recipes/mtf-trend-panel.json --target pine-v6
```

Paste the result into a new TradingView Pine Editor script.

Current generator supports a conservative subset: EMA, SMA, RSI, ATR, Pine session filter, cross/threshold/combine conditions, plots and alertcondition.

Review repainting, timeframe and session assumptions yourself.

Pine manual: https://www.tradingview.com/pine-script-docs/
