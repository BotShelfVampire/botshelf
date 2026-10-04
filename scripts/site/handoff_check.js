/* BSV AI Team Handoff Packet checker (original BSV code, MIT). Checks a filled packet against the packet's own rules,
   in the browser only: nothing is uploaded or stored. It checks structure and wording, not whether the facts are true. */
(function (root) {
  'use strict';
  var SECTIONS = ['JOB', 'SCOPE', 'CURRENT STATE', 'WORK COMPLETED', 'EVIDENCE', 'NEXT ACTION', 'DO NOT REPEAT'];
  var STATUS = ['NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'READY_FOR_REVIEW', 'DONE'];
  var DONE_EVIDENCE = ['source revision', 'check name', 'live URL or artifact', 'verification time'];
  var HEDGE = /\b(probably|presumably|likely|should work|should be fine|i think|i guess|guess(ed)?|maybe|tbd|unknown yet)\b/i;
  function parse(text) {
    var out = { sections: {}, order: [] }, cur = null;
    String(text || '').replace(/\r\n?/g, '\n').split('\n').forEach(function (line) {
      var t = line.trim();
      if (t === '' || t.indexOf('```') === 0) return;
      if (SECTIONS.indexOf(t.toUpperCase()) >= 0 && t === t.toUpperCase()) { cur = t; out.sections[cur] = out.sections[cur] || {}; out.order.push(cur); return; }
      var m = /^-\s*([^:]+):\s*(.*)$/.exec(t);
      if (m && cur) out.sections[cur][m[1].trim().toLowerCase()] = m[2].trim();
    });
    return out;
  }
  function field(p, sec, key) { var s = p.sections[sec]; if (!s) return undefined; return s[key.toLowerCase()]; }
  function checkHandoff(text) {
    var p = parse(text), errors = [], warnings = [], filled = 0, total = 0;
    var missing = SECTIONS.filter(function (s) { return !p.sections[s]; });
    if (missing.length) errors.push('Missing section(s): ' + missing.join(', ') + ' / 足りない項目: ' + missing.join(', '));
    var dup = p.order.filter(function (s, i) { return p.order.indexOf(s) !== i; });
    if (dup.length) warnings.push('Section repeated: ' + dup.join(', ') + ' / 項目が重複: ' + dup.join(', '));
    SECTIONS.forEach(function (s) { var f = p.sections[s] || {}; Object.keys(f).forEach(function (k) { total++; if (f[k]) filled++; }); });
    var st = field(p, 'JOB', 'status');
    if (st === undefined) errors.push('JOB has no "status" line / JOBに status がありません');
    else if (STATUS.indexOf(st) < 0) errors.push('status must be exactly one of ' + STATUS.join(', ') + ' (got "' + st + '") / status は1つだけ選びます');
    var ap = field(p, 'NEXT ACTION', 'owner approval needed');
    if (ap === undefined || (ap !== 'YES' && ap !== 'NO')) errors.push('"owner approval needed" must be YES or NO / owner approval needed は YES か NO です');
    if (st === 'DONE') {
      var empty = DONE_EVIDENCE.filter(function (k) { return !field(p, 'EVIDENCE', k); });
      if (empty.length) errors.push('DONE needs evidence: ' + empty.join(', ') + ' is empty (mark DONE only when the result exists in the intended environment) / DONE には根拠が必要です: ' + empty.join(', ') + ' が空です');
    }
    var nx = field(p, 'NEXT ACTION', 'highest-value next step');
    if (st !== 'DONE' && !nx) warnings.push('No highest-value next step / 次の一手がありません');
    if (nx && (/;|\band then\b/i.test(nx) || /(^|\s)\d[.)]\s.*\s\d[.)]\s/.test(nx))) warnings.push('Keep one highest-value next action (this line lists several) / 次の一手は1つにします');
    ['must not do', 'approval boundaries'].forEach(function (k) { if (!field(p, 'SCOPE', k)) warnings.push('SCOPE "' + k + '" is empty: write the boundary even if it is "none" / SCOPE の ' + k + ' が空です'); });
    [['CURRENT STATE', 'verified facts'], ['WORK COMPLETED', 'results'], ['EVIDENCE', 'limitations']].forEach(function (x) {
      var v = field(p, x[0], x[1]); if (v && HEDGE.test(v)) warnings.push(x[0] + ' "' + x[1] + '" sounds like a guess ("' + v.match(HEDGE)[0] + '"): do not guess missing results / 推測の表現があります');
    });
    return { ok: errors.length === 0, status: st || null, errors: errors, warnings: warnings, filled: filled, fields: total };
  }
  // Start a blank packet for one AI toolkit item: only facts known from the catalog are filled in (job id, NOT_STARTED, the
  // BSV source path, the framework, the catalog status as a limitation). Everything else, including owner approval, stays blank.
  function startPacket(template, item) {
    var set = { 'JOB': { 'id': 'toolkit:' + item.id, 'status': 'NOT_STARTED' },
      'CURRENT STATE': { 'authoritative source': 'BotShelfVampire/botshelf ' + item.path, 'live deploy / environment': item.framework + ' (your own; BSV does not run it)',
        'verified facts': 'AI toolkit catalog status ' + item.status },
      'EVIDENCE': { 'limitations': 'Not runtime-tested by BSV (catalog status ' + item.status + '); file presence and CI syntax checks are not runtime verification' } };
    var cur = null;
    return String(template || '').replace(/\r\n?/g, '\n').split('\n').map(function (line) {
      var t = line.trim();
      if (SECTIONS.indexOf(t) >= 0) { cur = t; return line; }
      var m = /^(\s*-\s*)([^:]+):(.*)$/.exec(line);
      if (m && cur && set[cur] && Object.prototype.hasOwnProperty.call(set[cur], m[2].trim().toLowerCase())) return m[1] + m[2] + ': ' + set[cur][m[2].trim().toLowerCase()];
      return line;
    }).join('\n');
  }
  var api = { checkHandoff: checkHandoff, parse: parse, startPacket: startPacket, SECTIONS: SECTIONS, STATUS: STATUS };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.BSVHandoff = api;
  if (!root.document) return;
  root.document.addEventListener('DOMContentLoaded', function () {
    var b = root.document.getElementById('ho-check'), ta = root.document.getElementById('ho-text'), out = root.document.getElementById('ho-out');
    if (!b || !ta || !out) return;
    var sb = root.document.getElementById('ho-start'), sel = root.document.getElementById('ho-item');
    if (sb && sel) sb.addEventListener('click', function () {
      var o = sel.options[sel.selectedIndex]; out.textContent = '';
      var msg = root.document.createElement('p'); msg.className = 'rq-msg';
      if (!o || !o.value) { msg.className += ' err'; msg.textContent = 'Choose a toolkit item first / 先に項目を選んでください'; }
      else if (ta.value.trim()) { msg.className += ' err'; msg.textContent = 'The box is not empty: clear it first so nothing you wrote is replaced / 入力欄が空ではありません。書いた内容を消さないよう、先に空にしてください'; }
      else { ta.value = startPacket(sb.getAttribute('data-ho-tpl'), { id: o.value, path: o.getAttribute('data-path'), framework: o.getAttribute('data-fw'), status: o.getAttribute('data-st') });
        msg.className += ' ok'; msg.textContent = 'Started a packet for ' + o.value + '. Fill in the rest, choose owner approval YES or NO, then press Check / 残りを記入し、owner approval を YES か NO にしてから Check を押してください'; }
      out.appendChild(msg);
    });
    b.addEventListener('click', function () {
      var r = checkHandoff(ta.value); out.textContent = '';
      var head = root.document.createElement('p'); head.className = 'rq-msg ' + (r.ok ? 'ok' : 'err');
      head.textContent = (r.ok ? 'No rule problems found' : r.errors.length + ' problem(s)') + ' · status ' + (r.status || '—') + ' · ' + r.filled + '/' + r.fields + ' fields filled · checked in this browser only; nothing was uploaded.';
      out.appendChild(head);
      var ul = root.document.createElement('ul');
      r.errors.forEach(function (e) { var li = root.document.createElement('li'); li.textContent = 'Problem: ' + e; ul.appendChild(li); });
      r.warnings.forEach(function (w) { var li = root.document.createElement('li'); li.textContent = 'Check: ' + w; ul.appendChild(li); });
      if (ul.children.length) out.appendChild(ul);
    });
  });
})(typeof window !== 'undefined' ? window : globalThis);
