// BSV EMA + ATR Overlay
// ORIGINAL BSV STARTER. Compile in MetaEditor before use.
// No order placement. No profitability claim.
#property strict
#property indicator_chart_window
#property indicator_buffers 3
#property indicator_plots   3

#property indicator_label1  "EMA"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrOrange
#property indicator_width1  2

#property indicator_label2  "ATR Upper"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrTomato
#property indicator_width2  1

#property indicator_label3  "ATR Lower"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrLimeGreen
#property indicator_width3  1

input int    InpEmaPeriod = 20;
input int    InpAtrPeriod = 14;
input double InpAtrMultiple = 1.5;

double EmaBuffer[];
double UpperBuffer[];
double LowerBuffer[];

int emaHandle = INVALID_HANDLE;
int atrHandle = INVALID_HANDLE;

int OnInit()
{
   if(InpEmaPeriod < 1 || InpAtrPeriod < 1 || InpAtrMultiple <= 0.0)
      return(INIT_PARAMETERS_INCORRECT);

   SetIndexBuffer(0, EmaBuffer, INDICATOR_DATA);
   SetIndexBuffer(1, UpperBuffer, INDICATOR_DATA);
   SetIndexBuffer(2, LowerBuffer, INDICATOR_DATA);

   ArraySetAsSeries(EmaBuffer, true);
   ArraySetAsSeries(UpperBuffer, true);
   ArraySetAsSeries(LowerBuffer, true);

   emaHandle = iMA(_Symbol, PERIOD_CURRENT, InpEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   atrHandle = iATR(_Symbol, PERIOD_CURRENT, InpAtrPeriod);

   if(emaHandle == INVALID_HANDLE || atrHandle == INVALID_HANDLE)
      return(INIT_FAILED);

   IndicatorSetString(INDICATOR_SHORTNAME, "BSV EMA + ATR Overlay");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   if(emaHandle != INVALID_HANDLE)
      IndicatorRelease(emaHandle);
   if(atrHandle != INVALID_HANDLE)
      IndicatorRelease(atrHandle);
}

int OnCalculate(
   const int rates_total,
   const int prev_calculated,
   const datetime &time[],
   const double &open[],
   const double &high[],
   const double &low[],
   const double &close[],
   const long &tick_volume[],
   const long &volume[],
   const int &spread[]
)
{
   if(rates_total < MathMax(InpEmaPeriod, InpAtrPeriod))
      return(0);

   static double atrValues[];
   ArraySetAsSeries(atrValues, true);

   int toCopy = rates_total;
   if(CopyBuffer(emaHandle, 0, 0, toCopy, EmaBuffer) <= 0)
      return(prev_calculated);
   if(CopyBuffer(atrHandle, 0, 0, toCopy, atrValues) <= 0)
      return(prev_calculated);

   int copied = MathMin(ArraySize(atrValues), rates_total);
   for(int i = 0; i < copied; i++)
   {
      UpperBuffer[i] = EmaBuffer[i] + atrValues[i] * InpAtrMultiple;
      LowerBuffer[i] = EmaBuffer[i] - atrValues[i] * InpAtrMultiple;
   }

   return(rates_total);
}
