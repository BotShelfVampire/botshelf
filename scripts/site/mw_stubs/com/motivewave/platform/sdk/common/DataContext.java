package com.motivewave.platform.sdk.common;
public interface DataContext { DataSeries getDataSeries(); void signal(int index, Object signalKey, String message, Object value); }
