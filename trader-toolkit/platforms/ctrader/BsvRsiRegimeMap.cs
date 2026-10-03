// BSV RSI Regime Map
// ORIGINAL BSV STARTER. Build in cTrader Automate before use.

using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo
{
    [Indicator(IsOverlay = false, TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class BsvRsiRegimeMap : Indicator
    {
        [Parameter("RSI Period", DefaultValue = 14, MinValue = 1)]
        public int Period { get; set; }

        [Output("RSI", LineColor = "DodgerBlue", Thickness = 2)]
        public IndicatorDataSeries RsiOutput { get; set; }

        private RelativeStrengthIndex _rsi;

        protected override void Initialize()
        {
            _rsi = Indicators.RelativeStrengthIndex(Bars.ClosePrices, Period);
        }

        public override void Calculate(int index)
        {
            RsiOutput[index] = _rsi.Result[index];
        }
    }
}
