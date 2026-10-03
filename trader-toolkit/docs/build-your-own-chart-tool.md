# Build your own chart tool

BSV Trader Tool Blocks is meant to reduce the blank-page problem.

## 1. Pick the outcome first

Choose one job:

- overlay: levels, averages, zones
- dashboard: compact status panel
- scanner: many symbols, one condition
- alert: one condition, one notification
- study: oscillator or regime map
- web chart: your own chart surface with Vela

Do not start with twenty signals. Start with one job that you can verify.

## 2. Pick blocks

A recipe is JSON. Each block has an `id`, `type`, and `params`.

Example:

```json
{
  "id": "ema_fast",
  "type": "indicator.ema",
  "params": { "source": "close", "length": 21 }
}
```

Then use that id in later signal/visual blocks.

## 3. Generate a starter

```bash
node trader-toolkit/generator/render.mjs trader-toolkit/recipes/mtf-trend-panel.json --target pine-v6
```

Other current targets:

```bash
--target mql5            # MT5
--target ctrader         # cTrader C#
--target mql4            # MT4
--target ctrader-python  # cTrader Python (attribute file in the header comments)
--target bookmap-python  # Bookmap Python API add-on (open beta; time bars built from trades)
--target ninjatrader     # NinjaTrader 8 NinjaScript indicator
--target quantower       # Quantower C# indicator
--target sierra-acsil    # Sierra Chart ACSIL C++ custom study
--target prorealtime     # ProRealTime ProBuilder indicator
--target gocharting-lipi # GoCharting Lipi indicator
--target motivewave      # MotiveWave SDK custom study (Java)
```

The generator is deliberately conservative. Unsupported blocks remain visible as `TODO` comments rather than being silently dropped.

## 4. Paste/import

### TradingView

Create a new Pine indicator, replace the editor content with the generated Pine v6 source, save, compile, add to chart.

### MT5

Create a custom indicator in MetaEditor. Use the generated MQL5 source as the starter, compile, then resolve any TODO markers before relying on it.

### cTrader

Create a custom indicator in Automate, paste the generated C# starter, build, then resolve TODO markers.

### Vela

Use the [Vela custom chart starter](../platforms/vela/). It is for people who want their own browser chart rather than only an indicator inside someone else's charting platform.

## 5. Verify

Check:

- exact source/version
- enough historical bars
- symbol/timezone assumptions
- repaint/lookahead behavior
- session handling
- alert frequency/deduplication
- parameter edge cases

A compile pass is not proof of trading value.

## 6. Customize

Useful next changes:

- swap EMA lengths
- add higher-timeframe data
- replace threshold values
- add ATR-based visual bands
- add a session gate
- add webhook-ready alerts
- split one large tool into one overlay + one scanner

## 7. Publish honestly

If you list the result on BSV, state:

- original/adapted source
- platform/version
- exact prerequisites
- what is tested
- what is not tested
- limitations
- no unsupported performance claims
