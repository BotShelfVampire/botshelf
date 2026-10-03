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
  var li=el('li',{'class':'bb-card','data-request-id':r.requestId},[el('div',{'class':'bb-meta'},[el('span',{text:meta.join(' — ')}),el('span',{'class':'bb-flag',text:r.status})]),el('p',{'class':'rq-job',text:r.job})]);
  var d=[];if(r.desiredInputs&&r.desiredInputs.length)d.push('In: '+r.desiredInputs.join(', '));if(r.desiredOutputs&&r.desiredOutputs.length)d.push('Out: '+r.desiredOutputs.join(', '));
  if(r.freeSolutionAcceptable===true)d.push('Free/open solution OK');
  if(r.willingnessToPay){var w=r.willingnessToPay;d.push('Stated budget: '+(w.min!=null?w.min:'?')+'–'+(w.max!=null?w.max:'?')+' USDT (not escrow)')}
  if(r.deadline)d.push('Deadline: '+r.deadline.slice(0,10));d.push('Posted: '+String(r.createdAt).slice(0,10)+' · '+r.requestId);
  li.appendChild(el('p',{'class':'small muted',text:d.join(' · ')}));ul.appendChild(li)})}
function areas(rs){var ul=$('#rq-areas');if(!ul)return;ul.textContent='';var m={};rs.filter(function(r){return r.status==='OPEN'}).forEach(function(r){(r.domains||[]).forEach(function(d){m[d]=m[d]||{n:0,b:0};m[d].n++;if(r.willingnessToPay)m[d].b++})});
 var ks=Object.keys(m).sort(function(a,b){return m[b].n-m[a].n});if(!ks.length){ul.appendChild(el('li',{'class':'empty'},[bi('No open public requests yet, so there is no area score yet.','公開中のリクエストがまだないため、分野ごとのスコアはまだありません。')]));return}
 ks.forEach(function(k){ul.appendChild(el('li',{'class':'bb-card'},[el('strong',{text:(LAB[k]||k)+' — score '+m[k].n}),el('span',{'class':'small muted',text:'with a stated budget: '+m[k].b}) ]))})}
function load(){fetch(API+'?op=public',{credentials:'omit'}).then(function(r){return r.json()}).then(function(j){if(j&&j.ok){render(j);areas(j.requests||[])}else throw 0}).catch(function(){var ul=$('#rq-list');ul.textContent='';ul.appendChild(el('li',{'class':'empty'},[bi('Could not load requests right now.','いまはリクエストを読み込めません。')]))})}
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
 if(q.get('kind')==='mission'){var j=$('#rq-job');if(j)j.setAttribute('placeholder','Mission: task to demonstrate; robot / embodiment; teleop interface; simulation or real hardware (owner-authorised, safety rules); location or remote; data needed; episode target; quality criteria; privacy / NDA');var h=$('#rq-mission');if(h)h.hidden=false}}
document.addEventListener('DOMContentLoaded',function(){prefill();load();var f=$('#rq-form');if(f)f.addEventListener('submit',submit)});
})();
"""


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


def builders_section(site: Path) -> str:
    import build_discovery as bd
    gaps = catalogue_gaps(site)
    rows = "".join(f'<tr><td>{both(g["label"], g["label_ja"])}</td><td>{g["count"]}</td><td class="small">{blt.esc(", ".join(f"{k} {v}" for k, v in g["byKind"].items()))}</td></tr>' for g in gaps)
    split = [x for x in bd.FACTS if x[0] == "seller_split_payout"][0]
    return (
        f'<section class="container bb-section" id="builders"><h2>{both("For builders: opportunities from real signals", "作り手の方へ: 実際のデータからわかること")}</h2>'
        f'<p>{both("Do not guess what to build. Everything below comes from real data; there are no revenue projections.", "何を作るか推測しなくて済むように、以下はすべて実際のデータです。売上の見込みは載せていません。")}</p>'
        f'<h3>{both("Open public requests by area (live)", "分野ごとの公開中リクエスト（その場で集計）")}</h3>'
        '<ul class="rq-list" id="rq-areas"><li class="empty">' + both("Loading…", "読み込み中…") + '</li></ul>'
        f'<p class="small muted">{both("Score = number of open public requests in that area; budget = how many of them state one. Both come from the request store.", "スコア＝その分野の公開中リクエストの数、予算あり＝そのうち予算が書かれている数。どちらもリクエストの保存先から数えています。")}</p>'
        f'<h3>{both("Supply gaps in the Traders Library catalogue", "Traders Library カタログの空き")}</h3>'
        f'<p class="small">{both("Counted from /trading/catalog.json. This is a fact about the catalogue, not a measure of demand. Porting someone else's source must follow that entry's license.", "/trading/catalog.json から数えた値です。カタログの事実であって、需要の大きさではありません。他の人のソースを移植する場合は、その項目のライセンスに従ってください。")}</p>'
        f'<div class="bb-table-wrap"><table class="qa-table"><thead><tr><th>{both("Gap", "空き")}</th><th>{both("Entries", "件数")}</th><th>{both("By type", "種類別")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
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
        '<ul class="rq-list" id="rq-list"><li class="empty">' + both("Loading…", "読み込み中…") + '</li></ul>'
        f'<p class="small muted">{both("A stated budget is what the requester typed. It is not escrow, a payment or a promise to pay.", "予算は依頼者が書いた金額です。エスクロー・支払い・支払いの約束ではありません。")} '
        f'<a href="{API}?op=public">JSON</a> · <a href="/schemas/demand-request-v0.1.json">schema v0.1</a></p></section>'
        + builders_section(site) +
        f'<section class="container bb-section" id="new"><h2>{both("New request", "新しいリクエスト")}</h2>'
        f'<p class="small">{both("Sending needs a verified email (free registration with a 6-digit code). Up to 5 requests per day.", "送信にはメール確認が必要です（無料登録・6桁のコード）。1日5件まで。")}</p>'
        f'<p class="small rp-box" id="rq-mission" hidden>{both("Robot pilot mission: include the task, robot/embodiment, teleop interface, simulation or real hardware, location or remote, data needed, episode target and quality criteria. Real hardware stays under the robot owner's authorisation and safety rules. Request only; no escrow.", "ロボット遠隔操作のミッション: タスク、ロボット、遠隔操作の方法、シミュレーションか実機か、場所またはリモート、必要なデータ、エピソード数、品質の基準を書いてください。実機はロボットの所有者の許可と安全ルールのもとで行います。リクエストのみで、エスクローはありません。")}</p>'
        '<form class="rq-form" id="rq-form" novalidate>'
        f'<div><label for="rq-job">{both("What job should it do? (20–2000 characters)", "何をしてほしいですか（20〜2000文字）")}</label><textarea id="rq-job" maxlength="2000" required></textarea></div>'
        f'<fieldset><legend>{both("Area", "分野")}</legend><div class="rq-checks">{checks}</div></fieldset>'
        f'<div><label for="rq-platforms">{both("Platform / runtime (comma separated)", "プラットフォーム・実行環境（カンマ区切り）")}</label><input type="text" id="rq-platforms" maxlength="480" placeholder="TradingView, MT5, n8n, ROS 2"></div>'
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
                             "/requests/", body, extra_head=f'<link rel="stylesheet" href="{css_href}"><script src="{js_href}" defer></script>')
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
            "catalogueGaps": {"source": ORIGIN + "/trading/catalog.json", "note": "Facts about the catalogue, not demand. Porting third-party source must follow its license.", "gaps": gaps}},
    }, ensure_ascii=False, indent=1) + "\n")
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
