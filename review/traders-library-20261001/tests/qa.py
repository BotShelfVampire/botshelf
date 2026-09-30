#!/usr/bin/env python3
"""Offline release checks. No trading code or account action is executed.
Browser checks render our own HTML in memory, not over HTTP or file navigation.
"""
from pathlib import Path
import json,hashlib,zipfile,io,re,sys
from collections import Counter
from urllib.parse import urlparse,unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
B=Path(__file__).resolve().parents[1];W=B/'trading';T=B/'tests'
checks=[]
def ok(value,label):
    if not value: raise AssertionError(label)
    checks.append(label)
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
D=json.loads((W/'catalog.json').read_text());C=json.loads((W/'source-policy.json').read_text())['counts']
ok(len(D)==C['items'],'catalogue count')
ok(len({x['id'] for x in D})==len(D),'unique program ids')
ok(C['bundled']==sum(x['is_bundled'] for x in D),'source bundles counted separately')
ok(C['author_hosted']==sum(not x['is_bundled'] for x in D),'author links counted separately')
ok(C['source_files']==sum(x['source_count'] or 0 for x in D),'source files not counted as extra products')
sources=[]
for d in D:
    ok(not d['compiled'] and not d['runtime_tested'],d['id']+' no false runtime badge')
    for lang in ['en','ja']:
        ok(all(len(d['text'][lang][k])>10 for k in ['purpose','mechanism','settings','caution']),d['id']+' '+lang+' editorial complete')
    page=W/d['detail_url'];text=page.read_text();sp=BeautifulSoup(text,'html.parser')
    ok(bool(sp.select_one('h1')) and d['name'] in sp.select_one('h1').text,d['id']+' detail title')
    ok('Not tested by BSV' in text,d['id']+' explicit verification status')
    if d['is_bundled']:
        zbytes=(W/d['download']).read_bytes()
        ok(sha(zbytes)==d['download_sha256'],d['id']+' ZIP SHA256')
        with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
            names=z.namelist();pre=d['id']+'/'
            ok(all(not n.startswith('/') and '..' not in Path(n).parts for n in names),d['id']+' safe ZIP paths')
            ok(z.read(pre+'LICENSE.txt')==(W/d['license_file']).read_bytes(),d['id']+' full original license')
            ok('English' in z.read(pre+'README-BSV.md').decode() and '日本語' in z.read(pre+'README-BSV.md').decode(),d['id']+' bilingual ZIP guide')
            for line in z.read(pre+'SHA256SUMS.txt').decode().splitlines():
                digest,name=line.split('  ',1)
                ok(sha(z.read(pre+name))==digest,d['id']+' archive manifest '+name)
            for f in d['files']:
                raw=(W/f['local_source']).read_bytes()
                ok(blob(raw)==f['blob_sha1'],d['id']+' upstream git blob '+f['path'])
                ok(sha(raw)==f['sha256'],d['id']+' source SHA256 '+f['path'])
                ok(z.read(pre+'source/'+f['path'])==raw,d['id']+' unmodified ZIP source '+f['path'])
                sources.append(sha(raw))
    else:
        ok(d['license']=='Apache-2.0' and d['source_url'].startswith('https://github.com/EarnForex/'),d['id']+' original-publisher source directory')
        ok('not every file or dependency' in text and 'not a BSV mirror' in text,d['id']+' honest directory scope')
        ok(not d.get('download'),d['id']+' no fake BSV download')
ok(len(sources)==len(set(sources)),'no duplicate source bytes within bundled collection')
for p in W.rglob('*.html'):
    sp=BeautifulSoup(p.read_text(),'html.parser')
    ids=[e['id'] for e in sp.select('[id]')]
    ok(len(ids)==len(set(ids)),p.name+' unique DOM ids')
    for e in sp.select('[href],[src]'):
        u=e.get('href') or e.get('src');a=urlparse(u)
        if a.scheme or a.netloc or not a.path:continue
        target=(p.parent/unquote(a.path)).resolve()
        ok(target.is_file(),p.name+' local reference '+u)
for p in W.rglob('*'):
    if p.is_file():ok(p.suffix.lower() not in {'.exe','.dll','.ex4','.ex5','.ttf','.otf','.woff','.woff2'},'no binaries/fonts '+str(p.relative_to(W)))
# Only our own self-contained document is rendered. Browser policy denies file:
# navigation, so these checks cannot establish HTTP delivery or real persistence.
browser_checks=[]
def bok(value,label):
    if not value:raise AssertionError(label)
    browser_checks.append(label)
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.set_default_timeout(5000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    html=(B/'Traders-Library-Preview.html').read_text()
    page.set_content(html,wait_until='load')
    bok(page.locator('#cards .card').count()==len(D),'all cards render')
    bok(page.evaluate('Object.keys(BSV_DETAILS).length')==len(D),'all detail views embedded')
    bok(page.evaluate('Object.keys(BSV_ZIPS).length')==C['bundled'],'all source ZIPs embedded')
    embedded=page.evaluate('Object.fromEntries(Object.entries(BSV_ZIPS).map(([k,v])=>[k,v.length]))')
    bok(len(embedded)==35,'35 actual embedded ZIP payloads')
    # A useful filter is checked against the catalogue, not an arbitrary target.
    page.locator('#distribution').select_option('bundled')
    bok(page.locator('#cards .card').count()==C['bundled'],'bundle filter')
    page.locator('#distribution').select_option('author-hosted')
    bok(page.locator('#cards .card').count()==C['author_hosted'],'author directory filter')
    page.locator('#clear-filters').click()
    page.locator('#platform').select_option('MT5')
    bok(page.locator('#cards .card').count()==sum('MT5' in d['platforms'] for d in D),'MT5 platform filter')
    page.locator('#clear-filters').click()
    page.locator('[data-kind="Strategy"]').click()
    bok(page.locator('#cards .card').count()==3,'strategy category')
    page.locator('#clear-filters').click()
    page.locator('#search').fill('Cumulative Volume')
    bok(set(page.locator('#cards .card').evaluate_all('(els)=>els.map(e=>e.dataset.cardId)'))=={'earnforex-cumulative-volume-delta','earnforex-breakeven-line'},'multiword AND search across descriptive text')
    page.locator('#search').fill('<img onerror=alert(1)>')
    bok(page.locator('#cards .card').count()==0 and page.locator('#empty').is_visible(),'safe empty search')
    page.locator('[data-reset]').click()
    page.locator('[data-set-lang="ja"]').click()
    bok(page.locator('html').get_attribute('lang')=='ja','Japanese toggle')
    page.locator('#search').fill('ヒゲ')
    bok(page.locator('#cards .card').count()>0,'Japanese search')
    page.locator('#clear-filters').click()
    page.locator('[data-set-lang="en"]').click()
    saved_id=D[0]['id'];page.locator('[data-save="'+saved_id+'"]').click()
    bok(page.locator('[data-save="'+saved_id+'"]').get_attribute('aria-pressed')=='true','save within session')
    page.locator('#saved-only').click()
    bok(page.locator('#cards .card').count()==1,'saved filter')
    page.locator('#saved-only').click()
    page.locator('#clear-filters').click()
    page.locator('[data-item="earnforex-spike-trader"]').first.click()
    bok(page.locator('#detail-view').is_visible() and not page.locator('#library-view').is_visible(),'inline item navigation')
    bok(page.locator('#detail-view .source-block').count()==3,'MT4 MT5 source plus full license')
    bok('CopyRates' in page.locator('#detail-view').inner_text(),'source-specific defect notes')
    bok(page.locator('#detail-view [data-download]').get_attribute('data-download')=='earnforex-spike-trader','real EA download action')
    # Download clicks are tested by intercepting the created own Blob before
    # browser delivery. This is not a network/download-manager verification.
    page.evaluate("()=>{window.__lastBlob=null;window.__oldCreate=URL.createObjectURL;URL.createObjectURL=b=>{window.__lastBlob=b;return window.__oldCreate(b)}}")
    page.locator('#detail-view [data-download]').click()
    byte_hash=page.evaluate("async()=>{const b=await __lastBlob.arrayBuffer();return Array.from(new Uint8Array(b));}")
    target=next(d for d in D if d['id']=='earnforex-spike-trader')
    bok(sha(bytes(byte_hash))==target['download_sha256'],'EA download Blob equals real ZIP')
    page.locator('#detail-view details.source-block').first.locator('summary').click()
    # A clipboard failure is acceptable only with an explicit truthful message.
    page.locator('#detail-view [data-copy]').first.click()
    page.wait_for_timeout(150)
    bok(page.locator('#toast').is_visible(),'source copy action gives status')
    page.locator('#detail-view [data-home]').click()
    bok(page.locator('#library-view').is_visible(),'return to catalogue')
    page.locator('[data-guide="licenses"]').first.click()
    bok(page.locator('#detail-view').is_visible() and 'license' in page.locator('#detail-view').inner_text().lower(),'source policy opens')
    page.locator('#detail-view [data-home]').click()
    page.evaluate("location.hash='%E0%A4%A'")
    page.wait_for_timeout(100)
    bok(not errors,'malformed route is handled without script errors')
    page.evaluate("location.hash=''");page.wait_for_timeout(100)
    page.locator('[data-set-lang="en"]').click()
    page.screenshot(path=str(T/'desktop-en.png'),full_page=False)
    page.locator('[data-set-lang="ja"]').click()
    page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(80)
    page.screenshot(path=str(T/'desktop-ja.png'),full_page=False)
    for width in [390,320]:
        page.set_viewport_size({'width':width,'height':844})
        for lang in ['en','ja']:
            page.locator('[data-set-lang="'+lang+'"]').click()
            page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(50)
            bok(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{width}px {lang} no horizontal page overflow')
            bok(page.locator('[data-kind="Strategy"]').inner_text().strip()!='',f'{width}px {lang} category labels visible')
        if width==390:page.screenshot(path=str(T/'mobile-ja.png'),full_page=False)
    page.set_viewport_size({'width':390,'height':844})
    page.locator('[data-item="earnforex-spike-trader"]').first.click()
    page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(80)
    bok(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'mobile EA detail no horizontal page overflow')
    page.screenshot(path=str(T/'mobile-ea.png'),full_page=False)
    # Exercise every detail route in this own document.
    for d in D:
        page.evaluate('(id)=>{location.hash="item/"+id}',d['id'])
        page.wait_for_timeout(5)
        bok(page.locator('#detail-view .detail-title').inner_text()==d['name'],'detail route '+d['id'])
    bok(not errors,'no JavaScript errors across all detail routes')
    home=browser.new_page(viewport={'width':1440,'height':820})
    home.set_content((B/'Homepage-Category-Preview.html').read_text())
    bok(home.locator('#traders-library').count()==1,'homepage category component')
    bok(home.locator('.bsv-traders-link').get_attribute('href')=='Traders-Library-Preview.html','homepage preview points to review library')
    home.screenshot(path=str(T/'homepage-category.png'),full_page=False)
    home.set_viewport_size({'width':320,'height':700})
    bok(home.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'homepage component narrow viewport')
    browser.close()
report={'status':'PASS','catalog_counts':C,'static_assertions':len(checks),'browser_assertions':len(browser_checks),'static_checks':checks,'browser_checks':browser_checks,'browser_mode':'Chromium, own document rendered in memory with set_content; not file:// navigation or HTTP serving','not_performed':['TradingView/Pine compilation','MT4/MT5 compilation','Backtests, demo or live trading','Full security/legal certification','Real HTTPS clipboard and browser download-manager delivery','Real localStorage persistence between page loads','Production homepage integration, HTTP headers, routes, server functions and deployment'],'environment_limit':'file:// navigation returned ERR_BLOCKED_BY_ADMINISTRATOR. No browser security policy was disabled to work around it.'}
(T/'qa-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps({k:report[k] for k in ['status','catalog_counts','static_assertions','browser_assertions','browser_mode']},ensure_ascii=False))
