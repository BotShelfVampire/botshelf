# MT4 / MQL4

Status: **UNTESTED_RUNTIME**. This is source prepared by BSV; it has not been compiled or run by BSV.

Starter: `BSV_EmaAtrOverlay.mq4` (EMA line with ATR bands; no order placement).

Generate an MQL4 indicator from any recipe:

```bash
node ../../generator/render.mjs ../../recipes/mtf-trend-panel.json --target mql4
```

The MQL4 renderer computes EMA / SMA / RSI / ATR with the built-in `iMA` / `iRSI` / `iATR` functions, evaluates cross / threshold / combine signals per bar, draws `visual.plot` blocks as indicator buffers, and raises `Alert()` once per closed bar. Session filters use broker server time and are marked TODO for timezone conversion. Unsupported blocks stay visible as TODO stubs.

Steps: MetaEditor (MT4) → File → New → Custom Indicator → paste → Compile (F7) → attach to a chart. Test on history and a demo account first.

Official docs: https://docs.mql4.com/ (custom indicators: https://docs.mql4.com/customind)
