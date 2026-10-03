# MT5 / MQL5

Generate a starter:

```bash
node ../../generator/render.mjs ../../recipes/mtf-trend-panel.json --target mql5
```

The MQL5 renderer creates indicator handles (`iMA`, `iRSI`, `iATR`) and copies them with `CopyBuffer`, evaluates cross / threshold / combine signals per bar (series indexing, 0 = newest), draws `visual.plot` blocks as indicator buffers and raises `Alert()` once per closed bar. Session filters use broker server time and are marked TODO; unsupported blocks stay visible as TODO stubs.

Compile in MetaEditor before use. A generated file is not marked Verified until the exact source is compiled/tested against a recorded MT5 build.
