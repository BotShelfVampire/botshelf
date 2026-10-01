import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {decodeSearchState,encodeSearchState,mergePublicCatalogues,searchPublicCatalogue} from './search-core.mjs';

const raw=JSON.parse(await readFile(new URL('../traders-studio-v3-1-20261001/public/trading/assets/catalog.json',import.meta.url),'utf8'));
const records=mergePublicCatalogues(raw.map(record=>({record,scope:'trading',source:'curated'})));
assert.equal(records.length,39,'review catalogue count changed; update the test fixture expectations');

const cases=[
  [
    "RSI",
    "everget-adaptive-rsi-moving-average"
  ],
  [
    "相対力指数",
    "everget-adaptive-rsi-moving-average"
  ],
  [
    "adaptive RSI",
    "everget-adaptive-rsi-moving-average"
  ],
  [
    "Simple Moving Average",
    "bachini-sma"
  ],
  [
    "cTrader SMA",
    "spotware-sample-sma"
  ],
  [
    "Backtrader SMA",
    "backtrader-sma"
  ],
  [
    "QuantConnect LEAN",
    "lean-basic-template"
  ],
  [
    "Freqtrade MACD RSI",
    "freqtrade-simple"
  ],
  [
    "Spike Trader",
    "earnforex-spike-trader"
  ],
  [
    "MT5 EA",
    "earnforex-spike-trader"
  ],
  [
    "breakout sniper",
    "bachini-breakout-sniper"
  ],
  [
    "ブレイクアウト",
    "bachini-breakout-sniper"
  ],
  [
    "crossover",
    "bachini-crossover"
  ],
  [
    "fear greed",
    "bachini-fear-greed"
  ],
  [
    "gaussian regression",
    "bachini-gaussian-regression"
  ],
  [
    "price channels",
    "bachini-price-channels"
  ],
  [
    "acceleration bands",
    "everget-acceleration-bands"
  ],
  [
    "awesome oscillator",
    "everget-awesome-oscillator"
  ],
  [
    "butterworth",
    "everget-butterworth-filter"
  ],
  [
    "cyber cycle",
    "everget-ehlers-cyber-cycle"
  ],
  [
    "forecast oscillator",
    "everget-forecast-oscillator"
  ],
  [
    "range candles",
    "everget-range-candles"
  ],
  [
    "STARC",
    "everget-stoller-average-range-channels"
  ],
  [
    "vortex bands",
    "everget-vortex-bands"
  ],
  [
    "mean absolute deviation",
    "everget-mean-absolute-deviation-bands"
  ],
  [
    "移動平均 channel",
    "everget-moving-average-channel"
  ],
  [
    "VWMA WMA",
    "everget-stoller-average-range-channels"
  ],
  [
    "derivative oscillator",
    "everget-derivative-oscillator"
  ],
  [
    "alpha decreasing exponential",
    "everget-alpha-decreasing-exponential-moving-average"
  ],
  [
    "interquartile range",
    "everget-interquartile-range-bands"
  ],
  [
    "Kirshenbaum",
    "everget-kirshenbaum-bands"
  ],
  [
    "Dorsey inertia",
    "everget-dorsey-inertia"
  ],
  [
    "double exponential moving average",
    "everget-double-exponential-moving-average"
  ],
  [
    "price action spike",
    "earnforex-spike-trader"
  ]
];
for(const [query,expectedId] of cases){
  const ids=searchPublicCatalogue(records,{q:query}).map(record=>record.id);
  assert.ok(ids.includes(expectedId),query+' should include '+expectedId+'; got '+ids.slice(0,5).join(','));
}
assert.equal(searchPublicCatalogue(records,{q:'unicorn banana impossible'}).length,0,'true zero-result query must stay empty');
assert.equal(searchPublicCatalogue(records,{q:'SMA',platform:'cTrader'})[0]?.id,'spotware-sample-sma');
assert.equal(searchPublicCatalogue(records,{q:'',pricing:'free'}).length,records.length);

const hidden=mergePublicCatalogues([{record:{id:'secret',title:'Secret RSI',mode:'free',status:'draft',visibility:'private',reviewStatus:'approved'},scope:'trading',source:'community'}]);
assert.equal(hidden.length,0,'draft/private community records must not enter public search');

const published={id:'community-rsi',title:'Community RSI',mode:'one_time',status:'published',visibility:'public',reviewStatus:'approved',revision:2};
const merged=mergePublicCatalogues([
 {record:{...published,revision:1},scope:'trading',source:'community'},
 {record:published,scope:'trading',source:'community'}
]);
assert.equal(merged.length,1,'scope+id duplicates must collapse');
assert.equal(merged[0].revision,2,'newest public revision must win');
assert.equal(merged[0].pricing,'one_time');

const regressions=mergePublicCatalogues([
 {record:{id:'support-resistance',title:'Support & Resistance',mode:'free',text:{ja:{purpose:'支持線と抵抗線'}}},scope:'trading',source:'curated'},
 {record:{id:'levels-paths',title:'Levels & Paths',mode:'free',text:{en:{purpose:'Support & Resistance scenarios'}}},scope:'ai',source:'curated'},
 {record:{id:'atr-trailing',title:'ATR Trailing Stop',mode:'free',text:{ja:{purpose:'損切り管理と追従ストップ'}}},scope:'trading',source:'curated'},
 {record:{id:'hold-reply',title:'Hold reply inbox',mode:'free',text:{ja:{purpose:'メール返信の下書き'}}},scope:'ai',source:'curated'},
 {record:{id:'ollama-local',title:'Ollama local kit',mode:'free',text:{ja:{purpose:'ローカル環境で実行'}}},scope:'build',source:'curated'},
 {record:{id:'position-sizer',title:'Position Sizer',mode:'free',text:{ja:{purpose:'ポジションサイズとロット計算'}}},scope:'trading',source:'curated'}
]);
assert.equal(searchPublicCatalogue(regressions,{q:'Support & Resistance'})[0]?.id,'support-resistance','exact title must outrank a summary mention');
assert.equal(searchPublicCatalogue(regressions,{q:'損切り管理'})[0]?.id,'atr-trailing');
assert.equal(searchPublicCatalogue(regressions,{q:'トレーリングストップ'})[0]?.id,'atr-trailing');
assert.equal(searchPublicCatalogue(regressions,{q:'メール返信'})[0]?.id,'hold-reply');
assert.equal(searchPublicCatalogue(regressions,{q:'ローカル環境'})[0]?.id,'ollama-local');
assert.equal(searchPublicCatalogue(regressions,{q:'ポジションサイズ'})[0]?.id,'position-sizer');

const roundTrip=decodeSearchState(encodeSearchState({q:'ＭＴ５　ＥＡ',scope:'trading',platform:'MT5',pricing:'one_time'}));
assert.deepEqual(roundTrip,{q:'ＭＴ５　ＥＡ',scope:'trading',kind:'',platform:'MT5',pricing:'one_time'});
console.log(JSON.stringify({catalogueRecords:records.length,queryCases:cases.length,totalAssertions:cases.length+15,status:'pass'}));
