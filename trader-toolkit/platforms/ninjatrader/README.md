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
