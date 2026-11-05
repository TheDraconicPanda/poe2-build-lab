import {decodeExport,parseBuild,prepareInput,applyScenario} from './build.js';
let worker, pending, nextId=0;
export function cancelCalculation() {
  worker?.terminate(); worker=null;
  if(pending) {pending.reject(new Error('Calculation cancelled.')); pending=null;}
}
function run(prepared,progress) {
  if(pending) return Promise.reject(new Error('A calculation is already running.'));
  if(!worker) {
    worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
    worker.onmessage=({data})=>{
      if(data.type==='progress') {pending?.progress?.(data.message);return;}
      if(!pending || data.id!==pending.id) return;
      const request=pending; pending=null;
      if(data.error) {request.reject(new Error(data.error));return;}
      request.resolve(data);
    };
    worker.onerror=event=>{const reject=pending?.reject;cancelCalculation();reject?.(new Error(event.message || 'The browser could not start the calculation engine.'));};
  }
  return new Promise((resolve,reject)=>{const id=++nextId; pending={id,resolve,reject,progress};worker.postMessage({id,xml:prepared.xml,metadata:prepared.metadata});});
}
export async function calculateXML(xml, chestES=null, progress=()=>{}) {
  const prepared=prepareInput(xml);
  if(chestES!==null) prepared.metadata.bodyArmourEnergyShield=chestES;
  const {result,manifest}=await run(prepared,progress);
  if(result.missingAllocatedNodes.length) throw new Error('Allocated nodes are absent from this pinned tree: '+result.missingAllocatedNodes.join(', '));
  result.reference=prepared.reference;
  result.comparison=Object.fromEntries(Object.entries(result.totals).map(([stat,value])=>[stat,{reference:prepared.reference[stat] ?? null,calculated:value,difference:stat in prepared.reference?value-prepared.reference[stat]:null}]));
  result.reconciled=['Life','EnergyShield'].every(stat=>prepared.reference[stat]===result.totals[stat]);
  result.provenance={engine:'PathOfBuildingCommunity/PathOfBuilding-PoE2',commit:manifest.engineCommit,treeVersion:prepared.metadata.treeVersion,savedOutputsRemoved:true,patch:'0.5.5 user-confirmed fixture; browser runtime compatibility is build-specific',runtime:manifest.runtime,selection:prepared.metadata};
  return result;
}
export async function request(method, data, progress=()=>{}) {
  const xml=await decodeExport(data.export);
  if(method==='import') return parseBuild(xml);
  if(method==='calculate') return calculateXML(xml,null,progress);
  if(method!=='compare') throw new Error('Unknown operation.');
  const edited=applyScenario(xml,data.scenario);
  progress('Calculating original build locally…');const baseline=await calculateXML(xml,null,progress);
  progress('Calculating changed build locally…');const after=await calculateXML(edited.xml,edited.chestES,progress);
  for(const change of edited.changes) if(change.kind==='chest') change.before=baseline.items.find(i=>i.slot==='Body Armour')?.energyShield;
  const deltas=Object.fromEntries(Object.entries(baseline.totals).map(([stat,value])=>[stat,{before:value,after:after.totals[stat],absolute:after.totals[stat]-value,percent:value?(after.totals[stat]-value)/value*100:null}]));
  const warnings=['Calculated entirely on your device with the pinned PoB engine. Current game validation is unresolved. Matching an exported reference does not prove game accuracy.','Jewel stat edits retain other modifiers; chest ES holds its other stats and sockets fixed.'];
  if(data.scenario.darknessRune) warnings.push('The selected augment and its Bonded benefits are replaced. Rune modifiers are rebuilt in the Body Armour context.');
  if(data.scenario.ingenuity) warnings.push('Ingenuity replaces the entire belt and removes its socket effects. Left = Ring 1; right = Ring 2. The current-version template has neutral charm-charge rolls.');
  for(const [label,side] of [['Original',baseline],['Changed',after]]) if(side.resources.SpiritUnreserved<0) warnings.unshift(`${label} build has insufficient Spirit for the selected skills. Defence totals are conditional on that skill setup.`);
  for(const [stat,saved] of Object.entries(baseline.provenance.selection.resourceReference)) if(baseline.resources[stat]!==saved) warnings.push(`${stat} is diagnostic and not reconciled: original engine value ${baseline.resources[stat]}, exported value ${saved}.`);
  if(!baseline.reconciled) warnings.unshift('The calculated baseline does not match both exported totals. Resolve this before trusting the upgrade.');
  return {baseline,upgraded:after,changes:edited.changes,deltas,warnings};
}
