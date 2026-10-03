# GoCharting / Lipi

GoCharting exposes Lipi, its chart scripting language.

BSV includes:
- `bsv-dual-ema.lipi` — copy/paste starter

## Use

1. Open the GoCharting Lipi editor.
2. Create a new indicator.
3. Paste the source.
4. Validate/compile in the editor.
5. Modify the input lengths and add additional visual logic.

Current Lipi scope is best treated as indicator/chart scripting. Do not imply order execution from this starter.

Official scripting docs:
https://gocharting.com/docs/scripting

## Generated indicators

The BSV generator also renders any recipe as a Lipi indicator: `node generator/render.mjs <recipe.json> --target gocharting-lipi` (or the browser recipe builder). Alerts use `alertcondition` plus a closed-bar `alert()`. Not checked in the Lipi editor by BSV.

Status: source prepared against the documented syntax; runtime validation still required.
