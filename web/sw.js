const PREFIX='poe2-build-lab:'+new URL(self.registration.scope).pathname+':';
const VERSION=PREFIX+'browser-v1-20261104';
const ASSETS=['./','./index.html','./style.css','./app.js','./build.js','./engine-client.js','./storage.js','./worker.js','./compat.lua','./glue.wasm','./engine.pack','./engine-manifest.json','./manifest.webmanifest'];
self.addEventListener('install',event=>event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const name of await caches.keys())if(name.startsWith(PREFIX)&&name!==VERSION)await caches.delete(name);await self.clients.claim();for(const client of await self.clients.matchAll())client.postMessage('offline-ready');})()));
self.addEventListener('message',event=>{if(event.data==='status')event.source?.postMessage('offline-ready');});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET'||new URL(event.request.url).origin!==self.location.origin)return;event.respondWith(caches.open(VERSION).then(async cache=>(await cache.match(event.request))??fetch(event.request)));});
