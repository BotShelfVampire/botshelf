"""One-time, offline v3 -> v3.1 explanatory UI patch. No network or production writes."""
from pathlib import Path
from bs4 import BeautifulSoup
from html import escape
import json
R=Path(__file__).resolve().parent
P=R/'public/trading'
def bi(ja,en):
    return '<span data-ja="">'+escape(ja)+'</span><span data-en="">'+escape(en)+'</span>'
def fragment(s): return BeautifulSoup(s,'html.parser')
def replace_content(node,html):
    node.clear()
    for n in list(fragment(html).contents): node.append(n)
def after(node,html):
    for n in reversed(list(fragment(html).contents)): node.insert_after(n)

guide_intro='<h2>'+bi('使う人も、作る人も。まずはここだけ。','Start here: use a tool or publish your own.')+'</h2>'
quick='''<section class="plain-start" id="how-it-works" aria-labelledby="start-heading"><h2 id="start-heading">'''+bi('無料で使う。自分の作品を販売する。','Use free code. Sell your own work.')+'''</h2><div class="plain-columns"><div><h3>'''+bi('使いたい人','For users')+'''</h3><p>'''+bi('メール登録 → 届いたメールで本人確認 → 使いたい作品を選びます。無料作品は代金0。有料作品は表示された月額を支払って利用します。','Register your email → verify it in the email you receive → choose a work. Free works cost nothing. Paid works require the displayed monthly payment.')+'''</p></div><div><h3>'''+bi('公開・販売したい人','For creators')+'''</h3><p>'''+bi('自分で作品を登録し、無料か月額有料かを選べます。月額はあなたが決めます。コードを見せるか、隠すか、招待した人だけに使わせるかも選べます。','Upload your work and choose free or monthly paid access. You set the price. You also choose whether users receive the code, use it without seeing the code, or need your invitation.')+'''</p></div></div><p class="money-example">'''+bi('売上が100 USDTなら、販売者に80 USDT、BSVの手数料は20 USDT。','On a 100 USDT sale, the seller receives 80 USDT and BSV receives a 20 USDT fee.')+'''</p><p>'''+bi('有料作品はすべて月額。支払いはUSDT・TRC20のみ。集めた無料作品をそのまま有料にはしません。','Every paid work is monthly. Payments use USDT on TRC20 only. Collected free originals stay free.')+'''</p><a class="text-link" href="/trading/guide/">'''+bi('公開設定・料金・使い方を確認する →','Read the guide to access, pricing and use →')+'''</a></section>'''

# All real public pages receive a discoverable guide. No source bytes are added.
for f in P.rglob('*.html'):
    s=BeautifulSoup(f.read_text(),'html.parser')
    nav=s.select_one('.navlinks')
    if nav and not nav.select_one('a[href="/trading/guide/"]'):
        a=s.new_tag('a',href='/trading/guide/');replace_content(a,bi('はじめての方へ','How it works'));nav.insert(0,a)
    footer=s.select_one('footer')
    if footer:
        replace_content(footer,bi('コードの取得・利用・作品の公開にはメール登録と本人確認が必要です。作者名と利用条件は各作品で確認できます。','Verified email registration is required to get code, use a work or publish. Each work identifies its author and usage terms.')+' <a class="text-link" href="/trading/guide/">'+bi('使い方・料金','Access and pricing')+'</a>')
    scripts=s.find_all('script',src=True)
    app=next((x for x in scripts if str(x.get('src','')).endswith('/app.js')),None)
    if app:
        g=s.new_tag('script',src='/trading/assets/clarity.js');g['defer']='';app.insert_before(g)
    f.write_text(str(s))

f=P/'index.html';s=BeautifulSoup(f.read_text(),'html.parser')
hero=s.select_one('.hero')
after(hero,quick)
# Explain monthly access in the main creator card, not only in the final form step.
card=s.select_one('.hero-card')
replace_content(card.select_one('p'),bi('自分のインジケーター・ストラテジー・EAを登録できます。無料配布も、あなたが決めた価格での月額販売も選べます。','Publish your own indicators, strategies or trading systems. Offer them free or set your own monthly subscription price.'))
s.title.string='Traders Library · 無料コードと作品の月額販売'
f.write_text(str(s))

f=P/'publish/index.html';s=BeautifulSoup(f.read_text(),'html.parser')
replace_content(s.select_one('main > p'),bi('自分の作品を、無料で配ることも、月額で販売することもできます。下の3つの画面で説明・コード・公開方法を決めます。','Offer your own work for free or as a monthly subscription. Use the three steps below to describe it, add your code and choose how to share it.'))
intro='<div class="creator-basics"><p>'+bi('販売する場合：月額はあなたが設定。売上の80%があなた、20%がBSVです。支払いはUSDT・TRC20のみです。','For paid works: you set the monthly price. You receive 80% of each sale; BSV receives 20%. Payments use USDT on TRC20 only.')+'</p><p>'+bi('コードをアップロードしただけでは公開されません。最後に「確認して公開」を押し、必要な確認を通過した作品だけ公開されます。','Uploading code does not publish it. Only the final publish action and successful checks can make a work available.')+'</p></div>'
s.select_one('#auth-status').insert_before(fragment(intro))
steps=[('作品の説明','Describe your work'),('コードと利用条件','Code and usage terms'),('見せ方・使わせ方・料金','Visibility, access and price')]
for n,(ja,en) in enumerate(steps,1):
    replace_content(s.select_one(f'[data-goto="{n}"]'),f'0{n}　'+bi(ja,en))
    replace_content(s.select_one(f'[data-step="{n}"] h2'),f'0{n}　'+bi(ja,en))
replace_content(s.select_one('.steps p'),bi('下書きは非公開です。いつでも編集でき、公開後の更新・停止は「作品管理」から行えます。','Drafts are private. Edit them at any time. Use your dashboard to update or unpublish a released work.'))
# Field-level examples give authors a practical writing model, not just labels.
hints={
 'summary':('何に役立つかを1〜2文で。例：価格が指定した線に触れたら通知するインジケーターです。','Explain its benefit in one or two sentences. Example: an indicator that alerts when price touches a chosen level.'),
 'purpose':('何を見て、何をする作品か。自動で注文するのか、表示・通知だけなのかも書きます。','Explain what it observes and what it does. Say whether it places orders or only displays information or alerts.'),
 'setup':('どのソフトに、どのファイルを入れ、何を押すかを順番に書きます。','List the steps: which software to open, where to put the files and which buttons to use.'),
 'parameters':('設定の名前と、変えると何が変わるか。数値の単位も書きます。','Name each setting and explain what changes when it is adjusted. Include the units.'),
 'limitations':('苦手な場面・必要な追加ソフト・未確認の動作を書きます。試していないことを「確認済み」にしないでください。','Describe limitations, extra software and untested behavior. Do not call something tested if it was not tested.'),
 'license':('自作の作品なら、オープンソースの条件も「作者独自の利用条件」も選べます。コードを見せる設定と、改変・再配布を許す条件は別です。','For original work, choose an open-source license or your own terms. Letting someone see code is separate from letting them modify or redistribute it.'),
 'licenseText':('利用者がしてよいこと・してはいけないことを書きます。他者のコードを含む場合は、その条件を消したり狭めたりできません。','State what users may and may not do. When including third-party code, preserve the applicable rights and conditions.'),
 'visibility':('ここで決めるのは「紹介ページを誰に見せるか」です。公開しても、コードが自動で公開されるわけではありません。','This controls who can see the listing page. A public listing does not automatically expose its code.'),
 'accessMode':('ここで決めるのは「コードを渡すか、見せずに使わせるか」です。無料か有料かは、次で別に選びます。','This controls whether users receive the code or use the work without seeing it. Choose free or paid access separately below.'),
 'price':('利用者1人あたりの月額です。売上100 USDTなら、あなたの取り分は80 USDTです。','Monthly price per user. A 100 USDT sale leaves you 80 USDT after BSV’s fee.'),
 'subscriptionValue':('毎月何を提供するかを具体的に。例：作品の利用、更新版の提供、質問対応。実際に提供するものだけを書きます。','List what users receive each month, such as access, updates or support. Include only what you will actually provide.'),
}
for ident,(ja,en) in hints.items():
    el=s.select_one('#'+ident);label=el.find_parent('label')
    old=label.find('small')
    if old:old.decompose()
    h=s.new_tag('small',id=ident+'-help');replace_content(h,bi(ja,en));label.append(h);el['aria-describedby']=ident+'-help'
    if ident in ['summary','purpose','setup','parameters','limitations','subscriptionValue']:
        el['data-placeholder-ja']=ja;el['data-placeholder-en']=en;el['placeholder']=ja
# Source and rights declarations: origin/policies are clear before uploads.
originbox=s.select_one('[data-step="2"] .notice')
replace_content(originbox,bi('無料で公開されている作品を、そのまま有料で売ることは禁止です。あなたが独自に改良したリメイクは、元の利用条件や作者の許可で販売できる場合に限り、月額で販売できます。','Do not sell an unchanged work that is available free elsewhere. Your own substantive remake may be sold monthly only when the original terms or permission allow it.'))
replace_content(s.select_one('#protection-note'),bi('ソース公開＝コードを渡す。ソース保護＝コードを見せずに使わせる。招待制＝コードを隠し、あなたが許可した人だけに使わせる。保護・招待制は、対応ソフトで本当に制限できることを確認してから公開します。','Source visible: users receive the code. Protected: users use the work without seeing its code. Invite-only: the code stays hidden and only people you approve may use it. Protected and invite-only works require a working access mechanism on their platform before publication.'))
# Explicit labels on each independent choice.
option_copy={
 ('visibility','public'):('公開：紹介ページを誰でも見られる','Public: anyone can see the listing'),
 ('visibility','private'):('非公開：作者と許可した人だけ','Private: only you and approved users'),
 ('accessMode','open'):('ソース公開：コードを渡して使ってもらう','Source visible: users receive the code'),
 ('accessMode','protected'):('ソース保護：コードは隠して使ってもらう','Protected: use without seeing the code'),
 ('accessMode','invite-only'):('招待制：コードを隠し、許可した人だけ','Invite-only: hidden code, approved users only'),
 ('mode','free'):('無料：代金0、メール登録は必要','Free: no charge, email required'),
 ('mode','paid'):('月額有料：価格はあなたが決める','Monthly paid: you set the price'),
}
for (sel,val),(ja,en) in option_copy.items():
    o=s.select_one(f'#{sel} option[value="{val}"]');o.string=ja;o['data-label-ja']=ja;o['data-label-en']=en
# Guided explanation of the current combination, updated as choices change.
recap='<section class="selection-summary" id="selection-summary" aria-labelledby="selection-heading"><h3 id="selection-heading">'+bi('今の設定だと、こうなります','What these settings mean')+'</h3><div id="selection-body" aria-live="polite"></div></section>'
s.select_one('#listing-preview').insert_before(fragment(recap))
term=s.select_one('#term-field')
replace_content(term.select_one('p.note'),bi('1回の支払いで、入金確認から30日間の利用期間が付きます。期限前に更新すれば、残りの期間に30日を追加。期限切れ後は、新しい入金確認から30日間です。自動引き落としではなく、継続にはその都度支払いが必要です。','One payment gives a 30-day period starting at payment confirmation. Renew before expiry to add 30 days to the remaining period. Renew after expiry to start a new 30-day period. Renewal requires another payment; there is no automatic debit.'))
after(term.select_one('.settlement'),'<p class="money-example">'+bi('例：月額100 USDTで1人が購入 → 販売者80 USDT ／ BSV20 USDT。','Example: one subscriber pays 100 USDT → seller 80 USDT / BSV 20 USDT.')+'</p><p>'+bi('USDTは支払いに使う暗号資産、TRC20は送金時に選ぶネットワークです。別の通貨・ネットワークでは支払わないでください。','USDT is the payment token; TRC20 is the network to select when sending it. Do not pay in another token or over another network.')+'</p>')
notes=s.select('[data-step="3"] > .notice')
for n in notes:replace_content(n,bi('無料でもメール登録と本人確認が必要です。有料作品は、入金確認と有効な利用期間が必要です。招待制は、支払うだけでは使えません。作者の許可も必要です。','Free works still require verified email registration. Paid works require confirmed payment and an active subscription. Payment alone does not unlock an invite-only work: the author must also approve you.'))
lastnote=s.select_one('[data-step="3"] > p.note:not(#protection-note)')
if lastnote:replace_content(lastnote,bi('ソース公開で渡したコードは、後から回収できません。契約終了後の利用は、そのコードの利用条件に従います。月額で提供する更新・サポートなども明記してください。','Code already delivered cannot be taken back. Its terms determine how it may be used after a subscription ends. Explain which ongoing updates or support the monthly payment covers.'))
# Make small but important controls bilingual.
for ident,ja,en in [('previous','戻る','Back'),('next','次へ','Next'),('preview','公開前に確認','Preview settings'),('save','下書きを保存','Save draft'),('publish','確認して公開','Submit for publication')]:
    replace_content(s.select_one('#'+ident),bi(ja,en))
f.write_text(str(s))

# Simple guide: complete answers and examples without requiring entry into the form.
f=P/'guide/index.html';f.parent.mkdir(exist_ok=True)
s=BeautifulSoup((P/'index.html').read_text(),'html.parser');s.body['data-page']='guide';s.title.string='使い方・公開設定・料金 · Traders Library'
sections=[
 ('use','使うまでの3ステップ','Three steps to use a work',[
 ('メール登録をして、届いたメールで本人確認します。紹介ページを見るだけなら登録せずに確認できます。','Register and verify your email using the message you receive. Listing descriptions can be browsed without registration.'),
 ('対応ソフトと使い方を読み、無料作品はコード取得へ。有料作品は月額・提供内容・使える条件を確認してから支払います。','Check the platform and setup guide. Get free works after verification. For paid works, check the price, what is included and the access requirements before paying.'),
 ('ソース公開の作品は、コードを対応ソフトに入れて使います。ソース保護・招待制の作品は、作者の案内に従って利用します。BSVのボタンだけでTradingViewなどの設定まで完了するわけではありません。','For source-visible works, install the code in the stated software. For protected or invite-only works, follow the author’s access instructions. A BSV action alone does not complete setup on TradingView or another platform.')]),
 ('publish','自分の作品を公開・販売する','Publish or sell your own work',[
 ('自作のインジケーター・ストラテジー・EAを、自分で登録できます。何に使うものか、導入手順、設定、注意点を記入し、コードと利用条件を追加します。','Register your own indicator, strategy or trading system. Explain its purpose, setup, settings and limitations, and add its code and usage terms.'),
 ('無料か月額有料かを選びます。有料なら価格はあなたが設定。コードを見せるかどうかも選べます。自作だからといって、オープンソースにする必要はありません。','Choose free or monthly paid access. For paid works, you set the price. You also choose whether to show the code. Original works do not have to be open source.'),
 ('下書きは非公開です。「確認して公開」を押しても、必要な確認が終わるまでは公開されません。公開後は「作品管理」で更新や公開停止、利用者の許可を管理します。著作権は作者に残ります。','Drafts are private. Submitting for publication does not skip required checks. After release, manage updates, unpublishing and permissions in your dashboard. Copyright remains with the author.')]),
 ('visibility','「ページを見せる」と「コードを見せる」は別','Showing a page is not the same as showing code',[
 ('公開：一覧・検索に載り、誰でも紹介ページを見られます。コードが自動で公開される設定ではありません。','Public: the work appears in listings and search, and anyone can view its description. This does not automatically reveal its code.'),
 ('非公開：一覧・検索に出さず、作者と許可した登録ユーザーだけが見られます。URLを知っているだけでは入れません。','Private: it is absent from listings and search, and only the author and approved registered users can view it. Knowing the URL is not sufficient.'),
 ('例：紹介ページは公開して集客し、作品は招待した有料会員だけに提供できます。','Example: make the description public so people can discover it, but allow only invited paying subscribers to use the work.')]),
 ('source','コードをどう提供するか','Choose how to provide the code',[
 ('ソース公開：利用条件を満たした人にコードを渡します。利用者はコードを読めます。改変や再配布まで許すかは、別途の利用条件で決まります。','Source visible: eligible users receive readable code. Whether they may modify or redistribute it is determined separately by its license or terms.'),
 ('ソース保護：コードを見せずに作品を使ってもらいます。料金を払った利用者にも、保護したコードは渡しません。','Protected: users use the work without seeing its source. Paying does not give a subscriber the protected code.'),
 ('招待制：コードを隠したまま、作者が許可した人だけ利用できます。有料なら「作者の許可」と「有効な月額契約」の両方が必要です。無料の招待制でも登録・本人確認は必要です。','Invite-only: the code stays hidden and only author-approved users may use it. A paid work requires both approval and an active subscription. Free invite-only works also require verified registration.'),
 ('保護・期限管理が本当にできる対応環境かを確認してから公開します。BSV上の許可と、TradingViewなど実際に使うソフト側の許可は別々に確認します。','Protected publication requires a working protection and expiry mechanism. BSV permission and permission on the actual trading platform are checked separately.')]),
 ('fees','月額・支払い・手数料','Monthly pricing, payments and fees',[
 ('有料作品はすべて月額サブスクリプションです。買い切りではありません。月額は作者が決め、利用者は注文画面で金額を確認します。','All paid works are monthly subscriptions, not one-time purchases. The creator sets the price and the user confirms it at checkout.'),
 ('売上が100 USDTなら、販売者に80 USDT、BSVの手数料は20 USDTです。手数料は売上から分けるもので、20%を作品代金に上乗せするわけではありません。','For a 100 USDT sale, 80 USDT goes to the seller and 20 USDT is BSV’s fee. The fee is taken from the sale, not added as a further 20% to the work’s price.'),
 ('支払いはUSDT・TRC20のみです。USDTは暗号資産の名前、TRC20は送金するネットワークです。注文画面の通貨・ネットワーク・送金先・金額を確認してください。','Payments use USDT on TRC20 only. USDT is the token and TRC20 is the transfer network. Check the token, network, destination and amount shown at checkout.'),
 ('送金したと入力しただけでは利用開始になりません。入金が確認されてから利用期間が始まります。招待や対応ソフトの設定が必要な作品は、その条件も満たす必要があります。','Entering a transaction reference does not activate access. The subscription starts after payment confirmation. Any invitation or platform setup requirements must also be met.')]),
 ('renewal','いつまで使える？ 更新は？','How long does access last? How do I renew?',[
 ('1回の支払いで、入金確認から30日間です。月末で打ち切られる仕組みではありません。','One payment gives 30 days from payment confirmation. Access does not reset at the end of a calendar month.'),
 ('期限前に更新すると、残り期間に30日を足します。例：残り10日で更新すれば、合計40日になります。期限が切れてから更新した場合は、新しい入金確認から30日間です。','Renew before expiry and 30 days are added to the remaining time. For example, 10 days left plus a renewal gives 40 days. After expiry, a renewal starts 30 days from the new payment confirmation.'),
 ('自動引き落としではありません。続ける場合は、その都度支払いが必要です。支払わなければ有効期間の終了後は月額サービスを利用できません。','There is no automatic debit. Continuing requires another payment. Without renewal, monthly service access ends when the paid period expires.'),
 ('一度受け取ったソースコードをBSVが消したり回収したりはできません。取得済みコードをその後どう使えるかは、コードの利用条件に従います。','BSV cannot delete or retrieve source code already delivered. Its license or usage terms determine how a received copy may be used afterward.')]),
 ('rights','他の人の無料作品は販売できる？','Can I sell someone else’s free work?',[
 ('そのまま転載して有料販売するのは禁止です。名前・説明・見た目だけを変えて有料にすることも認めません。集めた無料の原本は無料のままです。','Selling an unchanged free work is prohibited. Renaming it or changing only its description or appearance does not qualify it for paid resale. Collected free originals remain free.'),
 ('あなたが機能を追加・改良したリメイクは、元の利用条件や作者の許可が改変・販売・選んだ提供方法を認めている場合に月額販売できます。改変元と変更した内容を記入します。','Your substantive remake may be sold monthly when the original terms or permission allow modification, commercial use and the chosen delivery method. Identify the original and explain your changes.'),
 ('「無料で見つかった」だけでは転載の許可になりません。許可が不明なもの、無断コピー、流出品は載せません。必要な作者表示や利用条件は残します。','Being available free does not itself grant permission to redistribute. Unclear permissions, unauthorized copies and leaks are excluded. Required author notices and terms are retained.')]),
 ('platforms','対応ソフトと検証状況を確認する','Check the platform and testing status',[
 ('TradingView・MT4・MT5以外の作品も対象です。ただし、違うソフトのコードをそのまま使えるわけではありません。各作品に書かれた対応ソフトとバージョンを確認してください。','Works for platforms beyond TradingView, MT4 and MT5 are included in scope. Code is not interchangeable between different platforms. Check the platform and version listed on each work.'),
 ('掲載許可の確認と、売買の成績確認は別です。コンパイル・動作確認・バックテストをしていない場合は、そのまま未検証と表示します。','Permission checks are separate from trading-performance checks. Compilation, runtime testing and backtests that have not been performed are labelled untested.')]),
]
body='<div class="detail guide"><div class="eyebrow">TRADERS LIBRARY</div><h1>'+bi('はじめての方へ','How it works')+'</h1><p>'+bi('使う人・公開する人の疑問を、順番にまとめました。','A practical guide for users and creators.')+'</p><nav class="guide-jump" aria-label="Guide sections">'+''.join('<a href="#'+i+'">'+bi(ja,en)+'</a>' for i,ja,en,_ in sections)+'</nav>'
for i,ja,en,paras in sections:
    body+='<section class="guide-section" id="'+i+'"><h2>'+bi(ja,en)+'</h2>'+''.join('<p>'+bi(x,y)+'</p>' for x,y in paras)+'</section>'
body+='<div class="actions"><a class="btn" href="/trading/">'+bi('作品を探す','Explore works')+'</a><a class="btn secondary" href="/trading/publish/">'+bi('自分の作品を公開する','Publish your work')+'</a></div></div>'
replace_content(s.main,body);f.write_text(str(s))
# Homepage integration stays scoped and has its own accessible copy.
(R/'integration/homepage-section.html').write_text('''<section class="bsv-traders" aria-labelledby="traders-heading"><h2 id="traders-heading">Traders Library</h2><p>インジケーター・ストラテジー・自動売買のコードを探す。自分の作品を無料公開・月額販売する。</p><p><strong>利用・作品公開にはメール登録と本人確認が必要です。</strong> 作者が月額を決め、売上の80%は販売者、20%はBSVへ。支払いはUSDT・TRC20のみです。</p><p>コードを見せる・隠す・招待した人だけに使わせるかも作者が選べます。集めた無料作品をそのまま有料にはしません。</p><div class="bsv-traders-actions"><a href="/trading/">無料コードを探す</a> <a href="/trading/publish/">自分の作品を公開・販売する</a> <a href="/trading/guide/">使い方・料金を確認する</a></div></section>''')
# Styling is local to the new explanation blocks.
css=P/'assets/traders.css'
css.write_text(css.read_text()+'''\n/* v3.1: readable in-context explanations */
.plain-start{border:1px solid #3b352b;background:#13161a;border-radius:8px;padding:24px 28px;margin:25px 0 38px}.plain-start h2{margin:0 0 16px}.plain-columns{display:grid;grid-template-columns:1fr 1fr;gap:30px}.plain-columns h3{margin:0 0 8px;font-size:17px}.plain-start p,.creator-basics p,.guide p{font-size:15px;line-height:1.85;max-width:none}.money-example{color:#e5d4ad;background:#232018;padding:13px 16px;border-radius:5px;font-weight:600}.text-link{color:#dfc793;text-decoration:underline;text-underline-offset:4px}.creator-basics{border-left:3px solid #cbb27b;padding:2px 18px;margin:20px 0}.creator-basics p{margin:8px 0}.selection-summary{border:1px solid #5b4d35;border-radius:6px;background:#181815;padding:20px;margin:24px 0}.selection-summary h3{font-size:18px;margin:0 0 14px}.plain-dl{margin:0}.plain-dl div{display:grid;grid-template-columns:115px 1fr;gap:15px;border-top:1px solid #343630;padding:12px 0}.plain-dl div:first-child{border:0}.plain-dl dt{color:#e5d4ad;font-weight:600}.plain-dl dd{margin:0;color:#cbd0d8;line-height:1.85}.field small{font-size:13px;line-height:1.85;color:#aeb9ca}.guide-section{padding:20px 0;border-bottom:1px solid #303641;scroll-margin-top:20px}.guide-jump{display:flex;flex-wrap:wrap;margin:24px 0;padding:0;gap:10px 20px}.guide-jump a{font-size:13px;color:#dfc793;text-decoration:underline}.customer-guide{padding:16px 0;font-size:15px;line-height:1.85}.customer-guide p{margin:6px 0}.navlinks{flex-wrap:wrap}.choice-help-link{font-size:13px}#protection-note{font-size:14px;line-height:1.85}#listing-preview p{overflow-wrap:anywhere}@media(max-width:700px){.plain-columns{grid-template-columns:1fr;gap:18px}.plain-start{padding:20px}.plain-dl div{grid-template-columns:1fr;gap:4px}.selection-summary{padding:16px}.money-example{padding:12px}.guide-jump{gap:12px}.field small{font-size:13px}}\n''')
print('Patched public copy, creator form, guide and homepage component.')
