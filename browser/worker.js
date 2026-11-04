import {LuaFactory} from 'wasmoon';
import {inflate} from './build.js';
let factory, prelude, manifest;
const progress = message => self.postMessage({type:'progress',message});
async function initialize() {
  if (factory) return;
  progress('Downloading the pinned calculation engine…');
  const base=new URL('.',import.meta.url);
  manifest=await (await fetch(new URL('engine-manifest.json',base))).json();
  const packed=new Uint8Array(await (await fetch(new URL('engine.pack',base))).arrayBuffer());
  const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',packed))].map(b=>b.toString(16).padStart(2,'0')).join('');
  if(digest!==manifest.sha256) throw new Error('Engine integrity check failed. Reload online to refresh its files.');
  const files=JSON.parse(new TextDecoder().decode(await inflate(packed,'gzip',100_000_000)));
  const staged=new LuaFactory(new URL('glue.wasm',base).href);
  for(const [name,content] of Object.entries(files)) await staged.mountFile(name,content);
  const loadedPrelude=await (await fetch(new URL('compat.lua',base))).text();
  factory=staged;prelude=loadedPrelude;
  progress('Engine loaded. Calculating locally on your device…');
}
let running=false;
self.onmessage=async ({data})=>{
  if(running) {self.postMessage({id:data.id,error:'A calculation is already running.'}); return;}
  running=true; let lua;
  try {
    await initialize();
    await factory.mountFile('/input.xml',data.xml);
    await factory.mountFile('/metadata.json',JSON.stringify(data.metadata));
    const module=await factory.getLuaModule(); module.module.FS.chdir('/pob/src');
    lua=await factory.createEngine({enableProxy:false,injectObjects:false,functionTimeout:90000});
    await lua.doString(prelude);
    await lua.doFile('/runner.lua');
    const result=JSON.parse(lua.global.get('ResultJSON'));
    if(!Number.isFinite(result.totals.Life) || !Number.isFinite(result.totals.EnergyShield)) throw new Error('The engine did not produce finite defence totals.');
    self.postMessage({id:data.id,result,manifest});
  } catch(error) {self.postMessage({id:data.id,error:String(error.message ?? error)});}
  finally {if(lua)lua.global.close(); running=false;}
};
