// BSV functional stand-in for the cAlgo.API members the generator's `ctrader` scan output uses, so check_cs_scan.py can RUN the
// generated indicator on synthetic bars. Same member names / signatures as ctrader_stubs/CAlgoStubs.cs; the behaviour is BSV's model
// of the documented API (bars grow as time passes, the last bar is the forming one, indicator values come from the BSV reference,
// GetIndexByTime is modelled two ways because the reference does not say how it rounds). Not cTrader; UNTESTED_RUNTIME.
using System;
using System.Collections.Generic;
namespace cAlgo.API
{
    public enum TimeZones { UTC }
    public enum AccessRights { None }
    public enum MovingAverageType { Simple, Exponential, WilderSmoothing }
    [AttributeUsage(AttributeTargets.Class)] public sealed class IndicatorAttribute : Attribute { public bool IsOverlay { get; set; } public TimeZones TimeZone { get; set; } public AccessRights AccessRights { get; set; } }
    [AttributeUsage(AttributeTargets.Property)] public sealed class OutputAttribute : Attribute { public OutputAttribute(string name) { } }
    [AttributeUsage(AttributeTargets.Property)] public sealed class ParameterAttribute : Attribute { public ParameterAttribute(string name) { } public object DefaultValue { get; set; } }
    public interface DataSeries { double this[int index] { get; } double LastValue { get; } int Count { get; } }
    public interface IndicatorDataSeries : DataSeries { new double this[int index] { get; set; } }
    public interface TimeSeries { DateTime this[int index] { get; } DateTime LastValue { get; } int Count { get; } int GetIndexByTime(DateTime dateTime); int GetIndexByExactTime(DateTime dateTime); }
    public interface Bars { int Count { get; } TimeFrame TimeFrame { get; } TimeSeries OpenTimes { get; } DataSeries OpenPrices { get; } DataSeries HighPrices { get; } DataSeries LowPrices { get; } DataSeries ClosePrices { get; } DataSeries MedianPrices { get; } DataSeries TypicalPrices { get; } }
    public sealed class TimeFrame
    {
        private readonly string n; private TimeFrame(string n) { this.n = n; } public override string ToString() => n;
        public static readonly TimeFrame Minute = new("Minute"), Minute15 = new("Minute15"), Hour = new("Hour"), Daily = new("Daily");
    }
    public interface MarketData { Bars GetBars(TimeFrame timeFrame); Bars GetBars(TimeFrame timeFrame, string symbolName); }
    public abstract class Algo
    {
        public Bars Bars { get; set; } public MarketData MarketData { get; set; } public TimeFrame TimeFrame { get; set; } public cAlgo.API.Indicators.IIndicatorsAccessor Indicators { get; set; }
        public List<string> BsvPrints = new();
        public void Print(object message) { BsvPrints.Add(Convert.ToString(message)); } public void Print(string message, params object[] parameters) { BsvPrints.Add(string.Format(message, parameters)); }
    }
    public abstract class Indicator : Algo { public bool IsLastBar { get; set; } protected virtual void Initialize() { } public abstract void Calculate(int index); public void BsvInitialize() => Initialize(); }
}
namespace cAlgo.API.Indicators
{
    using cAlgo.API;
    public interface ExponentialMovingAverage { IndicatorDataSeries Result { get; } }
    public interface SimpleMovingAverage { IndicatorDataSeries Result { get; } }
    public interface RelativeStrengthIndex { IndicatorDataSeries Result { get; } }
    public interface AverageTrueRange { IndicatorDataSeries Result { get; } }
    public interface IIndicatorsAccessor
    {
        ExponentialMovingAverage ExponentialMovingAverage(DataSeries source, int periods);
        SimpleMovingAverage SimpleMovingAverage(DataSeries source, int periods);
        RelativeStrengthIndex RelativeStrengthIndex(DataSeries source, int periods);
        AverageTrueRange AverageTrueRange(int periods, MovingAverageType maType);
        AverageTrueRange AverageTrueRange(Bars bars, int periods, MovingAverageType maType);
    }
}
namespace BsvEval
{
    using cAlgo.API;
    using cAlgo.API.Indicators;
    // one symbol: bar m opens at T0 + (m + Off) * Step with the reference values of bar m; Count = bars opened so far (the last one forming)
    public sealed class SimBars : Bars
    {
        public string Name; public int Off; public double[][] Px; public double[] Rsi; public DateTime T0; public TimeSpan Step; public int N; public bool RoundUp;
        public int Count => N; public TimeFrame TimeFrame => TimeFrame.Minute15;
        public TimeSeries OpenTimes => new Times(this);
        public DataSeries OpenPrices => new Col(this, 0); public DataSeries HighPrices => new Col(this, 1); public DataSeries LowPrices => new Col(this, 2); public DataSeries ClosePrices => new Col(this, 3);
        public DataSeries MedianPrices => throw new NotSupportedException(); public DataSeries TypicalPrices => throw new NotSupportedException();
        public DateTime TimeOf(int m) => T0 + (m + Off) * Step;
        public sealed class Col : DataSeries { public readonly SimBars B; public readonly int K; public Col(SimBars b, int k) { B = b; K = k; }
            public double this[int i] => i >= 0 && i < B.N ? B.Px[i][K] : double.NaN; public double LastValue => this[B.N - 1]; public int Count => B.N; }
        sealed class Times : TimeSeries { readonly SimBars B; public Times(SimBars b) { B = b; }
            public DateTime this[int i] => (i >= 0 && i < B.N) ? B.TimeOf(i) : throw new IndexOutOfRangeException("OpenTimes[" + i + "]");
            public DateTime LastValue => this[B.N - 1]; public int Count => B.N;
            public int GetIndexByTime(DateTime t) { if (B.RoundUp) return B.N - 1; int k = -1; for (int m = 0; m < B.N; m++) if (B.TimeOf(m) <= t) k = m; return k; }
            public int GetIndexByExactTime(DateTime t) { for (int m = 0; m < B.N; m++) if (B.TimeOf(m) == t) return m; return -1; } }
    }
    public sealed class Res : IndicatorDataSeries, RelativeStrengthIndex
    {
        readonly SimBars B; public Res(SimBars b) { B = b; }
        public double this[int i] { get => i >= 0 && i < B.N ? B.Rsi[i] : double.NaN; set => throw new NotSupportedException(); }
        double DataSeries.this[int i] => this[i];
        public double LastValue => this[B.N - 1]; public int Count => B.N; public IndicatorDataSeries Result => this;
    }
    public sealed class Acc : IIndicatorsAccessor
    {
        public ExponentialMovingAverage ExponentialMovingAverage(DataSeries s, int p) => throw new NotSupportedException();
        public SimpleMovingAverage SimpleMovingAverage(DataSeries s, int p) => throw new NotSupportedException();
        public RelativeStrengthIndex RelativeStrengthIndex(DataSeries s, int p) { var c = (SimBars.Col)s; if (c.K != 3) throw new NotSupportedException("RSI of close only"); return new Res(c.B); }
        public AverageTrueRange AverageTrueRange(int p, MovingAverageType t) => throw new NotSupportedException();
        public AverageTrueRange AverageTrueRange(Bars b, int p, MovingAverageType t) => throw new NotSupportedException();
    }
    public sealed class Md : MarketData
    {
        public Dictionary<string, SimBars> Syms = new(); public SimBars Chart;
        public Bars GetBars(TimeFrame tf) => Chart;
        public Bars GetBars(TimeFrame tf, string name) => Syms.TryGetValue(name, out var b) ? b : throw new ArgumentException("symbol not found");
    }
}
