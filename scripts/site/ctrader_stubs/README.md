# cTrader Algo compile stubs (BSV)

`CAlgoStubs.cs` declares only the cAlgo.API members the generator's `ctrader` target uses, with signatures taken from the
official API reference (https://help.ctrader.com/ctrader-algo/references/). `scripts/site/check_ctrader_stubs.sh` renders
every recipe for `ctrader` and runs `dotnet build` against these stubs (nullable reference types off, as in cTrader projects).

This proves the output type-checks against the documented API surface. It is **not** a cTrader build, does not run the
indicator, and says nothing about runtime behaviour (UNTESTED_RUNTIME).
