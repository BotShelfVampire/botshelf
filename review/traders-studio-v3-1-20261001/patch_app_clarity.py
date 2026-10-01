from pathlib import Path
R=Path(__file__).resolve().parent
p=R/'public/trading/assets/app.js'
s=p.read_text()
# A choice summary is explanatory only. Existing server auth and billing remain unchanged.
s=s.replace("p.append(h,desc,info,access,billing,rights,status);p.hidden=false;", "const explanation=document.createElement('div');window.TradersClarity?.fill(explanation,d);p.append(h,desc,info,explanation,rights,status);p.hidden=false;")
s=s.replace(";if(communityItem&&d.accessMode&&d.accessMode!=='open')", ";const guidance=window.TradersClarity?.customer(d);if(guidance)target.querySelector('.actions').before(guidance);if(communityItem&&d.accessMode&&d.accessMode!=='open')")
s=s.replace("${tr('メール登録してコードを取得','Register to get code')}","${session?.emailVerified?tr('コードを表示・取得','View and get code'):tr('メール登録してコードを取得','Register to get code')}")
s=s.replace("$('#get-source').textContent=tr('利用権限を確認','Check access');", "$('#get-source').textContent=tr('この作品の利用を申し込む・確認する','Request or check access');")
s=s.replace("tr('購入手続きへ','Go to checkout')", "tr('月額の支払い手続きへ','Monthly subscription checkout')")
s=s.replace("if(page==='creator')await loadDashboard();", "if(page==='item')renderItem();if(page==='creator')await loadDashboard();")
s=s.replace("'ソースは非公開です。利用権限からアクセスしてください。'", "'この作品のコードは非公開です。「この作品の利用を申し込む・確認する」から利用状況を確認してください。'")
s=s.replace("'有効な月額契約が必要です。'", "'月額の利用期間が有効ではありません。支払い・更新状況を確認してください。'")
s=s.replace("'作者からの利用許可が必要です。'", "'作者の利用許可がまだありません。招待制は、支払いだけでは使えません。'")
s=s.replace("'このソースの取得には購入が必要です。'", "'この作品には月額料金がかかります。入金確認後、有効な利用期間中に取得できます。'")
s=s.replace("'期限（任意・日本時間）'", "'利用を許可する期限（任意・この端末の時刻）'")
# Avoid leaking internal status names to nontechnical creators.
s=s.replace("status.textContent=r.status;", "status.textContent=({draft:tr('下書き・未公開','Draft — private'),pending_review:tr('確認待ち・未公開','Checks pending — not published'),published:tr('公開中','Published'),unpublished:tr('公開停止中','Unpublished'),rejected:tr('確認で問題あり・未公開','Not published — changes needed')}[r.status]||tr('状態を確認中','Checking status'));")
s=s.replace("'+tr('登録済みのメールアドレス','Registered email')+'", "'+tr('許可したい人の登録メールアドレス','Registered email of the person to approve')+'")
s=s.replace("box.append(panel);const status", "const help=document.createElement('p');help.textContent=tr('ここで許可しても、有料作品の料金は免除されません。招待制は作者の許可と有効な月額契約の両方が必要です。','Approval does not waive a paid work’s fee. Invite-only paid works require both approval and an active subscription.');panel.querySelector('h2').after(help);box.append(panel);const status")
p.write_text(s)
# Include helper in both review bundling and browser tests. Offline preview is not a live site.
p=R/'make_preview.py';s=p.read_text();s=s.replace("app=(P/'assets/app.js').read_text()", "app=(P/'assets/app.js').read_text();clarity=(P/'assets/clarity.js').read_text()")
s=s.replace(",catalog,app,",",catalog,clarity,app,")
s=s.replace('<a href="#creator">作品管理</a>', '<a href="#creator">作品管理</a><a href="#guide">使い方・料金</a>')
s=s.replace("function pick(){show(location.hash", "function pick(){if(location.hash==='#guide'){show('/trading/guide/');return;}show(location.hash")
p.write_text(s)
p=R/'tests/browser_test.py';s=p.read_text();s=s.replace("await page.add_script_tag(content=(PUB/'trading/assets/app.js').read_text())", "await page.add_script_tag(content=(PUB/'trading/assets/clarity.js').read_text())\n   await page.add_script_tag(content=(PUB/'trading/assets/app.js').read_text())")
s=s.replace("'20.5 USDT' in await page.locator('#listing-preview').inner_text()", "'20.50 USDT' in await page.locator('#listing-preview').inner_text()")
# Updated preview has translated explanations rather than raw configuration words.
s=s.replace("'招待制' in await page.locator('#listing-preview').inner_text()", "'あなたが許可した人だけ' in await page.locator('#listing-preview').inner_text()")
p.write_text(s)
print('Client explanations integrated; no server enforcement changed.')
