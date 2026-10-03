// BSV Simple SMA for Quantower
// ORIGINAL BSV STARTER. Build inside Quantower Algo before use.
// No order placement. No profitability claim.

using System.Drawing;
using TradingPlatform.BusinessLayer;

public class BsvSimpleSma : Indicator
{
    private const int Period = 20;

    public BsvSimpleSma()
        : base()
    {
        Name = "BSV Simple SMA";
        Description = "Original BSV copy-paste moving-average starter.";
        AddLineSeries("SMA", Color.DodgerBlue, 2, LineStyle.Solid);
        SeparateWindow = false;
    }

    protected override void OnUpdate(UpdateArgs args)
    {
        if (Count <= Period)
            return;

        double sum = 0.0;

        for (int i = 0; i < Period; i++)
            sum += GetPrice(PriceType.Close, i);

        SetValue(sum / Period);
    }
}
