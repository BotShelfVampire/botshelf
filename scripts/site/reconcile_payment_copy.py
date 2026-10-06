#!/usr/bin/env python3
"""#4 6017081899 item 5: reconcile the shop-rental (Gold Session Desk / Switchboard) payment-confirmation copy with
the implementation. Copy only — payment logic, prices, wallets and auth are untouched.

How it actually works (netlify/functions/_lib): checkout creates a server order; the buyer submits the txid
(POST /payment/submit) and the page immediately asks the server to verify (POST /payment/verify). The server looks
the transaction up on the TRON chain (paymentVerifier.TronVerifier via Tronscan) and checks network, token,
destination, amount and confirmation. Match -> CONFIRMED / ACTIVE, and a license key is issued for these products:
shown on the checkout screen, in My purchases, and in the "payment confirmed" email. No match yet (not confirmed,
provider error) -> the order stays in payment review; the buyer can press Check verification again and the Desk
can confirm or reject it (operator endpoints). The optional Netlify txid form (txid-sent.html) is a notice only and
is left as is. Seller payouts stay manual (unchanged copy).

Idempotent exact-string replacements; --check fails if any old wording is still present."""
import argparse, pathlib, sys

EN = "the server checks the TRON chain automatically (SUBMITTED → VERIFYING → ACTIVE); if it cannot confirm yet, the Desk reviews it"
JA = "サーバーが TRON のチェーンを自動で確認します（SUBMITTED → VERIFYING → ACTIVE）。まだ確認できないときは Desk が確認します"

R = {
 "paid-gold-session-desk.html": [
  ("<li>2. Server checks the chain: SUBMITTED → VERIFYING → ACTIVE. Then use the key from My purchases.</li>",
   "<li>2. The server checks the TRON chain automatically: SUBMITTED → VERIFYING → ACTIVE. If it cannot confirm yet, the Desk reviews it. Your key appears on checkout, in My purchases and in the confirmation email.</li>"),
  ("<li>1. checkout で <strong>300 USDT TRC20</strong> を送り、txid を貼る（通知のみ）。</li>",
   "<li>1. checkout で <strong>300 USDT TRC20</strong> を送り、サーバー注文に txid を提出する。</li>"),
  ("<li>2. Desk が Tronscan を手で確認（自動ではない）。通ったらメールで鍵が届く。</li>",
   "<li>2. サーバーが TRON のチェーンを自動で確認：SUBMITTED → VERIFYING → ACTIVE。まだ確認できないときは Desk が確認する。鍵は checkout 画面・My purchases・確認メールに出る。</li>"),
  ("<li>2. Submit the txid to the server order. SUBMITTED → VERIFYING → ACTIVE. Then use the key from My purchases.</li>",
   "<li>2. Submit the txid to the server order; " + EN + ". Your key appears on checkout, in My purchases and in the confirmation email.</li>"),
  ("<li>1. checkout で <strong>USDT TRC20 の 300</strong> を払い、txid を貼る。カード不可。</li>",
   "<li>1. checkout で <strong>USDT TRC20 の 300</strong> を払い、サーバー注文に txid を提出する。カード不可。</li>"),
  ("<li>2. Desk が txid を手作業で確認。通ったら鍵が届く。</li>",
   "<li>2. " + JA + "。鍵は checkout 画面・My purchases・確認メールに出ます。</li>"),
 ],
 "gold-session-run.html": [
  ("<li>txid 通知だけでは開きません。Desk が手確認後にメールで鍵を送ります（自動ではありません）。</li>",
   "<li>checkout でサーバー注文に txid を提出すると、" + JA + "。確認が済むと鍵が checkout 画面・My purchases・確認メールに出ます（txid フォームの控えだけでは開きません）。</li>"),
  ("checkout で 300 USDT TRC20 → txid 通知 → Desk 手確認メール後に再試行。",
   "checkout で 300 USDT TRC20 → サーバー注文に txid を提出 → ACTIVE になったら My purchases の鍵で再試行。"),
 ],
 "trading-gold-morning-3.html": [
  ("Desk confirms after txid review — not automatic. No Verified sales counts.",
   "After you submit the txid, " + EN + ". No Verified sales counts."),
  ("txid 確認後に Desk が手作業で発行（自動ではありません）。Verified 売上数は出しません。",
   "txid を提出すると、" + JA + "。Verified 売上数は出しません。"),
 ],
 "switchboard-cos.html": [
  ("Desk confirms after txid review — not automatic.</p>", "After you submit the txid, " + EN + ".</p>"),
  ("txid 確認後に Desk が手作業で発行します（自動ではありません）。</p>", "txid を提出すると、" + JA + "。</p>"),
 ],
 "gold-analysis-ai-team/index.html": [
  ("Card is not available. Desk confirms after txid review.</div>",
   "Card is not available. After you submit the txid, " + EN + ".</div>"),
  ("checkout with USDT on TRON / TRC20. Desk confirms after txid review. Free Gold Morning 3",
   "checkout with USDT on TRON / TRC20. After you submit the txid, " + EN + ". Free Gold Morning 3"),
  ("with USDT TRC20. Desk confirms after txid review. Free Morning 3",
   "with USDT TRC20. After you submit the txid, " + EN + ". Free Morning 3"),
 ],
 "checkout.html": [
  ("After you send the txid: Desk checks by hand — not automatic. Watch email for the key.",
   "After you submit the txid: " + EN + ". The key appears here, in My purchases and by email."),
  ("txid送信後: Deskが手で確認（自動ではない）。鍵はメール。",
   "txid 提出後: " + JA + "。鍵はこの画面・My purchases・メールに出ます。"),
  ('"labKnow": "TRON / TRC20 の USDT だけ送りました。txid は通知だけ、',
   '"labKnow": "TRON / TRC20 の USDT だけ送りました。アクセスを開くのはサーバー注文（このフォームは控え）、'),
  ("Sé que el txid es aviso, la tienda", "Sé que la orden del servidor es la que da acceso (este formulario es respaldo), la tienda"),
  ("我知道 txid 只是通知，本店", "我知道开通访问的是服务器订单（此表单仅为备份），本店"),
  ("txid는 알림뿐이고, 상점은", "접근을 여는 것은 서버 주문이고(이 양식은 백업), 상점은"),
 ],
 "key.html": [
  ("<li><strong>Expired:</strong> new month = new USDT TRC20 (20 or 300) + new txid notice; Desk extends or grants after verify.</li>",
   "<li><strong>Expired:</strong> pay again through checkout (20 or 300 USDT TRC20) and submit the new txid to the server order; access resumes when the chain check confirms it (early renewal adds 30 days to the current end date).</li>"),
  ("<li><strong>Not automatic:</strong> grant and resend are manual Desk steps. Free teams never need a key.</li>",
   "<li><strong>What is automatic:</strong> the key is issued when the server confirms the payment on the TRON chain. A payment it cannot confirm, and a lost-key resend, are handled by the Desk. Free teams never need a key.</li>"),
  ("<li><strong>支払済み・メール未着:</strong> txid は通知のみ。Desk 手確認メールを待つ（迷惑メールも）。再送金・同じ txid の再送はしない。</li>",
   "<li><strong>支払済み・鍵が見えない:</strong> サインインして My purchases を開く。状態は SUBMITTED → VERIFYING → ACTIVE。まだ確認できないときは Desk が確認します（迷惑メールも確認）。再送金・同じ txid の再送はしない。</li>"),
  ("<li><strong>期限切れ:</strong> 新しい月の USDT TRC20（20 または 300）+ 新しい txid 通知 → Desk が確認後に延長または発行。</li>",
   "<li><strong>期限切れ:</strong> checkout から再度支払い（20 または 300 USDT TRC20）、新しい txid をサーバー注文に提出 → チェーンで確認されると再開（早めの更新は現在の期限 + 30 日）。</li>"),
  ("<li><strong>自動ではない:</strong> 付与も再送も Desk 手作業。無料チームに鍵は不要。</li>",
   "<li><strong>自動のもの:</strong> サーバーが TRON のチェーンで支払いを確認すると鍵が発行されます。確認できない支払いと鍵の再送は Desk が対応します。無料チームに鍵は不要。</li>"),
  ("Gold Session Desk 300 (USDT TRC20). Desk confirms txid by hand.</p>",
   "Gold Session Desk 300 (USDT TRC20). After you submit the txid, " + EN + ".</p>"),
 ],
 "paid.html": [
  ('"p1": "掲載の USDT を TRON / TRC20 で送る（例: Switchboard 20 / Gold Session Desk 300）。カード不可。txid は通知だけ — Desk が手で確認。',
   '"p1": "掲載の USDT を TRON / TRC20 で送る（例: Switchboard 20 / Gold Session Desk 300）。カード不可。txid をサーバー注文に提出（SUBMITTED → VERIFYING → ACTIVE）。'),
  ('"p2t": "2. メールでキーを受け取る"', '"p2t": "2. 鍵を受け取る"'),
  ('"p2": "Desk が txid を手で通したあと（自動ではない）、メールでキーと短いAIチームが届きます。仕事の全文はその短い文の中にはありません。遅いときは迷惑メールも確認。"',
   '"p2": "サーバーがチェーンで確認して ACTIVE になると、My purchases に 30 日の期限と鍵が出ます（確認メールも support@botshelfvampire.com から届きます）。まだ確認できないときは Desk が確認します。仕事の全文は公開の貼り付け文にはありません。"'),
  ("El txid es solo aviso — el Desk confirma a mano.", "Envía el txid a la orden del servidor (SUBMITTED → VERIFYING → ACTIVE)."),
  ('"p2": "Tras la comprobación manual del txid por Desk (no automática), recibes la clave por email y un pegado corto. El trabajo completo no está en ese pegado. Revisa spam si tarda."',
   '"p2": "Cuando el servidor confirma el pago en la cadena TRON (ACTIVE), My purchases muestra la caducidad de 30 días y la clave; también llega un email de confirmación. Si aún no se puede confirmar, el Desk lo revisa. El trabajo completo no está en el pegado público."'),
  ("txid 只是通知 — Desk 人工确认。", "把 txid 提交给服务器订单（SUBMITTED → VERIFYING → ACTIVE）。"),
  ('"p2": "Desk 手工核对 txid 后（非自动）会把密钥发到邮箱，并附短粘贴文。完整工作不在该粘贴里。若慢请查垃圾箱。"',
   '"p2": "服务器在 TRON 链上确认付款（ACTIVE）后，My purchases 显示 30 天到期和密钥，并发送确认邮件。暂时无法确认时由 Desk 复核。完整工作不在公开粘贴里。"'),
  ("txid는 알림뿐 — Desk가 손으로 확인.", "txid를 서버 주문에 제출(SUBMITTED → VERIFYING → ACTIVE)."),
  ('"p2": "Desk가 txid를 손으로 확인한 뒤(자동 아님) 이메일로 키와 짧은 붙여넣기를 보냅니다. 전체 일은 그 붙여넣기에 없습니다. 느리면 스팸함도 확인."',
   '"p2": "서버가 TRON 체인에서 결제를 확인하면(ACTIVE) My purchases에 30일 만료와 키가 표시되고 확인 메일도 옵니다. 아직 확인되지 않으면 Desk가 검토합니다. 전체 일은 공개 붙여넣기에 없습니다."'),
 ],
 "for-buyers.html": [
  ("Gold Session Desk 300 (USDT TRC20). Desk confirms txid by hand.</p>", "Gold Session Desk 300 (USDT TRC20). After you submit the txid, " + EN + ".</p>"),
  ("Gold Session Desk 300（USDT TRC20）。txidはDeskが手で確認。</p>", "Gold Session Desk 300（USDT TRC20）。txid を提出すると、" + JA + "。</p>"),
  ("txid 後に Desk が手確認（自動ではない）。返金なし。", "txid をサーバー注文に提出すると、サーバーが自動で確認（SUBMITTED → VERIFYING → ACTIVE）。返金なし。"),
  ("txid をメールする。Desk が確認してから通す（自動ではない）。カードなし。", "サーバー注文に txid を提出する。" + JA + "。カードなし。"),
  ("Desk confirma tras txid — no automático. Sin reembolsos.", "Tras enviar el txid a la orden, el servidor lo verifica (SUBMITTED → VERIFYING → ACTIVE). Sin reembolsos."),
  ("luego envía el txid por email. Enviar un txid es solo aviso. El pago no se confirma solo.", "luego envía el txid a la orden del servidor. El servidor comprueba la cadena TRON automáticamente; si aún no puede confirmarlo, el Desk lo revisa."),
  ("txid 后 Desk 手审（非自动）。不退款。", "向服务器订单提交 txid 后由服务器自动核验（SUBMITTED → VERIFYING → ACTIVE）。不退款。"),
  ("再邮件发送 txid。发送 txid 只是通知。支付不会自动确认。", "再把 txid 提交给服务器订单。服务器会自动查询 TRON 链；暂时无法确认时由 Desk 复核。"),
  ("txid 후 Desk 수동 확인(자동 아님). 환불 없음.", "서버 주문에 txid를 제출하면 서버가 자동 확인(SUBMITTED → VERIFYING → ACTIVE). 환불 없음."),
  ("txid를 메일로 보냅니다. txid는 알림일 뿐입니다. 결제는 자동 확정되지 않습니다.", "txid를 서버 주문에 제출합니다. 서버가 TRON 체인을 자동으로 확인하고, 아직 확인되지 않으면 Desk가 검토합니다."),
 ],
 "how.html": [
  ("<li><strong>Wait for Desk to confirm</strong> the txid by hand — it is not automatic.</li>",
   "<li><strong>Submit the txid to the server order.</strong> The server checks the TRON chain automatically (SUBMITTED → VERIFYING → ACTIVE). If it cannot confirm yet, the Desk reviews it.</li>"),
  ("<li><strong>Deskがtxidを手作業で確認</strong>するまで待つ（自動ではありません）。</li>",
   "<li><strong>サーバー注文に txid を提出</strong>する。" + JA + "。</li>"),
  ("<li>When confirmed, you get a <strong>key</strong> and a short paste.", "<li>When ACTIVE, your <strong>key</strong> appears on checkout, in My purchases and in the confirmation email, with a short paste."),
  ("<li>確認後、鍵と短い貼り付け文が届く。", "<li>ACTIVE になると、鍵が checkout 画面・My purchases・確認メールに出て、短い貼り付け文も届く。"),
  ("<li>Desk confirms the txid manually. Payment is not “done” just because you sent a txid.</li>",
   "<li>The server checks the txid on the TRON chain (network, token, our address, amount, confirmation). Payment is not “done” just because you sent a txid; if the check cannot confirm it yet, the Desk reviews it.</li>"),
  ("<li>Deskがtxidを手作業で確認します。txidを送っただけでは支払い完了にはなりません。</li>",
   "<li>サーバーが TRON のチェーンで txid を確認します（ネットワーク・トークン・送付先・金額・承認）。txid を送っただけでは支払い完了にはならず、まだ確認できないときは Desk が確認します。</li>"),
 ],
 "about.html": [
  ("<li>After you send USDT, you paste the txid. BotShelf Vampire Desk reviews it by hand.</li>",
   "<li>After you send USDT, you submit the txid; the server checks it on the TRON chain, and BotShelf Vampire Desk reviews any payment it cannot confirm yet.</li>"),
  ("<li>送付後に txid を貼ってもらい、BotShelf Vampire Desk が手作業で確認します。</li>",
   "<li>送付後に txid を提出してもらい、サーバーが TRON のチェーンで確認します。まだ確認できない支払いは BotShelf Vampire Desk が確認します。</li>"),
 ],
 "library/index.html": [
  ("— USDT TRC20, Desk confirms txid by hand.</p>", "— USDT TRC20; after you submit the txid, " + EN + ".</p>"),
  ("USDT TRC20、txid は Desk が手で確認。</p>", "USDT TRC20。txid を提出すると、" + JA + "。</p>"),
  ("(card not available). Desk confirms after txid — not automatic.</p>", "(card not available). After you submit the txid, " + EN + ".</p>"),
  ("（カード不可）。txid 確認後に Desk が手作業で発行（自動ではない）。</p>", "（カード不可）。txid を提出すると、" + JA + "。</p>"),
 ],
 "use-desk.html": [
  ("then paste txid. Key by email after hand-check.</p>", "then submit the txid to the server order. The key appears in My purchases and by email once the chain check confirms it.</p>"),
  ("を払いtxid送付。手確認後に鍵がメール。</p>", "を払い、サーバー注文に txid を提出。チェーンで確認されると鍵が My purchases とメールに出ます。</p>"),
 ],
}
SHARED = [  # identical bridge lines on several pages
 ("Desk confirms txid by hand.</p>", "After you submit the txid, " + EN + ".</p>"),
 ("txidはDeskが手で確認。</p>", "txid を提出すると、" + JA + "。</p>"),
]
SHARED_PAGES = ["contact.html", "sitemap.html", "registered.html", "use-routines.html", "use-media.html", "use-numbers.html", "use-write.html", "use-code.html", "key.html", "library/index.html", "library/mcp/index.html", "library/crewai/index.html", "library/n8n/index.html"]
OLD_MARKERS = ["by hand — it is not automatic", "Desk confirms txid by hand", "Desk confirms after txid review", "Desk checks by hand", "手で確認（自動ではない）", "手作業で確認", "手確認", "txid は通知だけ", "txid は通知のみ", "通知のみ）", "手作業で発行", "Key by email after hand-check", "reviews it by hand", "Desk confirms the txid manually", "grant and resend are manual", "付与も再送も Desk 手作業", "comprobación manual del txid", "Desk 手工核对", "txid 只是通知", "Desk가 손으로", "txid는 알림뿐 —", "Desk confirma a mano", "Desk 수동 확인", "Desk 手审", "Desk confirms after txid", "が手で確認", "Desk が手作業で発行"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", required=True); ap.add_argument("--check", action="store_true")
    a = ap.parse_args(); site = pathlib.Path(a.site); fails = []; changed = 0
    plan = {k: list(v) for k, v in R.items()}
    optional = set()
    for pg in SHARED_PAGES:
        plan.setdefault(pg, []).extend(SHARED); optional.update((pg, o) for o, _ in SHARED)
    for name, reps in plan.items():
        p = site / name; t = p.read_text(); orig = t
        for old, new in reps:
            if a.check:
                if old in t and new not in t: fails.append(f"{name}: old copy still present: {old[:60]}")
                continue
            if new in t and old not in t: continue
            n = t.count(old)
            if n == 0 and (name, old) in optional: continue
            if n == 0: fails.append(f"{name}: anchor not found: {old[:70]}"); continue
            t = t.replace(old, new)
        if t != orig: p.write_text(t); changed += 1
    for name in plan:
        t = (site / name).read_text()
        for m in OLD_MARKERS:
            if m in t: fails.append(f"{name}: legacy wording '{m}'")
    print({"test" if a.check else "pass": "payment_copy", "pages": len(plan), "changed": changed, "failures": len(fails), "fail": fails})
    if fails: sys.exit(1)

if __name__ == "__main__":
    main()
