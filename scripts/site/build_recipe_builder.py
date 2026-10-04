#!/usr/bin/env python3
"""Logged-in browser recipe builder for the Trader category.

- /trading/items/bsv-builder.html   gated page (existing /trading/items/* edge gate)
- /trading/sources/bsv-builder.<hash>.js  gated script: browser port of trader-toolkit/generator/render.mjs
  (render functions copied verbatim from the repo; only the Node CLI head is dropped) + starter recipes + UI
- /trading/tools/bsv-builder.html   public summary page (no generator code)
- entry block in /trading/build/, search row, sitemap URL

Run after build_live_toolkit.py:  python3 scripts/site/build_recipe_builder.py --site <tree>
Test parity:                      node scripts/site/test_builder_parity.mjs <tree>
"""
import argparse, hashlib, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_live_toolkit as blt  # noqa: E402

esc, both, T = blt.esc, blt.both, blt.T
SLUG = "bsv-builder"
PRICE = ["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]
# target id -> render function in trader-toolkit/generator/render.mjs (labels / extensions come from build_live_toolkit.TARGETS)
TARGET_FN = {"pine-v6": "renderPine", "mql5": "renderMql5", "ctrader": "renderCTrader", "mql4": "renderMql4", "ctrader-python": "renderCTraderPython",
             "bookmap-python": "renderBookmapPython", "ninjatrader": "renderNinja", "quantower": "renderQuantower",
             "sierra-acsil": "renderSierra", "prorealtime": "renderProRealTime",
             "gocharting-lipi": "renderLipi", "motivewave": "renderMotiveWave", "vela": "renderVela", "jforex": "renderJForex", "easylanguage": "renderEasyLanguage", "atas": "renderAtas", "amibroker": "renderAmiBroker", "thinkscript": "renderThinkScript", "tradovate": "renderTradovate", "backtrader": "renderBacktrader", "backtesting-py": "renderBacktestingPy", "nautilus": "renderNautilus"}
# Builder-only targets (cycle 9 rule): shown as builder tabs, not as pre-generated starters on recipe pages,
# so recipe-page copy and platform lists stay unchanged until the owner approves new copy.
BUILDER_EXTRA_TARGETS = []


UI_JS = r"""
var PRICE=__PRICE__;
var FIELDS={
 'indicator.ema':[['source','price'],['length','int']],'indicator.sma':[['source','price'],['length','int']],
 'indicator.rsi':[['source','price'],['length','int']],'indicator.atr':[['length','int']],
 'filter.session':[['session','text'],['timezone','text']],
 'signal.cross':[['left','ref'],['right','ref'],['direction','sel:above|below']],
 'signal.threshold':[['left','ref'],['op','sel:>|>=|<|<=|==|!='],['value','num']],
 'signal.combine':[['mode','sel:all|any'],['signals','list']],
 'visual.plot':[['source','ref'],['title','text']],
 'alert.condition':[['when','ref'],['message','text']]};
var DEFAULTS={'indicator.ema':{source:'close',length:20},'indicator.sma':{source:'close',length:50},'indicator.rsi':{source:'close',length:14},'indicator.atr':{length:14},
 'filter.session':{session:'0800-1200',timezone:'Europe/London'},'signal.cross':{left:'',right:'',direction:'above'},'signal.threshold':{left:'',op:'>=',value:50},
 'signal.combine':{mode:'all',signals:[]},'visual.plot':{source:'',title:''},'alert.condition':{when:'',message:'BSV recipe alert'}};
var EXT=__EXT__;
var KEY='bsv-rb-draft-v1';
function $(s){return document.querySelector(s)}
function el(tag,attrs,kids){var e=document.createElement(tag);if(attrs)Object.keys(attrs).forEach(function(k){if(k==='text')e.textContent=attrs[k];else e.setAttribute(k,attrs[k])});(kids||[]).forEach(function(c){e.appendChild(c)});return e}
var state={recipe:null,target:'pine-v6'};
function clone(o){return JSON.parse(JSON.stringify(o))}
function save(){try{localStorage.setItem(KEY,JSON.stringify(state.recipe))}catch(e){}}
function uniqueId(base){var ids=state.recipe.blocks.map(function(b){return b.id}),i=1,id=base;while(ids.indexOf(id)>=0){i++;id=base+'_'+i}return id}
function idsList(){var dl=$('#rb-ids');dl.textContent='';state.recipe.blocks.map(function(b){return b.id}).concat(PRICE).forEach(function(v){dl.appendChild(el('option',{value:v}))})}
function field(b,f){var key=f[0],kind=f[1],val=b.params[key],id='rb-'+b.id+'-'+key,inp;
 if(kind==='price'){inp=el('select',{id:id});PRICE.forEach(function(p){var o=el('option',{value:p,text:p});if(p===(val||'close'))o.selected=true;inp.appendChild(o)})}
 else if(kind.indexOf('sel:')===0){inp=el('select',{id:id});kind.slice(4).split('|').forEach(function(p){var o=el('option',{value:p,text:p});if(p===String(val))o.selected=true;inp.appendChild(o)})}
 else{inp=el('input',{id:id,type:(kind==='int'||kind==='num')?'number':'text'});if(kind==='ref')inp.setAttribute('list','rb-ids');if(kind==='int')inp.setAttribute('step','1');if(kind==='num')inp.setAttribute('step','any');
  inp.value=kind==='list'?(val||[]).join(', '):(val==null?'':String(val));if(kind==='list')inp.setAttribute('placeholder','id_a, id_b')}
 inp.addEventListener('change',function(){var v=inp.value;if(kind==='int')v=parseInt(v,10);else if(kind==='num')v=Number(v);else if(kind==='list')v=v.split(',').map(function(s){return s.trim()}).filter(Boolean);b.params[key]=v;update()});
 return el('label',{'class':'rb-field'},[el('span',{text:key}),inp])}
function blockRow(b,i){var box=el('fieldset',{'class':'rb-block',id:'rb-blk-'+b.id});
 var idIn=el('input',{type:'text',value:b.id,'aria-label':'block id',pattern:'[a-z][a-z0-9_]*'});idIn.value=b.id;
 idIn.addEventListener('change',function(){var old=b.id,nv=idIn.value.trim();b.id=nv;state.recipe.blocks.forEach(function(o){Object.keys(o.params||{}).forEach(function(k){if(o.params[k]===old)o.params[k]=nv;if(Array.isArray(o.params[k]))o.params[k]=o.params[k].map(function(x){return x===old?nv:x})})});draw()});
 var typeSel=el('select',{'aria-label':'block type'});TYPES.forEach(function(t){var o=el('option',{value:t,text:t+(FIELDS[t]?'':' (TODO in output)')});if(t===b.type)o.selected=true;typeSel.appendChild(o)});
 typeSel.addEventListener('change',function(){b.type=typeSel.value;b.params=clone(DEFAULTS[b.type]||{});draw()});
 var tools=el('div',{'class':'rb-tools'},[mk('↑',function(){if(i>0){var a=state.recipe.blocks;a.splice(i-1,0,a.splice(i,1)[0]);draw()}}),mk('↓',function(){var a=state.recipe.blocks;if(i<a.length-1){a.splice(i+1,0,a.splice(i,1)[0]);draw()}}),mk('×',function(){state.recipe.blocks.splice(i,1);draw()})]);
 box.appendChild(el('legend',{},[el('span',{text:'#'+(i+1)+' '}),el('span',{'class':'rb-tbadge',id:'rb-tb-'+b.id,hidden:''})]));
 box.appendChild(el('div',{'class':'rb-head'},[el('label',{'class':'rb-field'},[el('span',{text:'id'}),idIn]),el('label',{'class':'rb-field'},[el('span',{text:'type'}),typeSel]),tools]));
 if(FIELDS[b.type]){box.appendChild(el('div',{'class':'rb-params'},FIELDS[b.type].map(function(f){return field(b,f)})))}
 else{var ta=el('textarea',{rows:'3','aria-label':'params JSON','class':'rb-raw'});ta.value=JSON.stringify(b.params||{});ta.addEventListener('change',function(){try{b.params=JSON.parse(ta.value);ta.classList.remove('rb-bad');update()}catch(e){ta.classList.add('rb-bad')}});
  box.appendChild(el('p',{'class':'small',text:'This block type is kept as a TODO marker in the generated code. Params (JSON):'}));box.appendChild(ta)}
 return box}
function mk(t,fn){var b=el('button',{type:'button','class':'btn small-btn',text:t});b.addEventListener('click',fn);return b}
function draw(){var r=state.recipe;$('#rb-name').value=r.name||'';$('#rb-desc').value=r.description||'';$('#rb-overlay').checked=!!r.overlay;
 var c=$('#rb-blocks');c.textContent='';r.blocks.forEach(function(b,i){c.appendChild(blockRow(b,i))});idsList();update()}
function update(){var r=state.recipe,out='',err='';save();$('#rb-json').value=JSON.stringify(r,null,2);
 try{var copy=clone(r);validateRecipe(copy);out=RENDER[state.target](copy)}catch(e){err=String(e&&e.message||e)}
 $('#rb-err').hidden=!err;$('#rb-err').textContent=err?('Fix this first: '+err):'';
 $('#rb-out').textContent=out;var todo=(out.match(/TODO/g)||[]).length;$('#rb-todo').textContent=out?('TODO markers: '+todo):'';renderHints(out);renderLint();renderChecklist();
 ['#rb-copy','#rb-dl'].forEach(function(s){$(s).disabled=!out})}
function load(r){state.recipe=clone(r);if(!Array.isArray(state.recipe.blocks))state.recipe.blocks=[];draw()}
function toast(t){var e=$('#toast');if(!e)return;e.textContent=t;e.hidden=false;setTimeout(function(){e.hidden=true},1600)}
function download(name,text){var a=el('a',{href:URL.createObjectURL(new Blob([text],{type:'text/plain'})),download:name});document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},500)}
function fileBase(){return (state.recipe.name||'bsv-recipe').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'bsv-recipe'}
// ---- builder v2: per-block TODO hints + shareable recipe JSON (config only, no generated code, no server storage)
var SHARE_MAX=6000,PENDING='bsv-rb-pending-share',PREV=KEY+'-prev';
var HINTS={
 'filter.session':['Session windows depend on timezone: MT4/MT5 use broker server time; the cTrader Python and Bookmap outputs use UTC; NinjaTrader, Sierra Chart and ProRealTime use the platform or chart time zone; the GoCharting output converts with hour()/minute(), the MotiveWave output with java.time the Vela output with Intl and the JForex output with java.time, all in the recipe time zone; the TradeStation output uses Time (bar close, chart time zone); the ATAS output reads the candle open time as UTC and converts it with TimeZoneInfo; the AmiBroker output uses TimeNum() in the database time zone the thinkorswim output uses SecondsFromTime/SecondsTillTime in US Eastern time, and the Tradovate output converts the bar time to the recipe time zone with Intl.DateTimeFormat, the backtrader output reads the CSV bar time as UTC and converts it with zoneinfo, the Backtesting.py output reads it as UTC and converts it with pandas, and the NautilusTrader output reads it as UTC and converts it with zoneinfo. Convert the session before relying on alerts.','時間帯の判定はタイムゾーン次第です。MT4・MT5はブローカーのサーバー時間、cTrader PythonとBookmapの出力はUTC、NinjaTrader・Sierra Chart・ProRealTimeはプラットフォームまたはチャートのタイムゾーン、GoChartingの出力はhour()・minute()、MotiveWaveの出力はjava.time、Velaの出力はIntl、JForexの出力はjava.timeを使い、いずれもレシピのタイムゾーンで判定します。TradeStationの出力は、チャートのタイムゾーンでの足の終了時刻（Time）で判定します。ATASの出力は、足の開始時刻をUTCとして読み、TimeZoneInfoでレシピのタイムゾーンに変換します。AmiBrokerの出力はデータベースのタイムゾーンのTimeNum()、thinkorswimの出力は米国東部時間のSecondsFromTime/SecondsTillTimeで判定し、Tradovateの出力はIntl.DateTimeFormatで足の時刻をレシピのタイムゾーンに換算し、backtraderの出力はCSVの足の時刻をUTCとして読みzoneinfoで換算し、Backtesting.pyの出力はUTCとして読みpandasで換算し、NautilusTraderの出力はUTCとして読みzoneinfoで換算します。アラートに使う前に時間帯を換算してください。'],
 'signal.cross':['Cross = left is above (or below) right on this bar but was not on the previous bar. Where a target leaves it as TODO, compare current and previous values of both inputs.','クロスは「この足で左が右を上抜け（下抜け）し、1本前はそうでなかった」状態です。TODOが残る出力先では、両方の値の現在と1本前を比べて判定します。'],
 'signal.threshold':['Compares one value with a fixed number. Check the value range on your platform (for example RSI 0-100).','1つの値を固定の数値と比べます。プラットフォームでの値の範囲（例：RSIは0〜100）を確認してください。'],
 'signal.combine':['all = every listed signal is true on the same bar; any = at least one. Referenced ids must exist above this block.','all は列挙したシグナルが同じ足ですべて成立、any は1つ以上成立。参照するidはこのブロックより上に必要です。'],
 'indicator.ema':['If the source is ohlc4, some targets fall back to close (see the TODO); compute (open+high+low+close)/4 or pick hl2 / hlc3.','sourceがohlc4の場合、一部の出力先はcloseで代用します（TODO参照）。(始値+高値+安値+終値)/4を自分で計算するか、hl2・hlc3を選んでください。'],
 'indicator.sma':['If the source is ohlc4, some targets fall back to close (see the TODO).','sourceがohlc4の場合、一部の出力先はcloseで代用します（TODO参照）。'],
 'indicator.rsi':['If the source is ohlc4, some targets fall back to close (see the TODO).','sourceがohlc4の場合、一部の出力先はcloseで代用します（TODO参照）。'],
 'indicator.atr':['ATR smoothing differs by platform (Wilder vs simple); compare values with the platform built-in ATR.','ATRの平滑化方法はプラットフォームで異なります（Wilder／単純平均）。組み込みのATRと値を見比べてください。'],
 'visual.plot':['Plots draw a value block as a line. On Bookmap, overlay lines are price levels.','値ブロックを線として描きます。Bookmapでは重ね表示の線は価格水準として描かれます。'],
 'alert.condition':['MQL4 and cTrader Python alert once per closed bar; Pine needs an alert set up in TradingView. Check alert frequency before use.','MQL4とcTrader Pythonは確定足ごとに1回通知します。PineはTradingView側でアラート設定が必要です。使う前に通知頻度を確認してください。'],
 'alert.webhook':['backtrader, Backtesting.py and NautilusTrader print the JSON payload ({{symbol}}, {{timeframe}}, {{time}}, {{open}}, {{high}}, {{low}}, {{close}} filled in) once per completed bar; they never send it. Tradovate: W dots on the closed bar plus the same JSON text built in per-bar state, checked in the BSV stub of the documented API (not run on Tradovate); never sent. Elsewhere TODO. Webhooks: Pine alert() plus a TradingView webhook URL. On MT4/MT5, WebRequest only runs in Expert Advisors/scripts (not indicators) and the URL must be allow-listed. Never put secrets in the message.','backtrader・Backtesting.py・NautilusTraderは、確定した足ごとにJSONペイロード（{{symbol}}などを埋めたもの）を表示します。送信はしません。Tradovateは確定した足にWの点を描き、同じJSONを足ごとの状態に作ります（BSVの公開API スタブで確認、Tradovate上では未実行）。送信はしません。ほかはTODOです。Webhook：PineはalertとTradingViewのWebhook URLで送ります。MT4・MT5のWebRequestはEA・スクリプトでのみ動き（インジケーター不可）、URLの許可設定が必要です。メッセージに秘密情報を入れないでください。'],
 'data.higher_timeframe':['Closed higher-timeframe bars only. backtrader, Backtesting.py and NautilusTrader: computed and checked in the library. Tradovate: computed in per-bar JavaScript state, checked in the BSV stub of the documented API (not run on Tradovate). Pine v6, MQL5, MQL4, NinjaTrader 8, cTrader, AmiBroker, thinkorswim: the platform\'s documented closed-bar idiom (thinkScript close(period = AggregationPeriod.X) chain with [1] in that aggregation; AmiBroker TimeFrameSet + Ref(x, -1) + TimeFrameExpand expandFirst; Pine request.security with expr[1] + lookahead_on; MQL iBarShift + 1; NinjaTrader AddDataSeries + Calculate.OnBarClose; cTrader MarketData.GetBars + GetIndexByTime stepped back to a bar opened at or before the chart bar, minus 1), pattern checked by BSV but not run (UNTESTED_RUNTIME). Other targets: TODO stub (never computed on the chart timeframe); use the platform API with closed bars only.','確定した上位足だけを使います。backtrader・Backtesting.py・NautilusTrader：ライブラリ内で計算・確認。Tradovate：JavaScriptのバーごとの状態で計算し、公式APIのBSVスタブで確認（Tradovate上では未実行）。Pine v6・MQL5・MQL4・NinjaTrader 8・cTrader・AmiBroker・thinkorswim：各プラットフォームの公式の方法（thinkScriptはclose(period = AggregationPeriod.X)だけの式で[1]、AmiBrokerはTimeFrameSetでRef(x, -1)をとりexpandFirstで展開、cTraderはMarketData.GetBarsとGetIndexByTimeを足の始まり以前まで戻して−1、Pineはexpr[1]とlookahead_onを付けたrequest.security、MQLはiBarShift＋1、NinjaTraderはCalculate.OnBarCloseでのAddDataSeries）。形はBSVが確認していますが、実行はしていません（UNTESTED_RUNTIME）。ほかの出力先：TODOのスタブ（表示中の足では計算しません）。プラットフォームのAPI（例：cTraderのMarketData.GetBars）で確定した足だけを使ってください。'],
 'structure.pivot':['A pivot is a bar strictly beyond the left bars and at least as far as the right bars (a flat top counts once); it is confirmed only right bars later, and the last confirmed pivot high/low is held. Rendered on backtrader, Backtesting.py, NautilusTrader, Tradovate and AmiBroker (HHV / LLV / ValueWhen, checked in the BSV AFL evaluator); elsewhere TODO.','ピボットは、左側の足より厳密に外側で、右側の足以上に外側の足です（平らな天井は最初の足で1回）。確定するのは右側の本数だけ後で、最後に確定したピボットの高値・安値を保ちます。backtrader・Backtesting.py・NautilusTrader・Tradovate・AmiBroker（HHV・LLV・ValueWhen。BSVのAFL評価器で確認）で出力し、ほかはTODOです。'],
 'structure.range':['High/low of each window where the session (or signal) is true; resets at a new window and holds afterwards. The generator renders it on backtrader, Backtesting.py, NautilusTrader and Tradovate (per-bar state, checked in the BSV stub of the documented API) and AmiBroker (HighestSince / LowestSince / ValueWhen, checked in the BSV AFL evaluator, not AmiBroker); elsewhere it stays TODO.','セッション（またはシグナル）がtrueの時間帯ごとの高値・安値です。新しい時間帯でリセットし、終了後はその値を保ちます。ジェネレーターは backtrader・Backtesting.py・NautilusTrader・Tradovate（バーごとの状態。公式APIのBSVスタブで確認）・AmiBroker（HighestSince・LowestSince・ValueWhen。BSVのAFL評価器で確認、AmiBroker上では未実行）で出力し、それ以外ではTODOのままです。'],
 'signal.breakout':['First close beyond the finished window\'s high or low, on a closed bar outside the window (can fire again after price re-enters). Rendered on backtrader, Backtesting.py, NautilusTrader, Tradovate and AmiBroker; elsewhere TODO.','確定した足で、終わった時間帯の高値・安値を終値で初めて超えたときです（時間帯の外の足だけ。いったん戻って再び超えると、また出ます）。backtrader・Backtesting.py・NautilusTrader・Tradovate・AmiBroker で出力し、それ以外ではTODOです。'],
 'signal.liquidity_sweep':['Sweep candidate = wick beyond the last pivot high/low known before the bar by at least minAtrFraction x ATR, with the close back inside. A candidate only. Rendered on backtrader, Backtesting.py, NautilusTrader, Tradovate and AmiBroker; elsewhere TODO.','スイープ候補は、その足より前に確定したピボット高値・安値をヒゲでATR×minAtrFraction以上超え、終値で内側に戻った足です。あくまで候補です。backtrader・Backtesting.py・NautilusTrader・Tradovate・AmiBrokerで出力し、ほかはTODOです。'],
 'signal.divergence':['Regular divergence: a new pivot high above the previous one with a lower oscillator (bearish), or the mirror for lows (bullish); true only on the bar that confirms the pivot (right bars later). Rendered on backtrader, Backtesting.py, NautilusTrader, Tradovate and AmiBroker (ValueWhen(..., 2) = the pivot before); elsewhere TODO.','通常のダイバージェンスです。新しいピボット高値が前より高く、オシレーターが低いとき（弱気）、安値はその逆（強気）。ピボットが確定する足（right本後）でだけtrueです。backtrader・Backtesting.py・NautilusTrader・Tradovate・AmiBrokerで出力し、ほかはTODOです。'],
 'risk.atr_band':['Band = reference value plus/minus ATR x multiple. Plot it; do not place orders from an indicator.','バンドは基準値±ATR×倍率です。描画に使い、インジケーターから注文は出しません。'],
 'scanner.symbol_set':['Multi-symbol scanning needs platform APIs (Pine request.security per symbol, MQL SymbolSelect + iClose, cTrader MarketData.GetBars with a symbol).','複数銘柄のスキャンにはプラットフォームのAPIが必要です（Pineは銘柄ごとのrequest.security、MQLはSymbolSelectとiClose、cTraderは銘柄指定のMarketData.GetBars）。'],
 'visual.zone':['Two lines: the high and low of a range or pivot block. Rendered on backtrader, Backtesting.py and NautilusTrader (values only there), on Tradovate and AmiBroker for a pivot or range source (two lines); elsewhere TODO: draw a box between the two levels and keep the number of objects bounded.','レンジまたはピボットの高値・安値の2本の線です。backtrader・Backtesting.py・NautilusTraderで出力します（NautilusTraderは値のみ）。Tradovate・AmiBrokerではピボットまたはレンジが元のとき2本の線で出力します。ほかはTODOです。2つの水準の間に矩形を描き、オブジェクト数が増え続けないようにしてください。'],
 'visual.table':['The generator renders value panels on backtrader, Backtesting.py, NautilusTrader, thinkorswim, AmiBroker and JForex. Tradovate keeps the panel values in per-bar state (no panel call in its API; not drawn), checked in the BSV stub. Elsewhere use the platform panel API (Pine table.new, MQL ObjectCreate with OBJ_LABEL, cTrader Chart.DrawStaticText) and show the value of the last completed bar.','ジェネレーターは backtrader・Backtesting.py・NautilusTrader・thinkorswim・AmiBroker・JForex で値パネルを出力します。Tradovate はパネルの値を足ごとの状態に保持します（APIにパネルの機能がないため描画はしません。BSVのスタブで確認）。それ以外ではプラットフォームの表示API（Pineはtable.new、MQLはOBJ_LABELのObjectCreate、cTraderはChart.DrawStaticText）を使い、直近の確定足の値を表示してください。']};
var GENERIC_HINT=['Implement this block by hand on this platform, then remove the TODO.','このプラットフォーム向けにこのブロックを手で実装し、TODOを消してください。'];
function bi(pair,tag){var f=document.createDocumentFragment();f.appendChild(el(tag||'span',{'data-lang':'en',text:pair[0]}));f.appendChild(el(tag||'span',{'data-lang':'ja',text:pair[1]}));return f}
function escRe(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
function todoMap(out,blocks){var lines=out.split('\n').filter(function(l){return /TODO/.test(l)}),map={},general=[];
 var ids=blocks.map(function(b){return b.id}).sort(function(a,b){return b.length-a.length});
 lines.forEach(function(l){var hit=null,m=/TODO unsupported block [\w.]+: ([a-z][a-z0-9_]*)/.exec(l)||/^[\s\/#*]*(?:TODO\s+)?([a-z][a-z0-9_]*)\s*:/.exec(l);if(m&&ids.indexOf(m[1])>=0)hit=m[1];
  for(var i=0;!hit&&i<ids.length;i++){if(new RegExp('(^|[^A-Za-z0-9_])'+escRe(ids[i])+'([^A-Za-z0-9_]|$)').test(l)){hit=ids[i];break}}
  if(hit){(map[hit]=map[hit]||[]).push(l.trim())}else general.push(l.trim())});
 return {map:map,general:general,total:lines.length}}
function renderHints(out){var box=$('#rb-hints'),list=$('#rb-hint-list');if(!box)return;list.textContent='';
 var r=state.recipe,tm=todoMap(out||'',r.blocks),n=0;
 r.blocks.forEach(function(b){var badge=document.getElementById('rb-tb-'+b.id),c=(tm.map[b.id]||[]).length;
  if(badge){badge.textContent=c?('TODO×'+c):'';badge.hidden=!c}
  if(!c)return;n++;var li=el('li',{'class':'rb-hint'});
  var a=el('a',{href:'#rb-blk-'+b.id,text:b.id});a.addEventListener('click',function(e){e.preventDefault();var t=document.getElementById('rb-blk-'+b.id);if(t){t.scrollIntoView({block:'center'});var f=t.querySelector('input,select');if(f)f.focus()}});
  li.appendChild(el('p',{},[a,el('span',{'class':'small',text:' '+b.type+' · TODO×'+c})]));
  li.appendChild(bi(HINTS[b.type]||GENERIC_HINT,'p'));
  li.appendChild(el('pre',{'class':'rb-todo-lines',text:tm.map[b.id].slice(0,3).join('\n')+(c>3?'\n…':'')}));list.appendChild(li)});
 if(tm.general.length){n++;list.appendChild(el('li',{'class':'rb-hint'},[el('p',{text:'(general)'}),el('pre',{'class':'rb-todo-lines',text:tm.general.slice(0,3).join('\n')})]))}
 box.hidden=!n}
// ---- share: whitelist the recipe schema; params keep only plain values; nothing generated is ever included
function sanitize(input){var dropped=[];if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Recipe must be a JSON object');
 Object.keys(input).forEach(function(k){if(['schemaVersion','name','description','overlay','blocks'].indexOf(k)<0)dropped.push(k)});
 var str=function(v,n){return typeof v==='string'?v.slice(0,n):''};
 var out={schemaVersion:'0.1',name:str(input.name,80)||'Shared recipe',overlay:!!input.overlay,blocks:[]};
 var d=str(input.description,500);if(d)out.description=d;
 if(!Array.isArray(input.blocks))throw new Error('blocks must be an array');
 if(input.blocks.length>40)throw new Error('Too many blocks (max 40)');
 input.blocks.forEach(function(b,i){if(!b||typeof b!=='object')throw new Error('Block '+(i+1)+' is not an object');
  if(typeof b.id!=='string'||!/^[a-z][a-z0-9_]{0,39}$/.test(b.id))throw new Error('Block '+(i+1)+': invalid id');
  if(TYPES.indexOf(b.type)<0)throw new Error('Block '+b.id+': unknown type');
  Object.keys(b).forEach(function(k){if(['id','type','params'].indexOf(k)<0)dropped.push(b.id+'.'+k)});
  var p={},src=(b.params&&typeof b.params==='object'&&!Array.isArray(b.params))?b.params:{};
  Object.keys(src).slice(0,20).forEach(function(k){if(!/^[a-z][a-z0-9_]{0,39}$/i.test(k)){dropped.push(b.id+'.params.'+k);return}var v=src[k];
   if(typeof v==='string')p[k]=v.slice(0,200);else if(typeof v==='number'&&isFinite(v))p[k]=v;else if(typeof v==='boolean')p[k]=v;
   else if(Array.isArray(v)&&v.length<=20&&v.every(function(x){return typeof x==='string'}))p[k]=v.map(function(x){return x.slice(0,40)});
   else dropped.push(b.id+'.params.'+k)});
  out.blocks.push({id:b.id,type:b.type,params:p})});
 return {recipe:out,dropped:dropped}}
function canon(r){return JSON.stringify(sanitize(r).recipe)}
function starterIndex(r){var c=canon(r);for(var i=0;i<RECIPES.length;i++){if(canon(RECIPES[i])===c)return i}return -1}
function b64e(s){var b=new TextEncoder().encode(s),t='';for(var i=0;i<b.length;i++)t+=String.fromCharCode(b[i]);return btoa(t).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
function b64d(s){var t=atob(s.replace(/-/g,'+').replace(/_/g,'/')),b=new Uint8Array(t.length);for(var i=0;i<t.length;i++)b[i]=t.charCodeAt(i);return new TextDecoder().decode(b)}
function sharePayload(r){var i=starterIndex(r);if(i>=0)return 's='+encodeURIComponent(RECIPE_IDS[i]);
 var s=sanitize(r).recipe;RECIPES.forEach(function(x){if(s.description&&s.description===x.description)delete s.description});
 var j=JSON.stringify(s);if(j.length>SHARE_MAX)throw new Error('Recipe is too large to share as a link ('+j.length+' > '+SHARE_MAX+' characters). Download the JSON file instead.');
 return 'r='+b64e(j)}
function readPayload(h){h=String(h||'').replace(/^#/,'');var m=/^s=([a-z0-9-]+)$/.exec(h);if(m){var i=RECIPE_IDS.indexOf(decodeURIComponent(m[1]));if(i<0)throw new Error('Unknown starter in link');return clone(RECIPES[i])}
 m=/^r=([A-Za-z0-9_-]+)$/.exec(h);if(!m)return null;if(m[1].length>SHARE_MAX*2)throw new Error('Shared link is too large');return sanitize(JSON.parse(b64d(m[1]))).recipe}
function shareUrl(r){return location.origin+'/trading/items/bsv-builder.html#'+sharePayload(r)}
function applyImported(obj,label){var s=sanitize(obj);loadKeep(s.recipe);toast(label+(s.dropped.length?(' — ignored: '+s.dropped.slice(0,5).join(', ')):''))}
function loadKeep(r){try{var cur=localStorage.getItem(KEY);if(cur){localStorage.setItem(PREV,cur);var rb=$('#rb-restore');if(rb)rb.hidden=false}}catch(e){}load(r)}
function initShare(){
 $('#rb-share').addEventListener('click',function(){var u;try{u=shareUrl(state.recipe)}catch(e){$('#rb-err').hidden=false;$('#rb-err').textContent=String(e.message||e);return}
  $('#rb-share-url').value=u;$('#rb-share-box').hidden=false;if(navigator.clipboard)navigator.clipboard.writeText(u).then(function(){toast('Share link copied')})});
 $('#rb-import').addEventListener('change',function(e){var f=e.target.files&&e.target.files[0];if(!f)return;if(f.size>200000){toast('File too large');return}
  f.text().then(function(t){try{applyImported(JSON.parse(t),'Imported '+f.name)}catch(err){$('#rb-err').hidden=false;$('#rb-err').textContent='Import error: '+err.message}});e.target.value=''});
 $('#rb-restore').addEventListener('click',function(){try{var p=JSON.parse(localStorage.getItem(PREV)||'null');if(p){load(sanitize(p).recipe);localStorage.removeItem(PREV);$('#rb-restore').hidden=true;toast('Previous draft restored')}}catch(e){}});
 var got=null,err='';try{got=readPayload(location.hash)}catch(e){err=String(e.message||e)}
 if(!got&&!err){try{var pend=JSON.parse(localStorage.getItem(PENDING)||'null');localStorage.removeItem(PENDING);if(pend&&Date.now()-pend.t<86400000)got=readPayload(pend.h)}catch(e){err=String(e.message||e)}}
 if(got){loadKeep(got);toast('Shared recipe loaded');if(history.replaceState)history.replaceState(null,'',location.pathname+location.search)}
 if(err){$('#rb-err').hidden=false;$('#rb-err').textContent='Shared link error: '+err}
 return !!got}
// ---- builder: recipe lint (structure checks before render) + per-target compile checklist
var SINK=/^(visual|alert)\./;
function refsOf(b){var out=[];try{out=referencesFor(b).slice()}catch(e){}
 // also count id-like strings in params of block types the generator does not model yet (fields, during, range, timeframeRef, ...)
 var p=b.params||{};Object.keys(p).forEach(function(k){var v=p[k];(Array.isArray(v)?v:[v]).forEach(function(x){if(typeof x==='string'&&/^[a-z][a-z0-9_]*$/.test(x)&&out.indexOf(x)<0&&LINT_IDS[x])out.push(x)})});return out}
var LINT_IDS={};
function isBoolT(t){return /^(signal|filter|alert)\./.test(t||'')}
function reorder(r){var by={},order=[],state={},cyc=[];LINT_IDS={};r.blocks.forEach(function(b){by[b.id]=b;LINT_IDS[b.id]=true});
 function visit(b,stack){if(state[b.id]===2)return;if(state[b.id]===1){cyc.push(b.id);return}state[b.id]=1;
  refsOf(b).forEach(function(x){if(by[x]&&x!==b.id)visit(by[x])});state[b.id]=2;order.push(b)}
 r.blocks.forEach(function(b){visit(b)});return {blocks:order,cycle:cyc}}
function lint(r){var out=[],pos={},by={},used={};LINT_IDS={};r.blocks.forEach(function(b,i){pos[b.id]=i;by[b.id]=b;LINT_IDS[b.id]=true});
 var add=function(level,id,code,en,ja,fix){out.push({level:level,id:id,code:code,msg:[en,ja],fix:fix||''})};
 r.blocks.forEach(function(b,i){var p=b.params||{};
  refsOf(b).forEach(function(x){used[x]=true;
   if(x===b.id)add('error',b.id,'self-ref',b.id+' refers to itself.',b.id+' が自分自身を参照しています。');
   else if(pos[x]>i)add('warn',b.id,'forward-ref',b.id+' uses '+x+', which is defined below it. Pine and Bookmap evaluate top to bottom, so move '+x+' above (use "Fix order").',b.id+' が下にある '+x+' を参照しています。PineとBookmapは上から順に評価するため、'+x+' を上に移動してください（「順序を修正」）。','reorder')});
  if(b.type==='alert.condition'&&p.when&&!isBoolT((by[p.when]||{}).type))add('warn',b.id,'alert-value','Alert "'+b.id+'" watches '+p.when+', which is a value, not a condition; it fires whenever the value is non-zero.','アラート「'+b.id+'」が条件ではなく値（'+p.when+'）を見ています。値が0以外のあいだ毎回通知されます。');
  if(b.type==='signal.combine'){var s=p.signals||[];if(s.length<2)add('warn',b.id,'combine-few',b.id+' combines fewer than two signals.',b.id+' で組み合わせるシグナルが2つ未満です。');
   s.forEach(function(x){if(by[x]&&!isBoolT(by[x].type))add('warn',b.id,'combine-value',b.id+' combines '+x+', which is a value, not a condition.',b.id+' が条件ではなく値（'+x+'）を組み合わせています。')})}
  if(b.type==='signal.cross'&&p.left&&p.left===p.right)add('warn',b.id,'cross-same',b.id+' crosses '+p.left+' with itself; it can never fire.',b.id+' は同じ値同士のクロスなので成立しません。');
  if(b.type==='signal.threshold'&&(by[p.left]||{}).type==='indicator.rsi'&&(Number(p.value)<0||Number(p.value)>100))add('warn',b.id,'rsi-range',b.id+': RSI is 0-100, so '+p.value+' is never reached.',b.id+'：RSIは0〜100なので '+p.value+' には届きません。');
  if(b.type==='filter.session'&&!/^\d{4}-\d{4}$/.test(String(p.session||'')))add('error',b.id,'session-format',b.id+': session must look like HHMM-HHMM.',b.id+'：時間帯は HHMM-HHMM の形で入力してください。');
  if(b.type==='visual.plot'){var src=by[p.source]||{};
   if(r.overlay&&(src.type==='indicator.rsi'||isBoolT(src.type)))add('info',b.id,'scale',b.id+' plots '+p.source+' (0-100 or 0/1) on the price chart. Turn "overlay" off to see it in its own pane.',b.id+' は '+p.source+'（0〜100または0/1）を価格チャートに描きます。別ペインで見るには overlay をオフにしてください。');
   if(!r.overlay&&(['indicator.ema','indicator.sma'].indexOf(src.type)>=0||/^(open|high|low|close|hl2|hlc3|ohlc4)$/.test(p.source||'')))add('info',b.id,'scale',b.id+' plots a price-scale value in a separate pane. Turn "overlay" on to draw it on the price chart.',b.id+' は価格と同じ尺度の値を別ペインに描きます。価格チャートに重ねるには overlay をオンにしてください。')}});
 r.blocks.forEach(function(b){if(!SINK.test(b.type)&&!used[b.id])add('warn',b.id,'unused',b.id+' is not plotted, alerted or used by another block.',b.id+' はプロット・アラート・他のブロックのどれにも使われていません。','remove')});
 if(!r.blocks.some(function(b){return SINK.test(b.type)}))add('warn','','no-output','Nothing is plotted or alerted yet. Add a visual.plot or alert.condition block.','まだ何も描画・通知されません。visual.plot か alert.condition を追加してください。');
 var ro=reorder(r);ro.cycle.forEach(function(id){add('error',id,'cycle',id+' is part of a reference loop.',id+' が参照のループに含まれています。')});
 return out}
var COMMON_CHECK=[['Resolve every TODO marker (see the hints above).','TODOをすべて解消する（上のヒント参照）。'],['Check the result on history and a demo or replay account before any live use.','実運用の前に、過去データとデモ・リプレイ環境で確認する。'],['Record the platform name, version and build you used; BSV lists a target as verified only with that evidence.','使ったプラットフォーム名・バージョン・ビルドを記録する。BSVはその証拠があるときだけ検証済みとして扱います。']];
var CHECKLIST={
 'pine-v6':[['TradingView: open the Pine Editor, create a new indicator, paste, then Save and "Add to chart".','TradingView：Pineエディターで新規インジケーターを作り、貼り付けて保存し「チャートに追加」。'],['Fix anything the editor console reports, then re-add the script.','エディターのコンソールに出たエラーを直し、もう一度追加する。'],['For alerts, create an alert on the chart and pick this indicator\'s alert condition.','アラートはチャートでアラートを作成し、このインジケーターの条件を選ぶ。']],
 'mql5':[['MetaTrader 5: MetaEditor > New > Custom Indicator, paste, Compile (F7) with 0 errors.','MetaTrader 5：MetaEditorで「新規作成→カスタムインディケータ」、貼り付けてコンパイル（F7）しエラー0にする。'],['Attach it from the Navigator and watch the Experts / Journal tabs for runtime messages.','ナビゲーターからチャートに適用し、「エキスパート」「操作履歴」タブのメッセージを確認する。']],
 'mql4':[['MetaTrader 4: MetaEditor > New > Custom Indicator, paste, Compile (F7) with 0 errors.','MetaTrader 4：MetaEditorで「新規作成→カスタムインディケータ」、貼り付けてコンパイル（F7）しエラー0にする。'],['Refresh the Navigator, attach the indicator and check the Experts / Journal tabs.','ナビゲーターを更新してチャートに適用し、「エキスパート」「操作履歴」タブを確認する。']],
 'ctrader':[['cTrader: Algo > Indicators > New (C#), replace the code, Build (Ctrl+B) with no errors.','cTrader：Algo→インジケーター→新規（C#）でコードを置き換え、ビルド（Ctrl+B）しエラーなしにする。'],['Add it to a chart; alert lines appear in the Log tab (Print).','チャートに追加する。アラートはログタブに出力されます（Print）。']],
 'ctrader-python':[['cTrader: Algo > Indicators > New, language Python, same name as the generated class.','cTrader：Algo→インジケーター→新規で言語をPythonにし、生成されたクラスと同じ名前で作る。'],['Paste the commented attribute block into the .cs file and the rest into <Name>_main.py, then Build.','コメント内の属性部分を.csファイルに、残りを<Name>_main.pyに貼り付けてビルドする。']],
 'bookmap-python':[['Bookmap: set up the Python API add-on (open beta) as in the official BookmapAPI/python-api guide.','Bookmap：公式のBookmapAPI/python-apiの手順でPython APIアドオン（オープンベータ）を準備する。'],['Load the script, enable it for one instrument and check the add-on log; adjust BAR_SECONDS.','スクリプトを読み込んで1銘柄で有効にし、アドオンのログを確認する。BAR_SECONDSを調整する。']],
 'ninjatrader':[['NinjaTrader 8: New > NinjaScript Editor, create an indicator with the generated class name (or save the file under bin\\Custom\\Indicators), paste, Compile (F5).','NinjaTrader 8：「新規→NinjaScriptエディター」で生成されたクラス名のインジケーターを作る（またはbin\\Custom\\Indicatorsに保存）。貼り付けてコンパイル（F5）。'],['Add it to a chart; check the NinjaScript Output window. Alert() only fires in real time — use Market Replay to test alerts.','チャートに追加し、NinjaScript出力ウィンドウを確認する。Alert()はリアルタイムでのみ動くため、アラートはマーケットリプレイで確認する。']],
 'quantower':[['Quantower: create an indicator project with the Quantower Algo extension for Visual Studio, replace the class, build.','Quantower：Visual Studio用のQuantower Algo拡張でインジケーターのプロジェクトを作り、クラスを置き換えてビルドする。'],['Add the indicator to a chart; alert lines go to the Quantower event log.','インジケーターをチャートに追加する。アラートの行はQuantowerのイベントログに出ます。']],
 'sierra-acsil':[['Sierra Chart: save the file in the ACS_Source folder, then Analysis > Build Custom Studies DLL > Build; fix any compiler errors shown.','Sierra Chart：ファイルをACS_Sourceフォルダに保存し、Analysis→Build Custom Studies DLL→Buildでビルドする。表示されたコンパイルエラーを直す。'],['Add the study from Analysis > Studies (Add Custom Study); alerts are written to the Alerts Log (Window > Alert Manager > Alert Log).','Analysis→Studies（Add Custom Study）でスタディを追加する。アラートはAlerts Log（Window→Alert Manager→Alert Log）に出ます。']],
 'prorealtime':[['ProRealTime: Indicators > New > Creation by programming, paste, then Validate; fix the line the editor reports.','ProRealTime：インジケーター→新規→プログラミングで作成、貼り付けて「確認」。エディターが示した行を直す。'],['Add it to the chart. Alerts are created in ProRealTime on an indicator line (value 1); overlay recipes only draw markers — see the comment in the code.','チャートに追加する。アラートはProRealTimeでインジケーターの線（値が1）に対して作成します。価格チャートに重ねるレシピは印を描くだけです（コード内のコメント参照）。']],
 'gocharting-lipi':[['GoCharting: open the Lipi editor, create a new script, paste, then check it; fix the line the editor reports.','GoCharting：Lipiエディターで新しいスクリプトを作り、貼り付けてチェックする。エディターが示した行を直す。'],['Add it to the chart. In the alert dialog pick the alertcondition name; alert() only fires on realtime bars, once per closed bar here.','チャートに追加する。アラート画面ではalertconditionの名前を選ぶ。alert()はリアルタイムの足でだけ動き、このコードでは確定した足ごとに1回です。']],
 'motivewave':[['MotiveWave: in a Java project with the MotiveWave SDK jar on the classpath, save the code as <class name>.java, build the jar and put it in the MotiveWave Extensions folder.','MotiveWave：MotiveWave SDKのjarをクラスパスに入れたJavaプロジェクトで、コードを<クラス名>.javaとして保存し、jarをビルドしてMotiveWaveのExtensionsフォルダに置く。'],['Add the study from the BSV study menu. Signals fire on closed bars; turn on alerts for them in the study settings.','BSVのスタディメニューから追加する。シグナルは確定した足で出ます。スタディの設定でシグナルのアラートを有効にする。']],
 'vela':[['Vela: npm install @luxalgo/vela (Apache-2.0), save the code as a module, and call mountBsvChart("#chart", yourBars) from a page with a chart div (see platforms/vela).','Vela：npm install @luxalgo/vela（Apache-2.0）を実行し、コードをモジュールとして保存して、チャート用のdivがあるページからmountBsvChart("#chart", 自分の足データ)を呼ぶ（platforms/vela参照）。'],['Bars are { time (epoch ms), open, high, low, close, volume }. Signals draw markers; alerts go to handle.on("alert") for bars that close after loading. No Pine runtime is used.','足データは{ time（エポックミリ秒）, open, high, low, close, volume }。シグナルは印を描き、読み込み後に確定した足のアラートはhandle.on("alert")に届きます。Pineのランタイムは使いません。']],
 'jforex':[['JForex: save the code as <class name>.java in the JForex Strategies folder (or open it in the Strategies tab), then Compile; fix the line the compiler reports.','JForex：コードを<クラス名>.javaとしてJForexのStrategiesフォルダに保存し（またはStrategiesタブで開き）、コンパイルする。コンパイラーが示した行を直す。'],['Run it on a demo account with the instrument and period you want (set in the start dialog). Values and alerts are printed to the JForex console for closed bars; the strategy places no orders.','デモ口座で、開始時の画面で銘柄と時間足を選んで実行する。確定した足の値とアラートはJForexのコンソールに出ます。この戦略は発注しません。']],
 'atas':[['ATAS: in a C# class library that references the ATAS indicator API (ATAS.Indicators), save the code as <class name>.cs, build it and copy the dll to the ATAS Indicators folder.','ATAS：ATASのインジケーターAPI（ATAS.Indicators）を参照するC#クラスライブラリで、コードを<クラス名>.csとして保存してビルドし、dllをATASのIndicatorsフォルダにコピーする。'],['Add the indicator to a chart. Alerts use AddAlert once per closed bar after loading (set AlertFile to a sound you have). Session filters treat the candle time as UTC — check your data (see the TODO).','チャートにインジケーターを追加する。アラートは読み込み後に確定した足ごとに1回、AddAlertで出ます（AlertFileは手元にある音声ファイル名にする）。時間帯フィルターはローソク足の時刻をUTCとして扱います。データの時刻を確認してください（TODO参照）。']],
 'backtesting-py':[['Backtesting.py: install Python 3.9+ and Backtesting.py (pip install backtesting), save the code as a .py file and run python file.py bars.csv. The CSV needs a header row and the columns datetime,open,high,low,close,volume, with the time as YYYY-MM-DD HH:MM:SS in UTC.','Backtesting.py：Python 3.9以上とBacktesting.py（pip install backtesting）を入れ、コードを.pyファイルに保存して python ファイル名.py bars.csv で実行する。CSVは見出し行付きで、列は datetime,open,high,low,close,volume、時刻はUTCの YYYY-MM-DD HH:MM:SS 形式。'],['Each completed bar where an alert condition holds prints one ALERT line with the bar time, starting once every plotted line has a value. Add --plot to write an HTML chart (Bokeh). It places no orders and runs only on the data you give it.','アラート条件が成立した確定足ごとに、足の時刻付きのALERT行を1行出力します（描画するラインがすべて値を持った足から）。--plot を付けるとHTMLのチャート（Bokeh）を書き出します。注文は出さず、渡したデータだけで動きます。']],
 'nautilus':[['NautilusTrader: install Python 3.12+ and NautilusTrader 1.x (pip install "nautilus_trader<2"; BSV checked 1.231.0, the 2.0 release candidates change the config API), save the code as a .py file and run python file.py bars.csv. The CSV needs a header row and the columns datetime,open,high,low,close,volume, with the time as YYYY-MM-DD HH:MM:SS in UTC.','NautilusTrader：Python 3.12以上とNautilusTrader 1.x（pip install "nautilus_trader<2"。BSVの確認は1.231.0、2.0のリリース候補は設定APIが変わります）を入れ、コードを.pyファイルに保存して python ファイル名.py bars.csv で実行する。CSVは見出し行付きで、列は datetime,open,high,low,close,volume、時刻はUTCの YYYY-MM-DD HH:MM:SS 形式。'],['The sample run uses NautilusTrader\'s test EUR/USD instrument and a 15-minute bar type; change INSTRUMENT / BAR_SPEC for your data. Each completed bar where an alert condition holds prints one ALERT line with the bar time. There is no chart: plot blocks are values kept in the strategy. It places no orders and runs only on the data you give it.','サンプルの実行はNautilusTraderのテスト用EUR/USD銘柄と15分足を使います。データに合わせて INSTRUMENT / BAR_SPEC を変えてください。アラート条件が成立した確定足ごとに、足の時刻付きのALERT行を1行出力します。チャートは無く、描画ブロックはストラテジー内の値として保持します。注文は出さず、渡したデータだけで動きます。']],
 'backtrader':[['backtrader: install Python 3.9+ and backtrader (pip install backtrader), save the code as a .py file and run python file.py bars.csv. The CSV needs a header row and the columns datetime,open,high,low,close,volume, with the time as YYYY-MM-DD HH:MM:SS in UTC.','backtrader：Python 3.9以上とbacktrader（pip install backtrader）を入れ、コードを.pyファイルに保存して python ファイル名.py bars.csv で実行する。CSVは見出し行付きで、列は datetime,open,high,low,close,volume、時刻はUTCの YYYY-MM-DD HH:MM:SS 形式。'],['Each completed bar where an alert condition holds prints one ALERT line with the bar time. Add --plot to draw the lines (needs matplotlib). It places no orders and runs only on the data you give it.','アラート条件が成立した確定足ごとに、足の時刻付きのALERT行を1行出力します。--plot を付けるとラインを描画します（matplotlibが必要）。注文は出さず、渡したデータだけで動きます。']],
 'amibroker':[['AmiBroker: choose Analysis > Formula Editor, paste the code and press Apply indicator (Tools > Apply indicator); fix any line the editor reports. For overlay recipes, drag the formula onto the price pane.','AmiBroker：「Analysis→Formula Editor」を開いてコードを貼り付け、Apply indicator（Tools→Apply indicator）を押す。エディターが示した行を直す。重ねて表示するレシピは、式を価格のペインにドラッグする。'],['Alerts appear in the Alert Output window, once per completed bar (AlertIf with lookback 2). Session filters use TimeNum() in the database time zone — check your data and the bar time stamp setting (see the TODO).','アラートはAlert Outputウィンドウに、確定した足ごとに1回出ます（AlertIf、lookback 2）。時間帯フィルターはデータベースのタイムゾーンのTimeNum()で判定します。データと足の時刻の付け方の設定を確認してください（TODO参照）。']],
 'tradovate':[['Tradovate: in Tradovate Trader add the Code Explorer module (the + button), choose File > New, paste the code and save; fix any line the editor reports.','Tradovate：Tradovate TraderでCode Explorerモジュールを追加し（＋ボタン）、「File→New」でコードを貼り付けて保存する。エディターが示した行を直す。'],['Open the chart Indicators menu, find the indicator by its name in capitals (BSV…) and add it. The published custom-indicator API has no alert call, so alert conditions are drawn as dots on the bar that just closed; set up notifications in Tradovate yourself. No orders.','チャートのIndicatorsメニューで大文字の名前（BSV…）を探して追加する。公開されているカスタムインジケーターAPIにはアラートの呼び出しがないため、アラート条件は確定したばかりの足に点で表示されます。通知はTradovate側でご自身で設定してください。注文は出しません。']],
 'thinkscript':[['thinkorswim: on the Charts tab click Studies > Edit studies… > Create…, paste the code into the thinkScript Editor, name the study and save it; fix any line the editor marks. A saved .ts file can also be imported (Edit studies… > Import…).','thinkorswim：チャートタブで「Studies→Edit studies…→Create…」を選び、thinkScriptエディターにコードを貼り付けて名前を付けて保存する。エディターが示した行を直す。保存した.tsファイルは「Edit studies…→Import…」で読み込むこともできる。'],['Add the study to a chart. Alerts check the bar that just closed (condition[1]) and fire at most once per bar (Alert.BAR). Session filters use SecondsFromTime/SecondsTillTime in US Eastern time and need an intraday chart (see the TODO).','スタディーをチャートに追加する。アラートは確定したばかりの足（condition[1]）を調べ、1本の足につき1回まで出ます（Alert.BAR）。時間帯フィルターは米国東部時間のSecondsFromTime/SecondsTillTimeで判定し、日中足のチャートが必要です（TODO参照）。']],
 'easylanguage':[['TradeStation: in the TradeStation Development Environment choose File > New > Indicator, give it a name, paste the code and Verify (F3); fix the line the verifier reports.','TradeStation：TradeStation開発環境で「ファイル→新規→インジケーター」を選んで名前を付け、コードを貼り付けて検証（F3）する。検証で示された行を直す。'],['Insert the indicator on a chart. For alerts, enable them in the indicator Properties (Alerts tab); they fire only on the last bar, at its closing tick. Session times use the chart time zone (see the TODO).','チャートにインジケーターを挿入する。アラートはインジケーターのプロパティ（アラートタブ）で有効にする。アラートは最新の足の終了ティックでだけ出ます。時間帯はチャートのタイムゾーンで判定します（TODO参照）。']]};
function renderLint(){var box=$('#rb-lint'),list=$('#rb-lint-list');if(!box)return;list.textContent='';var issues=lint(state.recipe),hasOrder=false;
 issues.forEach(function(it){var li=el('li',{'class':'rb-lint-'+it.level});li.appendChild(el('strong',{text:it.level.toUpperCase()+' '}));li.appendChild(bi(it.msg));
  if(it.fix==='remove'){li.appendChild(mk('Remove '+it.id,function(){state.recipe.blocks=state.recipe.blocks.filter(function(b){return b.id!==it.id});draw()}))}
  if(it.fix==='reorder')hasOrder=true;list.appendChild(li)});
 $('#rb-lint-fix').hidden=!hasOrder;var e=issues.filter(function(x){return x.level==='error'}).length,w=issues.filter(function(x){return x.level==='warn'}).length;
 $('#rb-lint-sum').textContent=issues.length?('Recipe check: '+e+' error(s), '+w+' warning(s), '+(issues.length-e-w)+' note(s)'):'Recipe check: no issues';box.classList.toggle('rb-lint-ok',!issues.length)}
var RES_KEY='bsv-rb-compile-log',RES_MAX=200;
var RES_STATUS=[['not-tried','Not tried yet','未実施'],['compiled','Compiled with 0 errors','エラー0でコンパイルできた'],['compiled-warnings','Compiled with warnings','警告ありでコンパイルできた'],['compile-failed','Compile failed','コンパイルできなかった'],['ran-replay','Ran on a chart / replay (own check)','チャート・リプレイで動いた（自分で確認）']];
function fp(s){var h=0x811c9dc5;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0}return('0000000'+h.toString(16)).slice(-8)}
function clip(v,n){return String(v==null?'':v).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'').slice(0,n)}
function statusOk(x){return RES_STATUS.some(function(r){return r[0]===x})}
function cleanRecord(r){if(!r||typeof r!=='object')return null;var t=clip(r.target,32);if(!Object.prototype.hasOwnProperty.call(CHECKLIST,t))return null;var st=statusOk(r.status)?r.status:'not-tried';
 var steps=Array.isArray(r.steps)?r.steps.slice(0,12).map(function(b){return !!b}):[];
 return {v:1,recipe:clip(r.recipe,120),target:t,fp:/^[0-9a-f]{8}$/.test(String(r.fp))?String(r.fp):'',len:Math.max(0,Math.min(1e7,+r.len||0)),status:st,platform:clip(r.platform,120),notes:clip(r.notes,1000),steps:steps,at:clip(r.at,32),self_reported:true,bsv_verified:false}}
function makeRecord(recipeName,target,out,form){return cleanRecord({recipe:recipeName,target:target,fp:fp(out||''),len:(out||'').length,status:form.status,platform:form.platform,notes:form.notes,steps:form.steps||[],at:form.at||new Date().toISOString()})}
function recordMarkdown(r){var items=(CHECKLIST[r.target]||[]).concat(COMMON_CHECK),lab=RES_STATUS.filter(function(x){return x[0]===r.status})[0];
 return ['# Compile record (self-reported)','','> Recorded by the user in their own browser. Not verified by BSV; the BSV catalog status stays "Not runtime tested".','',
  '- Recipe: '+r.recipe,'- Target: '+r.target,'- Generated code fingerprint: '+r.fp+' ('+r.len+' chars, FNV-1a of the code shown in the builder)','- Result: '+(lab?lab[1]:r.status),'- Platform / version / build: '+(r.platform||'(not given)'),'- Recorded at: '+r.at,'','## Checklist']
  .concat(items.map(function(it,i){return '- ['+(r.steps[i]?'x':' ')+'] '+it[0]})).concat(['','## Notes','',r.notes||'(none)','']).join('\n')}
function loadRecords(){try{var a=JSON.parse(localStorage.getItem(RES_KEY)||'[]');return Array.isArray(a)?a.map(cleanRecord).filter(Boolean):[]}catch(e){return[]}}
function storeRecords(a){try{localStorage.setItem(RES_KEY,JSON.stringify(a.slice(-RES_MAX)))}catch(e){}}
state.checks=state.checks||{};
function checkKey(){return state.target+'|'+fp($('#rb-out')?$('#rb-out').textContent:'')}
function renderChecklist(){var ol=$('#rb-check-list');if(!ol)return;ol.textContent='';var k=checkKey(),cur=state.checks[k]||[];
 (CHECKLIST[state.target]||[]).concat(COMMON_CHECK).forEach(function(pair,i){var id='rb-ck-'+i,cb=el('input',{type:'checkbox',id:id,'class':'rb-ck','data-i':String(i)});cb.checked=!!cur[i];
  cb.addEventListener('change',function(){var a=state.checks[k]||[];a[i]=cb.checked;state.checks[k]=a});var lb=el('label',{'for':id});lb.appendChild(bi(pair));ol.appendChild(el('li',{},[cb,lb]))});
 var b=document.querySelector('[data-rb-target="'+state.target+'"]');$('#rb-check-target').textContent=b?b.textContent:state.target;renderRecords()}
function formNow(){var n=(CHECKLIST[state.target]||[]).length+COMMON_CHECK.length,cur=state.checks[checkKey()]||[],steps=[];for(var i=0;i<n;i++)steps.push(!!cur[i]);
 return {status:$('#rb-res-status').value,platform:$('#rb-res-platform').value,notes:$('#rb-res-notes').value,steps:steps}}
function renderRecords(){var ul=$('#rb-res-list');if(!ul)return;ul.textContent='';var out=$('#rb-out').textContent,cfp=fp(out),name=state.recipe.name||'';
 var mine=loadRecords().filter(function(r){return r.recipe===clip(name,120)});
 if(!mine.length){ul.appendChild(el('li',{'class':'muted'},[bi(['No saved records for this recipe yet.','このレシピの記録はまだありません。'])]));return}
 mine.slice(-10).reverse().forEach(function(r){var lab=RES_STATUS.filter(function(x){return x[0]===r.status})[0]||[r.status,r.status,r.status];
  var same=r.target===state.target&&r.fp===cfp;var li=el('li',{},[el('strong',{text:r.target+' · '}),bi([lab[1],lab[2]]),el('span',{'class':'muted',text:' · '+r.at.slice(0,16).replace('T',' ')+' UTC · '+r.fp+' '}),
   bi(r.target!==state.target?['(other target)','（別の出力先）']:same?['(matches the code shown)','（表示中のコードと一致）']:['(code changed since)','（その後コードが変わりました）'])]);
  li.appendChild(mk('.md',function(){download(fileBase()+'.'+r.target+'.compile-record.md',recordMarkdown(r))}));ul.appendChild(li)})}
function initRecords(){var s=$('#rb-res-status');if(!s)return;RES_STATUS.forEach(function(r){s.appendChild(el('option',{value:r[0],text:r[1]+' / '+r[2]}))});
 $('#rb-res-save').addEventListener('click',function(){var out=$('#rb-out').textContent;if(!out){toast('Nothing to record');return}var rec=makeRecord(state.recipe.name||'',state.target,out,formNow());var a=loadRecords();a.push(rec);storeRecords(a);renderRecords();toast('Saved in this browser')});
 $('#rb-res-dl').addEventListener('click',function(){var out=$('#rb-out').textContent;download(fileBase()+'.'+state.target+'.compile-record.md',recordMarkdown(makeRecord(state.recipe.name||'',state.target,out,formNow())))});
 $('#rb-res-send').addEventListener('click',function(){var out=$('#rb-out').textContent,msg=$('#rb-res-sent');if(!out){toast('Nothing to send');return}var r=makeRecord(state.recipe.name||'',state.target,out,formNow());var sc=document.querySelector('script[src*="bsv-builder."]'),bj=sc?String(sc.getAttribute('src')).split('/').pop():'';var body={recipe:r.recipe||'(unnamed)',target:r.target,status:r.status,platform:r.platform||'',notes:r.notes||'',steps:r.steps||[],fp:r.fp};if(/^bsv-builder\.[0-9a-f]{8}\.js$/.test(bj))body.builder=bj;var btn=this;btn.disabled=true;msg.textContent='Sending… / 送信中…';
  fetch('/.netlify/functions/compile-report',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(res){return res.json().catch(function(){return {}}).then(function(j){return {s:res.status,j:j}})}).then(function(x){
   if((x.s===201||x.s===200)&&x.j.ok)msg.textContent='Sent for BSV review ('+x.j.id+(x.j.duplicate?', already sent':'')+'). Not public; nothing is marked verified. / BSVの確認用に送信しました（'+x.j.id+(x.j.duplicate?'、送信済み':'')+'）。公開されず、検証済みにもなりません。';
   else if(x.s===401)msg.textContent='Please sign in again with the email code, then send. / メールのコードで再ログインしてから送信してください。';
   else if(x.s===429)msg.textContent='Daily limit reached (10 per account). / 1日の上限（10件）に達しました。';
   else msg.textContent='Not sent: '+(x.j.reason||x.s)+' / 送信できませんでした';}).catch(function(){msg.textContent='Not sent (network). / 送信できませんでした（通信）';}).then(function(){btn.disabled=false})});
 $('#rb-res-clear').addEventListener('click',function(){var name=clip(state.recipe.name||'',120);storeRecords(loadRecords().filter(function(r){return r.recipe!==name}));renderRecords();toast('Records for this recipe cleared')})}
function init(){if(!$('#rb-app'))return;initRecords();
 var st=$('#rb-start');RECIPES.forEach(function(r,i){st.appendChild(el('option',{value:String(i),text:r.name}))});
 st.addEventListener('change',function(){if(st.value==='blank')load({schemaVersion:'0.1',name:'My chart tool',description:'',overlay:true,blocks:[]});else if(st.value!=='')load(RECIPES[+st.value])});
 var at=$('#rb-add-type');TYPES.forEach(function(t){at.appendChild(el('option',{value:t,text:t}))});
 $('#rb-add').addEventListener('click',function(){var t=at.value;state.recipe.blocks.push({id:uniqueId(t.split('.').pop()),type:t,params:clone(DEFAULTS[t]||{})});draw()});
 $('#rb-name').addEventListener('change',function(e){state.recipe.name=e.target.value;update()});
 $('#rb-desc').addEventListener('change',function(e){state.recipe.description=e.target.value;update()});
 $('#rb-overlay').addEventListener('change',function(e){state.recipe.overlay=e.target.checked;update()});
 [].forEach.call(document.querySelectorAll('[data-rb-target]'),function(b){b.addEventListener('click',function(){state.target=b.getAttribute('data-rb-target');[].forEach.call(document.querySelectorAll('[data-rb-target]'),function(x){x.setAttribute('aria-pressed',String(x===b))});update()})});
 $('#rb-json-apply').addEventListener('click',function(){try{applyImported(JSON.parse($('#rb-json').value),'JSON applied')}catch(e){$('#rb-err').hidden=false;$('#rb-err').textContent='JSON error: '+e.message}});
 $('#rb-copy').addEventListener('click',function(){if(navigator.clipboard)navigator.clipboard.writeText($('#rb-out').textContent).then(function(){toast('Copied')})});
 $('#rb-dl').addEventListener('click',function(){download(fileBase()+EXT[state.target],$('#rb-out').textContent)});
 $('#rb-dl-json').addEventListener('click',function(){download(fileBase()+'.recipe.json',JSON.stringify(sanitize(state.recipe).recipe,null,2)+'\n')});
 $('#rb-lint-fix').addEventListener('click',function(){var ro=reorder(state.recipe);if(!ro.cycle.length){state.recipe.blocks=ro.blocks;draw();toast('Blocks reordered')}});
 if(initShare())return;
 var d=null;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){}
 var ok=null;try{ok=d?sanitize(d).recipe:null}catch(e){}
 load(ok||RECIPES[0]);}
root.BSVBuilder={fp:fp,makeRecord:makeRecord,cleanRecord:cleanRecord,recordMarkdown:recordMarkdown,resStatus:RES_STATUS,lint:lint,reorder:reorder,checklist:CHECKLIST,common:COMMON_CHECK,sanitize:sanitize,sharePayload:sharePayload,readPayload:readPayload,todoMap:todoMap,hints:HINTS,b64e:b64e,b64d:b64d};
if(typeof document!=='undefined'){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init()}
"""

# Public summary page only: a shared link (#r=… / #s=…) is stashed in this browser so it survives the
# email-verification redirect; the gated builder loads it once and deletes it. Nothing is sent anywhere.
SHARE_STASH_JS = r"""
(function(){var h=location.hash;if(!/^#(r=[A-Za-z0-9_-]{1,12000}|s=[a-z0-9-]{1,60})$/.test(h))return;
try{localStorage.setItem('bsv-rb-pending-share',JSON.stringify({h:h.slice(1),t:Date.now()}))}catch(e){}
function show(){var n=document.getElementById('rb-shared-note');if(n)n.hidden=false}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',show);else show()})();
"""

CSS = """
.rb-wrap{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:start}
.rb-panel{border:1px solid var(--line);border-radius:6px;padding:16px;background:var(--panel)}
.rb-panel h2{font-size:16px;margin:0 0 10px}
.rb-field{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--muted);min-width:0}
.rb-field input,.rb-field select,.rb-raw,#rb-json{background:#090d0b;color:var(--text);border:1px solid var(--line);border-radius:4px;padding:8px;min-width:0;max-width:100%;font:12px var(--mono)}
.rb-meta{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.rb-block{border:1px solid var(--line);border-radius:6px;margin:0 0 10px;padding:10px;min-width:0}
.rb-panel{min-width:0}.rb-field input:not([type=checkbox]),.rb-field select{width:100%}
.rb-block legend{font:11px var(--mono);color:var(--green)}
.rb-head{display:grid;grid-template-columns:1fr 1.4fr auto;gap:8px;align-items:end}
.rb-params{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:8px}
.rb-tools{display:flex;gap:4px}
.rb-add{display:flex;gap:8px;flex-wrap:wrap;align-items:end;margin-top:8px}
.rb-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.rb-tabs button[aria-pressed=true]{border-color:var(--green);color:var(--green)}
#rb-out{min-height:320px;max-height:640px}
#rb-err{border:1px solid var(--danger);color:var(--danger);padding:8px 10px;border-radius:4px;font-size:12px}
.rb-bad{border-color:var(--danger)!important}
.rb-sticky{position:sticky;top:12px}
.rb-panel [hidden],.rb-wrap [hidden]{display:none!important}
.rb-tbadge{margin-left:6px;color:var(--danger);font:11px var(--mono)}
#rb-hints{margin:8px 0;border:1px solid var(--line);border-radius:4px;padding:8px 10px}
#rb-hints summary{cursor:pointer;font-size:12px}
#rb-hint-list{list-style:none;padding:0;margin:8px 0 0}
.rb-hint{border-top:1px solid var(--line);padding:6px 0;font-size:12px}
.rb-hint p{margin:2px 0}
.rb-todo-lines{font:11px var(--mono);white-space:pre-wrap;margin:4px 0 0;padding:6px;max-height:120px;overflow:auto}
#rb-lint,#rb-check{margin:8px 0;border:1px solid var(--line);border-radius:4px;padding:8px 10px;font-size:12px}
#rb-lint summary,#rb-check summary{cursor:pointer}
#rb-lint-list{list-style:none;padding:0;margin:6px 0}
#rb-lint-list li{border-top:1px solid var(--line);padding:5px 0}
#rb-lint-list li .btn{margin-left:8px}
.rb-lint-error strong{color:var(--danger)}.rb-lint-warn strong{color:var(--danger)}.rb-lint-info strong{color:var(--muted)}
#rb-lint.rb-lint-ok summary{color:var(--green)}
#rb-check-list{margin:6px 0 0 18px;padding:0}
#rb-check-list li{margin:3px 0;display:flex;gap:6px;align-items:flex-start}
#rb-check-list input{margin-top:2px}
#rb-res{border-top:1px solid var(--line);margin-top:8px;padding-top:6px;display:grid;gap:4px}
#rb-res label{font-size:12px;color:var(--muted)}
#rb-res select,#rb-res input,#rb-res textarea{width:100%;box-sizing:border-box}
#rb-res-list{list-style:none;padding:0;margin:4px 0 0}
#rb-res-list li{border-top:1px solid var(--line);padding:4px 0}
#rb-res-list li .btn{margin-left:6px}
.rb-res-h{margin:4px 0 0}
.rb-share{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
#rb-share-url{width:100%;font:11px var(--mono);background:#090d0b;color:var(--text);border:1px solid var(--line);border-radius:4px;padding:6px}
.rb-file{display:inline-flex;align-items:center;gap:6px;font-size:12px}
#rb-json{width:100%;min-height:180px}
@media (max-width:900px){.rb-wrap{grid-template-columns:1fr}.rb-sticky{position:static}.rb-head{grid-template-columns:1fr 1fr}.rb-tools{grid-column:1/-1}.rb-meta{grid-template-columns:1fr}}
"""


def port_js(repo: Path) -> str:
    src = (repo / "trader-toolkit/generator/render.mjs").read_text()
    i = src.find("function validateRecipe")
    if i < 0 or "process." in src[i:] or "fs." in src[i:]:
        raise SystemExit("render.mjs layout changed: cannot port safely")
    rfiles = sorted((repo / "trader-toolkit/recipes").glob("*.json"))
    recipes = [json.loads(p.read_text()) for p in rfiles]
    schema = json.loads((repo / "trader-toolkit/schema/bsv-trader-recipe.schema.json").read_text())
    types = schema["properties"]["blocks"]["items"]["properties"]["type"]["enum"]
    return ("/* BSV recipe builder — gated. Generator functions are copied verbatim from trader-toolkit/generator/render.mjs (MIT). */\n"
            "(function(root){'use strict';\n" + src[i:] +
            "\nvar RENDER={" + ",".join(f"'{t}':function(r){{return renderFor('{t}',{TARGET_FN[t]},r)}}" for t, _, _ in blt.TARGETS + BUILDER_EXTRA_TARGETS) + "};\n"
            f"var RECIPES={json.dumps(recipes, ensure_ascii=False)};\nvar RECIPE_IDS={json.dumps([p.stem for p in rfiles])};\nvar TYPES={json.dumps(types)};\n"
            "root.BSVRender={validate:validateRecipe,render:function(r,t){validateRecipe(r);return RENDER[t](r)},recipes:RECIPES,types:TYPES};\n"
            + UI_JS.replace("__PRICE__", json.dumps(PRICE)).replace("__EXT__", json.dumps({t: e for t, _, e in blt.TARGETS + BUILDER_EXTRA_TARGETS})) + "\n})(typeof window!=='undefined'?window:globalThis);\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--repo", default=str(blt.REPO))
    a = ap.parse_args()
    site, repo = Path(a.site), Path(a.repo)
    blt.assets(site)
    js = port_js(repo)
    h = hashlib.sha256(js.encode()).hexdigest()[:8]
    for old in (site / "trading/sources").glob(f"{SLUG}.*.js"):
        old.unlink()
    js_path = f"/trading/sources/{SLUG}.{h}.js"
    blt.write(site / js_path.lstrip("/"), js)
    n_rec = len(list((repo / "trader-toolkit/recipes").glob("*.json")))

    # ---- gated builder page
    body = (
        f'<div class="container detail"><div class="breadcrumb"><a href="/trading/">← Traders Library</a> / <a href="/trading/build/">{both(T("Build your own chart tool", "自分のチャートツールを作る"))}</a> / {both(T("Recipe builder", "レシピビルダー"))}</div>'
        f'<h1 class="detail-title">{both(T("Recipe builder", "レシピビルダー"))}</h1>'
        f'{both(T("Pick a starter or start blank, edit the blocks, and the BSV generator renders TradingView Pine v6, MT5 MQL5, MT4 MQL4, cTrader C# / Python, Bookmap Python, NinjaTrader 8, Quantower, Sierra Chart (ACSIL), ProRealTime, GoCharting (Lipi), MotiveWave (Java), Vela (JavaScript), JForex (Java), TradeStation (EasyLanguage), ATAS (C#), AmiBroker (AFL), thinkorswim (thinkScript), Tradovate (JavaScript), backtrader (Python), Backtesting.py (Python) and NautilusTrader (Python) right here in your browser. Nothing is sent to a server.", "ひな形を選ぶか白紙から始めてブロックを編集すると、BSVジェネレーターがTradingView（Pine v6）・MT5（MQL5）・MT4（MQL4）・cTrader（C#／Python）・Bookmap（Python）・NinjaTrader 8・Quantower・Sierra Chart（ACSIL）・ProRealTime・GoCharting（Lipi）・MotiveWave（Java）・Vela（JavaScript）・JForex（Java）・TradeStation（EasyLanguage）・ATAS（C#）・AmiBroker（AFL）・thinkorswim（thinkScript）・Tradovate（JavaScript）・backtrader（Python）・Backtesting.py（Python）・NautilusTrader（Python）のコードをこのブラウザ内で生成します。サーバーには何も送信しません。"), "p", "detail-lead")}'
        f'<div class="notice"><p>{both(T("Output is a structural starter: compile it on your platform and resolve every TODO marker before use. Not runtime tested by BSV; not investment advice; no profitability is promised.", "出力は構造のひな形です。各プラットフォームでコンパイルし、TODOをすべて解消してから使ってください。BSVでは実行検証していません。投資助言ではなく、収益も保証しません。"))}</p></div>'
        '<noscript><p class="no-js">JavaScript is required for the builder.</p></noscript>'
        '<div id="rb-app" class="rb-wrap"><section class="rb-panel" aria-label="Recipe editor">'
        f'<h2>{both(T("1. Recipe", "1. レシピ"))}</h2>'
        f'<label class="rb-field"><span>{both(T("Start from", "開始点"))}</span><select id="rb-start"><option value="">—</option><option value="blank">Blank recipe</option></select></label>'
        '<div class="rb-meta"><label class="rb-field"><span>name</span><input id="rb-name" type="text"></label><label class="rb-field"><span>description</span><input id="rb-desc" type="text"></label>'
        '<label class="rb-field"><span>overlay (draw on price chart)</span><input id="rb-overlay" type="checkbox"></label></div>'
        f'<h2>{both(T("2. Blocks", "2. ブロック"))}</h2><div id="rb-blocks"></div><datalist id="rb-ids"></datalist>'
        f'<div class="rb-add"><label class="rb-field"><span>{both(T("Add block", "ブロックを追加"))}</span><select id="rb-add-type"></select></label><button type="button" class="btn small-btn" id="rb-add">+ Add</button></div>'
        f'<div class="rb-share"><h2>{both(T("Share / import", "共有・読み込み"))}</h2><div class="source-toolbar"><button type="button" class="btn small-btn" id="rb-share">Copy share link</button><label class="btn small-btn rb-file">Import JSON file<input type="file" id="rb-import" accept=".json,application/json" hidden></label><button type="button" class="btn small-btn" id="rb-restore" hidden>Restore my previous draft</button></div>'
        f'<div id="rb-share-box" hidden><input id="rb-share-url" type="text" readonly aria-label="Share link"></div>'
        f'{both(T("A share link holds only your block settings (id, type, params, name). It has no generated code and no BSV source, sits after # in the URL so it is never sent to a server, and unchanged starters are shared by name. Whoever opens it still needs free email verification to use the builder.", "共有リンクに入るのはブロックの設定（id・type・params・名前）だけです。生成コードやBSVのソースは含みません。URLの#以降に入るためサーバーには送信されず、変更していないひな形は名前だけで共有されます。開いた人がビルダーを使うには無料のメール確認が必要です。"), "p", "small")}</div>'
        f'<details class="source-block"><summary>{both(T("Recipe JSON (import / export)", "レシピJSON（読み込み・書き出し）"))}</summary><div class="source-toolbar"><button type="button" class="btn small-btn" id="rb-json-apply">Apply JSON</button><button type="button" class="btn small-btn" id="rb-dl-json">Download recipe JSON</button></div><textarea id="rb-json" spellcheck="false" aria-label="Recipe JSON"></textarea></details>'
        '</section><section class="rb-panel rb-sticky" aria-label="Generated code">'
        f'<h2>{both(T("3. Generated code", "3. 生成されたコード"))}</h2>'
        '<div class="rb-tabs" role="group" aria-label="Target">' + "".join(f'<button type="button" class="btn small-btn" data-rb-target="{t}" aria-pressed="{"true" if k == 0 else "false"}">{esc(lbl)}</button>' for k, (t, lbl, _) in enumerate(blt.TARGETS + BUILDER_EXTRA_TARGETS)) + '</div>'
        '<p id="rb-err" role="alert" hidden></p>'
        f'<details id="rb-lint" open><summary id="rb-lint-sum">Recipe check</summary><ul id="rb-lint-list"></ul><button type="button" class="btn small-btn" id="rb-lint-fix" hidden>{both(T("Fix order", "順序を修正"))}</button></details>'
        '<p class="small" id="rb-todo"></p>'
        f'<details id="rb-hints" open hidden><summary>{both(T("TODO hints for this target (per block)", "この出力先のTODOヒント（ブロック別）"))}</summary><ul id="rb-hint-list"></ul></details>'
        f'<details id="rb-check"><summary>{both(T("Compile checklist", "コンパイル確認リスト"))} — <span id="rb-check-target"></span></summary><ol id="rb-check-list"></ol>'
        f'<div id="rb-res"><p class="rb-res-h"><strong>{both(T("Record your result", "結果を記録"))}</strong></p>'
        f'<p class="small">{both(T("Your own record, saved in this browser. You may also send it to BSV: it then goes only to BSV's private review queue (signed-in account, at most 10 a day). Reviewers are the owner and BSV's review assistants; the assistants see your account id, not your email. Sent records are never published and never mark anything as verified; the catalog status stays \"Not runtime tested\". The fingerprint ties the record to the exact code shown.", "あなた自身の記録で、このブラウザ内に保存されます。BSVへ送ることもできます。送った記録はBSVの非公開の確認待ち一覧にだけ入ります（ログイン中のアカウント、1日10件まで）。確認するのはオーナーとBSVの確認アシスタントで、アシスタントに見えるのはアカウントIDだけです（メールアドレスは見えません）。公開されることはなく、何かが「検証済み」になることもありません。カタログの表示は「実行検証なし」のままです。指紋（fingerprint）で、表示中のコードと記録を対応づけます。"))}</p>'
        f'<label for="rb-res-status">{both(T("Result", "結果"))}</label><select id="rb-res-status"></select>'
        f'<label for="rb-res-platform">{both(T("Platform, version, build", "プラットフォーム・バージョン・ビルド"))}</label><input id="rb-res-platform" maxlength="120" autocomplete="off" placeholder="e.g. NinjaTrader 8.1.x">'
        f'<label for="rb-res-notes">{both(T("Notes (errors, fixes)", "メモ（エラー・直した点）"))}</label><textarea id="rb-res-notes" maxlength="1000" rows="3"></textarea>'
        '<div class="source-toolbar"><button type="button" class="btn small-btn" id="rb-res-save">Save record</button><button type="button" class="btn small-btn" id="rb-res-dl">Download .md</button><button type="button" class="btn small-btn" id="rb-res-clear">Clear this recipe</button><button type="button" class="btn small-btn" id="rb-res-send">Send to BSV (review)</button></div><p class="small" id="rb-res-sent" role="status" aria-live="polite"></p>'
        '<ul id="rb-res-list"></ul></div></details>'
        '<div class="source-toolbar"><button type="button" class="btn small-btn" id="rb-copy">Copy code</button><button type="button" class="btn small-btn" id="rb-dl">Download file</button></div>'
        '<pre id="rb-out" tabindex="0" aria-live="polite"></pre></section></div>'
        f'<p class="small">{both(T("Your draft is kept only in this browser (localStorage). Generator: trader-toolkit/generator/render.mjs (ORIGINAL BSV, MIT), ported unchanged to the browser.", "下書きはこのブラウザ内（localStorage）にだけ保存されます。ジェネレーター：trader-toolkit/generator/render.mjs（BSVオリジナル・MIT）をそのままブラウザに移植しています。"))}</p>'
        f'<p class="small"><a href="/trading/tools/{SLUG}.html">{both(T("← Back to the summary page", "← 解説ページへ戻る"))}</a></p></div>'
    )
    css = CSS.strip() + "\n"
    ch = hashlib.sha256(css.encode()).hexdigest()[:8]
    for old in (site / "trading/assets").glob(f"{SLUG}.*.css"):
        old.unlink()
    css_path = f"/trading/assets/{SLUG}.{ch}.css"
    blt.write(site / css_path.lstrip("/"), css)
    share_js = SHARE_STASH_JS.strip() + "\n"
    sh_h = hashlib.sha256(share_js.encode()).hexdigest()[:8]
    for old in (site / "trading/assets").glob(f"{SLUG}-share.*.js"):
        old.unlink()
    share_path = f"/trading/assets/{SLUG}-share.{sh_h}.js"
    blt.write(site / share_path.lstrip("/"), share_js)
    extra = f'<link rel="stylesheet" href="{css_path}"><script src="{js_path}" defer></script>'
    blt.write(site / f"trading/items/{SLUG}.html", blt.trader_shell(site, "Recipe builder — Build your own chart tool · BotShelf Vampire", "Edit recipe blocks and render Pine v6, MQL5, MQL4, cTrader (C# / Python) Bookmap Python, NinjaTrader 8, Quantower, Sierra Chart (ACSIL), ProRealTime, GoCharting (Lipi), MotiveWave (Java), Vela (JavaScript), JForex (Java), TradeStation (EasyLanguage), ATAS (C#), AmiBroker (AFL), thinkorswim (thinkScript), Tradovate (JavaScript), backtrader (Python), Backtesting.py (Python) and NautilusTrader (Python) starters in the browser.", f"/trading/tools/{SLUG}.html", body, robots="noindex,nofollow", extra_head=extra))

    # ---- public summary page (no generator code)
    nxt = f"/trading/register.html?next=%2Ftrading%2Fitems%2F{SLUG}.html"
    pub = (
        f'<div class="container detail"><div class="breadcrumb"><a href="/trading/">← Traders Library</a> / <a href="/trading/build/">{both(T("Build your own chart tool", "自分のチャートツールを作る"))}</a> / {both(T("Recipe builder", "レシピビルダー"))}</div>'
        f'<article class="prose"><div class="badges"><span class="badge">TradingView · MT5 · MT4 · cTrader · Bookmap · NinjaTrader · Quantower</span><span class="badge license">MIT</span><span class="badge">FREE</span></div>'
        f'<h1 class="detail-title">{both(T("Recipe builder (in your browser)", "レシピビルダー（ブラウザで動作）"))}</h1>'
        f'{both(T("Edit indicator, signal, plot and alert blocks in a form and get Pine v6, MQL5, MQL4, cTrader C# / Python, Bookmap Python, NinjaTrader 8, Quantower, Sierra Chart (ACSIL), ProRealTime, GoCharting (Lipi), MotiveWave (Java), Vela (JavaScript), JForex (Java), TradeStation (EasyLanguage), ATAS (C#), AmiBroker (AFL), thinkorswim (thinkScript), Tradovate (JavaScript), backtrader (Python), Backtesting.py (Python) and NautilusTrader (Python) starters generated instantly in your browser — the same BSV generator used for the pre-built recipes.", "指標・シグナル・プロット・アラートのブロックをフォームで編集すると、Pine v6・MQL5・MQL4・cTrader（C#／Python）・Bookmap（Python）・NinjaTrader 8・Quantower・Sierra Chart（ACSIL）・ProRealTime・GoCharting（Lipi）・MotiveWave（Java）・Vela（JavaScript）・JForex（Java）・TradeStation（EasyLanguage）・ATAS（C#）・AmiBroker（AFL）・thinkorswim（thinkScript）・Tradovate（JavaScript）・backtrader（Python）・Backtesting.py（Python）・NautilusTrader（Python）のひな形がブラウザ内ですぐ生成されます。生成済みレシピと同じBSVジェネレーターです。"), "p", "detail-lead")}'
        f'<p><span class="bb-status bb-warn">{both(T("Browser port of the repository generator — output not runtime tested", "リポジトリのジェネレーターをブラウザに移植・出力は実行検証なし"))}</span> <span class="bb-orig">ORIGINAL BSV SOURCE</span></p>'
        f'<div class="notice" id="rb-shared-note" hidden><p>{both(T("This link carries a shared recipe (block settings only). It opens automatically in the builder after free email verification; until then it is kept only in this browser for 24 hours.", "このリンクには共有されたレシピ（ブロックの設定のみ）が入っています。無料のメール確認後、ビルダーで自動的に開きます。それまではこのブラウザ内に24時間だけ保存されます。"))}</p></div>'
        f'<p><a class="btn primary" href="{nxt}" data-source-access="{SLUG}">{both(T("Open the builder — free email verification", "ビルダーを開く（無料のメール確認）"))}</a></p>'
        f'{both(T("The explanation is public. Using the builder (it contains the generator source) requires free email verification. Free stays free.", "解説は登録なしで読めます。ビルダー（ジェネレーターのソースを含みます）の利用には無料のメール確認が必要です。無料のものは無料のままです。"), "p", "small")}'
        f'<h2>{both(T("What you can do", "できること"))}</h2><ul data-lang="en"><li>Start from one of {n_rec} starter recipes or a blank recipe.</li><li>Add, remove, reorder and edit blocks: EMA, SMA, RSI, ATR, session filter, cross, threshold, combine, plot, alert.</li><li>Switch the target between Pine v6, MQL5, MQL4, cTrader C# / Python, Bookmap Python, NinjaTrader 8, Quantower, Sierra Chart (ACSIL), ProRealTime, GoCharting (Lipi), MotiveWave (Java), Vela (JavaScript), JForex (Java), TradeStation (EasyLanguage), ATAS (C#), AmiBroker (AFL), thinkorswim (thinkScript), Tradovate (JavaScript), backtrader (Python), Backtesting.py (Python) and NautilusTrader (Python) and see the TODO count for blocks a target cannot express yet.</li><li>Copy or download the code and the recipe JSON. Drafts stay in your browser.</li><li>Get a recipe check (unused blocks, blocks used before they are defined, value-vs-condition mix-ups) with one-click fixes, and a compile checklist for the selected platform where you can record your own result (kept in your browser; BSV does not verify it).</li><li>See per-block TODO hints for the selected target, and share your own recipe as a link or JSON file (block settings only — never generated code or BSV source).</li></ul>'
        f'<ul data-lang="ja"><li>{n_rec}種類のひな形レシピか、白紙から始められます。</li><li>ブロック（EMA・SMA・RSI・ATR・時間帯フィルター・クロス・しきい値・組み合わせ・プロット・アラート）の追加・削除・並べ替え・編集ができます。</li><li>出力先をPine v6・MQL5・MQL4・cTrader（C#／Python）・Bookmap（Python）・NinjaTrader 8・Quantower・Sierra Chart（ACSIL）・ProRealTime・GoCharting（Lipi）・MotiveWave（Java）・Vela（JavaScript）・JForex（Java）・TradeStation（EasyLanguage）・ATAS（C#）・AmiBroker（AFL）・thinkorswim（thinkScript）・Tradovate（JavaScript）・backtrader（Python）・Backtesting.py（Python）・NautilusTrader（Python）で切り替え、出力先でまだ表現できないブロックのTODO数を確認できます。</li><li>コードとレシピJSONをコピー・ダウンロードできます。下書きはブラウザ内に保存されます。</li><li>レシピの点検（使われていないブロック、定義より前での参照、値と条件の取り違え）とワンクリック修正、選んだプラットフォーム向けのコンパイル確認リストを表示します。結果は自分で記録できます（ブラウザ内に保存され、BSVは検証しません）。</li><li>選んだ出力先のTODOヒントをブロックごとに確認でき、自分のレシピをリンクやJSONファイルで共有できます（ブロックの設定のみ。生成コードやBSVのソースは含みません）。</li></ul>'
        f'<h2>{both(T("Verification status", "検証状態"))}</h2><table class="qa-table"><tbody>'
        f'<tr><td>{both(T("Generator parity", "ジェネレーターとの一致"))}</td><td>{both(T("Browser output is byte-identical to the repository generator for every starter recipe and target (automated check).", "すべてのひな形レシピと出力先で、ブラウザの出力がリポジトリのジェネレーターと完全に一致することを自動確認しています。"))}</td></tr>'
        f'<tr><td>{both(T("Compile on the platform", "プラットフォームでのコンパイル"))}</td><td>{both(T("Not performed by BSV", "BSVでは未実施"))}</td></tr>'
        f'<tr><td>{both(T("Backtest / demo / live run", "バックテスト・デモ・実運用"))}</td><td>{both(T("Not performed", "未実施"))}</td></tr></tbody></table>'
        f'<p class="small"><a href="/trading/build/">{both(T("← Build your own chart tool", "← 自分のチャートツールを作る"))}</a></p></article></div>'
    )
    blt.write(site / f"trading/tools/{SLUG}.html", blt.trader_shell(site, "Recipe builder (browser) — Build your own chart tool · BotShelf Vampire", "Edit recipe blocks and generate Pine v6, MQL5, MQL4, cTrader (C# / Python) Bookmap Python, NinjaTrader 8, Quantower, Sierra Chart (ACSIL), ProRealTime, GoCharting (Lipi), MotiveWave (Java), Vela (JavaScript), JForex (Java), TradeStation (EasyLanguage), ATAS (C#), AmiBroker (AFL), thinkorswim (thinkScript), Tradovate (JavaScript), backtrader (Python), Backtesting.py (Python) and NautilusTrader (Python) starters in your browser. Free with email verification.", f"/trading/tools/{SLUG}.html", pub, extra_head=f'<script src="{share_path}" defer></script>'))

    # ---- entry in the existing build hub
    hp = site / "trading/build/index.html"
    hub = hp.read_text()
    entry = (f'<section class="container bb-section" id="builder"><div class="bb-entry"><div><p class="eyebrow">{both(T("New · in your browser", "新着・ブラウザで動作"))}</p>'
             f'<h2>{both(T("Recipe builder", "レシピビルダー"))}</h2>{both(T("Edit blocks in a form and get Pine v6 / MQL5 / MQL4 / cTrader / Bookmap / NinjaTrader / Quantower starters instantly. Free with email verification.", "ブロックをフォームで編集すると、Pine v6・MQL5・MQL4・cTrader・Bookmap・NinjaTrader・Quantowerのひな形がすぐ生成されます。無料のメール確認で使えます。"), "p")}</div>'
             f'<a class="btn primary" href="/trading/tools/{SLUG}.html">{both(T("Open recipe builder", "レシピビルダーへ"))}</a></div></section>')
    hub = blt.replace_block(hub, "recipe-builder", entry, '<section class="container bb-section" id="paths">')
    hp.write_text(hub, encoding="utf-8")

    # ---- search row + sitemap
    sh = (site / "search/index.html").read_text()
    pj = (site / "js" / re.search(r"/js/(bsv-search-page\.v[0-9a-z]+\.js)", sh).group(1)).read_text()
    ip = site / "search" / re.search(r"(index\.v[0-9a-z]+\.json)", pj).group(1)
    idx = json.loads(ip.read_text())
    idx["rows"] = [r for r in idx["rows"] if r.get("id") != SLUG] + [{
        "s": "trading", "id": SLUG, "t": "Recipe builder (browser)", "k": "Builder", "kj": "ビルダー", "c": "Build your own chart tool",
        "p": ["TradingView", "MT5", "MT4", "cTrader", "Bookmap", "NinjaTrader", "Quantower", "Sierra Chart", "ProRealTime", "GoCharting", "MotiveWave", "Vela", "JForex", "TradeStation", "ATAS", "AmiBroker", "thinkorswim", "Tradovate", "backtrader", "Backtesting.py", "NautilusTrader"], "d": "Edit recipe blocks and generate Pine v6, MQL5, MQL4, cTrader, Bookmap, NinjaTrader, Quantower, Sierra Chart, ProRealTime, GoCharting, MotiveWave and Vela starters in your browser.",
        "dj": "レシピのブロックを編集して、Pine v6・MQL5・MQL4・cTrader・Bookmap・NinjaTrader・Quantowerのひな形をブラウザで生成します。", "x": "recipe builder generator editor pine mql5 mql4 mt4 ctrader python bookmap ninjatrader ninjascript quantower ORIGINAL BSV MIT",
        "u": f"/trading/tools/{SLUG}.html", "uj": f"/trading/tools/{SLUG}.html?lang=ja", "a": "free"}]
    ip.write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    smp = site / "sitemap.xml"
    sm = smp.read_text()
    loc = f"<loc>{blt.ORIGIN}/trading/tools/{SLUG}.html</loc>"
    if loc not in sm:
        smp.write_text(sm.replace("</urlset>", f"<url>{loc}<lastmod>2026-10-03</lastmod></url></urlset>"), encoding="utf-8")
    print(json.dumps({"gated_page": f"/trading/items/{SLUG}.html", "gated_js": js_path, "public_page": f"/trading/tools/{SLUG}.html", "recipes": n_rec}))


if __name__ == "__main__":
    main()
