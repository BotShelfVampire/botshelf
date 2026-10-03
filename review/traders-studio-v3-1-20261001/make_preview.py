from pathlib import Path
from bs4 import BeautifulSoup
import json
R=Path(__file__).resolve().parent;P=R/'public/trading'
css=(P/'assets/traders.css').read_text();catalog=(P/'assets/catalog.js').read_text();app=(P/'assets/app.js').read_text();clarity=(P/'assets/clarity.js').read_text()
pages={}
for f in P.rglob('*.html'):
 key='/trading/'+str(f.relative_to(P));key=key[:-10] if key.endswith('index.html') else key
 soup=BeautifulSoup(f.read_text(),'html.parser')
 for x in soup.find_all('script'):x.decompose()
 for x in soup.find_all('link',rel='stylesheet'):x.decompose()
 st=soup.new_tag('style');st.string=css;soup.head.append(st)
 for js in ["window.fetch=async()=>new Response(JSON.stringify({error:'production_adapters_not_connected'}),{status:503,headers:{'Content-Type':'application/json'}});",catalog,clarity,app,"document.addEventListener('click',e=>{const a=e.target.closest('a');if(!a)return;if(a.getAttribute('href').startsWith('#'))return;e.preventDefault();parent.postMessage({type:'navigate',path:a.getAttribute('href')},'*');});new ResizeObserver(()=>parent.postMessage({type:'height',height:document.documentElement.scrollHeight},'*')).observe(document.body);"]:
  s=soup.new_tag('script');s.string=js;soup.body.append(s)
 pages[key]=str(soup)
content='''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Traders Library / Creator Studio — Review</title><style>body{margin:0;background:#0b0d10;font-family:system-ui;color:#eee}.review{padding:12px 24px;background:#282218;color:#e2d3b4;border-bottom:1px solid #5b4d35;font-size:12px;line-height:1.7}.review a{color:inherit;margin-right:18px;text-decoration:underline}iframe{display:block;width:100%;border:0;min-height:100vh}</style></head><body><div class="review">確認用実装：メール送信・本番保存・公開・決済は行いません。<br><a href="#library">ライブラリ</a><a href="#publish">作品の公開（無料・有料）</a><a href="#creator">作品管理</a><a href="#guide">使い方・料金</a><span id="notice"></span></div><iframe title="Traders Library preview" id="frame"></iframe><script>const PAGES=__DATA__;const frame=document.getElementById('frame');function show(path){if(PAGES[path]){frame.srcdoc=PAGES[path];window.scrollTo(0,0);}else document.getElementById('notice').textContent='この操作は本番のメール登録・認証接続後に利用できます。';}function pick(){if(location.hash==='#guide'){show('/trading/guide/');return;}show(location.hash==='#publish'?'/trading/publish/':location.hash==='#creator'?'/trading/creator/':'/trading/');}window.addEventListener('hashchange',pick);window.addEventListener('message',e=>{if(e.source!==frame.contentWindow)return;if(e.data?.type==='navigate'){const path=String(e.data.path).split('?')[0];if(PAGES[path])show(path);else if(path.startsWith('#'))return;else document.getElementById('notice').textContent='本番への認証・決済接続前のため、この操作は実行しません。';}else if(e.data?.type==='height')frame.style.height=Math.min(30000,Math.max(800,Number(e.data.height)||800))+'px';});pick();</script></body></html>'''
content=content.replace('__DATA__',json.dumps(pages,ensure_ascii=False).replace('<','\\u003c'))
(R/'Traders-Studio-Preview.html').write_text(content)
print('Standalone preview',len(content.encode()),'bytes; protected sources excluded')
