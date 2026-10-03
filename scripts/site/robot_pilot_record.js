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
  var api = { build: build };
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
    var API = '/.netlify/functions/pilot-record';
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
