// BSV compile stubs for the cTrader Algo (cAlgo.API) members the generator's `ctrader` target uses.
// Signatures follow the official API reference (https://help.ctrader.com/ctrader-algo/references/): Indicator, Bars,
// DataSeries, TimeSeries (GetIndexByTime), MarketData.GetBars(TimeFrame), TimeFrame fields, IIndicatorsAccessor
// (ExponentialMovingAverage/SimpleMovingAverage/RelativeStrengthIndex(DataSeries, int), AverageTrueRange(int, MovingAverageType)
// and AverageTrueRange(Bars, int, MovingAverageType)). No behaviour: this only proves the output type-checks. Not a cTrader build.
using System;
namespace cAlgo.API
{
    public enum TimeZones { UTC }
    public enum AccessRights { None }
    public enum MovingAverageType { Simple, Exponential, WilderSmoothing }
    [AttributeUsage(AttributeTargets.Class)] public sealed class IndicatorAttribute : Attribute { public bool IsOverlay { get; set; } public TimeZones TimeZone { get; set; } public AccessRights AccessRights { get; set; } }
    [AttributeUsage(AttributeTargets.Property)] public sealed class OutputAttribute : Attribute { public OutputAttribute(string name) { } }
    public interface DataSeries { double this[int index] { get; } double LastValue { get; } int Count { get; } }
    public interface IndicatorDataSeries : DataSeries { new double this[int index] { get; set; } }
    public interface TimeSeries { DateTime this[int index] { get; } DateTime LastValue { get; } int Count { get; } int GetIndexByTime(DateTime dateTime); int GetIndexByExactTime(DateTime dateTime); }
    public interface Bars { int Count { get; } TimeFrame TimeFrame { get; } TimeSeries OpenTimes { get; } DataSeries OpenPrices { get; } DataSeries HighPrices { get; } DataSeries LowPrices { get; } DataSeries ClosePrices { get; } DataSeries MedianPrices { get; } DataSeries TypicalPrices { get; } }
    public sealed class TimeFrame
    {
        private readonly string n; private TimeFrame(string n) { this.n = n; } public override string ToString() => n;
        public static readonly TimeFrame Minute = new("Minute"), Minute2 = new("Minute2"), Minute3 = new("Minute3"), Minute4 = new("Minute4"), Minute5 = new("Minute5"), Minute6 = new("Minute6"),
            Minute7 = new("Minute7"), Minute8 = new("Minute8"), Minute9 = new("Minute9"), Minute10 = new("Minute10"), Minute15 = new("Minute15"), Minute20 = new("Minute20"), Minute30 = new("Minute30"),
            Minute45 = new("Minute45"), Hour = new("Hour"), Hour2 = new("Hour2"), Hour3 = new("Hour3"), Hour4 = new("Hour4"), Hour6 = new("Hour6"), Hour8 = new("Hour8"), Hour12 = new("Hour12"),
            Daily = new("Daily"), Day2 = new("Day2"), Day3 = new("Day3"), Weekly = new("Weekly"), Monthly = new("Monthly");
    }
    public interface MarketData { Bars GetBars(TimeFrame timeFrame); Bars GetBars(TimeFrame timeFrame, string symbolName); }
    public abstract class Algo
    {
        public Bars Bars => throw new NotImplementedException(); public MarketData MarketData => throw new NotImplementedException();
        public TimeFrame TimeFrame => throw new NotImplementedException(); public cAlgo.API.Indicators.IIndicatorsAccessor Indicators => throw new NotImplementedException();
        public void Print(object message) { } public void Print(string message, params object[] parameters) { }
    }
    public abstract class Indicator : Algo { public bool IsLastBar => false; protected virtual void Initialize() { } public abstract void Calculate(int index); }
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
