// BSV harness: runs the generated cTrader indicator on BsvEval.SimBars. History bars first (IsLastBar false), then from
// live_from on each new bar is the last bar (two Calculate calls per bar = two ticks). Prints "<chart index>|<Print text>".
using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using BsvEval;
public static class CtHarness
{
    public static int Main(string[] a)
    {
        var d = JsonDocument.Parse(File.ReadAllText(a[0])).RootElement;
        var px = d.GetProperty("bars").EnumerateArray().Select(r => r.EnumerateArray().Select(x => x.GetDouble()).ToArray()).ToArray();
        var rsi = d.GetProperty("rsi").EnumerateArray().Select(x => x.ValueKind == JsonValueKind.Number ? x.GetDouble() : double.NaN).ToArray();
        var t0 = DateTime.SpecifyKind(DateTime.Parse(d.GetProperty("t0").GetString()), DateTimeKind.Utc); var step = TimeSpan.FromMinutes(d.GetProperty("step_min").GetInt32());
        bool up = d.GetProperty("round_up").GetBoolean(); int live = d.GetProperty("live_from").GetInt32(), nb = px.Length;
        double[][] Px(JsonElement e) => e.GetProperty("bars").EnumerateArray().Select(r => r.EnumerateArray().Select(x => x.GetDouble()).ToArray()).ToArray();
        double[] Rs(JsonElement e) => e.GetProperty("rsi").EnumerateArray().Select(x => x.ValueKind == JsonValueKind.Number ? x.GetDouble() : double.NaN).ToArray();
        SimBars Mk(string n, int off, double[][] p, double[] r) => new SimBars { Name = n, Off = off, Px = p, Rsi = r, T0 = t0, Step = step, RoundUp = up };
        var md = new Md { Chart = Mk("CHART", 0, px, rsi) };
        foreach (var p in d.GetProperty("symbols").EnumerateObject()) md.Syms[p.Name] = Mk(p.Name, p.Value.GetProperty("off").GetInt32(), Px(p.Value), Rs(p.Value));
        var type = typeof(CtHarness).Assembly.GetTypes().Single(t => t.IsSubclassOf(typeof(cAlgo.API.Indicator)) && !t.IsAbstract);
        var ind = (cAlgo.API.Indicator)Activator.CreateInstance(type);
        ind.Bars = md.Chart; ind.MarketData = md; ind.TimeFrame = cAlgo.API.TimeFrame.Minute15; ind.Indicators = new Acc();
        var prop = type.GetProperties().Single(p => p.GetCustomAttributes(typeof(cAlgo.API.ParameterAttribute), false).Length > 0);
        prop.SetValue(ind, d.GetProperty("list").GetString());
        var o = new StreamWriter(a[1]);
        void Sync(int n) { md.Chart.N = n + 1; foreach (var s in md.Syms.Values) s.N = Math.Max(0, Math.Min(s.Px.Length, n - s.Off + 1)); }
        void Flush(int n) { foreach (var m in ind.BsvPrints) o.WriteLine(n + "|" + m); ind.BsvPrints.Clear(); }
        Sync(0); ind.BsvInitialize(); Flush(-1);
        for (int n = 0; n < nb; n++)
        {
            Sync(n); ind.IsLastBar = n >= live;
            ind.Calculate(n); if (ind.IsLastBar) ind.Calculate(n);
            Flush(n);
        }
        o.Close();
        return 0;
    }
}
