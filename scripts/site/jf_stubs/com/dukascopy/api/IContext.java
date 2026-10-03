// BSV stub written from the public JForex API javadoc signature (https://www.dukascopy.com/client/javadoc3/). Compile check only; no Dukascopy code.
package com.dukascopy.api;

import java.util.Set;
public interface IContext {
    IIndicators getIndicators(); IHistory getHistory(); IConsole getConsole(); IEngine getEngine();
    void setSubscribedInstruments(Set<Instrument> instruments);
    void setSubscribedInstruments(Set<Instrument> instruments, boolean lock);
}
