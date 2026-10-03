// BSV stubs written from the public ATAS indicator API reference (https://docs.atas.net/en/).
// Compile check only: these are stand-ins with matching member names/signatures, no ATAS code, and they do nothing.
using System;
using System.Collections.Generic;

namespace ATAS.Indicators
{
    public interface IDataSeries
    {
        string Name { get; set; }
        bool IsHidden { get; set; }
    }

    public class ValueDataSeries : IDataSeries
    {
        private readonly Dictionary<int, decimal> _v = new Dictionary<int, decimal>();
        public ValueDataSeries(string id) { Id = id; Name = id; }
        public ValueDataSeries(string id, string name) { Id = id; Name = name; }
        public string Id { get; }
        public string Name { get; set; }
        public bool IsHidden { get; set; }
        public decimal this[int index] { get => _v.TryGetValue(index, out var x) ? x : 0m; set => _v[index] = value; }
    }

    public class IndicatorCandle
    {
        public decimal Open { get; set; }
        public decimal High { get; set; }
        public decimal Low { get; set; }
        public decimal Close { get; set; }
        public decimal Volume { get; set; }
        public DateTime Time { get; set; }
    }

    public static class IndicatorDataProvider
    {
        public const string NewPanel = "NewPanel";
    }

    public abstract class BaseIndicator
    {
        public int CurrentBar { get; protected set; }
        public List<IDataSeries> DataSeries { get; } = new List<IDataSeries> { new ValueDataSeries("Value") };
        public string Panel { get; set; } = "";
        public string Name { get; set; } = "";
        protected abstract void OnCalculate(int bar, decimal value);
    }

    public abstract class ExtendedIndicator : BaseIndicator
    {
        protected void AddAlert(string soundFile, string message) { }
    }

    public abstract class Indicator : ExtendedIndicator
    {
        protected Indicator(bool useCandles = false) { }
        public IndicatorCandle GetCandle(int bar) => new IndicatorCandle();
    }
}
