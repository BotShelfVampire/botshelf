package com.motivewave.platform.sdk.common;
public interface DataSeries {
  float getOpen(int index); float getHigh(int index); float getLow(int index); float getClose(int index);
  long getStartTime(int index);
  Double ema(int index, int period, Object key); Double sma(int index, int period, Object key); Double smma(int index, int period, Object key);
  Double atr(int index, int period);
  void setDouble(int index, Object key, Double value);
  boolean isBarComplete(int index); void setComplete(int index, boolean b);
}
