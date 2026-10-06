'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const text = (en, ja) => window.BSVLabs.text(en, ja);
  const SAMPLE = $('pack').value;
  function estimate(s) {
    const chars = [...s].length;
    const bytes = new TextEncoder().encode(s).length;
    const words = (s.trim().match(/\S+/g) || []).length;
    const lines = s.length ? s.split(/\n/).length : 0;
    // Dual heuristic: chars/4 (Latin-heavy) and bytes/3 (UTF-8 denser scripts). Take max as planning floor.
    const tLatin = Math.ceil(chars / 4);
    const tDense = Math.ceil(bytes / 3);
    const tokens = Math.max(tLatin, tDense);
    return { chars, bytes, words, lines, tLatin, tDense, tokens };
  }
  function render() {
    const pack = $('pack').value;
    const windowTok = Number($('window').value);
    const reserve = Number($('reserve').value);
    const e = estimate(pack);
    const replyBudget = Math.floor(windowTok * (reserve / 100));
    const inputBudget = windowTok - replyBudget;
    const fill = inputBudget > 0 ? (e.tokens / inputBudget) * 100 : 0;
    const status = e.tokens <= inputBudget
      ? text('Fits the input budget under this rough estimate.', 'この概算では入力枠に収まります。')
      : text('Over the input budget — trim notes or pick a larger window.', '入力枠を超えています。メモを削るか、より大きい枠を選んでください。');
    $('result').innerHTML = [
      `<strong>${text('Rough tokens', 'おおよそのトークン')}</strong> ≈ ${e.tokens.toLocaleString()} ` +
        `<span class="muted">(${text('latin heuristic', '英数字寄り')} ${e.tLatin.toLocaleString()} · ${text('dense heuristic', '高密度寄り')} ${e.tDense.toLocaleString()})</span>`,
      `${text('Characters', '文字数')} ${e.chars.toLocaleString()} · ${text('UTF-8 bytes', 'UTF-8バイト')} ${e.bytes.toLocaleString()} · ${text('words', '語')} ${e.words.toLocaleString()} · ${text('lines', '行')} ${e.lines}`,
      `${text('Window', '枠')} ${windowTok.toLocaleString()} · ${text('reserved for reply', '返答用')} ${replyBudget.toLocaleString()} (${reserve}%) · ${text('input budget', '入力枠')} ${inputBudget.toLocaleString()}`,
      `<strong>${text('Fill of input budget', '入力枠の使用率')}</strong> ≈ ${fill.toFixed(1)}%`,
      status,
    ].join('<br>');
    const row = {
      rough_tokens: e.tokens, tokens_latin_chars_div4: e.tLatin, tokens_dense_bytes_div3: e.tDense,
      characters: e.chars, utf8_bytes: e.bytes, words: e.words, lines: e.lines,
      window_tokens: windowTok, reserve_pct: reserve, reply_budget_tokens: replyBudget,
      input_budget_tokens: inputBudget, fill_pct: Number(fill.toFixed(2)),
      fits_input_budget: e.tokens <= inputBudget ? 1 : 0,
    };
    const keys = Object.keys(row);
    $('export').value = [keys.join(','), keys.map((k) => row[k]).join(',')].join('\n');
    $('status').textContent = text('Estimated in-browser. Nothing was sent to a model API.', 'ブラウザ内で見積もりました。モデルAPIへの送信はありません。');
  }
  $('run').addEventListener('click', render);
  ['pack', 'window', 'reserve'].forEach((id) => $(id).addEventListener('input', render));
  $('example').addEventListener('click', () => { $('pack').value = SAMPLE; render(); });
  $('copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('export').value); $('status').textContent = text('CSV copied.', 'CSVをコピーしました。'); }
    catch { $('export').select(); }
  });
  $('download').addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([$('export').value], { type: 'text/csv' }));
    a.download = 'bsv-context-budget.csv'; a.click();
  });
  document.addEventListener('bsv:language', render);
  render();
})();
