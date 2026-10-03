# Quantower / Quantower Algo

BSV includes:

- `BsvSimpleSma.cs` — intentionally small original starter

The point is to give users a clean base they can alter rather than handing them an opaque premium indicator clone.

Quantower custom indicators derive from `Indicator`, can add line series, read bar prices, and publish values from `OnUpdate`.

Official starter documentation:
https://help.quantower.com/quantower/quantower-algo/simple-indicator

Status: source prepared from the documented indicator structure; runtime compile still required.

## Generator target

Any recipe can also be rendered as a Quantower indicator:

```bash
node trader-toolkit/generator/render.mjs trader-toolkit/recipes/golden-cross-alert.json --target quantower > BsvGoldenCrossAlertStarter.cs
```

The output creates built-in indicators with `Core.Indicators.BuiltIn` (`EMA`, `SMA`, `RSI`, `ATR`) and `AddIndicator`, adds line series, writes values with `SetValue`, and logs once per closed bar on `UpdateReason.NewBar`. The builder on botshelfvampire.com (`/trading/build/`) has a Quantower tab with a compile checklist.

Not compiled in Quantower by BSV yet.

- https://help.quantower.com/quantower/quantower-algo/built-in-indicators
- https://api.quantower.com/docs/TradingPlatform.BusinessLayer.BuiltInIndicators.html
