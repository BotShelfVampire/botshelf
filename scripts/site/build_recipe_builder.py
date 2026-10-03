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
var EXT={'pine-v6':'.pine','mql5':'.mq5','ctrader':'.cs','mql4':'.mq4','ctrader-python':'.py','bookmap-python':'.py'};
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
 $('#rb-out').textContent=out;var todo=(out.match(/TODO/g)||[]).length;$('#rb-todo').textContent=out?('TODO markers: '+todo):'';renderHints(out);
 ['#rb-copy','#rb-dl'].forEach(function(s){$(s).disabled=!out})}
function load(r){state.recipe=clone(r);if(!Array.isArray(state.recipe.blocks))state.recipe.blocks=[];draw()}
function toast(t){var e=$('#toast');if(!e)return;e.textContent=t;e.hidden=false;setTimeout(function(){e.hidden=true},1600)}
function download(name,text){var a=el('a',{href:URL.createObjectURL(new Blob([text],{type:'text/plain'})),download:name});document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},500)}
function fileBase(){return (state.recipe.name||'bsv-recipe').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'bsv-recipe'}
// ---- builder v2: per-block TODO hints + shareable recipe JSON (config only, no generated code, no server storage)
var SHARE_MAX=6000,PENDING='bsv-rb-pending-share',PREV=KEY+'-prev';
var HINTS={
 'filter.session':['Session windows depend on timezone: MT4/MT5 use broker server time; the cTrader Python and Bookmap outputs use UTC. Convert the session before relying on alerts.','時間帯の判定はタイムゾーン次第です。MT4・MT5はブローカーのサーバー時間、cTrader PythonとBookmapの出力はUTCで判定します。アラートに使う前に時間帯を換算してください。'],
 'signal.cross':['Cross = left is above (or below) right on this bar but was not on the previous bar. Where a target leaves it as TODO, compare current and previous values of both inputs.','クロスは「この足で左が右を上抜け（下抜け）し、1本前はそうでなかった」状態です。TODOが残る出力先では、両方の値の現在と1本前を比べて判定します。'],
 'signal.threshold':['Compares one value with a fixed number. Check the value range on your platform (for example RSI 0-100).','1つの値を固定の数値と比べます。プラットフォームでの値の範囲（例：RSIは0〜100）を確認してください。'],
 'signal.combine':['all = every listed signal is true on the same bar; any = at least one. Referenced ids must exist above this block.','all は列挙したシグナルが同じ足ですべて成立、any は1つ以上成立。参照するidはこのブロックより上に必要です。'],
 'indicator.ema':['If the source is ohlc4, some targets fall back to close (see the TODO); compute (open+high+low+close)/4 or pick hl2 / hlc3.','sourceがohlc4の場合、一部の出力先はcloseで代用します（TODO参照）。(始値+高値+安値+終値)/4を自分で計算するか、hl2・hlc3を選んでください。'],
 'indicator.sma':['If the source is ohlc4, some targets fall back to close (see the TODO).','sourceがohlc4の場合、一部の出力先はcloseで代用します（TODO参照）。'],
 'indicator.rsi':['If the source is ohlc4, some targets fall back to close (see the TODO).','sourceがohlc4の場合、一部の出力先はcloseで代用します（TODO参照）。'],
 'indicator.atr':['ATR smoothing differs by platform (Wilder vs simple); compare values with the platform built-in ATR.','ATRの平滑化方法はプラットフォームで異なります（Wilder／単純平均）。組み込みのATRと値を見比べてください。'],
 'visual.plot':['Plots draw a value block as a line. On Bookmap, overlay lines are price levels.','値ブロックを線として描きます。Bookmapでは重ね表示の線は価格水準として描かれます。'],
 'alert.condition':['MQL4 and cTrader Python alert once per closed bar; Pine needs an alert set up in TradingView. Check alert frequency before use.','MQL4とcTrader Pythonは確定足ごとに1回通知します。PineはTradingView側でアラート設定が必要です。使う前に通知頻度を確認してください。'],
 'alert.webhook':['Webhooks: Pine alert() plus a TradingView webhook URL. On MT4/MT5, WebRequest only runs in Expert Advisors/scripts (not indicators) and the URL must be allow-listed. Never put secrets in the message.','Webhook：PineはalertとTradingViewのWebhook URLで送ります。MT4・MT5のWebRequestはEA・スクリプトでのみ動き（インジケーター不可）、URLの許可設定が必要です。メッセージに秘密情報を入れないでください。'],
 'data.higher_timeframe':['Request higher-timeframe bars (Pine request.security, MQL iMA with a timeframe argument, cTrader MarketData.GetBars) and use only closed higher-timeframe bars to avoid lookahead.','上位足のデータを取得します（Pineはrequest.security、MQLは時間足を指定したiMA、cTraderはMarketData.GetBars）。先読みを避けるため確定した上位足だけを使います。'],
 'structure.pivot':['A pivot is a bar whose high/low is the extreme of N bars on each side; it is confirmed only N bars later.','ピボットは左右N本の中で高値・安値が最も外側の足です。確定するのはN本後です。'],
 'structure.range':['Track the high/low of a defined window (for example the opening range) and reset it each session.','決めた時間帯（例：寄り付きレンジ）の高値・安値を記録し、セッションごとにリセットします。'],
 'signal.breakout':['Breakout = close beyond a range or pivot level. Decide close vs intrabar and how to avoid repeated alerts.','ブレイクアウトはレンジやピボットの水準を終値で超えることです。終値判定か足の途中で判定するか、通知の重複をどう防ぐかを決めます。'],
 'signal.liquidity_sweep':['Sweep candidate = wick beyond a prior high/low with a close back inside. Label it as a candidate only.','スイープ候補は、前の高値・安値をヒゲで超えて終値で内側に戻った足です。あくまで候補として表示します。'],
 'signal.divergence':['Compare price pivots with oscillator pivots; a divergence is confirmed only after the right-side pivot bars close.','価格のピボットとオシレーターのピボットを比べます。右側のピボットが確定してから成立です。'],
 'risk.atr_band':['Band = reference value plus/minus ATR x multiple. Plot it; do not place orders from an indicator.','バンドは基準値±ATR×倍率です。描画に使い、インジケーターから注文は出しません。'],
 'scanner.symbol_set':['Multi-symbol scanning needs platform APIs (Pine request.security per symbol, MQL SymbolSelect + iClose, cTrader MarketData.GetBars with a symbol).','複数銘柄のスキャンにはプラットフォームのAPIが必要です（Pineは銘柄ごとのrequest.security、MQLはSymbolSelectとiClose、cTraderは銘柄指定のMarketData.GetBars）。'],
 'visual.zone':['Draw a box/rectangle object between two levels and keep the number of objects bounded.','2つの水準の間に矩形オブジェクトを描きます。オブジェクト数が増え続けないようにします。'],
 'visual.table':['Use the platform panel API (Pine table.new, MQL ObjectCreate with OBJ_LABEL, cTrader Chart.DrawStaticText).','プラットフォームの表示API（Pineはtable.new、MQLはOBJ_LABELのObjectCreate、cTraderはChart.DrawStaticText）を使います。']};
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
function init(){if(!$('#rb-app'))return;
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
 if(initShare())return;
 var d=null;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){}
 var ok=null;try{ok=d?sanitize(d).recipe:null}catch(e){}
 load(ok||RECIPES[0]);}
root.BSVBuilder={sanitize:sanitize,sharePayload:sharePayload,readPayload:readPayload,todoMap:todoMap,hints:HINTS,b64e:b64e,b64d:b64d};
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
            "\nvar RENDER={'pine-v6':renderPine,'mql5':renderMql5,'ctrader':renderCTrader,'mql4':renderMql4,'ctrader-python':renderCTraderPython,'bookmap-python':renderBookmapPython};\n"
            f"var RECIPES={json.dumps(recipes, ensure_ascii=False)};\nvar RECIPE_IDS={json.dumps([p.stem for p in rfiles])};\nvar TYPES={json.dumps(types)};\n"
            "root.BSVRender={validate:validateRecipe,render:function(r,t){validateRecipe(r);return RENDER[t](r)},recipes:RECIPES,types:TYPES};\n"
            + UI_JS.replace("__PRICE__", json.dumps(PRICE)) + "\n})(typeof window!=='undefined'?window:globalThis);\n")


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
        f'{both(T("Pick a starter or start blank, edit the blocks, and the BSV generator renders TradingView Pine v6, MT5 MQL5, MT4 MQL4, cTrader C#, cTrader Python and Bookmap Python right here in your browser. Nothing is sent to a server.", "ひな形を選ぶか白紙から始めてブロックを編集すると、BSVジェネレーターがTradingView（Pine v6）・MT5（MQL5）・MT4（MQL4）・cTrader（C#／Python）・Bookmap（Python）のコードをこのブラウザ内で生成します。サーバーには何も送信しません。"), "p", "detail-lead")}'
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
        '<div class="rb-tabs" role="group" aria-label="Target"><button type="button" class="btn small-btn" data-rb-target="pine-v6" aria-pressed="true">TradingView · Pine v6</button><button type="button" class="btn small-btn" data-rb-target="mql5" aria-pressed="false">MT5 · MQL5</button><button type="button" class="btn small-btn" data-rb-target="ctrader" aria-pressed="false">cTrader · C#</button><button type="button" class="btn small-btn" data-rb-target="mql4" aria-pressed="false">MT4 · MQL4</button><button type="button" class="btn small-btn" data-rb-target="ctrader-python" aria-pressed="false">cTrader · Python</button><button type="button" class="btn small-btn" data-rb-target="bookmap-python" aria-pressed="false">Bookmap · Python</button></div>'
        '<p id="rb-err" role="alert" hidden></p><p class="small" id="rb-todo"></p>'
        f'<details id="rb-hints" open hidden><summary>{both(T("TODO hints for this target (per block)", "この出力先のTODOヒント（ブロック別）"))}</summary><ul id="rb-hint-list"></ul></details>'
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
    blt.write(site / f"trading/items/{SLUG}.html", blt.trader_shell(site, "Recipe builder — Build your own chart tool · BotShelf Vampire", "Edit recipe blocks and render Pine v6, MQL5, MQL4, cTrader (C# / Python) and Bookmap Python starters in the browser.", f"/trading/tools/{SLUG}.html", body, robots="noindex,nofollow", extra_head=extra))

    # ---- public summary page (no generator code)
    nxt = f"/trading/register.html?next=%2Ftrading%2Fitems%2F{SLUG}.html"
    pub = (
        f'<div class="container detail"><div class="breadcrumb"><a href="/trading/">← Traders Library</a> / <a href="/trading/build/">{both(T("Build your own chart tool", "自分のチャートツールを作る"))}</a> / {both(T("Recipe builder", "レシピビルダー"))}</div>'
        f'<article class="prose"><div class="badges"><span class="badge">TradingView · MT5 · MT4 · cTrader · Bookmap</span><span class="badge license">MIT</span><span class="badge">FREE</span></div>'
        f'<h1 class="detail-title">{both(T("Recipe builder (in your browser)", "レシピビルダー（ブラウザで動作）"))}</h1>'
        f'{both(T("Edit indicator, signal, plot and alert blocks in a form and get Pine v6, MQL5, MQL4, cTrader C#, cTrader Python and Bookmap Python starters generated instantly in your browser — the same BSV generator used for the pre-built recipes.", "指標・シグナル・プロット・アラートのブロックをフォームで編集すると、Pine v6・MQL5・MQL4・cTrader（C#／Python）・Bookmap（Python）のひな形がブラウザ内ですぐ生成されます。生成済みレシピと同じBSVジェネレーターです。"), "p", "detail-lead")}'
        f'<p><span class="bb-status bb-warn">{both(T("Browser port of the repository generator — output not runtime tested", "リポジトリのジェネレーターをブラウザに移植・出力は実行検証なし"))}</span> <span class="bb-orig">ORIGINAL BSV SOURCE</span></p>'
        f'<div class="notice" id="rb-shared-note" hidden><p>{both(T("This link carries a shared recipe (block settings only). It opens automatically in the builder after free email verification; until then it is kept only in this browser for 24 hours.", "このリンクには共有されたレシピ（ブロックの設定のみ）が入っています。無料のメール確認後、ビルダーで自動的に開きます。それまではこのブラウザ内に24時間だけ保存されます。"))}</p></div>'
        f'<p><a class="btn primary" href="{nxt}" data-source-access="{SLUG}">{both(T("Open the builder — free email verification", "ビルダーを開く（無料のメール確認）"))}</a></p>'
        f'{both(T("The explanation is public. Using the builder (it contains the generator source) requires free email verification. Free stays free.", "解説は登録なしで読めます。ビルダー（ジェネレーターのソースを含みます）の利用には無料のメール確認が必要です。無料のものは無料のままです。"), "p", "small")}'
        f'<h2>{both(T("What you can do", "できること"))}</h2><ul data-lang="en"><li>Start from one of {n_rec} starter recipes or a blank recipe.</li><li>Add, remove, reorder and edit blocks: EMA, SMA, RSI, ATR, session filter, cross, threshold, combine, plot, alert.</li><li>Switch the target between Pine v6, MQL5, MQL4, cTrader C#, cTrader Python and Bookmap Python and see the TODO count for blocks a target cannot express yet.</li><li>Copy or download the code and the recipe JSON. Drafts stay in your browser.</li><li>See per-block TODO hints for the selected target, and share your own recipe as a link or JSON file (block settings only — never generated code or BSV source).</li></ul>'
        f'<ul data-lang="ja"><li>{n_rec}種類のひな形レシピか、白紙から始められます。</li><li>ブロック（EMA・SMA・RSI・ATR・時間帯フィルター・クロス・しきい値・組み合わせ・プロット・アラート）の追加・削除・並べ替え・編集ができます。</li><li>出力先をPine v6・MQL5・MQL4・cTrader（C#／Python）・Bookmap（Python）で切り替え、出力先でまだ表現できないブロックのTODO数を確認できます。</li><li>コードとレシピJSONをコピー・ダウンロードできます。下書きはブラウザ内に保存されます。</li><li>選んだ出力先のTODOヒントをブロックごとに確認でき、自分のレシピをリンクやJSONファイルで共有できます（ブロックの設定のみ。生成コードやBSVのソースは含みません）。</li></ul>'
        f'<h2>{both(T("Verification status", "検証状態"))}</h2><table class="qa-table"><tbody>'
        f'<tr><td>{both(T("Generator parity", "ジェネレーターとの一致"))}</td><td>{both(T("Browser output is byte-identical to the repository generator for every starter recipe and target (automated check).", "すべてのひな形レシピと出力先で、ブラウザの出力がリポジトリのジェネレーターと完全に一致することを自動確認しています。"))}</td></tr>'
        f'<tr><td>{both(T("Compile on the platform", "プラットフォームでのコンパイル"))}</td><td>{both(T("Not performed by BSV", "BSVでは未実施"))}</td></tr>'
        f'<tr><td>{both(T("Backtest / demo / live run", "バックテスト・デモ・実運用"))}</td><td>{both(T("Not performed", "未実施"))}</td></tr></tbody></table>'
        f'<p class="small"><a href="/trading/build/">{both(T("← Build your own chart tool", "← 自分のチャートツールを作る"))}</a></p></article></div>'
    )
    blt.write(site / f"trading/tools/{SLUG}.html", blt.trader_shell(site, "Recipe builder (browser) — Build your own chart tool · BotShelf Vampire", "Edit recipe blocks and generate Pine v6, MQL5, MQL4, cTrader (C# / Python) and Bookmap Python starters in your browser. Free with email verification.", f"/trading/tools/{SLUG}.html", pub, extra_head=f'<script src="{share_path}" defer></script>'))

    # ---- entry in the existing build hub
    hp = site / "trading/build/index.html"
    hub = hp.read_text()
    entry = (f'<section class="container bb-section" id="builder"><div class="bb-entry"><div><p class="eyebrow">{both(T("New · in your browser", "新着・ブラウザで動作"))}</p>'
             f'<h2>{both(T("Recipe builder", "レシピビルダー"))}</h2>{both(T("Edit blocks in a form and get Pine v6 / MQL5 / MQL4 / cTrader / Bookmap starters instantly. Free with email verification.", "ブロックをフォームで編集すると、Pine v6・MQL5・MQL4・cTrader・Bookmapのひな形がすぐ生成されます。無料のメール確認で使えます。"), "p")}</div>'
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
        "p": ["TradingView", "MT5", "MT4", "cTrader", "Bookmap"], "d": "Edit recipe blocks and generate Pine v6, MQL5, MQL4, cTrader and Bookmap starters in your browser.",
        "dj": "レシピのブロックを編集して、Pine v6・MQL5・MQL4・cTrader・Bookmapのひな形をブラウザで生成します。", "x": "recipe builder generator editor pine mql5 mql4 mt4 ctrader python bookmap ORIGINAL BSV MIT",
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
