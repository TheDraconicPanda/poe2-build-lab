const DB='poe2-build-lab:'+new URL('.',import.meta.url).pathname;
function database() {return new Promise((resolve,reject)=>{const req=indexedDB.open(DB,1);req.onupgradeneeded=()=>req.result.createObjectStore('builds',{keyPath:'id'});req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});}
export async function savedBuilds() {const db=await database();try{return await new Promise((resolve,reject)=>{const req=db.transaction('builds').objectStore('builds').getAll();req.onsuccess=()=>resolve(req.result.sort((a,b)=>b.updatedAt-a.updatedAt));req.onerror=()=>reject(req.error);});}finally{db.close();}}
export async function saveBuild(record) {const db=await database();try{await new Promise((resolve,reject)=>{const tx=db.transaction('builds','readwrite');tx.objectStore('builds').put(record);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error ?? new Error('Save aborted.'));});}finally{db.close();}}
export async function deleteBuild(id) {const db=await database();try{await new Promise((resolve,reject)=>{const tx=db.transaction('builds','readwrite');tx.objectStore('builds').delete(id);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});}finally{db.close();}}
export function downloadBackup(records) {
  const blob=new Blob([JSON.stringify({format:'poe2-build-lab',version:1,builds:records},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='poe2-build-lab-backup.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
}
export function readBackup(text) {
  const data=JSON.parse(text);
  if(data.format!=='poe2-build-lab'||data.version!==1||!Array.isArray(data.builds)||data.builds.length>100) throw new Error('Invalid Build Lab backup.');
  return data.builds.map(record=>{if(typeof record.export!=='string'||record.export.length>2_000_000||typeof record.name!=='string'||record.name.length>200||typeof record.id!=='string'||record.id.length>100||!record.scenario||typeof record.scenario!=='object'||Array.isArray(record.scenario))throw new Error('Invalid saved build in backup.');return {id:record.id,name:record.name,export:record.export,scenario:record.scenario,updatedAt:Date.now()};});
}
