// BSV EMA Overlay for Sierra Chart ACSIL
// ORIGINAL BSV STARTER. Build as a custom study before use.
// No order placement. No profitability claim.

#include "sierrachart.h"

SCDLLName("BSV Trader Tool Blocks")

SCSFExport scsf_BsvEmaOverlay(SCStudyInterfaceRef sc)
{
    SCSubgraphRef EMA = sc.Subgraph[0];
    SCInputRef Length = sc.Input[0];

    if (sc.SetDefaults)
    {
        sc.GraphName = "BSV EMA Overlay";
        sc.StudyDescription = "Original BSV copy-paste EMA study starter.";
        sc.AutoLoop = 1;
        sc.GraphRegion = 0;

        EMA.Name = "EMA";
        EMA.DrawStyle = DRAWSTYLE_LINE;
        EMA.PrimaryColor = RGB(255, 165, 0);
        EMA.LineWidth = 2;
        EMA.DrawZeros = false;

        Length.Name = "EMA Length";
        Length.SetInt(20);
        Length.SetIntLimits(1, 10000);

        return;
    }

    sc.ExponentialMovAvg(sc.BaseDataIn[SC_LAST], EMA, Length.GetInt());
}
