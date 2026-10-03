# MT5 / MQL5

Generate a starter:

```bash
node ../../generator/render.mjs ../../recipes/mtf-trend-panel.json --target mql5
```

The current renderer creates an indicator skeleton and emits explicit TODO markers for recipe features that need target-specific implementation.

Compile in MetaEditor before use. A generated file is not marked Verified until the exact source is compiled/tested against a recorded MT5 build.
