/* Public metadata/search presentation only. Never authenticate or deliver source here. */
(()=>{'use strict';
const root=document.querySelector('[data-bsv-trader-home]');
if(!root)return;
const $=s=>root.querySelector(s),all=s=>[...root.querySelectorAll(s)];
const lang=()=>document.documentElement.lang.toLowerCase().startsWith('ja')?'ja':'en';
const tr=(ja,en)=>lang()==='ja'?ja:en;
const kinds={ea:['EA・自動売買','EA / bot'],indicator:['インジケーター','Indicator'],strategy:['ストラテジー','Strategy'],template:['開発ひな形','Template'],'trade-manager':['取引管理','Trade manager']};
const aliases={ea:'ea expert advisor 自動売買 bot cbot',indicator:'indicator indicators インジケーター 指標',strategy:'strategy strategies ストラテジー 戦略',template:'template ひな形 開発','trade-manager':'trade management 取引管理'};
const categories={'Breakout':'breakout ブレイクアウト 高安','Trend':'trend トレンド 移動平均','Momentum':'momentum モメンタム 勢い','Mean reversion':'mean reversion 逆張り 回帰','Volume':'volume 出来高','Volatility':'volatility ボラティリティ 値幅','Price action':'price action プライスアクション スパイク','Research':'research 研究','Development':'development 開発','Chart tools':'chart tools チャート'};
const norm=v=>String(v||'').normalize('NFKC').toLocaleLowerCase();
const state={rows:[],q:'',kind:'',platform:'',mode:'free',limit:12,unavailable:false,rejected:0};
function safeRow(d){
 if(!d||d.namespace!=='trading'||typeof d.id!=='string'||!/^[a-z0-9][a-z0-9_-]{0,100}$/i.test(d.id))return null;
 if(!kinds[d.kind]||!['free','paid'].includes(d.mode)||!Array.isArray(d.platforms)||!d.platforms.length||d.platforms.some(p=>typeof p!=='string'||p.length>70))return null;
 if(typeof d.title!=='string'||!d.title.trim()||d.title.length>180||!d.summary||typeof d.summary.ja!=='string'||typeof d.summary.en!=='string')return null;
 if(typeof d.href!=='string'||!/^\/trading\/(?:items\/[a-z0-9_-]+\.html|community\.html\?id=[a-z0-9_-]+)$/.test(d.href))return null;
 if(d.mode==='paid'&&(d.currency!=='USDT'||d.network!=='TRC20'||d.billingInterval!=='month'||!/^\d{1,20}$/.test(d.priceMicros||'')||BigInt(d.priceMicros)<=0n))return null;
 // An explicit allowlist prevents accidentally retaining source or private evidence.
 return {id:d.id,title:d.title,kind:d.kind,platforms:[...d.platforms],summary:{ja:d.summary.ja.slice(0,900),en:d.summary.en.slice(0,900)},category:String(d.category||''),mode:d.mode,accessMode:['open','protected','invite-only'].includes(d.accessMode)?d.accessMode:'open',author:String(d.author||'').slice(0,100),license:String(d.license||'').slice(0,100),version:String(d.version||'').slice(0,100),validation:['not-run','compiled','runtime-tested'].includes(d.validation)?d.validation:'not-run',href:d.href,priceMicros:d.priceMicros||'0',namespace:'trading'};
}
function price(d){if(d.mode==='free')return tr('無料','Free');const a=BigInt(d.priceMicros),frac=(a%1000000n).toString().padStart(6,'0').replace(/0+$/,'');return `${a/1000000n}${frac?'.'+frac:''} USDT${tr(' / 月',' / month')}`;}
function filtered(){const tokens=norm(state.q).split(/[\s、,]+/).filter(Boolean);return state.rows.filter(d=>{const text=norm([d.title,d.summary.ja,d.summary.en,d.author,d.version,d.platforms.join(' '),aliases[d.kind],categories[d.category],d.mode==='free'?'free 無料':'monthly paid 月額 有料'].join(' '));return tokens.every(t=>text.includes(t))&&(!state.kind||state.kind===d.kind)&&(!state.platform||d.platforms.includes(state.platform))&&(!state.mode||state.mode===d.mode);});}
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function card(d){const a=el('article','bsv-hub-card');a.dataset.bsvTradingCard=d.id;const top=el('div','bsv-hub-card-top');top.append(el('span','bsv-hub-kind',kinds[d.kind][lang()==='ja'?0:1]),el('span','bsv-hub-price',price(d)));const title=el('h4'),link=el('a','',d.title);link.href=d.href;title.append(link);const footer=el('div','bsv-hub-card-footer');const label=d.validation==='not-run'?tr('実行未検証','Runtime untested'):d.validation==='compiled'?tr('コンパイル確認のみ','Compile check only'):tr('実行条件は詳細へ','See runtime test scope');const dest=el('a','',tr('使い方を見る →','View setup →'));dest.href=d.href;footer.append(el('span','',label),dest);a.append(top,title,el('p','',d.summary[lang()]),el('div','bsv-hub-card-platform',d.platforms.join(' / ')+' · '+d.version),footer);return a;}
function render(){const errorBox=$('[data-bsv-load-error]');if(errorBox)errorBox.hidden=!state.unavailable;if(state.unavailable){$('[data-bsv-trader-grid]').replaceChildren();$('[data-bsv-empty]').hidden=true;$('[data-bsv-more]').hidden=true;$('[data-bsv-result-count]').textContent=tr('一覧を取得できません','Catalogue unavailable');return;}const rows=filtered(),grid=$('[data-bsv-trader-grid]');grid.replaceChildren(...rows.slice(0,state.limit).map(card));$('[data-bsv-empty]').hidden=rows.length!==0;$('[data-bsv-more]').hidden=state.limit>=rows.length;const n=Math.min(rows.length,state.limit),suffix=root.dataset.review==='true'?tr(' · 確認版の件数',' · review inventory'):'';$('[data-bsv-result-count]').textContent=tr(`${rows.length}件中 ${n}件を表示`,`${n} of ${rows.length} tools`)+suffix+(state.rejected?tr(' · 一部の項目を表示できません',' · some records unavailable'):'');}
function refreshPlatforms(){const s=$('[data-bsv-platform]'),first=s.options[0];s.replaceChildren(first);[...new Set(state.rows.flatMap(d=>d.platforms))].sort().forEach(p=>s.add(new Option(p,p)));s.value=state.platform;if(s.value!==state.platform)state.platform='';}
function showUnavailable(){state.unavailable=true;render();}
function replaceCatalogue(input){if(!Array.isArray(input)){showUnavailable();return;}const seen=new Set();state.rejected=0;state.rows=input.map(safeRow).filter(d=>{if(!d){state.rejected++;return false;}if(seen.has(d.id))return false;seen.add(d.id);return true;});if(input.length&&!state.rows.length){showUnavailable();return;}state.unavailable=false;state.limit=12;refreshPlatforms();render();}
try{const data=$('[data-bsv-home-trader-data]');if(root.dataset.catalogueReady==='false'||!data)showUnavailable();else replaceCatalogue(JSON.parse(data.textContent));}catch{showUnavailable();}
$('[data-bsv-trader-search]').addEventListener('submit',e=>{e.preventDefault();state.q=$('#bsv-trader-query').value;state.limit=12;render();});
$('#bsv-trader-query').addEventListener('input',e=>{state.q=e.target.value;state.limit=12;render();});
all('[data-bsv-kind]').forEach(b=>b.addEventListener('click',()=>{state.kind=b.dataset.bsvKind;state.limit=12;all('[data-bsv-kind]').forEach(v=>v.setAttribute('aria-pressed',String(v===b)));render();}));
$('[data-bsv-platform]').addEventListener('change',e=>{state.platform=e.target.value;state.limit=12;render();});
$('[data-bsv-price]').addEventListener('change',e=>{state.mode=e.target.value;state.limit=12;render();});
$('[data-bsv-more]').addEventListener('click',()=>{state.limit+=12;render();});
$('[data-bsv-reset]').addEventListener('click',()=>{state.q='';state.kind='';state.platform='';state.mode='free';state.limit=12;$('#bsv-trader-query').value='';$('[data-bsv-platform]').value='';$('[data-bsv-price]').value='free';all('[data-bsv-kind]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.bsvKind==='')));render();$('#bsv-trader-query').focus();});
// AI search never queries the trading dataset or modifies trader card visibility.
// The integrator marks existing AI card nodes without replacing their contents.
const ai=document.querySelector('[data-bsv-ai-home]');
function renderAI(){if(!ai)return;const q=norm(ai.querySelector('[name=ai_q]')?.value).split(/\s+/).filter(Boolean),cards=[...ai.querySelectorAll('[data-bsv-ai-card]')];let count=0;cards.forEach(c=>{const text=norm(c.dataset.bsvAiSearchText||c.textContent);c.hidden=!q.every(t=>text.includes(t));if(!c.hidden)count++;});const status=ai.querySelector('[data-bsv-ai-result-count]');if(status)status.textContent=cards.length?tr(`${count}件を表示`,`${count} shown`):'';const empty=ai.querySelector('[data-bsv-ai-empty]');if(empty)empty.hidden=count!==0||cards.length===0;}
if(ai){ai.querySelector('[data-bsv-ai-search]')?.addEventListener('submit',e=>{e.preventDefault();renderAI();});ai.querySelector('[name=ai_q]')?.addEventListener('input',renderAI);renderAI();}
function refreshLanguage(){document.querySelectorAll('[data-bsv-placeholder-ja]').forEach(e=>{e.placeholder=e.getAttribute('data-bsv-placeholder-'+lang());});document.querySelectorAll('[data-bsv-label-ja]').forEach(e=>e.setAttribute('aria-label',e.getAttribute('data-bsv-label-'+lang())));root.querySelectorAll('option[data-ja]').forEach(o=>{o.textContent=o.dataset[lang()];});render();renderAI();}
const observer=new MutationObserver(()=>refreshLanguage());observer.observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
function active(area){document.querySelectorAll('[data-bsv-audience-nav] [data-bsv-area]').forEach(a=>{if(a.dataset.bsvArea===area)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});}
document.querySelectorAll('[data-bsv-area]').forEach(a=>a.addEventListener('click',()=>active(a.dataset.bsvArea)));
if('IntersectionObserver'in window){const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)active(e.target===ai?'ai':'trading');}),{rootMargin:'-10% 0px -70% 0px',threshold:0});io.observe(root);if(ai)io.observe(ai);}
refreshLanguage();
window.BSVHomeLayout=Object.freeze({replaceCatalogue,showUnavailable,refreshLanguage,refreshAI:renderAI});
})();
