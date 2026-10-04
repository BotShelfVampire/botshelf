#!/usr/bin/env python3
"""Issue #6 tranche 1: Request Market page (/requests/) on the existing Traders Library look (idempotent).

- The page lists only requests the API returns (approved + author chose PUBLIC). Nothing is seeded:
  with an empty store the page says 0.
- Submitting needs the existing email-verified session (function demand-request.js).
- Publishes the demand-request schema at its $id URL (/schemas/demand-request-v0.1.json).
- Adds /requests/ to the sitemap and a "Request a tool" link on /trading/build/.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import build_live_toolkit as blt

REPO = Path(__file__).resolve().parents[2]
ORIGIN = "https://botshelfvampire.com"
API = "/.netlify/functions/demand-request"
DOMAINS = [("trading", "Trading tools", "トレードツール"), ("ai-workflows", "AI workflows", "AIワークフロー"),
           ("robotics", "Robotics / physical AI", "ロボティクス"), ("space", "Space", "宇宙"), ("quantum", "Quantum", "量子"),
           ("biotech", "Biotech / bioinformatics", "バイオ"), ("bci", "BCI / neural interfaces", "BCI"),
           ("medical", "Medical / healthcare", "医療"), ("industrial", "Industrial / field service", "現場・産業"),
           ("data-workflows", "Data workflows", "データ業務"), ("robot-pilot", "Robot pilot / teleoperation", "ロボット遠隔操作"),
           ("other", "Other", "その他")]

CSS = """.rq-form{display:grid;gap:14px;max-width:760px}
.rq-form label{display:block;font-weight:600;margin-bottom:4px}
.rq-form textarea,.rq-form input[type=text],.rq-form input[type=number],.rq-form input[type=date]{width:100%;padding:10px 12px;background:var(--panel);border:1px solid var(--line);color:var(--text);border-radius:4px;font:inherit;min-width:0}
.rq-form textarea{min-height:120px;resize:vertical}
.rq-form fieldset{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:0}
.rq-form legend{padding:0 6px;font-weight:600}
.rq-checks{display:flex;flex-wrap:wrap;gap:8px 16px}
.rq-checks label{font-weight:400;display:inline-flex;gap:6px;align-items:center;margin:0}
.rq-checks input{width:auto;padding:0}
.rq-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.rq-msg{min-height:1.4em}
.rq-msg.err{color:var(--danger)}
.rq-msg.ok{color:var(--green)}
.rq-counts{display:flex;flex-wrap:wrap;gap:12px}
.rq-counts div{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 14px;min-width:150px}
.rq-counts b{display:block;font-size:1.6rem;color:var(--green)}
.rq-list{display:grid;gap:12px;padding:0;list-style:none}
.rq-filter{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.rq-filter .chip{cursor:pointer;font:inherit}
.rq-filter .chip[aria-pressed=true]{border-color:var(--green);color:var(--green)}
.rq-target{outline:2px solid var(--green);outline-offset:2px}
.rq-job{white-space:pre-wrap;margin:0}
.rp-box{border:1px solid var(--line);border-left:3px solid var(--green);border-radius:8px;padding:10px 14px;background:var(--panel)}
"""

JS = r"""(function(){'use strict';
var API='%API%';
function $(s){return document.querySelector(s)}
function el(t,a,k){var e=document.createElement(t);a=a||{};for(var x in a){if(x==='text')e.textContent=a[x];else e.setAttribute(x,a[x])}(k||[]).forEach(function(c){e.appendChild(c)});return e}
function bi(en,ja){var f=document.createDocumentFragment();f.appendChild(el('span',{'data-lang':'en',text:en}));f.appendChild(el('span',{'data-lang':'ja',text:ja}));return f}
var LAB=%LAB%;
function setCount(id,v){var b=document.getElementById(id);if(b)b.textContent=String(v)}
function render(j){var ul=$('#rq-list');ul.textContent='';var c=j.counts||{};
 setCount('rq-c-received',c.received||0);setCount('rq-c-published',c.published||0);setCount('rq-c-budget',c.publishedWithStatedBudget||0);
 var rs=j.requests||[];
 if(!rs.length){ul.appendChild(el('li',{'class':'empty'},[bi('No public requests yet. This list only shows real requests after review.','公開中のリクエストはまだありません。確認を通った実際のリクエストだけを表示します。')]));return}
 rs.forEach(function(r){var meta=[(r.domains||[]).map(function(d){return LAB[d]||d}).join(' · ')];
  if(r.platforms&&r.platforms.length)meta.push(r.platforms.join(', '));
  var li=el('li',{'class':'bb-card','id':r.requestId,'data-request-id':r.requestId,'data-areas':' '+(r.domains||[]).join(' ')+' '},[el('div',{'class':'bb-meta'},[el('span',{text:meta.join(' — ')}),el('span',{'class':'bb-flag',text:r.status})]),el('p',{'class':'rq-job',text:r.job})]);
  var d=[];if(r.desiredInputs&&r.desiredInputs.length)d.push('In: '+r.desiredInputs.join(', '));if(r.desiredOutputs&&r.desiredOutputs.length)d.push('Out: '+r.desiredOutputs.join(', '));
  if(r.freeSolutionAcceptable===true)d.push('Free/open solution OK');
  if(r.willingnessToPay){var w=r.willingnessToPay;d.push('Stated budget: '+(w.min!=null?w.min:'?')+'–'+(w.max!=null?w.max:'?')+' USDT (not escrow)')}
  if(r.deadline)d.push('Deadline: '+r.deadline.slice(0,10));d.push('Posted: '+String(r.createdAt).slice(0,10)+' · '+r.requestId);
  li.appendChild(el('p',{'class':'small muted',text:d.join(' · ')}));ul.appendChild(li)})}
function areaParam(){try{return (new URL(location.href).searchParams.get('area')||'').replace(/[^a-z-]/g,'')}catch(e){return ''}}
function applyFilter(a){var shown=0;[].forEach.call(document.querySelectorAll('#rq-list li[data-areas]'),function(li){var on=!a||li.getAttribute('data-areas').indexOf(' '+a+' ')!==-1;li.hidden=!on;if(on)shown++});
 [].forEach.call(document.querySelectorAll('#rq-filter [data-area]'),function(b){b.setAttribute('aria-pressed',String(b.getAttribute('data-area')===a))});
 var n=$('#rq-filter-note');if(n){n.textContent='';if(a&&!shown)n.appendChild(bi('No listed requests in this area yet.','この分野で公開中のリクエストはまだありません。'))}}
function filters(rs){var box=$('#rq-filter');if(!box)return;box.textContent='';var m={};rs.forEach(function(r){(r.domains||[]).forEach(function(d){m[d]=(m[d]||0)+1})});
 var mk=function(a,label,n){var b=el('button',{type:'button','class':'chip','data-area':a,'aria-pressed':'false',text:label+' ('+n+')'});b.addEventListener('click',function(){applyFilter(a)});box.appendChild(b)};
 mk('','All',rs.length);Object.keys(LAB).forEach(function(k){if(m[k])mk(k,LAB[k],m[k])});var a=areaParam();if(a&&!m[a])mk(a,LAB[a]||a,0);applyFilter(a)}
function target(){var h=decodeURIComponent((location.hash||'').slice(1));if(!/^req_[a-z0-9_-]+$/.test(h))return;var e=document.getElementById(h),n=$('#rq-target-note');
 if(e){e.hidden=false;e.classList.add('rq-target');e.scrollIntoView({block:'center'})}else if(n){n.textContent='';n.appendChild(bi('This request is not listed. It may be pending review, private or closed.','このリクエストは公開一覧にありません。確認待ち・非公開・終了のいずれかの可能性があります。'))}}
function areas(rs){var ul=$('#rq-areas');if(!ul)return;ul.textContent='';var m={};rs.filter(function(r){return r.status==='OPEN'}).forEach(function(r){(r.domains||[]).forEach(function(d){m[d]=m[d]||{n:0,b:0};m[d].n++;if(r.willingnessToPay)m[d].b++})});
 var ks=Object.keys(m).sort(function(a,b){return m[b].n-m[a].n});if(!ks.length){ul.appendChild(el('li',{'class':'empty'},[bi('No open public requests yet, so there is no area score yet.','公開中のリクエストがまだないため、分野ごとのスコアはまだありません。')]));return}
 ks.forEach(function(k){ul.appendChild(el('li',{'class':'bb-card'},[el('strong',{text:(LAB[k]||k)+' — score '+m[k].n}),el('span',{'class':'small muted',text:'with a stated budget: '+m[k].b}) ]))})}
function heat(rs){var t=$('#rq-heat');if(!t)return;t.textContent='';var open=rs.filter(function(r){return r.status==='OPEN'}),cols=[],rows=[],m={};
 open.forEach(function(r){var ps=(r.platforms||[]).length?r.platforms.slice(0,8):['—'];(r.domains||[]).forEach(function(d){if(rows.indexOf(d)<0)rows.push(d);ps.forEach(function(p){if(cols.indexOf(p)<0)cols.push(p);var k=d+'\u0000'+p;m[k]=(m[k]||0)+1})})});
 if(!open.length){t.appendChild(el('caption',{'class':'small muted'},[bi('No open public requests yet, so every cell is 0 and nothing is drawn.','公開中のリクエストがまだないため、すべて0で、表は空です。')]));return}
 rows.sort();cols.sort(function(a,b){return a==='—'?1:b==='—'?-1:a<b?-1:1});var hr=el('tr',{},[el('th',{text:'Area \u00d7 platform'})]);cols.forEach(function(c){hr.appendChild(el('th',{text:c}))});t.appendChild(el('thead',{},[hr]));var tb=el('tbody',{});
 rows.forEach(function(d){var tr=el('tr',{},[el('th',{text:LAB[d]||d})]);cols.forEach(function(c){var n=m[d+'\u0000'+c]||0;tr.appendChild(el('td',{'data-n':String(n),text:String(n)}))});tb.appendChild(tr)});t.appendChild(tb)}
function load(){fetch(API+'?op=public',{credentials:'omit'}).then(function(r){return r.json()}).then(function(j){if(j&&j.ok){render(j);filters(j.requests||[]);areas(j.requests||[]);heat(j.requests||[]);target()}else throw 0}).catch(function(){var ul=$('#rq-list');ul.textContent='';ul.appendChild(el('li',{'class':'empty'},[bi('Could not load requests right now.','いまはリクエストを読み込めません。')]))})}
function list(v){return String(v||'').split(',').map(function(s){return s.trim()}).filter(Boolean).slice(0,8)}
function msg(cls,en,ja){var m=$('#rq-msg');m.className='rq-msg '+cls;m.textContent='';m.appendChild(bi(en,ja));if(m.querySelector('a'))return}
function submit(ev){ev.preventDefault();var f=ev.target;var doms=[].slice.call(f.querySelectorAll('input[name=domain]:checked')).map(function(x){return x.value});
 var vis=f.querySelector('input[name=visibility]:checked');var free=f.querySelector('#rq-free').value;
 var body={job:f.querySelector('#rq-job').value,domains:doms,platforms:list(f.querySelector('#rq-platforms').value),desiredInputs:list(f.querySelector('#rq-in').value),desiredOutputs:list(f.querySelector('#rq-out').value),
  freeSolutionAcceptable:free==='yes'?true:free==='no'?false:null,visibility:vis?vis.value:'',contactViaBsv:f.querySelector('#rq-contact').checked};
 var mn=f.querySelector('#rq-min').value,mx=f.querySelector('#rq-max').value;if(mn||mx)body.willingnessToPay={min:mn?Number(mn):null,max:mx?Number(mx):null,currency:'USDT'};
 var dl=f.querySelector('#rq-deadline').value;if(dl)body.deadline=dl;
 if(body.job.trim().length<20){msg('err','Describe the job in at least 20 characters.','やりたいことを20文字以上で書いてください。');return}
 if(!doms.length){msg('err','Pick at least one area.','分野を1つ以上選んでください。');return}
 if(!body.visibility){msg('err','Choose public or private.','公開か非公開かを選んでください。');return}
 var btn=f.querySelector('button[type=submit]');btn.disabled=true;
 fetch(API,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){return{s:r.status,j:j}})}).then(function(x){btn.disabled=false;
  if(x.s===201){msg('ok','Received ('+x.j.id+'). It is pending review'+(body.visibility==='PUBLIC'?' and will be listed only after review.':' and stays private.'),'受け付けました（'+x.j.id+'）。確認待ちです。'+(body.visibility==='PUBLIC'?'公開は確認の後です。':'非公開のままです。'));f.reset()}
  else if(x.s===200&&x.j.duplicate){msg('ok','You already sent this request ('+x.j.id+').','同じリクエストは送信済みです（'+x.j.id+'）。')}
  else if(x.s===401){msg('err','Sign in with your verified email first (Register → 6-digit code), then send again.','先にメール確認済みのアカウントでログインしてください（登録→6桁のコード）。その後もう一度送ってください。');var a=el('a',{href:'/register.html?next=/requests/',text:' Register / sign in · 登録・ログイン'});$('#rq-msg').appendChild(a)}
  else if(x.s===429){msg('err','Daily limit reached (5 requests per day).','1日の上限（5件）に達しました。')}
  else{msg('err','Not sent: '+(x.j.reason||x.s),'送信できませんでした: '+(x.j.reason||x.s))}}).catch(function(){btn.disabled=false;msg('err','Not sent: network error','送信できませんでした（通信エラー）')})}
function prefill(){var q;try{q=new URL(location.href).searchParams}catch(e){return}var a=q.get('area');if(a){var c=document.querySelector('input[name=domain][value="'+a.replace(/[^a-z-]/g,'')+'"]');if(c)c.checked=true}
 var bk=q.get('block');if(bk&&/^[a-z]+\.[a-z_]+$/.test(bk)){var jb=$('#rq-job');if(jb&&!jb.value)jb.value='Generator block '+bk+': please render it for my platform (which: ...). Recipe or use case: ...'}
 var tk=q.get('toolkit');if(tk&&/^[a-z0-9-]{1,60}$/.test(tk)){var jt=$('#rq-job');if(jt&&!jt.value)jt.value='AI toolkit item '+tk+': please make a version for my framework or runtime (which: ...). What it should do: ...'}
 var md=q.get('module');if(q.get('kind')==='mission'&&md&&/^[a-z0-9-]{1,40}$/.test(md)){var jm=$('#rq-job');if(jm&&!jm.value)jm.value='Mission like Robot Pilot module '+md+': task to demonstrate: ...; robot / embodiment: ...; teleop interface: ...; simulation or real hardware: ...; episode target: ...; quality criteria: ...'}
 if(q.get('kind')==='mission'){var j=$('#rq-job');if(j)j.setAttribute('placeholder','Mission: task to demonstrate; robot / embodiment; teleop interface; simulation or real hardware (owner-authorised, safety rules); location or remote; data needed; episode target; quality criteria; privacy / NDA');var h=$('#rq-mission');if(h)h.hidden=false}}
function addPlat(cur,v){var a=list(cur);if(a.map(function(x){return x.toLowerCase()}).indexOf(v.toLowerCase())<0&&a.length<8)a.push(v);return a.join(', ')}
document.addEventListener('DOMContentLoaded',function(){prefill();load();window.addEventListener('hashchange',target);var f=$('#rq-form');if(f)f.addEventListener('submit',submit);
 [].forEach.call(document.querySelectorAll('[data-rq-plat]'),function(b){b.addEventListener('click',function(){var i=$('#rq-platforms');if(i){i.value=addPlat(i.value,b.getAttribute('data-rq-plat'));i.focus()}})})});
})();
"""



def ai_frameworks() -> list:
    """Frameworks named in ai-toolkit/catalog.json, in catalog order (#6 tranche 12); "Any framework" is not a framework."""
    cat = json.loads((Path(__file__).resolve().parents[2] / "ai-toolkit/catalog.json").read_text())["entries"]
    return [p for p in dict.fromkeys(e["platform"] for e in cat) if p != "Any framework"]

def h8(s):
    return hashlib.sha256(s.encode()).hexdigest()[:8]


def both(en, ja, tag="span", cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<{tag} data-lang="en"{c}>{blt.esc(en)}</{tag}><{tag} data-lang="ja"{c}>{blt.esc(ja)}</{tag}>'


def catalogue_gaps(site: Path) -> list:
    """Supply gaps counted from /trading/catalog.json (facts about the catalogue, not demand)."""
    cat = json.loads((site / "trading/catalog.json").read_text())
    def ent(i):
        return {"id": i["id"], "name": i["name"], "kind": i["kind"], "license": i.get("license"), "url": i.get("detail_url") or f"/trading/tools/{i['id']}.html"}
    rules = [("tradingview-only", "TradingView (Pine) only: no MT4 or MT5 version in the catalogue", "TradingView（Pine）のみ: カタログにMT4・MT5版がない",
              lambda p: p == {"TradingView"}),
             ("mt-no-pine", "MT4/MT5 only: no TradingView (Pine) version in the catalogue", "MT4・MT5のみ: カタログにTradingView（Pine）版がない",
              lambda p: "TradingView" not in p and ("MT4" in p or "MT5" in p)),
             ("mt5-no-mt4", "MT5 only: no MT4 version in the catalogue", "MT5のみ: カタログにMT4版がない", lambda p: p == {"MT5"})]
    out = []
    for gid, en, ja, f in rules:
        items = [ent(i) for i in cat if f(set(i["platforms"]))]
        kinds = {}
        for i in items:
            kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
        out.append({"id": gid, "label": en, "label_ja": ja, "count": len(items), "byKind": dict(sorted(kinds.items())), "entries": items})
    return out


_RENDERED = {}


def _render_all():
    """Render every recipe for every target once per build; keep TODO counts and unsupported block types."""
    if _RENDERED:
        return
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    tk = json.loads((REPO / "trader-toolkit/catalog.json").read_text())
    gen = REPO / "trader-toolkit/generator/render.mjs"
    def run(job):
        stem, t = job
        out = subprocess.run(["node", str(gen), str(REPO / f"trader-toolkit/recipes/{stem}.json"), "--target", t], capture_output=True, text=True, check=True).stdout
        return job, {"unsupported": sorted(set(re.findall(r"TODO unsupported block ([a-z_]+\.[a-z_]+)", out))), "todo": len(re.findall(r"\bTODO\b", out))}
    with ThreadPoolExecutor(8) as ex:
        for job, v in ex.map(run, [(stem, t) for stem in tk["recipes"] for t, _, _ in blt.TARGETS]):
            _RENDERED[job] = v


def generator_gaps() -> dict:
    """Block types used by the BSV recipes that the BSV generator does not render yet (Issue #6 tranche 6). Counted at
    build time by rendering every recipe for every target and reading the generator's own 'TODO unsupported block'
    lines. A fact about the generator, not a measure of demand."""
    tk = json.loads((REPO / "trader-toolkit/catalog.json").read_text())
    targets = [t for t, _, _ in blt.TARGETS]
    _render_all()
    res = [(stem, t, _RENDERED[(stem, t)]["unsupported"]) for stem in tk["recipes"] for t in targets]
    by = {}
    for stem, t, types in res:
        for ty in types:
            g = by.setdefault(ty, {"recipes": set(), "targets": set()})
            g["recipes"].add(stem); g["targets"].add(t)
    gaps = [{"blockType": ty, "recipes": sorted(g["recipes"]), "recipeCount": len(g["recipes"]), "targetsWithoutIt": len(g["targets"]), "targetsWithIt": len(targets) - len(g["targets"]),
             "targetsRenderingIt": [t for t in targets if t not in g["targets"]]}
            for ty, g in sorted(by.items(), key=lambda kv: (-len(kv[1]["recipes"]), kv[0]))]
    return {"targets": len(targets), "recipes": len(tk["recipes"]), "recipesWithGaps": len({stem for stem, _, types in res if types}), "gaps": gaps}


TARGET_CHECKS = {  # which BSV check covers each target (facts from build_stage / scripts/site); nothing here is a platform run
    "backtrader": ("LIBRARY_RUN", "scripts/site/check_backtrader.py", "Executed inside the backtrader library on synthetic bars; not a broker or live feed."),
    "backtesting-py": ("LIBRARY_RUN", "scripts/site/check_backtesting_py.py", "Executed inside the Backtesting.py library on synthetic bars; not a broker or live feed."),
    "nautilus": ("LIBRARY_RUN", "scripts/site/check_nautilus.py", "Executed inside the NautilusTrader BacktestEngine on synthetic bars; not a broker, venue or live feed."),
    "thinkscript": ("SUBSET_EVALUATOR", "scripts/site/check_thinkscript.mjs", "BSV-written thinkScript-subset parser/evaluator; not thinkorswim."),
    "amibroker": ("SUBSET_EVALUATOR", "scripts/site/check_amibroker_afl.mjs", "BSV-written AFL-subset parser/evaluator; not AmiBroker."),
    "tradovate": ("API_STUB_RUN", "scripts/site/check_tradovate.mjs", "Run in node:vm against a BSV stub of the documented custom-indicator API; not Tradovate."),
    "vela": ("ENGINE_STAND_IN", "scripts/site/test_vela_engine.mjs", "Vela imports swapped for local stand-ins and run over synthetic bars; not a Vela runtime test."),
    "motivewave": ("STUB_COMPILE", "scripts/site/check_motivewave_stubs.sh", "javac against BSV stubs written from the public SDK javadoc; not the real SDK."),
    "jforex": ("STUB_COMPILE", "scripts/site/check_jforex_stubs.sh", "javac against BSV stubs written from the JForex API javadoc; not run."),
    "ctrader": ("STUB_COMPILE", "scripts/site/check_ctrader_stubs.sh", "dotnet build against BSV stubs from the cTrader Algo API reference; not a real cTrader build."),
    "atas": ("STUB_COMPILE", "scripts/site/check_atas_stubs.sh", "dotnet build against BSV stubs from the ATAS API reference; not a real ATAS build."),
    "easylanguage": ("STRUCTURAL", "scripts/site/check_easylanguage_output.mjs", "Structural check only; not a TradeStation Verify."),
}
HTF_REAL = blt.HTF_REAL  # must match htfRealTargets() in render.mjs (checked by check_htf.py)
HTF_IDIOM = blt.HTF_IDIOM  # must match htfIdiomTargets() in render.mjs (checked by check_htf.py)
HTF_DISCLOSURE = ("Correction (2026-10-04): before this date every BSV generator target computed indicators marked with a higher "
                  "timeframe (timeframeRef) on the chart timeframe, with no warning. This affected the recipe mtf-confirmation-panel. "
                  "Now 4 targets compute real higher-timeframe values from closed bars (backtrader, Backtesting.py and NautilusTrader checked inside their libraries; Tradovate checked in a BSV stub of its documented API, not run on Tradovate), 7 more (Pine v6, MQL5, MQL4, NinjaTrader 8, cTrader, AmiBroker, thinkorswim) "
                  "read the last closed higher-timeframe bar with the platform's officially documented idiom (pattern checked statically; not run by BSV), "
                  "and the other 11 leave those blocks as TODO stubs.")
HTF_DISCLOSURE_JA = ("訂正（2026-10-04）：この日より前は、BSVジェネレーターのすべての出力先で、上位足を指定した指標（timeframeRef）を、注記なしで表示中の足で計算していました。"
                     "影響したのはレシピ mtf-confirmation-panel です。現在は4つの出力先で確定した上位足から計算し（backtrader・Backtesting.py・NautilusTraderはライブラリ内で確認、Tradovateは公式APIのBSVスタブで確認しTradovate上では未実行）、Pine v6・MQL5・MQL4・NinjaTrader 8・cTrader・AmiBroker・thinkorswimの7つでは各プラットフォームの公式ドキュメントにある方法で直前に確定した上位足を読みます（形を静的に確認。BSVは実行していません）。ほかの11ではそのブロックをTODOのスタブにしています。")
HTF_IDIOM_DOCS = {
    "pine-v6": ["https://www.tradingview.com/pine-script-docs/concepts/repainting/", "https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/"],
    "mql5": ["https://www.mql5.com/en/docs/series/ibarshift", "https://www.mql5.com/en/docs/series/copybuffer", "https://www.mql5.com/en/docs/constants/chartconstants/enum_timeframes"],
    "mql4": ["https://docs.mql4.com/series/ibarshift", "https://docs.mql4.com/indicators/ima", "https://docs.mql4.com/constants/chartconstants/enum_timeframes"],
    "ninjatrader": ["https://ninjatrader.com/support/helpGuides/nt8/multi-time_frame__instruments.htm", "https://ninjatrader.com/support/helpGuides/nt8/adddataseries.htm"],
    "amibroker": ["https://www.amibroker.com/guide/h_timeframe.html"],
    "thinkscript": ["https://toslc.thinkorswim.com/center/reference/thinkScript/tutorials/Advanced/Chapter-11---Referencing-Secondary-Aggregation", "https://toslc.thinkorswim.com/center/reference/thinkScript/Constants/AggregationPeriod", "https://toslc.thinkorswim.com/center/reference/thinkScript/Functions/Others/GetAggregationPeriod"],
    "ctrader": ["https://help.ctrader.com/ctrader-algo/references/Collections/DataSeries/TimeSeries/", "https://help.ctrader.com/ctrader-algo/references/MarketData/MarketData/", "https://help.ctrader.com/ctrader-algo/references/Period/TimeFrame/"],
}
HTF_IDIOM_NOTE = {
    "pine-v6": "request.security(syminfo.tickerid, tf, expr[1], lookahead = barmerge.lookahead_on) — the non-repainting idiom from the Pine Script v6 manual — plus a runtime.error guard when the chart timeframe is not lower. Pattern checked statically by BSV; not run by BSV (UNTESTED_RUNTIME).",
    "mql5": "Indicator handle on the higher PERIOD; value read with CopyBuffer at start_pos = iBarShift(chart bar time) + 1 = the last closed higher-timeframe bar. OnInit fails when the chart period is not lower. Pattern checked statically by BSV; not compiled or run by BSV (UNTESTED_RUNTIME). Bars follow broker server time.",
    "mql4": "iMA/iRSI/iATR on the higher PERIOD at shift = iBarShift(chart bar time) + 1 = the last closed higher-timeframe bar; standard MT4 periods only. OnInit fails when the chart period is not lower. Pattern checked statically by BSV; not compiled or run by BSV (UNTESTED_RUNTIME). Bars follow broker server time.",
    "ninjatrader": "AddDataSeries in State.Configure with Calculate forced to OnBarClose (the manual: chart bars then only know the last closed bar of the added series; shared timestamps run the chart series first); indicator on that series, stored per chart bar in BarsInProgress 0; DataLoaded throws when the chart timeframe is not lower. Pattern checked statically by BSV; not compiled or run by BSV (UNTESTED_RUNTIME). Bars follow the trading hours template.",
    "thinkscript": "C_x = close(period = AggregationPeriod.HOUR); E_x = ExpAverage(C_x, 50); H_x = E_x[1] — expressions made only of secondary-aggregation variables and constants keep that aggregation (manual), so [1] is the previous higher bar, as High(period = AggregationPeriod.DAY)[1] is the previous day in the manual; no chart-period price is mixed in. Empty unless GetAggregationPeriod() is shorter (time charts). Pattern checked statically, and BSV's thinkScript-subset evaluator (which models secondary contexts) compares the values with an independent hourly reference and a prefix (no-lookahead) test on 15-minute bars; not run in thinkorswim (UNTESTED_RUNTIME).",
    "amibroker": "TimeFrameSet(3600); H_x = Ref(EMA(Close, 50), -1); TimeFrameRestore(); then TimeFrameExpand(H_x, 3600, expandFirst) — the guide's TimeFrameGetPrice construction with a negative shift, which the guide says to use for trading rules (shift 0 can look into the future). Null unless the chart interval is shorter; signals require NOT IsNull. Pattern checked statically, and BSV's AFL-subset evaluator compares the values with an independent hourly reference and a prefix (no-lookahead) test on 15-minute bars; not run in AmiBroker (UNTESTED_RUNTIME).",
    "ctrader": "MarketData.GetBars(TimeFrame.Hour) and the indicator on that series; value at index k - 1, where k = GetIndexByTime(chart bar open time) stepped back with the OpenTimes indexer until that bar opened at or before the chart bar's open. The reference does not state how GetIndexByTime rounds a time inside a bar, so the step-back makes k - 1 a closed bar under any rounding (worst case one extra bar of lag, never a forming bar). Higher-timeframe values stay empty unless the chart TimeFrame is a strictly lower time frame. Pattern checked statically and compiled against BSV stubs; not run on cTrader (UNTESTED_RUNTIME).",
}
PARITY_ONLY = ("PARITY_ONLY", "scripts/site/test_builder_parity.mjs", "Only checked that the browser builder output equals the CLI generator; no target-specific check.")


def generator_coverage() -> dict:
    """Per target: which BSV check covers it; per recipe x target: generator TODO lines (Issue #8 tranche 7)."""
    _render_all()
    tk = json.loads((REPO / "trader-toolkit/catalog.json").read_text())
    targets = []
    for t, label, ext in blt.TARGETS:
        kind, script, note = TARGET_CHECKS.get(t, PARITY_ONLY)
        if not (REPO / script).exists():
            raise SystemExit(f"coverage: missing check script {script}")
        real, idiom = t in HTF_REAL, t in HTF_IDIOM
        targets.append({"id": t, "label": label, "extension": ext, "check": {"kind": kind, "script": script, "note": note},
                        "higherTimeframe": {"status": "CLOSED_BARS_CHECKED" if real else ("CLOSED_BAR_IDIOM_STATIC" if idiom else "UNSUPPORTED_TODO"),
                                            "note": ("Computed from closed higher-timeframe bars only (no repaint, no lookahead) in per-bar JavaScript state; checked in BSV's node:vm stub of the documented custom-indicator API (not Tradovate) against an independent reference on every bar, a forming-bar mutant, and no value on too-coarse bars." if t == "tradovate" else "Computed from closed higher-timeframe bars only (no repaint, no lookahead); checked in the library on synthetic bars, including a cut-off run and a stop on too-coarse bars.") if real
                                            else (HTF_IDIOM_NOTE[t] if idiom else "Blocks that use a higher timeframe are left as unsupported stubs with a TODO line (empty value / false signal); never computed on the chart timeframe."),
                                            **({"docs": HTF_IDIOM_DOCS[t], "check": "scripts/site/check_htf.py"} if idiom else {})},
                        "runtimeTestedByBSV": False})
    recipes = []
    for stem in tk["recipes"]:
        row = {t: _RENDERED[(stem, t)] for t, _, _ in blt.TARGETS}
        recipes.append({"id": stem, "todoLines": {t: v["todo"] for t, v in row.items()}, "unsupportedBlocks": sorted({x for v in row.values() for x in v["unsupported"]})})
    kinds = {}
    for x in targets:
        kinds[x["check"]["kind"]] = kinds.get(x["check"]["kind"], 0) + 1
    return {"schemaNote": "BSV generator coverage v0.1. Facts counted from the generator and BSV's own checks at build time. No target is runtime-tested by BSV.",
            "generatedFrom": "trader-toolkit/generator/render.mjs, trader-toolkit/recipes and scripts/site checks in the BSV repository",
            "higherTimeframeDisclosure": HTF_DISCLOSURE,
            "counts": {"targets": len(targets), "recipes": len(recipes), "byCheckKind": dict(sorted(kinds.items())), "runtimeTestedByBSV": 0,
                       "higherTimeframeReal": sum(1 for x in targets if x["higherTimeframe"]["status"] == "CLOSED_BARS_CHECKED"),
                       "higherTimeframeDocumentedIdiom": sum(1 for x in targets if x["higherTimeframe"]["status"] == "CLOSED_BAR_IDIOM_STATIC"),
                       "recipeTargetPairsWithoutTodo": sum(1 for r in recipes for v in r["todoLines"].values() if v == 0)},
            "targets": targets, "recipes": recipes}


KIND_TEXT = {"LIBRARY_RUN": ("Run inside the library", "ライブラリ内で実行"), "SUBSET_EVALUATOR": ("BSV subset evaluator", "BSVの部分評価器"),
             "API_STUB_RUN": ("Run against a BSV API stub", "BSVのAPIスタブで実行"), "ENGINE_STAND_IN": ("BSV stand-in engine", "BSVの代替エンジン"),
             "STUB_COMPILE": ("Compiled against BSV stubs", "BSVのスタブでコンパイル"), "STRUCTURAL": ("Structural check only", "構造チェックのみ"),
             "PARITY_ONLY": ("Browser = CLI output only", "ブラウザとCLIの一致のみ")}


def coverage_csv(cov: dict) -> str:
    """TODO matrix of coverage.json as CSV (Issue #8 tranche 9): one row per recipe, one column per target; then one row
    per target with its check kind and higher-timeframe status. Every value is copied from `cov`."""
    import csv, io
    b = io.StringIO(); w = csv.writer(b, lineterminator="\r\n"); T = [x["id"] for x in cov["targets"]]
    w.writerow(["recipe"] + T)
    for r in cov["recipes"]: w.writerow([r["id"]] + [r["todoLines"][t] for t in T])
    w.writerow([]); w.writerow(["target", "check_kind", "check_script", "higher_timeframe", "runtime_tested_by_bsv"])
    for x in cov["targets"]: w.writerow([x["id"], x["check"]["kind"], x["check"]["script"], x["higherTimeframe"]["status"], "false"])
    return b.getvalue()


def coverage_page(site: Path, cov: dict) -> str:
    """Readable view of /trading/build/coverage.json (Issue #8 tranche 8). Static HTML, no script; every cell is read
    from `cov`."""
    c = cov["counts"]; T = cov["targets"]; nT, nP = c["targets"], c["recipeTargetPairsWithoutTodo"]
    trows = "".join(
        f'<tr id="cov-{blt.esc(x["id"])}"><td>{blt.esc(x["label"])}</td><td data-kind="{x["check"]["kind"]}">{both(*KIND_TEXT[x["check"]["kind"]])}</td>'
        f'<td><code>{blt.esc(x["check"]["script"])}</code></td><td data-htf="{x["higherTimeframe"]["status"]}">{both("Closed bars, checked", "確定足・確認済み") if x["higherTimeframe"]["status"] == "CLOSED_BARS_CHECKED" else (both("Closed bars, documented idiom (static check)", "確定足・公式の方法（静的確認）") if x["higherTimeframe"]["status"] == "CLOSED_BAR_IDIOM_STATIC" else both("TODO stub", "TODOのスタブ"))}</td>'
        f'<td class="small">{blt.esc(x["check"]["note"])}{"".join(f' <a class="small" data-doc href="{blt.esc(u)}" rel="noopener">{blt.esc(u.split("//", 1)[1].split("/", 1)[0])}</a>' for u in x["higherTimeframe"].get("docs", []))}</td></tr>' for x in T)
    head = "".join(f'<th title="{blt.esc(x["label"])}"><code>{blt.esc(x["id"])}</code></th>' for x in T)
    mrows = "".join(f'<tr id="todo-{blt.esc(r["id"])}"><th><code>{blt.esc(r["id"])}</code></th>' + "".join(f'<td data-n="{r["todoLines"][x["id"]]}">{r["todoLines"][x["id"]]}</td>' for x in T) + "</tr>" for r in cov["recipes"])
    kinds = " · ".join(f'{KIND_TEXT[k][0]} {n}' for k, n in c["byCheckKind"].items())
    desc = f'For each of the {c["targets"]} BSV generator targets, which BSV check covers it, and the TODO lines per recipe and target. None is runtime-tested by BSV.'
    body = (f'<section class="container bb-section"><p class="small"><a href="/trading/build/">{both("Recipe builder", "レシピビルダー")}</a> › {both("Coverage", "確認状況")}</p>'
            f'<h1>{both("Generator coverage: what BSV checks for each target", "ジェネレーターの確認状況：出力先ごとにBSVが確かめていること")}</h1>'
            f'<p>{both(desc, f"BSVジェネレーターの{nT}種類の出力先それぞれについて、どのBSVチェックで確かめているか、レシピ×出力先ごとのTODO行の数を示します。BSVが実際の環境で動かして確かめた出力先はありません。")}</p>'
            f'<p class="small">{blt.esc(kinds)} · runtimeTestedByBSV: {c["runtimeTestedByBSV"]} · <a href="/trading/build/coverage.json">coverage.json</a> · <a href="/trading/build/coverage.csv" download>coverage.csv</a></p>'
            f'<div class="rp-box"><p class="small">{both(cov["higherTimeframeDisclosure"], HTF_DISCLOSURE_JA)}</p></div>'
            f'<h2 id="targets">{both("Targets", "出力先")}</h2><div class="bb-table-wrap"><table class="qa-table" id="cov-targets"><thead><tr><th>{both("Target", "出力先")}</th><th>{both("BSV check", "BSVのチェック")}</th><th>{both("Script", "スクリプト")}</th><th>{both("Higher timeframe", "上位足")}</th><th>{both("What it is not", "これは何でないか")}</th></tr></thead><tbody>{trows}</tbody></table></div>'
            f'<h2 id="todo">{both("TODO lines per recipe and target", "レシピ×出力先ごとのTODO行")}</h2>'
            f'<p class="small">{both(f"0 means the generator rendered every block of that recipe for that target ({nP} pairs). It does not mean the output was run on the platform.", "0は、その出力先でレシピのすべてのブロックを出力できたという意味です。プラットフォームで動かしたという意味ではありません。")}</p>'
            f'<div class="bb-table-wrap"><table class="qa-table" id="cov-todo"><thead><tr><th>{both("Recipe", "レシピ")}</th>{head}</tr></thead><tbody>{mrows}</tbody></table></div></section>')
    ld = {"@context": "https://schema.org", "@type": "Dataset", "name": "BSV generator coverage", "description": desc, "url": ORIGIN + "/trading/build/coverage/",
          "isAccessibleForFree": True, "creator": {"@type": "Organization", "name": "BotShelf Vampire", "url": ORIGIN + "/"},
          "variableMeasured": ["check.kind", "higherTimeframe.status", "todoLines", "runtimeTestedByBSV"],
          "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": ORIGIN + "/trading/build/coverage.json"},
                           {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": ORIGIN + "/trading/build/coverage.csv"}]}
    return blt.trader_shell(site, "Generator coverage — what BSV checks for each target · BotShelf Vampire", desc, "/trading/build/coverage/", body,
                            extra_head='<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + "</script>")


def builders_section(site: Path) -> str:
    import build_discovery as bd
    gaps = catalogue_gaps(site)
    rows = "".join(f'<tr><td>{both(g["label"], g["label_ja"])}</td><td>{g["count"]}</td><td class="small">{blt.esc(", ".join(f"{k} {v}" for k, v in g["byKind"].items()))}</td></tr>' for g in gaps)
    split = [x for x in bd.FACTS if x[0] == "seller_split_payout"][0]
    gg = generator_gaps()
    LABEL = {t: lab for t, lab, _ in blt.TARGETS}
    grows = "".join(f'<tr id="gap-{blt.esc(g["blockType"])}"><td><code>{blt.esc(g["blockType"])}</code></td><td>{g["recipeCount"]} <span class="small muted">({blt.esc(", ".join(g["recipes"]))})</span></td><td>{g["targetsWithIt"]} / {gg["targets"]}{(' <span class="small muted">(' + blt.esc(", ".join(LABEL[t] for t in g["targetsRenderingIt"])) + ')</span>') if g["targetsRenderingIt"] else ""}</td><td><a class="small" data-ask="{blt.esc(g["blockType"])}" href="/requests/?area=trading&amp;block={blt.esc(g["blockType"])}#rq-form">{both("Ask for it", "リクエストする")}</a></td></tr>' for g in gg["gaps"])
    gen_en = f"Counted at build time by rendering all {gg['recipes']} BSV recipes for all {gg['targets']} targets and reading the generator's own TODO lines ({gg['recipesWithGaps']} recipes have at least one). A fact about the generator, not a measure of demand."
    gen_ja = f"BSVレシピ{gg['recipes']}件を{gg['targets']}種類の出力先すべてで生成し、ジェネレーター自身のTODO行から数えた値です（1つ以上あるレシピは{gg['recipesWithGaps']}件）。ジェネレーターについての事実で、需要の量ではありません。"
    return (
        f'<section class="container bb-section" id="builders"><h2>{both("For builders: opportunities from real signals", "作り手の方へ: 実際のデータからわかること")}</h2>'
        f'<p>{both("Do not guess what to build. Everything below comes from real data; there are no revenue projections.", "何を作るか推測しなくて済むように、以下はすべて実際のデータです。売上の見込みは載せていません。")}</p>'
        f'<h3>{both("Open public requests by area (live)", "分野ごとの公開中リクエスト（その場で集計）")}</h3>'
        '<ul class="rq-list" id="rq-areas"><li class="empty">' + both("Loading…", "読み込み中…") + '</li></ul>'
        f'<p class="small muted">{both("Score = number of open public requests in that area; budget = how many of them state one. Both come from the request store.", "スコア＝その分野の公開中リクエストの数、予算あり＝そのうち予算が書かれている数。どちらもリクエストの保存先から数えています。")}</p>'
        f'<h3 id="heatmap">{both("Demand heatmap: area × platform (live)", "需要ヒートマップ：分野×プラットフォーム（その場で集計）")}</h3>'
        f'<p class="small">{both("Counts of open public requests only, aggregated in your browser from the same public JSON. A request with several areas or platforms counts once in each cell; “—” = no platform stated. No user ids, no private or pending requests, no searches or page views.", "公開中のリクエストの件数だけを、同じ公開JSONからこのブラウザ内で集計します。複数の分野・プラットフォームを持つリクエストは各マスに1件ずつ数えます。「—」はプラットフォーム未記入です。ユーザーID・非公開や確認待ちのリクエスト・検索・閲覧数は含みません。")}</p>'
        '<div class="bb-table-wrap"><table class="qa-table" id="rq-heat"></table></div>'
        f'<h3>{both("Supply gaps in the Traders Library catalogue", "Traders Library カタログの空き")}</h3>'
        f'<p class="small">{both("Counted from /trading/catalog.json. This is a fact about the catalogue, not a measure of demand. Porting someone else's source must follow that entry's license.", "/trading/catalog.json から数えた値です。カタログの事実であって、需要の大きさではありません。他の人のソースを移植する場合は、その項目のライセンスに従ってください。")}</p>'
        f'<div class="bb-table-wrap"><table class="qa-table"><thead><tr><th>{both("Gap", "空き")}</th><th>{both("Entries", "件数")}</th><th>{both("By type", "種類別")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
        f'<h3 id="generator-gaps">{both("Blocks the generator cannot render yet", "ジェネレーターがまだ出力できないブロック")}</h3>'
        f'<p class="small">{both(gen_en, gen_ja)} <a href="/trading/build/coverage/">{both("Coverage by target", "出力先ごとの確認状況")}</a> · <a href="/trading/build/coverage.json">coverage.json</a></p>'
        f'<div class="bb-table-wrap"><table class="qa-table" id="rq-gen-gaps"><thead><tr><th>{both("Block type", "ブロックの種類")}</th><th>{both("Recipes using it", "使っているレシピ")}</th><th>{both("Targets that render it", "出力できる出力先")}</th><th>{both("Request", "リクエスト")}</th></tr></thead><tbody>{grows}</tbody></table></div>'
        f'<h3>{both("Signals not collected yet", "まだ集めていないデータ")}</h3>'
        f'<p class="small">{both("No-result searches and page-view demand are not logged on this site, so they are not shown.", "結果0件の検索やページの閲覧数は記録していないため、表示していません。")}</p>'
        f'<h3>{both("If you build it", "作ったら")}</h3><ul><li><q>{blt.esc(split[2])}</q> <a class="small" href="/{split[1]}">{split[1]}</a></li>'
        f'<li>{both("Label exactly what you checked; untested stays untested.", "確認した範囲をそのまま表示します。未検証は未検証のままです。")} <a class="small" href="/transparency/#labels">/transparency/</a></li>'
        f'<li><a href="/trading/build/">{both("Build from recipe blocks", "レシピのブロックから作る")}</a> · <a href="/for-sellers.html">{both("How to publish", "出品のしかた")}</a> · <a href="/requests/opportunities.json">opportunities.json</a> · <a href="{API}?op=signals">{both("signals JSON", "シグナルJSON")}</a> (<a href="/schemas/opportunity-signal-v0.1.json">opportunity-signal v0.1</a>)</li></ul></section>'
    )


def page(site: Path, css_href: str, js_href: str) -> str:
    checks = "".join(f'<label><input type="checkbox" name="domain" value="{d}">{both(en, ja)}</label>' for d, en, ja in DOMAINS)
    body = (
        '<section class="container hero bb-hero"><div><div class="eyebrow">REQUEST MARKET</div>'
        f'<h1>{both("Request a tool, indicator or workflow.", "ほしいツール・インジケーター・ワークフローをリクエストする。")}</h1>'
        f'{both("Describe the job you need done. Builders can see real requests and build from them. There is no escrow and no promise that a request will be built.", "やってほしいことを書いてください。作り手は実際のリクエストを見て、そこから作れます。エスクローはなく、作られる約束もありません。", "p", "lead")}'
        f'{both("Only real requests are shown. Counts are read from the request store; nothing is seeded or estimated. Each request is reviewed before it is listed, private requests are never listed, and your email is never shown.", "表示するのは実際のリクエストだけです。数はリクエストの保存先から数えたもので、見本や推計は入れていません。公開の前に1件ずつ確認します。非公開のリクエストは表示せず、メールアドレスも表示しません。", "p", "small")}'
        '</div><aside class="hero-stats"><div class="stat-lines">'
        f'<div>{both("Requests received", "受け付けた数")}<b id="rq-c-received">–</b></div>'
        f'<div>{both("Listed after review", "確認後に公開")}<b id="rq-c-published">–</b></div>'
        f'<div>{both("Listed with a stated budget", "予算の記載あり（公開分）")}<b id="rq-c-budget">–</b></div>'
        '</div></aside></section>'
        '<div class="container subnav"><a class="chip" href="#open">' + both("Open requests", "公開中のリクエスト") + '</a><a class="chip" href="#new">' + both("New request", "新しいリクエスト") + '</a>'
        '<a class="chip" href="/trading/build/">' + both("Build your own chart tool", "自分のチャートツールを作る") + '</a><a class="chip" href="/for-sellers.html">' + both("Seller guide", "出品者ガイド") + '</a></div>'
        f'<section class="container bb-section" id="open"><h2>{both("Open requests", "公開中のリクエスト")}</h2>'
        '<div class="rq-filter" id="rq-filter" role="group" aria-label="Filter by area"></div><p class="small muted" id="rq-filter-note" role="status"></p><p class="small" id="rq-target-note" role="status"></p>'
        '<ul class="rq-list" id="rq-list"><li class="empty">' + both("Loading…", "読み込み中…") + '</li></ul>'
        f'<p class="small muted">{both("A stated budget is what the requester typed. It is not escrow, a payment or a promise to pay.", "予算は依頼者が書いた金額です。エスクロー・支払い・支払いの約束ではありません。")} '
        f'<a href="{API}?op=public">JSON</a> · <a href="{API}?op=feed">{both("Atom feed", "Atomフィード")}</a> · <a href="/schemas/demand-request-v0.1.json">schema v0.1</a></p></section>'
        + builders_section(site) +
        f'<section class="container bb-section" id="new"><h2>{both("New request", "新しいリクエスト")}</h2>'
        f'<p class="small">{both("Sending needs a verified email (free registration with a 6-digit code). Up to 5 requests per day.", "送信にはメール確認が必要です（無料登録・6桁のコード）。1日5件まで。")}</p>'
        f'<p class="small rp-box" id="rq-mission" hidden>{both("Robot pilot mission: include the task, robot/embodiment, teleop interface, simulation or real hardware, location or remote, data needed, episode target and quality criteria. Real hardware stays under the robot owner's authorisation and safety rules. Request only; no escrow.", "ロボット遠隔操作のミッション: タスク、ロボット、遠隔操作の方法、シミュレーションか実機か、場所またはリモート、必要なデータ、エピソード数、品質の基準を書いてください。実機はロボットの所有者の許可と安全ルールのもとで行います。リクエストのみで、エスクローはありません。")}</p>'
        '<form class="rq-form" id="rq-form" novalidate>'
        f'<div><label for="rq-job">{both("What job should it do? (20–2000 characters)", "何をしてほしいですか（20〜2000文字）")}</label><textarea id="rq-job" maxlength="2000" required></textarea></div>'
        f'<fieldset><legend>{both("Area", "分野")}</legend><div class="rq-checks">{checks}</div></fieldset>'
        f'<div><label for="rq-platforms">{both("Platform / runtime (comma separated)", "プラットフォーム・実行環境（カンマ区切り）")}</label><input type="text" id="rq-platforms" maxlength="480" placeholder="TradingView, MT5, n8n, ROS 2">'
        f'<p class="small muted" id="rq-plat-picks">{both("Trading platforms the recipe builder writes starters for (tap to add; any other platform can be typed):", "レシピビルダーが出力するトレード用プラットフォーム（タップで追加。ほかのプラットフォームは入力できます）:")} '
        + " ".join(f'<button type="button" class="chip" data-rq-plat="{blt.esc(p)}">{blt.esc(p)}</button>' for p in dict.fromkeys(l.split(" · ")[0] for _, l, _ in blt.TARGETS)) + '</p>'
        f'<p class="small muted" id="rq-ai-picks">{both("AI frameworks with BSV toolkit items (tap to add; any other can be typed):", "BSVのAIツールキットがあるフレームワーク（タップで追加。ほかも入力できます）:")} '
        + " ".join(f'<button type="button" class="chip" data-rq-plat="{blt.esc(p)}">{blt.esc(p)}</button>' for p in ai_frameworks()) + '</p></div>'
        f'<div class="rq-row"><div><label for="rq-in">{both("Inputs", "入力")}</label><input type="text" id="rq-in" maxlength="960"></div><div><label for="rq-out">{both("Outputs", "出力")}</label><input type="text" id="rq-out" maxlength="960"></div></div>'
        f'<div class="rq-row"><div><label for="rq-free">{both("Free / open solution OK?", "無料・オープンな解決でもよいか")}</label><select id="rq-free"><option value="">—</option><option value="yes">Yes / はい</option><option value="no">No / いいえ</option></select></div>'
        f'<div><label for="rq-min">{both("Budget min (USDT, optional)", "予算の下限（USDT・任意）")}</label><input type="number" id="rq-min" min="0" step="1"></div>'
        f'<div><label for="rq-max">{both("Budget max (USDT, optional)", "予算の上限（USDT・任意）")}</label><input type="number" id="rq-max" min="0" step="1"></div>'
        f'<div><label for="rq-deadline">{both("Deadline (optional)", "期限（任意）")}</label><input type="date" id="rq-deadline"></div></div>'
        f'<fieldset><legend>{both("Visibility", "公開範囲")}</legend><div class="rq-checks">'
        f'<label><input type="radio" name="visibility" value="PUBLIC">{both("Public after review", "確認後に公開")}</label>'
        f'<label><input type="radio" name="visibility" value="PRIVATE">{both("Private (only BSV reviewers see it)", "非公開（BSVの確認担当だけが見ます）")}</label></div></fieldset>'
        f'<div class="rq-checks"><label><input type="checkbox" id="rq-contact">{both("BSV may contact me by email about this request", "このリクエストについてBSVからメールで連絡してよい")}</label></div>'
        f'<div><button type="submit" class="btn primary">{both("Send request", "リクエストを送る")}</button></div>'
        '<p class="rq-msg" id="rq-msg" role="status"></p></form></section>'
    )
    html_ = blt.trader_shell(site, "Request Market — ask for a tool, indicator or workflow · BotShelf Vampire",
                             "Describe a trading tool, AI workflow or frontier-industry capability you need. Only real, reviewed requests are listed; counts come from the request store.",
                             "/requests/", body, extra_head=f'<link rel="stylesheet" href="{css_href}"><link rel="alternate" type="application/atom+xml" title="BSV Request Market: approved public requests" href="{API}?op=feed"><script src="{js_href}" defer></script>')
    foot = ('<footer class="site-footer"><div class="container"><p data-lang="en">Requests are written by users and reviewed by BSV before they are listed. BSV does not promise that a request will be built, and a stated budget is not a payment. Paid listings follow the seller guide.</p>'
            '<p data-lang="ja">リクエストは利用者が書いたもので、公開の前にBSVが確認します。作られる約束はなく、記載された予算は支払いではありません。有料の出品は出品者ガイドに従います。</p></div></footer>')
    html_ = re.sub(r'<footer class="site-footer">.*?</footer>', foot, html_, count=1, flags=re.S)
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "BotShelf Vampire", "item": ORIGIN + "/"},
        {"@type": "ListItem", "position": 2, "name": "Request Market", "item": ORIGIN + "/requests/"}]}
    return html_.replace("</head>", f'<script type="application/ld+json">{json.dumps(crumbs, separators=(",", ":"))}</script></head>', 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); a = ap.parse_args()
    site = Path(a.site)
    blt.assets(site)
    d = site / "requests"; d.mkdir(exist_ok=True)
    for old in d.glob("request-market.*"):
        old.unlink()
    lab = {k: en for k, en, _ in DOMAINS}
    js = JS.replace("%API%", API).replace("%LAB%", json.dumps(lab))
    css_n, js_n = f"request-market.{h8(CSS)}.css", f"request-market.{h8(js)}.js"
    (d / css_n).write_text(CSS); (d / js_n).write_text(js)
    (d / "index.html").write_text(page(site, f"/requests/{css_n}", f"/requests/{js_n}"))
    gaps = catalogue_gaps(site)
    (d / "opportunities.json").write_text(json.dumps({
        "schemaNote": "BSV builder opportunity feed v0.1. Real signals only; no revenue projections.",
        "generatedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signals": {
            "publicRequests": {"source": ORIGIN + API + "?op=public", "note": "Live: open public requests and their stated budgets, read from the request store."},
            "opportunitySignals": {"source": ORIGIN + API + "?op=signals", "schema": ORIGIN + "/schemas/opportunity-signal-v0.1.json", "note": "Live: REQUEST / FULFILLED_REQUEST signals aggregated from approved public requests. Other signal types are not produced because they are not collected."},
            "noResultSearches": {"collected": False, "note": "Not logged on this site."},
            "pageViews": {"collected": False, "note": "Not logged on this site."},
            "generatorGaps": {"source": "trader-toolkit/generator/render.mjs and trader-toolkit/recipes in the BSV repository", "note": "Block types the BSV generator does not render yet, counted from its own TODO lines at build time. Facts about the generator, not demand.", **generator_gaps()},
            "catalogueGaps": {"source": ORIGIN + "/trading/catalog.json", "note": "Facts about the catalogue, not demand. Porting third-party source must follow its license.", "gaps": gaps}},
    }, ensure_ascii=False, indent=1) + "\n")
    (site / "trading/build").mkdir(parents=True, exist_ok=True)
    cov = generator_coverage()
    (site / "trading/build/coverage.json").write_text(json.dumps(cov, ensure_ascii=False, indent=1) + "\n")
    (site / "trading/build/coverage").mkdir(exist_ok=True)
    (site / "trading/build/coverage/index.html").write_text(coverage_page(site, cov))
    (site / "trading/build/coverage.csv").write_text(coverage_csv(cov))
    smp = site / "sitemap.xml"; sm = smp.read_text(); u = ORIGIN + "/trading/build/coverage/"
    if f"<loc>{u}</loc>" not in sm:
        smp.write_text(sm.replace("</urlset>", f"  <url><loc>{u}</loc><lastmod>2026-10-04</lastmod></url>\n</urlset>"))
    sd = site / "schemas"; sd.mkdir(exist_ok=True)
    (sd / "demand-request-v0.1.json").write_text((REPO / "schemas/bsv-demand-request.schema.json").read_text())
    (sd / "opportunity-signal-v0.1.json").write_text((REPO / "schemas/bsv-opportunity-signal.schema.json").read_text())
    smp = site / "sitemap.xml"; s = smp.read_text()
    u = ORIGIN + "/requests/"
    if f"<loc>{u}</loc>" not in s:
        s = s.replace("</urlset>", f"  <url><loc>{u}</loc><lastmod>2026-10-03</lastmod></url>\n</urlset>")
        smp.write_text(s)
    b = site / "trading/build/index.html"; t = b.read_text()
    chip = '<a class="chip" href="/requests/" data-rq-link><span data-lang="en">Request a tool</span><span data-lang="ja">ツールをリクエスト</span></a>'
    if "data-rq-link" not in t:
        t = t.replace('<a class="chip" href="/trading/"><span data-lang="en">Traders Library</span>', chip + '<a class="chip" href="/trading/"><span data-lang="en">Traders Library</span>', 1)
        b.write_text(t)
    print(json.dumps({"requests_page": "/requests/", "js": js_n, "css": css_n, "build_link": "data-rq-link" in b.read_text()}))


if __name__ == "__main__":
    main()
