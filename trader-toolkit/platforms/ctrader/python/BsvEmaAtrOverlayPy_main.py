# BSV EMA + ATR Overlay (cTrader Algo / Python) - logic file.
# ORIGINAL BSV STARTER. Not runtime tested by BSV. No order placement. No profitability claim.
# Parameters and outputs are declared in BsvEmaAtrOverlayPy.cs.
import clr
clr.AddReference("cAlgo.API")
from cAlgo.API import *


class BsvEmaAtrOverlayPy():
    def initialize(self):
        self.ema = api.Indicators.ExponentialMovingAverage(api.Bars.ClosePrices, api.EmaPeriod)
        self.atr = api.Indicators.AverageTrueRange(api.AtrPeriod, MovingAverageType.WilderSmoothing)

    def calculate(self, index):
        ema = self.ema.Result[index]
        atr = self.atr.Result[index]
        api.Ema[index] = ema
        api.Upper[index] = ema + atr * api.AtrMultiple
        api.Lower[index] = ema - atr * api.AtrMultiple
