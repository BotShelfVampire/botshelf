import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];PUB=R/'public'
async def main():
 checks=[];errors=[];requests=[];state={'verified':False,'publish':'pending_review'}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True)
  page=await browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)))
  async def load(path):
   from bs4 import BeautifulSoup
   f=PUB/path.lstrip('/')
   if f.is_dir():f=f/'index.html'
   soup=BeautifulSoup(f.read_text(),'html.parser')
   for x in soup.find_all('script'):x.decompose()
   for x in soup.find_all('link',rel='stylesheet'):x.decompose()
   style=soup.new_tag('style');style.string=(PUB/'trading/assets/traders.css').read_text();soup.head.append(style)
   await page.set_content(str(soup))
   await page.evaluate("""state=>{window.TEST_STATE=state;window.TEST_REQUESTS=[];window.fetch=async(path,options={})=>{
     const key=String(path).replace('/api/traders/','');let status=200,data;
     if(key==='session')data={registered:state.verified,emailVerified:state.verified,displayName:'TEST SESSION'};
     else if(key==='catalogue'||key==='mine')data=[];
     else if(key==='listings'){window.TEST_REQUESTS.push(JSON.parse(options.body));data={id:'test-listing',revision:1,status:'draft'};status=201;}
     else if(key==='listings/test-listing/publish'){window.TEST_REQUESTS.push(JSON.parse(options.body));data={id:'test-listing',status:state.publish,publishResult:state.publish};}
     else if(key.startsWith('curated/')){data={error:'email_registration_required'};status=401;}
     else {data={error:'production_adapters_not_connected'};status=503;}
     return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
   };}""",state)
   await page.add_script_tag(content=(PUB/'trading/assets/catalog.js').read_text())
   await page.add_script_tag(content=(PUB/'trading/assets/clarity.js').read_text())
   await page.add_script_tag(content=(PUB/'trading/assets/app.js').read_text())
  async def check(name,value):
   if not value:raise AssertionError(name)
   checks.append(name)
  await load('/trading/')
  await page.wait_for_selector('.card')
  await check('39 real curated program cards',await page.locator('.card').count()==39)
  await check('no source bodies embedded in public page','//@version=' not in await page.content())
  await check('registration and creator CTAs visible','メール登録' in await page.locator('body').inner_text() and await page.locator('a[href="/trading/publish/"]').count()>0)
  await page.select_option('#platform-filter','cTrader')
  await check('cTrader filter populated from actual source',await page.locator('.card').count()==1)
  await page.select_option('#platform-filter','Backtrader')
  await check('Backtrader filter populated from actual source',await page.locator('.card').count()==1)
  await page.select_option('#platform-filter','')
  await page.fill('#search','totally-no-such-tool')
  await check('empty results correct',await page.locator('#empty').is_visible())
  await page.fill('#search','')
  await page.screenshot(path=str(R/'tests/library-desktop.png'),full_page=False)
  await load('/trading/items/spotware-sample-sma.html')
  await page.click('#get-source')
  await page.wait_for_timeout(100)
  await check('anonymous source access fails visibly','メール登録' in await page.locator('#download-status').inner_text())
  await check('anonymous source body remains absent',not await page.locator('#source-view').is_visible())
  await load('/trading/publish/')
  await page.wait_for_timeout(100)
  await check('registration required before creator save',not state['verified'] and 'メール登録' in await page.locator('#auth-status').inner_text())
  await check('15 extensible platform choices',await page.locator('#platform option').count()==15)
  await page.screenshot(path=str(R/'tests/creator-desktop.png'),full_page=False)
  payload={'title':'<img src=x onerror=alert(1)> Original work','authorName':'TEST AUTHOR','platformVersion':'Pine v6','summary':'This is an offline synthetic test publication.','purpose':'A synthetic original source used only for testing this user interface.','setup':'Install in a separate test environment; do not place any real trade.','parameters':'The example has no configurable parameters.','limitations':'This source has not been platform-compiled or tested live.'}
  for k,v in payload.items():await page.fill('[name="'+k+'"]',v)
  await page.click('[data-goto="2"]')
  await page.fill('#pasteName','test.pine');await page.fill('#pasteCode','//@version=6\nindicator("fixture")\nplot(close)')
  await page.select_option('#license','MIT');await page.fill('[name="licenseText"]','MIT License. Copyright (c) 2026 TEST AUTHOR. This is an offline fixture, not an actual uploaded publication.')
  await page.check('[name="agreedRights"]');await page.check('[name="agreedDistribution"]')
  await page.click('[data-goto="3"]')
  await page.select_option('#mode','paid');await page.fill('#price','20.5');await page.fill('#subscriptionValue','Monthly protected access and ongoing updates for this test only.')
  await page.click('#preview')
  await check('one-time option removed',await page.locator('option[value=perpetual]').count()==0)
  await check('seller 80 percent shown', '16.40 USDT' in await page.locator('#seller-amount').inner_text())
  await check('BSV 20 percent shown','4.10 USDT' in await page.locator('#platform-amount').inner_text())
  await page.select_option('#accessMode','invite-only');await page.select_option('#visibility','private');await page.click('#preview')
  await check('invite-only and private are independent', '非公開' in await page.locator('#listing-preview').inner_text() and 'あなたが許可した人だけ' in await page.locator('#listing-preview').inner_text())
  await page.select_option('#accessMode','open');await page.select_option('#visibility','public');await page.click('#preview')
  await check('paid option and price preview', '20.50 USDT' in await page.locator('#listing-preview').inner_text())
  await check('user title is escaped, not interpreted',await page.locator('#listing-preview img').count()==0)
  await page.click('#save')
  await check('anonymous save sends no write request',await page.evaluate('window.TEST_REQUESTS.length')==0)
  await check('anonymous save explains verification','メール登録' in await page.locator('#form-status').inner_text())
  await page.screenshot(path=str(R/'tests/creator-paid-preview.png'),full_page=False)
  await page.set_viewport_size({'width':390,'height':844})
  await check('mobile no horizontal overflow',await page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
  await page.screenshot(path=str(R/'tests/creator-mobile.png'),full_page=False)
  # Authenticated browser integration uses ONLY fake responses; no customer data.
  state['verified']=True
  await load('/trading/publish/')
  for k,v in payload.items():await page.fill('[name="'+k+'"]',v)
  await page.click('[data-goto="2"]');await page.fill('#pasteName','test.pine');await page.fill('#pasteCode','//@version=6\nindicator("fixture")\nplot(close)');await page.select_option('#license','MIT');await page.fill('[name="licenseText"]','MIT License. Copyright (c) 2026 TEST AUTHOR. This is an offline fixture, not an actual uploaded publication.');await page.check('[name="agreedRights"]');await page.check('[name="agreedDistribution"]');await page.click('[data-goto="3"]');await page.click('#publish');await page.wait_for_timeout(100)
  await check('verified publish sends save and publish calls',await page.evaluate('window.TEST_REQUESTS.length')==2)
  await check('source sent only in verified creator request',await page.evaluate('window.TEST_REQUESTS[0].draft.files[0].name')=='test.pine')
  await check('review-pending is not claimed published','確認待ち' in await page.locator('#form-status').inner_text())
  await check('no uncaught browser errors',not errors)
  await browser.close()
 result={'status':'PASS','browser_checks':len(checks),'checks':checks,'errors':errors,'scope':'In-memory own-document Chromium checks with mocked fetch. URL navigation was blocked by administrator; no policy settings were changed. No real HTTP route, email, registration, persistence, payment, publication or trading was tested.'}
 (R/'tests/browser-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps(result,ensure_ascii=False))
asyncio.run(main())
