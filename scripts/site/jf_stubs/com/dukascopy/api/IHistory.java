// BSV stub written from the public JForex API javadoc signature (https://www.dukascopy.com/client/javadoc3/). Compile check only; no Dukascopy code.
package com.dukascopy.api;

public interface IHistory { IBar getBar(Instrument instrument, Period period, OfferSide side, int shift) throws JFException; }
