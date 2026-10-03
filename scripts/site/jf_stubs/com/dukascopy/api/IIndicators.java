// BSV stub written from the public JForex API javadoc signature (https://www.dukascopy.com/client/javadoc3/). Compile check only; no Dukascopy code.
package com.dukascopy.api;

public interface IIndicators {
    enum AppliedPrice { CLOSE, OPEN, HIGH, LOW, MEDIAN_PRICE, TYPICAL_PRICE, WEIGHTED_CLOSE, TIMESTAMP, VOLUME }
    double ema(Instrument instrument, Period period, OfferSide side, AppliedPrice appliedPrice, int timePeriod, int shift) throws JFException;
    double sma(Instrument instrument, Period period, OfferSide side, AppliedPrice appliedPrice, int timePeriod, int shift) throws JFException;
    double rsi(Instrument instrument, Period period, OfferSide side, AppliedPrice appliedPrice, int timePeriod, int shift) throws JFException;
    double atr(Instrument instrument, Period period, OfferSide side, int timePeriod, int shift) throws JFException;
}
