#!/usr/bin/env node
import fs from 'node:fs';

const args = process.argv.slice(2);
const recipePath = args[0];
const targetIndex = args.indexOf('--target');
const target = targetIndex >= 0 ? args[targetIndex + 1] : 'pine-v6';

if (!recipePath) {
  console.error('Usage: node render.mjs <recipe.json> --target pine-v6|mql5|ctrader|mql4|ctrader-python|bookmap-python|ninjatrader|quantower|sierra-acsil|prorealtime|gocharting-lipi|motivewave|vela|jforex|easylanguage|atas|amibroker|thinkscript|tradovate|backtrader');
  process.exit(1);
}

const recipe = JSON.parse(fs.readFileSync(recipePath, 'utf8'));
validateRecipe(recipe);

const renderers = {
  'pine-v6': renderPine,
  'mql5': renderMql5,
  'ctrader': renderCTrader,
  'mql4': renderMql4,
  'ctrader-python': renderCTraderPython,
  'bookmap-python': renderBookmapPython,
  'ninjatrader': renderNinja,
  'quantower': renderQuantower,
  'sierra-acsil': renderSierra,
  'prorealtime': renderProRealTime,
  'gocharting-lipi': renderLipi,
  'motivewave': renderMotiveWave,
  'vela': renderVela,
  'jforex': renderJForex,
  'easylanguage': renderEasyLanguage,
  'atas': renderAtas,
  'amibroker': renderAmiBroker,
  'thinkscript': renderThinkScript,
  'tradovate': renderTradovate,
  'backtrader': renderBacktrader,
  'backtesting-py': renderBacktestingPy,
  'nautilus': renderNautilus
};

if (!renderers[target]) {
  throw new Error(`Unsupported target: ${target}`);
}

process.stdout.write(renderFor(target, renderers[target], recipe));

function validateRecipe(recipe) {
  if (recipe?.schemaVersion !== '0.1') throw new Error('schemaVersion must be 0.1');
  if (!recipe?.name || !Array.isArray(recipe?.blocks)) throw new Error('name and blocks are required');

  const ids = new Set();
  for (const block of recipe.blocks) {
    if (!/^[a-z][a-z0-9_]*$/.test(block.id || '')) throw new Error(`Invalid block id: ${block.id}`);
    if (ids.has(block.id)) throw new Error(`Duplicate block id: ${block.id}`);
    ids.add(block.id);
    if (!block.type || typeof block.params !== 'object') throw new Error(`Invalid block: ${block.id}`);
  }

  for (const block of recipe.blocks) {
    const p = block.params;
    for (const ref of referencesFor(block)) {
      if (!ids.has(ref) && !['open','high','low','close','hl2','hlc3','ohlc4'].includes(ref)) {
        throw new Error(`Block ${block.id} references missing id: ${ref}`);
      }
    }
    if (block.type === 'signal.threshold' && p.right !== undefined && (typeof p.right !== 'string' || !p.right)) throw new Error(`Block ${block.id}: right must be a block id or price`);
    if (block.type === 'signal.recent') {  // true if `signal` was true on one of the `bars` bars before this one (the current bar is not counted)
      const sg = recipe.blocks.find(x => x.id === p.signal), at = (id) => recipe.blocks.findIndex(x => x.id === id);
      if (!Number.isInteger(p.bars) || p.bars < 1 || p.bars > 50) throw new Error(`Block ${block.id}: bars must be an integer from 1 to 50`);
      if (!sg || !isBoolType(sg.type) || /^(alert|scanner)\./.test(sg.type) || sg.type === 'signal.recent' || at(sg.id) > at(block.id)) throw new Error(`Block ${block.id}: signal must be an earlier signal or filter block (not another signal.recent)`);
    }
    if (block.type === 'scanner.symbol_set') {  // symbols: optional fixed list (Pine needs it; MQL5 uses Market Watch when it is empty); signal: optional, default = the first alert.condition
      const sy = p.symbols, sg = recipe.blocks.find(x => x.id === p.signal), at = (id) => recipe.blocks.findIndex(x => x.id === id);
      if (sy !== undefined && (!Array.isArray(sy) || sy.length < 1 || sy.length > 40 || new Set(sy).size !== sy.length || !sy.every(x => typeof x === 'string' && /^[A-Za-z0-9_.:!&\/-]{1,40}$/.test(x)))) throw new Error(`Block ${block.id}: symbols must be 1 to 40 different symbol names (letters, digits and _ . : ! & / -)`);
      if (p.signal !== undefined && (!sg || !isBoolType(sg.type) || /^(alert|scanner)\./.test(sg.type) || at(sg.id) > at(block.id))) throw new Error(`Block ${block.id}: signal must be an earlier signal or filter block`);
    }
    if (['indicator.ema','indicator.sma','indicator.rsi','indicator.atr'].includes(block.type)) {
      if (!Number.isInteger(p.length) || p.length < 1 || p.length > 10000) {
        throw new Error(`Block ${block.id} has invalid length`);
      }
    }
  }
}

// Higher timeframe (data.higher_timeframe + timeframeRef). Real higher-timeframe values are rendered only on targets
// where a BSV check runs them (htfRealTargets()): built from closed higher-timeframe bars only, so no value repaints or
// looks ahead. On every other target the blocks that use a higher timeframe are rendered as unsupported stubs (empty
// value / false signal + a TODO line) instead of being computed on the chart timeframe.
function htfRealTargets() { return ['backtrader', 'backtesting-py', 'nautilus', 'tradovate']; }  // tradovate: JS per-bar state, checked by check_tradovate.mjs (node:vm stub)
function htfMinutes(b) {
  const t = String((b && b.params && b.params.timeframe) ?? '').trim().toUpperCase();
  if (/^\d+$/.test(t)) return Number(t) >= 1 && Number(t) <= 10080 ? Number(t) : null;
  const m = t.match(/^(\d*)D$/); if (m) return (Number(m[1]) || 1) <= 7 ? (Number(m[1]) || 1) * 1440 : null;
  return null;  // weeks, months and other strings: not rendered
}
function htfSource(recipe, b) {  // the data.higher_timeframe block an indicator reads, or null when it cannot be rendered
  const r = b.params && b.params.timeframeRef, d = r && blockMap(recipe).get(r);
  if (!d || d.type !== 'data.higher_timeframe' || htfMinutes(d) === null || !/^indicator\.(ema|sma|rsi|atr)$/.test(b.type)) return null;
  return d;
}
// Pine v6, MQL5 and MQL4 read the higher timeframe with each platform's officially documented closed-bar idiom
// (Pine: request.security(..., expr[1], lookahead = barmerge.lookahead_on); MQL5/MQL4: iBarShift(...) + 1 = the last
// closed higher-timeframe bar; NinjaTrader 8: AddDataSeries + Calculate.OnBarClose, where the added series' [0] is its
// last closed bar; cTrader: MarketData.GetBars(tf) + GetIndexByTime(chart bar open) stepped back with the documented
// OpenTimes indexer to a bar opened at or before that time, minus 1 = a closed bar under any GetIndexByTime rounding).
// BSV cannot run these platforms: the pattern is enforced by scripts/site/check_htf.py
// and the output stays UNTESTED_RUNTIME. Doc URLs: DECISIONS.md "Higher timeframe on Pine v6 / MQL5 / MQL4".
function htfIdiomTargets() { return ['pine-v6', 'mql5', 'mql4', 'ninjatrader', 'ctrader', 'amibroker', 'thinkscript']; }
// cTrader TimeFrame fields (https://help.ctrader.com/ctrader-algo/references/Period/TimeFrame/) by minutes; Monthly has no fixed length.
function htfCTraderTfs() { return { 1: 'Minute', 2: 'Minute2', 3: 'Minute3', 4: 'Minute4', 5: 'Minute5', 6: 'Minute6', 7: 'Minute7', 8: 'Minute8', 9: 'Minute9', 10: 'Minute10',
  15: 'Minute15', 20: 'Minute20', 30: 'Minute30', 45: 'Minute45', 60: 'Hour', 120: 'Hour2', 180: 'Hour3', 240: 'Hour4', 360: 'Hour6', 480: 'Hour8', 720: 'Hour12',
  1440: 'Daily', 2880: 'Day2', 4320: 'Day3', 10080: 'Weekly' }; }
function htfTf(t, minutes) {  // the target's own timeframe name, or null when the target cannot read that timeframe
  if (minutes === null || minutes === undefined) return null;
  const HTF_MQL_PERIOD = { 1: 'M1', 2: 'M2', 3: 'M3', 4: 'M4', 5: 'M5', 6: 'M6', 10: 'M10', 12: 'M12', 15: 'M15', 20: 'M20', 30: 'M30',
    60: 'H1', 120: 'H2', 180: 'H3', 240: 'H4', 360: 'H6', 480: 'H8', 720: 'H12', 1440: 'D1', 10080: 'W1' };
  if (t === 'pine-v6') return minutes % 1440 === 0 ? `${minutes / 1440}D` : (minutes <= 1440 ? String(minutes) : null);
  if (t === 'mql5') return HTF_MQL_PERIOD[minutes] ? 'PERIOD_' + HTF_MQL_PERIOD[minutes] : null;
  if (t === 'mql4') return [1, 5, 15, 30, 60, 240, 1440, 10080].includes(minutes) ? 'PERIOD_' + HTF_MQL_PERIOD[minutes] : null;  // MT4 standard periods only
  if (t === 'ctrader') return htfCTraderTfs()[minutes] || null;
  if (t === 'thinkscript') return ({ 1: 'MIN', 2: 'TWO_MIN', 3: 'THREE_MIN', 4: 'FOUR_MIN', 5: 'FIVE_MIN', 10: 'TEN_MIN', 15: 'FIFTEEN_MIN', 20: 'TWENTY_MIN', 30: 'THIRTY_MIN',
    60: 'HOUR', 120: 'TWO_HOURS', 240: 'FOUR_HOURS', 1440: 'DAY', 2880: 'TWO_DAYS', 4320: 'THREE_DAYS', 5760: 'FOUR_DAYS' })[minutes] || null;  // AggregationPeriod constants
  if (t === 'amibroker') return minutes === 1440 ? 'inDaily' : (minutes < 1440 ? String(minutes * 60) : null);  // TimeFrameSet interval in seconds
  if (t === 'ninjatrader') return minutes === 10080 ? 'BarsPeriodType.Week, 1' : (minutes % 1440 === 0 ? `BarsPeriodType.Day, ${minutes / 1440}` : `BarsPeriodType.Minute, ${minutes}`);
  return String(minutes);
}
function htfTfOf(recipe, b) {  // after htfPrep: the timeframe name of an indicator computed on a higher timeframe, else null
  if (!recipe.bsvHtfReal || !b || !b.params || !b.params.timeframeRef || !/^indicator\./.test(b.type)) return null;
  return htfTf(recipe.bsvHtfTarget, htfMinutes(blockMap(recipe).get(b.params.timeframeRef)));
}
function htfDataUsed(recipe, b) { return b.type === 'data.higher_timeframe' && !(b.params && b.params.bsvHtfOf) && recipe.blocks.some(x => x.params && x.params.timeframeRef === b.id && htfTfOf(recipe, x)); }
function htfPrep(recipe, t) {
  const out = JSON.parse(JSON.stringify(recipe));
  const idiom = htfIdiomTargets().includes(t), real = idiom || htfRealTargets().includes(t);
  out.bsvHtfReal = real;
  out.bsvHtfTarget = t;
  out.blocks = out.blocks.map(b => {
    if (!(b.params && b.params.timeframeRef)) return b;
    if (real && htfSource(recipe, b) && htfTf(t, htfMinutes(htfSource(recipe, b))) !== null) return b;
    return { id: b.id, type: 'data.higher_timeframe', params: Object.assign({}, b.params, { bsvHtfOf: b.type }) };
  });
  return out;
}
function renderFor(t, fn, recipe) { const r = htfPrep(recipe, t); r.bsvRangeReal = rangeRealTargets().includes(t); r.bsvPivotReal = r.bsvRangeReal || t === 'tradovate' || t === 'amibroker' || t === 'thinkscript' || t === 'pine-v6' || t === 'mql5'; r.bsvRangePine = t === 'pine-v6'; r.bsvRangeMql5 = t === 'mql5'; r.bsvRangeJs = t === 'tradovate'; r.bsvRangeAfl = t === 'amibroker'; r.bsvRangeTs = t === 'thinkscript'; r.bsvScanTarget = scanRealTargets().includes(t) ? t : null; r.bsvScanCs = (t === 'ninjatrader' || t === 'ctrader') && recipe.blocks.some(b => b.type === 'scanner.symbol_set'); return scanNotice(fn(r)); }
// scanner.symbol_set (batch 28): scan one signal on several symbols, each at its own bar that just closed. Rendered only on targets that
// can read other symbols natively and where a BSV check runs the scan: Pine v6 (request.security per listed symbol, at most 40 unique
// request.* calls per script), MQL5 (SymbolSelect + per-symbol indicator handles, or every Market Watch symbol), and the three Python
// targets (a dict of symbol -> bars). Every other target gets an explicit notice instead of a silent TODO.
// Batch 30: NinjaTrader 8 (AddDataSeries per listed symbol, evaluated in each symbol's own OnBarUpdate) and cTrader (MarketData.GetBars per
// symbol, once per new chart bar). On these two, pivots and divergence are generated only inside recipes with a symbol scan (bsvScanCs),
// so every other recipe's output stays byte-identical; both are run in the BSV C# evaluators (check_cs_scan.py), not on the platforms.
function scanRealTargets() { return ['pine-v6', 'mql5', 'backtrader', 'backtesting-py', 'nautilus', 'ninjatrader', 'ctrader']; }
function scanNotice(out) { return out.replace(/(TODO unsupported block scanner\.symbol_set: [a-z][a-z0-9_]*)(?![a-z0-9_]| - )/g, '$1 - unsupported for this target: run one chart per symbol (this script reads only the chart symbol)'); }
function scanSignal(recipe, b) { const p = b.params || {}; if (p.signal) return p.signal; const a = recipe.blocks.find(x => x.type === 'alert.condition' && x.params && x.params.when); return a ? a.params.when : null; }
function scanSymbols(b) { return Array.isArray(b?.params?.symbols) ? b.params.symbols : []; }
function scanSigOk(recipe, id, seen = new Set()) {  // the scanned signal and everything it reads are rendered for real on this target
  const b = blockMap(recipe).get(id);
  if (!b) return isPrice(id);
  if (seen.has(id)) return true;
  seen.add(id);
  const p = b.params || {}, all = () => referencesFor(b).every(x => scanSigOk(recipe, x, seen));
  if (p.timeframeRef) return false;
  if (/^indicator\.(ema|sma|rsi|atr)$/.test(b.type) || b.type === 'filter.session') return true;
  if (/^signal\.(cross|threshold|combine|recent)$/.test(b.type)) return all();
  if (b.type === 'structure.range') return rangeOk(recipe, b) && all();
  if (b.type === 'signal.breakout') return breakoutOk(recipe, b) && all();
  if (b.type === 'structure.pivot') return pivotOk(recipe, b);
  if (b.type === 'signal.liquidity_sweep') return sweepOk(recipe, b) && all();
  if (b.type === 'signal.divergence') return divergenceOk(recipe, b) && all();
  return false;
}
function scanWhyNot(recipe, b) {  // empty string = rendered
  const sig = scanSignal(recipe, b), sb = sig && blockMap(recipe).get(sig), n = scanSymbols(b).length;
  if (!recipe.bsvScanTarget) return 'unsupported for this target: run one chart per symbol (this script reads only the chart symbol)';
  if (!sb || !isBoolType(sb.type) || /^(alert|scanner)\./.test(sb.type)) return 'nothing to scan: set params.signal or add an alert.condition, or run one chart per symbol';
  if (recipe.blocks.some(x => x.params && x.params.timeframeRef)) return 'not rendered with higher-timeframe blocks: run one chart per symbol';
  if ((recipe.bsvScanTarget === 'ninjatrader' || recipe.bsvScanTarget === 'ctrader') && (n < 1 || n > 40)) return `list 1 to 40 symbols in params.symbols (${recipe.bsvScanTarget === 'ninjatrader' ? 'AddDataSeries needs hard-coded instrument names' : 'the symbol list parameter starts from it'}), or run one chart per symbol`;
  if ((recipe.bsvScanTarget === 'ninjatrader' || recipe.bsvScanTarget === 'ctrader') && recipe.blocks.find(x => x.type === 'scanner.symbol_set') !== b) return 'one symbol scan per script on this target: run one chart per symbol';
  if (recipe.bsvScanTarget === 'pine-v6' && (n < 1 || n > 40)) return 'TradingView scripts cannot read your watchlist: list 1 to 40 symbols in params.symbols (at most 40 unique request.* calls per script), or run one chart per symbol';
  if (!scanSigOk(recipe, sig)) return `the scanned signal ${sig} is not fully rendered on this target: run one chart per symbol`;
  return '';
}
function scanOk(recipe, b) { return !!b && b.type === 'scanner.symbol_set' && scanWhyNot(recipe, b) === ''; }
// structure.range (high/low of each window where a session/signal is true; reset when a new window starts; after the
// window the last window's values stay) and signal.breakout (first close beyond the finished window's high or low).
// Rendered only where a BSV check runs them; elsewhere they stay TODO.
function rangeRealTargets() { return ['backtrader', 'backtesting-py', 'nautilus']; }
function rangeKeys(b) { const t = Array.isArray(b?.params?.track) ? b.params.track : []; return t.filter((x, i) => (x === 'high' || x === 'low') && t.indexOf(x) === i); }
function rangeOk(recipe, b) {
  if (!(recipe.bsvRangeReal || recipe.bsvRangeJs || recipe.bsvRangeAfl || recipe.bsvRangeTs || recipe.bsvRangePine || recipe.bsvRangeMql5) || !b || b.type !== 'structure.range') return false;  // Python targets + Tradovate (per-bar state checked in node:vm) + AmiBroker (HighestSince / ValueWhen, checked in the BSV AFL evaluator) + thinkScript (CompoundValue + self reference [1], checked in the BSV thinkScript evaluator)
  const d = blockMap(recipe).get(b.params?.during), t = Array.isArray(b.params?.track) ? b.params.track : [];
  return !!d && isBoolType(d.type) && t.length > 0 && rangeKeys(b).length === t.length;
}
function breakoutOk(recipe, b) {
  return !!b && b.type === 'signal.breakout' && ['either', 'above', 'below'].includes(b.params?.direction || 'either') && rangeOk(recipe, blockMap(recipe).get(b.params?.range)) && rangeKeys(blockMap(recipe).get(b.params.range)).length === 2;
}
function pyRangeLines() {
  return [
    'def bsv_range_step(st, inside, h, l):  # st = [inside on the previous bar, high, low]',
    '    if inside:',
    '        if not st[0]:',
    '            st[1], st[2] = h, l  # a new window starts: reset',
    '        else:',
    '            st[1], st[2] = max(st[1], h), min(st[2], l)',
    '    st[0] = inside',
    '    return st[1], st[2]  # during a window: so far; after it: the finished window; NaN before the first window',
    '',
    '',
    'def bsv_breakout(inside, hi, lo, c, pc, direction):  # first close beyond the finished window, on a closed bar',
    '    if inside or hi != hi or pc != pc:',
    '        return False',
    '    up, dn = c > hi and pc <= hi, c < lo and pc >= lo',
    '    return (up or dn) if direction == "either" else (up if direction == "above" else dn)',
    '',
    '',
  ];
}
// structure.pivot (a bar whose value is strictly above / below the `left` bars before it and at least as high / low as
// the `right` bars after it, so a flat top counts once, at its first bar; known only `right` bars later, so no lookahead; the last confirmed pivot high / low is held),
// visual.zone (two lines: the high and low of a range or pivot) and alert.webhook (a JSON payload printed once per
// completed bar where the condition holds; the starter never sends it). Rendered only where a BSV check runs them.
function pivotOk(recipe, b) {
  if (!(recipe.bsvRangeReal || recipe.bsvPivotReal || recipe.bsvScanCs) || !b || b.type !== 'structure.pivot') return false;  // Python targets + Tradovate (per-bar state checked in node:vm); NinjaTrader / cTrader only in scan recipes
  const q = b.params || {}, n = (x) => Number.isInteger(x) && x >= 1 && x <= 50;
  return n(q.left) && n(q.right) && ['close', 'high_low'].includes(q.source || 'close');
}
function zoneOk(recipe, b) {
  if (!(recipe.bsvRangeReal || recipe.bsvPivotReal) || !b || b.type !== 'visual.zone') return false;  // Tradovate: pivot and range zones (rangeOk accepts bsvRangeJs)
  const d = blockMap(recipe).get(b.params?.source);
  return !!d && (pivotOk(recipe, d) || (rangeOk(recipe, d) && rangeKeys(d).length === 2));
}
function webhookOk(recipe, b) {
  if (!(recipe.bsvRangeReal || recipe.bsvRangeJs || recipe.bsvRangePine || recipe.bsvRangeMql5) || !b || b.type !== 'alert.webhook') return false;  // Tradovate: built per bar, drawn as W dots, never sent; Pine: alert() once per bar close (keys / texts without quotes, backslashes or control characters)
  const q = b.params || {}, w = blockMap(recipe).get(q.when), pl = q.payload;
  if (!w || !isBoolType(w.type) || w.type === 'alert.webhook' || !pl || typeof pl !== 'object' || Array.isArray(pl) || !Object.keys(pl).length) return false;
  if ((recipe.bsvRangePine || recipe.bsvRangeMql5) && !Object.entries(pl).every(([k, x]) => !/["\\\x00-\x1f]/.test(k) && (typeof x !== 'string' || !/["\\\x00-\x1f]/.test(x)) && (typeof x !== 'number' || Number.isFinite(x)))) return false;
  return Object.values(pl).every(x => ['number', 'boolean'].includes(typeof x) || (typeof x === 'string' && [...x.matchAll(/\{\{([^}]*)\}\}/g)].every(m => ['symbol', 'timeframe', 'time', 'open', 'high', 'low', 'close'].includes(m[1]))));
}
// signal.liquidity_sweep (a candidate only): on a completed bar, the wick goes beyond the last pivot high / low known
// before this bar by at least minAtrFraction x ATR (this bar's ATR) and the close is back inside that level.
// signal.divergence (regular): a newly confirmed price pivot high above the previous pivot high while the oscillator at
// those two pivot bars is lower (bearish), or the mirror for pivot lows (bullish); true only on the bar that confirms
// the new pivot (`right` bars after it), using the pivot block's left / right / source. Python targets only.
function sweepOk(recipe, b) {
  if (!(recipe.bsvRangeReal || recipe.bsvPivotReal) || !b || b.type !== 'signal.liquidity_sweep') return false;
  const q = b.params || {}, m = blockMap(recipe), a = m.get(q.atr), f = q.minAtrFraction === undefined ? 0 : q.minAtrFraction;
  return pivotOk(recipe, m.get(q.pivot)) && !!a && a.type === 'indicator.atr' && !(a.params && a.params.timeframeRef) && typeof f === 'number' && Number.isFinite(f) && f >= 0 && f <= 10;
}
function divergenceOk(recipe, b) {
  if (!(recipe.bsvRangeReal || recipe.bsvPivotReal || recipe.bsvScanCs) || !b || b.type !== 'signal.divergence') return false;
  const q = b.params || {}, m = blockMap(recipe), pv = m.get(q.pivot), o = m.get(q.oscillator);
  if (!pivotOk(recipe, pv) || !o || !/^indicator\.(ema|sma|rsi|atr)$/.test(o.type) || (o.params && o.params.timeframeRef)) return false;
  return (q.price === undefined || q.price === (pv.params.source || 'close')) && ['both', 'bullish', 'bearish'].includes(q.direction || 'both');
}
function pySignalLines(recipe) {
  const L = [];
  if (recipe.blocks.some(b => sweepOk(recipe, b))) L.push(
    'def bsv_sweep(ph, pl, h, l, c, atr, frac):  # ph / pl = the last pivot high / low known before this bar; a candidate only',
    '    if atr != atr:',
    '        return False',
    '    up = ph == ph and h > ph and h - ph >= frac * atr and c < ph  # wick above the prior high, close back below it',
    '    dn = pl == pl and l < pl and pl - l >= frac * atr and c > pl  # wick below the prior low, close back above it',
    '    return bool(up or dn)',
    '',
    '');
  if (recipe.blocks.some(b => divergenceOk(recipe, b))) L.push(
    'def bsv_divergence_step(st, h, l, x, left, right, direction):  # st = [recent highs, lows, oscillator, previous pivot high (price, osc), previous pivot low]',
    '    st[0].append(h)',
    '    st[1].append(l)',
    '    st[2].append(x)',
    '    if len(st[0]) > left + right + 1:',
    '        del st[0][0], st[1][0], st[2][0]',
    '    bear = bull = False',
    '    if len(st[0]) == left + right + 1:  # the bar `right` bars ago is confirmed only now: no lookahead',
    '        p, o = st[0][left], st[2][left]',
    '        if all(p > y for y in st[0][:left]) and all(p >= y for y in st[0][left + 1:]):',
    '            bear = st[3] is not None and p > st[3][0] and o < st[3][1]  # higher price high, lower oscillator',
    '            st[3] = (p, o)',
    '        p, o = st[1][left], st[2][left]',
    '        if all(p < y for y in st[1][:left]) and all(p <= y for y in st[1][left + 1:]):',
    '            bull = st[4] is not None and p < st[4][0] and o > st[4][1]  # lower price low, higher oscillator',
    '            st[4] = (p, o)',
    '    return bool(bear or bull) if direction == "both" else bool(bear if direction == "bearish" else bull)',
    '',
    '');
  return L;
}
function pyPivotLines() {
  return [
    'def bsv_pivot_step(st, h, l, left, right):  # st = [recent highs, recent lows, last pivot high, last pivot low]',
    '    st[0].append(h)',
    '    st[1].append(l)',
    '    if len(st[0]) > left + right + 1:',
    '        del st[0][0], st[1][0]',
    '    if len(st[0]) == left + right + 1:  # the bar `right` bars ago is confirmed only now: no lookahead',
    '        x = st[0][left]',
    '        if all(x > y for y in st[0][:left]) and all(x >= y for y in st[0][left + 1:]):',
    '            st[2] = x',
    '        x = st[1][left]',
    '        if all(x < y for y in st[1][:left]) and all(x <= y for y in st[1][left + 1:]):',
    '            st[3] = x',
    '    return st[2], st[3]  # NaN until the first confirmed pivot',
    '',
    '',
  ];
}
function pyWebhookLines(recipe) {
  const hooks = recipe.blocks.filter(b => webhookOk(recipe, b));
  return [
    'BSV_SYMBOL = "SYMBOL"  # set your symbol for {{symbol}}',
    'BSV_TIMEFRAME = "TIMEFRAME"  # set your bar timeframe for {{timeframe}}',
    `BSV_WEBHOOKS = (${hooks.map(b => `(${pyText(b.id)}, json.loads(${pyText(JSON.stringify(b.params.payload), 4000)}))`).join(', ')}${hooks.length === 1 ? ',' : ''})`,
    '',
    '',
    'def bsv_webhook(payload, when, o, h, l, c):  # JSON payload with {{...}} filled in; this file prints it and never sends it',
    '    f = {"symbol": BSV_SYMBOL, "timeframe": BSV_TIMEFRAME, "time": when, "open": "%.10g" % o, "high": "%.10g" % h, "low": "%.10g" % l, "close": "%.10g" % c}',
    '    out = {}',
    '    for k, x in payload.items():',
    '        if isinstance(x, str):',
    '            for name, val in f.items():',
    '                x = x.replace("{{" + name + "}}", val)',
    '        out[k] = x',
    '    return json.dumps(out, separators=(",", ":"))',
    '',
    '',
  ];
}
function htfNotes(recipe, prefix) {  // one line per block that uses a higher timeframe, saying how this target treats it
  return recipe.blocks.filter(b => b.params && b.params.timeframeRef).map(b => b.type === 'data.higher_timeframe'
    ? `${prefix} TODO ${b.id}: ${b.params.bsvHtfOf || 'block'} on higher timeframe ${b.params.timeframeRef} is not computed for this target (left empty), never on the chart timeframe.`
    : `${prefix} ${b.id}: ${b.type} on higher timeframe ${b.params.timeframeRef} (closed higher-timeframe bars only).`);
}

function referencesFor(block) {
  const p = block.params || {};
  switch (block.type) {
    case 'signal.cross': return [p.left, p.right].filter(Boolean);
    case 'signal.threshold': return [p.left, p.right].filter(x => typeof x === 'string' && x);
    case 'signal.recent': return [p.signal].filter(Boolean);
    case 'signal.combine': return Array.isArray(p.signals) ? p.signals : [];
    case 'visual.plot': return [p.source].filter(Boolean);
    case 'alert.condition': return [p.when].filter(Boolean);
    case 'visual.table': return Array.isArray(p.fields) ? p.fields.filter(Boolean) : [];
    case 'structure.range': return [p.during].filter(Boolean);
    case 'signal.breakout': return [p.range].filter(Boolean);
    case 'visual.zone': return [p.source].filter(Boolean);
    case 'alert.webhook': return [p.when].filter(Boolean);
    case 'signal.liquidity_sweep': return [p.pivot, p.atr].filter(Boolean);
    case 'signal.divergence': return [p.pivot, p.oscillator].filter(Boolean);
    case 'scanner.symbol_set': return [p.signal].filter(Boolean);
    default: return [];
  }
}

// visual.table = a value panel: the listed fields' values on the latest bar. A field is shown only when it and every
// block it depends on is rendered by the generator; a field that depends on a block that is not rendered yet (or on a
// higher timeframe) gets a TODO line instead of a value that would be wrong.
function tableValueType(t) { return /^(indicator\.(ema|sma|rsi|atr)|signal\.(cross|threshold|combine)|filter\.session)$/.test(t || ''); }
function tableSpec(recipe, b) {
  const map = blockMap(recipe), p = b.params || {};
  const why = (ref, seen) => {
    if (!map.has(ref)) return isPrice(ref) ? '' : `${ref} is not defined`;
    if (seen.has(ref)) return '';
    seen.add(ref);
    const d = map.get(ref), q = d.params || {};
    if (q.timeframeRef && !(recipe.bsvHtfReal && htfSource(recipe, d)) && !(recipe.bsvRangePine && /^indicator\./.test(d.type) && htfTfOf(recipe, d))) return `${ref} uses higher timeframe ${q.timeframeRef}, which this target does not compute (not shown rather than computed on the chart timeframe)`;
    if (!tableValueType(d.type) && !rangeOk(recipe, d) && !breakoutOk(recipe, d)) return `${ref} (${d.type}) is not rendered yet`;
    for (const r of referencesFor(d)) { const w = why(r, seen); if (w) return w; }
    return '';
  };
  const fields = [], skipped = [];
  for (const f of (Array.isArray(p.fields) ? p.fields : [])) {
    const w = why(String(f), new Set());
    if (w) skipped.push({ id: String(f), reason: w });
    else if (map.get(f)?.type === 'structure.range') rangeKeys(map.get(f)).forEach(k => fields.push({ id: `${f}.${k}`, bool: false }));
    else fields.push({ id: String(f), bool: map.has(f) && isBoolType(map.get(f).type) });
  }
  return { id: b.id, title: String(p.title || b.id).replace(/[\r\n]/g, ' ').trim().slice(0, 80), fields, skipped };
}
function tableTodos(spec, prefix) {
  const out = spec.skipped.map(x => `${prefix} TODO ${spec.id}: visual.table field ${x.id} not shown — ${x.reason}.`);
  if (!spec.fields.length) out.push(`${prefix} TODO ${spec.id}: visual.table has no field that can be shown yet, so the panel is left out.`);
  return out;
}
function tableBlocks(recipe) { return recipe.blocks.filter(b => b.type === 'visual.table').map(b => tableSpec(recipe, b)); }

function sourceName(v = 'close') {
  const allowed = new Set(['open','high','low','close','hl2','hlc3','ohlc4']);
  if (!allowed.has(v)) throw new Error(`Unsupported price source: ${v}`);
  return v;
}

function q(s) {
  return JSON.stringify(String(s ?? ''));
}

function safeTitle(recipe) {
  return String(recipe.name).replace(/["\r\n]/g, ' ').trim();
}

function className(recipe) {
  const c = safeTitle(recipe).replace(/[^A-Za-z0-9]+/g, ' ').trim()
    .split(/\s+/).map(x => x.charAt(0).toUpperCase() + x.slice(1)).join('');
  return (c || 'BSVCustomTool').replace(/^[0-9]/, 'BSV$&');
}

function blockMap(recipe) {
  return new Map(recipe.blocks.map(b => [b.id, b]));
}

function renderPine(recipe) {
  const lines = [];
  const map = blockMap(recipe);

  lines.push('//@version=6');
  lines.push(`indicator(${q('BSV — ' + safeTitle(recipe))}, overlay=${recipe.overlay ? 'true' : 'false'})`);
  lines.push('');
  lines.push('// Generated by BSV Trader Tool Blocks.');
  lines.push('// Structural starter only: compile and inspect on your TradingView version before relying on it.');
  lines.push('');
  const pinePeriods = [...new Set(recipe.blocks.map(b => htfTfOf(recipe, b)).filter(Boolean))];
  if (pinePeriods.length) {
    lines.push('// Higher timeframe: last CLOSED higher-timeframe bar only, with the non-repainting idiom from the Pine Script v6 manual');
    lines.push('// (https://www.tradingview.com/pine-script-docs/concepts/repainting/): expr[1] + lookahead = barmerge.lookahead_on.');
    lines.push('// Not run by BSV (UNTESTED_RUNTIME). Higher-timeframe bars follow the symbol\'s session on TradingView.');
    for (const tf of pinePeriods) {
      lines.push(`if timeframe.in_seconds() >= timeframe.in_seconds(${q(tf)})`);
      lines.push(`    runtime.error(${q(`BSV: the higher timeframe ${tf} must be higher than the chart timeframe. Use a lower chart timeframe.`)})`);
    }
    lines.push('');
  }
  const pineInd = (b, expr) => {
    const tf = htfTfOf(recipe, b);
    if (!tf) return `${b.id} = ${expr}`;
    return `// ${b.id}: ${b.type} on higher timeframe ${tf}, last closed bar only\n${b.id} = request.security(syminfo.tickerid, ${q(tf)}, ${expr}[1], lookahead = barmerge.lookahead_on)`;
  };

  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema':
        lines.push(pineInd(b, `ta.ema(${sourceName(p.source)}, ${p.length})`));
        break;
      case 'indicator.sma':
        lines.push(pineInd(b, `ta.sma(${sourceName(p.source)}, ${p.length})`));
        break;
      case 'indicator.rsi':
        lines.push(pineInd(b, `ta.rsi(${sourceName(p.source)}, ${p.length})`));
        break;
      case 'indicator.atr':
        lines.push(pineInd(b, `ta.atr(${p.length})`));
        break;
      case 'data.higher_timeframe':
        if (htfDataUsed(recipe, b)) { lines.push(`// ${b.id}: higher timeframe ${b.params.timeframe} (read with request.security below, closed bars only)`); break; }
        lines.push(`// TODO unsupported block ${b.type}: ${b.id}`);
        break;
      case 'filter.session': {
        const session = String(p.session || '0000-2359');
        const tz = String(p.timezone || 'Etc/UTC');
        lines.push(`${b.id} = not na(time(timeframe.period, ${q(session)}, ${q(tz)}))`);
        break;
      }
      case 'signal.cross':
        lines.push(`${b.id} = ${p.direction === 'below' ? 'ta.crossunder' : 'ta.crossover'}(${p.left}, ${p.right})`);
        break;
      case 'signal.threshold': {
        const op = ['>','>=','<','<=','==','!='].includes(p.op) ? p.op : '>=';
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        lines.push(`${b.id} = ${p.left} ${op} ${p.right !== undefined ? p.right : Number(p.value)}`);
        break;
      }
      case 'signal.recent':
        lines.push(`// ${b.id}: ${p.signal} was true on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before this one`, `${b.id} = ${orOf(p.bars, k => `${p.signal}[${k}]`, ' or ')}`);
        break;
      case 'signal.combine': {
        const op = p.mode === 'any' ? ' or ' : ' and ';
        lines.push(`${b.id} = ${(p.signals || []).map(x => '(' + x + ')').join(op) || 'false'}`);
        break;
      }
      case 'structure.range': {
        if (!rangeOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id}`, `float ${b.id} = na`); break; }
        lines.push(`// ${b.id}: high / low so far inside the window (a new window resets), then the finished window held; na before the first window (ta.valuewhen, ta.highest / ta.lowest with ta.barssince)`,
          `${b.id}_in = ${map.get(p.during) && isBoolType(map.get(p.during).type) ? p.during : `(${p.during} != 0)`}`, `${b.id}_new = ${b.id}_in and not (bar_index > 0 and ${b.id}_in[1])`);
        for (const k of rangeKeys(b)) lines.push(`${b.id}_${k} = ta.valuewhen(${b.id}_in, ta.${k === 'high' ? 'highest' : 'lowest'}(${k}, ta.barssince(${b.id}_new) + 1), 0)`);
        break;
      }
      case 'signal.breakout': {
        if (!breakoutOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id}`, `${b.id} = false`); break; }
        const r = p.range, d = p.direction || 'either', okb = `not ${r}_in and not na(${r}_high)`;
        lines.push(`// ${b.id}: first close beyond the finished window, on a bar outside it (the close before was at or inside)`,
          `${b.id}_up = ${okb} and close > ${r}_high and close[1] <= ${r}_high`, `${b.id}_dn = ${okb} and close < ${r}_low and close[1] >= ${r}_low`,
          `${b.id} = ${d === 'either' ? `${b.id}_up or ${b.id}_dn` : d === 'above' ? `${b.id}_up` : `${b.id}_dn`}`);
        break;
      }
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id}`, `float ${b.id} = na`); break; }
        const [xh, xl] = (p.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], R = p.right, Lf = p.left;
        lines.push(`// ${b.id}: the bar ${R} bars ago is a pivot high if it is above the ${Lf} bars before it and at least as high as the ${R} after it (a flat top counts once); known only now, so no lookahead. Written with ta.highest / ta.lowest so the tie rule is explicit. The last confirmed pivot is held (na before the first).`,
          `${b.id}_ph = ${xh}[${R}] > ta.highest(${xh}, ${Lf})[${R + 1}] and ${xh}[${R}] >= ta.highest(${xh}, ${R})`,
          `${b.id}_pl = ${xl}[${R}] < ta.lowest(${xl}, ${Lf})[${R + 1}] and ${xl}[${R}] <= ta.lowest(${xl}, ${R})`,
          `${b.id}_high = ta.valuewhen(${b.id}_ph, ${xh}[${R}], 0)`, `${b.id}_low = ta.valuewhen(${b.id}_pl, ${xl}[${R}], 0)`);
        break;
      }
      case 'signal.liquidity_sweep': {
        if (!sweepOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id}`, `${b.id} = false`); break; }
        const v = p.pivot, a = p.atr, m = `${Number(p.minAtrFraction || 0)} * ${a}`, ph = `${v}_high[1]`, pl = `${v}_low[1]`;
        lines.push(`// ${b.id}: sweep candidate: the wick goes beyond the last pivot known before this bar by at least ${Number(p.minAtrFraction || 0)} x ATR and the close is back inside`,
          `${b.id} = not na(${a}) and ((not na(${ph}) and high > ${ph} and high - ${ph} >= ${m} and close < ${ph}) or (not na(${pl}) and low < ${pl} and ${pl} - low >= ${m} and close > ${pl}))`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id}`, `${b.id} = false`); break; }
        const pb = map.get(p.pivot), pq = pb.params, R = pq.right, [xh, xl] = (pq.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], o = p.oscillator, d = p.direction || 'both', v = pb.id;
        lines.push(`// ${b.id}: regular divergence, true on the bar that confirms the new pivot; ta.valuewhen(..., 1) = the pivot before it`,
          `${b.id}_bear = ${v}_ph and ${xh}[${R}] > ta.valuewhen(${v}_ph, ${xh}[${R}], 1) and ${o}[${R}] < ta.valuewhen(${v}_ph, ${o}[${R}], 1)`,
          `${b.id}_bull = ${v}_pl and ${xl}[${R}] < ta.valuewhen(${v}_pl, ${xl}[${R}], 1) and ${o}[${R}] > ta.valuewhen(${v}_pl, ${o}[${R}], 1)`,
          `${b.id} = ${d === 'both' ? `${b.id}_bear or ${b.id}_bull` : d === 'bearish' ? `${b.id}_bear` : `${b.id}_bull`}`);
        break;
      }
      case 'visual.zone': {
        if (!zoneOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id}`); break; }
        const t = String(p.title || b.id).slice(0, 50);
        lines.push(`// ${b.id}: zone drawn as two lines from ${p.source} (${map.get(p.source).type === 'structure.range' ? 'the window high / low' : 'last confirmed pivot high / low'})`,
          `plot(${p.source}_high, title=${q(t + ' high')}, color=color.red)`, `plot(${p.source}_low, title=${q(t + ' low')}, color=color.green)`);
        break;
      }
      case 'scanner.symbol_set': {
        if (!scanOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id} - ${scanWhyNot(recipe, b)}`); break; }
        const sig = scanSignal(recipe, b), sy = scanSymbols(b);
        lines.push(`// ${b.id}: scan ${sig} on each listed symbol (chart timeframe) at that symbol's bar that just closed. request.security(symbol, timeframe.period, ${sig}[1],`,
          '// lookahead = barmerge.lookahead_on) recomputes the signal on the requested symbol (Pine manual, Other timeframes and data: declared variables) and does not',
          `// repaint. TradingView scripts cannot read your watchlist, so edit the symbol inputs. ${sy.length} request.security call${sy.length === 1 ? '' : 's'} here; at most 40 unique request.* calls per script (64 on Ultimate).`);
        sy.forEach((x, k) => lines.push(`${b.id}_sym_${k + 1} = input.symbol(${q(x)}, ${q(`${b.id} ${k + 1}`)})`));
        sy.forEach((x, k) => lines.push(`${b.id}_${k + 1} = request.security(${b.id}_sym_${k + 1}, timeframe.period, ${sig}[1], lookahead = barmerge.lookahead_on)`));
        lines.push(`${b.id} = ${sy.map((x, k) => `${b.id}_${k + 1}`).join(' or ')}`, `${b.id}_list = ${sy.map((x, k) => `(${b.id}_${k + 1} ? ${b.id}_sym_${k + 1} + " " : "")`).join(' + ')}`);
        break;
      }
      case 'visual.table': break;  // value panels are drawn after all blocks (below)
      case 'alert.webhook':
        if (!webhookOk(recipe, b)) { lines.push(`// TODO unsupported block ${b.type}: ${b.id}`, `${b.id} = false`); break; }
        lines.push(`// ${b.id}: webhook condition (the JSON is sent with alert() at the end)`, `${b.id} = ${p.when}`);
        break;
      case 'visual.plot':
        lines.push(`plot(${p.source}, title=${q(p.title || p.source)})`);
        break;
      case 'alert.condition':
        lines.push(`alertcondition(${p.when}, title=${q(b.id)}, message=${q(p.message || b.id)})`);
        break;
      default:
        lines.push(`// TODO unsupported block ${b.type}: ${b.id}`);
        // declared stub so later lines that use it still compile (never true / na), like the other targets' TODO stubs
        if (isBoolType(b.type)) lines.push(`${b.id} = false`);
        else if (/^structure\./.test(b.type)) lines.push(`float ${b.id} = na`);
    }
  }

  const pv = (id) => String(id).replace('.', '_'), num = (x) => `str.tostring(${x}, "#.########")`;
  for (const t of tableBlocks(recipe)) {
    lines.push('');
    tableTodos(t, '//').forEach(x => lines.push(x));
    if (!t.fields.length) continue;
    lines.push(`// Value panel ${t.title} (visual.table): drawn on the last bar, which may still be forming, so [1] shows the bar that just closed (na shows as NaN)`,
      `var table T_${t.id} = table.new(position.top_right, 2, ${t.fields.length + 1})`, 'if barstate.islast', `    table.cell(T_${t.id}, 0, 0, ${q(t.title)})`);
    t.fields.forEach((x, k) => lines.push(`    table.cell(T_${t.id}, 0, ${k + 1}, ${q(x.id)})`, `    table.cell(T_${t.id}, 1, ${k + 1}, ${x.bool ? `${pv(x.id)}[1] ? "true" : "false"` : num(`${pv(x.id)}[1]`)})`));
  }
  const ph = { symbol: 'syminfo.ticker', timeframe: 'timeframe.period', time: 'str.format_time(time, "yyyy-MM-dd HH:mm", "UTC")', open: num('open'), high: num('high'), low: num('low'), close: num('close') };
  for (const b of recipe.blocks.filter(x => x.type === 'alert.webhook' && webhookOk(recipe, x))) {
    const parts = []; let lit = '{';
    Object.entries(b.params.payload).forEach(([k, x], n) => {
      lit += `${n ? ',' : ''}"${k}":`;
      if (typeof x !== 'string') { lit += JSON.stringify(x); return; }
      lit += '"';
      String(x).split(/(\{\{[^}]*\}\})/).forEach(seg => { const m = /^\{\{([^}]*)\}\}$/.exec(seg); if (m) { parts.push(q(lit), ph[m[1]]); lit = ''; } else lit += seg; });
      lit += '"';
    });
    parts.push(q(lit + '}'));
    lines.push('', `// ${b.id}: webhook JSON. TradingView sends it only after you create an alert on this script with "Any alert() function call" and your webhook URL;`,
      '// once per bar close, so only completed bars. {{time}} = bar open time in UTC. Not run by BSV on TradingView (UNTESTED_RUNTIME).',
      `if ${b.id}`, `    alert(${parts.filter(x => x !== '""').join(' + ')}, alert.freq_once_per_bar_close)`);
  }

  for (const b of recipe.blocks.filter(x => x.type === 'scanner.symbol_set' && scanOk(recipe, x))) {
    lines.push('', `// ${b.id}: one alert per bar listing the symbols whose ${scanSignal(recipe, b)} held on the bar that just closed (create an alert on this script with "Any alert() function call").`,
      '// Once per bar: the values come from closed bars only, so the first tick of the new bar already has them. Not run by BSV on TradingView (UNTESTED_RUNTIME).',
      `if ${b.id}`, `    alert(${q(`BSV scan ${b.id}: `)} + ${b.id}_list, alert.freq_once_per_bar)`);
  }
  lines.push('');
  lines.push('// End BSV generated starter.');
  return lines.join('\n') + '\n';
}

function renderMql5(recipe) {
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot'), zones = recipe.blocks.filter(b => b.type === 'visual.zone' && zoneOk(recipe, b));
  const divFull = recipe.blocks.some(b => b.type === 'signal.divergence' && divergenceOk(recipe, b));
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const allInds = recipe.blocks.filter(b => ['indicator.ema', 'indicator.sma', 'indicator.rsi', 'indicator.atr'].includes(b.type));
  const inds = allInds.filter(b => !htfTfOf(recipe, b)), htfInds = allInds.filter(b => htfTfOf(recipe, b));
  const htfPeriods = [...new Set(htfInds.map(b => htfTfOf(recipe, b)))];
  const htfOk = (list, at) => list.filter(r => htfTfOf(recipe, map.get(r))).map(r => `${val(r, at)} != EMPTY_VALUE && `).join('');
  const appliedPrice = { open: 'PRICE_OPEN', high: 'PRICE_HIGH', low: 'PRICE_LOW', close: 'PRICE_CLOSE', hl2: 'PRICE_MEDIAN', hlc3: 'PRICE_TYPICAL' };
  const scans = recipe.blocks.filter(b => b.type === 'scanner.symbol_set' && scanOk(recipe, b));
  const S = scans.length ? 'g_sym, _Period' : '_Symbol, _Period', SC = '_Symbol, _Period';  // block functions read g_sym when a symbol scan switches the symbol; chart-only lines use _Symbol
  const priceExpr = { open: `iOpen(${S}, i)`, high: `iHigh(${S}, i)`, low: `iLow(${S}, i)`, close: `iClose(${S}, i)`,
    hl2: `(iHigh(${S}, i) + iLow(${S}, i)) / 2.0`, hlc3: `(iHigh(${S}, i) + iLow(${S}, i) + iClose(${S}, i)) / 3.0`,
    ohlc4: `(iOpen(${S}, i) + iHigh(${S}, i) + iLow(${S}, i) + iClose(${S}, i)) / 4.0` };
  const val = (ref, at) => isPrice(ref) ? priceExpr[ref].replace(/, i\)/g, `, ${at})`) : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0 : 0.0)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0 && ${val(ref, at)} != EMPTY_VALUE)`;
  const colors = ['clrDodgerBlue', 'clrOrange', 'clrLimeGreen', 'clrMagenta', 'clrGold', 'clrAqua'];
  const L = [];
  L.push('// ORIGINAL BSV STARTER — MT5 / MQL5 custom indicator. Compile in MetaEditor (MT5) before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(recipe.overlay ? '#property indicator_chart_window' : '#property indicator_separate_window');
  L.push(`#property indicator_buffers ${plots.length + 2 * zones.length}`);
  L.push(`#property indicator_plots   ${plots.length + 2 * zones.length}`);
  plots.forEach((p, k) => {
    L.push(`#property indicator_type${k + 1}   DRAW_LINE`);
    L.push(`#property indicator_color${k + 1}  ${colors[k % colors.length]}`);
    L.push(`#property indicator_label${k + 1}  ${q(String(p.params?.title || p.params?.source || p.id).replace(/[\r\n]/g, ' '))}`);
  });
  zones.forEach((z, k) => { const t = String(z.params?.title || z.id).replace(/[\r\n]/g, ' ').slice(0, 50), n = plots.length + 2 * k + 1;  // zone = two lines (high, low)
    L.push(`#property indicator_type${n}   DRAW_LINE`, `#property indicator_color${n}  clrRed`, `#property indicator_label${n}  ${q(t + ' high')}`,
      `#property indicator_type${n + 1}   DRAW_LINE`, `#property indicator_color${n + 1}  clrGreen`, `#property indicator_label${n + 1}  ${q(t + ' low')}`); });
  L.push('');
  for (const p of plots) L.push(`double Buf_${p.id}[];`);
  for (const z of zones) L.push(`double Buf_${z.id}_high[];`, `double Buf_${z.id}_low[];`);
  for (const b of inds) L.push(`int    h_${b.id} = INVALID_HANDLE;`, `double A_${b.id}[];`);
  for (const b of htfInds) L.push(`int    h_${b.id} = INVALID_HANDLE; // higher timeframe ${htfTfOf(recipe, b)}`);
  for (const a of alerts) L.push(`datetime g_alert_${a.id} = 0;`);
  const hooks = recipe.blocks.filter(b => b.type === 'alert.webhook' && webhookOk(recipe, b)), tables = tableBlocks(recipe).filter(t => t.fields.length);
  for (const h of hooks) L.push(`datetime g_hook_${h.id} = 0;`);
  L.push(`#define BSV_WARMUP ${warmup(recipe)}`);
  for (const b of scans) {
    L.push(`input string InpScan_${b.id} = ${q(scanSymbols(b).join(','))}; // ${b.id}: symbols to scan, comma-separated without spaces; empty = every symbol in Market Watch`);
    L.push(`string   g_scan_${b.id}[];`);
    for (const x of inds) L.push(`int      g_scan_${b.id}_h_${x.id}[];`);
    L.push(`datetime g_scan_${b.id}_t = 0;`);
  }
  if (scans.length) L.push('string   g_sym = ""; // the symbol the block functions read: the chart symbol, or the symbol being scanned', '#define BSV_SCAN_MAX 100');
  L.push('');
  if (htfInds.length) {
    L.push('// Higher timeframe: value of the last CLOSED higher-timeframe bar for chart bar i. iBarShift (exact=false) finds the');
    L.push('// higher-timeframe bar containing the chart bar\'s open time; +1 is the bar before it, which has closed, so the forming');
    L.push('// bar is never read (no repaint, no lookahead). Docs: https://www.mql5.com/en/docs/series/ibarshift and');
    L.push('// https://www.mql5.com/en/docs/series/copybuffer (start_pos counts from the newest bar = 0). Not run by BSV (UNTESTED_RUNTIME).');
    L.push('// Higher-timeframe bars follow the broker server time in MT5, so daily/4h boundaries depend on the broker.');
    L.push('double BsvHtfAt(int handle, ENUM_TIMEFRAMES tf, int i)');
    L.push('{');
    L.push(`   int s = iBarShift(_Symbol, tf, iTime(${S}, i), false);`);
    L.push('   if (s < 0) return(EMPTY_VALUE);');
    L.push('   double v[1];');
    L.push('   if (CopyBuffer(handle, 0, s + 1, 1, v) != 1) return(EMPTY_VALUE);');
    L.push('   return(v[0]);');
    L.push('}');
    L.push('');
  }
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': case 'indicator.atr':
        if (htfTfOf(recipe, b)) L.push(`double V_${b.id}(int i) { return BsvHtfAt(h_${b.id}, ${htfTfOf(recipe, b)}, i); } // last closed ${htfTfOf(recipe, b)} bar only`);
        else L.push(`double V_${b.id}(int i) { return A_${b.id}[i]; }`);
        break;
      case 'data.higher_timeframe':
        if (htfDataUsed(recipe, b)) { L.push(`// ${b.id}: higher timeframe ${b.params.timeframe} (read through BsvHtfAt, closed bars only)`); break; }
        L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id}`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push(`// TODO ${b.id}: session ${p.session || ''} is evaluated in broker server time; convert from ${p.timezone || 'Etc/UTC'} for your broker.`);
        L.push(`bool S_${b.id}(int i) { MqlDateTime t; TimeToStruct(iTime(${S}, i), t); int m = t.hour * 60 + t.min; return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`bool S_${b.id}(int i) { return ${htfOk([p.left, p.right], 'i')}${htfOk([p.left, p.right], 'i+1')}${val(p.left, 'i')} ${gt} ${val(p.right, 'i')} && ${val(p.left, 'i+1')} ${le} ${val(p.right, 'i+1')}; }`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`bool S_${b.id}(int i) { return ${htfOk([p.left, p.right].filter(x => typeof x === 'string'), 'i')}${val(p.left, 'i')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'i') : Number(p.value)}; }`);
        break;
      case 'signal.recent':
        L.push(`bool S_${b.id}(int i) { return ${orOf(p.bars, k => bool(p.signal, `i+${k}`), ' || ')}; } // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before i`);
        break;
      case 'signal.combine':
        L.push(`bool S_${b.id}(int i) { return ${(p.signals || []).map(x => bool(x, 'i')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; }`);
        break;
      case 'structure.range': {
        if (!rangeOk(recipe, b)) { L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        L.push(`// ${b.id}: high / low so far inside the window (a new window resets), then the finished window held; EMPTY_VALUE before the first window.`,
          `// Scans back from bar i (series index: larger = older): first to the latest window bar, then to the start of that window. Checked in the BSV MQL5 model, not MT5.`);
        for (const k of rangeKeys(b)) { const P = k === 'high' ? 'iHigh' : 'iLow', F = k === 'high' ? 'MathMax' : 'MathMin';
          L.push(`double V_${b.id}_${k}(int i) { int n = Bars(${S}); int k = i; while (k < n && !S_${p.during}(k)) k++; if (k >= n) return(EMPTY_VALUE); double v = ${P}(${S}, k); while (k + 1 < n && S_${p.during}(k + 1)) { k++; v = ${F}(v, ${P}(${S}, k)); } return(v); }`); }
        break;
      }
      case 'signal.breakout': {
        if (!breakoutOk(recipe, b)) { L.push(`bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const r = p.range, d = p.direction || 'either', inn = `S_${map.get(r).params.during}(i)`;
        L.push(`// ${b.id}: first close beyond the finished window, on a bar outside it (the close before was at or inside)`,
          `bool S_${b.id}_up(int i) { double h = V_${r}_high(i); return !${inn} && h != EMPTY_VALUE && iClose(${S}, i) > h && iClose(${S}, i + 1) <= h; }`,
          `bool S_${b.id}_dn(int i) { double l = V_${r}_low(i); return !${inn} && l != EMPTY_VALUE && iClose(${S}, i) < l && iClose(${S}, i + 1) >= l; }`,
          `bool S_${b.id}(int i) { return ${d === 'either' ? `S_${b.id}_up(i) || S_${b.id}_dn(i)` : d === 'above' ? `S_${b.id}_up(i)` : `S_${b.id}_dn(i)`}; }`);
        break;
      }
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const [xh, xl] = (p.source || 'close') === 'high_low' ? ['iHigh', 'iLow'] : ['iClose', 'iClose'], R = p.right, Lf = p.left;
        L.push(`// ${b.id}: bar i confirms a pivot at bar i + ${R} (series index: larger = older): above the ${Lf} bars before it and at least as high as the ${R} after it`,
          `// (a flat top counts once); known only at bar i, so no lookahead. The last confirmed pivot is found by scanning back (EMPTY_VALUE before the first).`,
          `bool S_${b.id}_ph(int i) { int c = i + ${R}; if (c + ${Lf} >= Bars(${S})) return(false); double v = ${xh}(${S}, c); for (int k = 1; k <= ${Lf}; k++) if (${xh}(${S}, c + k) >= v) return(false); for (int k = 1; k <= ${R}; k++) if (${xh}(${S}, c - k) > v) return(false); return(true); }`,
          `bool S_${b.id}_pl(int i) { int c = i + ${R}; if (c + ${Lf} >= Bars(${S})) return(false); double v = ${xl}(${S}, c); for (int k = 1; k <= ${Lf}; k++) if (${xl}(${S}, c + k) <= v) return(false); for (int k = 1; k <= ${R}; k++) if (${xl}(${S}, c - k) < v) return(false); return(true); }`,
          `double V_${b.id}_high(int i) { int n = Bars(${S}); for (int k = i; k + ${R + Lf} < n; k++) if (S_${b.id}_ph(k)) return(${xh}(${S}, k + ${R})); return(EMPTY_VALUE); }`,
          `double V_${b.id}_low(int i) { int n = Bars(${S}); for (int k = i; k + ${R + Lf} < n; k++) if (S_${b.id}_pl(k)) return(${xl}(${S}, k + ${R})); return(EMPTY_VALUE); }`);
        break;
      }
      case 'signal.liquidity_sweep': {
        if (!sweepOk(recipe, b)) { L.push(`bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const v = p.pivot, fr = Number(p.minAtrFraction || 0);
        L.push(`// ${b.id}: sweep candidate: the wick goes beyond the last pivot known before bar i by at least ${fr} x ATR and the close is back inside`,
          `bool S_${b.id}(int i) { double a = ${val(p.atr, 'i')}; if (a == EMPTY_VALUE) return(false); double m = ${fr} * a; double ph = V_${v}_high(i + 1); double pl = V_${v}_low(i + 1); double h = iHigh(${S}, i); double l = iLow(${S}, i); double c = iClose(${S}, i); return (ph != EMPTY_VALUE && h > ph && h - ph >= m && c < ph) || (pl != EMPTY_VALUE && l < pl && pl - l >= m && c > pl); }`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { L.push(`bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const pb = map.get(p.pivot), pq = pb.params, R = pq.right, Lf = pq.left, [xh, xl] = (pq.source || 'close') === 'high_low' ? ['iHigh', 'iLow'] : ['iClose', 'iClose'], o = p.oscillator, d = p.direction || 'both', v = pb.id;
        L.push(`// ${b.id}: regular divergence, true on the bar that confirms the new pivot (bar i + ${R}), compared with the pivot before it (scanning back).`,
          `// Reads ${o} at both pivots, so OnCalculate copies the whole ${o} buffer.`,
          `bool S_${b.id}_bear(int i) { if (!S_${v}_ph(i)) return(false); int n = Bars(${S}); for (int k = i + 1; k + ${R + Lf} < n; k++) if (S_${v}_ph(k)) { double o1 = ${val(o, `i + ${R}`)}; double o0 = ${val(o, `k + ${R}`)}; return o1 != EMPTY_VALUE && o0 != EMPTY_VALUE && ${xh}(${S}, i + ${R}) > ${xh}(${S}, k + ${R}) && o1 < o0; } return(false); }`,
          `bool S_${b.id}_bull(int i) { if (!S_${v}_pl(i)) return(false); int n = Bars(${S}); for (int k = i + 1; k + ${R + Lf} < n; k++) if (S_${v}_pl(k)) { double o1 = ${val(o, `i + ${R}`)}; double o0 = ${val(o, `k + ${R}`)}; return o1 != EMPTY_VALUE && o0 != EMPTY_VALUE && ${xl}(${S}, i + ${R}) < ${xl}(${S}, k + ${R}) && o1 > o0; } return(false); }`,
          `bool S_${b.id}(int i) { return ${d === 'both' ? `S_${b.id}_bear(i) || S_${b.id}_bull(i)` : d === 'bearish' ? `S_${b.id}_bear(i)` : `S_${b.id}_bull(i)`}; }`);
        break;
      }
      case 'visual.zone':
        if (!zoneOk(recipe, b)) L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push(`// ${b.id}: zone drawn as two lines from ${p.source} (${map.get(p.source).type === 'structure.range' ? 'the window high / low' : 'last confirmed pivot high / low'})`);
        break;
      case 'visual.table':
        tableTodos(tableSpec(recipe, b), '//').forEach(x => L.push(x));
        break;
      case 'alert.webhook':
        if (!webhookOk(recipe, b)) L.push(`bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        break;
      case 'scanner.symbol_set':
        if (!scanOk(recipe, b)) L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id} - ${scanWhyNot(recipe, b)}`);
        else L.push(`// ${b.id}: symbol scan of ${scanSignal(recipe, b)} (OnInit builds the list, OnCalculate scans once per closed chart bar)`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push(`bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  if (tables.length) L.push('', 'string BsvNum(double v) { if (v == EMPTY_VALUE) return("n/a"); return(DoubleToString(v, 8)); } // value panels: n/a = no value yet');
  L.push('');
  L.push('int OnInit()');
  L.push('{');
  plots.forEach((p, k) => { L.push(`   SetIndexBuffer(${k}, Buf_${p.id}, INDICATOR_DATA);`); L.push(`   ArraySetAsSeries(Buf_${p.id}, true);`); });
  zones.forEach((z, k) => { for (const [j, s] of [[0, 'high'], [1, 'low']]) L.push(`   SetIndexBuffer(${plots.length + 2 * k + j}, Buf_${z.id}_${s}, INDICATOR_DATA);`, `   ArraySetAsSeries(Buf_${z.id}_${s}, true);`); });
  for (const tf of htfPeriods) L.push(`   if (PeriodSeconds(${tf}) <= PeriodSeconds(_Period)) { Print(${q(`BSV: the higher timeframe ${tf} must be higher than the chart timeframe. Use a lower chart timeframe.`)}); return(INIT_FAILED); }`);
  for (const b of allInds) {
    const p = b.params || {};
    const S = htfTfOf(recipe, b) ? `_Symbol, ${htfTfOf(recipe, b)}` : '_Symbol, _Period';
    const src = b.type === 'indicator.atr' ? 'close' : sourceName(p.source);
    const ap = appliedPrice[src] || 'PRICE_CLOSE';
    const note = (b.type !== 'indicator.atr' && !appliedPrice[src]) ? ' // TODO ohlc4 has no MQL5 applied price; using close' : '';
    if (b.type === 'indicator.ema') L.push(`   h_${b.id} = iMA(${S}, ${p.length}, 0, MODE_EMA, ${ap});${note}`);
    if (b.type === 'indicator.sma') L.push(`   h_${b.id} = iMA(${S}, ${p.length}, 0, MODE_SMA, ${ap});${note}`);
    if (b.type === 'indicator.rsi') L.push(`   h_${b.id} = iRSI(${S}, ${p.length}, ${ap});${note}`);
    if (b.type === 'indicator.atr') L.push(`   h_${b.id} = iATR(${S}, ${p.length});`);
    L.push(`   if (h_${b.id} == INVALID_HANDLE) return(INIT_FAILED);`);
    if (!htfTfOf(recipe, b)) L.push(`   ArraySetAsSeries(A_${b.id}, true);`);
  }
  const hcall = (b, sym) => { const p = b.params || {}, ap = appliedPrice[b.type === 'indicator.atr' ? 'close' : sourceName(p.source)] || 'PRICE_CLOSE';
    return b.type === 'indicator.ema' ? `iMA(${sym}, _Period, ${p.length}, 0, MODE_EMA, ${ap})` : b.type === 'indicator.sma' ? `iMA(${sym}, _Period, ${p.length}, 0, MODE_SMA, ${ap})` : b.type === 'indicator.rsi' ? `iRSI(${sym}, _Period, ${p.length}, ${ap})` : `iATR(${sym}, _Period, ${p.length})`; };
  if (scans.length) L.push('   g_sym = _Symbol;');
  for (const b of scans) {
    const n = `ns_${b.id}`;
    L.push(`   // ${b.id}: the scan list = InpScan_${b.id}, or every Market Watch symbol when it is empty (at most BSV_SCAN_MAX). SymbolSelect adds a listed symbol to Market Watch so its bars load.`,
      `   int ${n} = 0;`,
      `   if (StringLen(InpScan_${b.id}) > 0) ${n} = StringSplit(InpScan_${b.id}, ',', g_scan_${b.id});`,
      `   else { ${n} = SymbolsTotal(true); ArrayResize(g_scan_${b.id}, ${n}); for (int k = 0; k < ${n}; k++) g_scan_${b.id}[k] = SymbolName(k, true); }`,
      `   if (${n} < 0) ${n} = 0;`, `   if (${n} > BSV_SCAN_MAX) ${n} = BSV_SCAN_MAX;`, `   ArrayResize(g_scan_${b.id}, ${n});`);
    for (const x of inds) L.push(`   ArrayResize(g_scan_${b.id}_h_${x.id}, ${n});`);
    L.push(`   for (int k = 0; k < ${n}; k++)`, '   {', `      if (!SymbolSelect(g_scan_${b.id}[k], true)) Print(${q(`BSV scan ${b.id}: unknown symbol `)}, g_scan_${b.id}[k]);`);
    for (const x of inds) L.push(`      g_scan_${b.id}_h_${x.id}[k] = ${hcall(x, `g_scan_${b.id}[k]`)};`);
    L.push('   }');
  }
  L.push(`   IndicatorSetString(INDICATOR_SHORTNAME, ${q('BSV — ' + safeTitle(recipe))});`);
  L.push('   return(INIT_SUCCEEDED);');
  L.push('}');
  L.push('');
  L.push('void OnDeinit(const int reason)');
  L.push('{');
  for (const b of allInds) L.push(`   if (h_${b.id} != INVALID_HANDLE) IndicatorRelease(h_${b.id});`);
  for (const b of scans) for (const x of inds) L.push(`   for (int k = 0; k < ArraySize(g_scan_${b.id}_h_${x.id}); k++) if (g_scan_${b.id}_h_${x.id}[k] != INVALID_HANDLE) IndicatorRelease(g_scan_${b.id}_h_${x.id}[k]);`);
  if (tables.length) L.push('   Comment(""); // remove the value panel');
  L.push('}');
  L.push('');
  L.push('int OnCalculate(const int rates_total, const int prev_calculated,');
  L.push('                const datetime &time[], const double &open[], const double &high[],');
  L.push('                const double &low[], const double &close[], const long &tick_volume[],');
  L.push('                const long &volume[], const int &spread[])');
  L.push('{');
  L.push('   if (rates_total <= BSV_WARMUP) return(0);');
  L.push('   // Series indexing (0 = newest bar), the same as the MQL4 target.');
  L.push('   int limit = rates_total - prev_calculated;');
  L.push('   if (prev_calculated > 0) limit++;');
  L.push('   if (limit > rates_total - BSV_WARMUP) limit = rates_total - BSV_WARMUP;');
  if (divFull) L.push('   int need = rates_total; // divergence reads the oscillator at older pivots: copy the whole buffer');
  else L.push(maxRecent(recipe) ? `   int need = MathMin(rates_total, MathMax(limit + ${2 + maxRecent(recipe)}, ${3 + maxRecent(recipe)})); // + ${maxRecent(recipe)} bars for signal.recent` : '   int need = MathMin(rates_total, MathMax(limit + 2, 3));');
  for (const b of inds) L.push(`   if (CopyBuffer(h_${b.id}, 0, 0, need, A_${b.id}) < need) return(0); // data not ready yet`);
  for (const b of htfInds) L.push(`   if (BarsCalculated(h_${b.id}) <= 0) return(0); // higher-timeframe data not ready yet`);
  L.push('   for (int i = limit - 1; i >= 0; i--)');
  L.push('   {');
  for (const p of plots) L.push(`      Buf_${p.id}[i] = ${val(p.params?.source, 'i')};`);
  for (const z of zones) L.push(`      Buf_${z.id}_high[i] = V_${z.params.source}_high(i);`, `      Buf_${z.id}_low[i] = V_${z.params.source}_low(i);`);
  L.push('   }');
  for (const a of alerts) {
    L.push(`   // ${a.id}: alert once per closed bar.`);
    L.push(`   if (${bool(a.params?.when, '1')} && g_alert_${a.id} != iTime(${SC}, 1)) { g_alert_${a.id} = iTime(${SC}, 1); Alert(${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}); }`);
  }
  const ph = { symbol: '_Symbol', timeframe: 'StringSubstr(EnumToString(_Period), 7)', time: `TimeToString(iTime(${SC}, 1), TIME_DATE | TIME_MINUTES)`, open: `DoubleToString(iOpen(${SC}, 1), _Digits)`, high: `DoubleToString(iHigh(${SC}, 1), _Digits)`, low: `DoubleToString(iLow(${SC}, 1), _Digits)`, close: `DoubleToString(iClose(${SC}, 1), _Digits)` };
  for (const h of hooks) {
    const parts = []; let lit = '{';
    Object.entries(h.params.payload).forEach(([k, x], n) => {
      lit += `${n ? ',' : ''}"${k}":`;
      if (typeof x !== 'string') { lit += JSON.stringify(x); return; }
      lit += '"';
      String(x).split(/(\{\{[^}]*\}\})/).forEach(seg => { const mm = /^\{\{([^}]*)\}\}$/.exec(seg); if (mm) { parts.push(q(lit), ph[mm[1]]); lit = ''; } else lit += seg; });
      lit += '"';
    });
    parts.push(q(lit + '}'));
    L.push(`   // ${h.id}: webhook JSON for the bar that just closed, once per bar. MT5 indicators cannot call WebRequest (MQL5 docs: only Expert Advisors and scripts),`,
      '   // so this prints the JSON to the Experts journal; send it from your own EA with WebRequest (allowed URL list in Tools > Options). {{time}} = bar open time in broker server time.',
      `   if (${bool(h.params.when, '1')} && g_hook_${h.id} != iTime(${SC}, 1)) { g_hook_${h.id} = iTime(${SC}, 1); Print("BSV webhook " + ${parts.filter(x => x !== '""').join(' + ')}); }`);
  }
  if (tables.length) {
    const cell = (x) => { const [id, k] = x.id.split('.'); return x.bool ? `(S_${id}(1) ? "true" : "false")` : `BsvNum(V_${k ? `${id}_${k}` : id}(1))`; };
    L.push('   // Value panel (visual.table): Comment() writes it to the top-left corner of the chart. Shift 1 = the bar that just closed (the newest bar may still be forming).',
      `   Comment(${tables.map(t => [q(t.title + '\n'), ...t.fields.map((x, k) => `${q(x.id + ': ')} + ${cell(x)}${k < t.fields.length - 1 ? ' + "\\n"' : ''}`)].join(' + ')).join(' + "\\n\\n" + ')});`);
  }
  for (const b of scans) {
    const sig = scanSignal(recipe, b), cp = inds.map(x => ` || g_scan_${b.id}_h_${x.id}[k] == INVALID_HANDLE || CopyBuffer(g_scan_${b.id}_h_${x.id}[k], 0, 0, nb, A_${x.id}) < nb`).join('');
    L.push(`   // ${b.id}: once per closed chart bar, ${sig} on each scanned symbol at that symbol's bar that just closed (shift 1). The block functions read g_sym;`,
      '   // each symbol\'s indicator values are copied into the same arrays (the next call copies the chart values again), then the chart symbol is restored.',
      `   if (g_scan_${b.id}_t != iTime(${SC}, 1))`, '   {', `      g_scan_${b.id}_t = iTime(${SC}, 1);`, '      string hits = "";', '      int skipped = 0;',
      `      for (int k = 0; k < ArraySize(g_scan_${b.id}); k++)`, '      {', `         g_sym = g_scan_${b.id}[k];`, '         int nb = Bars(g_sym, _Period);',
      `         if (nb <= BSV_WARMUP${cp}) { skipped++; continue; } // no data yet`, `         if (${bool(sig, '1')}) hits = hits + " " + g_sym;`, '      }', '      g_sym = _Symbol;',
      `      if (skipped > 0) Print(${q(`BSV scan ${b.id}: `)}, skipped, " symbol(s) skipped, no data yet");`, `      if (hits != "") Alert(${q(`BSV scan ${b.id}:`)} + hits);`, '   }');
  }
  L.push('   return(rates_total);');
  L.push('}');
  L.push('');
  L.push('// Compile in MetaEditor, check every TODO, then test on history and a demo account before relying on it.');
  return L.join('\n') + '\n';
}

function renderCTrader(recipe) {
  const map = blockMap(recipe);
  const cls = className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const inds = recipe.blocks.filter(b => ['indicator.ema', 'indicator.sma', 'indicator.rsi', 'indicator.atr'].includes(b.type));
  const series = { open: 'Bars.OpenPrices', high: 'Bars.HighPrices', low: 'Bars.LowPrices', close: 'Bars.ClosePrices', hl2: 'Bars.MedianPrices', hlc3: 'Bars.TypicalPrices' };
  const scan = recipe.blocks.find(b => b.type === 'scanner.symbol_set' && scanOk(recipe, b)), ssyms = scan ? scanSymbols(scan) : [];
  const BB = scan ? '_b' : 'Bars';  // block functions read _b (the chart bars, or the bars of the symbol being scanned) when the recipe scans symbols
  const series0 = { ...series };
  if (scan) for (const k of Object.keys(series)) series[k] = series[k].replace(/^Bars\./, '_b.');
  const CX = (src, at) => `${BB}.${src === 'high' ? 'HighPrices' : src === 'low' ? 'LowPrices' : 'ClosePrices'}[${at}]`;
  const priceAt = (ref, at) => ref === 'ohlc4' ? `(${BB}.OpenPrices[${at}] + ${BB}.HighPrices[${at}] + ${BB}.LowPrices[${at}] + ${BB}.ClosePrices[${at}]) / 4.0` : `${series[ref]}[${at}]`;
  const val = (ref, at) => isPrice(ref) ? priceAt(ref, at) : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0 : 0.0)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0 && !double.IsNaN(${val(ref, at)}))`;
  const CT = htfCTraderTfs(), ctMin = n => Number(Object.keys(CT).find(k => CT[k] === n));
  const htfNames = [...new Set(recipe.blocks.map(b => htfTfOf(recipe, b)).filter(Boolean))];
  const htfOk = (list, at) => list.filter(r => htfTfOf(recipe, map.get(r))).map(r => `!double.IsNaN(${val(r, at)}) && `).join('');
  const L = [];
  L.push('// ORIGINAL BSV STARTER — cTrader Algo (C#) custom indicator. Build in cTrader before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push('using System;');
  L.push('using cAlgo.API;');
  L.push('using cAlgo.API.Indicators;');
  L.push('');
  L.push('namespace cAlgo');
  L.push('{');
  L.push(`    [Indicator(IsOverlay = ${recipe.overlay ? 'true' : 'false'}, TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]`);
  L.push(`    public class ${cls} : Indicator`);
  L.push('    {');
  L.push(`        private const int Warmup = ${warmup(recipe)};`);
  for (const b of inds) {
    const t = { 'indicator.ema': 'ExponentialMovingAverage', 'indicator.sma': 'SimpleMovingAverage', 'indicator.rsi': 'RelativeStrengthIndex', 'indicator.atr': 'AverageTrueRange' }[b.type];
    L.push(`        private ${t} _${b.id};`);
  }
  for (const n of htfNames) L.push(`        private Bars _htfBars_${n};`, `        private bool _htfOk_${n};`);
  for (const a of alerts) L.push(`        private int _alert_${a.id} = -1;`);
  if (scan) {
    const T = { 'indicator.ema': 'ExponentialMovingAverage', 'indicator.sma': 'SimpleMovingAverage', 'indicator.rsi': 'RelativeStrengthIndex', 'indicator.atr': 'AverageTrueRange' };
    L.push('        private Bars _b; // the bars the block functions read: the chart, or the symbol being scanned');
    for (const b of inds) L.push(`        private ${T[b.type]} _c_${b.id}; // ${b.id} of _b`, `        private ${T[b.type]}[] _scan_${b.id};`);
    L.push(`        private string[] _scanNames_${scan.id};`, `        private Bars[] _scanBars_${scan.id};`, `        private DateTime _scanT_${scan.id} = DateTime.MinValue;`,
      '', `        [Parameter(${q(`${scan.id}: symbols to scan (comma-separated)`)}, DefaultValue = ${q(ssyms.join(','))})]`, `        public string Scan_${scan.id} { get; set; }`);
  }
  for (const p of plots) {
    L.push('');
    L.push(`        [Output(${q(String(p.params?.title || p.id).replace(/"/g, ''))})]`);
    L.push(`        public IndicatorDataSeries Out_${p.id} { get; set; }`);
  }
  L.push('');
  L.push('        protected override void Initialize()');
  L.push('        {');
  for (const n of htfNames) {
    const lower = Object.keys(CT).map(Number).filter(m => m < ctMin(n)).map(m => 'TimeFrame.' + CT[m]);
    L.push(`            _htfBars_${n} = MarketData.GetBars(TimeFrame.${n});`);
    L.push(`            _htfOk_${n} = Array.IndexOf(new[] { ${lower.join(', ')} }, TimeFrame) >= 0; // chart timeframe must be a time frame lower than ${n}`);
    L.push(`            if (!_htfOk_${n}) Print(${q(`BSV: the higher timeframe ${n} must be higher than the chart timeframe (time-based charts only). Higher-timeframe values stay empty.`)});`);
  }
  for (const b of inds) {
    const p = b.params || {};
    const H = htfTfOf(recipe, b) ? `_htfBars_${htfTfOf(recipe, b)}` : 'Bars';
    const src = () => (series0[sourceName(p.source)] || 'Bars.ClosePrices').replace(/^Bars\./, H + '.');
    const note = () => sourceName(p.source) === 'ohlc4' ? ' // TODO ohlc4 has no built-in series; using close' : '';
    if (b.type === 'indicator.ema') L.push(`            _${b.id} = Indicators.ExponentialMovingAverage(${src()}, ${p.length});${note()}`);
    if (b.type === 'indicator.sma') L.push(`            _${b.id} = Indicators.SimpleMovingAverage(${src()}, ${p.length});${note()}`);
    if (b.type === 'indicator.rsi') L.push(`            _${b.id} = Indicators.RelativeStrengthIndex(${src()}, ${p.length});${note()}`);
    if (b.type === 'indicator.atr') L.push(H === 'Bars' ? `            _${b.id} = Indicators.AverageTrueRange(${p.length}, MovingAverageType.WilderSmoothing);` : `            _${b.id} = Indicators.AverageTrueRange(${H}, ${p.length}, MovingAverageType.WilderSmoothing);`);
  }
  if (scan) {
    const mk = (b, X) => { const p = b.params || {}, src = (series0[sourceName(p.source)] || 'Bars.ClosePrices').replace(/^Bars\./, X + '.');
      return b.type === 'indicator.ema' ? `Indicators.ExponentialMovingAverage(${src}, ${p.length})` : b.type === 'indicator.sma' ? `Indicators.SimpleMovingAverage(${src}, ${p.length})` : b.type === 'indicator.rsi' ? `Indicators.RelativeStrengthIndex(${src}, ${p.length})` : `Indicators.AverageTrueRange(${X}, ${p.length}, MovingAverageType.WilderSmoothing)`; };
    const T = { 'indicator.ema': 'ExponentialMovingAverage', 'indicator.sma': 'SimpleMovingAverage', 'indicator.rsi': 'RelativeStrengthIndex', 'indicator.atr': 'AverageTrueRange' };
    const id = scan.id;
    L.push('            _b = Bars;');
    for (const b of inds) L.push(`            _c_${b.id} = _${b.id};`);
    L.push(`            // ${id}: bars of each listed symbol in the chart time frame (MarketData.GetBars(TimeFrame, symbolName)); a name the broker does not know is skipped.`,
      '            // https://help.ctrader.com/ctrader-algo/references/MarketData/MarketData/ . Not run on cTrader by BSV (UNTESTED_RUNTIME).',
      `            _scanNames_${id} = (Scan_${id} ?? "").Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);`,
      `            _scanBars_${id} = new Bars[_scanNames_${id}.Length];`);
    for (const b of inds) L.push(`            _scan_${b.id} = new ${T[b.type]}[_scanNames_${id}.Length];`);
    L.push(`            for (int k = 0; k < _scanNames_${id}.Length; k++)`, '            {', `                _scanNames_${id}[k] = _scanNames_${id}[k].Trim();`, '                try', '                {',
      `                    _scanBars_${id}[k] = MarketData.GetBars(TimeFrame, _scanNames_${id}[k]);`);
    for (const b of inds) L.push(`                    _scan_${b.id}[k] = ${mk(b, `_scanBars_${id}[k]`)};`);
    L.push('                }', `                catch (Exception e) { _scanBars_${id}[k] = null; Print(${q(`BSV scan ${id}: cannot load `)} + _scanNames_${id}[k] + ": " + e.Message); }`, '            }');
  }
  L.push('        }');
  L.push('');
  L.push('        public override void Calculate(int index)');
  L.push('        {');
  L.push('            if (index < Warmup)');
  L.push('                return;');
  for (const p of plots) L.push(`            Out_${p.id}[index] = ${val(p.params?.source, 'index')};`);
  if (alerts.length) {
    L.push('            if (!IsLastBar)');
    L.push('                return;');
    L.push('            int i = index - 1; // last closed bar');
    for (const a of alerts) {
      L.push(`            if (${bool(a.params?.when, 'i')} && _alert_${a.id} != i)`);
      L.push('            {');
      L.push(`                _alert_${a.id} = i;`);
      L.push(`                Print(${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}); // swap for Notifications if you want sound/email; no auto-trading`);
      L.push('            }');
    }
  }
  if (scan) {
    const id = scan.id, sig = scanSignal(recipe, scan);
    L.push(`            // ${id}: once per new chart bar (live, last bar only), ${sig} on each listed symbol at that symbol's last bar that closed by this chart bar's open.`,
      `            if (IsLastBar && Bars.OpenTimes[index] != _scanT_${id})`, '            {', `                _scanT_${id} = Bars.OpenTimes[index];`, '                string hits = "";', '                int skipped = 0;',
      `                for (int k = 0; k < _scanNames_${id}.Length; k++)`, '                {',
      `                    int j = _scanBars_${id}[k] == null ? -1 : BsvScanClosed(_scanBars_${id}[k], Bars.OpenTimes[index]);`,
      '                    if (j < Warmup) { skipped++; continue; } // not loaded or not enough history yet',
      `                    _b = _scanBars_${id}[k];`);
    for (const b of inds) L.push(`                    _c_${b.id} = _scan_${b.id}[k];`);
    L.push(`                    if (${bool(sig, 'j')}) hits += " " + _scanNames_${id}[k];`, '                }', '                _b = Bars;');
    for (const b of inds) L.push(`                _c_${b.id} = _${b.id};`);
    L.push(`                if (skipped > 0) Print(${q(`BSV scan ${id}: `)} + skipped + " symbol(s) skipped, no data yet");`,
      `                if (hits != "") Print(${q(`BSV scan ${id}:`)} + hits); // swap for Notifications if you want sound/email; no auto-trading`, '            }');
  }
  L.push('        }');
  if (scan) L.push('', '        // Last bar of s that opened before t (bars that open at or after t are still forming or in the future). The reference does not say how',
    '        // TimeSeries.GetIndexByTime rounds, so the index is stepped back with the OpenTimes indexer. Same chart time frame, so that bar has closed.',
    '        private int BsvScanClosed(Bars s, DateTime t)', '        {', '            int k = s.OpenTimes.GetIndexByTime(t);', '            if (k < 0 || k > s.Count - 1) k = s.Count - 1;',
    '            while (k >= 0 && s.OpenTimes[k] >= t) k--;', '            return k;', '        }');
  if (htfNames.length) {
    L.push('', '        // Higher timeframe, last CLOSED bar only (UNTESTED_RUNTIME: not compiled on cTrader or run by BSV). The reference does not say how',
      '        // TimeSeries.GetIndexByTime rounds a time inside a bar (https://help.ctrader.com/ctrader-algo/references/Collections/DataSeries/TimeSeries/),',
      '        // so the index is stepped back with the OpenTimes indexer until that bar opened at or before this chart bar\'s open time;',
      '        // the bar before it has then closed. Worst case one extra higher-timeframe bar of lag, never a forming or future bar.',
      '        // Bars from MarketData.GetBars: https://help.ctrader.com/ctrader-algo/references/MarketData/MarketData/',
      '        private int BsvHtfClosed(Bars htf, int i)',
      '        {',
      '            if (htf.OpenTimes.Count == 0) return -1;',
      '            DateTime t = Bars.OpenTimes[i];',
      '            int k = htf.OpenTimes.GetIndexByTime(t);',
      '            if (k > htf.OpenTimes.Count - 1) k = htf.OpenTimes.Count - 1;',
      '            while (k >= 0 && htf.OpenTimes[k] > t) k--;',
      '            return k - 1;',
      '        }');
  }
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': case 'indicator.atr': {
        const n = htfTfOf(recipe, b);
        L.push('', n ? `        private double V_${b.id}(int i) { int j = BsvHtfClosed(_htfBars_${n}, i); return (!_htfOk_${n} || j < ${Math.max(2, (Number(p.length) || 1) * 3 + 2)}) ? double.NaN : _${b.id}.Result[j]; } // last closed ${n} bar only`
          : `        private double V_${b.id}(int i) { return _${scan ? 'c_' : ''}${b.id}.Result[i]; }`);
        break;
      }
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { L.push('', `        private double V_${b.id}(int i) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const hl = (p.source || 'close') === 'high_low', R = p.right, Lf = p.left, xh = at => CX(hl ? 'high' : 'close', at), xl = at => CX(hl ? 'low' : 'close', at);
        L.push('', `        // ${b.id}: bar i confirms a pivot at bar i - ${R}: above the ${Lf} bars before it and at least as high as the ${R} after it (a flat top counts once);`,
          `        // known only at bar i, so no lookahead. The last confirmed pivot is found by scanning back (NaN before the first). Same rule as the Pine / MQL5 targets.`,
          `        private bool S_${b.id}_ph(int i) { int c = i - ${R}; if (c - ${Lf} < 0 || i >= ${BB}.Count) return false; double v = ${xh('c')}; for (int k = 1; k <= ${Lf}; k++) if (${xh('c - k')} >= v) return false; for (int k = 1; k <= ${R}; k++) if (${xh('c + k')} > v) return false; return true; }`,
          `        private bool S_${b.id}_pl(int i) { int c = i - ${R}; if (c - ${Lf} < 0 || i >= ${BB}.Count) return false; double v = ${xl('c')}; for (int k = 1; k <= ${Lf}; k++) if (${xl('c - k')} <= v) return false; for (int k = 1; k <= ${R}; k++) if (${xl('c + k')} < v) return false; return true; }`,
          `        private double V_${b.id}_high(int i) { for (int k = i; k - ${R + Lf} >= 0; k--) if (S_${b.id}_ph(k)) return ${xh(`k - ${R}`)}; return double.NaN; }`,
          `        private double V_${b.id}_low(int i) { for (int k = i; k - ${R + Lf} >= 0; k--) if (S_${b.id}_pl(k)) return ${xl(`k - ${R}`)}; return double.NaN; }`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { L.push('', `        private bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const pb = map.get(p.pivot), pq = pb.params, R = pq.right, Lf = pq.left, hl = (pq.source || 'close') === 'high_low', o = p.oscillator, d = p.direction || 'both', v = pb.id;
        const xh = at => CX(hl ? 'high' : 'close', at), xl = at => CX(hl ? 'low' : 'close', at);
        L.push('', `        // ${b.id}: regular divergence, true on the bar that confirms the new pivot (bar i - ${R}), compared with the pivot before it (scanning back).`,
          `        private bool S_${b.id}_bear(int i) { if (!S_${v}_ph(i)) return false; for (int k = i - 1; k - ${R + Lf} >= 0; k--) if (S_${v}_ph(k)) { double o1 = ${val(o, `i - ${R}`)}; double o0 = ${val(o, `k - ${R}`)}; return !double.IsNaN(o1) && !double.IsNaN(o0) && ${xh(`i - ${R}`)} > ${xh(`k - ${R}`)} && o1 < o0; } return false; }`,
          `        private bool S_${b.id}_bull(int i) { if (!S_${v}_pl(i)) return false; for (int k = i - 1; k - ${R + Lf} >= 0; k--) if (S_${v}_pl(k)) { double o1 = ${val(o, `i - ${R}`)}; double o0 = ${val(o, `k - ${R}`)}; return !double.IsNaN(o1) && !double.IsNaN(o0) && ${xl(`i - ${R}`)} < ${xl(`k - ${R}`)} && o1 > o0; } return false; }`,
          `        private bool S_${b.id}(int i) { return ${d === 'both' ? `S_${b.id}_bear(i) || S_${b.id}_bull(i)` : d === 'bearish' ? `S_${b.id}_bear(i)` : `S_${b.id}_bull(i)`}; }`);
        break;
      }
      case 'scanner.symbol_set':
        if (scan !== b) L.push('', `        private double V_${b.id}(int i) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id} - ${scanWhyNot(recipe, b)}`);
        else L.push('', `        // ${b.id}: symbol scan of ${scanSignal(recipe, b)} (Initialize loads the bars of each listed symbol, Calculate scans once per new chart bar)`);
        break;
      case 'data.higher_timeframe':
        if (htfDataUsed(recipe, b)) { L.push('', `        // ${b.id}: higher timeframe ${b.params.timeframe} (read through BsvHtfClosed, closed bars only)`); break; }
        L.push('', `        private double V_${b.id}(int i) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push('', `        // TODO ${b.id}: bar times are UTC (see TimeZone attribute); convert session ${p.session || ''} from ${p.timezone || 'Etc/UTC'}.`,
          `        private bool S_${b.id}(int i) { var t = ${BB}.OpenTimes[i]; int m = t.Hour * 60 + t.Minute; return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push('', `        private bool S_${b.id}(int i) { return ${htfOk([p.left, p.right], 'i')}${htfOk([p.left, p.right], 'i - 1')}${val(p.left, 'i')} ${gt} ${val(p.right, 'i')} && ${val(p.left, 'i - 1')} ${le} ${val(p.right, 'i - 1')}; }`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push('', `        private bool S_${b.id}(int i) { return ${htfOk([p.left, p.right].filter(x => typeof x === 'string'), 'i')}${val(p.left, 'i')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'i') : Number(p.value)}; }`);
        break;
      case 'signal.recent':
        L.push('', `        private bool S_${b.id}(int i) { return ${orOf(p.bars, k => `(i >= ${k} && ${bool(p.signal, `i - ${k}`)})`, ' || ')}; } // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before i`);
        break;
      case 'signal.combine':
        L.push('', `        private bool S_${b.id}(int i) { return ${(p.signals || []).map(x => bool(x, 'i')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; }`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push('', `        private bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push('', `        private double V_${b.id}(int i) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('    }');
  L.push('}');
  return L.join('\n') + '\n';
}

// ---------------------------------------------------------------------------
// Shared helpers for the MQL4 / cTrader Python / Bookmap Python targets.
// Blocks of type signal.* / filter.* / alert.* are booleans; everything else is a value.
// ---------------------------------------------------------------------------
function isPrice(ref) {
  return ['open','high','low','close','hl2','hlc3','ohlc4'].includes(ref);
}

function isBoolType(type) {
  return /^(signal|filter|alert)\./.test(type || '');
}

function parseSession(p) {
  const m = /^(\d{2})(\d{2})-(\d{2})(\d{2})$/.exec(String(p.session || '0000-2359'));
  if (!m) throw new Error('session must look like HHMM-HHMM');
  return { start: (+m[1]) * 60 + (+m[2]), end: (+m[3]) * 60 + (+m[4]) };
}

function thresholdOp(p) {
  return ['>','>=','<','<=','==','!='].includes(p.op) ? p.op : '>=';
}

function warmup(recipe) {
  let n = 2;
  for (const b of recipe.blocks) if (Number.isInteger(b.params?.length)) n = Math.max(n, b.params.length * 3 + 2);
  return n + maxRecent(recipe);
}
// signal.recent lookback: the most bars any signal.recent block looks back (0 when the recipe has none, so other outputs are unchanged)
function maxRecent(recipe) { return Math.max(0, ...recipe.blocks.filter(b => b.type === 'signal.recent').map(b => b.params.bars)); }
function orOf(n, f, op) { return Array.from({ length: n }, (_, k) => f(k + 1)).join(op); }

function renderMql4(recipe) {
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const appliedPrice = { open: 'PRICE_OPEN', high: 'PRICE_HIGH', low: 'PRICE_LOW', close: 'PRICE_CLOSE', hl2: 'PRICE_MEDIAN', hlc3: 'PRICE_TYPICAL' };
  const priceExpr = { open: 'Open[i]', high: 'High[i]', low: 'Low[i]', close: 'Close[i]', hl2: '(High[i]+Low[i])/2.0', hlc3: '(High[i]+Low[i]+Close[i])/3.0', ohlc4: '(Open[i]+High[i]+Low[i]+Close[i])/4.0' };
  const val = (ref, at) => isPrice(ref) ? priceExpr[ref].replace(/\[i\]/g, `[${at}]`) : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0 : 0.0)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0 && ${val(ref, at)} != EMPTY_VALUE)`;
  const colors = ['clrDodgerBlue','clrOrange','clrLimeGreen','clrMagenta','clrGold','clrAqua'];
  const htfPeriods = [...new Set(recipe.blocks.map(b => htfTfOf(recipe, b)).filter(Boolean))];
  const htfOk = (list, at) => list.filter(r => htfTfOf(recipe, map.get(r))).map(r => `${val(r, at)} != EMPTY_VALUE && `).join('');
  const tfOf = b => htfTfOf(recipe, b) || '0';
  const fn = (b, call, note) => htfTfOf(recipe, b)
    ? `double V_${b.id}(int i) { int k = BsvHtfShift(${htfTfOf(recipe, b)}, i); return k < 1 ? (double)EMPTY_VALUE : ${call.replace(/, i\)$/, ', k)')}; } // last closed ${htfTfOf(recipe, b)} bar only${note}`
    : `double V_${b.id}(int i) { return ${call}; }${note}`;
  const L = [];
  L.push('// ORIGINAL BSV STARTER — MT4 / MQL4 custom indicator. Compile in MetaEditor (MT4) before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push('#property strict');
  L.push(recipe.overlay ? '#property indicator_chart_window' : '#property indicator_separate_window');
  L.push(`#property indicator_buffers ${plots.length}`);
  L.push('');
  for (const p of plots) L.push(`double Buf_${p.id}[];`);
  for (const a of alerts) L.push(`datetime g_alert_${a.id} = 0;`);
  L.push(`#define BSV_WARMUP ${warmup(recipe)}`);
  L.push('');
  if (htfPeriods.length) {
    L.push('// Higher timeframe: shift of the last CLOSED higher-timeframe bar for chart bar i. iBarShift (exact=false) finds the');
    L.push('// higher-timeframe bar covering the chart bar\'s open time; +1 is the bar before it, which has closed, so the forming bar');
    L.push('// is never read (no repaint, no lookahead). Docs: https://docs.mql4.com/series/ibarshift and https://docs.mql4.com/indicators/ima');
    L.push('// (timeframe + shift arguments). Not run by BSV (UNTESTED_RUNTIME). Higher-timeframe bars follow the broker server time in MT4,');
    L.push('// and that timeframe\'s history must be loaded in the terminal (open that chart once).');
    L.push('int BsvHtfShift(int tf, int i) { int s = iBarShift(NULL, tf, iTime(NULL, 0, i), false); return s < 0 ? -1 : s + 1; }');
    L.push('');
  }
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema':
      case 'indicator.sma': {
        const mode = b.type === 'indicator.ema' ? 'MODE_EMA' : 'MODE_SMA';
        const src = sourceName(p.source);
        if (appliedPrice[src]) L.push(fn(b, `iMA(NULL, ${tfOf(b)}, ${p.length}, 0, ${mode}, ${appliedPrice[src]}, i)`, ''));
        else L.push(fn(b, `iMA(NULL, ${tfOf(b)}, ${p.length}, 0, ${mode}, PRICE_CLOSE, i)`, ' // TODO ohlc4 has no MQL4 applied price; using close'));
        break;
      }
      case 'indicator.rsi': {
        const src = sourceName(p.source);
        if (appliedPrice[src]) L.push(fn(b, `iRSI(NULL, ${tfOf(b)}, ${p.length}, ${appliedPrice[src]}, i)`, ''));
        else L.push(fn(b, `iRSI(NULL, ${tfOf(b)}, ${p.length}, PRICE_CLOSE, i)`, ' // TODO ohlc4 has no MQL4 applied price; using close'));
        break;
      }
      case 'indicator.atr':
        L.push(fn(b, `iATR(NULL, ${tfOf(b)}, ${p.length}, i)`, ''));
        break;
      case 'data.higher_timeframe':
        if (htfDataUsed(recipe, b)) { L.push(`// ${b.id}: higher timeframe ${b.params.timeframe} (read through BsvHtfShift, closed bars only)`); break; }
        L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id}`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push(`// TODO ${b.id}: session ${p.session || ''} is evaluated in broker server time; convert from ${p.timezone || 'Etc/UTC'} for your broker.`);
        L.push(`bool S_${b.id}(int i) { int m = TimeHour(Time[i]) * 60 + TimeMinute(Time[i]); return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`bool S_${b.id}(int i) { return ${htfOk([p.left, p.right], 'i')}${htfOk([p.left, p.right], 'i+1')}${val(p.left, 'i')} ${gt} ${val(p.right, 'i')} && ${val(p.left, 'i+1')} ${le} ${val(p.right, 'i+1')}; }`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`bool S_${b.id}(int i) { return ${htfOk([p.left, p.right].filter(x => typeof x === 'string'), 'i')}${val(p.left, 'i')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'i') : Number(p.value)}; }`);
        break;
      case 'signal.recent':
        L.push(`bool S_${b.id}(int i) { return ${orOf(p.bars, k => bool(p.signal, `i+${k}`), ' || ')}; } // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before i`);
        break;
      case 'signal.combine':
        L.push(`bool S_${b.id}(int i) { return ${(p.signals || []).map(x => bool(x, 'i')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; }`);
        break;
      case 'visual.plot':
      case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push(`bool S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push(`double V_${b.id}(int i) { return EMPTY_VALUE; } // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('');
  L.push('int OnInit()');
  L.push('{');
  for (const tf of htfPeriods) L.push(`   if (PeriodSeconds(${tf}) <= PeriodSeconds()) { Alert(${q(`BSV: the higher timeframe ${tf} must be higher than the chart timeframe. Use a lower chart timeframe.`)}); return(INIT_FAILED); }`);
  L.push(`   IndicatorShortName(${q('BSV — ' + safeTitle(recipe))});`);
  plots.forEach((p, k) => {
    L.push(`   SetIndexBuffer(${k}, Buf_${p.id});`);
    L.push(`   SetIndexStyle(${k}, DRAW_LINE, STYLE_SOLID, 1, ${colors[k % colors.length]});`);
    L.push(`   SetIndexLabel(${k}, ${q(p.params?.title || p.params?.source || p.id)});`);
  });
  L.push('   return(INIT_SUCCEEDED);');
  L.push('}');
  L.push('');
  L.push('int OnCalculate(const int rates_total, const int prev_calculated,');
  L.push('                const datetime &time[], const double &open[], const double &high[],');
  L.push('                const double &low[], const double &close[], const long &tick_volume[],');
  L.push('                const long &volume[], const int &spread[])');
  L.push('{');
  L.push('   if (rates_total <= BSV_WARMUP) return(0);');
  L.push('   int limit = rates_total - prev_calculated;');
  L.push('   if (prev_calculated > 0) limit++;');
  L.push('   if (limit > rates_total - BSV_WARMUP) limit = rates_total - BSV_WARMUP;');
  L.push('   for (int i = limit - 1; i >= 0; i--)');
  L.push('   {');
  for (const p of plots) L.push(`      Buf_${p.id}[i] = ${val(p.params?.source, 'i')};`);
  L.push('   }');
  for (const a of alerts) {
    L.push(`   // ${a.id}: alert once per closed bar.`);
    L.push(`   if (${bool(a.params?.when, '1')} && g_alert_${a.id} != Time[1]) { g_alert_${a.id} = Time[1]; Alert(${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}); }`);
  }
  L.push('   return(rates_total);');
  L.push('}');
  L.push('');
  L.push('// Compile in MetaEditor, check every TODO, then test on history and a demo account before relying on it.');
  return L.join('\n') + '\n';
}

function renderCTraderPython(recipe) {
  const map = blockMap(recipe);
  const cls = className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const series = { open: 'api.Bars.OpenPrices', high: 'api.Bars.HighPrices', low: 'api.Bars.LowPrices', close: 'api.Bars.ClosePrices', hl2: 'api.Bars.MedianPrices', hlc3: 'api.Bars.TypicalPrices' };
  const priceAt = (ref, at) => ref === 'ohlc4' ? `(api.Bars.OpenPrices[${at}] + api.Bars.HighPrices[${at}] + api.Bars.LowPrices[${at}] + api.Bars.ClosePrices[${at}]) / 4.0` : `${series[ref]}[${at}]`;
  const val = (ref, at) => isPrice(ref) ? priceAt(ref, at) : (isBoolType(map.get(ref)?.type) ? `(1.0 if self.s_${ref}(${at}) else 0.0)` : `self.v_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `self.s_${ref}(${at})` : `bool(${val(ref, at)})`;
  const L = [];
  L.push('# ORIGINAL BSV STARTER — cTrader Algo Python custom indicator. Build in cTrader before use.');
  L.push('# Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push('#');
  L.push(`# 1) In cTrader Algo create a new Python indicator named ${cls}.`);
  L.push(`# 2) Replace the attribute file ${cls}.cs with:`);
  L.push('#');
  L.push('#    using System;');
  L.push('#    using cAlgo.API;');
  L.push('#    namespace cAlgo.Indicators;');
  L.push(`#    [Indicator(IsOverlay = ${recipe.overlay ? 'true' : 'false'}, TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]`);
  L.push(`#    public partial class ${cls} : Indicator`);
  L.push('#    {');
  for (const p of plots) {
    L.push(`#        [Output(${q(String(p.params?.title || p.id).replace(/"/g, ''))})]`);
    L.push(`#        public IndicatorDataSeries Out_${p.id} { get; set; }`);
  }
  L.push('#    }');
  L.push('#');
  L.push(`# 3) Replace ${cls}_main.py with this file and build.`);
  L.push('');
  L.push('import clr');
  L.push('clr.AddReference("cAlgo.API")');
  L.push('from cAlgo.API import *');
  L.push('');
  L.push(`WARMUP = ${warmup(recipe)}`);
  L.push('');
  L.push(`class ${cls}():`);
  L.push('    def initialize(self):');
  L.push('        self.last_alert = {}');
  for (const b of recipe.blocks) {
    const p = b.params || {};
    const src = () => series[sourceName(p.source)] || 'api.Bars.ClosePrices';
    const note = () => sourceName(p.source) === 'ohlc4' ? '  # TODO ohlc4 has no built-in series; using close' : '';
    if (b.type === 'indicator.ema') L.push(`        self.${b.id} = api.Indicators.ExponentialMovingAverage(${src()}, ${p.length})${note()}`);
    if (b.type === 'indicator.sma') L.push(`        self.${b.id} = api.Indicators.SimpleMovingAverage(${src()}, ${p.length})${note()}`);
    if (b.type === 'indicator.rsi') L.push(`        self.${b.id} = api.Indicators.RelativeStrengthIndex(${src()}, ${p.length})${note()}`);
    if (b.type === 'indicator.atr') L.push(`        self.${b.id} = api.Indicators.AverageTrueRange(${p.length}, MovingAverageType.WilderSmoothing)`);
  }
  L.push('');
  L.push('    def calculate(self, index):');
  L.push('        if index < WARMUP:');
  L.push('            return');
  for (const p of plots) L.push(`        api.Out_${p.id}[index] = ${val(p.params?.source, 'index')}`);
  if (alerts.length) {
    L.push('        if api.IsLastBar:');
    L.push('            i = index - 1  # last closed bar');
    for (const a of alerts) {
      L.push(`            if ${bool(a.params?.when, 'i')} and self.last_alert.get(${q(a.id)}) != i:`);
      L.push(`                self.last_alert[${q(a.id)}] = i`);
      L.push(`                api.Print(${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))})  # swap for api.Notifications if you want sound/email`);
    }
  }
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': case 'indicator.atr':
        L.push('', `    def v_${b.id}(self, i):`, `        return self.${b.id}.Result[i]`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push('', `    def s_${b.id}(self, i):`, `        # TODO ${b.id}: bar times are UTC (see TimeZone attribute); convert session ${p.session || ''} from ${p.timezone || 'Etc/UTC'}.`,
          '        t = api.Bars.OpenTimes[i]', '        m = t.Hour * 60 + t.Minute', `        return ${ss.start <= ss.end ? `${ss.start} <= m < ${ss.end}` : `m >= ${ss.start} or m < ${ss.end}`}`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push('', `    def s_${b.id}(self, i):`, `        return ${val(p.left, 'i')} ${gt} ${val(p.right, 'i')} and ${val(p.left, 'i - 1')} ${le} ${val(p.right, 'i - 1')}`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push('', `    def s_${b.id}(self, i):`, `        return ${val(p.left, 'i')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'i') : Number(p.value)}`);
        break;
      case 'signal.recent':
        L.push('', `    def s_${b.id}(self, i):  # ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before i`, `        return ${orOf(p.bars, k => `(i >= ${k} and ${bool(p.signal, `i - ${k}`)})`, ' or ')}`);
        break;
      case 'signal.combine':
        L.push('', `    def s_${b.id}(self, i):`, `        return ${(p.signals || []).map(x => bool(x, 'i')).join(p.mode === 'any' ? ' or ' : ' and ') || 'False'}`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push('', `    def s_${b.id}(self, i):`, `        return False  # TODO unsupported block ${b.type}: ${b.id}`);
        else L.push('', `    def v_${b.id}(self, i):`, `        return float('nan')  # TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  return L.join('\n') + '\n';
}

function renderBookmapPython(recipe) {
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const graph = recipe.overlay ? 'PRIMARY' : 'BOTTOM';
  const R = ref => `vals.get(${q(ref)})`;
  const L = [];
  L.push("# ORIGINAL BSV STARTER — Bookmap Python API add-on (Bookmap's Python API is in open beta).");
  L.push('# Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push('# Bookmap is order-flow based: this starter builds time bars from trades (BAR_SECONDS)');
  L.push('# and evaluates the recipe on each closed bar. Load it via the Bookmap Python API add-on.');
  L.push('# API reference: https://github.com/BookmapAPI/python-api');
  L.push('import time');
  L.push('from collections import deque');
  L.push('import bookmap as bm');
  L.push('');
  L.push('BAR_SECONDS = 60');
  L.push('INTERVALS_PER_BAR = BAR_SECONDS * 10  # on_interval fires every 0.1 s');
  L.push(`PLOTS = ${JSON.stringify(plots.map(p => [p.id, String(p.params?.title || p.id)]))}`);
  L.push(`GRAPH = ${q(graph)}  # PRIMARY = price heatmap, BOTTOM = sub-chart`);
  L.push('');
  L.push('class Ema:');
  L.push('    def __init__(self, n): self.n, self.a, self.v, self.k, self.s = n, 2.0 / (n + 1), None, 0, 0.0');
  L.push('    def update(self, x):');
  L.push('        if self.v is None:');
  L.push('            self.k += 1; self.s += x');
  L.push('            if self.k >= self.n: self.v = self.s / self.n');
  L.push('        else:');
  L.push('            self.v = x * self.a + self.v * (1 - self.a)');
  L.push('        return self.v');
  L.push('');
  L.push('class Sma:');
  L.push('    def __init__(self, n): self.n, self.q = n, deque(maxlen=n)');
  L.push('    def update(self, x):');
  L.push('        self.q.append(x)');
  L.push('        return sum(self.q) / self.n if len(self.q) == self.n else None');
  L.push('');
  L.push('class Rsi:  # Wilder smoothing');
  L.push('    def __init__(self, n): self.n, self.prev, self.g, self.l, self.k = n, None, 0.0, 0.0, 0');
  L.push('    def update(self, x):');
  L.push('        if self.prev is None:');
  L.push('            self.prev = x');
  L.push('            return None');
  L.push('        ch, self.prev = x - self.prev, x');
  L.push('        up, dn = max(ch, 0.0), max(-ch, 0.0)');
  L.push('        self.k += 1');
  L.push('        if self.k <= self.n:');
  L.push('            self.g += up / self.n; self.l += dn / self.n');
  L.push('            if self.k < self.n: return None');
  L.push('        else:');
  L.push('            self.g = (self.g * (self.n - 1) + up) / self.n; self.l = (self.l * (self.n - 1) + dn) / self.n');
  L.push('        return 100.0 if self.l == 0 else 100.0 - 100.0 / (1 + self.g / self.l)');
  L.push('');
  L.push('class Atr:  # Wilder smoothing of true range');
  L.push('    def __init__(self, n): self.n, self.pc, self.v, self.k, self.s = n, None, None, 0, 0.0');
  L.push('    def update(self, b):');
  L.push('        tr = b["h"] - b["l"] if self.pc is None else max(b["h"] - b["l"], abs(b["h"] - self.pc), abs(b["l"] - self.pc))');
  L.push('        self.pc = b["c"]');
  L.push('        if self.v is None:');
  L.push('            self.k += 1; self.s += tr');
  L.push('            if self.k >= self.n: self.v = self.s / self.n');
  L.push('        else:');
  L.push('            self.v = (self.v * (self.n - 1) + tr) / self.n');
  L.push('        return self.v');
  L.push('');
  L.push('def make_calc():');
  L.push('    return {');
  for (const b of recipe.blocks) {
    const p = b.params || {};
    const cls = { 'indicator.ema': 'Ema', 'indicator.sma': 'Sma', 'indicator.rsi': 'Rsi', 'indicator.atr': 'Atr' }[b.type];
    if (cls) L.push(`        ${q(b.id)}: ${cls}(${p.length}),`);
  }
  L.push('    }');
  L.push('');
  L.push('def evaluate(s, b):');
  L.push('    # Runs the recipe on one closed bar b = {o, h, l, c, t}; returns the values by block id.');
  L.push('    calc, prev = s["calc"], s["prev"]');
  L.push('    vals = {"open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"], "hl2": (b["h"] + b["l"]) / 2.0,');
  L.push('            "hlc3": (b["h"] + b["l"] + b["c"]) / 3.0, "ohlc4": (b["o"] + b["h"] + b["l"] + b["c"]) / 4.0}');
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi':
        L.push(`    vals[${q(b.id)}] = calc[${q(b.id)}].update(vals[${q(sourceName(p.source))}])`);
        break;
      case 'indicator.atr':
        L.push(`    vals[${q(b.id)}] = calc[${q(b.id)}].update(b)`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push(`    # TODO ${b.id}: bar time is UTC here; convert session ${p.session || ''} from ${p.timezone || 'Etc/UTC'}.`);
        L.push('    g = time.gmtime(b["t"])');
        L.push('    m = g.tm_hour * 60 + g.tm_min');
        L.push(`    vals[${q(b.id)}] = ${ss.start <= ss.end ? `${ss.start} <= m < ${ss.end}` : `m >= ${ss.start} or m < ${ss.end}`}`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`    l, r, pl, pr = ${R(p.left)}, ${R(p.right)}, prev.get(${q(p.left)}), prev.get(${q(p.right)})`);
        L.push(`    vals[${q(b.id)}] = None not in (l, r, pl, pr) and l ${gt} r and pl ${le} pr`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(p.right !== undefined ? `    v, r = ${R(p.left)}, ${R(p.right)}` : `    v = ${R(p.left)}`);
        L.push(`    vals[${q(b.id)}] = v is not None and ${p.right !== undefined ? 'r is not None and ' : ''}v ${thresholdOp(p)} ${p.right !== undefined ? 'r' : Number(p.value)}`);
        break;
      case 'signal.recent':
        L.push(`    ps = prev.get(${q('~since:' + b.id)})  # bars since ${p.signal} was last true, as of the bar before`, `    vals[${q(b.id)}] = ps is not None and ps < ${p.bars}`, `    vals[${q('~since:' + b.id)}] = 0 if bool(${R(p.signal)}) else (None if ps is None else ps + 1)`);
        break;
      case 'signal.combine':
        L.push(`    vals[${q(b.id)}] = ${(p.signals || []).map(x => `bool(${R(x)})`).join(p.mode === 'any' ? ' or ' : ' and ') || 'False'}`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        L.push(`    vals[${q(b.id)}] = None  # TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('    return vals');
  L.push('');
  L.push('def on_bar_closed(addon, alias, s, b):');
  L.push('    vals = evaluate(s, b)');
  for (const p of plots) {
    L.push(`    v = vals.get(${q(p.params?.source)})`);
    L.push(`    if v is not None and ${q(p.id)} in s["ind"]:`);
    L.push(`        bm.add_point(addon, alias, s["ind"][${q(p.id)}], ${graph === 'PRIMARY' ? 'v / s["pips"])  # PRIMARY points are price levels' : 'float(v))  # check BOTTOM scaling in your Bookmap version'}`);
  }
  for (const a of recipe.blocks.filter(b => b.type === 'alert.condition')) {
    L.push(`    if vals.get(${q(a.params?.when)}):`);
    L.push(`        print(alias, ${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}, flush=True)  # one line per closed bar`);
  }
  L.push('    s["prev"] = vals');
  L.push('');
  L.push('state = {}');
  L.push('requests = {}');
  L.push('next_req = [1]');
  L.push('');
  L.push('def handle_subscribe_instrument(addon, alias, full_name, is_crypto, pips, size_multiplier, instrument_multiplier, supported_features):');
  L.push('    state[alias] = {"pips": pips, "bar": None, "ticks": 0, "calc": make_calc(), "prev": {}, "ind": {}}');
  L.push('    for pid, title in PLOTS:');
  L.push('        req = next_req[0]');
  L.push('        next_req[0] += 1');
  L.push('        requests[req] = (alias, pid)');
  L.push('        bm.register_indicator(addon, alias, req, "BSV " + title, GRAPH)');
  L.push('    req = next_req[0]');
  L.push('    next_req[0] += 1');
  L.push('    bm.subscribe_to_trades(addon, alias, req)');
  L.push('');
  L.push('def handle_unsubscribe_instrument(addon, alias):');
  L.push('    state.pop(alias, None)');
  L.push('');
  L.push('def handle_indicator_response(addon, request_id, indicator_id):');
  L.push('    if request_id in requests:');
  L.push('        alias, pid = requests[request_id]');
  L.push('        if alias in state:');
  L.push('            state[alias]["ind"][pid] = indicator_id');
  L.push('');
  L.push('def handle_trades(addon, alias, price_level, size_level, is_otc, is_bid, is_execution_start, is_execution_end, aggressor_order_id, passive_order_id):');
  L.push('    s = state.get(alias)');
  L.push('    if s is None:');
  L.push('        return');
  L.push('    px = price_level * s["pips"]');
  L.push('    b = s["bar"]');
  L.push('    if b is None:');
  L.push('        s["bar"] = {"o": px, "h": px, "l": px, "c": px, "t": time.time()}');
  L.push('    else:');
  L.push('        b["h"] = max(b["h"], px)');
  L.push('        b["l"] = min(b["l"], px)');
  L.push('        b["c"] = px');
  L.push('');
  L.push('def on_interval(addon, alias):');
  L.push('    s = state.get(alias)');
  L.push('    if s is None:');
  L.push('        return');
  L.push('    s["ticks"] += 1');
  L.push('    if s["ticks"] >= INTERVALS_PER_BAR:');
  L.push('        s["ticks"] = 0');
  L.push('        b, s["bar"] = s["bar"], None');
  L.push('        if b is not None:  # bars without trades are skipped');
  L.push('            on_bar_closed(addon, alias, s, b)');
  L.push('');
  L.push('if __name__ == "__main__":');
  L.push('    addon = bm.create_addon()');
  L.push('    bm.add_trades_handler(addon, handle_trades)');
  L.push('    bm.add_on_interval_handler(addon, on_interval)');
  L.push('    bm.add_indicator_response_handler(addon, handle_indicator_response)');
  L.push('    bm.start_addon(addon, handle_subscribe_instrument, handle_unsubscribe_instrument)');
  L.push('    bm.wait_until_addon_is_turned_off(addon)');
  return L.join('\n') + '\n';
}

function plotName(p) {
  return String(p.params?.title || p.id).replace(/[^A-Za-z0-9]+/g, '') || p.id;
}

function renderNinja(recipe) {
  const map = blockMap(recipe);
  const cls = 'Bsv' + className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const inds = recipe.blocks.filter(b => ['indicator.ema', 'indicator.sma', 'indicator.rsi', 'indicator.atr'].includes(b.type));
  const series = { open: 'Open', high: 'High', low: 'Low', close: 'Close', hl2: 'Median', hlc3: 'Typical' };
  const priceAt = (ref, at) => ref === 'ohlc4' ? (series.open === 'Open' ? `(Open[${at}] + High[${at}] + Low[${at}] + Close[${at}]) / 4.0` : `(Opens[_s][${at}] + Highs[_s][${at}] + Lows[_s][${at}] + Closes[_s][${at}]) / 4.0`) : `${series[ref]}[${at}]`;
  const val = (ref, at) => isPrice(ref) ? priceAt(ref, at) : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0 : 0.0)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0 && !double.IsNaN(${val(ref, at)}))`;
  const brushes = ['DodgerBlue', 'Orange', 'LimeGreen', 'Magenta', 'Gold', 'Aqua'];
  const htfPeriods = [...new Set(inds.map(b => htfTfOf(recipe, b)).filter(Boolean))];
  const bip = b => htfPeriods.indexOf(htfTfOf(recipe, b)) + 1;  // BarsInProgress index of the added higher-timeframe series (0 = chart)
  const scan = recipe.blocks.find(b => b.type === 'scanner.symbol_set' && scanOk(recipe, b)), ssyms = scan ? scanSymbols(scan) : [];
  const series0 = { ...series };  // chart series names for the indicator inputs
  if (scan) {  // block functions read series _s (0 = chart, k = scanned symbol k) instead of the chart-only Close / High / Low / Open
    const ms = { open: 'Opens', high: 'Highs', low: 'Lows', close: 'Closes', hl2: 'Medians', hlc3: 'Typicals' };
    for (const k of Object.keys(series)) series[k] = `${ms[k]}[_s]`;
  }
  const NX = (src, at) => `${src === 'high' ? 'Highs' : src === 'low' ? 'Lows' : 'Closes'}[_s][${at}]`;
  const L = [];
  L.push('// ORIGINAL BSV STARTER — NinjaTrader 8 NinjaScript indicator. Compile in the NinjaScript Editor before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// Save as Documents\\NinjaTrader 8\\bin\\Custom\\Indicators\\${cls}.cs (or create a new indicator named ${cls} and paste).`);
  L.push('#region Using declarations');
  L.push('using System;');
  L.push('using System.Windows.Media;');
  L.push('using NinjaTrader.Gui;');
  L.push('using NinjaTrader.Data;');
  L.push('using NinjaTrader.NinjaScript;');
  L.push('#endregion');
  L.push('');
  L.push('namespace NinjaTrader.NinjaScript.Indicators');
  L.push('{');
  L.push(`    public class ${cls} : Indicator`);
  L.push('    {');
  L.push(`        private const int Warmup = ${warmup(recipe)};`);
  for (const b of inds) L.push(`        private ${{ 'indicator.ema': 'EMA', 'indicator.sma': 'SMA', 'indicator.rsi': 'RSI', 'indicator.atr': 'ATR' }[b.type]} _${b.id};`);
  for (const b of inds.filter(x => htfTfOf(recipe, x))) L.push(`        private Series<double> _htf_${b.id}; // ${b.id} on ${htfTfOf(recipe, b).replace('BarsPeriodType.', '').replace(', ', ' ')} bars, stored per chart bar`);
  if (scan) {
    L.push(`        private static readonly string[] Scan_${scan.id} = { ${ssyms.map(q).join(', ')} }; // ${scan.id}: BarsInProgress k = Scan_${scan.id}[k - 1]`);
    for (const b of inds) L.push(`        private ${{ 'indicator.ema': 'EMA', 'indicator.sma': 'SMA', 'indicator.rsi': 'RSI', 'indicator.atr': 'ATR' }[b.type]}[] _scan_${b.id}; // ${b.id} on each scanned symbol`);
    L.push('        private int _s; // the series the block functions read: 0 = chart, k = scanned symbol k (BarsInProgress)');
  }
  L.push('');
  L.push('        protected override void OnStateChange()');
  L.push('        {');
  L.push('            if (State == State.SetDefaults)');
  L.push('            {');
  L.push(`                Name = ${q(cls)};`);
  L.push(`                Description = ${q('BSV — ' + safeTitle(recipe))};`);
  L.push('                Calculate = Calculate.OnBarClose;');
  L.push(`                IsOverlay = ${recipe.overlay ? 'true' : 'false'};`);
  L.push('                IsSuspendedWhileInactive = true;');
  plots.forEach((p, k) => L.push(`                AddPlot(Brushes.${brushes[k % brushes.length]}, ${q(plotName(p))});`));
  if (scan) L.push('                MaximumBarsLookBack = MaximumBarsLookBack.Infinite; // pivots / divergence look further back than the default 256 bars');
  L.push('            }');
  if (scan) {
    L.push('            else if (State == State.Configure)', '            {',
      `                // ${scan.id}: one added series per listed symbol, chart bar type and period. NinjaTrader 8 manual (AddDataSeries): the arguments must be`,
      '                // hard-coded (not inputs), so edit this list here or in the BSV Builder; every name must be an instrument NinjaTrader knows (e.g. "ES 12-26").',
      '                // https://ninjatrader.com/support/helpGuides/nt8/adddataseries.htm . Not run by BSV (UNTESTED_RUNTIME).',
      '                Calculate = Calculate.OnBarClose; // each symbol is evaluated on the bar that just closed');
    ssyms.forEach((x, k) => L.push(`                AddDataSeries(${q(x)}); // BarsInProgress ${k + 1}`));
    L.push('            }');
  }
  if (htfPeriods.length) {
    L.push('            else if (State == State.Configure)');
    L.push('            {');
    L.push('                // Higher timeframe, closed bars only. NinjaTrader 8 manual (Multi-Time Frame & Instruments, "How Bars Data is Referenced"):');
    L.push('                // with Calculate.OnBarClose the chart bars only know the last CLOSED bar of an added series; bars sharing a timestamp');
    L.push('                // run the chart series first. https://ninjatrader.com/support/helpGuides/nt8/multi-time_frame__instruments.htm');
    L.push('                // https://ninjatrader.com/support/helpGuides/nt8/adddataseries.htm . Not run by BSV (UNTESTED_RUNTIME).');
    L.push('                Calculate = Calculate.OnBarClose; // forced: OnEachTick / OnPriceChange would read the forming higher-timeframe bar');
    htfPeriods.forEach((tf, k) => L.push(`                AddDataSeries(${tf}); // BarsInProgress ${k + 1}`));
    L.push('            }');
  }
  L.push('            else if (State == State.DataLoaded)');
  L.push('            {');
  if (htfPeriods.length) {
    L.push('                int bsvChartMinutes = BarsPeriod.BarsPeriodType == BarsPeriodType.Minute ? BarsPeriod.Value : BarsPeriod.BarsPeriodType == BarsPeriodType.Day ? BarsPeriod.Value * 1440');
    L.push('                    : (BarsPeriod.BarsPeriodType == BarsPeriodType.Week || BarsPeriod.BarsPeriodType == BarsPeriodType.Month || BarsPeriod.BarsPeriodType == BarsPeriodType.Year) ? int.MaxValue : 0;');
    for (const tf of htfPeriods) {
      const [kind, n] = tf.replace('BarsPeriodType.', '').split(', ');
      const mins = kind === 'Week' ? 10080 : kind === 'Day' ? Number(n) * 1440 : Number(n);
      L.push(`                if (bsvChartMinutes >= ${mins}) throw new ArgumentException(${q(`BSV: the higher timeframe ${kind} ${n} must be higher than the chart timeframe. Use a lower chart timeframe.`)});`);
    }
  }
  const htfSeries = { open: 'Opens', high: 'Highs', low: 'Lows', close: 'Closes', hl2: 'Medians', hlc3: 'Typicals' };
  for (const b of inds) {
    const p = b.params || {};
    const k = htfTfOf(recipe, b) ? bip(b) : 0;
    const src = () => k ? `${htfSeries[sourceName(p.source)] || 'Closes'}[${k}]` : (series0[sourceName(p.source)] || 'Close');
    const note = () => sourceName(p.source) === 'ohlc4' ? ' // TODO ohlc4 has no built-in series; using Close' : '';
    if (b.type === 'indicator.ema') L.push(`                _${b.id} = EMA(${src()}, ${p.length});${note()}`);
    if (b.type === 'indicator.sma') L.push(`                _${b.id} = SMA(${src()}, ${p.length});${note()}`);
    if (b.type === 'indicator.rsi') L.push(`                _${b.id} = RSI(${src()}, ${p.length}, 1);${note()}`);
    if (b.type === 'indicator.atr') L.push(k ? `                _${b.id} = ATR(BarsArray[${k}], ${p.length});` : `                _${b.id} = ATR(${p.length});`);
    if (k) L.push(`                _htf_${b.id} = new Series<double>(this);`);
  }
  if (scan) for (const b of inds) {
    const p = b.params || {}, T = { 'indicator.ema': 'EMA', 'indicator.sma': 'SMA', 'indicator.rsi': 'RSI', 'indicator.atr': 'ATR' }[b.type], ms = { open: 'Opens', high: 'Highs', low: 'Lows', close: 'Closes', hl2: 'Medians', hlc3: 'Typicals' }[sourceName(p.source)] || 'Closes';
    const mk = b.type === 'indicator.ema' ? `EMA(${ms}[k + 1], ${p.length})` : b.type === 'indicator.sma' ? `SMA(${ms}[k + 1], ${p.length})` : b.type === 'indicator.rsi' ? `RSI(${ms}[k + 1], ${p.length}, 1)` : `ATR(BarsArray[k + 1], ${p.length})`;
    L.push(`                _scan_${b.id} = new ${T}[Scan_${scan.id}.Length];`, `                for (int k = 0; k < Scan_${scan.id}.Length; k++) _scan_${b.id}[k] = ${mk};`);
  }
  L.push('            }');
  L.push('        }');
  L.push('');
  L.push('        protected override void OnBarUpdate()');
  L.push('        {');
  if (scan) {
    const sig = scanSignal(recipe, scan);
    L.push('            if (BarsInProgress != 0)', '            {',
      `                // ${scan.id}: a scanned symbol just closed a bar (its own OnBarUpdate, so the chart series running first on shared timestamps does not matter):`,
      `                // ${sig} on that symbol at barsAgo 0. Alert() only fires in State.Realtime; one alert per symbol and closed bar.`,
      '                _s = BarsInProgress;',
      `                if (CurrentBars[_s] >= Warmup && ${bool(sig, '0')})`,
      `                    Alert(${q(`bsv_scan_${scan.id}_`)} + _s, Priority.Medium, ${q(`BSV scan ${scan.id}: `)} + Scan_${scan.id}[_s - 1], "", 0, Brushes.Black, Brushes.Yellow);`,
      '                _s = 0;', '                return;', '            }');
  }
  if (htfPeriods.length) {
    L.push('            if (BarsInProgress != 0) return; // the higher-timeframe series only update their own bars');
    for (const b of inds.filter(x => htfTfOf(recipe, x))) L.push(`            _htf_${b.id}[0] = CurrentBars[${bip(b)}] >= ${Number(b.params.length) || 1} ? _${b.id}[0] : double.NaN; // last closed ${htfTfOf(recipe, b).replace('BarsPeriodType.', '').replace(', ', ' ')} bar`);
  }
  L.push('            if (CurrentBar < Warmup)');
  L.push('                return;');
  L.push('            // Calculate.OnBarClose: barsAgo 0 is the bar that just closed.');
  plots.forEach((p, k) => L.push(`            Values[${k}][0] = ${val(p.params?.source, '0')};`));
  for (const a of alerts) {
    L.push(`            // ${a.id}: Alert() only fires in State.Realtime; once per closed bar.`);
    L.push(`            if (${bool(a.params?.when, '0')})`);
    L.push(`                Alert(${q('bsv_' + a.id)}, Priority.Medium, ${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}, "", 0, Brushes.Black, Brushes.Yellow);`);
  }
  L.push('        }');
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': case 'indicator.atr':
        L.push('', htfTfOf(recipe, b) ? `        private double V_${b.id}(int ago) { return _htf_${b.id}[ago]; } // last closed higher-timeframe bar as of each chart bar` : scan ? `        private double V_${b.id}(int ago) { return _s == 0 ? _${b.id}[ago] : _scan_${b.id}[_s - 1][ago]; }` : `        private double V_${b.id}(int ago) { return _${b.id}[ago]; }`);
        break;
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { L.push('', `        private double V_${b.id}(int ago) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const hl = (p.source || 'close') === 'high_low', R = p.right, Lf = p.left, xh = at => NX(hl ? 'high' : 'close', at), xl = at => NX(hl ? 'low' : 'close', at);
        L.push('', `        // ${b.id}: barsAgo a confirms a pivot at a + ${R}: above the ${Lf} bars before it and at least as high as the ${R} after it (a flat top counts once);`,
          `        // known only at a, so no lookahead. The last confirmed pivot is found by scanning back (NaN before the first). Same rule as the Pine / MQL5 targets.`,
          `        private bool S_${b.id}_ph(int a) { int c = a + ${R}; if (c + ${Lf} > CurrentBars[_s]) return false; double v = ${xh('c')}; for (int k = 1; k <= ${Lf}; k++) if (${xh('c + k')} >= v) return false; for (int k = 1; k <= ${R}; k++) if (${xh('c - k')} > v) return false; return true; }`,
          `        private bool S_${b.id}_pl(int a) { int c = a + ${R}; if (c + ${Lf} > CurrentBars[_s]) return false; double v = ${xl('c')}; for (int k = 1; k <= ${Lf}; k++) if (${xl('c + k')} <= v) return false; for (int k = 1; k <= ${R}; k++) if (${xl('c - k')} < v) return false; return true; }`,
          `        private double V_${b.id}_high(int a) { for (int k = a; k + ${R + Lf} <= CurrentBars[_s]; k++) if (S_${b.id}_ph(k)) return ${xh(`k + ${R}`)}; return double.NaN; }`,
          `        private double V_${b.id}_low(int a) { for (int k = a; k + ${R + Lf} <= CurrentBars[_s]; k++) if (S_${b.id}_pl(k)) return ${xl(`k + ${R}`)}; return double.NaN; }`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { L.push('', `        private bool S_${b.id}(int ago) { return false; } // TODO unsupported block ${b.type}: ${b.id}`); break; }
        const pb = map.get(p.pivot), pq = pb.params, R = pq.right, Lf = pq.left, hl = (pq.source || 'close') === 'high_low', o = p.oscillator, d = p.direction || 'both', v = pb.id;
        const xh = at => NX(hl ? 'high' : 'close', at), xl = at => NX(hl ? 'low' : 'close', at);
        L.push('', `        // ${b.id}: regular divergence, true on the bar that confirms the new pivot (barsAgo a + ${R}), compared with the pivot before it (scanning back).`,
          `        private bool S_${b.id}_bear(int a) { if (!S_${v}_ph(a)) return false; for (int k = a + 1; k + ${R + Lf} <= CurrentBars[_s]; k++) if (S_${v}_ph(k)) { double o1 = ${val(o, `a + ${R}`)}; double o0 = ${val(o, `k + ${R}`)}; return !double.IsNaN(o1) && !double.IsNaN(o0) && ${xh(`a + ${R}`)} > ${xh(`k + ${R}`)} && o1 < o0; } return false; }`,
          `        private bool S_${b.id}_bull(int a) { if (!S_${v}_pl(a)) return false; for (int k = a + 1; k + ${R + Lf} <= CurrentBars[_s]; k++) if (S_${v}_pl(k)) { double o1 = ${val(o, `a + ${R}`)}; double o0 = ${val(o, `k + ${R}`)}; return !double.IsNaN(o1) && !double.IsNaN(o0) && ${xl(`a + ${R}`)} < ${xl(`k + ${R}`)} && o1 > o0; } return false; }`,
          `        private bool S_${b.id}(int ago) { return ${d === 'both' ? `S_${b.id}_bear(ago) || S_${b.id}_bull(ago)` : d === 'bearish' ? `S_${b.id}_bear(ago)` : `S_${b.id}_bull(ago)`}; }`);
        break;
      }
      case 'scanner.symbol_set':
        if (scan !== b) L.push('', `        private double V_${b.id}(int ago) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id} - ${scanWhyNot(recipe, b)}`);
        else L.push('', `        // ${b.id}: symbol scan of ${scanSignal(recipe, b)} on ${ssyms.join(', ')} (AddDataSeries in State.Configure, evaluated in each symbol's OnBarUpdate)`);
        break;
      case 'data.higher_timeframe':
        if (htfDataUsed(recipe, b)) { L.push('', `        // ${b.id}: higher timeframe ${b.params.timeframe} (AddDataSeries in State.Configure, closed bars only)`); break; }
        L.push('', `        private double V_${b.id}(int ago) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push('', `        // TODO ${b.id}: Time[] uses the NinjaTrader time zone setting (Tools > Options > General); convert session ${p.session || ''} from ${p.timezone || 'Etc/UTC'}.`,
          `        private bool S_${b.id}(int ago) { DateTime t = ${scan ? 'Times[_s][ago]' : 'Time[ago]'}; int m = t.Hour * 60 + t.Minute; return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push('', `        private bool S_${b.id}(int ago) { return ${val(p.left, 'ago')} ${gt} ${val(p.right, 'ago')} && ${val(p.left, 'ago + 1')} ${le} ${val(p.right, 'ago + 1')}; }`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push('', `        private bool S_${b.id}(int ago) { return ${val(p.left, 'ago')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'ago') : Number(p.value)}; }`);
        break;
      case 'signal.recent':
        L.push('', `        private bool S_${b.id}(int ago) { return ${orOf(p.bars, k => bool(p.signal, `ago + ${k}`), ' || ')}; } // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before`);
        break;
      case 'signal.combine':
        L.push('', `        private bool S_${b.id}(int ago) { return ${(p.signals || []).map(x => bool(x, 'ago')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; }`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push('', `        private bool S_${b.id}(int ago) { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push('', `        private double V_${b.id}(int ago) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('    }');
  L.push('}');
  L.push('// The NinjaScript Editor appends its own "NinjaScript generated code" region on compile; do not hand-edit it.');
  return L.join('\n') + '\n';
}

function renderQuantower(recipe) {
  const map = blockMap(recipe);
  const cls = 'Bsv' + className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const inds = recipe.blocks.filter(b => ['indicator.ema', 'indicator.sma', 'indicator.rsi', 'indicator.atr'].includes(b.type));
  const pt = { open: 'PriceType.Open', high: 'PriceType.High', low: 'PriceType.Low', close: 'PriceType.Close', hl2: 'PriceType.Median', hlc3: 'PriceType.Typical' };
  const priceAt = (ref, at) => ref === 'ohlc4' ? `(GetPrice(PriceType.Open, ${at}) + GetPrice(PriceType.High, ${at}) + GetPrice(PriceType.Low, ${at}) + GetPrice(PriceType.Close, ${at})) / 4.0` : `GetPrice(${pt[ref]}, ${at})`;
  const val = (ref, at) => isPrice(ref) ? priceAt(ref, at) : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0 : 0.0)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0 && !double.IsNaN(${val(ref, at)}))`;
  const colors = ['DodgerBlue', 'Orange', 'LimeGreen', 'Magenta', 'Gold', 'Aqua'];
  const L = [];
  L.push('// ORIGINAL BSV STARTER — Quantower Algo indicator (C#). Build in Quantower Algo / Visual Studio before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push('using System;');
  L.push('using System.Drawing;');
  L.push('using TradingPlatform.BusinessLayer;');
  L.push('');
  L.push('namespace BsvIndicators');
  L.push('{');
  L.push(`    public class ${cls} : Indicator`);
  L.push('    {');
  L.push(`        private const int Warmup = ${warmup(recipe)};`);
  for (const b of inds) L.push(`        private Indicator _${b.id};`);
  for (const a of alerts) L.push(`        private DateTime _alert_${a.id} = DateTime.MinValue;`);
  L.push('');
  L.push(`        public ${cls}()`);
  L.push('            : base()');
  L.push('        {');
  L.push(`            Name = ${q('BSV — ' + safeTitle(recipe))};`);
  L.push('            Description = "Original BSV generated starter. Not runtime tested by BSV.";');
  plots.forEach((p, k) => L.push(`            AddLineSeries(${q(String(p.params?.title || p.id).replace(/"/g, ''))}, Color.${colors[k % colors.length]}, 1, LineStyle.Solid);`));
  L.push(`            SeparateWindow = ${recipe.overlay ? 'false' : 'true'};`);
  L.push('        }');
  L.push('');
  L.push('        protected override void OnInit()');
  L.push('        {');
  for (const b of inds) {
    const p = b.params || {};
    const src = () => pt[sourceName(p.source)] || 'PriceType.Close';
    const note = () => sourceName(p.source) === 'ohlc4' ? ' // TODO ohlc4 has no PriceType; using Close' : '';
    if (b.type === 'indicator.ema') L.push(`            _${b.id} = Core.Indicators.BuiltIn.EMA(${p.length}, ${src()});${note()}`);
    if (b.type === 'indicator.sma') L.push(`            _${b.id} = Core.Indicators.BuiltIn.SMA(${p.length}, ${src()});${note()}`);
    if (b.type === 'indicator.rsi') L.push(`            _${b.id} = Core.Indicators.BuiltIn.RSI(${p.length}, ${src()}, RSIMode.Exponential, MaMode.SMA, 1);${note()}`);
    if (b.type === 'indicator.atr') L.push(`            _${b.id} = Core.Indicators.BuiltIn.ATR(${p.length}, MaMode.SMMA);`);
    L.push(`            AddIndicator(_${b.id});`);
  }
  L.push('        }');
  L.push('');
  L.push('        protected override void OnUpdate(UpdateArgs args)');
  L.push('        {');
  L.push('            if (Count <= Warmup)');
  L.push('                return;');
  plots.forEach((p, k) => L.push(`            SetValue(${val(p.params?.source, '0')}, ${k});`));
  if (alerts.length) {
    L.push('            if (args.Reason != UpdateReason.NewBar)');
    L.push('                return;');
    L.push('            int i = 1; // the bar that just closed');
    for (const a of alerts) {
      L.push(`            if (${bool(a.params?.when, 'i')} && _alert_${a.id} != Time(i))`);
      L.push('            {');
      L.push(`                _alert_${a.id} = Time(i);`);
      L.push(`                Core.Instance.Loggers.Log(${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}); // event log line; no order placement`);
      L.push('            }');
    }
  }
  L.push('        }');
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': case 'indicator.atr':
        L.push('', `        private double V_${b.id}(int offset) { return _${b.id}.GetValue(offset); }`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push('', `        // TODO ${b.id}: check the time zone of Time() for your connection; convert session ${p.session || ''} from ${p.timezone || 'Etc/UTC'}.`,
          `        private bool S_${b.id}(int offset) { DateTime t = Time(offset); int m = t.Hour * 60 + t.Minute; return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push('', `        private bool S_${b.id}(int offset) { return ${val(p.left, 'offset')} ${gt} ${val(p.right, 'offset')} && ${val(p.left, 'offset + 1')} ${le} ${val(p.right, 'offset + 1')}; }`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push('', `        private bool S_${b.id}(int offset) { return ${val(p.left, 'offset')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'offset') : Number(p.value)}; }`);
        break;
      case 'signal.recent':
        L.push('', `        private bool S_${b.id}(int offset) { return ${orOf(p.bars, k => bool(p.signal, `offset + ${k}`), ' || ')}; } // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before`);
        break;
      case 'signal.combine':
        L.push('', `        private bool S_${b.id}(int offset) { return ${(p.signals || []).map(x => bool(x, 'offset')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; }`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push('', `        private bool S_${b.id}(int offset) { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push('', `        private double V_${b.id}(int offset) { return double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('    }');
  L.push('}');
  return L.join('\n') + '\n';
}


function lipiText(s) {
  return '"' + String(s ?? '').replace(/["\\\r\n]/g, ' ').trim() + '"';
}

function renderLipi(recipe) {
  const RESERVED = new Set(['open', 'high', 'low', 'close', 'volume', 'hl2', 'hlc3', 'hlcc4', 'ohlc4', 'bar_index', 'time', 'time_close', 'timenow', 'year', 'month', 'dayofmonth', 'dayofweek', 'hour', 'minute', 'second', 'na', 'true', 'false', 'and', 'or', 'not', 'if', 'else', 'switch', 'case', 'default', 'static', 'intra', 'for', 'while', 'return', 'color', 'input', 'math', 'str', 'talib', 'plot', 'alert', 'session', 'interval', 'syminfo', 'barstate', 'float', 'int', 'bool', 'string', 'shape', 'location', 'size', 'orderflow', 'chartPoint']);
  const map = blockMap(recipe);
  const nm = new Map(recipe.blocks.map(b => [b.id, RESERVED.has(b.id) ? b.id + '_v' : b.id]));
  const ref = (r) => isPrice(r) ? r : nm.get(r);
  const bool = (r) => isBoolType(map.get(r)?.type) ? nm.get(r) : `(${ref(r)} != 0)`;
  const colors = ['30, 144, 255', '255, 165, 0', '50, 205, 50', '255, 0, 255', '0, 255, 255', '220, 80, 80'];
  const L = [];
  L.push('// ORIGINAL BSV STARTER — GoCharting Lipi indicator. Paste into the Lipi editor and check it there.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push('// Lipi draws on the chart only: no orders, no other symbols, no other timeframes.');
  L.push(`indicator(${lipiText('BSV — ' + safeTitle(recipe))}, "BSV", ${recipe.overlay ? 'true' : 'false'})`);
  L.push('');
  for (const b of depOrder(recipe)) {
    const p = b.params || {}, n = nm.get(b.id);
    switch (b.type) {
      case 'indicator.ema': L.push(`float ${n} = talib.ema(${sourceName(p.source)}, ${p.length})`); break;
      case 'indicator.sma': L.push(`float ${n} = talib.sma(${sourceName(p.source)}, ${p.length})`); break;
      case 'indicator.rsi': L.push(`float ${n} = talib.rsi(${sourceName(p.source)}, ${p.length})`); break;
      case 'indicator.atr': L.push(`float ${n} = talib.atr(${p.length})`); break;
      case 'filter.session': {
        const ss = parseSession(p), tz = String(p.timezone || 'Etc/UTC').replace(/["\\\s]/g, '');
        L.push(`// ${b.id}: session ${p.session || '0000-2359'} in ${tz}, read from the bar's open time (check against your chart).`);
        L.push(`int ${n}_m = hour(time, "${tz}") * 60 + minute(time, "${tz}")`);
        L.push(`bool ${n} = ${ss.start <= ss.end ? `${n}_m >= ${ss.start} and ${n}_m < ${ss.end}` : `${n}_m >= ${ss.start} or ${n}_m < ${ss.end}`}`);
        break;
      }
      case 'signal.cross':
        L.push(`bool ${n} = ${p.direction === 'below' ? 'talib.crossunder' : 'talib.crossover'}(${ref(p.left)}, ${ref(p.right)})`);
        break;
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`bool ${n} = ${ref(p.left)} ${thresholdOp(p)} ${p.right !== undefined ? ref(p.right) : Number(p.value)}`);
        break;
      case 'signal.recent':
        L.push(`bool ${n} = ${orOf(p.bars, k => `${bool(p.signal)}[${k}]`, ' or ')}`);
        break;
      case 'signal.combine':
        L.push(`bool ${n} = ${(p.signals || []).length ? p.signals.map(x => bool(x)).join(p.mode === 'any' ? ' or ' : ' and ') : 'false'}`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        L.push(isBoolType(b.type) ? `bool ${n} = false // TODO unsupported block ${b.type}: ${b.id}` : `float ${n} = na // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  if (plots.length) L.push('');
  plots.forEach((b, k) => L.push(`plot(${ref(b.params?.source)}, title = ${lipiText(b.params?.title || b.params?.source || b.id)}, color = color.rgb(${colors[k % colors.length]}), linewidth = 2)`));
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  if (alerts.length) {
    L.push('');
    L.push('// Alerts: alertcondition offers a named condition in the GoCharting alert dialog; alert() fires on realtime bars only,');
    L.push('// at most once a bar. Testing the previous bar ([1]) makes it fire once per closed bar.');
    for (const a of alerts) {
      const w = bool(a.params?.when), msg = lipiText(a.params?.message || a.id);
      const down = signalDown(map, a.params?.when);
      L.push(`alertcondition(${w}, ${lipiText(a.id)}, ${msg})`);
      if (recipe.overlay) L.push(`plotshape(${w}, title = ${lipiText(a.id)}, shape = ${down ? 'shape.triangledown' : 'shape.triangleup'}, location = ${down ? 'location.abovebar' : 'location.belowbar'}, color = color.rgb(${down ? '220, 80, 80' : '50, 205, 50'}), size = size.tiny)`);
      L.push(`if ${/^[A-Za-z_][A-Za-z0-9_]*$/.test(w) ? w : '(' + w + ')'}[1] {`, `    alert(${msg})`, '}');
    }
  }
  L.push('');
  L.push('// End BSV generated starter.');
  return L.join('\n') + '\n';
}

function javaText(s) {
  return '"' + String(s ?? '').replace(/["\\\r\n]/g, ' ').trim() + '"';
}

function renderMotiveWave(recipe) {
  const map = blockMap(recipe);
  const cls = 'Bsv' + className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const rsis = recipe.blocks.filter(b => b.type === 'indicator.rsi');
  const bi = { open: 'OPEN', high: 'HIGH', low: 'LOW', close: 'CLOSE', hl2: 'MIDPOINT', hlc3: 'TP', ohlc4: 'WP' };
  const px = { open: 'series.getOpen(i)', high: 'series.getHigh(i)', low: 'series.getLow(i)', close: 'series.getClose(i)', hl2: '(series.getHigh(i) + series.getLow(i)) / 2.0', hlc3: '(series.getHigh(i) + series.getLow(i) + series.getClose(i)) / 3.0', ohlc4: '(series.getOpen(i) + series.getHigh(i) + series.getLow(i) + series.getClose(i)) / 4.0' };
  const priceAt = (ref, at) => `P_${ref}(${at})`;
  const val = (ref, at) => isPrice(ref) ? priceAt(ref, at) : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0 : 0.0)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0 && !Double.isNaN(${val(ref, at)}))`;
  const colors = ['30, 144, 255', '255, 165, 0', '50, 205, 50', '255, 0, 255', '0, 255, 255', '220, 80, 80'];
  const usedPrices = new Set();
  const scan = (ref) => { if (isPrice(ref)) usedPrices.add(ref); };
  for (const b of recipe.blocks) { const p = b.params || {}; [p.left, p.right, p.source].forEach(scan); }
  for (const b of rsis) usedPrices.add(sourceName(b.params?.source));
  const L = [];
  L.push('// ORIGINAL BSV STARTER — MotiveWave SDK custom study (Java). Build with the MotiveWave SDK before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// Save as ${cls}.java in an SDK project, build the jar and load it in MotiveWave (Extensions folder). No orders are placed.`);
  L.push('package com.botshelfvampire.generated;');
  L.push('');
  L.push('import java.awt.Color;');
  if (recipe.blocks.some(b => b.type === 'filter.session')) { L.push('import java.time.Instant;', 'import java.time.ZoneId;', 'import java.time.ZonedDateTime;'); }
  L.push('');
  L.push('import com.motivewave.platform.sdk.common.DataContext;');
  L.push('import com.motivewave.platform.sdk.common.DataSeries;');
  L.push('import com.motivewave.platform.sdk.common.Defaults;');
  L.push('import com.motivewave.platform.sdk.common.Enums;');
  L.push('import com.motivewave.platform.sdk.common.desc.PathDescriptor;');
  L.push('import com.motivewave.platform.sdk.study.Study;');
  L.push('import com.motivewave.platform.sdk.study.StudyHeader;');
  L.push('');
  L.push('@StudyHeader(');
  L.push('    namespace = "com.botshelfvampire.generated",');
  L.push(`    id = ${javaText(cls.toUpperCase())},`);
  L.push(`    name = ${javaText('BSV — ' + safeTitle(recipe))},`);
  L.push('    desc = "Original BSV generated starter. Not runtime tested by BSV.",');
  L.push('    menu = "BSV",');
  L.push(`    overlay = ${recipe.overlay ? 'true' : 'false'}${alerts.length ? ',' : ''}`);
  if (alerts.length) L.push('    signals = true');
  L.push(')');
  L.push(`public class ${cls} extends Study`);
  L.push('{');
  const vals = [...plots.map((_, k) => `PLOT${k}`), ...rsis.flatMap(b => [`U_${b.id}`, `D_${b.id}`])];
  L.push(`    enum Values { ${vals.length ? vals.join(', ') : 'NONE'} }`);
  if (alerts.length) L.push(`    enum Signals { ${alerts.map(a => 'A_' + a.id).join(', ')} }`);
  L.push(`    private static final int WARMUP = ${warmup(recipe)};`);
  L.push('    private DataSeries series;');
  L.push('');
  L.push('    @Override');
  L.push('    public void initialize(Defaults defaults)');
  L.push('    {');
  L.push('        var sd = createSD();');
  L.push('        var grp = sd.addTab("General").addGroup("Plots");');
  plots.forEach((p, k) => L.push(`        grp.addRow(new PathDescriptor("path${k}", ${javaText(p.params?.title || p.params?.source || p.id)}, new Color(${colors[k % colors.length]}), 1.5f, null, true, true, true));`));
  L.push('        var rd = createRD();');
  plots.forEach((p, k) => L.push(`        rd.declarePath(Values.PLOT${k}, "path${k}");`));
  if (plots.length) L.push(`        rd.setRangeKeys(${plots.map((_, k) => `Values.PLOT${k}`).join(', ')});`);
  for (const a of alerts) L.push(`        rd.declareSignal(Signals.A_${a.id}, ${javaText(a.params?.message || a.id)});`);
  L.push('    }');
  L.push('');
  L.push('    @Override');
  L.push('    protected void calculate(int index, DataContext ctx)');
  L.push('    {');
  L.push('        series = ctx.getDataSeries();');
  for (const b of rsis) {
    const s = sourceName(b.params?.source);
    L.push(`        if (index >= 1) { double ch = P_${s}(index) - P_${s}(index - 1); series.setDouble(index, Values.U_${b.id}, Math.max(ch, 0.0)); series.setDouble(index, Values.D_${b.id}, Math.max(-ch, 0.0)); }`);
  }
  L.push('        if (index < WARMUP)');
  L.push('            return;');
  plots.forEach((p, k) => L.push(`        { double v = ${val(p.params?.source, 'index')}; if (!Double.isNaN(v)) series.setDouble(index, Values.PLOT${k}, v); }`));
  L.push('        boolean closed = series.isBarComplete(index);');
  if (alerts.length) {
    L.push('        // Signals only on closed bars; MotiveWave raises each signal at most once per bar index.');
    for (const a of alerts) L.push(`        if (closed && ${bool(a.params?.when, 'index')})`, `            ctx.signal(index, Signals.A_${a.id}, ${javaText(a.params?.message || a.id)}, series.getClose(index));`);
  }
  L.push('        series.setComplete(index, closed);');
  L.push('    }');
  L.push('');
  L.push('    private static double d(Double v) { return v == null ? Double.NaN : v; }');
  for (const s of usedPrices) L.push(`    private double P_${s}(int i) { return ${px[s]}; }`);
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': L.push(`    private double V_${b.id}(int i) { return d(series.ema(i, ${p.length}, Enums.BarInput.${bi[sourceName(p.source)]})); }`); break;
      case 'indicator.sma': L.push(`    private double V_${b.id}(int i) { return d(series.sma(i, ${p.length}, Enums.BarInput.${bi[sourceName(p.source)]})); }`); break;
      case 'indicator.atr': L.push(`    private double V_${b.id}(int i) { return d(series.atr(i, ${p.length})); }`); break;
      case 'indicator.rsi':
        L.push(`    // ${b.id}: Wilder RSI from smoothed (SMMA) gains/losses stored per bar.`,
          `    private double V_${b.id}(int i) { double u = d(series.smma(i, ${p.length}, Values.U_${b.id})), dn = d(series.smma(i, ${p.length}, Values.D_${b.id})); if (Double.isNaN(u) || Double.isNaN(dn)) return Double.NaN; return dn == 0.0 ? 100.0 : 100.0 - 100.0 / (1.0 + u / dn); }`);
        break;
      case 'filter.session': {
        const ss = parseSession(p), tz = String(p.timezone || 'Etc/UTC').replace(/["\\\s]/g, '');
        L.push(`    // ${b.id}: session ${p.session || '0000-2359'} in ${tz}, read from the bar start time.`,
          `    private static final ZoneId TZ_${b.id} = ZoneId.of(${javaText(tz)});`,
          `    private boolean S_${b.id}(int i) { ZonedDateTime t = Instant.ofEpochMilli(series.getStartTime(i)).atZone(TZ_${b.id}); int m = t.getHour() * 60 + t.getMinute(); return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`    private boolean S_${b.id}(int i) { return i >= 1 && ${val(p.left, 'i')} ${gt} ${val(p.right, 'i')} && ${val(p.left, 'i - 1')} ${le} ${val(p.right, 'i - 1')}; }`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`    private boolean S_${b.id}(int i) { return ${val(p.left, 'i')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'i') : Number(p.value)}; }`);
        break;
      case 'signal.recent':
        L.push(`    private boolean S_${b.id}(int i) { return ${orOf(p.bars, k => `(i >= ${k} && ${bool(p.signal, `i - ${k}`)})`, ' || ')}; } // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before i`);
        break;
      case 'signal.combine':
        L.push(`    private boolean S_${b.id}(int i) { return ${(p.signals || []).map(x => bool(x, 'i')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; }`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push(`    private boolean S_${b.id}(int i) { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push(`    private double V_${b.id}(int i) { return Double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('}');
  return L.join('\n') + '\n';
}

function renderVela(recipe) {
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const nm = (r) => isPrice(r) ? `px.${r}` : `b_${r}`;
  const isB = (r) => !isPrice(r) && isBoolType(map.get(r)?.type);
  const num = (r) => isB(r) ? `toNum(${nm(r)})` : nm(r);
  const bool = (r) => isB(r) ? nm(r) : `toBool(${nm(r)})`;
  const colors = ['#1e90ff', '#ffa500', '#32cd32', '#ff00ff', '#00ffff', '#dc5050'];
  const L = [];
  L.push('// ORIGINAL BSV STARTER — Vela (LuxAlgo, Apache-2.0) chart with a small BSV recipe engine. Plain JavaScript, no Pine runtime.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice. No network requests, no orders.');
  L.push('// npm install @luxalgo/vela   then import this module from a page that has <div id="chart"></div> (see platforms/vela).');
  L.push("import { Vela } from '@luxalgo/vela';");
  L.push("import { stableSeriesId } from '@luxalgo/vela/plugin';");
  L.push('');
  L.push(`const TITLE = ${q('BSV — ' + safeTitle(recipe))};`);
  L.push(`const OVERLAY = ${recipe.overlay ? 'true' : 'false'};`);
  L.push('');
  L.push('// ---- helpers (Wilder RSI/ATR, SMA-seeded EMA; NaN until enough bars) ----');
  L.push('const toNum = (a) => a.map(x => (x ? 1 : 0));');
  L.push('const toBool = (a) => a.map(x => Number.isFinite(x) && x !== 0);');
  L.push('function sma(s, n) { const o = new Array(s.length).fill(NaN); let sum = 0, cnt = 0; for (let i = 0; i < s.length; i++) { sum += s[i]; cnt++; if (i >= n) { sum -= s[i - n]; cnt--; } if (cnt === n) o[i] = sum / n; } return o; }');
  L.push('function ema(s, n) { const o = new Array(s.length).fill(NaN), a = 2 / (n + 1); let p = NaN, sum = 0; for (let i = 0; i < s.length; i++) { if (i < n) { sum += s[i]; if (i === n - 1) p = sum / n; else continue; } else p = a * s[i] + (1 - a) * p; o[i] = p; } return o; }');
  L.push('function rma(s, n, from) { const o = new Array(s.length).fill(NaN); let p = NaN, sum = 0; for (let i = from; i < s.length; i++) { const k = i - from; if (k < n) { sum += s[i]; if (k === n - 1) p = sum / n; else continue; } else p = (p * (n - 1) + s[i]) / n; o[i] = p; } return o; }');
  L.push('function rsi(s, n) { const up = s.map((x, i) => (i ? Math.max(x - s[i - 1], 0) : 0)), dn = s.map((x, i) => (i ? Math.max(s[i - 1] - x, 0) : 0)); const u = rma(up, n, 1), d = rma(dn, n, 1); return u.map((x, i) => (Number.isNaN(x) ? NaN : d[i] === 0 ? 100 : 100 - 100 / (1 + x / d[i]))); }');
  L.push('function atr(bars, n) { const tr = bars.map((b, i) => (i ? Math.max(b.high - b.low, Math.abs(b.high - bars[i - 1].close), Math.abs(b.low - bars[i - 1].close)) : b.high - b.low)); return rma(tr, n, 0); }');
  L.push('function cross(a, b, up) { return a.map((x, i) => i > 0 && (up ? x > b[i] && a[i - 1] <= b[i - 1] : x < b[i] && a[i - 1] >= b[i - 1])); }');
  L.push('function minutesIn(tz) { const f = new Intl.DateTimeFormat(\'en-GB\', { timeZone: tz, hour: \'2-digit\', minute: \'2-digit\', hourCycle: \'h23\' }); return (t) => { const p = f.formatToParts(new Date(t)); return Number(p.find(x => x.type === \'hour\').value) * 60 + Number(p.find(x => x.type === \'minute\').value); }; }');
  L.push('');
  L.push('// ---- the recipe, compiled from its blocks ----');
  L.push('function compute(bars) {');
  L.push('  const px = { open: bars.map(b => b.open), high: bars.map(b => b.high), low: bars.map(b => b.low), close: bars.map(b => b.close) };');
  L.push('  px.hl2 = bars.map(b => (b.high + b.low) / 2); px.hlc3 = bars.map(b => (b.high + b.low + b.close) / 3); px.ohlc4 = bars.map(b => (b.open + b.high + b.low + b.close) / 4);');
  for (const b of depOrder(recipe)) {
    const p = b.params || {}, n = `b_${b.id}`;
    switch (b.type) {
      case 'indicator.ema': L.push(`  const ${n} = ema(px.${sourceName(p.source)}, ${p.length});`); break;
      case 'indicator.sma': L.push(`  const ${n} = sma(px.${sourceName(p.source)}, ${p.length});`); break;
      case 'indicator.rsi': L.push(`  const ${n} = rsi(px.${sourceName(p.source)}, ${p.length});`); break;
      case 'indicator.atr': L.push(`  const ${n} = atr(bars, ${p.length});`); break;
      case 'filter.session': {
        const ss = parseSession(p), tz = String(p.timezone || 'Etc/UTC').replace(/["\\\s']/g, '');
        L.push(`  // ${b.id}: session ${p.session || '0000-2359'} in ${tz}, read from each bar's open time.`);
        L.push(`  const m_${b.id} = minutesIn(${q(tz)});`);
        L.push(`  const ${n} = bars.map(x => { const m = m_${b.id}(x.time); return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; });`);
        break;
      }
      case 'signal.cross': L.push(`  const ${n} = cross(${num(p.left)}, ${num(p.right)}, ${p.direction === 'below' ? 'false' : 'true'});`); break;
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`  const ${n} = ${num(p.left)}.map(${p.right !== undefined ? '(x, i)' : 'x'} => x ${thresholdOp(p) === '==' ? '===' : thresholdOp(p) === '!=' ? '!==' : thresholdOp(p)} ${p.right !== undefined ? `${num(p.right)}[i]` : Number(p.value)});`);
        break;
      case 'signal.recent':
        L.push(`  const ${n} = bars.map((_, i) => ${orOf(p.bars, k => `(i >= ${k} && !!${bool(p.signal)}[i - ${k}])`, ' || ')});`);
        break;
      case 'signal.combine': {
        const sigs = (p.signals || []).map(bool);
        L.push(`  const ${n} = bars.map((_, i) => ${sigs.length ? sigs.map(s => `${s}[i]`).join(p.mode === 'any' ? ' || ' : ' && ') : 'false'});`);
        break;
      }
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        L.push(isBoolType(b.type) ? `  const ${n} = bars.map(() => false); // TODO unsupported block ${b.type}: ${b.id}` : `  const ${n} = bars.map(() => NaN); // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('  return {');
  L.push('    plots: [');
  plots.forEach((b, k) => L.push(`      { title: ${q(b.params?.title || b.params?.source || b.id)}, color: ${q(colors[k % colors.length])}, values: ${num(b.params?.source)} },`));
  L.push('    ],');
  L.push('    alerts: [');
  for (const a of alerts) {
    const down = signalDown(map, a.params?.when);
    L.push(`      { id: ${q(a.id)}, message: ${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}, down: ${down ? 'true' : 'false'}, when: ${bool(a.params?.when)} },`);
  }
  L.push('    ]');
  L.push('  };');
  L.push('}');
  L.push('');
  L.push('// ---- a minimal ScriptingEngine (Vela engine port): static runs, no inputs, no network ----');
  L.push('export const bsvRecipeEngine = {');
  L.push("  language: 'bsv-recipe',");
  L.push('  capabilities: { streaming: false, visibleRange: false, inputs: false },');
  L.push("  async prepare(source, instanceId) { return { language: 'bsv-recipe', inputs: [], meta: { title: TITLE, overlay: OVERLAY }, reactsToViewport: false, token: { instanceId } }; },");
  L.push('  execute(req, handlers) {');
  L.push('    const id = req.prepared.token.instanceId; let stopped = false, armedAfter = null; const fired = new Set();');
  L.push('    const run = () => {');
  L.push('      if (stopped) return;');
  L.push('      try {');
  L.push('        const bars = req.getBars ? req.getBars() : req.bars; if (!bars.length) return;');
  L.push('        const r = compute(bars);');
  L.push("        const series = r.plots.map((p, k) => ({ id: stableSeriesId({ instanceId: id, kind: 'line', title: p.title, ordinal: k }), title: p.title, paneId: '', kind: 'line', points: bars.map((b, i) => ({ time: b.time, value: Number.isFinite(p.values[i]) ? p.values[i] : null })), style: { color: p.color, width: 2, lineStyle: 'solid' } }));");
  L.push("        const labels = [];");
  L.push("        if (OVERLAY) r.alerts.forEach((a) => { let k = 0; bars.forEach((b, i) => { if (!a.when[i]) return; labels.push({ id: stableSeriesId({ instanceId: id, kind: 'label', title: a.id, ordinal: k++ }), paneId: '', xloc: 'bar_time', x: b.time, y: a.down ? b.high : b.low, yloc: a.down ? 'abovebar' : 'belowbar', style: a.down ? 'triangledown' : 'triangleup', color: a.down ? '#dc5050' : '#32cd32', size: 'small', textAlign: 'center', fontFamily: 'default', tooltip: a.message }); }); });");
  L.push("        handlers.onModel({ id, title: TITLE, overlay: OVERLAY, paneHint: OVERLAY ? 'price' : 'new', series, labels, fills: [], backgrounds: [], priceLines: [], inputs: [], inputValues: {} });");
  L.push('        // Alerts: only for bars that close after the first run; the last bar may still be forming, so check the one before it.');
  L.push('        const last = bars.length - 1;');
  L.push('        if (armedAfter === null) armedAfter = bars[last].time;');
  L.push('        else if (last >= 1 && bars[last - 1].time >= armedAfter) for (const a of r.alerts) { const key = a.id + "@" + bars[last - 1].time; if (a.when[last - 1] && !fired.has(key)) { fired.add(key); handlers.onAlert && handlers.onAlert({ id: a.id, message: a.message, title: TITLE, time: bars[last - 1].time, barIndex: last - 1 }); } }');
  L.push('        handlers.onDone && handlers.onDone();');
  L.push('      } catch (e) { handlers.onError && handlers.onError(e); }');
  L.push('    };');
  L.push("    if (req.historyState !== 'backfill') Promise.resolve().then(run);");
  L.push("    return { stop() { stopped = true; }, update() { run(); }, setVisibleRange() {}, notifyBars(reason) { if (reason !== 'backfill') run(); } };");
  L.push('  }');
  L.push('};');
  L.push('');
  L.push('// ---- usage: replace sampleBars with your own OHLCV bars ({ time: epoch ms, open, high, low, close, volume }) ----');
  L.push('export function mountBsvChart(target, bars, timeframe = \'1h\') {');
  L.push("  const chart = new Vela(target, { data: bars, timeframe, theme: 'dark' });");
  L.push("  chart.registerEngine('bsv-recipe', bsvRecipeEngine);");
  L.push(`  const handle = chart.addIndicator(${q('bsv-recipe: ' + safeTitle(recipe))}, { language: 'bsv-recipe' });`);
  L.push("  handle.on('alert', (a) => console.log('[BSV alert]', new Date(a.time).toISOString(), a.message));");
  L.push("  handle.on('error', ({ error }) => console.error('[BSV]', error));");
  L.push('  return { chart, handle };');
  L.push('}');
  L.push('');
  L.push('// End BSV generated starter.');
  return L.join('\n') + '\n';
}

function renderJForex(recipe) {
  const map = blockMap(recipe);
  const cls = 'Bsv' + className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const ap = { open: 'OPEN', high: 'HIGH', low: 'LOW', close: 'CLOSE', hl2: 'MEDIAN_PRICE', hlc3: 'TYPICAL_PRICE' };
  const px = { open: 'b.getOpen()', high: 'b.getHigh()', low: 'b.getLow()', close: 'b.getClose()', hl2: '(b.getHigh() + b.getLow()) / 2.0', hlc3: '(b.getHigh() + b.getLow() + b.getClose()) / 3.0', ohlc4: '(b.getOpen() + b.getHigh() + b.getLow() + b.getClose()) / 4.0' };
  const val = (ref, at) => isPrice(ref) ? `P_${ref}(${at})` : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0 : 0.0)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0 && !Double.isNaN(${val(ref, at)}))`;
  const usedPrices = new Set();
  for (const b of recipe.blocks) { const p = b.params || {}; [p.left, p.right, p.source].forEach(r => { if (isPrice(r) && !/^indicator\./.test(b.type)) usedPrices.add(r); }); }
  const L = [];
  L.push('// ORIGINAL BSV STARTER — Dukascopy JForex strategy (Java, IStrategy). Compile it in the JForex platform before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// Save as ${cls}.java in the JForex Strategies folder, compile it and run it on a demo account first.`);
  L.push('// It only reads closed bars and prints values/alerts to the JForex console. It places no orders (IEngine is never used).');
  L.push('import com.dukascopy.api.*;');
  L.push('import java.util.Collections;');
  if (recipe.blocks.some(b => b.type === 'filter.session')) { L.push('import java.time.Instant;', 'import java.time.ZoneId;', 'import java.time.ZonedDateTime;'); }
  L.push('');
  L.push(`public class ${cls} implements IStrategy {`);
  L.push('    @Configurable("Instrument")');
  L.push('    public Instrument instrument = Instrument.EURUSD;');
  L.push('    @Configurable("Period")');
  L.push('    public Period period = Period.ONE_HOUR;');
  L.push('    @Configurable("Offer side")');
  L.push('    public OfferSide side = OfferSide.BID;');
  L.push(`    @Configurable("Print plot values on each closed bar")`);
  L.push(`    public boolean logValues = ${plots.length ? 'true' : 'false'};`);
  const jfTables = tableBlocks(recipe);
  if (jfTables.some(t => t.fields.length)) {
    L.push('    @Configurable("Print value panels on each closed bar")');
    L.push('    public boolean logPanels = true;');
  }
  L.push('');
  L.push('    private IIndicators indicators;');
  L.push('    private IHistory history;');
  L.push('    private IConsole console;');
  L.push('');
  L.push('    @Override');
  L.push('    public void onStart(IContext context) throws JFException {');
  L.push('        indicators = context.getIndicators();');
  L.push('        history = context.getHistory();');
  L.push('        console = context.getConsole();');
  L.push('        context.setSubscribedInstruments(Collections.singleton(instrument), true);');
  L.push(`        console.getOut().println(${javaText('BSV — ' + safeTitle(recipe) + ' started (no orders).')});`);
  L.push('    }');
  L.push('');
  L.push('    @Override');
  L.push('    public void onBar(Instrument inst, Period per, IBar askBar, IBar bidBar) throws JFException {');
  L.push('        if (!inst.equals(instrument) || !per.equals(period))');
  L.push('            return;');
  L.push('        // shift 1 = the bar that just closed, shift 2 = the bar before it.');
  plots.forEach(p => L.push(`        if (logValues) { double v = ${val(p.params?.source, '1')}; if (!Double.isNaN(v)) console.getOut().println(${javaText(p.params?.title || p.params?.source || p.id)} + " = " + v); }`));
  for (const t of jfTables) {
    tableTodos(t, '        //').forEach(x => L.push(x));
    if (!t.fields.length) continue;
    L.push(`        // Value panel ${t.title.replace(/[\r\n]/g, ' ')} (visual.table): one console line per closed bar (shift 1).`);
    const jl = (x) => '"' + String(x).replace(/["\\\r\n]/g, ' ') + '"';
    L.push(`        if (logPanels) console.getOut().println(${t.fields.map((x, k) => `${jl((k ? ' | ' : '[' + t.title + '] ') + x.id + ' = ')} + ${x.bool ? `S_${x.id}(1)` : `V_${x.id}(1)`}`).join(' + ')});`);
  }
  for (const a of alerts) L.push(`        if (${bool(a.params?.when, '1')})`, `            console.getNotif().println(${javaText(a.params?.message || a.id)} + " " + instrument + " " + period);`);
  L.push('    }');
  L.push('');
  L.push('    @Override public void onTick(Instrument inst, ITick tick) throws JFException { }');
  L.push('    @Override public void onMessage(IMessage message) throws JFException { }');
  L.push('    @Override public void onAccount(IAccount account) throws JFException { }');
  L.push('    @Override public void onStop() throws JFException { }');
  L.push('');
  L.push('    private IBar bar(int s) throws JFException { return history.getBar(instrument, period, side, s); }');
  for (const s of usedPrices) L.push(`    private double P_${s}(int s) throws JFException { IBar b = bar(s); return b == null ? Double.NaN : ${px[s]}; }`);
  for (const b of recipe.blocks) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': {
        const src = sourceName(p.source), fnm = b.type.split('.')[1];
        if (!ap[src]) L.push(`    private double V_${b.id}(int s) throws JFException { return Double.NaN; } // TODO ${b.id}: JForex AppliedPrice has no OHLC/4; pick close, hl2 (MEDIAN_PRICE) or hlc3 (TYPICAL_PRICE).`);
        else L.push(`    private double V_${b.id}(int s) throws JFException { return indicators.${fnm}(instrument, period, side, IIndicators.AppliedPrice.${ap[src]}, ${p.length}, s); }`);
        break;
      }
      case 'indicator.atr': L.push(`    private double V_${b.id}(int s) throws JFException { return indicators.atr(instrument, period, side, ${p.length}, s); }`); break;
      case 'filter.session': {
        const ss = parseSession(p), tz = String(p.timezone || 'Etc/UTC').replace(/["\\\s]/g, '');
        L.push(`    // ${b.id}: session ${p.session || '0000-2359'} in ${tz}, read from the bar start time.`,
          `    private static final ZoneId TZ_${b.id} = ZoneId.of(${javaText(tz)});`,
          `    private boolean S_${b.id}(int s) throws JFException { IBar b = bar(s); if (b == null) return false; ZonedDateTime t = Instant.ofEpochMilli(b.getTime()).atZone(TZ_${b.id}); int m = t.getHour() * 60 + t.getMinute(); return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`    private boolean S_${b.id}(int s) throws JFException { return ${val(p.left, 's')} ${gt} ${val(p.right, 's')} && ${val(p.left, 's + 1')} ${le} ${val(p.right, 's + 1')}; }`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`    private boolean S_${b.id}(int s) throws JFException { return ${val(p.left, 's')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 's') : Number(p.value)}; }`);
        break;
      case 'signal.recent':
        L.push(`    private boolean S_${b.id}(int s) throws JFException { return ${orOf(p.bars, k => bool(p.signal, `s + ${k}`), ' || ')}; } // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before`);
        break;
      case 'signal.combine':
        L.push(`    private boolean S_${b.id}(int s) throws JFException { return ${(p.signals || []).map(x => bool(x, 's')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; }`);
        break;
      case 'visual.plot': case 'alert.condition': case 'visual.table':
        break;
      default:
        if (isBoolType(b.type)) L.push(`    private boolean S_${b.id}(int s) throws JFException { return false; } // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push(`    private double V_${b.id}(int s) throws JFException { return Double.NaN; } // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('}');
  return L.join('\n') + '\n';
}

function elText(s, max = 256) {
  return '"' + String(s ?? '').replace(/["\r\n{}]/g, ' ').trim().slice(0, max) + '"';
}

function elNote(s) {
  return String(s ?? '').replace(/[{}\r\n]/g, ' ').trim();
}

function renderEasyLanguage(recipe) {
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const px = { open: 'Open', high: 'High', low: 'Low', close: 'Close', hl2: '(High + Low) / 2', hlc3: '(High + Low + Close) / 3', ohlc4: '(Open + High + Low + Close) / 4' };
  const val = (ref, at = '') => isPrice(ref) ? (at ? `${px[ref].startsWith('(') ? px[ref].replace(/(Open|High|Low|Close)/g, `$1${at}`) : px[ref] + at}` : px[ref]) : (isBoolType(map.get(ref)?.type) ? `IFF(S_${ref}${at}, 1, 0)` : `V_${ref}${at}`);
  const bool = (ref) => isBoolType(map.get(ref)?.type) ? `S_${ref}` : `(${val(ref)} <> 0)`;
  const vars = [];
  for (const b of recipe.blocks) {
    if (b.type === 'visual.plot' || b.type === 'alert.condition') continue;
    vars.push(isBoolType(b.type) ? `bool S_${b.id}(false)` : `double V_${b.id}(0)`);
  }
  const L = [];
  L.push('{ ORIGINAL BSV STARTER — TradeStation EasyLanguage indicator.');
  L.push('  Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`  ${elNote(safeTitle(recipe))}: in the TradeStation Development Environment create a new Indicator, paste this code and Verify.`);
  L.push(`  ${recipe.overlay ? 'Overlay recipe: keep the indicator on the price subgraph (Properties > Scaling: Same as symbol).' : 'Separate-pane recipe: plot it in a subgraph below the price.'}`);
  L.push('  Indicator only: it plots and raises alerts on closed bars and places no orders. }');
  L.push('');
  if (vars.length) L.push(`Vars: ${vars.join(', ')};`, '');
  for (const b of depOrder(recipe)) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': L.push(`V_${b.id} = XAverage(${px[sourceName(p.source)]}, ${p.length});`); break;
      case 'indicator.sma': L.push(`V_${b.id} = Average(${px[sourceName(p.source)]}, ${p.length});`); break;
      case 'indicator.rsi': L.push(`V_${b.id} = RSI(${px[sourceName(p.source)]}, ${p.length});`); break;
      case 'indicator.atr': L.push(`V_${b.id} = AvgTrueRange(${p.length});`); break;
      case 'filter.session': {
        const ss = parseSession(p), hm = m => String(Math.floor(m / 60) * 100 + (m % 60));
        L.push(`{ TODO ${b.id}: Time is the bar close time (HHMM) in the chart time zone; convert session ${elNote(p.session || '0000-2359')} from ${elNote(p.timezone || 'Etc/UTC')} if they differ. }`);
        L.push(`S_${b.id} = ${ss.start <= ss.end ? `Time > ${hm(ss.start)} and Time <= ${hm(ss.end)}` : `Time > ${hm(ss.start)} or Time <= ${hm(ss.end)}`};`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`S_${b.id} = ${val(p.left)} ${gt} ${val(p.right)} and ${val(p.left, '[1]')} ${le} ${val(p.right, '[1]')};`);
        break;
      }
      case 'signal.threshold': {
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        const op = { '==': '=', '!=': '<>' }[thresholdOp(p)] || thresholdOp(p);
        L.push(`S_${b.id} = ${val(p.left)} ${op} ${p.right !== undefined ? val(p.right) : Number(p.value)};`);
        break;
      }
      case 'signal.recent':
        L.push(`S_${b.id} = ${orOf(p.bars, k => `S_${p.signal}[${k}]`, ' or ')};`);
        break;
      case 'signal.combine':
        L.push(`S_${b.id} = ${(p.signals || []).map(x => bool(x)).join(p.mode === 'any' ? ' or ' : ' and ') || 'false'};`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        L.push(`{ TODO unsupported block ${b.type}: ${b.id} }`);
        L.push(isBoolType(b.type) ? `S_${b.id} = false;` : `V_${b.id} = 0;`);
    }
  }
  if (plots.length) L.push('');
  plots.slice(0, 99).forEach((p, k) => L.push(`Plot${k + 1}(${val(p.params?.source)}, ${elText(p.params?.title || p.params?.source || p.id, 60)});`));
  if (alerts.length) {
    L.push('', '{ Alerts: enable them in the indicator Properties (Alerts tab). TradeStation only raises alerts on the last bar; BarStatus(1) = 2 limits them to the closing tick. }');
    for (const a of alerts) L.push(`if BarStatus(1) = 2 and ${bool(a.params?.when)} then`, `    Alert(${elText(a.params?.message || a.id)});`);
  }
  L.push('');
  L.push('{ End BSV generated starter. }');
  return L.join('\n') + '\n';
}

function csText(s, max = 200) {
  return '"' + String(s ?? '').replace(/["\\\r\n]/g, ' ').trim().slice(0, max) + '"';
}

function renderAtas(recipe) {
  const map = blockMap(recipe);
  const cls = 'Bsv' + className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const px = { open: 'c.Open', high: 'c.High', low: 'c.Low', close: 'c.Close', hl2: '(c.High + c.Low) / 2m', hlc3: '(c.High + c.Low + c.Close) / 3m', ohlc4: '(c.Open + c.High + c.Low + c.Close) / 4m' };
  const val = (ref, at) => isPrice(ref) ? `P_${ref}(${at})` : (isBoolType(map.get(ref)?.type) ? `(S_${ref}[${at}] ? 1.0 : 0.0)` : `V_${ref}[${at}]`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}[${at}]` : `(${val(ref, at)} != 0.0 && !double.IsNaN(${val(ref, at)}))`;
  const usedPrices = new Set(['close']);
  for (const b of recipe.blocks) { const p = b.params || {}; [p.left, p.right, p.source].forEach(r => { if (isPrice(r)) usedPrices.add(r); }); }
  const L = [];
  L.push('// ORIGINAL BSV STARTER — ATAS custom indicator (C#, ATAS.Indicators API). Build it with the ATAS indicator SDK before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// Build ${cls}.cs into a class library that references ATAS.Indicators, copy the dll to the ATAS Indicators folder and add it to a chart.`);
  L.push('// Indicator only: it draws lines and raises alerts on closed bars. It places no orders.');
  L.push('using System;');
  L.push('using System.Collections.Generic;');
  L.push('using ATAS.Indicators;');
  L.push('');
  L.push('namespace BotShelfVampire.Generated');
  L.push('{');
  L.push(`    public class ${cls} : Indicator`);
  L.push('    {');
  plots.forEach((p, k) => L.push(k === 0 ? '        private readonly ValueDataSeries _plot0;' : `        private readonly ValueDataSeries _plot${k} = new ValueDataSeries("plot${k}", ${csText(p.params?.title || p.params?.source || p.id, 60)});`));
  for (const b of recipe.blocks) {
    if (b.type === 'visual.plot' || b.type === 'alert.condition') continue;
    L.push(isBoolType(b.type) ? `        private readonly List<bool> S_${b.id} = new List<bool>();` : `        private readonly List<double> V_${b.id} = new List<double>();`);
    if (b.type === 'indicator.rsi') L.push(`        private readonly List<double> GI_${b.id} = new List<double>(), DI_${b.id} = new List<double>(), G_${b.id} = new List<double>(), D_${b.id} = new List<double>();`);
    if (b.type === 'indicator.atr') L.push(`        private readonly List<double> TI_${b.id} = new List<double>();`);
  }
  if (alerts.length) {
    L.push('        private int _alertBar = -1;');
    L.push('        private bool _seenLast;');
    L.push('');
    L.push('        // Sound file name for AddAlert; use one that exists in your ATAS alert settings.');
    L.push('        public string AlertFile { get; set; } = "alert1";');
  }
  L.push('');
  L.push(`        public ${cls}() : base(true)`);
  L.push('        {');
  if (!recipe.overlay) L.push('            Panel = IndicatorDataProvider.NewPanel;');
  if (plots.length) L.push('            _plot0 = (ValueDataSeries)DataSeries[0];', `            _plot0.Name = ${csText(plots[0].params?.title || plots[0].params?.source || plots[0].id, 60)};`);
  plots.slice(1).forEach((_, k) => L.push(`            DataSeries.Add(_plot${k + 1});`));
  L.push('        }');
  L.push('');
  L.push('        protected override void OnCalculate(int bar, decimal value)');
  L.push('        {');
  L.push('            // Called for every history bar, then on every tick of the last bar; values for `bar` are recomputed each time.');
  for (const b of depOrder(recipe)) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.sma': L.push(`            Put(V_${b.id}, bar, Sma(i => P_${sourceName(p.source)}(i), bar, ${p.length}));`); usedPrices.add(sourceName(p.source)); break;
      case 'indicator.ema': L.push(`            Put(V_${b.id}, bar, bar < ${p.length} - 1 ? double.NaN : (bar == ${p.length} - 1 || double.IsNaN(V_${b.id}[bar - 1]) ? Sma(i => P_${sourceName(p.source)}(i), bar, ${p.length}) : V_${b.id}[bar - 1] + 2.0 / (${p.length} + 1) * (P_${sourceName(p.source)}(bar) - V_${b.id}[bar - 1])));`); usedPrices.add(sourceName(p.source)); break;
      case 'indicator.rsi': {
        const s = sourceName(p.source), n = p.length; usedPrices.add(s);
        L.push(`            { double ch = bar < 1 ? 0.0 : P_${s}(bar) - P_${s}(bar - 1); Rma(G_${b.id}, GI_${b.id}, bar, Math.Max(ch, 0.0), ${n}, 1); Rma(D_${b.id}, DI_${b.id}, bar, Math.Max(-ch, 0.0), ${n}, 1);`,
          `              double g = G_${b.id}[bar], d = D_${b.id}[bar]; Put(V_${b.id}, bar, double.IsNaN(g) || double.IsNaN(d) ? double.NaN : (d == 0.0 ? 100.0 : 100.0 - 100.0 / (1.0 + g / d))); }`);
        break;
      }
      case 'indicator.atr':
        L.push(`            { var c = GetCandle(bar); double tr = bar < 1 ? (double)(c.High - c.Low) : Math.Max((double)(c.High - c.Low), Math.Max(Math.Abs((double)c.High - P_close(bar - 1)), Math.Abs((double)c.Low - P_close(bar - 1)))); Rma(V_${b.id}, TI_${b.id}, bar, tr, ${p.length}, 0); }`);
        break;
      case 'filter.session': {
        const ss = parseSession(p), tz = String(p.timezone || 'Etc/UTC').replace(/["\\\s]/g, '');
        L.push(`            // TODO ${b.id}: treats the candle open time as UTC and converts it to ${tz}; check the time basis of your ATAS data.`,
          `            { var t = TimeZoneInfo.ConvertTimeFromUtc(DateTime.SpecifyKind(GetCandle(bar).Time, DateTimeKind.Utc), TZ_${b.id}); int m = t.Hour * 60 + t.Minute; Put(S_${b.id}, bar, ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}); }`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`            Put(S_${b.id}, bar, bar >= 1 && ${val(p.left, 'bar')} ${gt} ${val(p.right, 'bar')} && ${val(p.left, 'bar - 1')} ${le} ${val(p.right, 'bar - 1')});`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`            Put(S_${b.id}, bar, ${val(p.left, 'bar')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'bar') : Number(p.value)});`);
        break;
      case 'signal.recent':
        L.push(`            Put(S_${b.id}, bar, ${orOf(p.bars, k => `(bar >= ${k} && ${bool(p.signal, `bar - ${k}`)})`, ' || ')});`);
        break;
      case 'signal.combine':
        L.push(`            Put(S_${b.id}, bar, ${(p.signals || []).map(x => bool(x, 'bar')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'});`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        L.push(`            // TODO unsupported block ${b.type}: ${b.id}`);
        L.push(isBoolType(b.type) ? `            Put(S_${b.id}, bar, false);` : `            Put(V_${b.id}, bar, double.NaN);`);
    }
  }
  plots.forEach((p, k) => L.push(`            { double v = ${val(p.params?.source, 'bar')}; if (!double.IsNaN(v) && !double.IsInfinity(v)) _plot${k}[bar] = (decimal)v; }`));
  if (alerts.length) {
    L.push('            // Alerts once per closed bar, only for bars that close after the indicator was loaded.');
    L.push('            if (bar != CurrentBar - 1 || bar < 1)');
    L.push('                return;');
    L.push('            if (!_seenLast) { _seenLast = true; _alertBar = bar - 1; return; }');
    L.push('            if (bar - 1 <= _alertBar)');
    L.push('                return;');
    L.push('            _alertBar = bar - 1;');
    for (const a of alerts) L.push(`            if (${bool(a.params?.when, 'bar - 1')})`, `                AddAlert(AlertFile, ${csText(a.params?.message || a.id)});`);
  }
  L.push('        }');
  L.push('');
  for (const s of usedPrices) L.push(`        private double P_${s}(int i) { var c = GetCandle(i); return (double)(${px[s]}); }`);
  for (const b of recipe.blocks) if (b.type === 'filter.session') L.push(`        private static readonly TimeZoneInfo TZ_${b.id} = TimeZoneInfo.FindSystemTimeZoneById(${csText(String(b.params?.timezone || 'Etc/UTC').replace(/["\\\s]/g, ''))});`);
  L.push('        private static void Put(List<double> l, int bar, double v) { while (l.Count <= bar) l.Add(double.NaN); l[bar] = v; }');
  L.push('        private static void Put(List<bool> l, int bar, bool v) { while (l.Count <= bar) l.Add(false); l[bar] = v; }');
  L.push('        private static double Sma(Func<int, double> src, int bar, int n) { if (bar < n - 1) return double.NaN; double s = 0.0; for (int i = bar - n + 1; i <= bar; i++) s += src(i); return s / n; }');
  L.push('        // Wilder smoothing seeded with the simple mean of the first n inputs (inputs start at bar `first`).');
  L.push('        private static void Rma(List<double> o, List<double> inp, int bar, double x, int n, int first) { Put(inp, bar, x); if (bar < first + n - 1) { Put(o, bar, double.NaN); return; } if (bar == first + n - 1) { double s = 0.0; for (int i = first; i <= bar; i++) s += inp[i]; Put(o, bar, s / n); return; } Put(o, bar, (o[bar - 1] * (n - 1) + x) / n); }');
  L.push('    }');
  L.push('}');
  return L.join('\n') + '\n';
}

function signalDown(map, ref, seen = new Set()) {
  // true when the signal is (or combines) a downward cross: draw its marker above the bar.
  const b = map.get(ref);
  if (!b || seen.has(ref)) return false;
  seen.add(ref);
  if (b.type === 'signal.cross') return b.params?.direction === 'below';
  if (b.type === 'signal.combine') return (b.params?.signals || []).some(x => signalDown(map, x, seen));
  return false;
}

function aflText(s, max = 200) {
  return '"' + String(s ?? '').replace(/["\\\r\n]/g, ' ').trim().slice(0, max) + '"';
}

function aflNote(s) {
  return String(s ?? '').replace(/[\r\n]/g, ' ').replace(/\*\//g, '* /').trim();
}

function renderAmiBroker(recipe) {
  // AmiBroker Formula Language (AFL), checked against the AFL function reference on amibroker.com/guide.
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const px = { open: 'Open', high: 'High', low: 'Low', close: 'Close', hl2: '(High + Low) / 2', hlc3: '(High + Low + Close) / 3', ohlc4: '(Open + High + Low + Close) / 4' };
  const val = (ref) => isPrice(ref) ? px[ref] : (isBoolType(map.get(ref)?.type) ? `S_${ref}` : `V_${String(ref).replace('.', '_')}`); // range fields <id>.high -> V_<id>_high
  const prev = (ref) => `Ref(${val(ref)}, -1)`;
  const bool = (ref) => isBoolType(map.get(ref)?.type) ? `S_${ref}` : `(${val(ref)} != 0)`;
  const htfOk = (list) => list.filter(r => htfTfOf(recipe, map.get(r))).map(r => `NOT IsNull(${val(r)}) AND `).join('');
  const htfInds = recipe.blocks.filter(b => htfTfOf(recipe, b));
  const colors = ['colorBlue', 'colorRed', 'colorGreen', 'colorOrange', 'colorViolet', 'colorTeal', 'colorBrown', 'colorGrey50'];
  const L = [];
  L.push('// ORIGINAL BSV STARTER — AmiBroker Formula Language (AFL) indicator.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// ${aflNote(safeTitle(recipe))}: choose Analysis > Formula Editor, paste this code and press Apply indicator (Tools > Apply indicator); fix any line the editor reports.`);
  L.push(`// ${recipe.overlay ? 'Overlay recipe: drag the formula from the Charts list onto the price pane to overlay it.' : 'Separate-pane recipe: keep it in its own pane below the price.'}`);
  L.push('// Indicator only: it plots and raises alerts on completed bars. No Buy/Sell/Short/Cover arrays, no orders.');
  L.push('');
  const ivs = [...new Set(htfInds.map(b => htfTfOf(recipe, b)))];
  if (ivs.length) {
    L.push('// Higher timeframe, last CLOSED bar only (AFL guide "Multiple Time Frame Support", https://www.amibroker.com/guide/h_timeframe.html):',
      '// compute in the higher time frame, take Ref(x, -1) there (the previous, completed higher bar), then TimeFrameExpand with',
      '// expandFirst. This is the guide\'s TimeFrameGetPrice construction with a negative shift, which the guide says to use for',
      '// trading rules (shift 0 can look into the future). Values are Null unless the chart interval is shorter. Higher bars follow',
      '// your database time stamps/session settings. Not run in AmiBroker by BSV (UNTESTED_RUNTIME).');
    for (const iv of ivs) {
      L.push(`TimeFrameSet(${iv});`);
      for (const b of htfInds.filter(x => htfTfOf(recipe, x) === iv)) {
        const p = b.params || {}, src = px[sourceName(p.source)];
        const f = { 'indicator.ema': `EMA(${src}, ${p.length})`, 'indicator.sma': `MA(${src}, ${p.length})`, 'indicator.rsi': `RSIa(${src}, ${p.length})`, 'indicator.atr': `ATR(${p.length})` }[b.type];
        L.push(`H_${b.id} = Ref(${f}, -1);`);
      }
      L.push('TimeFrameRestore();');
      for (const b of htfInds.filter(x => htfTfOf(recipe, x) === iv)) L.push(`V_${b.id} = IIf(Interval() < ${iv === 'inDaily' ? 86400 : iv}, TimeFrameExpand(H_${b.id}, ${iv}, expandFirst), Null);`);
    }
    L.push('');
  }
  for (const b of depOrder(recipe)) {
    const p = b.params || {};
    if (htfTfOf(recipe, b)) continue;
    if (htfDataUsed(recipe, b)) { L.push(`// ${b.id}: higher timeframe ${aflNote(String(b.params.timeframe))} (TimeFrameSet + Ref(x, -1) + TimeFrameExpand expandFirst above, closed bars only)`); continue; }
    switch (b.type) {
      case 'indicator.ema': L.push(`V_${b.id} = EMA(${px[sourceName(p.source)]}, ${p.length});`); break;
      case 'indicator.sma': L.push(`V_${b.id} = MA(${px[sourceName(p.source)]}, ${p.length});`); break;
      case 'indicator.rsi': L.push(`V_${b.id} = RSIa(${px[sourceName(p.source)]}, ${p.length});`); break;
      case 'indicator.atr': L.push(`V_${b.id} = ATR(${p.length});`); break;
      case 'filter.session': {
        const ss = parseSession(p), hms = m => String((Math.floor(m / 60) * 100 + (m % 60)) * 100);
        L.push(`// TODO ${b.id}: TimeNum() is the bar time stamp (HHMMSS) in the database time zone, start or end of the interval as set in your intraday preferences; convert session ${aflNote(p.session || '0000-2359')} from ${aflNote(p.timezone || 'Etc/UTC')} if they differ.`);
        L.push(`S_${b.id} = ${ss.start <= ss.end ? `TimeNum() >= ${hms(ss.start)} AND TimeNum() < ${hms(ss.end)}` : `TimeNum() >= ${hms(ss.start)} OR TimeNum() < ${hms(ss.end)}`};`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`S_${b.id} = ${htfOk([p.left, p.right])}${htfOk([p.left, p.right]).replace(/IsNull\((\w+)\)/g, 'IsNull(Ref($1, -1))')}${val(p.left)} ${gt} ${val(p.right)} AND ${prev(p.left)} ${le} ${prev(p.right)};`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`S_${b.id} = ${htfOk([p.left, p.right].filter(x => typeof x === 'string'))}${val(p.left)} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right) : Number(p.value)};`);
        break;
      case 'signal.recent':
        L.push(`S_${b.id} = ${orOf(p.bars, k => `Nz(Ref(${bool(p.signal)}, -${k}))`, ' OR ')}; // ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before (Nz: Null before the first bar = false)`);
        break;
      case 'signal.combine':
        L.push(`S_${b.id} = ${(p.signals || []).map(x => bool(x)).join(p.mode === 'any' ? ' OR ' : ' AND ') || 'False'};`);
        break;
      case 'visual.plot': case 'alert.condition': case 'visual.table':
        break;
      case 'structure.range': {
        if (!rangeOk(recipe, b)) { L.push(`// TODO unsupported block ${b.type}: ${b.id}`, `V_${b.id} = Null;`); break; }
        L.push(`// ${b.id}: high / low so far inside the window (a new window resets), then the finished window held; Null before the first window (AFL guide: HighestSince, LowestSince, ValueWhen)`,
          `R_${b.id} = ${bool(p.during)};`, `W_${b.id} = R_${b.id} AND (BarIndex() == 0 OR Ref(R_${b.id}, -1) == 0);`);
        for (const k of rangeKeys(b)) L.push(`V_${b.id}_${k} = ValueWhen(R_${b.id}, ${k === 'high' ? 'HighestSince' : 'LowestSince'}(W_${b.id}, ${k === 'high' ? 'High' : 'Low'}));`);
        break;
      }
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { L.push(`// TODO unsupported block ${b.type}: ${b.id}`, `V_${b.id} = Null;`); break; }
        const [xh, xl] = (p.source || 'close') === 'high_low' ? ['High', 'Low'] : ['Close', 'Close'], R = p.right, Lf = p.left;
        L.push(`// ${b.id}: the bar ${R} bars ago is a pivot high if it is above the ${Lf} bars before it and at least as high as the ${R} after it (a flat top counts once); known only now, so no lookahead. The last confirmed pivot is held (Null before the first).`,
          `P_${b.id}_h = Ref(${xh}, -${R}) > Ref(HHV(${xh}, ${Lf}), -${R + 1}) AND Ref(${xh}, -${R}) >= HHV(${xh}, ${R});`,
          `P_${b.id}_l = Ref(${xl}, -${R}) < Ref(LLV(${xl}, ${Lf}), -${R + 1}) AND Ref(${xl}, -${R}) <= LLV(${xl}, ${R});`,
          `V_${b.id}_high = ValueWhen(P_${b.id}_h, Ref(${xh}, -${R}));`, `V_${b.id}_low = ValueWhen(P_${b.id}_l, Ref(${xl}, -${R}));`);
        break;
      }
      case 'signal.liquidity_sweep': {
        if (!sweepOk(recipe, b)) { L.push(`// TODO unsupported block ${b.type}: ${b.id}`, `S_${b.id} = False;`); break; }
        const v = p.pivot, a = val(p.atr), m = `${Number(p.minAtrFraction || 0)} * ${a}`, ph = `Ref(V_${v}_high, -1)`, pl = `Ref(V_${v}_low, -1)`;
        L.push(`// ${b.id}: sweep candidate: the wick goes beyond the last pivot known before this bar by at least ${Number(p.minAtrFraction || 0)} x ATR and the close is back inside`,
          `S_${b.id} = NOT IsNull(${a}) AND ((NOT IsNull(${ph}) AND High > ${ph} AND High - ${ph} >= ${m} AND Close < ${ph}) OR (NOT IsNull(${pl}) AND Low < ${pl} AND ${pl} - Low >= ${m} AND Close > ${pl}));`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { L.push(`// TODO unsupported block ${b.type}: ${b.id}`, `S_${b.id} = False;`); break; }
        const pb = map.get(p.pivot), pq = pb.params, R = pq.right, [xh, xl] = (pq.source || 'close') === 'high_low' ? ['High', 'Low'] : ['Close', 'Close'], o = val(p.oscillator), d = p.direction || 'both', v = pb.id;
        L.push(`// ${b.id}: regular divergence, true on the bar that confirms the new pivot; ValueWhen(..., 2) = the pivot before it`,
          `B_${b.id} = P_${v}_h AND Ref(${xh}, -${R}) > ValueWhen(P_${v}_h, Ref(${xh}, -${R}), 2) AND Ref(${o}, -${R}) < ValueWhen(P_${v}_h, Ref(${o}, -${R}), 2);`,
          `U_${b.id} = P_${v}_l AND Ref(${xl}, -${R}) < ValueWhen(P_${v}_l, Ref(${xl}, -${R}), 2) AND Ref(${o}, -${R}) > ValueWhen(P_${v}_l, Ref(${o}, -${R}), 2);`,
          `S_${b.id} = ${d === 'both' ? `B_${b.id} OR U_${b.id}` : d === 'bearish' ? `B_${b.id}` : `U_${b.id}`};`);
        break;
      }
      case 'visual.zone':
        if (!zoneOk(recipe, b)) { L.push(`// TODO unsupported block ${b.type}: ${b.id}`, `V_${b.id} = Null;`); break; }
        L.push(`// ${b.id}: zone drawn as two lines from ${p.source} (${map.get(p.source).type === 'structure.range' ? 'the window high / low' : 'last confirmed pivot high / low'}), see the Plot lines below`);
        break;
      case 'signal.breakout': {
        if (!breakoutOk(recipe, b)) { L.push(`// TODO unsupported block ${b.type}: ${b.id}`, `S_${b.id} = False;`); break; }
        const r = p.range, d = p.direction || 'either', ok = `R_${r} == 0 AND NOT IsNull(V_${r}_high)`;
        L.push(`// ${b.id}: first close beyond the finished window, on a bar outside it (the close before was at or inside)`,
          `U_${b.id} = ${ok} AND Close > V_${r}_high AND Ref(Close, -1) <= V_${r}_high;`, `D_${b.id} = ${ok} AND Close < V_${r}_low AND Ref(Close, -1) >= V_${r}_low;`,
          `S_${b.id} = ${d === 'either' ? `U_${b.id} OR D_${b.id}` : d === 'above' ? `U_${b.id}` : `D_${b.id}`};`);
        break;
      }
      default:
        L.push(`// TODO unsupported block ${b.type}: ${b.id}`);
        L.push(isBoolType(b.type) ? `S_${b.id} = False;` : `V_${b.id} = Null;`);
    }
  }
  if (plots.length) L.push('');
  plots.forEach((p, k) => L.push(`Plot(${val(p.params?.source)}, ${aflText(p.params?.title || p.params?.source || p.id, 60)}, ${colors[k % colors.length]}, styleLine);`));
  const zones = recipe.blocks.filter(b => zoneOk(recipe, b));
  if (zones.length) L.push('');
  zones.forEach(z => { const t = String(z.params?.title || z.id).slice(0, 50); L.push(`Plot(V_${z.params.source}_high, ${aflText(t + ' high', 60)}, colorRed, styleLine);`, `Plot(V_${z.params.source}_low, ${aflText(t + ' low', 60)}, colorGreen, styleLine);`); });
  for (const t of tableBlocks(recipe)) {
    L.push('');
    tableTodos(t, '//').forEach(x => L.push(x));
    if (!t.fields.length) continue;
    L.push(`// Value panel ${t.title.replace(/[\r\n]/g, ' ')} (visual.table): printf writes to the Interpretation window. The last bar may still be forming,`,
      '// so LastValue(Ref(x, -1)) shows the most recent completed bar. NumToStr format 1.6 = 6 decimals, no thousands separator.');
    L.push(`printf(${aflText(t.title, 80)} + "\\n");`);
    t.fields.forEach(x => { const n = String(x.id).replace(/[^A-Za-z0-9_]/g, '_'); L.push(x.bool ? `printf("${n}: " + WriteIf(LastValue(Ref(${val(x.id)}, -1)), "true", "false") + "\\n");` : `printf("${n}: " + NumToStr(LastValue(Ref(${val(x.id)}, -1)), 1.6, False) + "\\n");`); });
  }
  if (alerts.length) {
    L.push('', '// Alerts go to the Alert Output window. Completed bars only (AFL guide, "Using formula-based alerts"):',
      '// the last bar is still forming, so lookback = 2 checks the most recent completed bar; flags 1+2+4+8 = text, beep, no repeats.',
      'bsvBarComplete = BarIndex() < LastValue(BarIndex());');
    for (const a of alerts) L.push(`AlertIf(bsvBarComplete AND ${bool(a.params?.when)}, "", ${aflText(a.params?.message || a.id)}, 0, 1 + 2 + 4 + 8, 2);`);
  }
  L.push('');
  L.push('// End BSV generated starter.');
  return L.join('\n') + '\n';
}

function tsText(s, max = 200) {
  return '"' + String(s ?? '').replace(/["\\\r\n]/g, ' ').trim().slice(0, max) + '"';
}

function tsNote(s) {
  return String(s ?? '').replace(/[\r\n]/g, ' ').trim();
}

function renderThinkScript(recipe) {
  // thinkorswim thinkScript study, checked against the thinkScript reference on tlc.thinkorswim.com.
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const px = { open: ['open'], high: ['high'], low: ['low'], close: ['close'], hl2: ['high', 'low'], hlc3: ['high', 'low', 'close'], ohlc4: ['open', 'high', 'low', 'close'] };
  const price = (ref, at = '') => { const k = px[ref]; return k.length === 1 ? k[0] + at : `((${k.map(x => x + at).join(' + ')}) / ${k.length})`; };
  const val = (ref, at = '') => isPrice(ref) ? price(ref, at) : (isBoolType(map.get(ref)?.type) ? `S_${ref}${at}` : `V_${String(ref).replace('.', '_')}${at}`); // range / pivot fields <id>.high -> V_<id>_high
  const bool = (ref, at = '') => isBoolType(map.get(ref)?.type) ? `S_${ref}${at}` : `(${val(ref, at)} != 0)`;
  const colors = ['CYAN', 'MAGENTA', 'YELLOW', 'ORANGE', 'GREEN', 'RED', 'PINK', 'LIGHT_GRAY'];
  const hhmm = m => String(Math.floor(m / 60) * 100 + (m % 60)).padStart(4, '0');
  const L = [];
  L.push('# ORIGINAL BSV STARTER — thinkorswim thinkScript study.');
  L.push('# Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`# ${tsNote(safeTitle(recipe))}: on the Charts tab click Studies > Edit studies… > Create…, paste this code into the thinkScript Editor, name the study and save it; fix any line the editor marks. You can also import a saved .ts file (Edit studies… > Import…).`);
  L.push(`# ${recipe.overlay ? 'Overlay recipe: the study draws on the price chart.' : 'Separate-pane recipe: declare lower puts it on a lower subgraph.'}`);
  L.push('# Study only: it plots and raises alerts for closed bars. No AddOrder, no orders.');
  L.push('');
  if (!recipe.overlay) L.push('declare lower;', '');
  const aggs = [...new Set(recipe.blocks.map(b => htfTfOf(recipe, b)).filter(Boolean))];
  if (aggs.length) {
    L.push('# Higher timeframe, last CLOSED bar only (thinkScript manual, "Referencing Secondary Aggregation",',
      '# https://toslc.thinkorswim.com/center/reference/thinkScript/tutorials/Advanced/Chapter-11---Referencing-Secondary-Aggregation):',
      '# values come from close(period = AggregationPeriod.X) etc.; expressions that use only those variables and constants keep the',
      '# secondary aggregation, so H_x = E_x[1] is the previous secondary bar (as High(period = AggregationPeriod.DAY)[1] is the',
      '# previous day in the manual). Never mixed with chart-period prices. Empty unless the chart aggregation is shorter (time charts).',
      '# Not run in thinkorswim by BSV (UNTESTED_RUNTIME).');
    for (const g of aggs) L.push(`def bsvHtfOk_${g} = GetAggregationPeriod() < AggregationPeriod.${g};`);
  }
  const hp = (g, ref, at = '') => { const k = px[ref]; const one = x => `${x}(period = AggregationPeriod.${g})`; return k.length === 1 ? one(k[0]) : `((${k.map(one).join(' + ')}) / ${k.length})`; };
  for (const b of depOrder(recipe)) {
    const p = b.params || {};
    const g = htfTfOf(recipe, b);
    if (g) {
      const src = sourceName(p.source);
      if (b.type === 'indicator.atr') L.push(`def E_${b.id} = WildersAverage(TrueRange(high(period = AggregationPeriod.${g}), close(period = AggregationPeriod.${g}), low(period = AggregationPeriod.${g})), ${p.length});`);
      else {
        L.push(`def C_${b.id} = ${hp(g, src)};`);
        if (b.type === 'indicator.ema') L.push(`def E_${b.id} = ExpAverage(C_${b.id}, ${p.length});`);
        if (b.type === 'indicator.sma') L.push(`def E_${b.id} = Average(C_${b.id}, ${p.length});`);
        if (b.type === 'indicator.rsi') L.push(`def U_${b.id} = WildersAverage(Max(C_${b.id} - C_${b.id}[1], 0), ${p.length});`, `def D_${b.id} = WildersAverage(Max(C_${b.id}[1] - C_${b.id}, 0), ${p.length});`,
          `def E_${b.id} = if U_${b.id} + D_${b.id} == 0 then 50 else 100 * U_${b.id} / (U_${b.id} + D_${b.id});`);
      }
      L.push(`def H_${b.id} = E_${b.id}[1]; # previous (closed) ${g} bar`, `def V_${b.id} = if bsvHtfOk_${g} then H_${b.id} else Double.NaN;`);
      continue;
    }
    if (htfDataUsed(recipe, b)) { L.push(`# ${b.id}: higher timeframe ${tsNote(String(b.params.timeframe))} (secondary aggregation above, closed bars only)`); continue; }
    switch (b.type) {
      case 'indicator.ema': L.push(`def V_${b.id} = ExpAverage(${price(sourceName(p.source))}, ${p.length});`); break;
      case 'indicator.sma': L.push(`def V_${b.id} = Average(${price(sourceName(p.source))}, ${p.length});`); break;
      case 'indicator.rsi': {
        const src = sourceName(p.source);
        L.push(`def U_${b.id} = WildersAverage(Max(${price(src)} - ${price(src, '[1]')}, 0), ${p.length});`,
          `def D_${b.id} = WildersAverage(Max(${price(src, '[1]')} - ${price(src)}, 0), ${p.length});`,
          `def V_${b.id} = if U_${b.id} + D_${b.id} == 0 then 50 else 100 * U_${b.id} / (U_${b.id} + D_${b.id});`);
        break;
      }
      case 'indicator.atr': L.push(`def V_${b.id} = WildersAverage(TrueRange(high, close, low), ${p.length});`); break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push(`# TODO ${b.id}: SecondsFromTime/SecondsTillTime count in the EST (US Eastern) time zone; convert session ${tsNote(p.session || '0000-2359')} from ${tsNote(p.timezone || 'Etc/UTC')} if they differ. Intraday charts only.`);
        L.push(`def S_${b.id} = ${ss.start <= ss.end ? `SecondsFromTime(${hhmm(ss.start)}) >= 0 and SecondsTillTime(${hhmm(ss.end)}) > 0` : `SecondsFromTime(${hhmm(ss.start)}) >= 0 or SecondsTillTime(${hhmm(ss.end)}) > 0`};`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`def S_${b.id} = ${val(p.left)} ${gt} ${val(p.right)} and ${val(p.left, '[1]')} ${le} ${val(p.right, '[1]')};`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`def S_${b.id} = ${val(p.left)} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right) : Number(p.value)};`);
        break;
      case 'signal.recent':
        L.push(`def S_${b.id} = ${orOf(p.bars, k => bool(p.signal, `[${k}]`), ' or ')}; # ${p.signal} on ${p.bars === 1 ? 'the bar' : `one of the ${p.bars} bars`} before`);
        break;
      case 'signal.combine':
        L.push(`def S_${b.id} = ${(p.signals || []).map(x => bool(x)).join(p.mode === 'any' ? ' or ' : ' and ') || 'no'};`);
        break;
      case 'visual.plot': case 'alert.condition': case 'visual.table':
        break;
      case 'structure.range': {
        if (!rangeOk(recipe, b)) { L.push(`# TODO unsupported block ${b.type}: ${b.id}`, `def V_${b.id} = Double.NaN;`); break; }
        L.push(`# ${b.id}: high / low so far inside the window (a new window resets), then the finished window held; NaN before the first window.`,
          '# CompoundValue(1, x, y) is y on the first bar and x after it; V[1] is the value one bar back (thinkScript reference: CompoundValue, Referencing Historical Data).',
          `def R_${b.id} = ${bool(p.during)};`, `def W_${b.id} = CompoundValue(1, R_${b.id} and R_${b.id}[1] == 0, R_${b.id});`);
        for (const k of rangeKeys(b)) { const [x, f] = k === 'high' ? ['high', 'Max'] : ['low', 'Min'];
          L.push(`def V_${b.id}_${k} = CompoundValue(1, if W_${b.id} then ${x} else if R_${b.id} then ${f}(V_${b.id}_${k}[1], ${x}) else V_${b.id}_${k}[1], if R_${b.id} then ${x} else Double.NaN);`); }
        break;
      }
      case 'signal.breakout': {
        if (!breakoutOk(recipe, b)) { L.push(`# TODO unsupported block ${b.type}: ${b.id}`, `def S_${b.id} = no;`); break; }
        const r = p.range, d = p.direction || 'either', ok = `R_${r} == 0 and IsNaN(V_${r}_high) == 0`;
        L.push(`# ${b.id}: first close beyond the finished window, on a bar outside it (the close before was at or inside)`,
          `def U_${b.id} = ${ok} and close > V_${r}_high and close[1] <= V_${r}_high;`, `def D_${b.id} = ${ok} and close < V_${r}_low and close[1] >= V_${r}_low;`,
          `def S_${b.id} = ${d === 'either' ? `U_${b.id} or D_${b.id}` : d === 'above' ? `U_${b.id}` : `D_${b.id}`};`);
        break;
      }
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { L.push(`# TODO unsupported block ${b.type}: ${b.id}`, `def V_${b.id} = Double.NaN;`); break; }
        const [xh, xl] = (p.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], R = p.right, Lf = p.left;
        L.push(`# ${b.id}: the bar ${R} bars ago is a pivot high if it is above the ${Lf} bars before it and at least as high as the ${R} after it (a flat top counts once); known only now, so no lookahead. The last confirmed pivot is held (NaN before the first).`,
          `def P_${b.id}_h = ${xh}[${R}] > Highest(${xh}[${R + 1}], ${Lf}) and ${xh}[${R}] >= Highest(${xh}, ${R});`,
          `def P_${b.id}_l = ${xl}[${R}] < Lowest(${xl}[${R + 1}], ${Lf}) and ${xl}[${R}] <= Lowest(${xl}, ${R});`,
          `def V_${b.id}_high = CompoundValue(1, if P_${b.id}_h then ${xh}[${R}] else V_${b.id}_high[1], Double.NaN);`,
          `def V_${b.id}_low = CompoundValue(1, if P_${b.id}_l then ${xl}[${R}] else V_${b.id}_low[1], Double.NaN);`);
        break;
      }
      case 'signal.liquidity_sweep': {
        if (!sweepOk(recipe, b)) { L.push(`# TODO unsupported block ${b.type}: ${b.id}`, `def S_${b.id} = no;`); break; }
        const v = p.pivot, a = val(p.atr), m = `${Number(p.minAtrFraction || 0)} * ${a}`, ph = `V_${v}_high[1]`, pl = `V_${v}_low[1]`;
        L.push(`# ${b.id}: sweep candidate: the wick goes beyond the last pivot known before this bar by at least ${Number(p.minAtrFraction || 0)} x ATR and the close is back inside`,
          `def S_${b.id} = IsNaN(${a}) == 0 and ((IsNaN(${ph}) == 0 and high > ${ph} and high - ${ph} >= ${m} and close < ${ph}) or (IsNaN(${pl}) == 0 and low < ${pl} and ${pl} - low >= ${m} and close > ${pl}));`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { L.push(`# TODO unsupported block ${b.type}: ${b.id}`, `def S_${b.id} = no;`); break; }
        const pb = map.get(p.pivot), pq = pb.params, R = pq.right, [xh, xl] = (pq.source || 'close') === 'high_low' ? ['high', 'low'] : ['close', 'close'], oR = val(p.oscillator, `[${R}]`), d = p.direction || 'both', v = pb.id;
        L.push(`# ${b.id}: regular divergence, true on the bar that confirms the new pivot; V_${v}_high[1] is the pivot before it, O_ holds the oscillator at that pivot`,
          `def OH_${b.id} = CompoundValue(1, if P_${v}_h then ${oR} else OH_${b.id}[1], Double.NaN);`, `def OL_${b.id} = CompoundValue(1, if P_${v}_l then ${oR} else OL_${b.id}[1], Double.NaN);`,
          `def B_${b.id} = P_${v}_h and ${xh}[${R}] > V_${v}_high[1] and ${oR} < OH_${b.id}[1];`,
          `def U_${b.id} = P_${v}_l and ${xl}[${R}] < V_${v}_low[1] and ${oR} > OL_${b.id}[1];`,
          `def S_${b.id} = ${d === 'both' ? `B_${b.id} or U_${b.id}` : d === 'bearish' ? `B_${b.id}` : `U_${b.id}`};`);
        break;
      }
      case 'visual.zone':
        if (!zoneOk(recipe, b)) { L.push(`# TODO unsupported block ${b.type}: ${b.id}`, `def V_${b.id} = Double.NaN;`); break; }
        L.push(`# ${b.id}: zone drawn as two lines from ${p.source} (${map.get(p.source).type === 'structure.range' ? 'the window high / low' : 'last confirmed pivot high / low'}), see the plots below`);
        break;
      default:
        L.push(`# TODO unsupported block ${b.type}: ${b.id}`);
        L.push(isBoolType(b.type) ? `def S_${b.id} = no;` : `def V_${b.id} = Double.NaN;`);
    }
  }
  if (plots.length) L.push('');
  plots.forEach((p, k) => L.push(`plot P${k + 1} = ${val(p.params?.source)};`, `P${k + 1}.SetDefaultColor(Color.${colors[k % colors.length]});`));
  recipe.blocks.filter(b => zoneOk(recipe, b)).forEach((z, k) => L.push(`plot ZH${k + 1} = V_${z.params.source}_high; # ${tsNote(String(z.params?.title || z.id).slice(0, 50))} high`, `ZH${k + 1}.SetDefaultColor(Color.RED);`, `plot ZL${k + 1} = V_${z.params.source}_low; # ${tsNote(String(z.params?.title || z.id).slice(0, 50))} low`, `ZL${k + 1}.SetDefaultColor(Color.GREEN);`));
  for (const t of tableBlocks(recipe)) {
    L.push('');
    tableTodos(t, '#').forEach(x => L.push(x));
    if (!t.fields.length) continue;
    L.push(`# Value panel ${tsNote(t.title)} (visual.table): AddLabel uses the last real bar, which is still forming, so [1] shows the bar that just closed${tableBlocks(recipe).some(() => recipe.blocks.some(b => htfTfOf(recipe, b))) ? ' (higher-timeframe-only fields are already the previous closed higher bar and are shown as they are)' : ''}.`);
    L.push(`AddLabel(yes, ${tsText(t.title)}, Color.WHITE);`);
    // a field built only from higher-timeframe values is already a closed bar and stays in the secondary aggregation, where
    // [1] would mean one more higher bar back; so it is shown without the offset (never the forming chart bar either way)
    const onlyHtf = (id, seen = new Set()) => { const d = map.get(id); if (!d) return false; if (htfTfOf(recipe, d)) return true; if (seen.has(id)) return true; seen.add(id); const r = referencesFor(d); return r.length > 0 && r.every(x => onlyHtf(x, seen)); };
    const at = id => onlyHtf(id) ? '' : '[1]';
    t.fields.forEach(x => L.push(x.bool ? `AddLabel(yes, "${String(x.id).replace(/[^A-Za-z0-9_]/g, '_')}: " + (if ${val(x.id, at(x.id))} then "true" else "false"), Color.LIGHT_GRAY);` : `AddLabel(yes, "${String(x.id).replace(/[^A-Za-z0-9_]/g, '_')}: " + ${val(x.id, at(x.id))}, Color.LIGHT_GRAY);`));
  }
  if (alerts.length) {
    L.push('', '# Alerts: Alert() uses the value at the last real bar, which is still forming, so [1] checks the bar that just closed;',
      '# Alert.BAR raises it at most once per bar. Add the study to a chart for the alerts to run.');
    for (const a of alerts) L.push(`Alert(${bool(a.params?.when, '[1]')}, ${tsText(a.params?.message || a.id)}, Alert.BAR, Sound.Ding);`);
  }
  L.push('');
  L.push('# End BSV generated starter.');
  return L.join('\n') + '\n';
}

function jsText(s, max = 200) {
  return JSON.stringify(String(s ?? '').replace(/[\r\n\u2028\u2029]/g, ' ').trim().slice(0, max));
}

function renderTradovate(recipe) {
  // Tradovate custom indicator (JavaScript), following the published API at tradovate.github.io/custom-indicators
  // (module.exports { name, description, calculator, params, inputType, areaChoice, plots, plotter, shifts, schemeStyles };
  // Calculator.init / map(d, index); BarInputEntity open/high/low/close/timestamp). Self-contained math: only predef.plotters is required.
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const zones = recipe.blocks.filter(b => zoneOk(recipe, b)); // zones: two lines, the source's high and low (pivot or range)
  const hooks = recipe.blocks.filter(b => webhookOk(recipe, b)); // webhooks: W dots + the JSON payload built per bar (never sent)
  const tables = tableBlocks(recipe); // value panels: no panel call in the published API, so the values are kept in per-bar state
  const id = (x) => String(x).replace(/[^A-Za-z0-9_]/g, '_');
  const px = { open: 's.o', high: 's.h', low: 's.l', close: 's.c', hl2: '(s.h + s.l) / 2', hlc3: '(s.h + s.l + s.c) / 3', ohlc4: '(s.o + s.h + s.l + s.c) / 4' };
  const at = (expr, who) => who === 's' ? expr : expr.replace(/\bs\./g, who + '.');
  const val = (ref, who = 's') => isPrice(ref) ? at(px[ref], who) : (isBoolType(map.get(ref)?.type) ? `(${who}.S_${id(ref)} ? 1 : 0)` : `${who}.V_${id(ref)}`);
  const bool = (ref, who = 's') => isBoolType(map.get(ref)?.type) ? `${who}.S_${id(ref)}` : `(Number.isFinite(${val(ref, who)}) && ${val(ref, who)} !== 0)`;
  const colors = ['cyan', 'magenta', 'yellow', 'orange', 'lime', 'red', 'pink', 'lightgray'];
  const name = 'bsv' + className(recipe);
  const tzs = new Map();
  let usesPivot = false, usesHtf = false;
  const L = [];
  L.push('// ORIGINAL BSV STARTER — Tradovate custom indicator (JavaScript).');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// ${tsNote(safeTitle(recipe))}: in Tradovate Trader add the Code Explorer module (the + button), choose File > New, paste this code and save. Then open the chart's Indicators menu, find ${name.toUpperCase()} and add it.`);
  L.push(`// ${recipe.overlay ? 'Overlay recipe: the indicator draws on the price chart.' : 'Separate-pane recipe: areaChoice "new" puts it in a new area.'}`);
  L.push('// Indicator only: it plots values. It places no orders and makes no network calls.');
  if (alerts.length) L.push('// Alerts: the published custom-indicator API has no alert call, so each alert condition is drawn as dots on the bar that just closed (A1, A2, …). Set up notifications in Tradovate yourself if your version offers them.');
  if (tables.length) L.push('// Value panels: the published custom-indicator API has no panel or label call, so each panel is kept as values, not drawn: this.bars[i - 1].T_<id> holds the fields of the bar that just closed (true / false for signals, NaN while warming up).', ...tables.flatMap(t => tableTodos(t, '//')));
  if (hooks.length) L.push('// Webhooks: this indicator makes no network calls. Each webhook condition is drawn as dots on the bar that just closed (W1, W2, …), and its JSON payload for that bar is built in this.bars[i - 1].J_<id> with {{...}} filled in, for you to copy into your own Tradovate alert or automation. It is never sent. Never put secrets in a payload.');
  L.push('');
  L.push('const predef = require("./tools/predef");');
  if (hooks.length) L.push('const BSV_SYMBOL = "SYMBOL"; // set your symbol for {{symbol}}', 'const BSV_TIMEFRAME = "TIMEFRAME"; // set your bar timeframe for {{timeframe}}');
  L.push('');
  L.push('class bsvRecipe {');
  L.push('  init() {');
  L.push('    this.bars = []; // per-bar state by index: map() may run again for the forming bar, so each index is recomputed from the one before');
  const initAt = L.length;
  L.push('  }');
  L.push('');
  L.push('  map(d, i) {');
  L.push('    const p = i > 0 ? this.bars[i - 1] : undefined;');
  L.push('    const s = { o: d.open(), h: d.high(), l: d.low(), c: d.close() };');
  for (const b of depOrder(recipe)) {
    const q = b.params || {}, k = id(b.id);
    if (/^indicator\.(ema|sma|rsi|atr)$/.test(b.type) && htfTfOf(recipe, b)) {  // on closed higher-timeframe bars only
      const h = id(q.timeframeRef);
      L.push(`    s.H_${k} = s.hnew_${h} ? this.BsvHtf(p.H_${k}, "${b.type.slice(10)}", ${q.length}, p.hb_${h}, p.hlc_${h}, "${sourceName(q.source)}") : p ? p.H_${k} : null; // ${b.type} ${q.length} on the higher timeframe`,
        `    s.V_${k} = s.hbad_${h} || !s.H_${k} ? NaN : s.H_${k}.V; // value of the last closed higher-timeframe bar`);
      continue;
    }
    if (b.type === 'data.higher_timeframe' && htfDataUsed(recipe, b)) {
      const sec = htfMinutes(b) * 60e3;
      usesHtf = true;
      L.push(`    const tm_${k} = +d.timestamp(); // ${tsNote(q.timeframe)} higher timeframe: periods aligned to UTC, bar times read as bar-open times`,
        `    s.ht_${k} = tm_${k}; s.hs_${k} = !p ? null : p.hs_${k} === null ? tm_${k} - p.ht_${k} : Math.min(p.hs_${k}, tm_${k} - p.ht_${k}); // smallest chart-bar step`,
        `    s.hbad_${k} = !!p && (p.hbad_${k} || tm_${k} <= p.ht_${k} || s.hs_${k} >= ${sec}); // bar times must increase and chart bars must be shorter: otherwise no value (not computed on the chart timeframe)`,
        `    s.hk_${k} = Math.floor(tm_${k} / ${sec}); s.hnew_${k} = !!p && p.hk_${k} !== s.hk_${k}; // a new period: the previous one (p.hb_${k}) is now closed`,
        `    s.hb_${k} = p && !s.hnew_${k} ? { o: p.hb_${k}.o, h: Math.max(p.hb_${k}.h, s.h), l: Math.min(p.hb_${k}.l, s.l), c: s.c } : { o: s.o, h: s.h, l: s.l, c: s.c }; // forming higher-timeframe bar (never used until closed)`,
        `    s.hlc_${k} = s.hnew_${k} ? p.hb_${k}.c : p ? p.hlc_${k} : NaN; // close of the last closed higher-timeframe bar`);
      continue;
    }
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': {
        const n = q.length;
        L.push(`    s.x_${k} = ${px[sourceName(q.source)]};`, `    s.k_${k} = p ? p.k_${k} + 1 : 1;`, `    s.t_${k} = (p ? p.t_${k} : 0) + (s.k_${k} <= ${n} ? s.x_${k} : 0);`);
        if (b.type === 'indicator.ema') L.push(`    s.V_${k} = s.k_${k} < ${n} ? NaN : s.k_${k} === ${n} ? s.t_${k} / ${n} : p.V_${k} + ${2 / (n + 1)} * (s.x_${k} - p.V_${k}); // EMA ${n}, seeded with the SMA of the first ${n} bars`);
        else L.push(`    if (s.k_${k} >= ${n}) { let t = s.x_${k}; for (let j = i - ${n - 1}; j < i; j++) t += this.bars[j].x_${k}; s.V_${k} = t / ${n}; } else s.V_${k} = NaN; // SMA ${n}`);
        break;
      }
      case 'indicator.rsi': case 'indicator.atr': {
        const n = q.length;
        if (b.type === 'indicator.rsi') {
          L.push(`    s.x_${k} = ${px[sourceName(q.source)]};`,
            `    const u_${k} = p ? Math.max(s.x_${k} - p.x_${k}, 0) : 0, v_${k} = p ? Math.max(p.x_${k} - s.x_${k}, 0) : 0;`);
        } else {
          L.push(`    const u_${k} = p ? Math.max(s.h, p.c) - Math.min(s.l, p.c) : 0, v_${k} = 0; // true range`);
        }
        L.push(`    s.k_${k} = p ? p.k_${k} + 1 : 0; // changes counted from the second bar`,
          `    s.su_${k} = (p ? p.su_${k} : 0) + (s.k_${k} <= ${n} ? u_${k} : 0); s.sd_${k} = (p ? p.sd_${k} : 0) + (s.k_${k} <= ${n} ? v_${k} : 0);`,
          `    s.U_${k} = s.k_${k} < ${n} ? NaN : s.k_${k} === ${n} ? s.su_${k} / ${n} : (p.U_${k} * ${n - 1} + u_${k}) / ${n}; // Wilder average ${n}`,
          `    s.D_${k} = s.k_${k} < ${n} ? NaN : s.k_${k} === ${n} ? s.sd_${k} / ${n} : (p.D_${k} * ${n - 1} + v_${k}) / ${n};`);
        L.push(b.type === 'indicator.rsi' ? `    s.V_${k} = !Number.isFinite(s.U_${k}) ? NaN : s.U_${k} + s.D_${k} === 0 ? 50 : 100 * s.U_${k} / (s.U_${k} + s.D_${k}); // RSI ${n}` : `    s.V_${k} = s.U_${k}; // ATR ${n}`);
        break;
      }
      case 'filter.session': {
        const ss = parseSession(q), tz = String(q.timezone || 'Etc/UTC');
        if (!/^[A-Za-z_]+(\/[A-Za-z0-9_+\-]+)*$/.test(tz)) throw new Error(`Invalid timezone in ${b.id}`);
        if (!tzs.has(tz)) tzs.set(tz, `tz${tzs.size}`);
        const f = tzs.get(tz);
        L.push(`    const m_${k} = this.minutes(this.${f}, d.timestamp()); // minutes after midnight in ${tz}`);
        L.push(`    s.S_${k} = ${ss.start <= ss.end ? `m_${k} >= ${ss.start} && m_${k} < ${ss.end}` : `m_${k} >= ${ss.start} || m_${k} < ${ss.end}`}; // session ${tsNote(q.session || '0000-2359')}`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = q.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`    s.S_${k} = !!p && ${val(q.left)} ${gt} ${val(q.right)} && ${val(q.left, 'p')} ${le} ${val(q.right, 'p')};`);
        break;
      }
      case 'signal.threshold': {
        if (q.right === undefined && !Number.isFinite(Number(q.value))) throw new Error(`Invalid threshold in ${b.id}`);
        const op = { '==': '===', '!=': '!==' }[thresholdOp(q)] || thresholdOp(q);
        L.push(`    s.S_${k} = Number.isFinite(${val(q.left)}) && ${val(q.left)} ${op} ${q.right !== undefined ? val(q.right) : Number(q.value)};`);
        break;
      }
      case 'signal.recent':
        L.push(`    s.S_${k} = ${orOf(q.bars, j => `(i >= ${j} && !!this.bars[i - ${j}].S_${id(q.signal)})`, ' || ')}; // ${q.signal} on ${q.bars === 1 ? 'the bar' : `one of the ${q.bars} bars`} before this one`);
        break;
      case 'signal.combine':
        L.push(`    s.S_${k} = ${(q.signals || []).map(x => bool(x)).join(q.mode === 'any' ? ' || ' : ' && ') || 'false'};`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      case 'visual.table': {
        const t = tables.find(x => x.id === b.id);
        if (!t || !t.fields.length) { L.push(`    // TODO unsupported block ${b.type}: ${k} (no field can be shown yet)`); break; }
        L.push(`    s.T_${k} = { ${t.fields.map(x => `${JSON.stringify(x.id)}: ${x.bool ? `!!${bool(x.id)}` : val(x.id)}`).join(', ')} }; // panel ${tsNote(t.title)}: this bar's values (read this.bars[i - 1].T_${k} for the bar that just closed)`);
        break;
      }
      case 'alert.webhook':
        if (!webhookOk(recipe, b)) { L.push(`    // TODO unsupported block ${b.type}: ${k}`, `    s.S_${k} = false;`); break; }
        L.push(`    s.S_${k} = ${bool(q.when)}; // webhook condition on this bar`,
          `    s.J_${k} = s.S_${k} ? this.bsvWebhook(${JSON.stringify(q.payload)}, d.timestamp(), s) : null; // JSON text for this bar, rebuilt if the forming bar changes; built here, never sent`);
        break;
      case 'visual.zone':
        if (zoneOk(recipe, b)) { L.push(`    // zone ${k}: drawn as Z lines from ${id(q.source)} (${map.get(q.source).type === 'structure.range' ? 'the window high / low' : 'last confirmed pivot high / low'})`); break; }
        L.push(`    // TODO unsupported block ${b.type}: ${k}`, `    s.V_${k} = NaN;`);
        break;
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { L.push(`    // TODO unsupported block ${b.type}: ${k}`, `    s.V_${k} = NaN;`); break; }
        const [hk, lk] = (q.source || 'close') === 'high_low' ? ['h', 'l'] : ['c', 'c'];
        usesPivot = true;
        L.push(`    s.N_${k} = this.bsvPivot(s, i, ${q.left}, ${q.right}, "${hk}", "${lk}"); // is bar i - ${q.right} a new pivot high / low? known only now: no lookahead`,
          `    s.V_${k}_high = s.N_${k}[0] ? this.bars[i - ${q.right}].${hk} : p ? p.V_${k}_high : NaN; // last confirmed pivot high, held`,
          `    s.V_${k}_low = s.N_${k}[1] ? this.bars[i - ${q.right}].${lk} : p ? p.V_${k}_low : NaN; // last confirmed pivot low, held`);
        break;
      }
      case 'structure.range': {
        if (!rangeOk(recipe, b)) { L.push(`    // TODO unsupported block ${b.type}: ${k}`, `    s.V_${k} = NaN;`); break; }
        L.push(`    s.R_${k} = ${bool(q.during)}; // inside the window`,
          `    if (s.R_${k}) { const fresh = !p || !p.R_${k}; s.V_${k}_high = fresh ? s.h : Math.max(p.V_${k}_high, s.h); s.V_${k}_low = fresh ? s.l : Math.min(p.V_${k}_low, s.l); } // so far in this window; a new window resets`,
          `    else { s.V_${k}_high = p ? p.V_${k}_high : NaN; s.V_${k}_low = p ? p.V_${k}_low : NaN; } // after the window: the finished window, held (NaN before the first)`);
        break;
      }
      case 'signal.breakout': {
        if (!breakoutOk(recipe, b)) { L.push(`    // TODO unsupported block ${b.type}: ${k}`, `    s.S_${k} = false;`); break; }
        const r = id(q.range), d = q.direction || 'either', ok = `!!p && !s.R_${r} && Number.isFinite(s.V_${r}_high)`;
        L.push(`    const up_${k} = ${ok} && s.c > s.V_${r}_high && p.c <= s.V_${r}_high, dn_${k} = ${ok} && s.c < s.V_${r}_low && p.c >= s.V_${r}_low;`,
          `    s.S_${k} = ${d === 'either' ? `up_${k} || dn_${k}` : d === 'above' ? `up_${k}` : `dn_${k}`}; // first close beyond the finished window, on a closed bar outside it`);
        break;
      }
      case 'signal.liquidity_sweep': {
        if (!sweepOk(recipe, b)) { L.push(`    // TODO unsupported block ${b.type}: ${k}`, `    s.S_${k} = false;`); break; }
        const pv = id(q.pivot), a = val(q.atr), m = `${Number(q.minAtrFraction || 0)} * ${a}`;
        L.push(`    s.S_${k} = !!p && Number.isFinite(${a}) && ((Number.isFinite(p.V_${pv}_high) && s.h > p.V_${pv}_high && s.h - p.V_${pv}_high >= ${m} && s.c < p.V_${pv}_high) || (Number.isFinite(p.V_${pv}_low) && s.l < p.V_${pv}_low && p.V_${pv}_low - s.l >= ${m} && s.c > p.V_${pv}_low)); // sweep candidate: wick beyond the pivot level known before this bar, close back inside`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { L.push(`    // TODO unsupported block ${b.type}: ${k}`, `    s.S_${k} = false;`); break; }
        const pb = map.get(q.pivot), pv = id(pb.id), pq = pb.params, [hk, lk] = (pq.source || 'close') === 'high_low' ? ['h', 'l'] : ['c', 'c'], o = id(q.oscillator), d = q.direction || 'both';
        L.push(`    s.dh_${k} = p ? p.dh_${k} : null; s.dl_${k} = p ? p.dl_${k} : null; let bear_${k} = false, bull_${k} = false; // previous pivot high / low as [price, oscillator]`,
          `    if (s.N_${pv}[0]) { const b = this.bars[i - ${pq.right}], x = [b.${hk}, b.V_${o}]; bear_${k} = !!s.dh_${k} && x[0] > s.dh_${k}[0] && x[1] < s.dh_${k}[1]; s.dh_${k} = x; } // higher price high, lower oscillator`,
          `    if (s.N_${pv}[1]) { const b = this.bars[i - ${pq.right}], x = [b.${lk}, b.V_${o}]; bull_${k} = !!s.dl_${k} && x[0] < s.dl_${k}[0] && x[1] > s.dl_${k}[1]; s.dl_${k} = x; } // lower price low, higher oscillator`,
          `    s.S_${k} = ${d === 'both' ? `bear_${k} || bull_${k}` : d === 'bearish' ? `bear_${k}` : `bull_${k}`}; // regular divergence, true on the bar that confirms the pivot`);
        break;
      }
      default:
        L.push(`    // TODO unsupported block ${b.type}: ${k}`);
        L.push(isBoolType(b.type) ? `    s.S_${k} = false;` : `    s.V_${k} = NaN;`);
    }
  }
  L.push('    this.bars[i] = s;');
  L.push('    this.bars.length = i + 1;');
  L.push('    const out = (v) => Number.isFinite(v) ? v : undefined;');
  const ret = [];
  plots.forEach((b, k) => ret.push(`P${k + 1}: out(${val(b.params?.source)})`));
  zones.forEach((b, n) => ret.push(`Z${n + 1}H: out(s.V_${id(b.params.source)}_high)`, `Z${n + 1}L: out(s.V_${id(b.params.source)}_low)`));
  alerts.forEach((b, k) => ret.push(`A${k + 1}: p && ${bool(b.params?.when, 'p')} ? ${recipe.overlay ? 'p.c' : '1'} : undefined`));
  hooks.forEach((b, n) => ret.push(`W${n + 1}: p && p.S_${id(b.id)} ? ${recipe.overlay ? 'p.c' : '1'} : undefined`));
  L.push(`    return { ${ret.join(', ')} };`);
  L.push('  }');
  if (hooks.length) L.push('', '  bsvWebhook(payload, t, s) { // {{symbol}} {{timeframe}} {{time}} (UTC, YYYY-MM-DDTHH:MM:SS) {{open}} {{high}} {{low}} {{close}} filled in; returns JSON text',
    '    const g = (v) => String(Number(v.toPrecision(10))), f = { symbol: BSV_SYMBOL, timeframe: BSV_TIMEFRAME, time: new Date(+t).toISOString().slice(0, 19), open: g(s.o), high: g(s.h), low: g(s.l), close: g(s.c) };',
    '    const out = {};', '    for (const k of Object.keys(payload)) out[k] = typeof payload[k] === "string" ? payload[k].replace(/\\{\\{([^}]*)\\}\\}/g, (m, n) => f[n]) : payload[k];', '    return JSON.stringify(out);', '  }');
  if (usesPivot) L.push('', '  bsvPivot(s, i, left, right, hk, lk) { // bar j = i - right: strictly beyond the left bars, at least as far as the right bars (a flat top counts once)',
    '    const j = i - right;', '    if (j - left < 0) return [false, false];', '    const x = this.bars[j], at = (n) => (n === i ? s : this.bars[n]);', '    let up = true, dn = true;',
    '    for (let n = j - left; n <= i; n++) {', '      if (n === j) continue;', '      const y = at(n);', '      if (n < j ? !(x[hk] > y[hk]) : !(x[hk] >= y[hk])) up = false;', '      if (n < j ? !(x[lk] < y[lk]) : !(x[lk] <= y[lk])) dn = false;', '    }', '    return [up, dn];', '  }');
  if (usesHtf) L.push('', '  BsvHtf(st, kind, n, b, pc, src) { // one closed higher-timeframe bar b (closed bars only: no repaint, no lookahead); pc = close of the closed bar before it',
    '    const x = { open: b.o, high: b.h, low: b.l, close: b.c, hl2: (b.h + b.l) / 2, hlc3: (b.h + b.l + b.c) / 3, ohlc4: (b.o + b.h + b.l + b.c) / 4 }[src];',
    '    const q = st ? Object.assign({}, st) : { k: kind === "ema" || kind === "sma" ? 0 : -1, t: 0, w: [], V: NaN, U: NaN, D: NaN, su: 0, sd: 0, px: NaN };',
    '    q.k++;',
    '    if (kind === "ema" || kind === "sma") {',
    '      if (q.k <= n) q.t += x;',
    '      if (kind === "ema") q.V = q.k < n ? NaN : q.k === n ? q.t / n : q.V + 2 / (n + 1) * (x - q.V); // seeded with the SMA of the first n closed bars',
    '      else { q.w = q.w.concat([x]).slice(-n); q.V = q.w.length === n ? q.w.reduce((a, v) => a + v, 0) / n : NaN; }',
    '    } else { // RSI / ATR: Wilder averages of the changes, counted from the second closed bar',
    '      const first = q.k === 0, u = first ? 0 : kind === "rsi" ? Math.max(x - q.px, 0) : Math.max(b.h, pc) - Math.min(b.l, pc), v = first || kind !== "rsi" ? 0 : Math.max(q.px - x, 0);',
    '      if (q.k <= n) { q.su += u; q.sd += v; }',
    '      q.U = q.k < n ? NaN : q.k === n ? q.su / n : (q.U * (n - 1) + u) / n;',
    '      q.D = q.k < n ? NaN : q.k === n ? q.sd / n : (q.D * (n - 1) + v) / n;',
    '      q.V = kind === "rsi" ? (!Number.isFinite(q.U) ? NaN : q.U + q.D === 0 ? 50 : 100 * q.U / (q.U + q.D)) : q.U;',
    '      q.px = x;',
    '    }',
    '    return q;',
    '  }');
  if (tzs.size) {
    L.splice(initAt, 0, ...[...tzs].map(([tz, f]) => `    this.${f} = new Intl.DateTimeFormat("en-US", { timeZone: ${JSON.stringify(tz)}, hour: "2-digit", minute: "2-digit", hourCycle: "h23" });`));
    L.push('', '  minutes(fmt, date) {', '    const parts = fmt.formatToParts(date), get = (t) => Number(parts.find((x) => x.type === t).value);', '    return get("hour") * 60 + get("minute");', '  }');
  }
  L.push('}');
  L.push('');
  const zt = (b, x) => jsText(String(b.params?.title || b.id).slice(0, 50) + ' ' + x, 60);
  const plotEntries = [...plots.map((b, k) => `    P${k + 1}: { title: ${jsText(b.params?.title || b.params?.source || b.id, 60)} }`), ...zones.flatMap((b, n) => [`    Z${n + 1}H: { title: ${zt(b, 'high')} }`, `    Z${n + 1}L: { title: ${zt(b, 'low')} }`]), ...alerts.map((b, k) => `    A${k + 1}: { title: ${jsText('Alert: ' + (b.params?.message || b.id), 80)} }`), ...hooks.map((b, n) => `    W${n + 1}: { title: ${jsText('Webhook: ' + b.id, 80)} }`)];
  const styles = [...plots.map((b, k) => `      P${k + 1}: { color: "${colors[k % colors.length]}" }`), ...zones.flatMap((b, n) => [`      Z${n + 1}H: { color: "salmon" }`, `      Z${n + 1}L: { color: "lightgreen" }`]), ...alerts.map((b, k) => `      A${k + 1}: { color: "${k % 2 ? 'salmon' : 'lightgreen'}" }`), ...hooks.map((b, n) => `      W${n + 1}: { color: "yellow" }`)];
  L.push('module.exports = {');
  L.push(`  name: "${name}",`);
  L.push(`  description: ${jsText(safeTitle(recipe), 80)},`);
  L.push('  calculator: bsvRecipe,');
  L.push('  params: {},');
  L.push('  inputType: "bars",');
  L.push(`  areaChoice: "${recipe.overlay ? 'overlay' : 'new'}",`);
  L.push('  tags: ["BSV starters"],');
  L.push(`  plots: {${plotEntries.length ? '\n' + plotEntries.join(',\n') + '\n  ' : ''}},`);
  L.push(`  plotter: [${[...plots.map((b, k) => `predef.plotters.singleline("P${k + 1}")`), ...zones.flatMap((b, n) => [`predef.plotters.singleline("Z${n + 1}H")`, `predef.plotters.singleline("Z${n + 1}L")`]), ...alerts.map((b, k) => `predef.plotters.dots("A${k + 1}")`), ...hooks.map((b, n) => `predef.plotters.dots("W${n + 1}")`)].join(', ')}],`);
  if (alerts.length || hooks.length) L.push(`  shifts: { ${[...alerts.map((b, k) => `A${k + 1}: -1`), ...hooks.map((b, n) => `W${n + 1}: -1`)].join(', ')} }, // alert and webhook dots sit on the bar that just closed`);
  L.push(`  schemeStyles: { dark: {${styles.length ? '\n' + styles.join(',\n') + '\n    ' : ''}} }`);
  L.push('};');
  L.push('');
  L.push('// End BSV generated starter.');
  return L.join('\n') + '\n';
}

function pyText(s, max = 200) {
  return JSON.stringify(String(s ?? '').replace(/[\r\n\u2028\u2029]/g, ' ').trim().slice(0, max));
}

function pyHtfLines() {
  // Pure-Python higher-timeframe bars (shared by the Python targets). A higher-timeframe bar is used only once a chart
  // bar of the next higher-timeframe period has arrived, so it is always closed: no repaint, no lookahead.
  return [
    'class BsvHtf:',
    '    """Higher-timeframe bars built from the chart bars; only closed ones are used. Periods are aligned to UTC',
    '    (Unix time) and bar times are read as bar-open times. Refuses to run if chart bars are not shorter."""',
    '    def __init__(self, minutes):',
    '        self.sec, self.done, self.cur, self.last, self.step, self.memo = int(minutes) * 60, [], None, None, None, {}',
    '    def update(self, t, o, h, l, c):  # t = chart bar time in Unix seconds (UTC); call once per completed chart bar',
    '        if self.last is not None:',
    '            if t <= self.last:',
    '                raise SystemExit("BSV higher timeframe: bar times must increase")',
    '            self.step = t - self.last if self.step is None else min(self.step, t - self.last)',
    '            if self.step >= self.sec:',
    '                raise SystemExit("BSV higher timeframe: chart bars must be shorter than %d minutes; not computing it on the chart timeframe" % (self.sec // 60))',
    '        self.last = t',
    '        k = int(t // self.sec)',
    '        if self.cur is not None and self.cur[0] == k:',
    '            self.cur[2], self.cur[3], self.cur[4] = max(self.cur[2], h), min(self.cur[3], l), c',
    '            return',
    '        if self.cur is not None:',
    '            self.done.append(tuple(self.cur[1:]))  # the previous period is now closed',
    '            self.memo = {}',
    '        self.cur = [k, o, h, l, c]',
    '    def value(self, kind, source, n):  # indicator on the closed higher-timeframe bars; NaN while warming up',
    '        key = (kind, source, n)',
    '        if key not in self.memo:',
    '            self.memo[key] = bsv_htf_last(self.done, kind, source, n)',
    '        return self.memo[key]',
    '',
    '',
    'def bsv_htf_rma(x, n):  # Wilder average seeded with the simple average of the first n values; last value',
    '    if len(x) < n:',
    '        return NAN',
    '    r = sum(x[:n]) / n',
    '    for v in x[n:]:',
    '        r = (r * (n - 1) + v) / n',
    '    return r',
    '',
    '',
    'def bsv_htf_last(bars, kind, source, n):',
    '    if kind == "atr":',
    '        return bsv_htf_rma([max(bars[i][1], bars[i - 1][3]) - min(bars[i][2], bars[i - 1][3]) for i in range(1, len(bars))], n)',
    '    px = {"open": lambda b: b[0], "high": lambda b: b[1], "low": lambda b: b[2], "close": lambda b: b[3], "hl2": lambda b: (b[1] + b[2]) / 2,',
    '          "hlc3": lambda b: (b[1] + b[2] + b[3]) / 3, "ohlc4": lambda b: (b[0] + b[1] + b[2] + b[3]) / 4}[source]',
    '    x = [px(b) for b in bars]',
    '    if kind == "sma":',
    '        return sum(x[-n:]) / n if len(x) >= n else NAN',
    '    if kind == "ema":',
    '        if len(x) < n:',
    '            return NAN',
    '        e, a = sum(x[:n]) / n, 2.0 / (n + 1)',
    '        for v in x[n:]:',
    '            e = a * v + (1 - a) * e',
    '        return e',
    '    up = bsv_htf_rma([max(x[i] - x[i - 1], 0) for i in range(1, len(x))], n)',
    '    dn = bsv_htf_rma([max(x[i - 1] - x[i], 0) for i in range(1, len(x))], n)',
    '    if up != up:',
    '        return NAN',
    '    return 50.0 if up + dn == 0 else (100.0 if dn == 0 else 100.0 * up / (up + dn))  # Wilder RSI',
    '',
    '',
  ];
}
function pyHtfUses(recipe) {  // [{block, src, minutes}] for indicators rendered on a higher timeframe
  return recipe.blocks.map(b => ({ b, src: recipe.bsvHtfReal ? htfSource(recipe, b) : null })).filter(x => x.src).map(x => ({ block: x.b, src: x.src, minutes: htfMinutes(x.src) }));
}
function pyHtfCall(u, obj) {
  const kind = u.block.type.split('.')[1], q = u.block.params || {};
  return `${obj}.value(${pyText(kind)}, ${pyText(kind === 'atr' ? 'close' : sourceName(q.source))}, ${Number(q.length) | 0})`;
}

function renderBacktrader(recipe) {
  // backtrader (Python) indicator + an alert-only Strategy, using backtrader's documented indicators
  // (bt.ind.EMA / SMA / RSI (Wilder, safediv) / ATR) and GenericCSVData. Strategy.next() only sees completed bars.
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const id = (x) => String(x).replace(/[^A-Za-z0-9_]/g, '_');
  const pxl = { open: 'd.open', high: 'd.high', low: 'd.low', close: 'd.close', hl2: '(d.high + d.low) / 2', hlc3: '(d.high + d.low + d.close) / 3', ohlc4: '(d.open + d.high + d.low + d.close) / 4' };
  const pxv = (ref, k) => {
    const f = (n) => `d.${n}[${k}]`;
    return { open: f('open'), high: f('high'), low: f('low'), close: f('close'), hl2: `(${f('high')} + ${f('low')}) / 2`, hlc3: `(${f('high')} + ${f('low')} + ${f('close')}) / 3`, ohlc4: `(${f('open')} + ${f('high')} + ${f('low')} + ${f('close')}) / 4` }[ref];
  };
  const htf = pyHtfUses(recipe), htfIds = new Set(htf.map(u => u.block.id)), htfSrc = [...new Set(htf.map(u => u.src.id))];
  const isInd = (ref) => /^indicator\.(ema|sma|rsi|atr)$/.test(map.get(ref)?.type || '') && !htfIds.has(ref);
  const val = (ref, prev = false) => isPrice(ref) ? pxv(ref, prev ? -1 : 0)
    : isBoolType(map.get(ref)?.type) ? `(1.0 if ${prev ? 'p' : 's'}.get(${pyText(ref)}) else 0.0)`
    : isInd(ref) ? `self.i_${id(ref)}[${prev ? -1 : 0}]` : `${prev ? 'p' : 's'}.get(${pyText(ref)}, NAN)`;
  const bool = (ref, prev = false) => isBoolType(map.get(ref)?.type) ? `bool(${prev ? 'p' : 's'}.get(${pyText(ref)}))` : `(not math.isnan(${val(ref, prev)}) and ${val(ref, prev)} != 0)`;
  const cls = 'Bsv' + className(recipe);
  const zones = recipe.blocks.filter(b => zoneOk(recipe, b)), hooks = recipe.blocks.filter(b => webhookOk(recipe, b)), pivots = recipe.blocks.filter(b => pivotOk(recipe, b));
  const lines = [...plots.map((_, k) => `p${k + 1}`), ...alerts.map((_, k) => `a${k + 1}`), ...zones.flatMap((_, k) => [`z${k + 1}h`, `z${k + 1}l`]), ...hooks.map((_, k) => `w${k + 1}`)];
  const tzs = [];
  const L = [];
  L.push('# ORIGINAL BSV STARTER — backtrader indicator + alert-only strategy (Python).');
  L.push('# Generated by BSV Trader Tool Blocks. Not runtime tested by BSV on a broker or live feed. Not investment advice.');
  L.push(`# ${tsNote(safeTitle(recipe))}: pip install backtrader, then run: python this_file.py bars.csv [--plot]`);
  L.push('# bars.csv columns: datetime (YYYY-MM-DD HH:MM:SS, read as UTC), open, high, low, close, volume.');
  L.push(`# ${recipe.overlay ? 'Overlay recipe: lines are drawn on the price chart.' : 'Separate-pane recipe: lines are drawn in their own subplot.'}`);
  L.push('# Alerts are printed for completed bars only (backtrader calls next() once per completed bar). The strategy places no orders.');
  L.push('');
  if (hooks.length) L.push('import json');
  L.push('import math');
  L.push('import sys');
  if (recipe.blocks.some(b => b.type === 'filter.session')) L.push('from datetime import timezone', 'from zoneinfo import ZoneInfo');
  else if (htf.length) L.push('from datetime import timezone');
  L.push('');
  L.push('import backtrader as bt');
  L.push('');
  L.push('NAN = float("nan")');
  L.push('');
  L.push('');
  if (recipe.blocks.some(b => b.type === 'visual.table')) {
    L.push('def bsv_cell(x):  # value-panel cell: n/a while the value is still warming up');
    L.push('    x = float(x)');
    L.push('    return "n/a" if not math.isfinite(x) else "%.6g" % x');
    L.push('');
    L.push('');
  }
  if (htf.length) pyHtfLines().forEach(x => L.push(x));
  const ranges = recipe.blocks.filter(b => rangeOk(recipe, b));
  if (ranges.length) pyRangeLines().forEach(x => L.push(x));
  if (pivots.length) pyPivotLines().forEach(x => L.push(x));
  pySignalLines(recipe).forEach(x => L.push(x));
  if (hooks.length) pyWebhookLines(recipe).forEach(x => L.push(x));
  const noLines = !lines.length;
  if (noLines) lines.push('idle');  // backtrader needs at least one line; this one stays NaN and is not plotted
  L.push(`class ${cls}(bt.Indicator):`);
  L.push(`    lines = (${lines.map(x => `"${x}"`).join(', ')}${lines.length === 1 ? ',' : ''})`);
  L.push(`    plotinfo = dict(subplot=${recipe.overlay ? 'False' : 'True'})`);
  const pl = [...alerts.map((_, k) => `a${k + 1}=dict(marker="o", ls="", markersize=6)`), ...hooks.map((_, k) => `w${k + 1}=dict(marker="^", ls="", markersize=6)`), ...(noLines ? ['idle=dict(_plotskip=True)'] : [])];
  if (pl.length) L.push(`    plotlines = dict(${pl.join(', ')})`);
  L.push('');
  L.push('    def __init__(self):');
  L.push('        d = self.data');
  L.push('        self._prev = {}');
  let nInd = 0;
  for (const b of recipe.blocks) {
    const q = b.params || {}, k = id(b.id), src = /^indicator\.(ema|sma|rsi)$/.test(b.type) ? pxl[sourceName(q.source)] : null;
    if (htfIds.has(b.id)) continue;  // computed in next() from closed higher-timeframe bars
    if (b.type === 'indicator.ema') { L.push(`        self.i_${k} = bt.ind.EMA(${src}, period=${q.length})`); nInd++; }
    if (b.type === 'indicator.sma') { L.push(`        self.i_${k} = bt.ind.SMA(${src}, period=${q.length})`); nInd++; }
    if (b.type === 'indicator.rsi') { L.push(`        self.i_${k} = bt.ind.RSI(${src}, period=${q.length}, safediv=True)  # Wilder smoothing; 100 when there are no down moves, 50 when flat`); nInd++; }
    if (b.type === 'indicator.atr') { L.push(`        self.i_${k} = bt.ind.ATR(d, period=${q.length})  # Wilder-smoothed true range`); nInd++; }
    if (b.type === 'filter.session') { const tz = String(q.timezone || 'Etc/UTC'); if (!/^[A-Za-z_]+(\/[A-Za-z0-9_+\-]+)*$/.test(tz)) throw new Error(`Invalid timezone in ${b.id}`); if (!tzs.includes(tz)) tzs.push(tz); }
  }
  tzs.forEach((tz, n) => L.push(`        self.tz${n} = ZoneInfo(${pyText(tz)})`));
  ranges.forEach(b => L.push(`        self.rg_${id(b.id)} = [False, NAN, NAN]  # ${tsNote(b.id)}: window state`));
  pivots.forEach(b => L.push(`        self.pv_${id(b.id)} = [[], [], NAN, NAN]  # ${tsNote(b.id)}: pivot state`));
  recipe.blocks.filter(b => divergenceOk(recipe, b)).forEach(b => L.push(`        self.dv_${id(b.id)} = [[], [], [], None, None]  # ${tsNote(b.id)}: divergence state`));
  htfSrc.forEach(h => L.push(`        self.htf_${id(h)} = BsvHtf(${htfMinutes(map.get(h))})  # ${tsNote(h)}: closed higher-timeframe bars only`));
  L.push('');
  L.push('    def prenext(self):');
  L.push('        self.next()  # also evaluate while the slowest average is still warming up (its values are NaN)');
  L.push('');
  L.push('    def next(self):');
  L.push('        d, p, s = self.data, self._prev, {}');
  L.push('        first = len(self) < 2');
  if (htfSrc.length) L.push('        t_unix = d.datetime.datetime(0).replace(tzinfo=timezone.utc).timestamp()');
  htfSrc.forEach(h => L.push(`        self.htf_${id(h)}.update(t_unix, d.open[0], d.high[0], d.low[0], d.close[0])`));
  for (const b of depOrder(recipe)) {
    const q = b.params || {}, k = pyText(b.id);
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': case 'indicator.atr': {
        const u = htf.find(x => x.block.id === b.id);
        if (u) L.push(`        s[${k}] = ${pyHtfCall(u, 'self.htf_' + id(u.src.id))}  # timeframe ${tsNote(u.src.params.timeframe)}, closed bars only`);
        break;
      }
      case 'visual.plot': case 'alert.condition': case 'visual.table':
        break;
      case 'structure.range':
        if (!rangeOk(recipe, b)) { L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`); L.push(`        s[${k}] = NAN`); break; }
        L.push(`        s[${pyText(b.id + '.high')}], s[${pyText(b.id + '.low')}] = bsv_range_step(self.rg_${id(b.id)}, ${bool(q.during)}, d.high[0], d.low[0])`);
        break;
      case 'structure.pivot': {
        if (!pivotOk(recipe, b)) { L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`); L.push(`        s[${k}] = NAN`); break; }
        const hl = (q.source || 'close') === 'high_low' ? 'd.high[0], d.low[0]' : 'd.close[0], d.close[0]';
        L.push(`        s[${pyText(b.id + '.high')}], s[${pyText(b.id + '.low')}] = bsv_pivot_step(self.pv_${id(b.id)}, ${hl}, ${q.left}, ${q.right})`);
        break;
      }
      case 'visual.zone':
        if (!zoneOk(recipe, b)) { L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`); L.push(`        s[${k}] = NAN`); }
        break;
      case 'alert.webhook':
        if (!webhookOk(recipe, b)) { L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`); L.push(`        s[${k}] = False`); }
        break;
      case 'signal.liquidity_sweep': {
        if (!sweepOk(recipe, b)) { L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`); L.push(`        s[${k}] = False`); break; }
        L.push(`        s[${k}] = bsv_sweep(p.get(${pyText(q.pivot + '.high')}, NAN), p.get(${pyText(q.pivot + '.low')}, NAN), d.high[0], d.low[0], d.close[0], ${val(q.atr)}, ${Number(q.minAtrFraction || 0)})  # candidate only`);
        break;
      }
      case 'signal.divergence': {
        if (!divergenceOk(recipe, b)) { L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`); L.push(`        s[${k}] = False`); break; }
        const pq = map.get(q.pivot).params, hl = (pq.source || 'close') === 'high_low' ? 'd.high[0], d.low[0]' : 'd.close[0], d.close[0]';
        L.push(`        s[${k}] = bsv_divergence_step(self.dv_${id(b.id)}, ${hl}, ${val(q.oscillator)}, ${pq.left}, ${pq.right}, ${pyText(q.direction || 'both')})`);
        break;
      }
      case 'signal.breakout': {
        if (!breakoutOk(recipe, b)) { L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`); L.push(`        s[${k}] = False`); break; }
        const r = map.get(q.range);
        L.push(`        s[${k}] = bsv_breakout(${bool(r.params.during)}, s[${pyText(r.id + '.high')}], s[${pyText(r.id + '.low')}], d.close[0], NAN if first else d.close[-1], ${pyText(q.direction || 'either')})`);
        break;
      }
      case 'data.higher_timeframe':
        if (htfSrc.includes(b.id)) break;
        L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`);
        L.push(`        s[${k}] = NAN`);
        break;
      case 'filter.session': {
        const ss = parseSession(q), n = tzs.indexOf(String(q.timezone || 'Etc/UTC'));
        L.push(`        t = d.datetime.datetime(0).replace(tzinfo=timezone.utc).astimezone(self.tz${n})`);
        L.push(`        m = t.hour * 60 + t.minute  # session ${tsNote(q.session || '0000-2359')} in ${tsNote(q.timezone || 'Etc/UTC')}`);
        L.push(`        s[${k}] = ${ss.start <= ss.end ? `${ss.start} <= m < ${ss.end}` : `m >= ${ss.start} or m < ${ss.end}`}`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = q.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`        s[${k}] = (not first) and ${val(q.left)} ${gt} ${val(q.right)} and ${val(q.left, true)} ${le} ${val(q.right, true)}`);
        break;
      }
      case 'signal.threshold': {
        if (q.right === undefined && !Number.isFinite(Number(q.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`        s[${k}] = ${val(q.left)} ${thresholdOp(q)} ${q.right !== undefined ? val(q.right) : Number(q.value)}`);
        break;
      }
      case 'signal.recent':
        L.push(`        ps = p.get(${pyText('~since:' + b.id)})  # bars since ${q.signal} was last true, as of the bar before`, `        s[${k}] = ps is not None and ps < ${q.bars}`, `        s[${pyText('~since:' + b.id)}] = 0 if ${bool(q.signal)} else (None if ps is None else ps + 1)`);
        break;
      case 'signal.combine':
        L.push(`        s[${k}] = ${(q.signals || []).map(x => bool(x)).join(q.mode === 'any' ? ' or ' : ' and ') || 'False'}`);
        break;
      case 'scanner.symbol_set':
        if (scanOk(recipe, b)) { L.push(`        # ${tsNote(b.id)}: symbol scan of ${tsNote(scanSignal(recipe, b))}, see bsv_scan_${id(b.id)}() below`); break; }
        L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)} - ${scanWhyNot(recipe, b)}`, `        s[${k}] = NAN`);
        break;
      default:
        L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`);
        L.push(isBoolType(b.type) ? `        s[${k}] = False` : `        s[${k}] = NAN`);
    }
  }
  plots.forEach((b, n) => L.push(`        self.lines.p${n + 1}[0] = ${val(b.params?.source)}`));
  alerts.forEach((b, n) => L.push(`        self.lines.a${n + 1}[0] = ${recipe.overlay ? 'd.close[0]' : '1.0'} if ${bool(b.params?.when)} else NAN`));
  zones.forEach((b, n) => { const src = b.params.source; L.push(`        self.lines.z${n + 1}h[0], self.lines.z${n + 1}l[0] = s.get(${pyText(src + '.high')}, NAN), s.get(${pyText(src + '.low')}, NAN)  # zone ${tsNote(b.params?.title || b.id)}`); });
  hooks.forEach((b, n) => L.push(`        self.lines.w${n + 1}[0] = ${recipe.overlay ? 'd.close[0]' : '1.0'} if ${bool(b.params.when)} else NAN  # webhook ${tsNote(b.id)}`));
  L.push('        self._prev = s');
  L.push('');
  L.push('');
  L.push('class BsvAlerts(bt.Strategy):');
  L.push(`    messages = (${alerts.map(b => pyText(b.params?.message || b.id)).join(', ')}${alerts.length === 1 ? ',' : ''})`);
  L.push('');
  L.push('    def __init__(self):');
  L.push(`        self.ind = ${cls}(self.data)`);
  L.push('');
  L.push('    def prenext(self):');
  L.push('        self.next()');
  L.push('');
  L.push('    def next(self):');
  L.push('        when = self.data.datetime.datetime(0).isoformat()');
  if (alerts.length) {
    L.push('        for k, msg in enumerate(self.messages):');
    L.push('            if not math.isnan(getattr(self.ind.lines, "a%d" % (k + 1))[0]):');
    L.push('                print("ALERT", when, msg)');
  } else if (!hooks.length) L.push('        pass  # this recipe has no alert blocks');
  if (hooks.length) {
    L.push('        d = self.data');
    L.push('        for k, (name, payload) in enumerate(BSV_WEBHOOKS):');
    L.push('            if not math.isnan(getattr(self.ind.lines, "w%d" % (k + 1))[0]):');
    L.push('                print("WEBHOOK", when, bsv_webhook(payload, when, d.open[0], d.high[0], d.low[0], d.close[0]))  # printed, not sent');
  }
  const tables = tableBlocks(recipe);
  if (tables.length) {
    L.push('');
    L.push('    def stop(self):  # backtrader calls stop() after the last bar: print each value panel for that bar');
    L.push('        ind, d = self.ind, self.data');
    L.push('        s = ind._prev');
    for (const t of tables) {
      tableTodos(t, '        #').forEach(x => L.push(x));
      if (!t.fields.length) continue;
      L.push(`        print("TABLE", ${pyText(t.title)})`);
      t.fields.forEach(f => L.push(f.bool ? `        print("  " + ${pyText(f.id)}, "true" if s.get(${pyText(f.id)}) else "false")` : `        print("  " + ${pyText(f.id)}, bsv_cell(${val(f.id).replace(/\bself\.i_/g, 'ind.i_')}))`));
    }
  }
  L.push('');
  L.push('');
  const scans = recipe.blocks.filter(b => b.type === 'scanner.symbol_set' && scanOk(recipe, b));
  if (scans.length) {
    L.push('def bsv_feed(path):  # a CSV in the format main() reads', '    return bt.feeds.GenericCSVData(dataname=path, dtformat="%Y-%m-%d %H:%M:%S", datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1, timeframe=bt.TimeFrame.Minutes)', '', '');
    for (const b of scans) { const n = id(b.id), sg = pyText(scanSignal(recipe, b));
      L.push(`class BsvScan_${n}(bt.Strategy):  # ${tsNote(b.id)}: keeps ${tsNote(scanSignal(recipe, b))} of the bar that just completed (no orders, no ALERT lines)`, '    def __init__(self):', `        self.ind = ${cls}(self.data)`, '        self.hit, self.when = False, None', '',
        '    def prenext(self):', '        self.next()', '', '    def next(self):', `        self.hit, self.when = bool(self.ind._prev.get(${sg})), self.data.datetime.datetime(0)`, '', '',
        `def bsv_scan_${n}(data):  # ${tsNote(b.id)}: data = {symbol: backtrader data feed}; returns [(symbol, bar time)] for each symbol whose ${tsNote(scanSignal(recipe, b))} held on its last completed bar`,
        '    hits = []', '    for sym, feed in data.items():', '        cerebro = bt.Cerebro(stdstats=False, runonce=False)  # one run per symbol, the same indicator code as the chart run', '        cerebro.adddata(feed, name=sym)',
        `        cerebro.addstrategy(BsvScan_${n})`, '        st = cerebro.run()[0]', '        if st.hit:', '            hits.append((sym, st.when))', '    return hits', '', ''); }
  }
  L.push('def main(argv):');
  for (const b of scans) L.push(`    if len(argv) > 2 and argv[1] == "--scan":  # ${tsNote(b.id)}: python this_file.py --scan SYMBOL=bars.csv [SYMBOL=bars.csv ...]`, '        data = dict(x.split("=", 1) for x in argv[2:])',
    `        for sym, when in bsv_scan_${id(b.id)}({k: bsv_feed(v) for k, v in data.items()}):`, `            print("SCAN", ${pyText(b.id)}, sym, when.strftime("%Y-%m-%dT%H:%M:%S"))`, `        print("SCAN", ${pyText(b.id)}, "done", len(data))`, '        return');
  L.push('    if len(argv) < 2:');
  L.push('        sys.exit("usage: python this_file.py bars.csv [--plot]  (CSV with a header row: datetime,open,high,low,close,volume; datetime as %Y-%m-%d %H:%M:%S in UTC)")');
  L.push('    cerebro = bt.Cerebro(stdstats=False, runonce=False)  # step bar by bar: the indicator logic lives in next()');
  L.push('    cerebro.adddata(bt.feeds.GenericCSVData(dataname=argv[1], dtformat="%Y-%m-%d %H:%M:%S", datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1, timeframe=bt.TimeFrame.Minutes))');
  L.push('    cerebro.addstrategy(BsvAlerts)');
  L.push('    cerebro.run()');
  L.push('    if "--plot" in argv:');
  L.push('        cerebro.plot()  # needs matplotlib');
  L.push('');
  L.push('');
  L.push('if __name__ == "__main__":');
  L.push('    main(sys.argv)');
  L.push('');
  L.push('# End BSV generated starter.');
  return L.join('\n') + '\n';
}

function renderBacktestingPy(recipe) {
  // Backtesting.py (Python) alert-only Strategy. Indicators (EMA/SMA/RSI Wilder/ATR Wilder) and signals are computed
  // once in init() as numpy arrays where bar i only uses bars 0..i; next() prints ALERT lines for the completed bar.
  const map = blockMap(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const PX = { open: 'o', high: 'h', low: 'l', close: 'c', hl2: 'hl2', hlc3: 'hlc3', ohlc4: 'ohlc4' };
  const isPx = (ref) => Object.prototype.hasOwnProperty.call(PX, ref) && !map.has(ref);
  const val = (ref) => isPx(ref) ? PX[ref] : /\./.test(ref) && map.has(ref.split('.')[0]) ? `v[${pyText(ref)}]` : !map.has(ref) ? 'NANS' : isBoolType(map.get(ref).type) ? `s[${pyText(ref)}].astype(float)` : `v[${pyText(ref)}]`;
  const bool = (ref) => map.has(ref) && isBoolType(map.get(ref).type) ? `s[${pyText(ref)}]` : `(np.isfinite(${val(ref)}) & (${val(ref)} != 0))`;
  const htf = pyHtfUses(recipe), htfSrc = [...new Set(htf.map(u => u.src.id))];
  const zones = recipe.blocks.filter(b => zoneOk(recipe, b)), hooks = recipe.blocks.filter(b => webhookOk(recipe, b)), pivots = recipe.blocks.filter(b => pivotOk(recipe, b));
  const cls = 'Bsv' + className(recipe);
  const L = [];
  L.push('# ORIGINAL BSV STARTER — Backtesting.py alert-only strategy (Python).');
  L.push('# Generated by BSV Trader Tool Blocks. Not runtime tested by BSV on a broker or live feed. Not investment advice.');
  L.push(`# ${tsNote(safeTitle(recipe))}: pip install backtesting, then run: python this_file.py bars.csv [--plot]`);
  L.push('# bars.csv columns: datetime (YYYY-MM-DD HH:MM:SS, read as UTC), open, high, low, close, volume.');
  L.push('# Every value for bar i is computed from bars 0..i only. Backtesting.py calls next() once per completed bar, starting');
  L.push('# when every plotted line has a value (and never on the first bar); alerts on earlier bars are not printed.');
  if (zones.length) L.push('# Zone lines count as plotted lines for that start.');
  L.push('# The strategy places no orders.');
  L.push('');
  if (hooks.length) L.push('import json');
  L.push('import sys');
  L.push('');
  L.push('import numpy as np');
  L.push('import pandas as pd');
  L.push('from backtesting import Backtest, Strategy');
  L.push('');
  L.push('');
  L.push('def bsv_sma(x, n):');
  L.push('    x = np.asarray(x, float)');
  L.push('    out = np.full(len(x), np.nan)');
  L.push('    for i in range(n - 1, len(x)):');
  L.push('        out[i] = x[i - n + 1:i + 1].sum() / n');
  L.push('    return out');
  L.push('');
  L.push('');
  L.push('def bsv_ema(x, n):  # seeded with the simple average of the first n bars');
  L.push('    x = np.asarray(x, float)');
  L.push('    out = np.full(len(x), np.nan)');
  L.push('    if len(x) >= n:');
  L.push('        out[n - 1] = x[:n].sum() / n');
  L.push('        a = 2.0 / (n + 1)');
  L.push('        for i in range(n, len(x)):');
  L.push('            out[i] = a * x[i] + (1 - a) * out[i - 1]');
  L.push('    return out');
  L.push('');
  L.push('');
  L.push('def bsv_rma(x, n):  # Wilder average, seeded with the simple average of the first n values');
  L.push('    out = np.full(len(x), np.nan)');
  L.push('    if len(x) >= n:');
  L.push('        out[n - 1] = x[:n].sum() / n');
  L.push('        for i in range(n, len(x)):');
  L.push('            out[i] = (out[i - 1] * (n - 1) + x[i]) / n');
  L.push('    return out');
  L.push('');
  L.push('');
  L.push('def bsv_rsi(x, n):  # Wilder RSI; 100 when there are no down moves, 50 when flat');
  L.push('    x = np.asarray(x, float)');
  L.push('    dx = np.diff(x)');
  L.push('    up, dn = bsv_rma(np.maximum(dx, 0), n), bsv_rma(np.maximum(-dx, 0), n)');
  L.push('    with np.errstate(invalid="ignore", divide="ignore"):');
  L.push('        r = np.where(up + dn == 0, 50.0, np.where(dn == 0, 100.0, 100.0 * up / (up + dn)))');
  L.push('    r[np.isnan(up)] = np.nan');
  L.push('    return np.concatenate(([np.nan], r))');
  L.push('');
  L.push('');
  L.push('def bsv_atr(h, l, c, n):  # Wilder-smoothed true range');
  L.push('    tr = np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])');
  L.push('    return np.concatenate(([np.nan], bsv_rma(tr, n)))');
  L.push('');
  L.push('');
  if (recipe.blocks.some(b => b.type === 'signal.recent')) L.push('def bsv_recent(a, n):  # true if a was true on one of the n bars before this one (the current bar is not counted)', '    a = np.asarray(a, dtype=bool)', '    out = np.zeros(len(a), dtype=bool)', '    for k in range(1, n + 1):', '        out[k:] |= a[:len(a) - k]', '    return out', '', '');
  L.push('def bsv_prev(a):');
  L.push('    return np.concatenate(([np.nan], np.asarray(a, float)[:-1]))');
  L.push('');
  L.push('');
  L.push('def bsv_minutes(index, tz):  # minute of the day in the recipe time zone; bar times are read as UTC');
  L.push('    t = pd.DatetimeIndex(index)');
  L.push('    t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert(tz)');
  L.push('    return np.asarray(t.hour * 60 + t.minute)');
  L.push('');
  L.push('');
  if (htf.length) {
    L.push('NAN = float("nan")');
    pyHtfLines().forEach(x => L.push(x));
    L.push('def bsv_htf_series(index, o, h, l, c, minutes, kind, source, n):  # bar i sees closed higher-timeframe bars only');
    L.push('    t = pd.DatetimeIndex(index)');
    L.push('    t = t.tz_localize("UTC") if t.tz is None else t');
    L.push('    x, out = BsvHtf(minutes), np.full(len(c), np.nan)');
    L.push('    for i in range(len(c)):');
    L.push('        x.update(t[i].timestamp(), float(o[i]), float(h[i]), float(l[i]), float(c[i]))');
    L.push('        out[i] = x.value(kind, source, n)');
    L.push('    return out');
  }
  const ranges = recipe.blocks.filter(b => rangeOk(recipe, b));
  if ((ranges.length || pivots.length) && !htf.length) L.push('NAN = float("nan")');
  if (ranges.length) pyRangeLines().forEach(x => L.push(x));
  if (pivots.length) pyPivotLines().forEach(x => L.push(x));
  pySignalLines(recipe).forEach(x => L.push(x));
  if (hooks.length) pyWebhookLines(recipe).forEach(x => L.push(x));
  L.push(`class ${cls}(Strategy):`);
  L.push(`    messages = (${alerts.map(b => pyText(b.params?.message || b.id)).join(', ')}${alerts.length === 1 ? ',' : ''})`);
  L.push('');
  L.push('    def init(self):');
  L.push('        d = self.data');
  L.push('        o, h, l, c = (np.asarray(x, float) for x in (d.Open, d.High, d.Low, d.Close))');
  L.push('        hl2, hlc3, ohlc4 = (h + l) / 2, (h + l + c) / 3, (o + h + l + c) / 4');
  L.push('        NANS = np.full(len(c), np.nan)');
  L.push('        v, s = {}, {}');
  L.push('        with np.errstate(invalid="ignore"):');
  for (const b of depOrder(recipe)) {
    const q = b.params || {}, k = pyText(b.id);
    const u = htf.find(x => x.block.id === b.id);
    if (u) { L.push(`            v[${k}] = bsv_htf_series(d.index, o, h, l, c, ${u.minutes}, ${pyHtfCall(u, 'X').replace(/^X\.value\(/, '').replace(/\)$/, '')})  # timeframe ${tsNote(u.src.params.timeframe)}, closed bars only`); continue; }
    if (b.type === 'data.higher_timeframe' && htfSrc.includes(b.id)) continue;
    if (rangeOk(recipe, b)) {
      L.push(`            st, hi_, lo_ = [False, NAN, NAN], np.full(len(c), np.nan), np.full(len(c), np.nan)  # ${tsNote(b.id)}: bar i only uses bars 0..i`);
      L.push(`            for i, inside in enumerate(${bool(q.during)}):`);
      L.push(`                hi_[i], lo_[i] = bsv_range_step(st, bool(inside), float(h[i]), float(l[i]))`);
      L.push(`            v[${pyText(b.id + '.high')}], v[${pyText(b.id + '.low')}] = hi_, lo_`);
      continue;
    }
    if (pivotOk(recipe, b)) {
      const [hh, ll] = (q.source || 'close') === 'high_low' ? ['h', 'l'] : ['c', 'c'];
      L.push(`            st, hi_, lo_ = [[], [], NAN, NAN], np.full(len(c), np.nan), np.full(len(c), np.nan)  # ${tsNote(b.id)}: bar i only uses bars 0..i`);
      L.push(`            for i in range(len(c)):`);
      L.push(`                hi_[i], lo_[i] = bsv_pivot_step(st, float(${hh}[i]), float(${ll}[i]), ${q.left}, ${q.right})`);
      L.push(`            v[${pyText(b.id + '.high')}], v[${pyText(b.id + '.low')}] = hi_, lo_`);
      continue;
    }
    if (zoneOk(recipe, b) || webhookOk(recipe, b)) continue;
    if (sweepOk(recipe, b)) {
      L.push(`            ph_, pl_, a_ = bsv_prev(v[${pyText(q.pivot + '.high')}]), bsv_prev(v[${pyText(q.pivot + '.low')}]), ${val(q.atr)}  # ${tsNote(b.id)}: pivot levels known before bar i`);
      L.push(`            s[${k}] = np.array([bsv_sweep(ph_[i], pl_[i], h[i], l[i], c[i], a_[i], ${Number(q.minAtrFraction || 0)}) for i in range(len(c))], bool)  # candidate only`);
      continue;
    }
    if (divergenceOk(recipe, b)) {
      const pq = map.get(q.pivot).params, [hh, ll] = (pq.source || 'close') === 'high_low' ? ['h', 'l'] : ['c', 'c'];
      L.push(`            st, x_ = [[], [], [], None, None], ${val(q.oscillator)}  # ${tsNote(b.id)}: bar i only uses bars 0..i`);
      L.push(`            s[${k}] = np.array([bsv_divergence_step(st, float(${hh}[i]), float(${ll}[i]), float(x_[i]), ${pq.left}, ${pq.right}, ${pyText(q.direction || 'both')}) for i in range(len(c))], bool)`);
      continue;
    }
    if (breakoutOk(recipe, b)) {
      const r = map.get(q.range);
      L.push(`            ins, pc = ${bool(r.params.during)}, bsv_prev(c)`);
      L.push(`            s[${k}] = np.array([bsv_breakout(bool(ins[i]), v[${pyText(r.id + '.high')}][i], v[${pyText(r.id + '.low')}][i], c[i], pc[i], ${pyText(q.direction || 'either')}) for i in range(len(c))], bool)`);
      continue;
    }
    switch (b.type) {
      case 'indicator.ema': L.push(`            v[${k}] = bsv_ema(${PX[sourceName(q.source)]}, ${Number(q.length) | 0})`); break;
      case 'indicator.sma': L.push(`            v[${k}] = bsv_sma(${PX[sourceName(q.source)]}, ${Number(q.length) | 0})`); break;
      case 'indicator.rsi': L.push(`            v[${k}] = bsv_rsi(${PX[sourceName(q.source)]}, ${Number(q.length) | 0})`); break;
      case 'indicator.atr': L.push(`            v[${k}] = bsv_atr(h, l, c, ${Number(q.length) | 0})`); break;
      case 'visual.plot': case 'alert.condition': case 'visual.table': break;
      case 'filter.session': {
        const ss = parseSession(q), tz = String(q.timezone || 'Etc/UTC');
        if (!/^[A-Za-z_]+(\/[A-Za-z0-9_+\-]+)*$/.test(tz)) throw new Error(`Invalid timezone in ${b.id}`);
        L.push(`            m = bsv_minutes(d.index, ${pyText(tz)})  # session ${tsNote(q.session || '0000-2359')}`);
        L.push(`            s[${k}] = ${ss.start <= ss.end ? `(m >= ${ss.start}) & (m < ${ss.end})` : `(m >= ${ss.start}) | (m < ${ss.end})`}`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = q.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`            s[${k}] = (${val(q.left)} ${gt} ${val(q.right)}) & (bsv_prev(${val(q.left)}) ${le} bsv_prev(${val(q.right)}))`);
        break;
      }
      case 'signal.threshold': {
        if (q.right === undefined && !Number.isFinite(Number(q.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`            s[${k}] = np.isfinite(${val(q.left)}) & (${val(q.left)} ${thresholdOp(q)} ${q.right !== undefined ? val(q.right) : Number(q.value)})`);
        break;
      }
      case 'signal.recent':
        L.push(`            s[${k}] = bsv_recent(${bool(q.signal)}, ${q.bars})  # ${q.signal} on ${q.bars === 1 ? 'the bar' : `one of the ${q.bars} bars`} before`);
        break;
      case 'signal.combine': {
        const xs = (q.signals || []).map(x => bool(x));
        L.push(`            s[${k}] = ${xs.length ? `np.logical_${q.mode === 'any' ? 'or' : 'and'}.reduce([${xs.join(', ')}])` : 'np.zeros(len(c), bool)'}`);
        break;
      }
      default:
        if (b.type === 'scanner.symbol_set' && scanOk(recipe, b)) { L.push(`            # ${tsNote(b.id)}: symbol scan of ${tsNote(scanSignal(recipe, b))}, see bsv_scan_${String(b.id).replace(/[^A-Za-z0-9_]/g, '_')}() below`); break; }
        L.push(`            # TODO unsupported block ${b.type}: ${tsNote(b.id)}${b.type === 'scanner.symbol_set' ? ' - ' + scanWhyNot(recipe, b) : ''}`);
        L.push(isBoolType(b.type) ? `            s[${k}] = np.zeros(len(c), bool)` : `            s[${k}] = NANS`);
    }
  }
  L.push('        self.bsv_values, self.bsv_signals = v, s');
  const btTables = tableBlocks(recipe);
  if (btTables.length) {
    for (const t of btTables) tableTodos(t, '        #').forEach(x => L.push(x));
    L.push(`        self.bsv_tables = [${btTables.filter(t => t.fields.length).map(t => `(${pyText(t.title)}, [${t.fields.map(f => `(${pyText(f.id)}, ${f.bool ? 'True' : 'False'}, np.asarray(${f.bool ? `s[${pyText(f.id)}]` : val(f.id)}))`).join(', ')}])`).join(', ')}]  # value panels`);
  }
  plots.forEach((b, n) => L.push(`        self.p${n + 1} = self.I(np.asarray, ${val(b.params?.source)}, name=${pyText(b.params?.title || b.params?.source || b.id, 60)}, overlay=${recipe.overlay ? 'True' : 'False'})`));
  zones.forEach((b, n) => ['high', 'low'].forEach(x => L.push(`        self.z${n + 1}${x[0]} = self.I(np.asarray, v[${pyText(b.params.source + '.' + x)}], name=${pyText((b.params?.title || b.id) + ' ' + x, 60)}, overlay=${recipe.overlay ? 'True' : 'False'})  # zone`)));
  L.push(`        self.bsv_alerts = [${alerts.map(b => `np.asarray(${bool(b.params?.when)}, bool)`).join(', ')}]`);
  if (hooks.length) {
    L.push(`        self.bsv_webhooks = [${hooks.map(b => `np.asarray(${bool(b.params.when)}, bool)`).join(', ')}]  # same order as BSV_WEBHOOKS`);
    L.push('        self.bsv_px = (o, h, l, c)');
  }
  alerts.forEach((b, n) => L.push(`        self.a${n + 1} = self.I(np.where, self.bsv_alerts[${n}], ${recipe.overlay ? 'c' : '1.0'}, np.nan, name=${pyText('alert ' + (n + 1))}, overlay=${recipe.overlay ? 'True' : 'False'}, scatter=True)`));
  L.push('');
  L.push('    def next(self):');
  L.push('        i = len(self.data) - 1  # the bar that just completed');
  if (alerts.length) {
    L.push('        for msg, a in zip(self.messages, self.bsv_alerts):');
    L.push('            if a[i]:');
    L.push('                print("ALERT", self.data.index[i].isoformat(), msg)');
  } else if (!hooks.length) L.push('        pass  # this recipe has no alert blocks');
  if (hooks.length) {
    L.push('        when, (o, h, l, c) = self.data.index[i].isoformat(), self.bsv_px');
    L.push('        for (name, payload), w in zip(BSV_WEBHOOKS, self.bsv_webhooks):');
    L.push('            if w[i]:');
    L.push('                print("WEBHOOK", when, bsv_webhook(payload, when, o[i], h[i], l[i], c[i]))  # printed, not sent');
  }
  L.push('');
  L.push('');
  if (btTables.length) {
    L.push('def bsv_print_tables(strategy):  # value panels for the last bar of the run');
    L.push('    for title, cells in strategy.bsv_tables:');
    L.push('        print("TABLE", title)');
    L.push('        for name, is_bool, a in cells:');
    L.push('            x = a[-1]');
    L.push('            print("  " + name, ("true" if x else "false") if is_bool else ("n/a" if not np.isfinite(x) else "%.6g" % float(x)))');
    L.push('');
    L.push('');
  }
  const scans = recipe.blocks.filter(b => b.type === 'scanner.symbol_set' && scanOk(recipe, b)), sid = (x) => String(x).replace(/[^A-Za-z0-9_]/g, '_');
  if (scans.length) {
    L.push('def bsv_frame(path):  # a CSV in the format main() reads', '    df = pd.read_csv(path)', '    df.index = pd.to_datetime(df.pop("datetime"), format="%Y-%m-%d %H:%M:%S")',
      '    return df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})', '', '');
    for (const b of scans) L.push(`def bsv_scan_${sid(b.id)}(data):  # ${tsNote(b.id)}: data = {symbol: DataFrame with Open, High, Low, Close, Volume}; returns [(symbol, bar time)] for each symbol whose ${tsNote(scanSignal(recipe, b))} held on its last completed bar`,
      `    class Quiet(${cls}):`, '        def next(self):', '            pass  # no ALERT lines while scanning', '', '    hits = []', '    for sym, df in data.items():',
      '        strategy = Backtest(df, Quiet, cash=1_000_000, commission=0.0).run()._strategy  # one run per symbol, the same init() as the chart run',
      `        if len(df) and bool(strategy.bsv_signals[${pyText(scanSignal(recipe, b))}][-1]):`, '            hits.append((sym, df.index[-1]))', '    return hits', '', '');
  }
  L.push('def main(argv):');
  for (const b of scans) L.push(`    if len(argv) > 2 and argv[1] == "--scan":  # ${tsNote(b.id)}: python this_file.py --scan SYMBOL=bars.csv [SYMBOL=bars.csv ...]`, '        data = dict(x.split("=", 1) for x in argv[2:])',
    `        for sym, when in bsv_scan_${sid(b.id)}({k: bsv_frame(v) for k, v in data.items()}):`, `            print("SCAN", ${pyText(b.id)}, sym, when.strftime("%Y-%m-%dT%H:%M:%S"))`, `        print("SCAN", ${pyText(b.id)}, "done", len(data))`, '        return');
  L.push('    if len(argv) < 2:');
  L.push('        sys.exit("usage: python this_file.py bars.csv [--plot]  (CSV with a header row: datetime,open,high,low,close,volume; datetime as %Y-%m-%d %H:%M:%S in UTC)")');
  L.push('    df = pd.read_csv(argv[1])');
  L.push('    df.index = pd.to_datetime(df.pop("datetime"), format="%Y-%m-%d %H:%M:%S")');
  L.push('    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})');
  L.push(`    bt = Backtest(df, ${cls}, cash=1_000_000, commission=0.0)`);
  if (btTables.length) {
    L.push('    stats = bt.run()');
    L.push('    bsv_print_tables(stats._strategy)');
  } else L.push('    bt.run()');
  L.push('    if "--plot" in argv:');
  L.push('        bt.plot(open_browser=False)  # writes an HTML chart next to this file');
  L.push('');
  L.push('');
  L.push('if __name__ == "__main__":');
  L.push('    main(sys.argv)');
  L.push('');
  L.push('# End BSV generated starter.');
  return L.join('\n') + '\n';
}

function renderNautilus(recipe) {
  // NautilusTrader (Python) alert-only Strategy. on_bar() receives completed bars; indicators are small pure-Python
  // classes seeded with the simple average (EMA) / Wilder (RSI, ATR) so values match the other BSV targets.
  const map = blockMap(recipe);
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const PXK = ['open', 'high', 'low', 'close', 'hl2', 'hlc3', 'ohlc4'];
  const isPx = (ref) => PXK.includes(ref) && !map.has(ref);
  const id = (x) => String(x).replace(/[^A-Za-z0-9_]/g, '_');
  const val = (ref, prev = false) => isPx(ref) ? `${prev ? 'pv' : 'v'}.get(${pyText(ref)}, NAN)`
    : map.has(ref) && isBoolType(map.get(ref).type) ? `(1.0 if ${prev ? 'ps' : 's'}.get(${pyText(ref)}) else 0.0)`
    : `${prev ? 'pv' : 'v'}.get(${pyText(ref)}, NAN)`;
  const bool = (ref) => map.has(ref) && isBoolType(map.get(ref).type) ? `bool(s.get(${pyText(ref)}))` : `bsv_true(${val(ref)})`;
  const htf = pyHtfUses(recipe), htfIds = new Set(htf.map(u => u.block.id)), htfSrc = [...new Set(htf.map(u => u.src.id))];
  const cls = 'Bsv' + className(recipe), nScans = recipe.blocks.filter(b => b.type === 'scanner.symbol_set' && scanOk(recipe, b));
  const tzs = [];
  for (const b of recipe.blocks) if (b.type === 'filter.session') {
    const tz = String(b.params?.timezone || 'Etc/UTC');
    if (!/^[A-Za-z_]+(\/[A-Za-z0-9_+\-]+)*$/.test(tz)) throw new Error(`Invalid timezone in ${b.id}`);
    if (!tzs.includes(tz)) tzs.push(tz);
  }
  const L = [];
  L.push('# ORIGINAL BSV STARTER — NautilusTrader alert-only strategy (Python).');
  L.push('# Generated by BSV Trader Tool Blocks. Not runtime tested by BSV on a broker or live feed. Not investment advice.');
  L.push(`# ${tsNote(safeTitle(recipe))}: pip install "nautilus_trader<2", then run: python this_file.py bars.csv`);
  L.push('# Written for the NautilusTrader 1.x Python API (checked by BSV with 1.231.0); the 2.0 release candidates change StrategyConfig.');
  L.push('# bars.csv columns: datetime (YYYY-MM-DD HH:MM:SS, read as UTC), open, high, low, close, volume.');
  L.push('# on_bar() is called once per completed bar; ALERT lines carry the bar time from the CSV. The strategy places no orders.');
  L.push("# The sample backtest uses NautilusTrader's test EUR/USD instrument (prices kept at 5 decimals) and a 15-minute bar");
  L.push('# type; replace INSTRUMENT / BAR_SPEC with your own. NautilusTrader has no chart here: plot blocks are values in self._pv.');
  L.push('');
  L.push('import csv');
  if (recipe.blocks.some(b => webhookOk(recipe, b))) L.push('import json');
  L.push('import math');
  L.push('import sys');
  L.push('from collections import deque');
  L.push('from datetime import datetime, timedelta, timezone');
  if (tzs.length) L.push('from zoneinfo import ZoneInfo');
  L.push('');
  L.push('from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig');
  L.push('from nautilus_trader.config import LoggingConfig, StrategyConfig');
  L.push('from nautilus_trader.model.currencies import USD');
  L.push('from nautilus_trader.model.data import Bar, BarType');
  L.push('from nautilus_trader.model.enums import AccountType, OmsType');
  L.push('from nautilus_trader.model.identifiers import Venue');
  L.push('from nautilus_trader.model.objects import Money');
  L.push('from nautilus_trader.test_kit.providers import TestInstrumentProvider');
  L.push('from nautilus_trader.trading.strategy import Strategy');
  L.push('');
  L.push('NAN = float("nan")');
  L.push('EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)');
  L.push('BAR_SPEC = "15-MINUTE-LAST-EXTERNAL"');
  L.push('');
  L.push('');
  L.push('def bsv_true(x):');
  L.push('    return isinstance(x, float) and math.isfinite(x) and x != 0');
  L.push('');
  L.push('');
  L.push('def bsv_fin(x):');
  L.push('    return isinstance(x, float) and math.isfinite(x)');
  L.push('');
  L.push('');
  L.push('class BsvSma:');
  L.push('    def __init__(self, n):');
  L.push('        self.n, self.w = n, deque(maxlen=n)');
  L.push('');
  L.push('    def update(self, x):');
  L.push('        self.w.append(x)');
  L.push('        return sum(self.w) / self.n if len(self.w) == self.n else NAN');
  L.push('');
  L.push('');
  L.push('class BsvEma:  # seeded with the simple average of the first n values');
  L.push('    def __init__(self, n, wilder=False):');
  L.push('        self.n, self.seed, self.val = n, [], NAN');
  L.push('        self.a = 1.0 / n if wilder else 2.0 / (n + 1)');
  L.push('        self.wilder = wilder');
  L.push('');
  L.push('    def update(self, x):');
  L.push('        if len(self.seed) < self.n:');
  L.push('            self.seed.append(x)');
  L.push('            if len(self.seed) == self.n:');
  L.push('                self.val = sum(self.seed) / self.n');
  L.push('        elif self.wilder:');
  L.push('            self.val = (self.val * (self.n - 1) + x) / self.n');
  L.push('        else:');
  L.push('            self.val = self.a * x + (1 - self.a) * self.val');
  L.push('        return self.val');
  L.push('');
  L.push('');
  L.push('class BsvRsi:  # Wilder RSI; 100 when there are no down moves, 50 when flat');
  L.push('    def __init__(self, n):');
  L.push('        self.prev, self.up, self.dn = None, BsvEma(n, wilder=True), BsvEma(n, wilder=True)');
  L.push('');
  L.push('    def update(self, x):');
  L.push('        if self.prev is None:');
  L.push('            self.prev = x');
  L.push('            return NAN');
  L.push('        u, d = self.up.update(max(x - self.prev, 0)), self.dn.update(max(self.prev - x, 0))');
  L.push('        self.prev = x');
  L.push('        if not bsv_fin(u):');
  L.push('            return NAN');
  L.push('        return 50.0 if u + d == 0 else (100.0 if d == 0 else 100.0 * u / (u + d))');
  L.push('');
  L.push('');
  L.push('class BsvAtr:  # Wilder-smoothed true range');
  L.push('    def __init__(self, n):');
  L.push('        self.prev_close, self.rma = None, BsvEma(n, wilder=True)');
  L.push('');
  L.push('    def update(self, h, l, c):');
  L.push('        pc, self.prev_close = self.prev_close, c');
  L.push('        if pc is None:');
  L.push('            return NAN');
  L.push('        return self.rma.update(max(h, pc) - min(l, pc))');
  L.push('');
  L.push('');
  if (htf.length) pyHtfLines().forEach(x => L.push(x));
  const ranges = recipe.blocks.filter(b => rangeOk(recipe, b));
  const zones = recipe.blocks.filter(b => zoneOk(recipe, b)), hooks = recipe.blocks.filter(b => webhookOk(recipe, b)), pivots = recipe.blocks.filter(b => pivotOk(recipe, b));
  if (ranges.length) pyRangeLines().forEach(x => L.push(x));
  if (pivots.length) pyPivotLines().forEach(x => L.push(x));
  pySignalLines(recipe).forEach(x => L.push(x));
  if (hooks.length) pyWebhookLines(recipe).forEach(x => L.push(x));
  L.push(`class ${cls}Config(StrategyConfig, frozen=True):`);
  L.push('    bar_type: str');
  L.push('');
  L.push('');
  L.push(`class ${cls}(Strategy):`);
  L.push(`    messages = (${alerts.map(b => pyText(b.params?.message || b.id)).join(', ')}${alerts.length === 1 ? ',' : ''})`);
  if (nScans.length) L.push('    bsv_quiet = False  # True inside bsv_scan_*(): no ALERT lines while scanning');
  L.push('');
  L.push('    def __init__(self, config):');
  L.push('        super().__init__(config)');
  L.push('        self._pv, self._ps = {}, {}');
  for (const b of recipe.blocks) {
    const q = b.params || {}, k = id(b.id);
    if (htfIds.has(b.id)) continue;
    if (b.type === 'indicator.ema') L.push(`        self.i_${k} = BsvEma(${Number(q.length) | 0})`);
    if (b.type === 'indicator.sma') L.push(`        self.i_${k} = BsvSma(${Number(q.length) | 0})`);
    if (b.type === 'indicator.rsi') L.push(`        self.i_${k} = BsvRsi(${Number(q.length) | 0})`);
    if (b.type === 'indicator.atr') L.push(`        self.i_${k} = BsvAtr(${Number(q.length) | 0})`);
  }
  tzs.forEach((tz, n) => L.push(`        self.tz${n} = ZoneInfo(${pyText(tz)})`));
  ranges.forEach(b => L.push(`        self.rg_${id(b.id)} = [False, NAN, NAN]  # ${tsNote(b.id)}: window state`));
  pivots.forEach(b => L.push(`        self.pv_${id(b.id)} = [[], [], NAN, NAN]  # ${tsNote(b.id)}: pivot state`));
  recipe.blocks.filter(b => divergenceOk(recipe, b)).forEach(b => L.push(`        self.dv_${id(b.id)} = [[], [], [], None, None]  # ${tsNote(b.id)}: divergence state`));
  htfSrc.forEach(h => L.push(`        self.htf_${id(h)} = BsvHtf(${htfMinutes(map.get(h))})  # ${tsNote(h)}: closed higher-timeframe bars only`));
  L.push('');
  L.push('    def on_start(self):');
  L.push('        self.subscribe_bars(BarType.from_str(self.config.bar_type))');
  L.push('');
  L.push('    def on_bar(self, bar):');
  L.push('        o, h, l, c = float(bar.open), float(bar.high), float(bar.low), float(bar.close)');
  L.push('        v = {"open": o, "high": h, "low": l, "close": c, "hl2": (h + l) / 2, "hlc3": (h + l + c) / 3, "ohlc4": (o + h + l + c) / 4}');
  L.push('        pv, s = self._pv, {}');
  L.push('        when = EPOCH + timedelta(microseconds=bar.ts_event // 1000)');
  htfSrc.forEach(h => L.push(`        self.htf_${id(h)}.update(bar.ts_event / 1e9, o, h, l, c)`));
  for (const b of depOrder(recipe)) {
    const q = b.params || {}, k = pyText(b.id), ik = id(b.id);
    const u = htf.find(x => x.block.id === b.id);
    if (u) { L.push(`        v[${k}] = ${pyHtfCall(u, 'self.htf_' + id(u.src.id))}  # timeframe ${tsNote(u.src.params.timeframe)}, closed bars only`); continue; }
    if (b.type === 'data.higher_timeframe' && htfSrc.includes(b.id)) continue;
    if (rangeOk(recipe, b)) { L.push(`        v[${pyText(b.id + '.high')}], v[${pyText(b.id + '.low')}] = bsv_range_step(self.rg_${ik}, ${bool(q.during)}, h, l)`); continue; }
    if (pivotOk(recipe, b)) { L.push(`        v[${pyText(b.id + '.high')}], v[${pyText(b.id + '.low')}] = bsv_pivot_step(self.pv_${ik}, ${(q.source || 'close') === 'high_low' ? 'h, l' : 'c, c'}, ${q.left}, ${q.right})`); continue; }
    if (zoneOk(recipe, b)) { L.push(`        v[${pyText('zone:' + b.id + '.high')}], v[${pyText('zone:' + b.id + '.low')}] = v[${pyText(q.source + '.high')}], v[${pyText(q.source + '.low')}]  # zone ${tsNote(q.title || b.id)} (no chart in this starter)`); continue; }
    if (webhookOk(recipe, b)) { L.push(`        s[${k}] = ${bool(q.when)}  # webhook`); continue; }
    if (sweepOk(recipe, b)) { L.push(`        s[${k}] = bsv_sweep(pv.get(${pyText(q.pivot + '.high')}, NAN), pv.get(${pyText(q.pivot + '.low')}, NAN), h, l, c, ${val(q.atr)}, ${Number(q.minAtrFraction || 0)})  # candidate only`); continue; }
    if (divergenceOk(recipe, b)) { const pq = map.get(q.pivot).params; L.push(`        s[${k}] = bsv_divergence_step(self.dv_${ik}, ${(pq.source || 'close') === 'high_low' ? 'h, l' : 'c, c'}, ${val(q.oscillator)}, ${pq.left}, ${pq.right}, ${pyText(q.direction || 'both')})`); continue; }
    if (breakoutOk(recipe, b)) { const r = map.get(q.range); L.push(`        s[${k}] = bsv_breakout(${bool(r.params.during)}, v[${pyText(r.id + '.high')}], v[${pyText(r.id + '.low')}], c, pv.get("close", NAN), ${pyText(q.direction || 'either')})`); continue; }
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi':
        L.push(`        v[${k}] = self.i_${ik}.update(v[${pyText(sourceName(q.source))}])`); break;
      case 'indicator.atr': L.push(`        v[${k}] = self.i_${ik}.update(h, l, c)`); break;
      case 'visual.plot': L.push(`        v[${pyText('plot:' + b.id)}] = ${val(q.source)}  # plot value (no chart in this starter)`); break;
      case 'alert.condition': case 'visual.table': break;
      case 'filter.session': {
        const ss = parseSession(q), n = tzs.indexOf(String(q.timezone || 'Etc/UTC'));
        L.push(`        t = when.astimezone(self.tz${n})`);
        L.push(`        m = t.hour * 60 + t.minute  # session ${tsNote(q.session || '0000-2359')} in ${tsNote(q.timezone || 'Etc/UTC')}`);
        L.push(`        s[${k}] = ${ss.start <= ss.end ? `${ss.start} <= m < ${ss.end}` : `m >= ${ss.start} or m < ${ss.end}`}`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = q.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`        s[${k}] = ${val(q.left)} ${gt} ${val(q.right)} and ${val(q.left, true).replace(/\bps\b/g, 'self._ps')} ${le} ${val(q.right, true).replace(/\bps\b/g, 'self._ps')}`);
        break;
      }
      case 'signal.threshold': {
        if (q.right === undefined && !Number.isFinite(Number(q.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`        s[${k}] = bsv_fin(${val(q.left)}) and ${val(q.left)} ${thresholdOp(q)} ${q.right !== undefined ? val(q.right) : Number(q.value)}`);
        break;
      }
      case 'signal.recent':
        L.push(`        ps = self._ps.get(${pyText('~since:' + b.id)})  # bars since ${q.signal} was last true, as of the bar before`, `        s[${k}] = ps is not None and ps < ${q.bars}`, `        s[${pyText('~since:' + b.id)}] = 0 if ${bool(q.signal)} else (None if ps is None else ps + 1)`);
        break;
      case 'signal.combine': {
        const xs = (q.signals || []).map(x => bool(x));
        L.push(`        s[${k}] = ${xs.length ? xs.join(q.mode === 'any' ? ' or ' : ' and ') : 'False'}`);
        break;
      }
      case 'scanner.symbol_set':
        if (scanOk(recipe, b)) { L.push(`        # ${tsNote(b.id)}: symbol scan of ${tsNote(scanSignal(recipe, b))}, see bsv_scan_${String(b.id).replace(/[^A-Za-z0-9_]/g, '_')}() below`); break; }
        L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)} - ${scanWhyNot(recipe, b)}`, `        v[${k}] = NAN`);
        break;
      default:
        L.push(`        # TODO unsupported block ${b.type}: ${tsNote(b.id)}`);
        L.push(isBoolType(b.type) ? `        s[${k}] = False` : `        v[${k}] = NAN`);
    }
  }
  if (alerts.length) {
    L.push(`        for msg, hit in zip(self.messages, (${alerts.map(b => bool(b.params?.when)).join(', ')}${alerts.length === 1 ? ',' : ''})):`);
    L.push(nScans.length ? '            if hit and not self.bsv_quiet:' : '            if hit:');
    L.push('                print("ALERT", when.strftime("%Y-%m-%dT%H:%M:%S"), msg)');
  }
  if (hooks.length) {
    L.push('        for name, payload in BSV_WEBHOOKS:');
    L.push('            if s.get(name):');
    L.push('                stamp = when.strftime("%Y-%m-%dT%H:%M:%S")');
    L.push('                print("WEBHOOK", stamp, bsv_webhook(payload, stamp, o, h, l, c))  # printed, not sent');
  }
  L.push('        self._pv, self._ps = v, s');
  const ntTables = tableBlocks(recipe);
  if (ntTables.length) {
    L.push('');
    L.push('    def bsv_print_tables(self):  # value panels for the last bar received');
    L.push('        v, s = self._pv, self._ps');
    for (const t of ntTables) {
      tableTodos(t, '        #').forEach(x => L.push(x));
      if (!t.fields.length) continue;
      L.push(`        print("TABLE", ${pyText(t.title)})`);
      t.fields.forEach(f => L.push(f.bool ? `        print("  " + ${pyText(f.id)}, "true" if s.get(${pyText(f.id)}) else "false")` : `        print("  " + ${pyText(f.id)}, "n/a" if not bsv_fin(${val(f.id)}) else "%.6g" % ${val(f.id)})`));
    }
    if (!ntTables.some(t => t.fields.length)) L.push('        pass');
  }
  L.push('');
  L.push('');
  L.push('def load_csv(path):');
  L.push('    with open(path, newline="") as fh:');
  L.push('        return [(datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc), float(r["open"]), float(r["high"]),');
  L.push('                 float(r["low"]), float(r["close"]), float(r.get("volume") or 0)) for r in csv.DictReader(fh)]');
  L.push('');
  L.push('');
  L.push(`def run_backtest(rows, strategy_cls=${cls}):`);
  L.push('    engine = BacktestEngine(config=BacktestEngineConfig(logging=LoggingConfig(log_level="ERROR")))');
  L.push('    venue = Venue("SIM")');
  L.push('    engine.add_venue(venue=venue, oms_type=OmsType.NETTING, account_type=AccountType.MARGIN, base_currency=USD, starting_balances=[Money(1_000_000, USD)])');
  L.push('    instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD", venue)  # INSTRUMENT: replace with your own');
  L.push('    engine.add_instrument(instrument)');
  L.push('    bar_type = BarType.from_str(f"{instrument.id}-{BAR_SPEC}")');
  L.push('    bars = []');
  L.push('    for t, o, h, l, c, vol in rows:');
  L.push('        ns = int((t - EPOCH) / timedelta(microseconds=1)) * 1000');
  L.push('        bars.append(Bar(bar_type, instrument.make_price(o), instrument.make_price(h), instrument.make_price(l), instrument.make_price(c), instrument.make_qty(vol), ns, ns))');
  L.push('    engine.add_data(bars)');
  L.push(`    strategy = strategy_cls(${cls}Config(bar_type=str(bar_type)))`);
  L.push('    engine.add_strategy(strategy)');
  L.push('    engine.run()');
  L.push('    strategy.bsv_orders = len(engine.cache.orders())  # stays 0: the strategy never submits an order');
  if (ntTables.length) L.push('    strategy.bsv_print_tables()');
  L.push('    engine.dispose()');
  L.push('    return strategy');
  L.push('');
  L.push('');
  const sid = (x) => String(x).replace(/[^A-Za-z0-9_]/g, '_');
  for (const b of nScans) L.push(`def bsv_scan_${sid(b.id)}(data):  # ${tsNote(b.id)}: data = {symbol: rows as load_csv returns}; returns [(symbol, bar time)] for each symbol whose ${tsNote(scanSignal(recipe, b))} held on its last completed bar`,
    `    class Quiet(${cls}):`, '        bsv_quiet = True  # no ALERT lines while scanning', '', '    hits = []', '    for sym, rows in data.items():', '        st = run_backtest(rows, Quiet)  # one engine run per symbol, the same on_bar() as the chart run',
    `        if rows and st._ps.get(${pyText(scanSignal(recipe, b))}):`, '            hits.append((sym, rows[-1][0]))', '    return hits', '', '');
  L.push('def main(argv):');
  for (const b of nScans) L.push(`    if len(argv) > 2 and argv[1] == "--scan":  # ${tsNote(b.id)}: python this_file.py --scan SYMBOL=bars.csv [SYMBOL=bars.csv ...]`, '        data = dict(x.split("=", 1) for x in argv[2:])',
    `        for sym, when in bsv_scan_${sid(b.id)}({k: load_csv(v) for k, v in data.items()}):`, `            print("SCAN", ${pyText(b.id)}, sym, when.strftime("%Y-%m-%dT%H:%M:%S"))`, `        print("SCAN", ${pyText(b.id)}, "done", len(data))`, '        return');
  L.push('    if len(argv) < 2:');
  L.push('        sys.exit("usage: python this_file.py bars.csv  (CSV with a header row: datetime,open,high,low,close,volume; datetime as %Y-%m-%d %H:%M:%S in UTC)")');
  L.push('    run_backtest(load_csv(argv[1]))');
  L.push('');
  L.push('');
  L.push('if __name__ == "__main__":');
  L.push('    main(sys.argv)');
  L.push('');
  L.push('# End BSV generated starter.');
  return L.join('\n') + '\n';
}

function depOrder(recipe) {
  // Dependency order for targets that need definitions before use (C++ lambdas). Falls back to recipe order on a loop.
  const map = blockMap(recipe), seen = new Map(), out = [];
  const visit = (b) => {
    const st = seen.get(b.id);
    if (st === 2) return true;
    if (st === 1) return false;
    seen.set(b.id, 1);
    for (const r of referencesFor(b)) { const d = map.get(r); if (d && !visit(d)) return false; }
    seen.set(b.id, 2); out.push(b); return true;
  };
  for (const b of recipe.blocks) if (!visit(b)) return recipe.blocks.slice();
  return out;
}

function renderSierra(recipe) {
  const map = blockMap(recipe);
  const fn = 'scsf_Bsv' + className(recipe);
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const inds = recipe.blocks.filter(b => ['indicator.ema', 'indicator.sma', 'indicator.rsi', 'indicator.atr'].includes(b.type));
  if (plots.length + inds.length > 60) throw new Error('Sierra Chart supports up to 60 subgraphs per study');
  const base = { open: 'SC_OPEN', high: 'SC_HIGH', low: 'SC_LOW', close: 'SC_LAST' };
  const priceAt = (ref, at) => {
    const B = k => `sc.BaseDataIn[${base[k]}][${at}]`;
    if (base[ref]) return B(ref);
    if (ref === 'hl2') return `(${B('high')} + ${B('low')}) / 2.0f`;
    if (ref === 'hlc3') return `(${B('high')} + ${B('low')} + ${B('close')}) / 3.0f`;
    return `(${B('open')} + ${B('high')} + ${B('low')} + ${B('close')}) / 4.0f`;
  };
  const val = (ref, at) => isPrice(ref) ? priceAt(ref, at) : (isBoolType(map.get(ref)?.type) ? `(S_${ref}(${at}) ? 1.0f : 0.0f)` : `V_${ref}(${at})`);
  const bool = (ref, at) => isBoolType(map.get(ref)?.type) ? `S_${ref}(${at})` : `(${val(ref, at)} != 0.0f)`;
  const colors = ['RGB(30,144,255)', 'RGB(255,165,0)', 'RGB(50,205,50)', 'RGB(255,0,255)', 'RGB(255,215,0)', 'RGB(0,255,255)'];
  const sg = new Map();
  plots.forEach((p, k) => sg.set(p.id, k));
  inds.forEach((b, k) => sg.set(b.id, plots.length + k));
  const L = [];
  L.push('// ORIGINAL BSV STARTER — Sierra Chart ACSIL custom study (C++). Build with Analysis >> Build Custom Studies DLL before use.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// Save as ACS_Source\\Bsv${className(recipe)}.cpp, build the DLL, then add the study "${'BSV — ' + safeTitle(recipe)}" to a chart.`);
  L.push('#include "sierrachart.h"');
  L.push('');
  L.push(`SCDLLName(${q('BSV ' + safeTitle(recipe))})`);
  L.push('');
  L.push(`SCSFExport ${fn}(SCStudyInterfaceRef sc)`);
  L.push('{');
  for (const p of plots) L.push(`    SCSubgraphRef Sg_${p.id} = sc.Subgraph[${sg.get(p.id)}];`);
  for (const b of inds) L.push(`    SCSubgraphRef Sg_${b.id} = sc.Subgraph[${sg.get(b.id)}]; // calculation only (hidden)`);
  L.push(`    const int BSV_WARMUP = ${warmup(recipe)};`);
  L.push('');
  L.push('    if (sc.SetDefaults)');
  L.push('    {');
  L.push(`        sc.GraphName = ${q('BSV — ' + safeTitle(recipe))};`);
  L.push(`        sc.StudyDescription = ${q('Original BSV generated starter. Not runtime tested by BSV. Not investment advice.')};`);
  L.push('        sc.AutoLoop = 1;');
  L.push(`        sc.GraphRegion = ${recipe.overlay ? 0 : 1};`);
  plots.forEach((p, k) => {
    L.push(`        Sg_${p.id}.Name = ${q(p.params?.title || p.params?.source || p.id)};`);
    L.push(`        Sg_${p.id}.DrawStyle = DRAWSTYLE_LINE;`);
    L.push(`        Sg_${p.id}.PrimaryColor = ${colors[k % colors.length]};`);
  });
  for (const b of inds) { L.push(`        Sg_${b.id}.Name = ${q(b.id)};`); L.push(`        Sg_${b.id}.DrawStyle = DRAWSTYLE_IGNORE;`); }
  L.push('        return;');
  L.push('    }');
  L.push('');
  L.push('    // Built-in calculations run on every bar (automatic looping).');
  for (const b of inds) {
    const p = b.params || {};
    const src = b.type === 'indicator.atr' ? null : sourceName(p.source);
    let input = src && base[src] ? `sc.BaseDataIn[${base[src]}]` : null;
    if (src && !base[src]) {
      L.push(`    Sg_${b.id}.Arrays[9][sc.Index] = ${priceAt(src, 'sc.Index')}; // ${src} source`);
      input = `Sg_${b.id}.Arrays[9]`;
    }
    if (b.type === 'indicator.ema') L.push(`    sc.ExponentialMovAvg(${input}, Sg_${b.id}, ${p.length});`);
    if (b.type === 'indicator.sma') L.push(`    sc.SimpleMovAvg(${input}, Sg_${b.id}, ${p.length});`);
    if (b.type === 'indicator.rsi') L.push(`    sc.RSI(${input}, Sg_${b.id}, MOVAVGTYPE_WILDERS, ${p.length});`);
    if (b.type === 'indicator.atr') L.push(`    sc.ATR(sc.BaseDataIn, Sg_${b.id}, ${p.length}, MOVAVGTYPE_WILDERS);`);
  }
  L.push('');
  L.push('    // Block values and signals by absolute bar index (i). Defined in dependency order.');
  for (const b of depOrder(recipe)) {
    const p = b.params || {};
    switch (b.type) {
      case 'indicator.ema': case 'indicator.sma': case 'indicator.rsi': case 'indicator.atr':
        L.push(`    auto V_${b.id} = [&](int i) -> float { return Sg_${b.id}[i]; };`);
        break;
      case 'filter.session': {
        const ss = parseSession(p);
        L.push(`    // TODO ${b.id}: bar times use the chart time zone (Global Settings or chart setting); convert session ${p.session || ''} from ${p.timezone || 'Etc/UTC'}.`);
        L.push(`    auto S_${b.id} = [&](int i) -> bool { int m = sc.BaseDateTimeIn[i].GetTimeInSeconds() / 60; return ${ss.start <= ss.end ? `m >= ${ss.start} && m < ${ss.end}` : `m >= ${ss.start} || m < ${ss.end}`}; };`);
        break;
      }
      case 'signal.cross': {
        const [gt, le] = p.direction === 'below' ? ['<', '>='] : ['>', '<='];
        L.push(`    auto S_${b.id} = [&](int i) -> bool { return ${val(p.left, 'i')} ${gt} ${val(p.right, 'i')} && ${val(p.left, 'i - 1')} ${le} ${val(p.right, 'i - 1')}; };`);
        break;
      }
      case 'signal.threshold':
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        L.push(`    auto S_${b.id} = [&](int i) -> bool { return ${val(p.left, 'i')} ${thresholdOp(p)} ${p.right !== undefined ? val(p.right, 'i') : Number(p.value)}; };`);
        break;
      case 'signal.recent':
        L.push(`    auto S_${b.id} = [&](int i) -> bool { return ${orOf(p.bars, k => `(i >= ${k} && ${bool(p.signal, `i - ${k}`)})`, ' || ')}; };`);
        break;
      case 'signal.combine':
        L.push(`    auto S_${b.id} = [&](int i) -> bool { return ${(p.signals || []).map(x => bool(x, 'i')).join(p.mode === 'any' ? ' || ' : ' && ') || 'false'}; };`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        if (isBoolType(b.type)) L.push(`    auto S_${b.id} = [&](int i) -> bool { return false; }; // TODO unsupported block ${b.type}: ${b.id}`);
        else L.push(`    auto V_${b.id} = [&](int i) -> float { return 0.0f; }; // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  L.push('');
  L.push('    if (sc.Index < BSV_WARMUP) return;');
  for (const p of plots) L.push(`    Sg_${p.id}[sc.Index] = ${val(p.params?.source, 'sc.Index')};`);
  if (alerts.length) {
    L.push('');
    L.push('    // Alerts: evaluate the last closed bar once, only on the newest bar and not during a full recalculation.');
    L.push('    if (sc.Index == sc.ArraySize - 1 && !sc.IsFullRecalculation)');
    L.push('    {');
    L.push('        const int c = sc.Index - 1;');
    alerts.forEach((a, k) => {
      L.push(`        int& last_${a.id} = sc.GetPersistentInt(${k + 1});`);
      L.push(`        if (c > BSV_WARMUP && last_${a.id} != c && ${bool(a.params?.when, 'c')}) { last_${a.id} = c; sc.AddAlertLine(${q(String(a.params?.message || a.id).replace(/[\r\n]/g, ' '))}, 0); }`);
    });
    L.push('    }');
  }
  L.push('}');
  L.push('');
  L.push('// Build the DLL, resolve every marked item above, then test on history and in replay or simulation before relying on it.');
  return L.join('\n') + '\n';
}

function prtName(id, used) {
  let n = 'v' + id.split('_').map(x => x.charAt(0).toUpperCase() + x.slice(1)).join('').replace(/[^A-Za-z0-9]/g, '');
  while (used.has(n.toLowerCase())) n += 'X';
  used.add(n.toLowerCase());
  return n;
}

function renderProRealTime(recipe) {
  const map = blockMap(recipe);
  const used = new Set();
  const nm = new Map(recipe.blocks.map(b => [b.id, prtName(b.id, used)]));
  const plots = recipe.blocks.filter(b => b.type === 'visual.plot');
  const alerts = recipe.blocks.filter(b => b.type === 'alert.condition');
  const price = { open: 'Open', high: 'High', low: 'Low', close: 'Close', hl2: '((High + Low) / 2)', hlc3: '((High + Low + Close) / 3)', ohlc4: '((Open + High + Low + Close) / 4)' };
  const ref = (r) => isPrice(r) ? price[r] : nm.get(r);
  const bool = (r) => isBoolType(map.get(r)?.type) ? nm.get(r) : `(${ref(r)} <> 0)`;
  const colors = ['30,144,255', '255,165,0', '50,205,50', '255,0,255', '255,215,0', '0,255,255'];
  const L = [];
  L.push('// ORIGINAL BSV STARTER — ProRealTime ProBuilder indicator. Paste into a new indicator (Indicators >> New >> Creation by programming) and validate.');
  L.push('// Generated by BSV Trader Tool Blocks. Not runtime tested by BSV. Not investment advice.');
  L.push(`// ${safeTitle(recipe)} — add it ${recipe.overlay ? 'on the price chart' : 'below the price chart'}.`);
  L.push('// Block variables use names without underscores (block id -> name):');
  for (const b of recipe.blocks) L.push(`//   ${b.id} -> ${nm.get(b.id)}`);
  L.push('');
  for (const b of depOrder(recipe)) {
    const p = b.params || {}, n = nm.get(b.id);
    switch (b.type) {
      case 'indicator.ema': L.push(`${n} = ExponentialAverage[${p.length}](${price[sourceName(p.source)]})`); break;
      case 'indicator.sma': L.push(`${n} = Average[${p.length}](${price[sourceName(p.source)]})`); break;
      case 'indicator.rsi': L.push(`${n} = RSI[${p.length}](${price[sourceName(p.source)]})`); break;
      case 'indicator.atr': L.push(`${n} = AverageTrueRange[${p.length}](Close)`); break;
      case 'filter.session': {
        const ss = parseSession(p);
        const hhmmss = m => String(Math.floor(m / 60)).padStart(2, '0') + String(m % 60).padStart(2, '0') + '00';
        L.push(`// TODO ${b.id}: Time is the bar time in the platform time zone; convert session ${p.session || ''} from ${p.timezone || 'Etc/UTC'} and check bar open vs close time.`);
        L.push(`${n} = ${ss.start <= ss.end ? `(Time >= ${hhmmss(ss.start)} AND Time < ${hhmmss(ss.end)})` : `(Time >= ${hhmmss(ss.start)} OR Time < ${hhmmss(ss.end)})`}`);
        break;
      }
      case 'signal.cross':
        L.push(`${n} = (${ref(p.left)} CROSSES ${p.direction === 'below' ? 'UNDER' : 'OVER'} ${ref(p.right)})`);
        break;
      case 'signal.threshold': {
        if (p.right === undefined && !Number.isFinite(Number(p.value))) throw new Error(`Invalid threshold in ${b.id}`);
        const op = { '==': '=', '!=': '<>' }[thresholdOp(p)] || thresholdOp(p);
        L.push(`${n} = (${ref(p.left)} ${op} ${p.right !== undefined ? ref(p.right) : Number(p.value)})`);
        break;
      }
      case 'signal.recent':
        L.push(`${n} = (${orOf(p.bars, k => `${bool(p.signal)}[${k}]`, ' OR ')})`);
        break;
      case 'signal.combine':
        L.push(`${n} = ${(p.signals || []).length ? '(' + p.signals.map(bool).join(p.mode === 'any' ? ' OR ' : ' AND ') + ')' : '0'}`);
        break;
      case 'visual.plot': case 'alert.condition':
        break;
      default:
        L.push(`${n} = 0 // TODO unsupported block ${b.type}: ${b.id}`);
    }
  }
  const outs = [];
  plots.forEach((p, k) => outs.push(`${ref(p.params?.source)} COLOURED(${colors[k % colors.length]}) AS ${q(p.params?.title || p.params?.source || p.id)}`));
  if (alerts.length) {
    L.push('');
    L.push('// Alerts: ProBuilder indicators cannot raise alerts themselves; you create the alert in ProRealTime on an indicator line.');
    for (const a of alerts) {
      const n = nm.get(a.id), msg = String(a.params?.message || a.id).replace(/[\r\n]/g, ' ');
      L.push(`${n} = ${bool(a.params?.when)} // ${msg}`);
      if (recipe.overlay) {
        const down = signalDown(map, a.params?.when);
        L.push(`IF ${n} THEN`, down ? `  DRAWARROWDOWN(barindex, High) COLOURED(220,80,80)` : `  DRAWARROWUP(barindex, Low) COLOURED(50,205,50)`, 'ENDIF');
      } else {
        outs.push(`${n} AS ${q('Alert: ' + msg.replace(/"/g, ' ').slice(0, 60))}`);
      }
    }
    if (recipe.overlay) L.push(`// TODO alerts: this overlay only draws markers. For an alert, create a second indicator below the chart that returns ${alerts.map(a => nm.get(a.id)).join(', ')} (0/1) and set the alert on value 1.`);
    else L.push('// Set each alert on its 0/1 line (value = 1). Lines update with the live bar; prefer bar-close alert options where available.');
  }
  L.push('');
  L.push('RETURN ' + (outs.length ? outs.join(', ') : '0 AS "no output"'));
  return L.join('\n') + '\n';
}
