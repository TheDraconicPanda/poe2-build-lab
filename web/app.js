import {applyScenario, decodeExport} from './build.js';
import {request, cancelCalculation} from './engine-client.js';
import {savedBuilds, saveBuild, deleteBuild, downloadBackup, readBackup} from './storage.js';
const $ = id => document.getElementById(id);
let build;
let importedExport;
let importGeneration = 0;
let activeSaveId, pendingSave, records=[];
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
  cancelCalculation();
  const restore = pendingSave; pendingSave = null;
  activeSaveId = restore?.id ?? crypto.randomUUID();
  importedExport = null;
  $('calculated').hidden = true;
  $('calc-message').textContent = '';
  setEngineBusy(false);
  $('scenario-results').hidden = true;
  $('scenario-message').textContent = '';
  $('message').textContent = 'Reading export…';
  $('results').hidden = true;
  try {
    const exportText = $('export').value;
    const data = await request('import', {export: exportText});
    if (generation !== importGeneration) return;
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
    $('jewel').replaceChildren(...data.jewels.map(j => {const o = document.createElement('option'); o.value = j.id; o.textContent = `${j.name} (${j.esIncrease == null ? 'no plain ES modifier' : `${j.esIncrease}% increased ES`})`; return o;}));
    for (const id of ['game-life','game-es']) $(id).value = '';
    $('edit-jewels').checked = true;
    $('edit-chest').checked = false;
    $('jewel-mode').value = 'one';
    $('chest-es').value = 400;
    $('target').value = 20;
    $('belt-mode').value = 'keep';
    const belt = data.equipment.find(item => item.slot === 'Belt');
    const effect = belt?.text.match(/(\d+)% increased effect of Socketed Augment Items/);
    $('belt-effect').value = effect ? effect[1] : 94;
    const runes = [...(belt?.text.matchAll(/^Rune: (.+)$/gm) ?? [])].map(match => match[1]);
    for (let index = 0; index < 2; index++) $('belt-socket').options[index].textContent = `Socket ${index + 1}: ${runes[index] ?? 'unknown'}`;
    $('belt-socket').value = '1';
    $('belt-rune').value = 'Iron Rune';
    $('ring-left').value = 30; $('ring-right').value = 20; $('belt-charms').value = 3;
    $('results').hidden = false;
    $('message').textContent = `Imported ${data.equipment.length} equipped items and ${data.jewels.length} jewels.`;
    $('build-name').value = restore?.name ?? `${data.character.ascendancy ?? data.character.characterClass} · Level ${data.character.level}`;
    if (restore) restoreScenario(restore.scenario);
    compare(); syncScenarioFields();
    await persistCurrent();
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
for (const id of ['game-life', 'game-es']) $(id).addEventListener('input', compare);

function syncScenarioFields() {
  const enabled = $('edit-jewels').checked;
  const mode = $('jewel-mode').value;
  $('jewel-mode').disabled = !enabled;
  $('jewel').disabled = !enabled || mode === 'all';
  $('target').disabled = !enabled || mode === 'remove';
  $('chest-es').disabled = !$('edit-chest').checked;
  const beltMode = $('belt-mode').value;
  $('darkness-fields').hidden = beltMode !== 'rune';
  $('ingenuity-fields').hidden = beltMode !== 'ingenuity';
  for (const id of ['belt-socket','belt-rune','belt-effect']) $(id).disabled = beltMode !== 'rune';
  for (const id of ['ring-left','ring-right','belt-charms']) $(id).disabled = beltMode !== 'ingenuity';
}
function setEngineBusy(busy) {
  $('calculate').disabled = busy;
  $('scenario-button').disabled = busy;
  $('scenario-fields').disabled = busy;
  $('cancel-calculation').hidden = !busy;
}
for (const id of ['edit-jewels','edit-chest','jewel-mode','jewel','target','chest-es','belt-mode','belt-socket','belt-rune','belt-effect','ring-left','ring-right','belt-charms']) {
  $(id).addEventListener('input', () => {
    $('scenario-results').hidden = true;
    $('scenario-message').textContent = '';
    syncScenarioFields();
  });
}
$('scenario-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!importedExport) return;
  const generation = importGeneration;
  const scenario = currentScenario();
  setEngineBusy(true);
  $('scenario-results').hidden = true;
  $('scenario-message').textContent = 'Calculating original and changed builds on this device…';
  try {
    const data = await request('compare', {export: importedExport, scenario}, message => {if(generation===importGeneration)$('scenario-message').textContent=message;});
    if (generation !== importGeneration) return;
    tableRows('scenario-totals', ['Life','EnergyShield'].map(stat => {
      const row = data.deltas[stat];
      return [stat === 'Life' ? 'Life' : 'Energy Shield', number(row.before), number(row.after), `${row.absolute > 0 ? '+' : ''}${number(row.absolute)}`, row.percent == null ? '—' : `${row.percent > 0 ? '+' : ''}${number(row.percent)}%`];
    }));
    $('scenario-baseline').textContent = data.baseline.reconciled ? 'The original calculated Life and ES both match the imported reference.' : 'Original calculated totals do not match both imported reference values. Investigate the baseline before trusting this comparison.';
    listRows('scenario-changes', data.changes.length ? data.changes.map(change => {
      if (change.kind === 'removeJewel') return `Remove ${change.name} from socket ${change.nodeId} (all its modifiers removed)`;
      if (change.kind === 'darknessRune') return `Socket ${change.socket}: ${change.before} → ${change.after}; augment effect ${change.effectBefore}% → ${change.effectAfter}%`;
      if (change.kind === 'ingenuity') return `${change.before} → Ingenuity; left ring +${change.leftPercent}%, right ring +${change.rightPercent}%, ${change.charmSlots} charm slots`;
      return `${change.name}: ${change.before} → ${change.after}${change.kind === 'chest' ? ' final local ES' : '% increased maximum ES'}`;
    }) : ['No changes requested.']);
    const beforeSpirit = data.baseline.resources, afterSpirit = data.upgraded.resources;
    $('scenario-resources').textContent = `Calculated unreserved Spirit (diagnostic): ${number(beforeSpirit.SpiritUnreserved)} → ${number(afterSpirit.SpiritUnreserved)}. Total Spirit: ${number(beforeSpirit.Spirit)} → ${number(afterSpirit.Spirit)}.`;
    listRows('interaction-equipment', data.upgraded.equipment.map(item => `${item.slot}: ${item.name}${item.runes.length ? ` · Sockets: ${item.runes.join(', ')}` : ''}`));
    const interactionMods = data.upgraded.ledger.filter(row => row.scope === 'Global' && (row.source.includes('Ring 1 Bonus Effect') || row.source.includes('Ring 2 Bonus Effect') || row.stat.startsWith('EffectOfBonusesFromRing') || (row.slot === 'Belt' || (row.source.startsWith('Item:') && data.changes.some(change => change.kind === 'darknessRune') && row.source.includes(':Darkness Enthroned')))));
    tableRows('interaction-mods', interactionMods.map(row => [row.stat, String(row.value), row.source]));
    const coverage = [...data.warnings];
    for (const [label, side] of [['Original',data.baseline],['Changed',data.upgraded]]) {
      for (const row of side.unsupported) coverage.push(`${label} unparsed modifier (${row.slot}): ${row.line}`);
    }
    listRows('scenario-warnings', coverage);
    $('scenario-provenance').textContent = `Engine ${data.upgraded.provenance.commit} · tree ${data.upgraded.provenance.treeVersion} · Saved totals removed on both sides.`;
    $('scenario-results').hidden = false;
    $('scenario-message').textContent = 'Comparison complete. Calculated on this device.';
    await persistCurrent();
  } catch(error) { if (generation === importGeneration) $('scenario-message').textContent = error.message; }
  finally { if (generation === importGeneration) {setEngineBusy(false); syncScenarioFields();} }
});

function listRows(id, lines) {
  $(id).replaceChildren(...lines.map(text => {const li = document.createElement('li'); li.textContent = text; return li;}));
}
function tableRows(id, rows) {
  $(id).replaceChildren(...rows.map(cells => {const tr = document.createElement('tr'); for (const value of cells) {const td = document.createElement('td'); td.textContent = value ?? '—'; tr.append(td);} return tr;}));
}
$('calculate').addEventListener('click', async () => {
  if (!importedExport) return;
  const generation = importGeneration;
  setEngineBusy(true);
  $('calculated').hidden = true;
  $('calc-message').textContent = 'Recalculating from items, tree, quests and skills. This can take up to a minute…';
  try {
    const data = await request('calculate', {export: importedExport}, message => {if(generation===importGeneration)$('calc-message').textContent=message;});
    if (generation !== importGeneration) return;
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
  finally { if (generation === importGeneration) {setEngineBusy(false); syncScenarioFields();} }
});

function currentScenario() {
  const scenario={};
  if ($('edit-jewels').checked) {
    scenario.jewels={mode:$('jewel-mode').value};
    if(scenario.jewels.mode!=='all') scenario.jewels.itemId=$('jewel').value;
    if(scenario.jewels.mode!=='remove') scenario.jewels.targetPercent=Number($('target').value);
  }
  if($('edit-chest').checked) scenario.chestEnergyShield=Number($('chest-es').value);
  if($('belt-mode').value==='rune') scenario.darknessRune={socket:Number($('belt-socket').value),rune:$('belt-rune').value,effectPercent:Number($('belt-effect').value)};
  if($('belt-mode').value==='ingenuity') scenario.ingenuity={leftPercent:Number($('ring-left').value),rightPercent:Number($('ring-right').value),charmSlots:Number($('belt-charms').value)};
  return scenario;
}
function restoreScenario(s={}) {
  $('edit-jewels').checked=Boolean(s.jewels); $('edit-chest').checked='chestEnergyShield' in s;
  if(s.jewels) {$('jewel-mode').value=s.jewels.mode;$('jewel').value=s.jewels.itemId ?? $('jewel').value;$('target').value=s.jewels.targetPercent ?? 20;}
  if('chestEnergyShield' in s) $('chest-es').value=s.chestEnergyShield;
  $('belt-mode').value=s.darknessRune?'rune':s.ingenuity?'ingenuity':'keep';
  if(s.darknessRune) {$('belt-socket').value=s.darknessRune.socket;$('belt-rune').value=s.darknessRune.rune;$('belt-effect').value=s.darknessRune.effectPercent ?? 94;}
  if(s.ingenuity) {$('ring-left').value=s.ingenuity.leftPercent;$('ring-right').value=s.ingenuity.rightPercent;$('belt-charms').value=s.ingenuity.charmSlots;}
}
async function refreshLibrary() {
  try {records=await savedBuilds();$('saved-builds').replaceChildren(...records.map(record=>{const option=document.createElement('option');option.value=record.id;option.textContent=record.name;return option;}));if(activeSaveId)$('saved-builds').value=activeSaveId;}
  catch(error) {$('library-status').textContent='Browser storage is unavailable. Use Export backup before closing this page.';}
}
async function persistCurrent() {
  if(!importedExport) return;
  const record={id:activeSaveId,name:$('build-name').value.trim().slice(0,200)||'Saved build',export:importedExport,scenario:currentScenario(),updatedAt:Date.now()};
  try {await saveBuild(record);await refreshLibrary();$('library-status').textContent='Saved on this device. Export a backup to keep a separate copy in Files.';}
  catch(error) {records=[...records.filter(r=>r.id!==record.id),record];$('library-status').textContent='Could not save in browser storage. Export a backup before closing this page.';}
}
$('save-build').addEventListener('click',persistCurrent);
$('load-build').addEventListener('click',()=>{const record=records.find(r=>r.id===$('saved-builds').value);if(!record)return;pendingSave=record;$('export').value=record.export;$('import-form').requestSubmit();});
$('delete-build').addEventListener('click',async()=>{const id=$('saved-builds').value;if(!id)return;try{await deleteBuild(id);if(id===activeSaveId)activeSaveId=crypto.randomUUID();await refreshLibrary();$('library-status').textContent='Saved copy removed. The current imported build is still open.';}catch(error){$('library-status').textContent=error.message;}});
$('export-backup').addEventListener('click',()=>{
  const snapshot=[...records];
  if(importedExport) {
    const record={id:activeSaveId,name:$('build-name').value.trim().slice(0,200)||'Saved build',export:importedExport,scenario:currentScenario(),updatedAt:Date.now()};
    const index=snapshot.findIndex(r=>r.id===record.id);
    if(index>=0)snapshot[index]=record;else snapshot.push(record);
  }
  // Start the file download within the tap gesture for iOS Safari. IndexedDB
  // writes can finish afterward; the backup already contains the current state.
  if(snapshot.length) {downloadBackup(snapshot);void persistCurrent();}
  else $('library-status').textContent='Import a build before exporting a backup.';
});
$('backup-file').addEventListener('change',async event=>{const file=event.target.files[0];if(!file)return;try{if(file.size>20_000_000)throw new Error('Backup exceeds 20 MB.');const restored=readBackup(await file.text());for(const record of restored){applyScenario(await decodeExport(record.export),record.scenario);const existing=records.find(r=>r.id===record.id);await saveBuild({...record,id:existing?crypto.randomUUID():record.id});}await refreshLibrary();$('library-status').textContent=`Restored ${restored.length} build(s). Select one and tap Load.`;}catch(error){$('library-status').textContent=error.message;}finally{event.target.value='';}});
$('cancel-calculation').addEventListener('click',()=>{cancelCalculation();setEngineBusy(false);syncScenarioFields();});
await refreshLibrary();
if('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').then(()=>{$('offline-status').textContent='Preparing offline files…';navigator.serviceWorker.addEventListener('message',event=>{if(event.data==='offline-ready')$('offline-status').textContent='Ready offline on this device.';});navigator.serviceWorker.ready.then(()=>navigator.serviceWorker.controller?.postMessage('status'));}).catch(()=>{$('offline-status').textContent='Offline caching is unavailable; your saved builds can still be backed up.';});
