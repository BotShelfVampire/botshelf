// BSV EMA + ATR Overlay
// ORIGINAL BSV STARTER. Build in cTrader Automate before use.
// No order placement. No profitability claim.

using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo
{
    [Indicator(IsOverlay = true, TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class BsvEmaAtrOverlay : Indicator
    {
        [Parameter("EMA Period", DefaultValue = 20, MinValue = 1)]
        public int EmaPeriod { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 1)]
        public int AtrPeriod { get; set; }

        [Parameter("ATR Multiple", DefaultValue = 1.5, MinValue = 0.1, Step = 0.1)]
        public double AtrMultiple { get; set; }

        [Output("EMA", LineColor = "Orange", Thickness = 2)]
        public IndicatorDataSeries EmaOutput { get; set; }

        [Output("ATR Upper", LineColor = "Tomato", Thickness = 1)]
        public IndicatorDataSeries UpperOutput { get; set; }

        [Output("ATR Lower", LineColor = "LimeGreen", Thickness = 1)]
        public IndicatorDataSeries LowerOutput { get; set; }

        private ExponentialMovingAverage _ema;
        private AverageTrueRange _atr;

        protected override void Initialize()
        {
            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaPeriod);
            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);
        }

        public override void Calculate(int index)
        {
            var ema = _ema.Result[index];
            var atr = _atr.Result[index];

            EmaOutput[index] = ema;
            UpperOutput[index] = ema + atr * AtrMultiple;
            LowerOutput[index] = ema - atr * AtrMultiple;
        }
    }
}
