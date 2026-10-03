// BSV Robot Pilot practice record builder (browser + node). Builds documents that follow
// teleop-session-evidence v0.1 and robot-pilot-profile v0.1. Sent to BSV only when the user presses Send (private review).
(function (root) {
  'use strict';
  function rid(n) { var a = '', c = '0123456789abcdef'; var r = (root.crypto && root.crypto.getRandomValues) ? root.crypto.getRandomValues(new Uint8Array(n)) : null;
    for (var i = 0; i < n; i++) a += c[(r ? r[i] : Math.floor(Math.random() * 256)) % 16]; return a; }
  function s(v, max) { return String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max || 300); }
  function n0(v) { var x = Number(v); return isFinite(x) && x >= 0 ? Math.floor(x) : NaN; }
  function iso(v) { if (!v) return null; var d = new Date(v); return isNaN(d.getTime()) ? NaN : d.toISOString().replace(/\.\d{3}Z$/, 'Z'); }
  // f: plain object of form values; modules: [{id, passCriteria:[...]}]; checks: {"moduleId:i": true}
  function build(f, modules, checks, ids) {
    var errs = [];
    ids = ids || {};
    var ev = {
      schemaVersion: '0.1', evidenceId: ids.evidenceId || 'teleop_' + rid(16), pilotId: s(f.pilotId, 80) || ids.pilotId || 'pilot_local_' + rid(10),
      taskId: s(f.taskId, 160), environment: 'SIMULATION', runtime: s(f.runtime, 160), runtimeVersion: s(f.runtimeVersion, 80) || null,
      sourceRevision: s(f.sourceRevision, 120) || null, embodiment: s(f.embodiment, 160), inputDevice: s(f.inputDevice, 160) || null,
      startedAt: iso(f.startedAt), endedAt: iso(f.endedAt),
      episodes: { attempted: n0(f.attempted), successful: n0(f.successful), failed: n0(f.failed) },
      safetyEvents: String(f.safetyEvents || '').split('\n').map(function (x) { return s(x, 300); }).filter(Boolean).slice(0, 50),
      dataArtifacts: [], metrics: {}, review: { status: 'UNREVIEWED', reviewerId: null, reviewedAt: null, note: s(f.note, 2000) || null }
    };
    if (f.recovery !== '' && f.recovery != null) ev.episodes.recoveryEpisodes = n0(f.recovery);
    if (s(f.artifactRef, 500)) ev.dataArtifacts.push({ type: s(f.artifactType, 40) || 'HDF5', uriOrRef: s(f.artifactRef, 500), sha256: /^[0-9a-f]{64}$/.test(s(f.artifactSha, 64).toLowerCase()) ? s(f.artifactSha, 64).toLowerCase() : null });
    if (s(f.artifactSha, 64) && !ev.dataArtifacts.length) errs.push('sha256 given without a dataset reference');
    if (s(f.artifactSha, 64) && ev.dataArtifacts.length && ev.dataArtifacts[0].sha256 === null) errs.push('sha256 must be 64 hex characters');
    (modules || []).forEach(function (m) { (m.passCriteria || []).forEach(function (_, i) { ev.metrics['module.' + m.id + '.criterion' + (i + 1)] = !!(checks || {})[m.id + ':' + i]; }); });
    ev.metrics['curriculumId'] = s(f.curriculumId, 120) || null;
    if (!ev.taskId) errs.push('task id is required');
    if (!ev.runtime) errs.push('runtime is required');
    if (!ev.embodiment) errs.push('embodiment is required');
    if (ev.startedAt === null || (typeof ev.startedAt === 'number')) errs.push('start time is required');
    if (typeof ev.endedAt === 'number') errs.push('end time is not a valid date');
    if (ev.endedAt && ev.startedAt && ev.endedAt < ev.startedAt) errs.push('end time is before start time');
    ['attempted', 'successful', 'failed'].forEach(function (k) { if (isNaN(ev.episodes[k])) errs.push(k + ' must be a whole number ≥ 0'); });
    if ('recoveryEpisodes' in ev.episodes && isNaN(ev.episodes.recoveryEpisodes)) errs.push('recovery episodes must be a whole number ≥ 0');
    if (!errs.length && ev.episodes.successful + ev.episodes.failed > ev.episodes.attempted) errs.push('successful + failed is more than attempted');
    var rec = {
      schemaVersion: '0.1', pilotId: ev.pilotId, visibility: 'PRIVATE',
      practiceRecords: [{ recordId: 'rec_' + ev.evidenceId.slice(7), taskId: ev.taskId, runtime: ev.runtime, runtimeVersion: ev.runtimeVersion,
        embodiment: ev.embodiment, inputDevice: ev.inputDevice, environment: 'SIMULATION', status: 'SELF_REPORTED', evidenceIds: [ev.evidenceId],
        limitations: ['Self-reported; not reviewed by BSV', 'Simulation only; no permission to operate real hardware', 'Not a government licence or manufacturer certification'] }]
    };
    return { errors: errs, evidence: ev, profile: rec };
  }
  // Open robot-pilot missions (Issue #7 tranche 4): approved PUBLIC requests from the Request Market whose areas
  // include robot-pilot. Rows come from demand-request?op=public as-is; nothing is added, seeded or estimated.
  function missions(rows) {
    return (Array.isArray(rows) ? rows : []).filter(function (r) { return r && r.visibility === 'PUBLIC' && Array.isArray(r.domains) && r.domains.indexOf('robot-pilot') !== -1; })
      .map(function (r) { var w = r.willingnessToPay;
        return { id: s(r.requestId, 80), job: s(r.job, 280), status: s(r.status, 20), platforms: (r.platforms || []).map(function (x) { return s(x, 60); }).join(', '),
          budget: w && (w.min != null || w.max != null) ? (w.min != null ? w.min : '?') + '–' + (w.max != null ? w.max : '?') + ' ' + s(w.currency || 'USDT', 8) + ' (stated, not escrow)' : '',
          deadline: r.deadline ? s(r.deadline, 10) : '', createdAt: s(r.createdAt, 10) }; });
  }
  // Check a saved file (Issue #7 tranche 5): validates a downloaded session-evidence or practice-record JSON against
  // the published schema in this browser (BSV mini JSON-Schema validator, same rules as test_robot_pilot.mjs).
  // Nothing is uploaded. A file can never raise its own review status; boundary notes say so.
  function tOf(v) { return v === null ? 'null' : Array.isArray(v) ? 'array' : (typeof v === 'number' && isFinite(v) && Math.floor(v) === v) ? 'integer' : typeof v; }
  function validate(sc, v, p, errs) {
    p = p || '$'; errs = errs || [];
    if (sc.const !== undefined && v !== sc.const) errs.push(p + ' must be ' + JSON.stringify(sc.const));
    if (sc.enum && sc.enum.indexOf(v) === -1) errs.push(p + ' must be one of ' + sc.enum.join('/'));
    if (sc.type) { var ts = [].concat(sc.type), t = tOf(v); if (!ts.some(function (x) { return x === t || (x === 'number' && t === 'integer'); })) { errs.push(p + ' has type ' + t + ', expected ' + ts.join('/')); return errs; } }
    if (typeof v === 'string') {
      if (sc.pattern && !new RegExp(sc.pattern).test(v)) errs.push(p + ' does not match the pattern');
      if (sc.minLength && v.length < sc.minLength) errs.push(p + ' is too short');
      if (sc.maxLength && v.length > sc.maxLength) errs.push(p + ' is too long');
      if (sc.format === 'date-time' && !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/.test(v)) errs.push(p + ' is not a date-time');
    }
    if (typeof v === 'number' && sc.minimum !== undefined && v < sc.minimum) errs.push(p + ' is below ' + sc.minimum);
    if (tOf(v) === 'object') {
      (sc.required || []).forEach(function (r) { if (!Object.prototype.hasOwnProperty.call(v, r)) errs.push(p + ' is missing ' + r); });
      Object.keys(v).forEach(function (k) {
        if (sc.properties && sc.properties[k]) validate(sc.properties[k], v[k], p + '.' + k, errs);
        else if (sc.additionalProperties === false) errs.push(p + ' has an unknown field ' + k);
        else if (sc.additionalProperties && typeof sc.additionalProperties === 'object') validate(sc.additionalProperties, v[k], p + '.' + k, errs);
      });
    }
    if (Array.isArray(v) && sc.items) v.forEach(function (x, i) { validate(sc.items, x, p + '[' + i + ']', errs); });
    return errs;
  }
  var SCHEMA_URL = { evidence: '/schemas/teleop-session-evidence-v0.1.json', profile: '/schemas/robot-pilot-profile-v0.1.json' };
  function kindOf(doc) { return doc && typeof doc === 'object' && !Array.isArray(doc) ? (Object.prototype.hasOwnProperty.call(doc, 'evidenceId') ? 'evidence' : Object.prototype.hasOwnProperty.call(doc, 'practiceRecords') ? 'profile' : '') : ''; }
  function checkDoc(doc, schemas) {
    var kind = kindOf(doc);
    if (!kind) return { kind: '', errors: ['Not a BSV session-evidence or practice-record file (no evidenceId or practiceRecords).'], notes: [] };
    var errors = validate(schemas[kind], doc).slice(0, 50), notes = [];
    if (kind === 'evidence') {
      if (doc.environment !== 'SIMULATION') notes.push('environment is ' + doc.environment + ': the Academy only covers simulation; this record gives no permission to operate real hardware.');
      if (doc.review && doc.review.status && doc.review.status !== 'UNREVIEWED') notes.push('review.status is ' + doc.review.status + ' in the file. Only a BSV review sets this; editing the file does not change any record.');
    } else {
      (Array.isArray(doc.practiceRecords) ? doc.practiceRecords : []).forEach(function (r, i) {
        if (r && r.status && r.status !== 'SELF_REPORTED') notes.push('practiceRecords[' + i + '].status is ' + r.status + ' in the file. Records you build here are SELF_REPORTED; editing the file does not change any record.');
      });
    }
    return { kind: kind, errors: errors, notes: notes };
  }
  // Practice log (Issue #7 tranche 6): totals over evidence records saved in this browser. Self-reported input only;
  // nothing is estimated, uploaded or upgraded. Records whose counts do not add up are flagged, not corrected.
  function summarize(list) {
    var o = { sessions: 0, attempted: 0, successful: 0, failed: 0, recovery: 0, safetyEvents: 0, nonSimulation: 0, inconsistent: [], byTask: {} };
    (Array.isArray(list) ? list : []).forEach(function (e, i) {
      if (!e || typeof e !== 'object' || !e.episodes || typeof e.episodes !== 'object') return;
      var ep = e.episodes, n = function (x) { return typeof x === 'number' && isFinite(x) && x >= 0 ? Math.floor(x) : 0; };
      var a = n(ep.attempted), s = n(ep.successful), f = n(ep.failed), r = n(ep.recoveryEpisodes);
      o.sessions++; o.attempted += a; o.successful += s; o.failed += f; o.recovery += r;
      o.safetyEvents += Array.isArray(e.safetyEvents) ? e.safetyEvents.length : 0;
      if (e.environment !== 'SIMULATION') o.nonSimulation++;
      if (s + f > a) o.inconsistent.push(e.evidenceId || ('#' + i));
      var t = String(e.taskId || '(no task)'), b = o.byTask[t] || (o.byTask[t] = { sessions: 0, attempted: 0, successful: 0, failed: 0, recovery: 0 });
      b.sessions++; b.attempted += a; b.successful += s; b.failed += f; b.recovery += r;
    });
    o.successRate = o.attempted ? o.successful / o.attempted : null;
    return o;
  }
  // CSV of the sessions saved in this browser (Issue #7 tranche 8): one row per saved evidence file, values copied as
  // saved (nothing estimated). Cells that a spreadsheet would read as a formula get a leading apostrophe.
  var CSV_COLS = ['evidenceId', 'taskId', 'environment', 'runtime', 'runtimeVersion', 'inputDevice', 'startedAt', 'endedAt', 'attempted', 'successful', 'failed', 'recoveryEpisodes', 'safetyEvents', 'reviewStatus'];
  function csvCell(v) { var t = v == null ? '' : String(v); if (/^[=+\-@\t\r]/.test(t)) t = "'" + t; return /[",\r\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t; }
  function toCsv(list) {
    var rows = [CSV_COLS.join(',')];
    (Array.isArray(list) ? list : []).forEach(function (e) {
      if (!e || typeof e !== 'object') return;
      var ep = e.episodes || {}, rt = e.runtime && typeof e.runtime === 'object' ? e.runtime : {};
      rows.push([e.evidenceId, e.taskId, e.environment, typeof e.runtime === 'string' ? e.runtime : rt.name, e.runtimeVersion || rt.version, e.inputDevice, e.startedAt, e.endedAt,
        ep.attempted, ep.successful, ep.failed, ep.recoveryEpisodes, Array.isArray(e.safetyEvents) ? e.safetyEvents.length : '', e.review && e.review.status].map(csvCell).join(','));
    });
    return rows.join('\r\n') + '\r\n';
  }
  var api = { build: build, missions: missions, validate: validate, checkDoc: checkDoc, kindOf: kindOf, summarize: summarize, toCsv: toCsv };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.BSVPilot = api;
  if (!root.document) return;
  var KEY = 'bsv-pilot-records-v1';
  function $(q) { return root.document.querySelector(q); }
  function val(id) { var e = root.document.getElementById(id); return e ? e.value : ''; }
  function dl(name, obj) { var b = new Blob([JSON.stringify(obj, null, 2) + '\n'], { type: 'application/json' }); var a = root.document.createElement('a'); a.href = URL.createObjectURL(b); a.download = name; root.document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
  function current() {
    var cur = JSON.parse($('#rp-curriculum-data').textContent);
    var checks = {}; [].forEach.call(root.document.querySelectorAll('input[data-rp-crit]'), function (c) { checks[c.getAttribute('data-rp-crit')] = c.checked; });
    var f = {}; ['pilotId', 'taskId', 'runtime', 'runtimeVersion', 'sourceRevision', 'embodiment', 'inputDevice', 'startedAt', 'endedAt', 'attempted', 'successful', 'failed', 'recovery', 'safetyEvents', 'artifactType', 'artifactRef', 'artifactSha', 'note'].forEach(function (k) { f[k] = val('rp-' + k); });
    f.curriculumId = cur.curriculumId;
    var ids = {}; try { ids = JSON.parse(root.localStorage.getItem(KEY + ':ids') || '{}'); } catch (e) {}
    var out = build(f, cur.modules, checks, ids.pilotId && !f.pilotId ? { pilotId: ids.pilotId } : {});
    if (!ids.pilotId && !f.pilotId) { try { root.localStorage.setItem(KEY + ':ids', JSON.stringify({ pilotId: out.evidence.pilotId })); } catch (e) {} }
    return out;
  }
  function show(out) {
    var m = $('#rp-msg'); m.textContent = out.errors.length ? 'Fix: ' + out.errors.join('; ') : 'Valid against teleop-session-evidence v0.1 (status UNREVIEWED) and robot-pilot-profile v0.1 (SELF_REPORTED).';
    m.className = 'rq-msg ' + (out.errors.length ? 'err' : 'ok'); $('#rp-preview').textContent = JSON.stringify(out.evidence, null, 2); return !out.errors.length;
  }
  root.document.addEventListener('DOMContentLoaded', function () {
    var f = $('#rp-form'); if (!f) return;
    f.addEventListener('submit', function (e) { e.preventDefault(); show(current()); });
    $('#rp-dl-ev').addEventListener('click', function () { var o = current(); if (show(o)) dl(o.evidence.evidenceId + '.teleop-session-evidence.json', o.evidence); });
    $('#rp-dl-rec').addEventListener('click', function () { var o = current(); if (show(o)) dl(o.profile.practiceRecords[0].recordId + '.practice-record.json', o.profile); });
    $('#rp-save').addEventListener('click', function () { var o = current(); if (!show(o)) return; var a = []; try { a = JSON.parse(root.localStorage.getItem(KEY) || '[]'); } catch (e) {} a.push(o.evidence); try { root.localStorage.setItem(KEY, JSON.stringify(a.slice(-20))); } catch (e) {} $('#rp-saved').textContent = a.length + ' saved in this browser'; });
    try { var a = JSON.parse(root.localStorage.getItem(KEY) || '[]'); if (a.length) $('#rp-saved').textContent = a.length + ' saved in this browser'; } catch (e) {}
    function pct(x) { return x === null ? '—' : (Math.round(x * 1000) / 10) + '%'; }
    function td(tr, v) { var c = root.document.createElement('td'); c.textContent = String(v); tr.appendChild(c); }
    function renderLog() {
      var tb = $('#rp-log-rows'), sm = $('#rp-log-sum'); if (!tb || !sm) return;
      var list = []; try { list = JSON.parse(root.localStorage.getItem(KEY) || '[]'); } catch (e) {}
      var o = summarize(list); tb.textContent = '';
      Object.keys(o.byTask).sort().forEach(function (t) { var b = o.byTask[t], tr = root.document.createElement('tr'); [t, b.sessions, b.attempted, b.successful, b.failed, b.recovery, pct(b.attempted ? b.successful / b.attempted : null)].forEach(function (v) { td(tr, v); }); tb.appendChild(tr); });
      sm.textContent = o.sessions ? (o.sessions + ' session(s) saved in this browser: ' + o.attempted + ' attempted, ' + o.successful + ' successful (' + pct(o.successRate) + '), ' + o.failed + ' failed, ' + o.recovery + ' recovery, ' + o.safetyEvents + ' safety event(s).' +
        (o.nonSimulation ? ' ' + o.nonSimulation + ' not marked SIMULATION.' : '') + (o.inconsistent.length ? ' Counts do not add up in: ' + o.inconsistent.join(', ') + '.' : '') + ' Self-reported; not reviewed.') : 'No sessions saved in this browser yet.';
    }
    renderLog();
    $('#rp-save').addEventListener('click', renderLog);
    var csvb = $('#rp-log-csv'); if (csvb) csvb.addEventListener('click', function () { var a = []; try { a = JSON.parse(root.localStorage.getItem(KEY) || '[]'); } catch (e) {} var b = new Blob([toCsv(a)], { type: 'text/csv' }), l = root.document.createElement('a'); l.href = URL.createObjectURL(b); l.download = 'bsv-practice-log.csv'; root.document.body.appendChild(l); l.click(); setTimeout(function () { URL.revokeObjectURL(l.href); l.remove(); }, 500); });
    var clr = $('#rp-log-clear'); if (clr) clr.addEventListener('click', function () { try { root.localStorage.removeItem(KEY); } catch (e) {} $('#rp-saved').textContent = ''; renderLog(); });
    var API = '/.netlify/functions/pilot-record';
    var cf = $('#rp-check-file');
    if (cf) cf.addEventListener('change', function () {
      var out = $('#rp-check-msg'), f = cf.files && cf.files[0]; if (!out || !f) return;
      out.className = 'rq-msg'; out.textContent = 'Checking ' + f.name + '…';
      if (f.size > 1000000) { out.className = 'rq-msg err'; out.textContent = 'File is larger than 1 MB; not checked.'; return; }
      f.text().then(function (txt) {
        var doc; try { doc = JSON.parse(txt); } catch (e) { out.className = 'rq-msg err'; out.textContent = 'Not valid JSON.'; return; }
        var kind = kindOf(doc); if (!kind) { var r0 = checkDoc(doc, {}); out.className = 'rq-msg err'; out.textContent = r0.errors[0]; return; }
        return fetch(SCHEMA_URL[kind], { credentials: 'omit' }).then(function (r) { return r.json(); }).then(function (sc) {
          var sch = {}; sch[kind] = sc; var r = checkDoc(doc, sch);
          out.className = 'rq-msg ' + (r.errors.length || r.notes.length ? 'err' : 'ok');
          out.textContent = (kind === 'evidence' ? 'Session evidence (teleop-session-evidence v0.1): ' : 'Practice record (robot-pilot-profile v0.1): ') +
            (r.errors.length ? r.errors.length + ' problem(s): ' + r.errors.join('; ') : 'valid against the published schema.') + (r.notes.length ? ' Note: ' + r.notes.join(' ') : '') + ' Checked in this browser only; nothing was uploaded.';
        });
      }).catch(function () { out.className = 'rq-msg err'; out.textContent = 'Could not check the file.'; });
    });
    fetch('/.netlify/functions/demand-request?op=public', { credentials: 'omit' }).then(function (r) { return r.json(); }).then(function (j) {
      var ul = $('#rp-missions'), c = $('#rp-c-missions'); if (!ul || !j || !j.ok) return;
      var ms = missions(j.requests); c.textContent = String(ms.length); ul.textContent = '';
      if (!ms.length) { var e = root.document.createElement('li'); e.className = 'empty'; e.textContent = 'No approved robot-pilot missions yet. / 承認済みのロボットパイロットのミッションはまだありません。'; ul.appendChild(e); return; }
      ms.forEach(function (m) { var li = root.document.createElement('li'), a = root.document.createElement('a'), meta = root.document.createElement('div');
        a.href = '/requests/#' + encodeURIComponent(m.id); a.textContent = m.job; meta.className = 'small muted';
        meta.textContent = [m.status, m.platforms, m.budget, m.deadline ? 'deadline ' + m.deadline : '', 'listed ' + m.createdAt].filter(Boolean).join(' · ');
        li.appendChild(a); li.appendChild(meta); ul.appendChild(li); });
    }).catch(function () { var ul = $('#rp-missions'); if (ul) ul.textContent = 'Could not load missions. / ミッションを読み込めませんでした。'; });
    fetch(API + '?op=stats', { credentials: 'omit' }).then(function (r) { return r.json(); }).then(function (j) { if (j && j.ok) { $('#rp-c-received').textContent = String(j.counts.received); $('#rp-c-reviewed').textContent = String(j.counts.reviewed); } }).catch(function () {});
    $('#rp-send').addEventListener('click', function () { var o = current(); if (!show(o)) return; var m = $('#rp-msg'), b = $('#rp-send'); b.disabled = true;
      fetch(API, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ evidence: o.evidence }) })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; }); })
        .then(function (x) { b.disabled = false;
          if (x.s === 201 || (x.s === 200 && x.j.duplicate)) { m.className = 'rq-msg ok'; m.textContent = (x.j.duplicate ? 'Already sent' : 'Sent privately') + ' (' + x.j.id + '). Status: SELF_REPORTED, pending review. Not a licence or certification.'; }
          else if (x.s === 401) { m.className = 'rq-msg err'; m.textContent = 'Sign in with your verified email first, then send again. '; var a = root.document.createElement('a'); a.href = '/register.html?next=/robot-pilot/'; a.textContent = 'Register / sign in'; m.appendChild(a); }
          else if (x.s === 429) { m.className = 'rq-msg err'; m.textContent = 'Daily limit reached (10 records per day).'; }
          else { m.className = 'rq-msg err'; m.textContent = 'Not sent: ' + (x.j.reason || x.s); } })
        .catch(function () { b.disabled = false; m.className = 'rq-msg err'; m.textContent = 'Not sent: network error'; }); });
  });
})(typeof window !== 'undefined' ? window : globalThis);
