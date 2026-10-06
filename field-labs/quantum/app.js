'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const text = (en, ja) => window.BSVLabs.text(en, ja);
  const clean = (n) => Math.abs(n) < 1e-12 ? 0 : n;
  function state(theta, phi) {
    const t = theta * Math.PI / 180, p = phi * Math.PI / 180;
    const x = clean(Math.sin(t) * Math.cos(p)), y = clean(Math.sin(t) * Math.sin(p)), z = clean(Math.cos(t));
    return {theta, phi, x, y, z, alpha: clean(Math.cos(t / 2)), betaReal: clean(Math.sin(t / 2) * Math.cos(p)), betaImaginary: clean(Math.sin(t / 2) * Math.sin(p)), p0: (1 + z) / 2, pPlus: (1 + x) / 2};
  }
  window.BSVQubit = {state};
  let sampled = null;
  const pct = (n) => (n * 100).toFixed(1) + '%';
  const num = (n) => clean(n).toFixed(3);
  function draw(s) {
    const canvas = $('bloch'), c = canvas.getContext('2d');
    if (!c) return;
    c.clearRect(0, 0, 600, 390);
    const origin = {x:300,y:190};
    const project = (x,y,z) => ({x:origin.x+135*x-74*y,y:origin.y+44*x+65*y-142*z});
    c.strokeStyle='#344f65'; c.lineWidth=1.4;
    c.beginPath(); c.arc(300,190,151,0,Math.PI*2); c.stroke();
    for (const plane of ['xy','xz','yz']) {
      c.beginPath();
      for(let i=0;i<=120;i++) {const a=i*Math.PI/60, ca=Math.cos(a),sa=Math.sin(a);const p=plane==='xy'?project(ca,sa,0):plane==='xz'?project(ca,0,sa):project(0,ca,sa);i===0?c.moveTo(p.x,p.y):c.lineTo(p.x,p.y);}
      c.stroke();
    }
    c.font='16px system-ui'; c.fillStyle='#bad0dc';
    [[1,0,0,'X / +'],[0,1,0,'Y / +i'],[0,0,1,'Z / 0'],[0,0,-1,'1']].forEach(([x,y,z,label])=>{const p=project(x*1.2,y*1.2,z*1.2);c.beginPath();c.moveTo(300,190);c.lineTo(p.x,p.y);c.stroke();c.fillText(label,p.x+6,p.y+5);});
    const end=project(s.x,s.y,s.z);c.strokeStyle='#60e0c0';c.lineWidth=4;c.beginPath();c.moveTo(300,190);c.lineTo(end.x,end.y);c.stroke();c.fillStyle='#60e0c0';c.beginPath();c.arc(end.x,end.y,8,0,Math.PI*2);c.fill();
    c.font='13px system-ui';c.fillStyle='#bad0dc';c.fillText(text('Oblique projection · pure state on the unit sphere','斜投影 · 単位球面上の純粋状態'),100,374);
    canvas.setAttribute('aria-label',text(`Bloch vector x ${num(s.x)}, y ${num(s.y)}, z ${num(s.z)}`,`ブロッホベクトル x ${num(s.x)}、y ${num(s.y)}、z ${num(s.z)}`));
  }
  function render() {
    const s=state(Number($('theta').value),Number($('phi').value)), n=Number($('shots').value);
    $('theta-value').textContent=s.theta+'°'; $('phi-value').textContent=s.phi+'°';
    $('coordinates').textContent=`(x, y, z) = (${num(s.x)}, ${num(s.y)}, ${num(s.z)})`;
    $('state-value').textContent=`|ψ⟩ = ${num(s.alpha)} |0⟩ + (${num(s.betaReal)} ${s.betaImaginary<0?'−':'+'} ${num(Math.abs(s.betaImaginary))}i) |1⟩`;
    $('z-prob').textContent=`0: ${pct(s.p0)} · 1: ${pct(1-s.p0)}`;
    $('x-prob').textContent=`+: ${pct(s.pPlus)} · −: ${pct(1-s.pPlus)}`;
    $('z-meter').value=s.p0; $('z-meter').textContent=pct(s.p0); $('x-meter').value=s.pPlus; $('x-meter').textContent=pct(s.pPlus);
    $('insight').textContent=Math.abs(s.z)>0.999999?text('At a pole, relative phase cannot change any measurement prediction. Move θ toward 90° to see interference.','極では位相を変えても測定の予測は変わりません。θを90°へ近づけて干渉を確かめましょう。'):text(`Phase changes the X odds while leaving the Z odds fixed. With this θ, P(+) can range from ${pct((1-Math.sin(s.theta*Math.PI/180))/2)} to ${pct((1+Math.sin(s.theta*Math.PI/180))/2)} as φ moves.`,`位相はZの確率を変えず、Xの確率を変えます。現在のθでは、φを動かすとP(+)は${pct((1-Math.sin(s.theta*Math.PI/180))/2)}から${pct((1+Math.sin(s.theta*Math.PI/180))/2)}の範囲を動きます。`);
    const rows=[['Z → 0',s.p0,sampled?.z],['Z → 1',1-s.p0,sampled?n-sampled.z:null],['X → +',s.pPlus,sampled?.x],['X → −',1-s.pPlus,sampled?n-sampled.x:null]];
    $('counts').replaceChildren(...rows.map(([name,p,count])=>{const tr=document.createElement('tr');[name,(n*p).toFixed(1),count==null?'—':String(count)].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});return tr;}));
    $('sample-note').textContent=sampled?text(`${n.toLocaleString()} independent shots per basis. Expected counts are mathematical averages; sample counts are one random trial.`, `各基底${n.toLocaleString()}回の独立した測定。期待回数は数学的な平均値、乱数による回数は1回の模擬実験結果です。`):text('Expected counts are deterministic averages and may be fractional. Select “Simulate random shots” to compare one trial.','期待回数は数式で決まる平均値なので、小数になる場合があります。「ランダム測定を模擬実行」で1回の試行と比較できます。');
    $('circuit').textContent=`|0⟩ → Rᵧ(${s.theta}°) → P(${s.phi}°) → ${text('Z measurement / H → Z measurement','Z測定 / H → Z測定')}`;
    $('state-export').value=JSON.stringify({model:'ideal-pure-single-qubit',angleUnit:'degrees',theta:s.theta,phi:s.phi,amplitudes:{zero:{real:s.alpha,imaginary:0},one:{real:s.betaReal,imaginary:s.betaImaginary}},bloch:{x:s.x,y:s.y,z:s.z},probabilities:{Z:{zero:s.p0,one:1-s.p0},X:{plus:s.pPlus,minus:1-s.pPlus}},shotsPerBasis:n,simulatedCounts:sampled?{Z:{zero:sampled.z,one:n-sampled.z},X:{plus:sampled.x,minus:n-sampled.x}}:null},null,2);
    draw(s);
  }
  ['theta','phi','shots'].forEach(id=>$(id).addEventListener('input',()=>{sampled=null;$('copy-status').textContent='';render();}));
  document.querySelectorAll('[data-preset]').forEach(button=>button.addEventListener('click',()=>{const[t,p]=button.dataset.preset.split(',');$('theta').value=t;$('phi').value=p;sampled=null;render();}));
  $('sample').addEventListener('click',()=>{const s=state(Number($('theta').value),Number($('phi').value));sampled={x:0,z:0};for(let i=0;i<Number($('shots').value);i++){if(Math.random()<s.p0)sampled.z++;if(Math.random()<s.pPlus)sampled.x++;}render();});
  $('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('state-export').value);$('copy-status').textContent=text('State copied.','状態をコピーしました。');}catch{$('state-export').focus();$('state-export').select();$('copy-status').textContent=text('Select and copy the highlighted state text.','選択された状態データを手動でコピーしてください。');}});
  $('download').addEventListener('click',()=>{const blob=new Blob([$('state-export').value],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='bsv-qubit-state.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  document.addEventListener('bsv:language',render);render();
})();
