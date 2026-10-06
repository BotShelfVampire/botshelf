(function () {
  'use strict';
  const SYNTHETIC_CSV = 'sample_id,group,feature_a,feature_b,feature_c\nS01,A,4,8,2\nS02,A,6,10,4\nS03,A,8,12,6\nS04,B,10,14,8\nS05,B,12,16,10\nS06,B,14,NA,12\n';
  const SYNTHETIC_SHA256 = '6a25ca0e4007c6bb37ca0e92f67c8cf1f56294df220ff419643beecb8aa31b45';
  const fields = [
    { key: 'dataset', label: ['Dataset and observation unit', 'データセットと観測単位'], next: ['Record the dataset name and what one row or sample represents.', 'データセット名と、1 行または 1 試料が何を表すかを記録します。'] },
    { key: 'version', label: ['Version, date, and file', '版・日付・ファイル'], next: ['Add the exact filename and a release/version or retrieval date; replace “latest” with a frozen reference.', '正確なファイル名と版または取得日を記入。「最新版」は固定した参照に置き換えます。'] },
    { key: 'license', label: ['Reuse terms and source', '再利用条件と確認元'], next: ['Locate the dataset-specific terms and record the source. Keep unresolved conditions explicit.', 'データセット固有の条件を調べ、確認元を記録。未確認の条件は明示します。'] },
    { key: 'accession', label: ['Persistent identifier', '永続的な識別子'], next: ['Record a study accession, DOI, or persistent record URL and its repository. Label local synthetic IDs as such.', '研究番号・DOI・永続 URL とリポジトリを記録。ローカルな合成データの ID はその旨を明示します。'] },
    { key: 'checksum', label: ['SHA-256', 'SHA-256'], next: ['Calculate the SHA-256 of the exact file and record 64 hexadecimal characters. Keep the original filename alongside it.', '対象ファイルの SHA-256 を計算し、16 進数 64 文字で記録。元のファイル名も合わせて残します。'] },
    { key: 'missingness', label: ['Missingness and handling', '欠損と処理'], next: ['Give missing counts and denominators, including zero if none; describe the affected variables/groups and handling rule.', '欠損件数と分母（欠損がなければ 0）、影響する変数・群、処理規則を記入します。'] },
    { key: 'method', label: ['Method and replay details', '方法と再実行の詳細'], next: ['Record transformations, exclusions, parameters, software/code versions, seed if relevant, and expected output.', '変換・除外・パラメータ・ソフトウェアとコードの版・必要な乱数種・期待出力を記録します。'] }
  ];
  function example(lang) {
    const ja = lang === 'ja';
    return {
      dataset: ja ? 'BSV 合成測定表：6 行 × 3 特徴。1 行は架空の観測。生物学的データではない。' : 'BSV synthetic measurement table: 6 rows × 3 features; one invented observation per row; not biological data.',
      version: ja ? 'v1、作成日 2026-10-06、toy-expression-v1.csv、UTF-8、LF 改行、末尾改行あり' : 'v1; generated 2026-10-06; toy-expression-v1.csv; UTF-8; LF line endings; final newline present',
      license: ja ? '付属する BSV 合成 CSV は CC0 1.0。本ページの合成データ節と https://creativecommons.org/publicdomain/zero/1.0/ を参照。' : 'Included BSV synthetic CSV: CC0 1.0. Source: this page’s synthetic example section and https://creativecommons.org/publicdomain/zero/1.0/',
      accession: ja ? 'BSV-TOY-001（本ページ内の合成データ ID。外部リポジトリの研究番号ではない）' : 'BSV-TOY-001 (local synthetic example ID on this page; not a repository accession)',
      checksum: SYNTHETIC_SHA256,
      missingness: ja ? '測定値 18 個中 1 個が欠損（5.56%）。feature_b の S06、B 群。例示計算では feature_b が NA の行を除外。6 行中 1 行を除外（16.67%）、残りは A 群 3 行、B 群 2 行。補完なし。' : '1 / 18 measurement cells missing (5.56%): feature_b for S06 in group B. For the illustrative calculation, exclude rows with NA in feature_b: 1 / 6 rows removed (16.67%); remaining groups A = 3, B = 2. No imputation.',
      method: ja ? '実行仕様 v1：UTF-8 CSV を読み込み、文字列 NA を欠損として扱う。feature_b が欠損の行を除外し、group ごとに feature_a/b/c の算術平均を求める。正規化・変換・重み付け・仮説検定なし。期待する平均は A = 6/10/4、B = 11/15/9。出力は群別件数と 3 特徴の平均。乱数なし、seed は非該当。再実行の実装、実際のソフトウェアとコードの版は未確認。再実行時に追記する。' : 'Replay specification v1: read UTF-8 CSV and interpret literal NA as missing. Exclude rows missing feature_b. Compute arithmetic means of feature_a/b/c within group. No normalization, transformation, weighting, or hypothesis tests. Expected means: A = 6/10/4; B = 11/15/9. Output group counts and three feature means. Deterministic; seed not applicable. Replay implementation and actual software/code versions: unresolved. Add these when replayed.'
    };
  }
  function assessRecord(input, lang) {
    const j = lang === 'ja' ? 1 : 0;
    const t = (en, ja) => [en, ja][j];
    const normalized = {};
    const gaps = [];
    let filled = 0;
    for (const field of fields) {
      const value = String(input[field.key] || '').trim();
      normalized[field.key] = value;
      if (value) filled++;
      let reason = '';
      if (!value) reason = t('Not recorded.', '未記入です。');
      else if (field.key === 'checksum' && !/^[a-f0-9]{64}$/i.test(value)) reason = t('Not a 64-character SHA-256 hexadecimal value.', 'SHA-256 の 16 進数 64 文字の形式ではありません。');
      else if (field.key === 'version' && /\blatest\b|最新版|最新のみ/i.test(value)) reason = t('The version includes a moving “latest” reference.', '「最新版」という変化する参照が含まれています。');
      else if (/\b(unknown|unresolved|tbd|not recorded)\b|未確認|未定|不明/i.test(value)) reason = t('Contains an unresolved marker.', '未確定を示す記述が含まれています。');
      else if (field.key === 'missingness' && !/[0-9０-９]/.test(value)) reason = t('No numeric count or denominator was detected.', '件数・分母の数値が見当たりません。');
      if (reason) gaps.push({ key: field.key, label: field.label[j], reason, next: field.next[j] });
    }
    const lines = [
      t('BSV PUBLIC DATA — REPRODUCIBILITY RECORD', 'BSV 公開データ — 再現性記録'),
      t('Status: self-reported worksheet; no repository, license, file origin, or analysis result has been independently verified.', '状態：記入者による記録。リポジトリ・再利用条件・ファイルの出所・分析結果は独立に検証していません。'), '',
      ...fields.flatMap(field => [`${field.label[j].toUpperCase()}`, normalized[field.key] || t('[not recorded]', '[未記入]'), '']),
      t('AUTOMATIC FIELD CHECK', '入力項目の自動確認'),
      `${filled} / ${fields.length} ${t('fields have text.', '項目に記入あり。')}`,
      ...(gaps.length ? gaps.map(gap => `- ${gap.label}: ${gap.reason} ${gap.next}`) : [t('- No empty fields, unresolved markers, or hash-format gaps detected. This is not a successful replay or a quality rating.', '- 空欄・未確定表記・ハッシュ形式の不足は検出されませんでした。再実行の成功や品質を判定する結果ではありません。')]), '',
      t('HANDOFF CHECK — COMPLETE AFTER REPLAY', '引き継ぎ確認 — 再実行後に記入'),
      t('1. Locate the exact input file and confirm the recorded hash matches. Preserve raw data separately from derived files.', '1. 対象ファイルを特定し、記録したハッシュと一致するか確認。元データと加工ファイルを分けて保管。'),
      t('2. Review the recorded reuse/access conditions and the variable dictionary, including units and missing-value codes.', '2. 記録した再利用・アクセス条件と、単位・欠損コードを含む変数辞書を確認。'),
      t('3. Run a small replay with recorded software/code versions. Compare expected and observed output, with a stated numerical tolerance if relevant.', '3. ソフトウェア・コードの版を記録して小さく再実行。必要な数値許容差を明示し、期待値と実測出力を比較。'),
      t('Replay date / reviewer role: [record]', '再実行日／確認担当の役割：[記入]'),
      t('Actual software, environment, and code version: [record]', '実際のソフトウェア・環境・コード版：[記入]'),
      t('Observed output and differences: [record]', '得られた出力と差分：[記入]'),
      t('Decision and remaining limitations: [record]', '判断と残る制約：[記入]')
    ];
    return { text: lines.join('\n'), filled, gaps, normalized };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { assessRecord, example, SYNTHETIC_CSV, SYNTHETIC_SHA256 };
  if (typeof document === 'undefined') return;
  const form = document.getElementById('worksheet-form');
  if (!form) return;
  const output = document.getElementById('record-output');
  const status = document.getElementById('record-status');
  const hashStatus = document.getElementById('hash-status');
  const lang = () => window.BSVLabs ? window.BSVLabs.lang() : 'en';
  const text = (en, ja) => lang() === 'ja' ? ja : en;
  let manuallyEdited = false;
  let inputsChanged = false;
  let exampleLoaded = true;
  let hashJob = 0;
  const placeholders = {
    dataset: ['e.g. public expression matrix; one sample per row', '例：公開発現行列。1 行が 1 試料。'],
    version: ['Release/date + filename; avoid “latest”', '版・日付とファイル名。「最新版」のみは避ける。'],
    license: ['Dataset-specific terms + source; write unresolved if unknown', 'データセット固有の条件と確認元。不明なら「未確認」。'],
    accession: ['Record ID and repository; distinguish study from sample IDs', '記録 ID とリポジトリ。研究 ID と試料 ID を区別。'],
    checksum: ['64 hexadecimal characters', '16 進数 64 文字'],
    missingness: ['Missing cells / measured cells, by variable and group; handling rule', '欠損数／測定値数、変数・群別の状況、処理規則。'],
    method: ['Transformations → analysis → output; versions; seed or not applicable', '変換 → 分析 → 出力。各種の版。乱数種または非該当。']
  };
  function localize() {
    Object.entries(placeholders).forEach(([id, labels]) => { document.getElementById(id).placeholder = labels[lang() === 'ja' ? 1 : 0]; });
  }
  function read() {
    return Object.fromEntries(fields.map(field => [field.key, form.elements[field.key].value]));
  }
  function generate() {
    const record = assessRecord(read(), lang());
    output.value = record.text;
    document.getElementById('record-summary').textContent = `${record.filled} / 7 ${text('fields recorded', '項目に記入あり')} · ${record.gaps.length} ${text('field gaps. ', '項目の不足。')}${text('Presence and format checks only; replay is still needed.', '記入と形式の確認です。再実行の検証は別途必要です。')}`;
    const list = document.getElementById('record-gaps'); list.replaceChildren();
    record.gaps.forEach(gap => {
      const card = document.createElement('article'); card.className = 'card';
      const heading = document.createElement('h3'); heading.textContent = gap.label;
      const paragraph = document.createElement('p'); paragraph.textContent = `${gap.reason} ${gap.next}`;
      card.append(heading, paragraph); list.appendChild(card);
    });
    if (!record.gaps.length) {
      const paragraph = document.createElement('p'); paragraph.className = 'muted';
      paragraph.textContent = text('Next: replay one small result and fill in the actual software versions and observed output at the end of the record.', '次は小さな結果を再実行し、記録の末尾に実際のソフトウェアの版と得られた出力を記入してください。'); list.appendChild(paragraph);
    }
    status.textContent = text('Record created. Edit it before copying or saving.', '記録を作成しました。コピー・保存前に編集できます。');
    manuallyEdited = false; inputsChanged = false;
  }
  function loadExample() {
    const data = example(lang());
    fields.forEach(field => { form.elements[field.key].value = data[field.key]; });
    document.getElementById('hash-file').value = '';
    hashJob++;
    hashStatus.textContent = text('The example hash matches the exact downloadable CSV, including its final newline.', '例のハッシュは、末尾の改行を含むダウンロード用 CSV と一致します。');
    exampleLoaded = true; generate();
  }
  function changed() {
    inputsChanged = true; exampleLoaded = false;
    status.textContent = text('Inputs changed. Build a new record to apply them; your current draft is preserved.', '入力を変更しました。反映するには記録を再作成してください。現在の本文は保持しています。');
  }
  async function hashFile(event) {
    const job = ++hashJob;
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 20 * 1024 * 1024) { hashStatus.textContent = text('Choose a file no larger than 20 MB for this local calculation. The existing hash was kept.', '計算対象は 20 MB 以下のファイルにしてください。既存のハッシュは保持しています。'); return; }
    hashStatus.textContent = text('Calculating locally…', 'ブラウザ内で計算中…');
    try {
      const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
      if (job !== hashJob) return;
      form.elements.checksum.value = Array.from(new Uint8Array(digest)).map(byte => byte.toString(16).padStart(2, '0')).join('');
      hashStatus.textContent = `${file.name} · ${file.size.toLocaleString()} ${text('bytes. Hash filled in. Add this exact filename to the version field, then rebuild the record.', 'バイト。ハッシュを入力しました。このファイル名を版の欄に記入し、記録を再作成してください。')}`;
      changed();
    } catch (_) {
      if (job === hashJob) hashStatus.textContent = text('Local hashing is unavailable in this browser context. You can paste a SHA-256 calculated elsewhere; the existing value was kept.', 'この環境ではローカル計算を利用できません。別途計算した SHA-256 を貼り付けられます。既存の値は保持しています。');
    }
  }
  async function copy() {
    try { await navigator.clipboard.writeText(output.value); status.textContent = text('Record copied.', '記録をコピーしました。'); }
    catch (_) { output.focus(); output.select(); status.textContent = text('The record is selected. Use your browser’s Copy command.', '本文を選択しました。ブラウザのコピー操作で取得してください。'); }
  }
  function download(content, filename, type) {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const link = document.createElement('a'); link.href = url; link.download = filename;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  form.addEventListener('submit', event => { event.preventDefault(); generate(); });
  form.addEventListener('input', changed);
  output.addEventListener('input', () => { manuallyEdited = true; status.textContent = text('Manual edits are included when you copy or download.', '手動の編集はコピー・ダウンロードに含まれます。'); });
  document.getElementById('hash-file').addEventListener('change', hashFile);
  document.getElementById('load-example').addEventListener('click', loadExample);
  document.getElementById('copy-record').addEventListener('click', copy);
  document.getElementById('download-record').addEventListener('click', () => { download(output.value, `bsv-reproducibility-${lang()}.txt`, 'text/plain;charset=utf-8'); status.textContent = text('Record download prepared.', '記録のダウンロードを開始しました。'); });
  document.getElementById('download-synthetic').addEventListener('click', () => { download(SYNTHETIC_CSV, 'toy-expression-v1.csv', 'text/csv;charset=utf-8'); status.textContent = text('Synthetic CSV download prepared.', '合成 CSV のダウンロードを開始しました。'); });
  document.addEventListener('bsv:language', () => {
    localize();
    if (manuallyEdited || inputsChanged) status.textContent = text('Your draft is preserved. Build again to create an English record.', '編集中の本文を保持しました。日本語の記録を作る場合は再作成してください。');
    else if (exampleLoaded) loadExample();
    else generate();
  });
  localize(); loadExample();
})();
