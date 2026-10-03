/* Plain-language UI helpers. Metadata only; not an authorization or payment layer. */
(()=>{'use strict';
const ja=()=>document.documentElement.lang!=='en';
const t=(a,b)=>ja()?a:b;
const $=s=>document.querySelector(s);
function amount(raw){
  const s=String(raw??'0');
  if(!/^\d{1,18}(?:\.\d{1,6})?$/.test(s))return null;
  const [w,f='']=s.split('.');return BigInt(w)*1000000n+BigInt(f.padEnd(6,'0'));
}
function money(n){const tail=(n%1000000n).toString().padStart(6,'0').replace(/0+$/,'').padEnd(2,'0');return (n/1000000n)+'.'+tail+' USDT';}
function rows(d){
 const priv=d.visibility==='private',paid=d.mode==='paid',mode=d.accessMode||'open';
 const r=[
 [t('紹介ページ','Listing page'),priv?t('非公開です。一覧・検索には出さず、あなたと許可した登録ユーザーだけに見せます。','Private: absent from listings and search; visible only to you and approved registered users.'):t('公開です。誰でも紹介ページを見られます。これだけではコードは公開されません。','Public: anyone can see the description. This alone does not reveal the code.')],
 [t('コード','Source code'),mode==='open'?t('利用条件を満たした人にコードを渡します。改変・再配布の可否は、別に指定した利用条件で決まります。','Eligible users receive readable code. Modification and redistribution follow the separately stated terms.'):mode==='invite-only'?t('コードは渡しません。あなたが許可した人だけが作品を使えます。','No source is delivered. Only people you approve can use the work.'):t('コードは渡しません。利用条件を満たした人が、コードを見ずに作品を使います。','No source is delivered. Eligible users use the work without seeing its code.')],
 [t('利用できる人','Who may use it'),paid?(mode==='invite-only'||priv?t('メール確認済みで、あなたの許可と有効な月額契約の両方がある人です。支払いだけでは使えません。','Email-verified users need BOTH your approval and an active monthly subscription. Payment alone is not enough.'):t('メール確認済みで、入金確認後の月額利用期間が有効な人です。','Email-verified users with an active monthly period following confirmed payment.')):(mode==='invite-only'||priv?t('メール確認済みで、あなたが許可した人です。無料でも登録は必要です。','Email-verified users whom you approve. Free access still requires registration.'):t('メール登録と本人確認が済んだ人です。作品の代金はかかりません。','Users who have registered and verified their email. The work has no charge.'))],
 ];
 if(paid){const n=amount(d.price);r.push([t('月額と取り分','Price and split'),n!==null&&n>0n?t('1人あたり月額 '+money(n)+'。販売者 '+money(n-n/5n)+' ／ BSV手数料 '+money(n/5n)+'。','Per user per month: '+money(n)+'. Seller '+money(n-n/5n)+' / BSV fee '+money(n/5n)+'.'):t('月額を入力してください。売上の80%が販売者、20%がBSVです。','Enter a monthly price. The seller receives 80%; BSV receives 20%.')]);
 r.push([t('支払い・期間','Payment and period'),t('USDT・TRC20のみ。入金確認から30日間。継続には毎回支払いが必要で、自動引き落としではありません。','USDT on TRC20 only. Each confirmed payment grants 30 days. Continuing requires another payment; there is no automatic debit.')]);
 }else r.push([t('料金','Price'),t('無料です。作品代金は0。メール登録と本人確認は必要です。','Free: no charge for the work. Email registration and verification are required.')]);
 return r;
}
function fill(node,data){
 node.replaceChildren();const dl=document.createElement('dl');dl.className='plain-dl';
 for(const [label,value] of rows(data)){const line=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;line.append(dt,dd);dl.append(line);}node.append(dl);
}
function update(){
 document.querySelectorAll('[data-label-ja]').forEach(x=>{x.textContent=x.getAttribute(ja()?'data-label-ja':'data-label-en');});
 document.querySelectorAll('[data-placeholder-ja]').forEach(x=>{x.placeholder=x.getAttribute(ja()?'data-placeholder-ja':'data-placeholder-en');});
 const node=$('#selection-body'),form=$('#publish-form');
 if(node&&form)fill(node,{visibility:form.elements.namedItem('visibility')?.value,accessMode:form.elements.namedItem('accessMode')?.value,mode:form.elements.namedItem('mode')?.value,price:form.elements.namedItem('price')?.value});
}
function customer(d){
 const box=document.createElement('div');box.className='customer-guide';
 const mode=d.accessMode||'open',paid=d.mode==='paid';
 const lines=[mode==='invite-only'?t('この作品は招待制です。コードは非公開で、作者が許可した人だけ利用できます。','This work is invite-only. Its source stays hidden and the author must approve your access.'):mode==='protected'?t('この作品はソース保護です。作品は使えますが、コードを見る・取得することはできません。','This work is source-protected. It can be used, but its code cannot be viewed or downloaded.'):t('この作品はソース公開です。利用条件を確認したうえで、コードを取得して対応ソフトに入れて使います。','This work supplies readable source. Check its terms, get the code and install it in the listed software.')];
 lines.push(t('無料・有料にかかわらず、メール登録と本人確認が必要です。','Verified email registration is required for both free and paid use.'));
 if(paid)lines.push(t('買い切りではありません。入金確認から30日間の月額契約です。継続する場合はその都度支払いが必要で、自動引き落としはありません。','This is not a one-time purchase. A monthly period lasts 30 days from payment confirmation. Continuing requires another payment; there is no automatic debit.'));
 if(mode==='invite-only')lines.push(paid?t('支払いだけでは利用できません。購入前に作者の許可も確認してください。','Payment alone does not grant access. Confirm author approval before paying.'):t('作者の許可が必要です。無料でも、誰でもすぐ使える設定ではありません。','Author approval is required. Free does not mean open access to everyone.'));
 for(const text of lines){const p=document.createElement('p');p.textContent=text;box.append(p);}
 const link=document.createElement('a');link.className='text-link';link.href='/trading/guide/';link.textContent=t('利用条件・支払い・更新の説明を見る','Read the guide to access, payment and renewal');box.append(link);return box;
}
window.TradersClarity=Object.freeze({fill,rows,customer,update});
function start(){update();$('#publish-form')?.addEventListener('input',update);$('#publish-form')?.addEventListener('change',()=>queueMicrotask(update));new MutationObserver(update).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
