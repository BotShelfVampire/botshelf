// BSV stub written from the public JForex API javadoc signature (https://www.dukascopy.com/client/javadoc3/). Compile check only; no Dukascopy code.
package com.dukascopy.api;

public class Instrument implements IFinancialInstrument, Comparable<Instrument> {
    public static final Instrument EURUSD = new Instrument("EUR/USD");
    private final String name;
    private Instrument(String n) { name = n; }
    @Override public int compareTo(Instrument o) { return name.compareTo(o.name); }
    @Override public String toString() { return name; }
}
