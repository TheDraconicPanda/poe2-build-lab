const $ = id => document.getElementById(id);
let build;
let importedExport;
let importGeneration = 0;
const number = value => value == null ? 'Not exported' : value.toLocaleString(undefined, {maximumFractionDigits: 2});
$('file').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 1900000) { $('message').textContent = 'File exceeds the import size limit.'; return; }
  $('export').value = await file.text();
});
$('import-form').addEventListener('submit', async event => {
  event.preventDefault();
  const generation = ++importGeneration;
  importedExport = null;
  $('calculated').hidden = true;
  $('calc-message').textContent = '';
  $('calculate').disabled = false;
  $('message').textContent = 'Reading export…';
  $('results').hidden = true;
  try {
    const exportText = $('export').value;
    const response = await fetch('/api/import', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({export: exportText})});
    const data = await response.json();
    if (generation !== importGeneration) return;
    if (!response.ok) throw new Error(data.error);
    build = data;
    importedExport = exportText;
    $('character').textContent = `Level ${data.character.level} ${data.character.characterClass} · ${data.character.ascendancy} · Tree ${data.character.treeVersion ?? 'unknown'}`;
    $('life').textContent = number(data.stats.Life);
    $('es').textContent = number(data.stats.EnergyShield);
    $('nodes').textContent = data.passiveNodeCount;
    $('warnings').replaceChildren(...data.warnings.map(text => {const li = document.createElement('li'); li.textContent = text; return li;}));
    $('items').replaceChildren(...[...data.equipment, ...data.jewels].map(item => {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = `${item.slot} · ${item.name} · ${item.base}`;
      const pre = document.createElement('pre'); pre.textContent = item.text;
      details.append(summary, pre); return details;
    }));
    $('quests').replaceChildren(...data.quests.map(quest => { const li = document.createElement('li'); li.textContent = `${quest.name.replace(/^quest/, '')}: ${quest.value}`; return li; }));
    if (!data.quests.length) {const li = document.createElement('li'); li.textContent = 'No selected quest rewards exported.'; $('quests').append(li);}
    $('jewel').replaceChildren(...data.jewels.filter(j => j.esIncrease != null).map(j => {const o = document.createElement('option'); o.value = j.id; o.textContent = `${j.name} (${j.esIncrease}%)`; return o;}));
    for (const id of ['game-life','game-es','pool']) $(id).value = '';
    $('all').checked = false;
    $('target').value = 20;
    $('results').hidden = false;
    $('message').textContent = `Imported ${data.equipment.length} equipped items and ${data.jewels.length} jewels.`;
    compare(); estimate();
  } catch(error) { build = null; $('message').textContent = error.message; }
});
function compare() {
  if (!build) return;
  const messages = [];
  for (const [id, stat] of [['game-life','Life'], ['game-es','EnergyShield']]) {
    if ($(id).value === '' || !$(id).validity.valid || build.stats[stat] == null) continue;
    const delta = Number($(id).value) - build.stats[stat];
    messages.push(`${stat}: ${delta === 0 ? 'reported values match' : `game differs by ${number(delta)}`}`);
  }
  $('comparison').textContent = messages.join(' · ') || 'Enter game values to compare.';
}
function estimate() {
  if (!build) return;
  const candidates = build.jewels.filter(j => j.esIncrease != null && ($('all').checked || j.id === $('jewel').value));
  if (!$('pool').value || !candidates.length || !$('pool').validity.valid || !$('target').validity.valid || !$('target').value || build.stats.EnergyShield == null) {
    $('estimate').textContent = 'Enter a valid full increased-ES pool and select a jewel modifier.'; return;
  }
  const pool = Number($('pool').value), target = Number($('target').value);
  const delta = candidates.reduce((sum, j) => sum + target - j.esIncrease, 0);
  if (100 + pool + delta < 0) { $('estimate').textContent = 'The resulting increased-ES pool is invalid.'; return; }
  const after = build.stats.EnergyShield * (100 + pool + delta) / (100 + pool);
  $('estimate').textContent = `Illustrative ES: ${number(after)} (${after >= build.stats.EnergyShield ? '+' : ''}${number(after - build.stats.EnergyShield)}). Additive pool change: ${number(delta)} percentage points across ${candidates.length} jewel(s).`;
}
for (const id of ['game-life', 'game-es']) $(id).addEventListener('input', compare);
for (const id of ['pool', 'jewel', 'target', 'all']) $(id).addEventListener('input', estimate);

function listRows(id, lines) {
  $(id).replaceChildren(...lines.map(text => {const li = document.createElement('li'); li.textContent = text; return li;}));
}
function tableRows(id, rows) {
  $(id).replaceChildren(...rows.map(cells => {const tr = document.createElement('tr'); for (const value of cells) {const td = document.createElement('td'); td.textContent = value ?? '—'; tr.append(td);} return tr;}));
}
$('calculate').addEventListener('click', async () => {
  if (!importedExport) return;
  const generation = importGeneration;
  $('calculate').disabled = true;
  $('calculated').hidden = true;
  $('calc-message').textContent = 'Recalculating from items, tree, quests and skills. This can take up to a minute…';
  try {
    const response = await fetch('/api/calculate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({export: importedExport})});
    const data = await response.json();
    if (generation !== importGeneration) return;
    if (!response.ok) throw new Error(data.error);
    $('calculated-life').textContent = number(data.totals.Life);
    $('calculated-es').textContent = number(data.totals.EnergyShield);
    $('calc-comparison').textContent = data.reconciled ? 'Both calculated totals match the export. Saved outputs were removed before calculation.' : Object.entries(data.comparison).map(([stat, row]) => `${stat}: ${row.reference == null ? 'no exported reference' : `difference ${number(row.difference)}`}`).join(' · ');
    $('calc-provenance').textContent = `Engine ${data.provenance.commit} · tree ${data.provenance.treeVersion} · ${data.provenance.patch}`;
    listRows('life-breakdown', data.breakdown.Life.lines);
    tableRows('es-breakdown', data.breakdown.EnergyShield.slots.map(row => [row.description || row.source, number(row.base), row.increased || '× 1', row.more || '× 1', row.total]));
    listRows('calc-warnings', [
      'Agreement validates these two totals for this build and engine snapshot; it does not prove all item or combat mechanics are supported.',
      ...data.unsupported.map(row => `Unparsed modifier (${row.slot}): ${row.line}`),
      'The upstream tree logs missing connector nodes at startup. All allocated node IDs in this import were checked and exist.'
    ]);
    tableRows('ledger', data.ledger.map(row => [row.scope, `${row.stat} / ${row.kind}`, String(row.value), row.sourceName ? `${row.sourceName} (${row.source})` : row.source]));
    $('diagnostics').textContent = data.diagnostics.join('\n');
    $('calculated').hidden = false;
    $('calc-message').textContent = 'Recalculation complete.';
  } catch(error) { if (generation === importGeneration) $('calc-message').textContent = error.message; }
  finally { if (generation === importGeneration) $('calculate').disabled = false; }
});
