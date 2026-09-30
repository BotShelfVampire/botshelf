#!/usr/bin/env python3
"""Build a license-preserving, static Traders Library. Offline and deterministic.
No network requests. No third-party trading code is executed.
"""
from __future__ import annotations
import base64, hashlib, html, json, re, zipfile, io
from pathlib import Path
from collections import Counter

BASE=Path(__file__).resolve().parent
OUT=BASE/'trading'
OUT.mkdir(exist_ok=True)
DATA=json.loads((BASE/'bundled_catalog.json').read_text('utf-8'))
if (BASE/'author_catalog.json').exists():
    DATA+=json.loads((BASE/'author_catalog.json').read_text('utf-8'))
E=lambda x:html.escape(str(x),quote=True)
J=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
DATE='2026-10-01'
ENJA=lambda en,ja,tag='span',cls='':f'<{tag} data-lang="en" class="{cls}">{E(en)}</{tag}><{tag} data-lang="ja" class="{cls}">{E(ja)}</{tag}>'
HASH=lambda b:hashlib.sha256(b).hexdigest()
BLOB=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
LICENSE_HASH={'GPL-3.0-only':'f288702d2fa16d3cdf0035b15a9fcbc552cd88e7','MIT':'0c89a10691806014181b818c55ac3b5784683a16','Apache-2.0':'261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64'}
CATEGORY_JA={'Trend':'トレンド','Breakout':'ブレイクアウト','Mean reversion':'平均回帰','Momentum':'モメンタム','Research':'研究','Volatility':'ボラティリティ','Volume':'出来高','Chart tools':'チャート補助','Price action':'値動き','Trade management':'注文・決済管理','Risk tools':'リスク確認','Sessions':'時間帯','Levels':'価格水準'}
KIND_JA={'Indicator':'インジケーター','Strategy':'ストラテジー','Expert Advisor':'自動売買EA','Trade manager':'取引管理EA','Script':'スクリプト','Template':'開発ひな形'}
for folder in ['assets','items','guides','downloads','licenses','provenance']:(OUT/folder).mkdir(exist_ok=True)

# The landing order is editorial, not a popularity or profitability ranking.
front=['bachini-crossover','earnforex-position-sizer','earnforex-positionsizer','everget-arnaud-legoux-moving-average','earnforex-marketprofile','bachini-breakout-sniper','earnforex-atr-trailing-stop','earnforex-spike-trader','bachini-price-channels']
priority={id:i for i,id in enumerate(front)}
DATA.sort(key=lambda d:(priority.get(d['id'],100),d['name'].lower()))
assert len({d['id'] for d in DATA})==len(DATA),'Duplicate catalogue IDs'

# Normalize and statically inspect supported source snapshots.
for d in DATA:
    assert re.fullmatch(r'[a-z0-9-]+',d['id']),d['id']
    d['detail_url']='items/'+d['id']+'.html'
    d.setdefault('risk_level','Not runtime tested')
    d.setdefault('distribution','bundled')
    d.setdefault('version','See source')
    d['is_bundled']=d['distribution']=='bundled'
    if d['is_bundled']:
        if '/' not in d['license_file']: d['license_file']='licenses/'+d['license_file']
        lic=(OUT/d['license_file']).read_bytes()
        assert BLOB(lic)==LICENSE_HASH[d['license']],(d['id'],'license hash mismatch')
        d['license_blob_sha1']=BLOB(lic)
        if not d.get('files'):
            d['files']=[{'path':d['path'],'local_source':d['local_source'],'blob_sha1':d['blob_sha1'],'sha256':d['sha256'],'encoding':'utf-8'}]
        texts=[]
        for f in d['files']:
            b=(OUT/f['local_source']).read_bytes()
            assert BLOB(b)==f['blob_sha1'],(d['id'],'source mismatch')
            assert HASH(b)==f['sha256'],(d['id'],'source SHA256 mismatch')
            f['bytes']=len(b)
            f['source_url']=f"https://github.com/{d['repo']}/blob/{d['commit']}/{f['path']}"
            text=b.decode(f.get('encoding','utf-8'))
            texts.append(text)
            if not f.get('platform'):f['platform']='MT4' if f['path'].endswith('.mq4') else 'MT5' if f['path'].endswith('.mq5') else 'TradingView'
        joined='\n'.join(texts)
        assert not re.search(r'CC[- ]BY[- ]NC|redistribution prohibited|do not redistribute',joined,re.I),(d['id'],'conflicting notice')
        version=re.search(r'//@version=(\d+)',joined)
        d['version']='Pine v'+version.group(1) if version else 'MQL4 / MQL5'
        d['legacy']=bool(version and int(version.group(1))<6)
        # Explicitly a pattern scan. Absence of patterns is not a safety guarantee.
        d['scan']={k:bool(re.search(p,joined,re.I)) for k,p in {
            'dll_import':r'#import\s+["\'][^"\']+\.dll',
            'web_request':r'\bWebRequest\s*\(',
            'pine_security':r'\b(?:request\.)?security\s*\(',
            'lookahead_on':r'lookahead\s*=\s*barmerge\.lookahead_on',
            'order_calls':r'\b(?:OrderSend|PositionOpen|PositionClose|OrderClose)\s*\(',
            'strategy_orders':r'\bstrategy\.(?:entry|order|exit|close)\s*\(',
            'external_include':r'#include',
            'file_write':r'\bFile(?:Write|Open)\s*\('}.items()}
        d['runtime_tested']=False
        d['compiled']=False
        d['source_count']=len(d['files'])
        d['download']='downloads/'+d['id']+'.zip'
        d['provenance_url']='provenance/'+d['id']+'.json'
    else:
        d['source_count']=None
        assert d['source_url'].startswith('https://github.com/EarnForex/'),d['id']
        assert d['license']=='Apache-2.0',d['id']

COUNTS={'items':len(DATA),'bundled':sum(d['is_bundled'] for d in DATA),'author_hosted':sum(not d['is_bundled'] for d in DATA),'source_files':sum(d['source_count'] or 0 for d in DATA),'kinds':dict(Counter(d['kind'] for d in DATA))}

CSS=r'''
:root{color-scheme:dark;--bg:#0d100f;--panel:#151a17;--panel2:#1b211d;--line:#313930;--text:#f2f1e9;--muted:#a5afa3;--gold:#dfc583;--green:#bad4b7;--danger:#e9b99e;--sans:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif;--mono:ui-monospace,SFMono-Regular,Consolas,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:100px}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 var(--sans)}a{color:inherit;text-decoration:none}button,input,select{font:inherit}button,a,input,select{touch-action:manipulation}button{cursor:pointer}button:disabled{opacity:.5;cursor:default}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:4px}button,a{ -webkit-tap-highlight-color:transparent}img{max-width:100%}[hidden]{display:none!important}html[lang=en] [data-lang=ja],html[lang=ja] [data-lang=en]{display:none!important}.container{width:min(1380px,calc(100% - 64px));margin:auto}.site-header{border-bottom:1px solid var(--line);background:var(--bg)}.header-inner{min-height:90px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{display:flex;align-items:center;gap:12px;white-space:nowrap}.brandmark{display:grid;place-items:center;border:1px solid var(--gold);width:38px;height:38px;color:var(--gold);font:bold 14px var(--mono)}.brandword{font-size:12px;font-weight:700;letter-spacing:.15em;line-height:1.4}.brandword small{display:block;font:10px var(--mono);letter-spacing:.28em;color:var(--muted);margin-top:5px}.nav{display:flex;align-items:center;gap:28px;color:var(--muted);font-size:13px}.nav a.active{color:var(--text);border-bottom:1px solid var(--gold);padding:5px 0}.language{display:flex;border:1px solid var(--line);border-radius:4px;padding:3px;gap:2px}.language button{border:0;color:var(--muted);background:none;padding:6px 10px;font-size:12px;border-radius:2px}.language button[aria-pressed=true]{background:var(--gold);color:var(--bg)}.eyebrow{font:11px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--gold)}.hero{padding:66px 0 54px;display:grid;grid-template-columns:1fr 310px;gap:72px;align-items:end}.hero h1{font-size:clamp(42px,5.5vw,76px);font-weight:580;letter-spacing:-.058em;line-height:1.06;margin:18px 0 24px}.hero h1 em{font-style:normal;color:var(--gold)}.hero .lead{max-width:700px;color:#c3cbbf;font-size:18px;line-height:1.65;margin:0}.hero .small{margin-top:15px;font-size:12px}.hero-stats{border-top:1px solid var(--gold);padding-top:18px}.stat-total{display:flex;align-items:baseline;gap:12px}.stat-total strong{font-size:66px;letter-spacing:-.07em;font-weight:500;line-height:1.1}.stat-total span{font-size:12px;color:var(--muted)}.stat-lines{margin:15px 0;display:grid;gap:7px;font-size:12px}.stat-lines div{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:7px}.stat-lines b{font:12px var(--mono);color:var(--gold)}.small,.muted{color:var(--muted)}.small{font-size:12px}.subnav{display:flex;gap:10px;flex-wrap:wrap;padding:20px 0;border-block:1px solid var(--line);align-items:center}.chip{display:inline-flex;align-items:center;gap:8px;background:none;color:var(--text);border:1px solid var(--line);border-radius:4px;padding:9px 14px;font-size:12px;min-height:38px}.chip:hover,.chip[aria-pressed=true]{border-color:var(--gold);color:var(--gold)}.subnav .intro{color:var(--muted);font-size:12px;margin-right:auto}.main-layout>*{min-width:0}.detail-grid>*{min-width:0}.main-layout{display:grid;grid-template-columns:200px minmax(0,1fr);gap:36px;padding:40px 0 64px}.sidebar h2{font-size:10px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin:2px 0 15px}.type-tabs{display:grid;gap:5px}.type-tabs button{background:none;color:var(--muted);border:0;text-align:left;padding:10px 12px;font-size:13px;border-left:2px solid transparent;display:flex;justify-content:space-between;gap:8px}.type-tabs button > span:last-child{font:11px var(--mono);margin-top:4px;color:var(--muted)}.type-tabs button[aria-pressed=true]{color:var(--text);background:var(--panel);border-left-color:var(--gold)}.sidebar-rule{border-top:1px solid var(--line);margin:26px 0 0;padding-top:22px}.sidebar-rule p{font-size:12px;color:var(--muted)}.sidebar-rule a{text-decoration:underline;text-underline-offset:4px;color:var(--gold);font-size:12px}.collection-header{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-bottom:18px}.collection-header h2{font-size:22px;font-weight:520;letter-spacing:-.025em;margin:0}.results{color:var(--muted);font:11px var(--mono)}.filters{display:grid;grid-template-columns:1.6fr 1fr 1fr;gap:9px;margin-bottom:12px}.search-wrap{position:relative}.search-wrap span{position:absolute;left:13px;top:12px;color:var(--muted);font:16px var(--mono)}.search-wrap input{width:100%;padding:11px 14px 11px 36px;background:var(--panel);border:1px solid var(--line);color:var(--text);border-radius:4px;min-width:0}.filters select,.secondary-filters select{background:var(--panel);color:var(--text);border:1px solid var(--line);padding:10px 12px;border-radius:4px;max-width:100%;min-width:0}.secondary-filters{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:0 0 24px;font-size:12px;flex-wrap:wrap}.filter-left{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.text-button{background:none;color:var(--muted);border:0;font-size:12px;padding:7px 3px}.text-button:hover{color:var(--gold)}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.card{display:flex;flex-direction:column;border:1px solid var(--line);background:var(--panel);border-radius:5px;min-height:294px;padding:20px;transition:transform .15s,border-color .15s;position:relative}.card:hover{transform:translateY(-2px);border-color:#66715f}.card-meta{font:10px var(--mono);letter-spacing:.04em;color:var(--green);display:flex;gap:7px;align-items:center;justify-content:space-between;min-height:22px}.star{border:0;background:none;color:var(--muted);font-size:20px;width:32px;height:32px;display:grid;place-items:center;margin:-7px -9px -7px 0}.star[aria-pressed=true]{color:var(--gold)}.card h3{font-size:18px;line-height:1.32;letter-spacing:-.02em;font-weight:580;margin:17px 0 11px;overflow-wrap:anywhere}.card h3 a:hover{color:var(--gold)}.card p{font-size:12px;line-height:1.7;color:#bbc5b6;margin:0 0 18px}.card .card-bottom{margin-top:auto}.badges{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:15px}.badge{font:9px var(--mono);color:var(--muted);border:1px solid #3a4436;border-radius:3px;padding:4px 6px;line-height:1.2}.badge.license{color:var(--gold)}.badge.risk{color:var(--danger);border-color:#665348}.card-foot{border-top:1px solid var(--line);padding-top:12px;display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10px;color:var(--muted)}.card-foot a{font-size:11px;color:var(--text)}.card-foot a:hover{color:var(--gold)}.empty{text-align:center;padding:65px 20px;border:1px dashed var(--line);border-radius:5px}.empty h3{font-weight:500}.empty p{color:var(--muted)}.btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:4px;min-height:44px;padding:11px 18px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:13px;text-align:center}.btn.primary{color:#171b13;background:var(--gold);border-color:var(--gold);font-weight:650}.btn:hover{filter:brightness(1.08)}.btn.small-btn{font-size:11px;min-height:36px;padding:7px 12px}.no-js{border:1px solid var(--line);padding:15px;color:var(--muted);font-size:12px}.guides-strip{border-top:1px solid var(--line);padding:38px 0 54px}.guides-strip h2{font-size:27px;font-weight:500;letter-spacing:-.03em}.guide-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.guide-card{border:1px solid var(--line);padding:20px;border-radius:4px}.guide-card:hover{border-color:var(--gold)}.guide-card small{color:var(--gold);font:10px var(--mono)}.guide-card h3{font-size:16px;font-weight:500;margin:12px 0 4px}.site-footer{border-top:1px solid var(--line);padding:30px 0 45px;color:var(--muted);font-size:11px}.footer-row{display:flex;justify-content:space-between;gap:20px;margin-bottom:18px;align-items:center}.site-footer p{max-width:1000px;margin:7px 0}.site-footer a{text-decoration:underline;text-underline-offset:4px}.detail{padding:34px 0 60px}.breadcrumb{color:var(--muted);font-size:12px;margin-bottom:28px}.breadcrumb a{color:var(--gold)}.detail-grid{display:grid;grid-template-columns:minmax(0,1fr) 305px;gap:50px;align-items:start}.detail-title{font-size:clamp(32px,4vw,52px);line-height:1.1;font-weight:550;letter-spacing:-.045em;overflow-wrap:anywhere;margin:18px 0}.detail-lead{color:#c1cbbd;font-size:18px;max-width:820px}.prose{max-width:860px}.prose h2{font-size:22px;font-weight:500;letter-spacing:-.02em;margin:34px 0 12px}.prose h3{font-size:16px;margin:25px 0 8px}.prose p,.prose li{color:#c1cbbb;font-size:14px;line-height:1.85;overflow-wrap:anywhere}.prose ol,.prose ul{padding-left:24px}.prose li{margin-bottom:8px}.prose a{color:var(--gold);text-decoration:underline;text-underline-offset:4px}.notice{border:1px solid #554b36;background:#1d1e17;padding:17px 20px;border-radius:4px;margin:22px 0}.notice p{margin:0;font-size:13px}.notice.danger{border-color:#725742;background:#211b17}.notice.danger p{color:#e4c7b2}.download-panel{border:1px solid var(--line);padding:22px;background:var(--panel);border-radius:5px;position:sticky;top:25px}.download-panel .price{font-size:36px;letter-spacing:-.03em;margin:9px 0 15px;font-weight:500}.download-panel .btn{width:100%;margin-top:9px}.download-panel h2{font:11px var(--mono);text-transform:uppercase;letter-spacing:.1em;color:var(--gold);margin:0}.download-panel dl{font-size:11px;border-top:1px solid var(--line);padding-top:10px;margin:19px 0 0}.download-panel dt{color:var(--muted);margin-top:10px}.download-panel dd{margin:2px 0 0;overflow-wrap:anywhere;color:var(--text)}.download-panel .small{font-size:11px}.source-block{border:1px solid var(--line);border-radius:4px;margin:16px 0;overflow:hidden}.source-block summary{padding:15px;cursor:pointer;color:var(--text);background:var(--panel);font:12px var(--mono);overflow-wrap:anywhere}.source-toolbar{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:10px 15px;border-top:1px solid var(--line);font-size:10px;color:var(--muted);flex-wrap:wrap}.source-toolbar a{color:var(--gold)}pre{overflow:auto;padding:18px;margin:0;background:#090d0b;color:#c7d6c0;font:12px/1.65 var(--mono);tab-size:4;max-height:580px;white-space:pre}code{font-family:var(--mono);font-size:.9em;overflow-wrap:anywhere}.hash{font:10px/1.6 var(--mono);word-break:break-all;color:var(--muted)}.provenance{border:1px solid var(--line);padding:19px;border-radius:4px;margin-top:20px}.provenance dl{display:grid;grid-template-columns:140px minmax(0,1fr);gap:10px;font-size:12px;margin:0}.provenance dt{color:var(--muted)}.provenance dd{margin:0;overflow-wrap:anywhere}.guide-page{padding:35px 0 65px;max-width:920px}.guide-page h1{font-size:42px;line-height:1.2;letter-spacing:-.04em;font-weight:530}.qa-table{width:100%;border-collapse:collapse;font-size:12px;margin:17px 0}.qa-table td,.qa-table th{border-bottom:1px solid var(--line);padding:11px;text-align:left;vertical-align:top}.qa-table th{color:var(--muted);font-weight:500}.qa-table td{color:var(--text)}.home-category{border:1px solid var(--line);border-top:2px solid var(--gold);border-radius:5px;padding:34px;display:grid;grid-template-columns:1fr auto;gap:30px;align-items:center;background:var(--panel);margin:35px 0}.home-category h2{font-size:34px;font-weight:530;letter-spacing:-.04em;margin:10px 0}.home-category p{color:var(--muted);max-width:700px}.preview-label{border-bottom:1px solid var(--line);padding:10px 16px;font:11px var(--mono);text-align:center;color:var(--gold);background:#191c14}.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--gold);color:#171b13;padding:12px 20px;border-radius:4px;font-size:12px;max-width:calc(100% - 40px);z-index:100;box-shadow:0 8px 30px #0008}.skip{position:fixed;left:12px;top:-60px;background:var(--gold);color:var(--bg);padding:10px;z-index:100}.skip:focus{top:12px}.hidden{display:none!important}
@media(min-width:1450px){.hero h1{font-size:80px}}
@media(max-width:1120px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.hero{grid-template-columns:1fr 260px;gap:35px}.main-layout{grid-template-columns:170px minmax(0,1fr);gap:25px}.nav{gap:16px}.detail-grid{gap:28px;grid-template-columns:minmax(0,1fr) 275px}}
@media(max-width:800px){.container{width:calc(100% - 36px)}.header-inner{min-height:76px;gap:12px}.nav{display:none}.hero{grid-template-columns:1fr;padding:42px 0 32px;gap:28px}.hero h1{font-size:58px;max-width:650px}.hero .lead{font-size:16px}.hero-stats{display:flex;gap:28px;align-items:center}.stat-lines{flex:1;min-width:150px}.hero-stats>.small{display:none}.stat-total strong{font-size:51px}.stat-total{flex-direction:column;gap:4px}.main-layout{grid-template-columns:minmax(0,1fr);gap:25px;padding-top:27px}.sidebar{display:block}.sidebar h2,.sidebar-rule{display:none}.type-tabs{display:flex;gap:8px;overflow-x:auto;padding-bottom:8px}.type-tabs button{white-space:nowrap;border:1px solid var(--line);border-radius:3px;flex-shrink:0;padding:9px 12px}.type-tabs button[aria-pressed=true]{border-color:var(--gold)}.type-tabs button > span:last-child{display:none}.filters{grid-template-columns:1fr 1fr}.search-wrap{grid-column:1/-1}.detail-grid{grid-template-columns:1fr;gap:22px}.download-panel{position:static;grid-row:1}.download-panel dl{display:grid;grid-template-columns:1fr 1fr;gap:2px 12px}.download-panel dd{align-self:end}.download-panel .price{display:inline-block;margin:8px 0}.guide-grid{grid-template-columns:1fr 1fr}.guide-page h1{font-size:34px}.home-category{grid-template-columns:1fr;gap:12px;padding:24px}.home-category .btn{justify-self:start}.footer-row{align-items:flex-start}.provenance dl{grid-template-columns:100px minmax(0,1fr)}}
@media(max-width:490px){.container{width:calc(100% - 28px)}.brandword{font-size:10px;letter-spacing:.09em}.brandword small{font-size:8px}.brandmark{width:32px;height:32px;font-size:12px}.language button{font-size:10px;padding:7px}.hero h1{font-size:45px;letter-spacing:-.055em}.hero-stats{gap:22px}.cards{grid-template-columns:1fr}.card{min-height:250px;padding:22px}.card h3{font-size:21px}.card p{font-size:13px}.guide-grid{grid-template-columns:1fr}.collection-header h2{font-size:20px}.results{font-size:10px}.subnav .intro{width:100%;margin-bottom:3px}.subnav .chip{font-size:11px;padding:8px 11px}.filters select{font-size:12px}.secondary-filters select{font-size:11px;max-width:170px}.collection-header{align-items:baseline}.detail-title{font-size:37px}.detail-lead{font-size:16px}.provenance dl{grid-template-columns:1fr;gap:3px}.provenance dd{margin-bottom:10px}.footer-row{display:block}.footer-row a{display:inline-block;margin-top:14px}pre{font-size:11px}.guide-page h1{font-size:30px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.card{transition:none}.card:hover{transform:none}}
'''
(OUT/'assets'/'library.css').write_text(CSS,'utf-8')

def link(label,ja,href,**attrs):
    at=' '.join(f'{E(k.replace("_","-"))}="{E(v)}"' for k,v in attrs.items())
    return f'<a href="{E(href)}" {at}>'+ENJA(label,ja)+'</a>'

def guide_link(id,en,ja,prefix=''):
    return link(en,ja,prefix+'guides/'+id+'.html',data_guide=id)

def header(prefix=''):
    return f'''<a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="container header-inner"><a class="brand" href="https://botshelfvampire.com/" aria-label="BotShelf Vampire home"><span class="brandmark" aria-hidden="true">BV</span><span class="brandword">BOTSHELF VAMPIRE<small>OPEN TO BUILD</small></span></a><nav class="nav" aria-label="Main navigation"><a href="https://botshelfvampire.com/">{ENJA('Home','ホーム')}</a><a class="active" href="{prefix}index.html" data-home>Traders Library</a>{guide_link('licenses','Source policy','掲載とライセンス',prefix)}</nav><div class="language" aria-label="Language"><button data-set-lang="en" aria-pressed="true">EN</button><button data-set-lang="ja" aria-pressed="false">日本語</button></div></div></header>'''

def footer(prefix=''):
    return f'''<footer class="site-footer"><div class="container"><div class="footer-row"><span>BotShelf Vampire / Traders Library</span>{guide_link('licenses','Licenses & attribution','ライセンスと出典',prefix)}</div>{ENJA('Free educational source code. License checks are separate from compilation, security certification, backtests, or live trading. No profitability or suitability is promised.','無料の学習・研究用ソースコードです。ライセンス確認とコンパイル・安全性認証・バックテスト・実運用の検証は別です。収益や適合性を保証するものではありません。','p')}{ENJA('TradingView, MetaTrader, their owners, and the original authors are not represented as sponsors or partners. Code keeps its original license; BSV explanations do not replace it.','TradingView・MetaTraderや各運営元・原作者との提携を示すものではありません。コードには元のライセンスが適用され、BSVの解説が置き換えることはありません。','p')}<p data-lang="ja">学習・研究のための情報提供です。投資助言ではありません。</p></div></footer>'''

def page(title,content,prefix='',description='',extra_head=''):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{E(description or 'Free, attributed trading source code with setup notes and honest verification status.')}"><title>{E(title)} · BotShelf Vampire</title><link rel="stylesheet" href="{prefix}assets/library.css">{extra_head}<script src="{prefix}assets/catalog.js" defer></script><script src="{prefix}assets/library.js" defer></script></head><body>{header(prefix)}<main id="main">{content}</main>{footer(prefix)}<div id="toast" role="status" class="toast" hidden></div></body></html>'''

def card(d,prefix=''):
    kind=ENJA(d['kind'],KIND_JA.get(d['kind'],d['kind']))
    purpose=ENJA(d['text']['en']['purpose'],d['text']['ja']['purpose'],'p')
    status=ENJA('Source bundle','ソース同梱') if d['is_bundled'] else ENJA('Author-hosted source','原作者が配布')
    version=f'<span class="badge">{E(d["version"])}</span>' if d['is_bundled'] else ''
    if d.get('legacy'): version+='<span class="badge">'+ENJA('Legacy source','旧版ソース')+'</span>'
    research='<span class="badge risk">'+ENJA('Research only','研究用')+'</span>' if d.get('risk_level')=='Research only' else ''
    return f'''<article class="card" data-card-id="{d['id']}"><div class="card-meta"><span>{E(' / '.join(d['platforms']))}</span><button class="star" data-save="{d['id']}" aria-label="Save {E(d['name'])}" aria-pressed="false">☆</button></div><h3><a href="{prefix}{d['detail_url']}" data-item="{d['id']}">{E(d['name'])}</a></h3>{purpose}<div class="card-bottom"><div class="badges"><span class="badge">{kind}</span><span class="badge license">{E(d['license'])}</span>{version}{research}</div><div class="card-foot"><span>{status}</span><a href="{prefix}{d['detail_url']}" data-item="{d['id']}">{ENJA('Read & get code','解説とコード')} ↗</a></div></div></article>'''

INTRO_PINE={
'en':['Download the source-and-license ZIP and extract it. Keep LICENSE.txt with the source when you share a copy.','Open a TradingView chart, open Pine Editor, and create a blank script. Paste the chosen Pine source, preserving its version line. The .ps files in this collection are Pine Script examples, not PowerShell programs.','Save and use Add to chart. For Pine v3/v4 code, try the original version first; use TradingView’s official migration tools sequentially if conversion is necessary. Compilation has not been performed by BSV.','Open Inputs and Style. Reproduce a small historical example, then use replay and an isolated paper workflow to observe how the current bar changes. A plotted indicator does not automatically place orders.'],
'ja':['ソースとライセンスのZIPを取得して展開します。再配布する際はLICENSE.txtを原本と一緒に保持します。','TradingViewのチャートでPineエディタを開き、空のスクリプトへ貼り付けます。先頭のバージョン指定を残します。このライブラリの.psはPine Scriptで、PowerShell用ではありません。','保存してチャートに追加します。Pine v3/v4はまず原版のまま確認し、変換が必要なら公式の移行機能で段階的に移行します。BSVではコンパイルを実施していません。','入力とスタイルを設定し、小さな過去例を再現します。リプレイと隔離したペーパー環境で未確定バーの変化を観察します。インジケーターの表示だけで自動発注されるわけではありません。']}
INTRO_MT={
'en':['Download the source bundle and extract it. Use .mq4 in MT4 and .mq5 in MT5; these are different languages and cannot be swapped by renaming. Keep LICENSE.txt.','In the matching desktop terminal choose File → Open Data Folder. Copy this EA source under MQL4/Experts or MQL5/Experts. Preserve include/folder structure if the author’s package has it.','Open the matching MetaEditor, compile the main source, and resolve errors and missing dependencies. Check the tool-specific notes before enabling any permission. Do not enable DLL or external-web access simply to make an error disappear.','Use Strategy Tester and an isolated demo account with no other positions first. Confirm entries, exits, order filters, costs, restart behavior and failures. Reading source is not a substitute for those checks.'],
'ja':['ソース一式を取得して展開します。.mq4はMT4、.mq5はMT5用です。名前を変えるだけでは変換できません。LICENSE.txtも保持します。','対応するデスクトップ版で「ファイル→データフォルダを開く」を選び、EAをMQL4/ExpertsまたはMQL5/Expertsへ置きます。作者のパッケージに付属フォルダがある場合は階層を崩しません。','対応するMetaEditorで本体をコンパイルし、エラーと依存不足を確認します。各ツールの注意点を読み、エラーを消す目的だけでDLLや外部通信を許可しないでください。','まず他のポジションがないテスター・隔離したデモ口座で、新規注文・決済・対象の絞り込み・コスト・再起動・失敗時の処理を確認します。ソースを読むだけではこれらの実行確認の代わりになりません。']}

DETAILS={}
ZIPS={}
LICENSES={}
for d in DATA:
    for lang in ('en','ja'):
        for field in ('purpose','mechanism','settings','caution'):
            assert len(d['text'][lang][field])>=10,(d['id'],lang,field)
    if d['is_bundled']:
        # Explicit aggregation, not a relicensing of upstream code.
        license_text=(OUT/d['license_file']).read_text('utf-8')
        LICENSES[d['license_file']]=license_text
        readme=f"# {d['name']}\n\nOriginal author: {d['provider']}\nSource: {d['source_url']}\nPinned commit: {d['commit']}\nLicense: {d['license']} (see LICENSE.txt). Original source is unmodified.\n\nBSV explanatory notes follow. They do not replace the source license.\n\n"
        for lang in ('en','ja'):
            readme+='## '+('English' if lang=='en' else '日本語')+'\n\n'
            for k,t in [('purpose','Purpose / 目的'),('mechanism','Logic / 仕組み'),('settings','Settings / 設定'),('caution','Limitations / 注意点')]:readme+='### '+t+'\n'+d['text'][lang][k]+'\n\n'
            if d.get('known_issues',{}).get(lang):readme+='### Known source issues / 原本の既知の問題\n'+'\n'.join('- '+x for x in d['known_issues'][lang])+'\n\n'
            readme+='### Install / 導入\n'+'\n'.join(str(i+1)+'. '+x for i,x in enumerate((INTRO_PINE if 'TradingView' in d['platforms'] else INTRO_MT)[lang]))+'\n\n'
            if d.get('dependencies',{}).get(lang):readme+='Dependencies: '+d['dependencies'][lang]+'\n\n'
        readme+='\nVerification: source and license bytes checked; no compilation, backtest, demo or live run by BSV. No profit claim.\n'
        prov={k:v for k,v in d.items() if k not in ('text','download_bytes','download_sha256')}
        (OUT/d['provenance_url']).write_text(json.dumps(prov,indent=2,ensure_ascii=False),'utf-8')
        entries={'LICENSE.txt':(OUT/d['license_file']).read_bytes(),'README-BSV.md':readme.encode(),'PROVENANCE.json':json.dumps(prov,indent=2,ensure_ascii=False).encode()}
        for f in d['files']:entries['source/'+f['path']]=(OUT/f['local_source']).read_bytes()
        entries['SHA256SUMS.txt']=('\n'.join(HASH(v)+'  '+k for k,v in sorted(entries.items()))+'\n').encode()
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,b in sorted(entries.items()):
                zi=zipfile.ZipInfo(d['id']+'/'+name,date_time=(2026,10,1,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16
                z.writestr(zi,b)
        raw=buf.getvalue();(OUT/d['download']).write_bytes(raw)
        d['download_bytes']=len(raw);d['download_sha256']=HASH(raw)
        ZIPS[d['id']]=base64.b64encode(raw).decode()

    prefix='../'
    badges='<span class="badge">'+E(' / '.join(d['platforms']))+'</span><span class="badge license">'+E(d['license'])+'</span><span class="badge">'+ENJA(d['kind'],KIND_JA.get(d['kind'],d['kind']))+'</span>'
    if d.get('legacy'): badges+='<span class="badge">'+ENJA(d['version']+' · Legacy source',d['version']+' · 旧版ソース')+'</span>'
    blocks=''
    for key,en,ja in [('mechanism','What it does','仕組みと使い道'),('settings','Settings to understand first','最初に確認する設定'),('caution','What to watch out for','注意点と制約')]:
        blocks+=ENJA(en,ja,'h2')+ENJA(d['text']['en'][key],d['text']['ja'][key],'p')
    if d.get('known_issues'):
        blocks+=ENJA('Known issues in this exact source','この原本で確認した問題','h2')
        for lang in ('en','ja'):blocks+=f'<ul data-lang="{lang}">'+''.join('<li>'+E(x)+'</li>' for x in d['known_issues'][lang])+'</ul>'
    blocks+=ENJA('Install, inspect, then test','導入から検証まで','h2')
    instructions=INTRO_PINE if 'TradingView' in d['platforms'] else INTRO_MT
    # Indicator / utility source goes to a different terminal directory.
    if 'TradingView' not in d['platforms'] and d['kind'] in ('Indicator','Script'):
        instructions={lang:[s.replace('EA source','indicator source' if d['kind']=='Indicator' else 'script source').replace('MQL4/Experts','MQL4/'+('Indicators' if d['kind']=='Indicator' else 'Scripts')).replace('MQL5/Experts','MQL5/'+('Indicators' if d['kind']=='Indicator' else 'Scripts')).replace('EAを','インジケーターを' if d['kind']=='Indicator' else 'スクリプトを') for s in ss] for lang,ss in INTRO_MT.items()}
    if 'TradingView' not in d['platforms'] and d['kind']=='Indicator':
        instructions={lang:list(ss) for lang,ss in instructions.items()}
        instructions['en'][-1]='Use a demo chart and a small, known price sample. Compare plots, update timing, missing history and alert behavior. This indicator is not represented as an order-entry system.'
        instructions['ja'][-1]='デモのチャートで、確認しやすい少量の価格履歴を使います。描画、更新タイミング、履歴不足、通知の挙動を照合します。この指標を発注システムとは表示していません。'
    if 'TradingView' not in d['platforms'] and d['kind']=='Script':
        instructions={lang:list(ss) for lang,ss in instructions.items()}
        instructions['en'][-1]='On an isolated demo account, verify target filters before running the script. Include an order that must remain untouched; inspect actual results and partial failures afterward.'
        instructions['ja'][-1]='隔離したデモ口座で、実行前に対象の絞り込みを確認します。対象外として残す注文も用意し、実行後の結果と一部失敗を確認します。'
    if not d['is_bundled']:
        instructions={lang:list(ss) for lang,ss in instructions.items()}
        instructions['en'][0]='Open the original author repository below and read its current LICENSE and installation instructions. Get the matching source folder or repository ZIP from that author; no source package for this item is mirrored by BSV.'
        instructions['ja'][0]='下の原作者リポジトリで、現行のLICENSEと導入手順を読みます。対応するソースフォルダーまたはリポジトリZIPを原配布元から取得します。この項目のソース一式はBSVでは複製配布していません。'
    for lang in ('en','ja'):blocks+=f'<ol data-lang="{lang}">'+''.join('<li>'+E(s)+'</li>' for s in instructions[lang])+'</ol>'
    if d.get('dependencies'):blocks+=ENJA('Dependencies','必要な依存関係','h3')+ENJA(d['dependencies']['en'],d['dependencies']['ja'],'p')
    if d['is_bundled']:
        blocks+=ENJA('Source files','ソースコード','h2')
        blocks+='<div class="notice">'+ENJA('The files below are the byte-verified originals. Copy adds the full license as comments for convenience; the ZIP keeps the original files unchanged.','下のファイルは原本とのバイト一致を確認済みです。コピーボタンではライセンス全文をコメントとして付け加えます。ZIP内の原本は変更していません。','p')+'</div>'
        for i,f in enumerate(d['files']):
            text=(OUT/f['local_source']).read_bytes().decode(f.get('encoding','utf-8'))
            source_id=d['id']+'-'+str(i)
            blocks+=f'''<details class="source-block"><summary>{E(f['platform'])} · {E(f['path'])} · {f['bytes']} bytes</summary><div class="source-toolbar"><a href="{E(f['source_url'])}" target="_blank" rel="noopener noreferrer">{ENJA('Compare with upstream','原作者の版と比較')}</a><button class="btn small-btn" data-copy="{source_id}" data-license="{E(d['license_file'])}" data-provider="{E(d['provider'])}">{ENJA('Copy code + license','ライセンス付きでコピー')}</button></div><pre id="{source_id}" tabindex="0"><code>{E(text)}</code></pre><div class="source-toolbar hash">SHA256 {f['sha256']}</div></details>'''
        blocks+=f'<details class="source-block"><summary>{ENJA("Full source license","ソースのライセンス全文")} · {E(d["license"])}</summary><pre data-license-text="{E(d["license_file"])}">{E(license_text)}</pre></details>'
        blocks+=ENJA('Verification scope','確認の範囲','h2')
        blocks+='<table class="qa-table"><thead><tr><th>'+ENJA('Check','確認項目')+'</th><th>'+ENJA('Status','状態')+'</th></tr></thead><tbody>'
        for en,ja,status,jstatus in [('Source provenance and license','出典とライセンス','Pinned original and license text checked','固定版の原本とライセンス原文を確認'),('Source byte equality','原本とのバイト一致','Git blob SHA1 and SHA256 recorded','Git blob SHA1とSHA256を記録'),('Compilation','コンパイル','Not performed','未実施'),('Backtest / demo / live run','バックテスト・デモ・実運用','Not performed','未実施'),('DLL / direct web request patterns','DLL・直接Web通信のパターン','Detected' if d['scan']['dll_import'] or d['scan']['web_request'] else 'Not detected in these source files','検出' if d['scan']['dll_import'] or d['scan']['web_request'] else '掲載ファイルの該当パターンは未検出')]:blocks+='<tr><td>'+ENJA(en,ja)+'</td><td>'+ENJA(status,jstatus)+'</td></tr>'
        blocks+='</tbody></table>'+ENJA('A pattern scan is not a complete security audit. Platform libraries and broker execution are outside this check.','パターン検査は完全な安全性監査ではありません。ターミナル標準ライブラリとブローカーでの実行は確認対象外です。','p')
        main_action=f'<a class="btn primary" href="../{d["download"]}" data-download="{d["id"]}" download>{ENJA("Download source ZIP","ソースZIPを無料取得")} ↓</a>'
        file_info=f'{d["source_count"]} source file'+('s' if d['source_count']!=1 else '')+f' · {d["download_bytes"]/1024:.1f} KB'
        file_info_ja=f'{d["source_count"]}ソースファイル · {d["download_bytes"]/1024:.1f} KB'
        provenance_link=link('Machine-readable provenance','出典・ハッシュの記録','../'+d['provenance_url'],data_provenance=d['id'])
    else:
        main_action=f'<a class="btn primary" href="{E(d["source_url"])}" target="_blank" rel="noopener noreferrer">{ENJA("Get source from author","原作者のソースを開く")} ↗</a>'
        file_info='Source hosted by its original author';file_info_ja='ソースは原作者の配布元から取得'
        provenance_link=link('Original license','原作者のライセンス',d['license_url'],target='_blank',rel='noopener noreferrer')
        blocks+=ENJA('Source and license','ソースとライセンス','h2')
        blocks+='<div class="notice">'+ENJA('This is an author-hosted source listing, not a BSV mirror. The author repository is explicitly licensed Apache-2.0. BSV has checked the upstream listing and description, not every file or dependency. No runtime verification is claimed.','原作者が配布するソースの案内で、BSVでの複製配布ではありません。原作者リポジトリのApache-2.0表示と説明を確認していますが、全ファイル・依存関係の個別監査はしていません。実行検証済みとは表示しません。','p')+'</div>'
        blocks+=link('Read the author’s setup and full documentation','原作者の導入手順・全機能を読む',d.get('documentation_url',d['source_url']),target='_blank',rel='noopener noreferrer')
    evidence=f'<div class="provenance"><dl><dt>{ENJA("Original author","原作者")}</dt><dd>{E(d["provider"])}</dd><dt>{ENJA("License","ライセンス")}</dt><dd>{E(d["license"])}</dd><dt>{ENJA("Source version","取得対象の版")}</dt><dd><code>{E(d.get("commit") or "Author default branch; may change")}</code></dd><dt>{ENJA("Checked","確認日")}</dt><dd>{DATE}</dd><dt>{ENJA("Evidence","出典")}</dt><dd>{provenance_link}</dd></dl></div>'
    if d.get('credit_note'): blocks+='<div class="notice small">'+E(d['credit_note'])+'</div>'
    blocks+=evidence
    danger='<div class="notice danger">'+ENJA('Research source, not a live-ready EA. Read all known issues before any demo test.','研究用の原本です。実運用向けのEAではありません。デモ検証の前に既知の問題を確認してください。','p')+'</div>' if d['kind']=='Expert Advisor' else ''
    status=ENJA('Source + license included','ソース・ライセンス同梱') if d['is_bundled'] else ENJA('Author-hosted source','原作者がソースを配布')
    panel=f'''<aside class="download-panel"><h2>{status}</h2><div class="price">{ENJA('Free','無料')}</div>{main_action}<p class="small">{ENJA(file_info,file_info_ja)}</p><a class="btn" href="{E(d['source_url'])}" target="_blank" rel="noopener noreferrer">{ENJA('Original project','原作者のプロジェクト')} ↗</a><dl><dt>{ENJA('Platform','対応環境')}</dt><dd>{E(' / '.join(d['platforms']))}</dd><dt>{ENJA('License','ライセンス')}</dt><dd>{E(d['license'])}</dd><dt>{ENJA('Runtime status','実行検証')}</dt><dd>{ENJA('Not tested by BSV','BSVでは未実施')}</dd><dt>{ENJA('Source owner','原作者')}</dt><dd>{E(d['provider'])}</dd></dl><p class="small">{ENJA('No email or account is required for the BSV source downloads. Platform accounts or desktop tools may be needed to run the code.','BSVのソース取得に会員登録やメール登録は不要です。コードの利用には各プラットフォームのアカウントやデスクトップ環境が必要な場合があります。')}</p></aside>'''
    content=f'''<div class="container detail"><div class="breadcrumb"><a href="../index.html" data-home>← Traders Library</a> / {E(d['name'])}</div><div class="detail-grid"><article class="prose"><div class="badges">{badges}</div><h1 class="detail-title">{E(d['name'])}</h1>{ENJA(d['text']['en']['purpose'],d['text']['ja']['purpose'],'p','detail-lead')}{danger}{blocks}</article>{panel}</div></div>'''
    DETAILS[d['id']]=content
    (OUT/d['detail_url']).write_text(page(d['name'],content,'../',d['text']['en']['purpose']),encoding='utf-8')

# Guides are original editorial material; original legal/technical references remain linked.
GUIDES={}
def guide(id,en,ja,sections):
    text=f'<div class="container guide-page prose"><div class="breadcrumb"><a href="../index.html" data-home>← Traders Library</a></div><div class="eyebrow">FIELD GUIDE / {len(GUIDES)+1:02d}</div>'+ENJA(en,ja,'h1')
    for h1,h2,ps_en,ps_ja in sections:
        text+=ENJA(h1,h2,'h2')
        for a,b in zip(ps_en,ps_ja):text+=ENJA(a,b,'p')
    text+='</div>'
    GUIDES[id]={'en':en,'ja':ja,'html':text}
    (OUT/'guides'/f'{id}.html').write_text(page(en,text,'../'),encoding='utf-8')

guide('pine','Install Pine source without losing its license','Pineソースの導入とライセンスの保持',[
('A source file is not a TradingView publication','ソースの導入と公開投稿は別です',
['The source ZIP contains original code, its license and attribution, BSV notes, and provenance. A private working copy in Pine Editor does not make you its original author. Do not publish another author’s work as your own.','The .ps files in the James Bachini collection contain Pine Script. They are not PowerShell commands. Inspect them as text, then paste their contents into Pine Editor.'],
['ZIPには原本・ライセンス・作者表示・BSV解説・出典記録を同梱しています。Pineエディタの作業コピーを作っても、原著作者が自分になるわけではありません。他人の作品を自作として公開しないでください。','James Bachiniの.psファイルの内容はPine Scriptで、PowerShellのコマンドではありません。テキストとして確認し、Pineエディタへ貼り付けます。']),
('Install and compare one change at a time','一つずつ導入・比較します',INTRO_PINE['en'],INTRO_PINE['ja']),
('Respect the original version','元のバージョンを保持します',
['A version annotation is part of the source, not a compatibility badge added by BSV. Older v3/v4 examples are clearly marked as legacy. Converting the annotation alone is not a migration.','After any conversion, compare plots, alert timing and strategy trade lists against the original on the same feed and timeframe. Keep a dated change note and the original notices. Conversion has not been performed or certified here.'],
['バージョン指定はソースの一部で、BSVが互換性を保証する表示ではありません。v3/v4は旧版として明記します。数字の書き換えだけで移行できるわけではありません。','変換後は同じ配信元・時間足で、線・アラート時刻・取引一覧を原版と比較します。変更日と内容、原作者表示を保持します。このライブラリでは変換や互換性の認証は行っていません。']),
('Public reposting has additional rules','公開再投稿には追加のルールがあります',
['TradingView’s script-publication and reuse rules apply when you publish there, independently of the source license. A BSV download is not a blanket permission to rebrand, resell access or republish it in any format.','Primary references: TradingView Pine Script documentation: Writing scripts → Publishing scripts and Release notes → Migration guides; TradingView Script publishing rules.'],
['TradingViewへ公開する場合は、ソースのライセンスとは別に公開・再利用ルールが適用されます。BSVから取得したことは、あらゆる形式での自作化・アクセス権販売・再投稿の包括許可ではありません。','一次資料：TradingView Pine ScriptドキュメントのPublishing scripts・Migration guides、およびScript publishing rules。'])])

guide('metatrader','Install MT4 and MT5 source in the right place','MT4・MT5ソースの正しい導入',[
('Choose the platform before copying files','コピーする前に対応環境を確認',
['.mq4 targets MT4; .mq5 targets MT5. A source-language file is different from .ex4/.ex5 compiled output. Renaming a file does not port its code.','Use the terminal’s File → Open Data Folder. Indicators belong in MQL4/Indicators or MQL5/Indicators; EAs and trade managers in Experts; one-shot scripts in Scripts. Keep matching Include, Files and resource folders in the author’s intended structure.'],
['.mq4はMT4、.mq5はMT5向けです。ソースファイルと実行形式の.ex4/.ex5は別で、ファイル名変更だけでは移植できません。','ターミナルの「ファイル→データフォルダを開く」を使います。インジケーターはMQL4/IndicatorsまたはMQL5/Indicators、EA・取引管理はExperts、単発スクリプトはScriptsへ。Include・Filesなどの階層も原作者の指定を維持します。']),
('Compile before enabling anything','有効化の前にコンパイルします',
['Use the matching MetaEditor and compile the main .mq4/.mq5 file. A missing .mqh dependency must be located in the documented package or the platform’s standard library. Do not substitute a binary from an unrelated site.','Check all compiler errors and warnings. A successful compile still does not prove that price units, volume steps, symbol selection, account mode, stop distance or order result handling are correct.'],
['対応するMetaEditorで本体の.mq4/.mq5をコンパイルします。不足する.mqhは作者の配布物かターミナル標準ライブラリで確認し、無関係なサイトの実行ファイルで代用しないでください。','エラーと警告を確認します。コンパイル成功だけでは、価格単位・ロット刻み・対象銘柄・口座方式・ストップ距離・注文結果の処理が正しいことの証明にはなりません。']),
('Keep permission and trade scope narrow','権限と操作対象を確認',
['An indicator normally calculates or displays values; an EA can open, modify or close positions. Trade managers can affect existing trades even when they do not generate entries. Check the exact source rather than trusting its name.','Do not enable DLL imports or add WebRequest destinations without understanding the code and the documented need. Check symbol and magic-number filters, and test with no unrelated positions in the account.'],
['インジケーターは通常計算・表示を行いますが、EAは新規注文・変更・決済を行えます。取引管理EAは新規シグナルがなくても既存の注文へ作用します。名前だけでなく実際のソースを確認します。','コードと必要性を理解しないままDLLやWebRequestの接続先を許可しないでください。銘柄とマジックナンバーの絞り込みを確認し、無関係なポジションがない環境で試します。']),
('Test failures, not only profitable history','良い過去成績だけでなく失敗時を確認',
['In Strategy Tester and a demo terminal, inspect insufficient history, disconnections, rejected orders, spread changes, restart behavior and accidental duplicate instances. A source library is not an installation or live-performance certification.'],
['テスターとデモ端末で、履歴不足・切断・注文拒否・スプレッド変化・再起動・二重起動も確認します。ソースライブラリは、インストールや実運用の認証ではありません。'])])

guide('testing','A repeatable test beats a perfect screenshot','きれいな画像より再現できる検証',[
('Record the exact experiment','検証条件を固定します',
['Keep source commit and SHA256, terminal/Pine version, instrument, feed, timeframe, timezone, dates, settings and all enabled permissions. Note whether source was modified. Record commission, spread, slippage and execution assumptions before viewing results.'],
['ソースのコミットとSHA256、環境の版、銘柄、配信元、時間足、時間帯、期間、設定、権限を記録します。改変の有無も残し、結果を見る前に手数料・スプレッド・スリッページ・約定条件を固定します。']),
('Separate fit from evidence','調整した期間と評価する期間を分けます',
['Use one interval to develop the rule and untouched intervals to evaluate it. Changing parameters after seeing the test interval turns it into another development sample. Include quiet, trending and volatile periods instead of selecting only the favorable chart.'],
['開発に使う期間と、まだ見ていない評価用の期間を分けます。評価期間を見てから調整すると、その期間も開発用になります。良い場面だけでなく、閑散・トレンド・高変動を含めて比較します。']),
('Inspect what was actually known at the time','その時点で知り得た値を確認',
['Compare historical plots with bar replay and live updates. Check higher-timeframe requests, pivots that need later bars, negative plot offsets, rolling curve redraws and alerts before bar confirmation. A later-stabilized plot is not necessarily a signal available in real time.','Use standard OHLC prices for execution assumptions. Synthetic candle values, including Heikin Ashi values, are not automatically executable market prices.'],
['過去の表示をバーリプレイとリアルタイム更新で比較します。上位足の取得、後続バーを要するピボット、負の表示シフト、過去曲線の描き直し、足確定前のアラートを確認します。後から整った線が、その場で利用可能なシグナルとは限りません。','約定条件には通常のOHLCを使って確認します。平均足などの合成価格がそのまま市場で約定する価格とは限りません。']),
('Check the full trade lifecycle','注文から終了まで確認',
['For EAs, inspect order acceptance, rejection, stop placement, close failures, repeated signals and restart recovery. Compare requested trades with filled trades, not just the equity curve. Never let a demo pass silently become a live authorization.','BSV currently records source and license checks, not a passed compiler, backtest, demo, or live trading result. Verification labels should change only when reproducible evidence is attached to that exact code version.'],
['EAでは注文受付・拒否・ストップ設置・決済失敗・連続シグナル・再起動復元まで確認します。損益曲線だけでなく、要求した注文と実際の約定を比較します。デモ合格を自動的な実口座運用の許可にしないでください。','現在のBSV表示はソースとライセンスの確認で、コンパイル・バックテスト・デモ・実運用の合格表示ではありません。検証ラベルは、そのコードの版に紐付いた再現可能な証拠が揃ったときだけ更新します。'])])

guide('licenses','Open source, with the original rights intact','原作者の権利を保持したオープンソース',[
('How source bundles are admitted','ソース同梱の掲載基準',
['BSV uses an identifiable author repository, an explicit distribution license, preserved copyright and applicable notices, a fixed version, and checksums. Source bundles exclude unlicensed reposts, leaked paid products, decompiled code, noncommercial-only material and unresolved contradictory restrictions.','Author-hosted listings are separate: the source remains at the original repository. They are not counted as BSV-mirrored files, full dependency audits or tested products. A free price alone is never a license grant.'],
['作者を特定できる配布元、明示された再配布ライセンス、著作権・必要な通知の保持、固定版、ハッシュを確認します。無許諾転載・有料品の流出・逆コンパイル物・非商用限定・矛盾した権利表示が未解決のものは同梱しません。','原作者配布の案内は区別し、BSVが複製したファイル数・依存関係の全体監査・動作検証済み製品として数えません。価格が無料というだけでは、再配布の許可にはなりません。']),
('MIT and Apache-2.0','MITとApache-2.0',
['For MIT code, keep the original copyright and permission notice with copies or substantial portions. The included full license controls; BSV does not claim authorship of the original code.','For Apache-2.0 code, provide the license, retain applicable source notices and NOTICE material, and mark files you modify. Patent and trademark provisions also matter. An Apache license does not by itself authorize endorsement claims or reuse of a logo.'],
['MITでは、複製物または主要な部分に元の著作権表示と許諾表示を保持します。同梱したライセンス全文が適用され、原本の著作者をBSVへ変更しません。','Apache-2.0ではライセンスの提供、適用される権利表示・NOTICEの保持、変更ファイルへの変更表示が必要です。特許や商標の条項もあります。提携をうたうことやロゴ利用まで自動的に許可されるわけではありません。']),
('GPL source stays GPL','GPLのソースはGPLのまま',
['The GPL-3.0 source bundles retain their original notices and complete license. Redistribution of modified or compiled derivatives has additional requirements; do not label the whole downloaded work MIT or remove its source obligations.','Separate programs can be distributed together as an aggregate without pretending their licenses become one license. Combining code into a derivative is a different question and requires a compatibility review.'],
['GPL-3.0の同梱ソースには元の表示とライセンス全文を保持します。改変物・実行形式の再配布には追加の条件があります。取得した作品全体をMITへ貼り替えたり、ソース提供義務を消したりしないでください。','独立したプログラムをまとめて配布する場合も、それぞれのライセンスを区別します。コードを組み合わせて派生物にする場合は別途、互換性の確認が必要です。']),
('Scope, corrections and platform rules','確認の範囲・訂正・プラットフォーム規則',
['This is a documented license-compliance process, not a guarantee that every possible legal claim has been resolved. Rights questions, third-party dependencies and platform publication terms must be evaluated for the actual use. BSV does not distribute a license to use platform names as an endorsement.','For an attribution or rights concern, contact support@botshelfvampire.com with the item URL, affected file, claimed rights and supporting evidence. Questionable items should be reviewed and withheld from distribution while unresolved.'],
['これは記録に基づくライセンス対応であり、あらゆる法的問題が解消したことの保証ではありません。権利関係・第三者依存・各プラットフォームの公開規則は実際の用途に応じて確認します。','作者表示・権利に関する連絡は、項目URL・対象ファイル・権利の内容・根拠とともにsupport@botshelfvampire.comへ。疑義のあるものは確認し、未解決の間は配布対象から外す方針です。'])])

guide('choose','Choose the tool that matches the job','目的に合うツールを選ぶ',[
('Indicators explain a measurement','インジケーターは何を測るかで選びます',
['Moving averages and filters summarize price; oscillators describe relative momentum; bands describe a calculation of dispersion or range. Two tools with similar names may implement different formulas. Read What it does and the exact source before stacking them.'],
['移動平均やフィルターは価格の要約、オシレーターは相対的な勢い、バンドは散らばりや値幅の計算を示します。似た名称でも式が異なるため、重ねる前に「仕組み」と原本を確認します。']),
('Strategies simulate rules','ストラテジーはルールの検証用',
['A Pine strategy models entries and exits in TradingView’s broker emulator. Its existence does not provide a connection to your live broker or demonstrate that its hypothetical fills are achievable. Read the entry, exit and cost assumptions separately.'],
['PineストラテジーはTradingViewのブローカーエミュレーター上で売買条件を検証します。ソースがあるだけで実口座へ接続されたり、仮想の約定が実現できると証明されたりはしません。新規・決済・コスト条件を分けて確認します。']),
('EAs and trade managers can act','EA・取引管理は実際の操作があり得ます',
['Entry EAs can open positions; a trade manager may only move stops or close existing positions. Both can cause financial loss. Always check the exact scope of symbol, ticket and magic-number filters and any terminal-wide actions.','Start with a source whose logic and dependencies you can explain. Favor a small reproducible demo experiment over the largest number of settings. The library’s ordering is editorial, not a ranking of returns.'],
['売買EAは新規注文を行い、取引管理はストップ変更や既存ポジションの決済だけを行う場合があります。どちらも損失につながり得ます。銘柄・チケット・マジックナンバーの絞り込みと、ターミナル全体へ及ぶ操作を確認します。','仕組みと依存を説明できる原本から始めます。設定の多さより、再現できる小さなデモ検証を優先する構成です。掲載順は編集上の順序で、収益ランキングではありません。'])])
# Primary documentation links are an explicit appendix, not copied screenshots or prose.
REFS={
'pine':[('Publishing scripts','https://www.tradingview.com/pine-script-docs/writing/publishing/'),('Migration guides','https://www.tradingview.com/pine-script-docs/migration-guides/overview/'),('Script publishing rules','https://www.tradingview.com/support/solutions/43000590599-script-publishing-rules/')],
'metatrader':[('MQL4 reference','https://docs.mql4.com/'),('MQL5 reference','https://www.mql5.com/en/docs'),('MetaEditor help','https://www.metatrader5.com/en/metaeditor/help')],
'licenses':[('MIT license','https://opensource.org/license/mit'),('Apache License 2.0','https://www.apache.org/licenses/LICENSE-2.0'),('GNU GPL version 3','https://www.gnu.org/licenses/gpl-3.0.html'),('TradingView reuse rules','https://www.tradingview.com/support/solutions/43000590599-script-publishing-rules/')],
 'testing':[('TradingView strategies','https://www.tradingview.com/pine-script-docs/concepts/strategies/'),('TradingView repainting','https://www.tradingview.com/pine-script-docs/concepts/repainting/'),('MQL5 testing','https://www.metatrader5.com/en/terminal/help/algotrading/testing')],
 'choose':[('TradingView script types','https://www.tradingview.com/pine-script-docs/language/script-structure/'),('MQL5 program types','https://www.mql5.com/en/docs/basis/program')]
}
for id,g in GUIDES.items():
    appendix=ENJA('Primary references','一次資料','h2')+'<ul>'+''.join('<li><a target="_blank" rel="noopener noreferrer" href="'+E(url)+'">'+E(name)+'</a></li>' for name,url in REFS[id])+'</ul>'
    g['html']=g['html'].rsplit('</div>',1)[0]+appendix+'</div>'
    (OUT/'guides'/f'{id}.html').write_text(page(g['en'],g['html'],'../'),'utf-8')

stats=f'''<aside class="hero-stats"><div class="stat-total"><strong>{COUNTS['items']}</strong>{ENJA('free resources','無料リソース')}</div><div class="stat-lines"><div>{ENJA('Source bundles','ソース同梱')}<b>{COUNTS['bundled']}</b></div><div>{ENJA('Author-hosted sources','原作者が配布')}<b>{COUNTS['author_hosted']}</b></div><div>{ENJA('Runtime-tested by BSV','BSVでの実行検証済み')}<b>0</b></div></div><p class="small">{ENJA('Original authors. Explicit licenses. No invented performance.','原作者を明示。ライセンスを保持。架空の運用実績は載せません。')}</p></aside>'''
hero=f'''<section class="container hero"><div><div class="eyebrow">FREE SOURCE CODE / TRADINGVIEW · MT4 · MT5</div><h1>Traders <em>Library.</em></h1>{ENJA('Understand the logic. Inspect the source. Build your own research.','仕組みを知る。コードを読む。自分で検証する。','p','lead')}{ENJA('Indicators, strategies and trading tools, with practical setup notes and their original licenses.','インジケーター・ストラテジー・自動売買ツールを、用途と導入手順、元のライセンスとともに。','p','lead')}{ENJA('No email gate. No paywall. Source access is free.','メール登録不要。課金不要。ソースへ無料でアクセス。','p','small')}</div>{stats}</section>'''
quick=f'''<div class="container subnav"><span class="intro">{ENJA('Not sure where to start?','初めて利用する方へ')}</span>{link('Choose a tool','目的から選ぶ','guides/choose.html',class_='chip',data_guide='choose')}{link('Install Pine','Pineの導入','guides/pine.html',class_='chip',data_guide='pine')}{link('Install MT4 / MT5','MT4・MT5の導入','guides/metatrader.html',class_='chip',data_guide='metatrader')}{link('Test the idea','検証の進め方','guides/testing.html',class_='chip',data_guide='testing')}</div>'''
# class_ is mapped explicitly because generic HTML attribute conversion preserves hyphens.
quick=quick.replace('class-="','class="')
types=[('', 'All resources','すべて')]+[(k,k,KIND_JA[k]) for k in ['Indicator','Strategy','Expert Advisor','Trade manager','Script','Template'] if k in COUNTS['kinds']]
tabs=''.join(f'<button data-kind="{E(k)}" aria-pressed="{str(not k).lower()}"><span>{ENJA(en,ja)}</span><span>{COUNTS["kinds"].get(k,COUNTS["items"])}</span></button>' for k,en,ja in types)
category_options=''.join(f'<option value="{E(c)}" data-en="{E(c)}" data-ja="{E(CATEGORY_JA.get(c,c))}">{E(c)}</option>' for c in sorted({d['category'] for d in DATA}))
license_options=''.join('<option>'+E(l)+'</option>' for l in sorted({d['license'] for d in DATA}))
collection=f'''<div class="container main-layout" id="collection"><aside class="sidebar"><h2>{ENJA('Browse by type','種類で探す')}</h2><div class="type-tabs">{tabs}</div><div class="sidebar-rule"><h2>{ENJA('Before you run it','実行する前に')}</h2>{ENJA('A license check is not a trading test. Every item states what is known and what is not.','ライセンス確認は売買検証ではありません。各項目に確認済み・未確認の範囲を明記しています。','p')}{guide_link('licenses','Read our source policy','掲載基準を読む')}</div></aside><section aria-label="Source catalogue"><div class="collection-header"><h2>{ENJA('Find your next experiment.','次に試すコードを探す。')}</h2><span class="results" id="result-count" aria-live="polite">{COUNTS['items']} resources</span></div><div class="filters"><label class="search-wrap"><span aria-hidden="true">⌕</span><input id="search" type="search" placeholder="Search tools, logic, authors…" aria-label="Search library" autocomplete="off"></label><select id="platform" aria-label="Platform"><option value="" data-en="All platforms" data-ja="すべての環境">All platforms</option><option>TradingView</option><option>MT4</option><option>MT5</option></select><select id="category" aria-label="Use case"><option value="" data-en="All use cases" data-ja="すべての用途">All use cases</option>{category_options}</select></div><div class="secondary-filters"><div class="filter-left"><select id="license" aria-label="License"><option value="" data-en="All licenses" data-ja="すべてのライセンス">All licenses</option>{license_options}</select><select id="distribution" aria-label="Source location"><option value="" data-en="All source locations" data-ja="すべての配布元">All source locations</option><option value="bundled" data-en="BSV source bundles" data-ja="BSVのソース同梱">BSV source bundles</option><option value="author-hosted" data-en="Author-hosted sources" data-ja="原作者が配布">Author-hosted sources</option></select><button class="chip" id="saved-only" aria-pressed="false">☆ {ENJA('Saved','保存済み')}</button></div><button class="text-button" id="clear-filters">{ENJA('Reset filters','絞り込み解除')}</button></div><noscript><p class="no-js">JavaScript is off: the full catalogue and source detail pages remain readable. Search, language switching and saved items require JavaScript.</p></noscript><div class="cards" id="cards">{''.join(card(d) for d in DATA)}</div><div class="empty" id="empty" hidden>{ENJA('No exact matches.','一致する項目がありません。','h3')}{ENJA('Try a different keyword or reset the filters.','別のキーワードを試すか、絞り込みを解除してください。','p')}<button class="btn" data-reset>{ENJA('Show all resources','すべて表示')}</button></div></section></div>'''
guide_strip='<section class="container guides-strip">'+ENJA('Keep the source. Learn the method.','コードだけでなく、使い方も。','h2')+'<div class="guide-grid">'+''.join(f'<a class="guide-card" href="guides/{id}.html" data-guide="{id}"><small>GUIDE {n+1:02d}</small>'+ENJA(g['en'],g['ja'],'h3')+'</a>' for n,(id,g) in enumerate(GUIDES.items()))+'</div></section>'
index_content='<div id="library-view">'+hero+quick+collection+guide_strip+'</div><div id="detail-view" hidden></div>'
(OUT/'index.html').write_text(page('Traders Library — Free Trading Source Code',index_content,description='Free Pine Script indicators and strategies, MT4/MT5 EA source, explicit licenses, setup guides and source provenance.'),'utf-8')

# Safe source policy in machine-readable form; upstream code is never relicensed.
policy={'name':'Traders Library','date':DATE,'fee':0,'currency':None,'requires_email':False,'counts':COUNTS,'counting':'One distinct program per item; platform variants and translations are not extra items. Author-hosted links are separate from BSV source bundles.','license_policy':'Preserve original source licenses, notices, pinned provenance and checksums. No unlicensed, leaked, decompiled, noncommercial-only or contradictory source bundles.','runtime_verification':'No compiler, backtest, demo or live execution by BSV.','known_limitations':'Keyword scans are not complete security audits; source licenses are not legal guarantees; author-hosted listing content may change.'}
(OUT/'catalog.json').write_text(json.dumps(DATA,indent=2,ensure_ascii=False),'utf-8')
(OUT/'source-policy.json').write_text(json.dumps(policy,indent=2,ensure_ascii=False),'utf-8')
(OUT/'assets'/'catalog.js').write_text('window.BSV_DATA='+J(DATA)+';\nwindow.BSV_COUNTS='+J(COUNTS)+';\nwindow.BSV_LICENSES='+J(LICENSES)+';\n','utf-8')

JS=r'''
(()=>{'use strict';
const DATA=window.BSV_DATA||[];const byId=new Map(DATA.map(x=>[x.id,x]));
const $=s=>document.querySelector(s);const $$=s=>Array.from(document.querySelectorAll(s));
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const readStore=k=>{try{return localStorage.getItem(k)}catch{return null}};const writeStore=(k,v)=>{try{localStorage.setItem(k,v);return true}catch{return false}};
let lang='en';let saved=new Set();let kind='';let savedOnly=false;let toastTimer;
try{const v=JSON.parse(readStore('bsv-traders-saved')||'[]');if(Array.isArray(v)) saved=new Set(v.filter(id=>byId.has(id)))}catch{}
const tr=(en,ja)=>lang==='ja'?ja:en;
const both=(en,ja,tag='span')=>`<${tag} data-lang="en">${esc(en)}</${tag}><${tag} data-lang="ja">${esc(ja)}</${tag}>`;
const KJA={'Indicator':'インジケーター','Strategy':'ストラテジー','Expert Advisor':'自動売買EA','Trade manager':'取引管理EA','Script':'スクリプト','Template':'開発ひな形'};
function toast(s){const t=$('#toast');if(!t)return;t.textContent=s;t.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.hidden=true,4000)}
function setLanguage(next){lang=next==='ja'?'ja':'en';document.documentElement.lang=lang;writeStore('bsv-traders-lang',lang);$$('[data-set-lang]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.setLang===lang)));$$('option[data-en]').forEach(o=>o.textContent=o.dataset[lang]);if($('#search')){$('#search').placeholder=tr('Search tools, logic, authors…','名称・仕組み・作者で検索…');$('#search').setAttribute('aria-label',tr('Search library','ライブラリを検索'))}updateSavedButtons();filter();}
function card(d){const risk=d.risk_level==='Research only'?`<span class="badge risk">${both('Research only','研究用')}</span>`:'';return `<article class="card" data-card-id="${d.id}"><div class="card-meta"><span>${esc(d.platforms.join(' / '))}</span><button class="star" data-save="${d.id}" aria-label="${esc(tr('Save ','保存：')+d.name)}" aria-pressed="${saved.has(d.id)}">${saved.has(d.id)?'★':'☆'}</button></div><h3><a href="${esc(d.detail_url)}" data-item="${d.id}">${esc(d.name)}</a></h3>${both(d.text.en.purpose,d.text.ja.purpose,'p')}<div class="card-bottom"><div class="badges"><span class="badge">${both(d.kind,KJA[d.kind]||d.kind)}</span><span class="badge license">${esc(d.license)}</span>${d.is_bundled?`<span class="badge">${esc(d.version)}</span>`:''}${d.legacy?`<span class="badge">${both('Legacy source','旧版ソース')}</span>`:''}${risk}</div><div class="card-foot"><span>${d.is_bundled?both('Source bundle','ソース同梱'):both('Author-hosted source','原作者が配布')}</span><a href="${esc(d.detail_url)}" data-item="${d.id}">${both('Read & get code','解説とコード')} ↗</a></div></div></article>`}
function updateSavedButtons(){$$('[data-save]').forEach(b=>{const yes=saved.has(b.dataset.save);b.setAttribute('aria-pressed',String(yes));b.textContent=yes?'★':'☆';b.setAttribute('aria-label',tr(yes?'Unsave ':'Save ',yes?'保存を解除：':'保存：')+(byId.get(b.dataset.save)?.name||''))});if($('#saved-only'))$('#saved-only').setAttribute('aria-pressed',String(savedOnly))}
function normalize(s){return String(s).normalize('NFKC').toLocaleLowerCase()}
function filter(){const el=$('#cards');if(!el)return;const q=normalize($('#search').value.trim()).split(/\s+/).filter(Boolean),platform=$('#platform').value,category=$('#category').value,license=$('#license').value,dist=$('#distribution').value;const rows=DATA.filter(d=>{if(kind&&d.kind!==kind||platform&&!d.platforms.includes(platform)||category&&d.category!==category||license&&d.license!==license||dist&&d.distribution!==dist||savedOnly&&!saved.has(d.id))return false;const hay=normalize([d.name,d.provider,d.kind,KJA[d.kind],d.category,d.platforms.join(' '),d.license,d.text.en.purpose,d.text.ja.purpose,d.text.en.mechanism,d.text.ja.mechanism].join(' '));return q.every(w=>hay.includes(w))});el.innerHTML=rows.map(card).join('');$('#empty').hidden=rows.length!==0;$('#result-count').textContent=tr(`${rows.length} / ${DATA.length} resources`,`${rows.length} / ${DATA.length} 件`);$$('[data-kind]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.kind===kind)));updateSavedButtons();}
function reset(){kind='';savedOnly=false;['search','platform','category','license','distribution'].forEach(id=>{if($('#'+id))$('#'+id).value=''});filter()}
function showInline(){if(!window.BSV_STANDALONE)return;const lib=$('#library-view'),view=$('#detail-view');let key='';try{key=decodeURIComponent(location.hash.slice(1))}catch{}let content;if(key.startsWith('item/'))content=window.BSV_DETAILS?.[key.slice(5)];else if(key.startsWith('guide/'))content=window.BSV_GUIDES?.[key.slice(6)]?.html;if(content){view.innerHTML=content;view.hidden=false;lib.hidden=true;document.title=(key.startsWith('item/')?(byId.get(key.slice(5))?.name||'Source'):'Guide')+' · Traders Library';}else{view.innerHTML='';view.hidden=true;lib.hidden=false;document.title='Traders Library · BotShelf Vampire'}updateSavedButtons();window.scrollTo(0,0)}
function downloadBytes(bytes,name,type){const url=URL.createObjectURL(new Blob([bytes],{type}));const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000)}
async function copySource(button){const pre=document.getElementById(button.dataset.copy);if(!pre)return;const lic=window.BSV_LICENSES?.[button.dataset.license];if(!lic){toast(tr('License text unavailable. Use the source ZIP.','ライセンス原文を取得できません。ソースZIPを利用してください。'));return;}const notice=`// Source license: ${button.dataset.license}\n// Original author: ${button.dataset.provider}\n// BSV copy helper: license comments added; source logic unchanged.\n`+lic.split('\n').map(s=>'// '+s).join('\n')+'\n\n';const original=pre.textContent;let text;if(original.startsWith('//@version=')){const pos=original.indexOf('\n');text=original.slice(0,pos+1)+notice+original.slice(pos+1)}else{text=notice+original}let ok=false;try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text);ok=true}}catch{}if(!ok){const t=document.createElement('textarea');t.value=text;t.style.position='fixed';t.style.opacity='0';document.body.append(t);t.select();try{ok=document.execCommand('copy')}catch{}t.remove();button.focus()}toast(ok?tr('Source and license copied.','ソースとライセンスをコピーしました。'):tr('Clipboard unavailable. Use the source ZIP or select the text.','コピーを利用できません。ZIP取得またはテキスト選択を利用してください。'));}
document.addEventListener('click',e=>{const b=e.target.closest('button,a');if(!b)return;if(b.dataset.setLang){setLanguage(b.dataset.setLang);return}if(b.hasAttribute('data-kind')){kind=b.dataset.kind;filter();return}if(b.dataset.save){const id=b.dataset.save;if(!byId.has(id))return;saved.has(id)?saved.delete(id):saved.add(id);const persisted=writeStore('bsv-traders-saved',JSON.stringify([...saved]));updateSavedButtons();if(savedOnly)filter();if(!persisted)toast(tr('Saved for this session only; browser storage is unavailable.','ブラウザー保存が利用できないため、この画面の間だけ保持します。'));return}if(b.id==='saved-only'){savedOnly=!savedOnly;filter();return}if(b.id==='clear-filters'||b.hasAttribute('data-reset')){reset();return}if(b.dataset.copy){copySource(b);return}if(window.BSV_STANDALONE){if(b.dataset.item||b.dataset.guide||b.hasAttribute('data-home')){e.preventDefault();location.hash=b.dataset.item?'item/'+b.dataset.item:b.dataset.guide?'guide/'+b.dataset.guide:'';showInline();return}if(b.dataset.download&&window.BSV_ZIPS?.[b.dataset.download]){e.preventDefault();const raw=atob(window.BSV_ZIPS[b.dataset.download]);downloadBytes(Uint8Array.from(raw,c=>c.charCodeAt(0)),b.dataset.download+'.zip','application/zip');return}if(b.dataset.provenance){e.preventDefault();const d=byId.get(b.dataset.provenance);if(d)downloadBytes(JSON.stringify(d,null,2),d.id+'-provenance.json','application/json');return}}});
['search','platform','category','license','distribution'].forEach(id=>{const el=$('#'+id);if(el)el.addEventListener(id==='search'?'input':'change',filter)});
let param;try{param=new URL(location.href).searchParams.get('lang')}catch{}setLanguage(param||readStore('bsv-traders-lang')||'en');window.addEventListener('hashchange',showInline);showInline();
})();
'''
(OUT/'assets'/'library.js').write_text(JS,'utf-8')

# A single self-contained review page includes actual packages, not mock buttons.
standalone=(OUT/'index.html').read_text('utf-8').replace('<link rel="stylesheet" href="assets/library.css">','<style>'+CSS+'</style>').replace('<script src="assets/catalog.js" defer></script>','').replace('<script src="assets/library.js" defer></script>','')
payload='window.BSV_STANDALONE=true;window.BSV_DATA='+J(DATA)+';window.BSV_COUNTS='+J(COUNTS)+';window.BSV_LICENSES='+J(LICENSES)+';window.BSV_DETAILS='+J(DETAILS)+';window.BSV_GUIDES='+J(GUIDES)+';window.BSV_ZIPS='+J(ZIPS)+';'
standalone=standalone.replace('<body>','<body><div class="preview-label">'+ENJA('SELF-CONTAINED REVIEW BUILD · Not proof of deployment to the BSV website','単体で動くレビュー版 · BSV本番サイトへの反映を示すものではありません')+'</div>')
standalone=standalone.replace('</body>','<script>'+payload+'</script><script>'+JS+'</script></body>')
(BASE/'Traders-Library-Preview.html').write_text(standalone,'utf-8')

HOME_CSS="""
.bsv-traders{box-sizing:border-box;background:#151a17;color:#f2f1e9;border:1px solid #313930;border-top:2px solid #dfc583;border-radius:5px;padding:32px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:28px;align-items:center;margin:32px 0;font:15px/1.6 system-ui,sans-serif}.bsv-traders *{box-sizing:border-box}.bsv-traders .bsv-traders-kicker{font:11px ui-monospace,monospace;letter-spacing:.1em;color:#dfc583}.bsv-traders h2{font:550 clamp(30px,4vw,44px)/1.15 system-ui,sans-serif;letter-spacing:-.04em;margin:12px 0 16px}.bsv-traders p{margin:0 0 15px;max-width:680px;color:#bfc8bc}.bsv-traders .bsv-traders-tags{display:flex;gap:8px;flex-wrap:wrap}.bsv-traders .bsv-traders-tags span{border:1px solid #394234;border-radius:3px;padding:4px 8px;color:#dfc583;font-size:11px}.bsv-traders a.bsv-traders-link{color:#151a17;background:#dfc583;text-decoration:none;font-weight:600;font-size:13px;padding:13px 17px;border-radius:3px;white-space:nowrap}.bsv-traders a:focus-visible{outline:3px solid #f2f1e9;outline-offset:4px}.bsv-traders .bsv-traders-ja{display:none}html[lang^=ja] .bsv-traders .bsv-traders-en{display:none}html[lang^=ja] .bsv-traders .bsv-traders-ja{display:block}@media(max-width:760px){.bsv-traders{grid-template-columns:1fr;padding:23px;gap:14px}.bsv-traders a.bsv-traders-link{justify-self:start;white-space:normal}}
"""
home_component=f'''<section class="bsv-traders" id="traders-library" aria-labelledby="traders-library-heading"><div><div class="bsv-traders-kicker">FREE / TRADINGVIEW · MT4 · MT5</div><h2 id="traders-library-heading">Traders Library</h2><p class="bsv-traders-en">Free indicators, strategies and trading-system source. Find the purpose, setup steps, limitations and original license in one place.</p><p class="bsv-traders-ja">無料のインジケーター・ストラテジー・自動売買ソース。目的・導入手順・注意点・元のライセンスをまとめて確認できます。</p><div class="bsv-traders-tags"><span>{COUNTS['bundled']} source bundles</span><span>{COUNTS['author_hosted']} author-hosted sources</span><span>No registration</span></div></div><a class="bsv-traders-link" href="/trading/"><span class="bsv-traders-en">Explore Traders Library ↗</span><span class="bsv-traders-ja">トレーダーズライブラリへ ↗</span></a></section>'''
(BASE/'integration'/'homepage-section.html').write_text(home_component,'utf-8')
(BASE/'integration'/'homepage-category.css').write_text(HOME_CSS,'utf-8')
(BASE/'integration'/'homepage-nav.html').write_text('<a href="/trading/">Traders Library</a>\n','utf-8')
home_review='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BSV homepage category · Review only</title><style>body{margin:0;padding:7vw;background:#0d100f;color:#bfc8bc;font:14px/1.6 system-ui}body>p{max-width:700px}'+HOME_CSS+'</style><body><p>Proposed homepage category. This is the new section only, not a reproduction or a deployed copy of the existing BSV homepage.</p>'+home_component.replace('href="/trading/"','href="Traders-Library-Preview.html"')+'</body></html>'
(BASE/'Homepage-Category-Preview.html').write_text(home_review,'utf-8')
urls=['https://botshelfvampire.com/trading/']+[f'https://botshelfvampire.com/trading/{d["detail_url"]}' for d in DATA]+[f'https://botshelfvampire.com/trading/guides/{id}.html' for id in GUIDES]
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+E(u)+'</loc></url>' for u in urls)+'</urlset>','utf-8')
(OUT/'LICENSE-SCOPE.txt').write_text('This directory is an aggregate. Third-party source retains its original license, authorship and notices. Each download contains the applicable LICENSE.txt. Do not apply a repository-wide MIT license to GPL or Apache source. BSV explanatory pages, stylesheet and browser script are original editorial/interface work; no ownership of upstream source is claimed.\n','utf-8')
(BASE/'build-manifest.json').write_text(json.dumps({'date':DATE,'counts':COUNTS,'html_pages':len(list(OUT.rglob('*.html'))),'source_snapshots':COUNTS['source_files'],'status':'Built locally; production deployment not performed by this builder','source_execution':'None','files':[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,'sha256':HASH(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]},ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'counts':COUNTS,'html_pages':len(list(OUT.rglob('*.html'))),'preview_bytes':(BASE/'Traders-Library-Preview.html').stat().st_size},ensure_ascii=False))
