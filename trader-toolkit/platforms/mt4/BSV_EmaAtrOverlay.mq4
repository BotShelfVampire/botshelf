// BSV EMA + ATR Overlay (MT4 / MQL4)
// ORIGINAL BSV STARTER. Compile in MetaEditor (MT4) before use.
// Not runtime tested by BSV. No order placement. No profitability claim.
#property strict
#property indicator_chart_window
#property indicator_buffers 3
#property indicator_color1  clrOrange
#property indicator_color2  clrTomato
#property indicator_color3  clrLimeGreen
#property indicator_width1  2

input int    InpEmaPeriod   = 20;
input int    InpAtrPeriod   = 14;
input double InpAtrMultiple = 1.5;

double EmaBuffer[];
double UpperBuffer[];
double LowerBuffer[];

int OnInit()
{
   if(InpEmaPeriod < 1 || InpAtrPeriod < 1 || InpAtrMultiple <= 0.0)
      return(INIT_PARAMETERS_INCORRECT);

   SetIndexBuffer(0, EmaBuffer);
   SetIndexBuffer(1, UpperBuffer);
   SetIndexBuffer(2, LowerBuffer);
   SetIndexStyle(0, DRAW_LINE);
   SetIndexStyle(1, DRAW_LINE);
   SetIndexStyle(2, DRAW_LINE);
   SetIndexLabel(0, "EMA");
   SetIndexLabel(1, "ATR Upper");
   SetIndexLabel(2, "ATR Lower");
   IndicatorShortName("BSV EMA + ATR Overlay");
   return(INIT_SUCCEEDED);
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   int warmup = MathMax(InpEmaPeriod, InpAtrPeriod) + 1;
   if(rates_total <= warmup)
      return(0);

   // MT4 buffers are series-indexed: bar 0 is the newest bar.
   int limit = rates_total - prev_calculated;
   if(prev_calculated > 0)
      limit++;
   if(limit > rates_total - warmup)
      limit = rates_total - warmup;

   for(int i = limit - 1; i >= 0; i--)
   {
      double ema = iMA(NULL, 0, InpEmaPeriod, 0, MODE_EMA, PRICE_CLOSE, i);
      double atr = iATR(NULL, 0, InpAtrPeriod, i);
      EmaBuffer[i]   = ema;
      UpperBuffer[i] = ema + atr * InpAtrMultiple;
      LowerBuffer[i] = ema - atr * InpAtrMultiple;
   }
   return(rates_total);
}
