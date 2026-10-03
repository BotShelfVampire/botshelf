// BSV EMA + ATR Overlay (cTrader Algo / Python) - attribute file.
// ORIGINAL BSV STARTER. Not runtime tested by BSV. No order placement.
// The logic lives in BsvEmaAtrOverlayPy_main.py.
using System;
using cAlgo.API;

namespace cAlgo.Indicators;

[Indicator(IsOverlay = true, TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
public partial class BsvEmaAtrOverlayPy : Indicator
{
    [Parameter("EMA Period", DefaultValue = 20, MinValue = 1)]
    public int EmaPeriod { get; set; }

    [Parameter("ATR Period", DefaultValue = 14, MinValue = 1)]
    public int AtrPeriod { get; set; }

    [Parameter("ATR Multiple", DefaultValue = 1.5, MinValue = 0.1)]
    public double AtrMultiple { get; set; }

    [Output("EMA", LineColor = "Orange", Thickness = 2)]
    public IndicatorDataSeries Ema { get; set; }

    [Output("ATR Upper", LineColor = "Tomato")]
    public IndicatorDataSeries Upper { get; set; }

    [Output("ATR Lower", LineColor = "LimeGreen")]
    public IndicatorDataSeries Lower { get; set; }
}
