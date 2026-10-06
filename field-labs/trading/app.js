'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const text = (en, ja) => window.BSVLabs.text(en, ja);
  function num(id) { return Number($(id).value); }
  function render() {
    const equity = num('equity'), riskPct = num('risk_pct'), entry = num('entry'), stop = num('stop');
    const targetRaw = $('target').value.trim();
    const target = targetRaw === '' ? null : Number(targetRaw);
    const side = $('side').value;
    const px = num('tick');
    const stopDist = Math.abs(entry - stop);
    const riskCash = equity * (riskPct / 100);
    let err = null;
    if (!(equity > 0 && riskPct > 0 && px > 0)) err = text('Equity, risk % and $ per price unit must be positive.', '資金・リスク％・価格あたり金額は正の数が必要です。');
    else if (!(stopDist > 0)) err = text('Entry and stop must differ.', 'エントリーと損切りは異なる値にしてください。');
    else if (side === 'long' && !(stop < entry)) err = text('Long: stop should be below entry.', 'ロング：損切りはエントリーより下にしてください。');
    else if (side === 'short' && !(stop > entry)) err = text('Short: stop should be above entry.', 'ショート：損切りはエントリーより上にしてください。');
    else if (target != null && Number.isNaN(target)) err = text('Target must be a number or blank.', '目標は数値か空欄にしてください。');
    else if (target != null && side === 'long' && !(target > entry)) err = text('Long: target should be above entry.', 'ロング：目標はエントリーより上にしてください。');
    else if (target != null && side === 'short' && !(target < entry)) err = text('Short: target should be below entry.', 'ショート：目標はエントリーより下にしてください。');
    if (err) {
      $('result').textContent = err;
      $('export').value = 'ok,0\n';
      return;
    }
    const riskPerUnit = stopDist * px;
    const units = riskCash / riskPerUnit;
    const rewardDist = target == null ? null : Math.abs(target - entry);
    const rMult = rewardDist == null ? null : rewardDist / stopDist;
    const rewardCash = rMult == null ? null : riskCash * rMult;
    const lines = [
      `<strong>${text('Cash at risk', 'リスク金額')}</strong> = ${riskCash.toFixed(2)} (${riskPct}% ${text('of', 'of')} ${equity.toFixed(2)})`,
      `<strong>${text('Stop distance', '損切り幅')}</strong> = ${stopDist.toPrecision(6)} · <strong>${text('Units', '数量')}</strong> ≈ ${units.toPrecision(6)}`,
      `<strong>${text('$ risk per unit', '1単位あたりリスク')}</strong> = ${riskPerUnit.toPrecision(6)}`,
    ];
    if (rMult != null) {
      lines.push(`<strong>R</strong> ≈ ${rMult.toFixed(3)} · <strong>${text('Reward if target hits', '目標到達時の利益')}</strong> ≈ ${rewardCash.toFixed(2)}`);
    } else {
      lines.push(text('Add a target to see R-multiple.', '目標を入れるとR倍数が表示されます。'));
    }
    lines.push(`<span class="muted">${text('Illustrative only. Broker lot/contract steps and margin are not applied.', '説明用です。ブローカーのロット刻み・証拠金は未適用です。')}</span>`);
    $('result').innerHTML = lines.join('<br>');
    const row = {
      side, equity, risk_pct: riskPct, entry, stop, target: target == null ? '' : target,
      dollars_per_price_unit: px, stop_distance: stopDist, cash_at_risk: riskCash,
      units, r_multiple: rMult == null ? '' : rMult, reward_if_target: rewardCash == null ? '' : rewardCash,
    };
    const keys = Object.keys(row);
    $('export').value = [keys.join(','), keys.map((k) => row[k]).join(',')].join('\n');
    $('status').textContent = text('Sized in-browser. Nothing was sent to a server.', 'ブラウザ内で計算しました。サーバー送信はありません。');
  }
  $('solve').addEventListener('click', render);
  ['equity', 'risk_pct', 'entry', 'stop', 'target', 'side', 'tick'].forEach((id) => $(id).addEventListener('input', render));
  $('example').addEventListener('click', () => {
    $('equity').value = 10000; $('risk_pct').value = 1; $('side').value = 'long';
    $('tick').value = 1; $('entry').value = 100; $('stop').value = 98; $('target').value = 106;
    render();
  });
  $('copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('export').value); $('status').textContent = text('CSV copied.', 'CSVをコピーしました。'); }
    catch { $('export').select(); }
  });
  $('download').addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([$('export').value], { type: 'text/csv' }));
    a.download = 'bsv-risk-plan.csv'; a.click();
  });
  document.addEventListener('bsv:language', render);
  render();
})();
