// BSV EMA + ATR Overlay
// ORIGINAL BSV STARTER. Import/build in NinjaTrader before use.
// No order placement. No profitability claim.

using System.Windows.Media;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class BsvEmaAtrOverlay : Indicator
    {
        private const int EmaPeriod = 20;
        private const int AtrPeriod = 14;
        private const double AtrMultiple = 1.5;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "BSV original EMA plus ATR visual planning overlay.";
                Name = "BsvEmaAtrOverlay";
                Calculate = Calculate.OnBarClose;
                IsOverlay = true;
                IsSuspendedWhileInactive = true;

                AddPlot(Brushes.Orange, "EMA");
                AddPlot(Brushes.Tomato, "ATRUpper");
                AddPlot(Brushes.LimeGreen, "ATRLower");
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < System.Math.Max(EmaPeriod, AtrPeriod))
                return;

            double ema = EMA(EmaPeriod)[0];
            double atr = ATR(AtrPeriod)[0];

            Values[0][0] = ema;
            Values[1][0] = ema + atr * AtrMultiple;
            Values[2][0] = ema - atr * AtrMultiple;
        }
    }
}
