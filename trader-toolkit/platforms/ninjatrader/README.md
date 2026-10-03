# NinjaTrader / NinjaScript

BSV includes an original indicator starter:

- `BsvEmaAtrOverlay.cs`

## Use

1. In NinjaTrader, create a new custom Indicator named `BsvEmaAtrOverlay`.
2. Replace the generated class body/source with the BSV starter as appropriate for your editor.
3. Compile inside NinjaScript Editor.
4. Add it to a chart.
5. Verify behavior on a non-live workflow before adapting it.

NinjaScript indicators use the standard indicator lifecycle and plotting methods such as `OnStateChange`, `OnBarUpdate`, and `AddPlot`.

Official language reference:
https://ninjatrader.com/support/helpguides/nt8/indicator.htm

Status: source prepared; exact NinjaTrader build/runtime verification still required.

## Generator target

Any recipe can also be rendered as a NinjaTrader 8 indicator:

```bash
node trader-toolkit/generator/render.mjs trader-toolkit/recipes/golden-cross-alert.json --target ninjatrader > BsvGoldenCrossAlertStarter.cs
```

The output uses `OnStateChange` (`AddPlot`, `Calculate.OnBarClose`, built-in `EMA`/`SMA`/`RSI`/`ATR` created in `State.DataLoaded`) and `OnBarUpdate` with `Alert()` on closed bars. Alerts only fire in real time. Session filters stay marked TODO because they depend on the chart's time zone setting. The builder on botshelfvampire.com (`/trading/build/`) has a NinjaTrader tab with a compile checklist.

Not compiled in NinjaTrader by BSV yet.

- https://ninjatrader.com/support/helpguides/nt8/alert.htm
