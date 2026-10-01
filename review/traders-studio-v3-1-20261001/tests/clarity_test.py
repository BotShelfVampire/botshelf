"""Own-document browser QA. Every API call is a stub; no login, order or publication."""
import asyncio, json, itertools, hashlib, zipfile
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];P=R/'public/trading'
async def main():
 checks=[];errors=[]
 def check(name,ok):
  if not ok:raise AssertionError(name)
  checks.append(name)
 async with async_playwright() as playwright:
  browser=await playwright.chromium.launch(executable_path='/usr/bin/chromium',headless=True)
  page=await browser.new_page(viewport={'width':1440,'height':1100})
  page.on('pageerror',lambda e:errors.append(str(e)))
  async def load(relative):
   soup=BeautifulSoup((P/relative).read_text(),'html.parser')
   for e in soup.select('script,link[rel=stylesheet]'):e.decompose()
   style=soup.new_tag('style');style.string=(P/'assets/traders.css').read_text();soup.head.append(style)
   await page.set_content(str(soup))
   await page.evaluate("""()=>{window.fetch=async(url)=>new Response(JSON.stringify(String(url).endsWith('/session')?{emailVerified:false}:String(url).endsWith('/catalogue')?[]:{error:'email_registration_required'}),{status:String(url).endsWith('/session')||String(url).endsWith('/catalogue')?200:401,headers:{'Content-Type':'application/json'}})}""")
   for n in ['catalog.js','clarity.js','app.js']:await page.add_script_tag(content=(P/'assets'/n).read_text())
   await page.wait_for_timeout(40)
  await load('publish/index.html');await page.click('[data-goto="3"]')
  for lang in ['ja','en']:
   await page.evaluate('(l)=>document.documentElement.lang=l',lang)
   for visibility,access,mode in itertools.product(['public','private'],['open','protected','invite-only'],['free','paid']):
    for selector,value in [('visibility',visibility),('accessMode',access),('mode',mode)]:await page.select_option('#'+selector,value)
    if mode=='paid':await page.fill('#price','100')
    text=await page.locator('#selection-body').inner_text()
    check(f'{lang} {visibility}/{access}/{mode} source explanation',(('No source is delivered' in text or 'コードは渡しません' in text)==(access!='open')))
    if mode=='paid':
     check(f'{lang} {visibility}/{access} exact 100 split',all(x in text for x in ['100.00 USDT','80.00 USDT','20.00 USDT','TRC20']))
     if visibility=='private' or access=='invite-only':check(f'{lang} {visibility}/{access} permission AND paid',('支払いだけでは使えません' in text or 'Payment alone is not enough' in text))
    else:check(f'{lang} {visibility}/{access} free still needs registration','登録' in text or 'registration' in text)
   check(lang+' dropdown label in selected language',('Source visible' if lang=='en' else 'ソース公開') in await page.locator('#accessMode').inner_text())
  await page.evaluate("document.documentElement.lang='ja'");await page.select_option('#visibility','public');await page.select_option('#accessMode','invite-only');await page.select_option('#mode','paid');await page.fill('#price','100')
  for width in [320,390,1440]:
   await page.set_viewport_size({'width':width,'height':1000})
   check('creator width '+str(width),await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  await page.set_viewport_size({'width':1440,'height':1100});await page.locator('[data-step="3"]').scroll_into_view_if_needed();await page.screenshot(path=str(R/'tests/clarity-pricing-desktop.png'))
  await page.locator('#selection-summary').scroll_into_view_if_needed();await page.locator('#selection-summary').screenshot(path=str(R/'tests/clarity-selection.png'))
  await page.set_viewport_size({'width':390,'height':844});await page.locator('#selection-summary').scroll_into_view_if_needed();await page.screenshot(path=str(R/'tests/clarity-selection-mobile.png'))
  await load('guide/index.html')
  text=await page.locator('body').inner_text()
  for phrase in ['100 USDT','80 USDT','20 USDT','30日','40日','本人確認','回収','改良','支払いはUSDT・TRC20のみ']:
   check('guide explains '+phrase,phrase in text)
  for width in [320,390,1440]:
   await page.set_viewport_size({'width':width,'height':1000});check('guide width '+str(width),await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  await page.set_viewport_size({'width':1440,'height':1000});await page.screenshot(path=str(R/'tests/clarity-guide.png'))
  await load('index.html')
  for width in [320,390,1440]:
   await page.set_viewport_size({'width':width,'height':1000});check('library width '+str(width),await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  await page.set_viewport_size({'width':390,'height':844});await page.locator('#how-it-works').scroll_into_view_if_needed();await page.screenshot(path=str(R/'tests/clarity-library-mobile.png'))
  await page.set_viewport_size({'width':1440,'height':1100});await page.evaluate('window.scrollTo(0,0)');await page.screenshot(path=str(R/'tests/clarity-library-desktop.png'))
  # Exercise the actual buyer copy from the public rendering helper, not a fake sale.
  for mode in ['open','protected','invite-only']:
   text=await page.evaluate("d=>{const n=window.TradersClarity.customer(d);return n.textContent}",{'accessMode':mode,'mode':'paid'})
   check('customer '+mode+' renewal explained','自動引き落とし' in text and '30日間' in text)
   if mode=='invite-only':check('customer invitation before purchase','購入前に作者の許可' in text)
  check('no uncaught browser errors',not errors)
  await browser.close()
 # No protected bytes changed, relocated, or newly published by copy work.
 with zipfile.ZipFile('/mnt/data/BSV-Traders-Studio-v3.zip') as baseline:
  for n in baseline.namelist():
   if n.startswith('private/') or n.startswith('server/'):
    check(n+' unchanged',baseline.read(n)==(R/n).read_bytes())
 for f in P.rglob('*.html'):
  soup=BeautifulSoup(f.read_text(),'html.parser')
  check(str(f.relative_to(P))+' visible guide link',bool(soup.select_one('a[href="/trading/guide/"]')))
  check(str(f.relative_to(P))+' helper wired',bool(soup.select_one('script[src="/trading/assets/clarity.js"]')))
 report={'status':'PASS','checks':len(checks),'details':checks,'errors':errors,'scope':'Own-document Chromium with stubbed APIs; 320/390/1440 viewport layout and bilingual explanatory states. Includes unchanged private-source/server hash checks. No production HTTP, email, login, checkout, actual user test, payment or native-platform test.'}
 (R/'tests/clarity-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('Clarity QA:',len(checks),'PASS')
asyncio.run(main())
