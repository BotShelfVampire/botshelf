package com.botshelfvampire.motivewave;

import com.motivewave.platform.sdk.common.Defaults;
import com.motivewave.platform.sdk.common.Enums;
import com.motivewave.platform.sdk.common.desc.IntegerDescriptor;
import com.motivewave.platform.sdk.common.desc.PathDescriptor;
import com.motivewave.platform.sdk.study.Study;
import com.motivewave.platform.sdk.study.StudyHeader;
import com.motivewave.platform.sdk.common.DataContext;

@StudyHeader(
    namespace="com.botshelfvampire",
    id="BSV_EMA_STARTER",
    name="BSV EMA Starter",
    desc="Original BSV EMA custom-study starter.",
    overlay=true
)
public class BsvEmaStarter extends Study
{
  private static final String PERIOD = "period";
  private static final String PATH = "path";
  private static final String EMA = "ema";

  @Override
  public void initialize(Defaults defaults)
  {
    var sd = createSD();
    var tab = sd.addTab("General");
    var group = tab.addGroup("Inputs");

    group.addRow(new IntegerDescriptor(PERIOD, "EMA Period", 20, 1, 10000, 1));
    group.addRow(new PathDescriptor(PATH, "EMA", defaults.getLineColor(), 1.0f, null, true, true, true));

    var rd = createRD();
    rd.declarePath(EMA, PATH);
    rd.setLabelSettings(PERIOD);
  }

  @Override
  protected void calculate(int index, DataContext ctx)
  {
    int period = getSettings().getInteger(PERIOD, 20);
    if (index < period) return;

    var series = ctx.getDataSeries();
    Double ema = series.ema(index, period, Enums.BarInput.CLOSE);
    if (ema == null) return;

    series.setDouble(index, EMA, ema);
    series.setComplete(index);
  }
}
