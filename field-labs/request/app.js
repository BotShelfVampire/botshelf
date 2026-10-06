'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const text = (en, ja) => window.BSVLabs.text(en, ja);
  const SAMPLE = { job: $('job').value, area: $('area').value, platforms: $('platforms').value, inputs: $('inputs').value, outputs: $('outputs').value };
  function score() {
    const job = $('job').value.trim();
    const area = $('area').value;
    const platforms = $('platforms').value.trim();
    const inputs = $('inputs').value.trim();
    const outputs = $('outputs').value.trim();
    const checks = [];
    let pts = 0;
    const len = job.length;
    if (len >= 20 && len <= 2000) { pts += 25; checks.push(text('Job length OK (20–2000).', '仕事内容の文字数OK（20〜2000）。')); }
    else if (len < 20) checks.push(text('Job is shorter than 20 characters.', '仕事内容が20文字未満です。'));
    else checks.push(text('Job exceeds 2000 characters — trim it.', '仕事内容が2000文字を超えています。短くしてください。'));
    if (/\b(input|output|csv|json|api|file|chart|workflow|indicator|ea|bot|ros|dataset)\b/i.test(job) || /入力|出力|ファイル|チャート|ワークフロー/.test(job)) {
      pts += 15; checks.push(text('Mentions a concrete artifact or surface.', '具体的な成果物・画面に触れています。'));
    } else checks.push(text('Name an artifact (file, chart, API, indicator…).', '成果物（ファイル・チャート・API・インジケーターなど）を書いてください。'));
    if (area) { pts += 15; checks.push(text('Area selected.', '分野が選ばれています。')); }
    if (platforms) { pts += 15; checks.push(text('Platform / runtime stated.', 'プラットフォームが書かれています。')); }
    else checks.push(text('Add a platform (n8n, TradingView, MT5…).', 'プラットフォームを追加（n8n、TradingView、MT5など）。'));
    if (inputs) { pts += 15; checks.push(text('Inputs filled.', '入力あり。')); }
    else checks.push(text('Say what the builder receives.', '作り手が受け取る入力を書いてください。'));
    if (outputs) { pts += 15; checks.push(text('Outputs filled.', '出力あり。')); }
    else checks.push(text('Say what success looks like.', '成功時の出力を書いてください。'));
    if (!/\b(asap|guaranteed|profit|passive income)\b/i.test(job) && !/必ず儲か|保証|必ず稼/.test(job)) {
      pts += 0; // already full path without this; keep soft
    } else {
      pts = Math.max(0, pts - 20);
      checks.push(text('Avoid guarantee / profit claims — Request Market is not escrow.', '保証・収益表現は避けてください（エスクローではありません）。'));
    }
    pts = Math.min(100, pts);
    const clean = [
      job,
      '',
      text('Area:', '分野:') + ' ' + area,
      platforms ? (text('Platform:', 'プラットフォーム:') + ' ' + platforms) : null,
      inputs ? (text('Inputs:', '入力:') + ' ' + inputs) : null,
      outputs ? (text('Outputs:', '出力:') + ' ' + outputs) : null,
      '',
      text('Note: draft from BSV Request draft lab — paste into /requests/#new after email verify. No escrow.',
           '注: BSVリクエスト下書きラボからの清書。メール確認後に /requests/#new へ貼り付け。エスクローなし。'),
    ].filter((x) => x !== null).join('\n');
    $('clean').value = clean;
    $('result').innerHTML = [
      `<strong>${text('Completeness', '完成度')}</strong> ${pts}/100`,
      checks.map((c) => `• ${c}`).join('<br>'),
      pts >= 80
        ? text('Ready to paste into Request Market.', 'Request Market に貼れる水準です。')
        : text('Raise the score before sending — builders need a clear job.', '送信前にスコアを上げてください。作り手には明確な仕事内容が必要です。'),
    ].join('<br>');
    const row = { score: pts, job_chars: len, area, platforms, inputs: inputs || '', outputs: outputs || '' };
    const keys = Object.keys(row);
    $('export').value = [keys.join(','), keys.map((k) => JSON.stringify(String(row[k]))).join(',')].join('\n');
    $('status').textContent = text('Scored in-browser. Nothing was submitted.', 'ブラウザ内で採点しました。送信はしていません。');
    try {
      sessionStorage.setItem('bsv-rq-draft', JSON.stringify({ job, area, platforms, inputs, outputs, clean, score: pts }));
    } catch (_) {}
  }
  $('score').addEventListener('click', score);
  ['job', 'area', 'platforms', 'inputs', 'outputs'].forEach((id) => $(id).addEventListener('input', score));
  $('example').addEventListener('click', () => {
    $('job').value = SAMPLE.job; $('area').value = SAMPLE.area; $('platforms').value = SAMPLE.platforms;
    $('inputs').value = SAMPLE.inputs; $('outputs').value = SAMPLE.outputs; score();
  });
  $('copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('clean').value); $('status').textContent = text('Cleaned job copied.', '清書をコピーしました。'); }
    catch { $('clean').select(); }
  });
  document.addEventListener('bsv:language', score);
  score();
})();
