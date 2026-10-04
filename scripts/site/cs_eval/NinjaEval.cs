// BSV functional stand-in for the NinjaScript (NinjaTrader 8) members the generator's `ninjatrader` target uses, so check_cs_scan.py
// can compile every recipe's output and RUN the symbol-scan output on synthetic bars. Behaviour = BSV's model of the NT8 manual:
// Calculate.OnBarClose, one OnBarUpdate per closed bar per series (BarsInProgress), barsAgo 0 = that series' bar that just closed,
// Closes[k] / CurrentBars[k] per series, indicators on a series follow that series' current bar, bars sharing a timestamp run the chart
// series first (the harness can also run them in reverse). Indicator values come from the BSV reference. Not NinjaTrader; UNTESTED_RUNTIME.
using System;
using System.Collections.Generic;
namespace System.Windows.Media { public sealed class Brush { } public static class Brushes { public static readonly Brush Black = new(), Yellow = new(), DodgerBlue = new(), Orange = new(), LimeGreen = new(), Magenta = new(), Gold = new(), Aqua = new(), Red = new(), Green = new(); } }
namespace NinjaTrader.Gui { }
namespace NinjaTrader.Data { public enum BarsPeriodType { Tick, Second, Minute, Day, Week, Month, Year } public sealed class BarsPeriod { public BarsPeriodType BarsPeriodType = BarsPeriodType.Minute; public int Value = 15; } }
namespace NinjaTrader.NinjaScript
{
    using NinjaTrader.Data;
    using System.Windows.Media;
    public enum State { SetDefaults, Configure, DataLoaded, Historical, Realtime, Terminated }
    public enum Calculate { OnBarClose, OnEachTick, OnPriceChange }
    public enum Priority { Low, Medium, High }
    public enum MaximumBarsLookBack { TwoHundredFiftySix, Infinite }
    public interface ISeries<T> { T this[int barsAgo] { get; } }
    // one series: bar m of series S; [barsAgo] = bar CurrentBars[S] - barsAgo of that series
    public sealed class PriceSeries : ISeries<double>
    {
        public readonly NinjaScriptBase O; public readonly int S; public readonly int K;
        public PriceSeries(NinjaScriptBase o, int s, int k) { O = o; S = s; K = k; }
        public double this[int ago] { get { int m = O.CurrentBars[S] - ago; if (ago < 0 || m < 0) throw new ArgumentOutOfRangeException("barsAgo " + ago + " on series " + S); return K == 4 ? (O.Px(S, m, 1) + O.Px(S, m, 2)) / 2 : K == 5 ? (O.Px(S, m, 1) + O.Px(S, m, 2) + O.Px(S, m, 3)) / 3 : O.Px(S, m, K); } }
    }
    public sealed class TimeSeriesN { readonly NinjaScriptBase O; readonly int S; public TimeSeriesN(NinjaScriptBase o, int s) { O = o; S = s; } public DateTime this[int ago] => O.TimeOf(S, O.CurrentBars[S] - ago); }
    public sealed class Series<T> : ISeries<T> { readonly Dictionary<int, T> v = new(); readonly NinjaScriptBase O; public Series(NinjaScriptBase o) { O = o; } public T this[int ago] { get => v.TryGetValue(O.CurrentBars[0] - ago, out var x) ? x : default; set => v[O.CurrentBars[0] - ago] = value; } }
    public sealed class Indexed<T> { readonly Func<int, T> f; public Indexed(Func<int, T> f) { this.f = f; } public T this[int i] => f(i); }
    public abstract class NinjaScriptBase
    {
        public string Name, Description; public bool IsOverlay, IsSuspendedWhileInactive; public Calculate Calculate; public MaximumBarsLookBack MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
        public State State { get; set; } public int BarsInProgress { get; set; } public int[] CurrentBars = new int[64]; public BarsPeriod BarsPeriod = new();
        public List<string> BsvAdded = new(); public List<string> BsvAlerts = new(); public Func<int, int, int, double> BsvPx; public Func<int, int, DateTime> BsvTime; public Func<int, int, double> BsvRsi;
        public double Px(int s, int m, int k) => BsvPx(s, m, k); public DateTime TimeOf(int s, int m) => BsvTime(s, m);
        public Indexed<PriceSeries> Opens => new(s => new PriceSeries(this, s, 0)); public Indexed<PriceSeries> Highs => new(s => new PriceSeries(this, s, 1));
        public Indexed<PriceSeries> Lows => new(s => new PriceSeries(this, s, 2)); public Indexed<PriceSeries> Closes => new(s => new PriceSeries(this, s, 3));
        public Indexed<PriceSeries> Medians => new(s => new PriceSeries(this, s, 4)); public Indexed<PriceSeries> Typicals => new(s => new PriceSeries(this, s, 5));
        public Indexed<TimeSeriesN> Times => new(s => new TimeSeriesN(this, s)); public Indexed<int> BarsArray => new(s => s);
        public PriceSeries Open => Opens[BarsInProgress]; public PriceSeries High => Highs[BarsInProgress]; public PriceSeries Low => Lows[BarsInProgress]; public PriceSeries Close => Closes[BarsInProgress];
        public PriceSeries Median => Medians[BarsInProgress]; public PriceSeries Typical => Typicals[BarsInProgress]; public TimeSeriesN Time => Times[BarsInProgress];
        public int CurrentBar => CurrentBars[BarsInProgress];
        public List<Series<double>> Values = new();
        public void AddPlot(Brush b, string name) { Values.Add(new Series<double>(this)); }
        public void AddDataSeries(string instrumentName) { BsvAdded.Add(instrumentName); }
        public void AddDataSeries(BarsPeriodType t, int v) { BsvAdded.Add(t + " " + v); }
        public void Alert(string id, Priority p, string message, string sound, int rearmSeconds, Brush back, Brush fore) { BsvAlerts.Add(message); }
        protected virtual void OnStateChange() { } protected virtual void OnBarUpdate() { }
        public void BsvState(State s) { State = s; OnStateChange(); } public void BsvBar(int bip) { BarsInProgress = bip; OnBarUpdate(); }
    }
    public sealed class IndValue : ISeries<double>
    {
        readonly NinjaScriptBase O; readonly int S; readonly Func<int, double> V;
        public IndValue(NinjaScriptBase o, int s, Func<int, double> v) { O = o; S = s; V = v; }
        public double this[int ago] { get { int m = O.CurrentBars[S] - ago; if (ago < 0 || m < 0) throw new ArgumentOutOfRangeException("indicator barsAgo " + ago); return V(m); } }
    }
}
namespace NinjaTrader.NinjaScript.Indicators
{
    using NinjaTrader.NinjaScript;
    public sealed class RSI : ISeries<double> { readonly IndValue v; public RSI(IndValue v) { this.v = v; } public double this[int ago] => v[ago]; }
    public sealed class EMA : ISeries<double> { public double this[int ago] => throw new NotSupportedException(); }
    public sealed class SMA : ISeries<double> { public double this[int ago] => throw new NotSupportedException(); }
    public sealed class ATR : ISeries<double> { public double this[int ago] => throw new NotSupportedException(); }
    public abstract class Indicator : NinjaScriptBase
    {
        static int Sr(ISeries<double> s) => s is PriceSeries p ? (p.K == 3 ? p.S : throw new NotSupportedException("RSI of close only")) : throw new NotSupportedException();
        public RSI RSI(ISeries<double> input, int period, int smooth) { int s = Sr(input); return new RSI(new IndValue(this, s, m => BsvRsi(s, m))); }
        public EMA EMA(ISeries<double> input, int period) => new(); public SMA SMA(ISeries<double> input, int period) => new();
        public ATR ATR(int period) => new(); public ATR ATR(int barsArray, int period) => new();
    }
}
