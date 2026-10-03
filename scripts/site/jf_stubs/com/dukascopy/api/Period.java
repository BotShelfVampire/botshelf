// BSV stub written from the public JForex API javadoc signature (https://www.dukascopy.com/client/javadoc3/). Compile check only; no Dukascopy code.
package com.dukascopy.api;

public final class Period implements Comparable<Period>, java.io.Serializable {
    private static final long serialVersionUID = 1L;
    public static final Period ONE_MIN = new Period(60000L), FIVE_MINS = new Period(300000L), FIFTEEN_MINS = new Period(900000L), ONE_HOUR = new Period(3600000L), FOUR_HOURS = new Period(14400000L), DAILY = new Period(86400000L);
    private final long ms;
    private Period(long ms) { this.ms = ms; }
    public long getInterval() { return ms; }
    @Override public int compareTo(Period o) { return Long.compare(ms, o.ms); }
    @Override public boolean equals(Object o) { return o instanceof Period && ((Period) o).ms == ms; }
    @Override public int hashCode() { return Long.hashCode(ms); }
}
