/* Public-metadata search only. Never index source bodies, emails, entitlements, or private drafts. */
const GROUPS = [
  ['rsi','relative strength index','相対力指数'],
  ['ma','moving average','移動平均'],
  ['sma','simple moving average','単純移動平均'],
  ['ema','exponential moving average','exponential','指数移動平均'],
  ['ea','expert advisor','自動売買','trading bot'],
  ['cbot','c bot','ctrader bot'],
  ['breakout','ブレイクアウト','高値安値抜け'],
  ['trend','トレンド','trend following','順張り'],
  ['mean reversion','平均回帰','逆張り'],
  ['volatility','ボラティリティ','値幅'],
  ['volume','出来高'],
  ['stop loss','stoploss','損切り'],
  ['lot size','position size','lot calculator','ロット計算'],
  ['meeting notes','minutes','議事録'],
  ['research','調査','リサーチ'],
  ['code review','コードレビュー'],
  ['workflow','automation','ワークフロー','自動化'],
  ['mcp','model context protocol'],
  ['local environment','ローカル環境']
];
export function normalize(value=''){
  return String(value).normalize('NFKC').toLocaleLowerCase()
    .replace(/-/g,' ')
    .replace(/[‐‑‒–—―ーｰ_/\\|・:;,.()[\]{}'"’“”!?！？、。]/g,' ')
    .replace(/\s+/g,' ').trim();
}
const ALIASES = new Map();
for (const group of GROUPS) {
  const values=[...new Set(group.map(normalize))];
  for (const value of values) ALIASES.set(value,values);
}
function queryTerms(query){
  const q=normalize(query);
  if(!q)return [];
  const raw=q.split(' ').filter(Boolean);
  const terms=[];
  for(const token of raw){
    const group=ALIASES.get(token);
    terms.push(group||[token]);
  }
  for(const [key,group] of ALIASES){
    if(key.includes(' ')&&q.includes(key)&&!terms.some(g=>g===group))terms.push(group);
  }
  return terms;
}
function list(value){return Array.isArray(value)?value.filter(v=>v!==null&&v!==undefined).map(String):value?[String(value)]:[];}
function localizedText(record,key){
  const out=[];
  if(record?.text?.ja?.[key])out.push(record.text.ja[key]);
  if(record?.text?.en?.[key])out.push(record.text.en[key]);
  if(record?.summary?.ja)out.push(record.summary.ja);
  if(record?.summary?.en)out.push(record.summary.en);
  if(typeof record?.summary==='string')out.push(record.summary);
  return out;
}
export function toPublicRecord(record,{scope='trading',source='curated'}={}){
  if(!record||typeof record!=='object')return null;
  const id=String(record.id||'').trim();
  if(!/^[a-z0-9][a-z0-9_.:-]{0,159}$/i.test(id))return null;
  if(source==='community'&&(record.status!=='published'||record.visibility!=='public'||record.reviewStatus!=='approved'))return null;
  const title=String(record.title||record.name||'').trim();
  if(!title)return null;
  const pricing=record.pricing||record.mode||'free';
  const normalizedPricing=pricing==='paid'?(record.billingInterval==='once'?'one_time':'monthly'):pricing;
  if(!['free','monthly','one_time'].includes(normalizedPricing))return null;
  const summary=[...localizedText(record,'purpose'),...localizedText(record,'mechanism')].join(' ');
  const tags=[...list(record.tags),record.category,record.kind].filter(Boolean);
  const platforms=list(record.platforms||record.platform||record.environment);
  const author=String(record.author||record.authorName||'');
  return Object.freeze({
    id,scope,source,title,summary,author,tags,platforms,
    kind:String(record.kind||record.type||''),pricing:normalizedPricing,
    href:String(record.href||''),revision:Number.isFinite(Number(record.revision))?Number(record.revision):0
  });
}
export function mergePublicCatalogues(inputs){
  const byId=new Map();
  for(const input of inputs||[]){
    const record=toPublicRecord(input.record||input,input);
    if(!record)continue;
    const key=record.scope+':'+record.id;
    const old=byId.get(key);
    if(!old||record.revision>old.revision||(record.revision===old.revision&&record.source==='community'))byId.set(key,record);
  }
  return [...byId.values()];
}
function contains(field,term){
  if(!field)return false;
  if(/^[a-z0-9]{1,3}$/i.test(term))return (' '+field+' ').includes(' '+term+' ');
  return field.includes(term);
}
function groupMatches(fields,group){return group.some(term=>fields.some(field=>contains(field,term)));}
export function scoreRecord(record,query){
  const q=normalize(query),terms=queryTerms(query);
  if(!q)return 1;
  const title=normalize(record.title),summary=normalize(record.summary),author=normalize(record.author);
  const tags=normalize(record.tags.join(' ')),platforms=normalize(record.platforms.join(' ')),kind=normalize(record.kind);
  const all=[title,summary,author,tags,platforms,kind];
  if(!terms.every(group=>groupMatches(all,group)))return 0;
  let score=0;
  if(title===q)score+=1200; else if(title.startsWith(q))score+=700; else if(contains(title,q))score+=500;
  for(const group of terms){
    if(groupMatches([title],group))score+=240;
    else if(groupMatches([tags,platforms,kind],group))score+=140;
    else if(groupMatches([author],group))score+=90;
    else if(groupMatches([summary],group))score+=55;
  }
  if(contains(summary,q))score+=110;
  if(contains(tags,q)||contains(platforms,q)||contains(kind,q))score+=150;
  return score;
}
export function searchPublicCatalogue(records,{q='',scope='all',kind='',platform='',pricing='all'}={}){
  const platformNeedle=normalize(platform),kindNeedle=normalize(kind);
  return (records||[]).filter(record=>{
    if(scope!=='all'&&record.scope!==scope)return false;
    if(pricing!=='all'&&record.pricing!==pricing)return false;
    if(kindNeedle&&normalize(record.kind)!==kindNeedle)return false;
    if(platformNeedle&&!record.platforms.some(p=>normalize(p)===platformNeedle))return false;
    return scoreRecord(record,q)>0;
  }).map(record=>({record,score:scoreRecord(record,q)}))
    .sort((a,b)=>b.score-a.score||a.record.title.localeCompare(b.record.title)||a.record.id.localeCompare(b.record.id))
    .map(x=>x.record);
}
export function encodeSearchState(state={}){
  const p=new URLSearchParams();
  for(const key of ['q','scope','kind','platform','pricing']){
    const value=String(state[key]??'').trim();
    if(value&&value!=='all')p.set(key,value);
  }
  const s=p.toString();
  return s?'?'+s:'';
}
export function decodeSearchState(input=''){
  const p=new URLSearchParams(String(input).replace(/^.*\?/,''));
  return {q:p.get('q')||'',scope:p.get('scope')||'all',kind:p.get('kind')||'',platform:p.get('platform')||'',pricing:p.get('pricing')||'all'};
}
export function suggestions(records,state={},limit=3){
  if(!normalize(state.q))return [];
  const groups=queryTerms(state.q),partial=[];
  for(const record of records||[]){
    if(state.scope&&state.scope!=='all'&&record.scope!==state.scope)continue;
    const fields=[normalize(record.title),normalize(record.summary),normalize(record.tags.join(' ')),normalize(record.platforms.join(' '))];
    const hits=groups.reduce((n,g)=>n+(groupMatches(fields,g)?1:0),0);
    if(hits)partial.push({record,hits,score:scoreRecord(record,state.q)});
  }
  return partial.sort((a,b)=>b.hits-a.hits||b.score-a.score||a.record.title.localeCompare(b.record.title)).slice(0,limit).map(x=>x.record);
}
