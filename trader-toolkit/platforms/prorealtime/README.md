# ProRealTime / ProBuilder

BSV includes:

- `bsv-dual-ema.itf.txt` — copy/paste ProBuilder starter

## Use

1. Open ProRealTime.
2. Create a new personal indicator.
3. Paste the BSV source.
4. Validate it in the platform.
5. Change periods or extend the logic.

ProBuilder is the platform's language for personal indicators. ProBackTest / ProOrder and ProScreener are separate paths and should not be confused with this simple visual indicator.

Official references:
- https://www.prorealtime.com/en/help-manual/probuilder-custom-indicators
- https://www.prorealtime.com/en/pdf/probuilder.pdf

## Generated indicators

The BSV generator also renders any recipe as a ProBuilder indicator: `node generator/render.mjs <recipe.json> --target prorealtime` (or the browser recipe builder). Overlay recipes draw arrow markers; for alerts, create a second indicator that returns the 0/1 line and set the alert on it. Not validated by BSV.

- https://www.prorealcode.com/documentation/probuilder/

Status: source prepared; runtime validation still required.
