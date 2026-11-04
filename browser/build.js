// XML/import and controlled item-input edits. Calculations run in the PoB worker.
export const LIMIT = 2_000_000;
const children = (node, name) => [...(node?.children ?? [])].filter(child => child.tagName === name);
const child = (node, name) => children(node, name)[0];
const text = node => [...node.childNodes].filter(n => n.nodeType === 3 || n.nodeType === 4).map(n => n.nodeValue).join('');
const setText = (node, value) => {for (const n of [...node.childNodes]) if (n.nodeType === 3 || n.nodeType === 4) n.remove(); node.insertBefore(node.ownerDocument.createTextNode(value), node.firstChild);};
const attr = (node, key) => node?.getAttribute(key);
export async function inflate(bytes, format, limit = LIMIT) {
  if (!globalThis.DecompressionStream) throw new Error('This app requires Safari 17 or newer (or another browser with DecompressionStream).');
  const reader = new Blob([bytes]).stream().pipeThrough(new DecompressionStream(format)).getReader();
  const parts = []; let length = 0;
  try {
    while (true) {const {done,value} = await reader.read(); if (done) break; length += value.length; if (length > limit) throw new Error('Decompressed file exceeds the size limit.'); parts.push(value);}
  } finally {await reader.cancel().catch(() => {});}
  const result = new Uint8Array(length); let offset=0; for (const part of parts) {result.set(part,offset); offset += part.length;} return result;
}
export async function decodeExport(value) {
  if (typeof value !== 'string' || value.length > LIMIT) throw new Error('Import exceeds the 2 MB limit.');
  let xml=value.trim();
  if (!xml.startsWith('<')) {
    try {const raw=atob(xml.replace(/-/g,'+').replace(/_/g,'/')); xml=new TextDecoder('utf-8',{fatal:true}).decode(await inflate(Uint8Array.from(raw,c=>c.charCodeAt(0)),'deflate'));}
    catch(error) {throw new Error('Paste a PoB2 export code or XML file, rather than a share URL. '+error.message);}
  }
  if (new TextEncoder().encode(xml).length > LIMIT || /<!DOCTYPE|<!ENTITY/i.test(xml)) throw new Error('Oversized XML or XML entity declarations are not supported.');
  parseXML(xml); return xml;
}
export function parseXML(xml) {
  const doc=new DOMParser().parseFromString(xml,'application/xml');
  if (doc.querySelector('parsererror') || doc.documentElement.tagName !== 'PathOfBuilding2') throw new Error('Expected a valid PathOfBuilding2 export.');
  return doc;
}
function selection(doc) {
  const root=doc.documentElement, build=child(root,'Build'), items=child(root,'Items'), tree=child(root,'Tree');
  if (!build || !items) throw new Error('Export needs Build and Items sections.');
  const itemSet=children(items,'ItemSet').find(s=>attr(s,'id')===attr(items,'activeItemSet'));
  if (!itemSet) throw new Error('Active item set is missing.');
  const specs=children(tree,'Spec'), index=Number(attr(tree,'activeSpec') ?? 1)-1;
  const spec=specs.find(s=>attr(s,'id') !== null && attr(s,'id')===attr(tree,'activeSpec')) ?? (Number.isInteger(index) && index>=0 ? specs[index] : null);
  const swap=(attr(itemSet,'useSecondWeaponSet') ?? attr(items,'useSecondWeaponSet'))==='true';
  return {root,build,items,tree,itemSet,spec,swap};
}
export function parseBuild(xml) {
  const doc=parseXML(xml), {root,build,items,itemSet,spec,swap}=selection(doc);
  const stats={}; for (const stat of children(build,'PlayerStat')) {const raw=attr(stat,'value'); if(raw?.trim() && Number.isFinite(Number(raw))) stats[attr(stat,'stat')]=Number(raw);}
  const inventory=new Map();
  for (const item of children(items,'Item')) {const lines=text(item).split(/\r?\n/).map(s=>s.trim()).filter(Boolean); if(lines.length<3) throw new Error('An item has incomplete text.'); const match=lines.map(s=>s.replace(/\{[^}]+\}/g,'')).map(s=>s.match(/^(\d+)% increased maximum Energy Shield$/)).find(Boolean); inventory.set(attr(item,'id'),{id:attr(item,'id'),name:lines[1],base:lines[2],text:lines.join('\n'),esIncrease:match ? Number(match[1]) : null});}
  const equipment=[];
  for (const slot of children(itemSet,'Slot')) {const name=attr(slot,'name') ?? ''; if(name.startsWith('Weapon') && name.includes('Swap')!==swap) continue; const item=inventory.get(attr(slot,'itemId')); if(item) equipment.push({...item,slot:name});}
  const nodes=new Set((attr(spec,'nodes') ?? '').split(','));
  const active=new Set((attr(child(spec,swap?'WeaponSet2':'WeaponSet1'),'nodes') ?? '').split(','));
  for (const node of (attr(child(spec,swap?'WeaponSet1':'WeaponSet2'),'nodes') ?? '').split(',')) if(!active.has(node)) nodes.delete(node);
  const jewels=[]; for (const socket of children(child(spec,'Sockets'),'Socket')) {const item=inventory.get(attr(socket,'itemId')); if(item && nodes.has(attr(socket,'nodeId'))) jewels.push({...item,slot:'Jewel '+attr(socket,'nodeId')});}
  const config=child(root,'Config'), configSet=children(config,'ConfigSet').find(s=>attr(s,'id')===attr(config,'activeConfigSet'));
  const quests=children(configSet,'Input').filter(i=>attr(i,'name')?.startsWith('quest')).map(i=>({name:attr(i,'name'),value:attr(i,'string')}));
  return {character:{level:attr(build,'level'),characterClass:attr(build,'className'),ascendancy:attr(build,'ascendClassName'),treeVersion:attr(spec,'treeVersion')},stats,equipment,jewels,quests,passiveNodeCount:(attr(spec,'nodes') ?? '').split(',').filter(Boolean).length,warnings:['These imported Life/ES values are saved references; use recalculation to independently check them.','Calculations run on your device using a pinned PoB engine. Only tree 0_5 is supported.','Spirit is diagnostic; the original export and engine disagree on unreserved Spirit.']};
}
export function prepareInput(xml) {
  const doc=parseXML(xml), {root,build,items,tree,itemSet,spec,swap}=selection(doc);
  if (!spec || attr(spec,'treeVersion')!=='0_5') throw new Error('The pinned engine currently supports tree 0_5 only.');
  const reference={}, resourceReference={};
  for (const stat of children(build,'PlayerStat')) {const name=attr(stat,'stat'), raw=attr(stat,'value'); if(raw?.trim() && Number.isFinite(Number(raw))) {if(['Life','EnergyShield'].includes(name)) reference[name]=Number(raw); if(['Spirit','SpiritUnreserved'].includes(name)) resourceReference[name]=Number(raw);} stat.remove();}
  for (const stat of children(build,'MinionStat')) stat.remove();
  return {xml:new XMLSerializer().serializeToString(doc),reference,metadata:{resourceReference,nodes:(attr(spec,'nodes') ?? '').split(',').filter(Boolean),treeVersion:attr(spec,'treeVersion'),activeSpec:attr(tree,'activeSpec'),activeItemSet:attr(items,'activeItemSet'),useSecondWeaponSet:swap?'true':'false',activeConfigSet:attr(child(root,'Config'),'activeConfigSet'),activeSkillSet:attr(child(root,'Skills'),'activeSkillSet')}};
}
const integer=(v,label,max,min=0)=>{if(!Number.isInteger(v)||v<min||v>max) throw new Error(`${label} must be an integer from ${min} to ${max}.`);return v;};
const keys=(v,allowed)=>{if(!v || Array.isArray(v) || typeof v!=='object' || Object.keys(v).some(k=>!allowed.includes(k))) throw new Error('Invalid or unsupported scenario fields.');};
export function applyScenario(xml, scenario) {
  keys(scenario,['jewels','chestEnergyShield','darknessRune','ingenuity']);
  const data=parseBuild(xml), doc=parseXML(xml), {items,spec}=selection(doc), changes=[];
  const inventory=new Map(children(items,'Item').map(i=>[attr(i,'id'),i]));
  if ('jewels' in scenario) {const c=scenario.jewels; keys(c,['mode','itemId','targetPercent']); if(!['one','all','remove'].includes(c.mode)) throw new Error('Invalid jewel mode.'); const candidates=data.jewels.filter(j=>c.mode==='all'?j.esIncrease!==null:j.id===c.itemId); if(!candidates.length) throw new Error('Select an allocated jewel in the active weapon set.'); if(c.mode!=='remove') integer(c.targetPercent,'Jewel increased ES',1000);
    for (const jewel of candidates) {if(c.mode==='remove') {const nodeId=jewel.slot.slice(6); children(child(spec,'Sockets'),'Socket').find(s=>attr(s,'nodeId')===nodeId).setAttribute('itemId','0'); changes.push({kind:'removeJewel',itemId:jewel.id,name:jewel.name,nodeId}); continue;}
      const item=inventory.get(jewel.id), lines=text(item).split('\n'), indices=lines.map((s,i)=>/^\s*\d+% increased maximum Energy Shield\s*$/.test(s)?i:-1).filter(i=>i>=0); if(indices.length!==1) throw new Error(jewel.name+' needs exactly one plain increased maximum ES modifier.'); const i=indices[0], before=Number(lines[i].match(/\d+/)[0]); lines[i]=lines[i].replace(/\d+% increased maximum Energy Shield/,`${c.targetPercent}% increased maximum Energy Shield`); setText(item,lines.join('\n')); changes.push({kind:'jewel',itemId:jewel.id,name:jewel.name,before,after:c.targetPercent});}}
  let chestES=null;
  if ('chestEnergyShield' in scenario) {chestES=integer(scenario.chestEnergyShield,'Final local chest ES',100000); const chest=data.equipment.find(i=>i.slot==='Body Armour'); if(!chest) throw new Error('No body armour is equipped.'); changes.push({kind:'chest',itemId:chest.id,name:chest.name,after:chestES});}
  if ('darknessRune' in scenario && 'ingenuity' in scenario) throw new Error('Choose a rune swap or a belt replacement, not both.');
  if ('darknessRune' in scenario) {const c=scenario.darknessRune; keys(c,['socket','rune','effectPercent']); integer(c.socket,'Socket number',2,1); if(!['None','Iron Rune','Greater Iron Rune','Perfect Iron Rune'].includes(c.rune)) throw new Error('Select a supported Iron Rune or empty socket.'); const belt=data.equipment.find(i=>i.slot==='Belt'); if(belt?.name!=='Darkness Enthroned' || !belt.text.includes('This item gains bonuses from Socketed Items as though it was a Body Armour')) throw new Error('The Body Armour variant of Darkness Enthroned must be equipped.'); const item=inventory.get(belt.id), lines=text(item).split('\n'), indices=lines.map((s,i)=>s.trim().startsWith('Rune: ')?i:-1).filter(i=>i>=0); const sockets=lines.filter(s=>s.trim().startsWith('Sockets: ')); if(indices.length!==2 || sockets.length!==1 || sockets[0].trim().split(/\s+/).length!==3) throw new Error('Expected two explicit rune socket bindings.'); const i=indices[c.socket-1], previous=lines[i].trim().slice(6); if(!['None','Fox Idol','Rune of the Blossom','Iron Rune','Greater Iron Rune','Perfect Iron Rune'].includes(previous)) throw new Error('Existing augment is outside the validated set.'); const effects=lines.map((s,i)=>/^\s*\d+% increased effect of Socketed Augment Items\s*$/.test(s)?i:-1).filter(i=>i>=0); if(effects.length!==1) throw new Error('Expected one explicit augment-effect roll.'); const ei=effects[0], oldEffect=Number(lines[ei].match(/\d+/)[0]), effect=integer(c.effectPercent ?? oldEffect,'Augment effect',100,50); lines[i]=lines[i].replace(/Rune: .+/,'Rune: '+c.rune); lines[ei]=lines[ei].replace(/\d+%/,effect+'%'); setText(item,lines.join('\n')); changes.push({kind:'darknessRune',name:belt.name,socket:c.socket,before:previous,after:c.rune,effectBefore:oldEffect,effectAfter:effect});}
  if ('ingenuity' in scenario) {const c=scenario.ingenuity; keys(c,['leftPercent','rightPercent','charmSlots']); const left=integer(c.leftPercent,'Left-ring effect',30,20),right=integer(c.rightPercent,'Right-ring effect',30,20),slots=integer(c.charmSlots,'Charm slots',3,1); const belt=data.equipment.find(i=>i.slot==='Belt'); if(!belt) throw new Error('Equip a belt before comparing a replacement.'); inventory.get(belt.id).replaceChildren(doc.createTextNode(`\nRarity: UNIQUE\nIngenuity\nUtility Belt\nImplicits: 2\nHas ${slots} Charm Slots\n20% of Flask Recovery applied Instantly\n0% reduced Charm Charges gained\n0% reduced Charm Charges used\n${left}% increased bonuses gained from left Equipped Ring\n${right}% increased bonuses gained from right Equipped Ring\n`)); changes.push({kind:'ingenuity',name:'Belt replacement',before:belt.name,after:'Ingenuity',leftPercent:left,rightPercent:right,charmSlots:slots});}
  return {xml:new XMLSerializer().serializeToString(doc),chestES,changes};
}
