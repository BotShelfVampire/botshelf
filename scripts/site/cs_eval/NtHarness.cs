// BSV harness: runs the generated NinjaTrader indicator. State SetDefaults -> Configure (records AddDataSeries) -> DataLoaded, then one
// OnBarUpdate per closed bar per series in time order (shared timestamps: chart first, or reversed with "reverse_ties").
// Prints "<series>|<bar index>|<Alert message>".
using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using NinjaTrader.NinjaScript;
public static class NtHarness
{
    public static int Main(string[] a)
    {
        var d = JsonDocument.Parse(File.ReadAllText(a[0])).RootElement;
        var px = d.GetProperty("bars").EnumerateArray().Select(r => r.EnumerateArray().Select(x => x.GetDouble()).ToArray()).ToArray();
        var rsi = d.GetProperty("rsi").EnumerateArray().Select(x => x.ValueKind == JsonValueKind.Number ? x.GetDouble() : double.NaN).ToArray();
        var t0 = DateTime.SpecifyKind(DateTime.Parse(d.GetProperty("t0").GetString()), DateTimeKind.Utc); var step = TimeSpan.FromMinutes(d.GetProperty("step_min").GetInt32());
        bool rev = d.GetProperty("reverse_ties").GetBoolean(); int nb = px.Length;
        double[][] Px(JsonElement e) => e.GetProperty("bars").EnumerateArray().Select(r => r.EnumerateArray().Select(x => x.GetDouble()).ToArray()).ToArray();
        double[] Rs(JsonElement e) => e.GetProperty("rsi").EnumerateArray().Select(x => x.ValueKind == JsonValueKind.Number ? x.GetDouble() : double.NaN).ToArray();
        var syms = d.GetProperty("symbols").EnumerateObject().ToDictionary(p => p.Name, p => (off: p.Value.GetProperty("off").GetInt32(), px: Px(p.Value), rsi: Rs(p.Value)));
        var type = typeof(NtHarness).Assembly.GetTypes().Single(t => t.IsSubclassOf(typeof(NinjaTrader.NinjaScript.Indicators.Indicator)) && !t.IsAbstract);
        var ind = (NinjaTrader.NinjaScript.Indicators.Indicator)Activator.CreateInstance(type);
        for (int s = 0; s < ind.CurrentBars.Length; s++) ind.CurrentBars[s] = -1;
        ind.BsvState(State.SetDefaults); ind.BsvState(State.Configure);
        var ser = new[] { (off: 0, px, rsi) }.Concat(ind.BsvAdded.Select(n => syms.TryGetValue(n, out var o) ? o : throw new Exception("unknown instrument " + n))).ToArray();
        var off = ser.Select(x => x.off).ToArray();
        ind.BsvPx = (s, m, k) => m < ser[s].px.Length ? ser[s].px[m][k] : throw new Exception("future bar"); ind.BsvTime = (s, m) => t0 + (m + off[s]) * step; ind.BsvRsi = (s, m) => ser[s].rsi[m];
        ind.BsvState(State.DataLoaded);
        var ev = Enumerable.Range(0, off.Length).SelectMany(s => Enumerable.Range(0, ser[s].px.Length).Select(m => (close: m + off[s] + 1, s, m)))
            .OrderBy(e => e.close).ThenBy(e => rev ? -e.s : e.s).ToList();
        var o = new StreamWriter(a[1]);
        foreach (var e in ev)
        {
            if (e.close > nb) break; // the chart's last bar closes at nb
            ind.CurrentBars[e.s] = e.m; ind.BsvBar(e.s);
            foreach (var m in ind.BsvAlerts) o.WriteLine(e.s + "|" + e.m + "|" + m); ind.BsvAlerts.Clear();
        }
        o.Close();
        return 0;
    }
}
