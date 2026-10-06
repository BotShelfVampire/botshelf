'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const text = (en, ja) => window.BSVLabs.text(en, ja);
  function ik(x, y, L1, L2) {
    const r2 = x * x + y * y;
    const c2 = (r2 - L1 * L1 - L2 * L2) / (2 * L1 * L2);
    if (Math.abs(c2) > 1) return null;
    const q2 = Math.acos(Math.max(-1, Math.min(1, c2)));
    const q1 = Math.atan2(y, x) - Math.atan2(L2 * Math.sin(q2), L1 + L2 * Math.cos(q2));
    return { q1, q2 };
  }
  function fk(q1, q2, L1, L2) {
    return {
      x: L1 * Math.cos(q1) + L2 * Math.cos(q1 + q2),
      y: L1 * Math.sin(q1) + L2 * Math.sin(q1 + q2),
      elbow: { x: L1 * Math.cos(q1), y: L1 * Math.sin(q1) },
    };
  }
  function manip(q1, q2, L1, L2) {
    const s1 = Math.sin(q1), c1 = Math.cos(q1);
    const s12 = Math.sin(q1 + q2), c12 = Math.cos(q1 + q2);
    const J = [[-L1 * s1 - L2 * s12, -L2 * s12], [L1 * c1 + L2 * c12, L2 * c12]];
    const det = J[0][0] * J[1][1] - J[0][1] * J[1][0];
    const a = J[0][0] * J[0][0] + J[0][1] * J[0][1] + J[1][0] * J[1][0] + J[1][1] * J[1][1];
    const b = det * det;
    // sqrt(det(J J^T)) for 2x2 = |det|
    return { det, w: Math.abs(det) };
  }
  function draw(sol, L1, L2, tx, ty) {
    const c = $('arm'), ctx = c.getContext('2d');
    const W = c.width, H = c.height, scale = 900, ox = W * 0.2, oy = H * 0.75;
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = '#344f65'; ctx.beginPath();
    for (let i = 0; i < W; i += 40) { ctx.moveTo(i, 0); ctx.lineTo(i, H); }
    for (let j = 0; j < H; j += 40) { ctx.moveTo(0, j); ctx.lineTo(W, j); }
    ctx.stroke();
    const to = (x, y) => [ox + x * scale, oy - y * scale];
    ctx.fillStyle = '#60e0c0'; const [gx, gy] = to(tx, ty);
    ctx.beginPath(); ctx.arc(gx, gy, 6, 0, Math.PI * 2); ctx.fill();
    if (!sol) return;
    const p = fk(sol.q1, sol.q2, L1, L2);
    const [bx, by] = to(0, 0), [ex, ey] = to(p.elbow.x, p.elbow.y), [tx2, ty2] = to(p.x, p.y);
    ctx.strokeStyle = '#bad0dc'; ctx.lineWidth = 6; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(ex, ey); ctx.lineTo(tx2, ty2); ctx.stroke();
    ctx.fillStyle = '#e8f4f8'; [[bx, by], [ex, ey], [tx2, ty2]].forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill(); });
  }
  function render() {
    const L1 = Number($('L1').value), L2 = Number($('L2').value);
    const tx = Number($('tx').value), ty = Number($('ty').value);
    const sol = ik(tx, ty, L1, L2);
    draw(sol, L1, L2, tx, ty);
    if (!sol) {
      $('result').textContent = text('Unreachable with elbow-down IK for these lengths.', 'このリンク長では肘下がりIKでは到達できません。');
      $('export').value = 'reachable,0\n';
      return;
    }
    const tip = fk(sol.q1, sol.q2, L1, L2);
    const err = Math.hypot(tip.x - tx, tip.y - ty) * 1000;
    const m = manip(sol.q1, sol.q2, L1, L2);
    $('result').innerHTML = [
      `<strong>q1</strong> = ${sol.q1.toFixed(4)} rad · <strong>q2</strong> = ${sol.q2.toFixed(4)} rad`,
      text(`Tip error ${err.toFixed(3)} mm · manipulability |det J| = ${m.w.toFixed(5)}`,
           `先端誤差 ${err.toFixed(3)} mm · 可操作性 |det J| = ${m.w.toFixed(5)}`),
    ].join('<br>');
    $('export').value = ['q1_rad,q2_rad,x_m,y_m,err_mm,manipulability,L1_m,L2_m',
      [sol.q1, sol.q2, tip.x, tip.y, err, m.w, L1, L2].join(',')].join('\n');
  }
  $('solve').addEventListener('click', render);
  ['L1', 'L2', 'tx', 'ty'].forEach((id) => $(id).addEventListener('input', render));
  $('example').addEventListener('click', () => { $('L1').value = 0.12; $('L2').value = 0.10; $('tx').value = 0.15; $('ty').value = 0.08; render(); });
  $('arm').addEventListener('click', (e) => {
    const r = $('arm').getBoundingClientRect();
    const scale = 900, ox = $('arm').width * 0.2, oy = $('arm').height * 0.75;
    const sx = $('arm').width / r.width, sy = $('arm').height / r.height;
    const cx = (e.clientX - r.left) * sx, cy = (e.clientY - r.top) * sy;
    $('tx').value = ((cx - ox) / scale).toFixed(4);
    $('ty').value = ((oy - cy) / scale).toFixed(4);
    render();
  });
  $('copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('export').value); $('status').textContent = text('CSV copied.', 'CSVをコピーしました。'); }
    catch { $('export').select(); $('status').textContent = text('Select and copy manually.', '選択して手動でコピーしてください。'); }
  });
  $('download').addEventListener('click', () => {
    const blob = new Blob([$('export').value], { type: 'text/csv' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'bsv-2r-ik.csv'; a.click();
  });
  document.addEventListener('bsv:language', render);
  render();
})();
