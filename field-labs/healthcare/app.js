(function () {
  'use strict';
  const tasks = {
    logistics: {
      name: ['Supply delivery', '物品搬送'],
      question: ['Can the system complete a defined dummy delivery and make interruptions visible?', '定義した模擬搬送を完了し、中断を可視化できるか？'],
      baseline: ['A fixed scripted route with the same start, destination, layout, and dummy payload.', '開始点・目的地・配置・模擬荷物をそろえた固定経路。'],
      metrics: ['Completed deliveries / all attempts; assisted attempts / all attempts; end-to-end time for completed runs, with failed and timed-out runs listed separately.', '搬送完了数／全試行数、介入があった試行数／全試行数、完了試行の総所要時間。失敗とタイムアウトは別途全件を記録。'],
      scenarios: [
        ['Nominal: clear route and unambiguous destination.', '通常条件：障害物のない経路と明確な目的地。'],
        ['Blocked route: insert a simulated blockage; observe the transition to a defined waiting or stopped state and operator notification.', '経路閉塞：模擬的に経路を塞ぎ、定義した待機・停止状態への遷移と操作者への通知を確認。'],
        ['Interrupted task: interrupt the mock task and verify that the pending delivery and restart decision remain explicit.', 'タスク中断：模擬タスクを中断し、未完了の搬送と再開判断が明示されるかを確認。']
      ]
    },
    handover: {
      name: ['Operator handover', '操作者の引き継ぎ'],
      question: ['Can the receiving operator identify mode, pending task, and control ownership without guessing?', '受け手は、モード・保留タスク・操作権の所在を推測せずに把握できるか？'],
      baseline: ['The current mock handover screen or a plain status-and-acknowledgement checklist, using the same scripted task.', '同一の模擬タスクに対する現行の引き継ぎ画面、または状態と確認応答だけの簡単なチェックリスト。'],
      metrics: ['Correctly identified mode, pending task, and control owner / handovers; time to acknowledgement; unacknowledged and conflicting-control events.', 'モード・保留タスク・操作権を正しく把握できた件数／引き継ぎ数、確認応答までの時間、未応答と操作権競合の発生件数。'],
      scenarios: [
        ['Nominal: transfer a paused mock task and ask the receiving operator to describe its state before acknowledging.', '通常条件：一時停止した模擬タスクを引き継ぎ、受け手が状態を説明した後で確認応答。'],
        ['Stale information: replay delayed status messages and inspect whether their age and current control owner remain visible.', '情報の遅延：遅延した状態メッセージを再生し、情報の古さと現在の操作権が判別できるかを確認。'],
        ['Lost connection: inject a simulated disconnect during transfer and inspect the defined fallback state and event record.', '通信断：引き継ぎ途中の模擬通信断で、事前に決めた退避状態とイベント記録を確認。']
      ]
    },
    positioning: {
      name: ['Fixture positioning', '治具の位置決め'],
      question: ['How do reference-position error and repeated-position spread vary across an inert target set?', '人体を使わない複数の目標位置で、基準との誤差と繰り返し時のばらつきはどう変わるか？'],
      baseline: ['A fixed reference command or existing positioning method, using the same inert fixture and coordinate definition.', '同一の非生体治具と座標定義を用いた固定基準コマンド、または既存の位置決め方法。'],
      metrics: ['Position error from a stated reference in stated units; spread across repeats; measurement uncertainty; aborted or unreachable targets, reported separately.', '単位を明記した基準位置からの誤差、繰り返しのばらつき、測定の不確かさ、中止・到達不能の目標位置（別途記録）。'],
      scenarios: [
        ['Nominal: repeat the same inert target, then test multiple predefined target positions.', '通常条件：同じ非生体目標への繰り返し試行の後、事前に定義した複数位置を確認。'],
        ['Reference mismatch: use a simulated frame/configuration mismatch and inspect rejection or explicit invalid-state reporting.', '基準の不一致：座標系・設定の不一致を模擬し、拒否または明示的な無効状態表示を確認。'],
        ['Unreachable target: request an out-of-model target in simulation and inspect the defined rejection, without extending hardware limits.', '到達不能位置：シミュレーション内でモデル範囲外を指定し、定義した拒否動作を確認。実機の制限は拡張しない。']
      ]
    }
  };
  const settings = {
    simulation: {
      name: ['Digital simulation / recorded replay', 'デジタルシミュレーション・記録再生'],
      control: ['Freeze model version, scenario inputs, time step, random seed if used, and replay timing. Record which physical and human behaviors are not modeled.', 'モデル版、シナリオ入力、時間刻み、使用する場合の乱数種、再生タイミングを固定。モデル化していない物理現象・人の行動を記録。'],
      limit: ['Simulation results describe the model. Carry its untested assumptions into any later bench or mock-room plan.', '結果が示すのはモデル内の挙動です。未検証の仮定を、次のベンチ・模擬室計画へ引き継ぎます。']
    },
    mock: {
      name: ['Controlled mock room / mock corridor', '管理された模擬室・模擬廊下'],
      control: ['Freeze room layout, lighting/noise conditions, dummy objects, operator instructions, and observation method. Keep the activity separated from care delivery.', '室内配置、照明・騒音条件、模擬物品、操作者への説明、観察方法を固定。診療の動線と活動を分離。'],
      limit: ['A controlled mock setting can reveal workflow issues, but its participants and conditions may not represent actual use.', '模擬環境では作業上の課題を探せますが、参加者と条件が実際の使用を代表するとは限りません。']
    },
    bench: {
      name: ['Isolated bench with inert fixtures', '非生体治具を使う隔離ベンチ'],
      control: ['Record fixture and device configuration, reference coordinates, measurement uncertainty, and a documented stop condition. Use inert objects and an isolated test area.', '治具・機器の構成、基準座標、測定の不確かさ、文書化した中止条件を記録。非生体物と隔離した試験区画を使用。'],
      limit: ['A bench isolates a subsystem. It does not reproduce a complete ward route or the full workload of an operator.', 'ベンチで調べるのは切り出した機能です。病棟経路全体や操作者の実作業全体を再現するものではありません。']
    }
  };
  function buildPlan(input, lang) {
    const j = lang === 'ja' ? 1 : 0;
    const t = (en, ja) => [en, ja][j];
    const task = tasks[input.use] || tasks.logistics;
    const setting = settings[input.environment] || settings.simulation;
    const owner = String(input.owner || '').trim();
    const criteria = String(input.criteria || '').trim();
    const notes = [];
    if (!owner) notes.push(t('Add a decision-owner role before sharing the plan.', '共有前に、判断を担当する役割を記入してください。'));
    if (!criteria) notes.push(t('Define the metric, threshold, denominator, and test conditions.', '指標・閾値・分母・試験条件を定義してください。'));
    else if (!/[0-9０-９]/.test(criteria)) notes.push(t('No numeric target was detected. Add one where appropriate, or make a binary pass condition explicit.', '数値目標が見当たりません。必要に応じて数値を追加するか、二値の合格条件を明示してください。'));
    if (input.environment === 'bench' && input.use !== 'positioning') notes.push(t('This bench selection only tests a subsystem. Add a later mock-setting study before making workflow claims.', 'このベンチ選択で調べるのは機能の一部です。作業全体を評価するには、別途模擬環境での検証が必要です。'));
    const lines = [
      t('BSV MEDICAL ROBOTICS — RESEARCH PoC BRIEF', 'BSV 医療ロボティクス — 研究 PoC 計画'),
      t('Status: planning draft; no tests or outcomes have been verified.', '状態：計画案。試験の実施・結果は未確認。'), '',
      t('1. QUESTION & SCOPE', '1. 問いと範囲'),
      `${t('Task', '用途')}: ${task.name[j]}`,
      `${t('Question', '検証する問い')}: ${task.question[j]}`,
      `${t('Environment', '環境')}: ${setting.name[j]}`,
      `${t('Decision owner', '判断担当')}: ${owner || t('[assign a role]', '[役割を指定]')}`,
      t('Boundary: research, simulation, and inert mock tasks only; no clinical performance claim follows from this plan.', '対象：研究・シミュレーション・非生体の模擬タスク。本計画から臨床性能を主張することはできません。'), '',
      t('2. COMPARISON & PREDECLARED CRITERIA', '2. 比較と事前に決める基準'),
      `${t('Baseline', '比較対象')}: ${task.baseline[j]}`,
      `${t('Draft criteria supplied by the team', 'チームが入力した仮の基準')}: ${criteria || t('[define before running]', '[実施前に定義]')}`,
      t('Before running, fix the number of attempts and its rationale, timeout, exclusion rules, and separate acceptance rules for nominal and interruption cases. Do not choose them after inspecting results.', '試行数と根拠、タイムアウト、除外規則、通常条件と中断条件それぞれの合否規則を実施前に確定します。結果を見てから選ばないようにします。'), '',
      t('3. FREEZE THE SETUP', '3. 条件を固定'), setting.control[j],
      t('Use the same conditions for baseline and candidate. Record software/configuration versions and change only the factor under investigation; alternate run order where order effects are plausible.', '比較対象と候補の条件をそろえ、ソフトウェア・設定の版を記録。調べる要因だけを変え、順序の影響が考えられる場合は実施順序を交互にします。'), '',
      t('4. SCENARIO SHEET', '4. シナリオ一覧'),
      ...task.scenarios.map((s, i) => `${i + 1}. ${s[j]}`),
      t('For every scenario, write: input state → expected state transition → observed state → evidence ID → pass / fail / not tested. Preserve the first failure before any reset.', '各シナリオに「入力状態 → 期待する状態遷移 → 観測状態 → 証拠 ID → 合格／不合格／未実施」を記録。リセットする前に最初の失敗を保存します。'), '',
      t('5. MEASURE & KEEP EVIDENCE', '5. 測定と証拠'), task.metrics[j],
      t('One row per attempt: run ID | scenario | baseline/candidate | configuration | start/end | result | intervention | failure reason | log/screenshot reference.', '試行ごとに 1 行：試行 ID | シナリオ | 比較対象／候補 | 設定 | 開始／終了 | 結果 | 介入 | 失敗理由 | ログ・画像の参照。'),
      t('Report counts and denominators by scenario. Keep failed, aborted, and repeated attempts visible; a pooled average can hide a failing condition.', 'シナリオ別に件数と分母を報告。失敗・中止・再試行も明示します。全体平均だけでは、特定条件の失敗が隠れることがあります。'), '',
      t('6. REVIEW & NEXT DECISION', '6. レビューと次の判断'),
      t('Compare every predeclared criterion with its evidence. Mark untested criteria as not tested, never as passed.', '事前基準ごとに証拠を照合。未検証の基準は「未実施」とし、合格扱いにしません。'),
      t('Decision: revise / repeat / explore next question. Assign a role and due date to each unresolved failure. Record what changed before a repeat.', '判断：修正／再試行／次の問いを検証。未解決の失敗ごとに担当の役割と期限を決め、再試行前の変更点を記録。'),
      `${t('Evidence boundary', '結果の適用範囲')}: ${setting.limit[j]}`,
      t('Next experiment and owner: [fill in after review]', '次の検証と担当：[レビュー後に記入]'),
      '', t('OPEN ITEMS', '未確定事項'),
      ...(notes.length ? notes.map(n => `- ${n}`) : [t('- Confirm the criteria, sample-size rationale, and stop rules with the decision owner.', '- 判断担当と、基準・試行数の根拠・中止規則を確定してください。')])
    ];
    return { text: lines.join('\n'), notes, task: task.name[j], environment: setting.name[j] };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { buildPlan };
  if (typeof document === 'undefined') return;
  const form = document.getElementById('planner-form');
  if (!form) return;
  const output = document.getElementById('plan-output');
  const status = document.getElementById('plan-status');
  let manuallyEdited = false;
  let inputsChanged = false;
  let exampleLoaded = true;
  const lang = () => window.BSVLabs ? window.BSVLabs.lang() : 'en';
  const text = (en, ja) => lang() === 'ja' ? ja : en;
  const read = () => Object.fromEntries(new FormData(form).entries());
  function localize() {
    document.querySelectorAll('option[data-en]').forEach(option => { option.textContent = option.dataset[lang()] || option.dataset.en; });
  }
  function generate() {
    const plan = buildPlan(read(), lang());
    output.value = plan.text;
    document.getElementById('plan-summary').textContent = `${plan.task} · ${plan.environment}. ${plan.notes.length ? plan.notes.join(' ') : text('Review the proposed criteria and run count before testing.', '実施前に、仮の基準と試行数を確認してください。')}`;
    status.textContent = text('Draft generated. You can edit the text before copying or saving.', '計画案を生成しました。コピー・保存前に本文を編集できます。');
    manuallyEdited = false;
    inputsChanged = false;
  }
  function loadExample() {
    form.elements.use.value = 'logistics';
    form.elements.environment.value = 'simulation';
    form.elements.owner.value = text('Robotics research lead', 'ロボティクス研究責任者');
    form.elements.criteria.value = text('At least 18 of 20 simulated deliveries complete without assistance; all injected blockage cases end in a logged stop; report time and interventions against the baseline.', '模擬搬送 20 回中 18 回以上が介入なしで完了。模擬閉塞の全試行で停止が記録される。比較対象に対する所要時間と介入数を報告する。');
    exampleLoaded = true;
    generate();
  }
  async function copy() {
    try {
      await navigator.clipboard.writeText(output.value);
      status.textContent = text('Plan copied.', '計画をコピーしました。');
    } catch (_) {
      output.focus(); output.select();
      status.textContent = text('The plan is selected. Use your browser’s Copy command.', '本文を選択しました。ブラウザのコピー操作で取得してください。');
    }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([output.value], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = `bsv-robotics-poc-${lang()}.txt`;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = text('Download prepared.', 'ダウンロードを開始しました。');
  }
  form.addEventListener('submit', event => { event.preventDefault(); generate(); });
  form.addEventListener('input', () => { inputsChanged = true; exampleLoaded = false; status.textContent = text('Inputs changed. Generate a new plan to apply them; the current draft is preserved.', '入力を変更しました。反映するには計画を再生成してください。現在の本文は保持しています。'); });
  output.addEventListener('input', () => { manuallyEdited = true; status.textContent = text('Manual edits are included when you copy or download.', '手動の編集はコピー・ダウンロードに含まれます。'); });
  document.getElementById('load-example').addEventListener('click', loadExample);
  document.getElementById('copy-plan').addEventListener('click', copy);
  document.getElementById('download-plan').addEventListener('click', download);
  document.addEventListener('bsv:language', () => {
    localize();
    if (manuallyEdited || inputsChanged) status.textContent = text('Your draft is preserved. Generate again to create the plan in English.', '編集中の本文を保持しました。日本語の計画を作る場合は再生成してください。');
    else if (exampleLoaded) loadExample();
    else generate();
  });
  localize(); loadExample();
})();
