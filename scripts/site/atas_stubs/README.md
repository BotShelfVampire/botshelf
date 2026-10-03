# ATAS indicator API stubs (BSV, compile check only)

Minimal stand-ins written by BSV from the public ATAS API reference (https://docs.atas.net/en/):
`Indicator(bool useCandles)`, `OnCalculate(int bar, decimal value)`, `GetCandle(int bar)` → `IndicatorCandle`
(Open/High/Low/Close/Time), `CurrentBar`, `DataSeries`, `ValueDataSeries(id, name)`, `Panel` /
`IndicatorDataProvider.NewPanel`, `AddAlert(string soundFile, string message)`.
They contain no ATAS code and do nothing at runtime. `scripts/site/check_atas_stubs.sh` compiles every generator
`atas` output against them with the .NET 8 C# compiler (warnings as errors). Passing it is NOT an ATAS build and NOT a chart test.
