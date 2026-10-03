# Sierra Chart / ACSIL

BSV includes:

- `BsvEmaOverlay.cpp` — original custom-study starter

ACSIL custom studies expose chart data through `SCStudyInterfaceRef`, draw through Subgraphs, and expose settings through Inputs.

## Use

1. Add the source to your Sierra Chart custom-study source location.
2. Build it using the supported custom-study build flow.
3. Add `BSV EMA Overlay` to a chart.
4. Change the EMA Length input.
5. Verify it on your installed Sierra Chart version before adapting it.

Official ACSIL reference:
https://www.sierrachart.com/index.php?page=doc/AdvancedCustomStudyInterfaceAndLanguage.php

## Generated studies

The BSV generator also renders any recipe as an ACSIL study: `node generator/render.mjs <recipe.json> --target sierra-acsil` (or the browser recipe builder). Build it with Analysis > Build Custom Studies DLL. Not compiled by BSV.

Status: source prepared against documented ACSIL interfaces; exact runtime/build verification required.
