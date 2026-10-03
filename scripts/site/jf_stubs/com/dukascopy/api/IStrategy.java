// BSV stub written from the public JForex API javadoc signature (https://www.dukascopy.com/client/javadoc3/). Compile check only; no Dukascopy code.
package com.dukascopy.api;

public interface IStrategy {
    void onStart(IContext context) throws JFException;
    void onTick(Instrument instrument, ITick tick) throws JFException;
    void onBar(Instrument instrument, Period period, IBar askBar, IBar bidBar) throws JFException;
    void onMessage(IMessage message) throws JFException;
    void onAccount(IAccount account) throws JFException;
    void onStop() throws JFException;
}
