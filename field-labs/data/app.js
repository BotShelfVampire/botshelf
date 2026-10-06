'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const text = (en, ja) => window.BSVLabs.text(en, ja);
  const SAMPLE = $('csv').value;
  function parseCsv(text) {
    const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim().split('\n').filter(Boolean);
    if (lines.length < 2) throw new Error('need header + row');
    const split = (line) => {
      const out = []; let cur = '', q = false;
      for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') { q = !q; continue; }
        if (ch === ',' && !q) { out.push(cur); cur = ''; continue; }
        cur += ch;
      }
      out.push(cur); return out;
    };
    const cols = split(lines[0]);
    const rows = lines.slice(1).map(split);
    return { cols, rows };
  }
  function isFloat(s) { if (s === '' || s == null) return false; return !Number.isNaN(Number(s)); }
  function profile() {
    let parsed;
    try { parsed = parseCsv($('csv').value); $('status').textContent = ''; }
    catch (e) { $('status').textContent = text('Could not parse CSV (need a header and at least one row).', 'CSVを読めません（ヘッダと1行以上が必要）。'); return; }
    const { cols, rows } = parsed;
    const body = $('table').querySelector('tbody');
    body.replaceChildren();
    const outRows = [];
    cols.forEach((c, i) => {
      const vals = rows.map((r) => (r[i] == null ? '' : String(r[i])));
      const empty = vals.filter((v) => v.trim() === '').length;
      const filled = vals.filter((v) => v.trim() !== '');
      const distinct = new Set(filled).size;
      const numeric = filled.length > 0 && filled.every(isFloat);
      const counts = {};
      filled.forEach((v) => { counts[v] = (counts[v] || 0) + 1; });
      const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([v, n]) => `${JSON.stringify(v)}×${n}`).join(', ');
      const guess = filled.length === 0 ? 'empty' : (numeric ? 'numeric' : 'text');
      const tr = document.createElement('tr');
      [c, String(filled.length), String(empty), String(distinct), guess, top || '—'].forEach((v) => {
        const td = document.createElement('td'); td.textContent = v; tr.append(td);
      });
      body.append(tr);
      outRows.push({ column: c, non_null: filled.length, nulls: empty, distinct, guess, top_values: top });
    });
    const header = 'column,non_null,nulls,distinct,guess,top_values';
    const lines = outRows.map((r) => [r.column, r.non_null, r.nulls, r.distinct, r.guess, JSON.stringify(r.top_values)].join(','));
    $('export').value = [header, ...lines].join('\n');
    $('status').textContent = text(`Profiled ${rows.length} rows × ${cols.length} columns.`, `${rows.length} 行 × ${cols.length} 列をプロフィールしました。`);
  }
  $('run').addEventListener('click', profile);
  $('example').addEventListener('click', () => { $('csv').value = SAMPLE; profile(); });
  $('copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('export').value); $('status').textContent = text('Profile CSV copied.', 'プロフィールCSVをコピーしました。'); }
    catch { $('export').select(); }
  });
  $('download').addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([$('export').value], { type: 'text/csv' }));
    a.download = 'bsv-csv-profile.csv'; a.click();
  });
  document.addEventListener('bsv:language', profile);
  profile();
})();
