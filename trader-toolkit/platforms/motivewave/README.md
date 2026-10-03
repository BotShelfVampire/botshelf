# MotiveWave / Java SDK

BSV includes:

- `BsvEmaStarter.java` — original custom-study starter
- generator target `motivewave` — `node generator/render.mjs <recipe.json> --target motivewave` writes one `Study` class per recipe (also in the browser recipe builder)

MotiveWave exposes a Java SDK for custom studies and strategies. BSV starts with a study only; it does not add order submission.

## Use

1. Start from the current MotiveWave SDK sample project for version 7+.
2. Add the BSV Java source into your study package.
3. Resolve the SDK dependency/imports against your installed SDK.
4. Build the study.
5. Load it in MotiveWave and verify it before adapting.

Official references:
- https://motivewave.com/sdk.htm
- https://www.motivewave.com/sdk/javadoc/com/motivewave/platform/sdk/study/Study.html

Generated code: save it as `<class name>.java` (the class name is in the header comment). Signals are raised only on closed bars; enable alerts for them in the study settings.

Status: generated studies for all 14 recipes compile with javac 21 against stub classes BSV wrote from the public javadoc. Not built against the real SDK jar, not loaded in MotiveWave, not runtime tested by BSV.
