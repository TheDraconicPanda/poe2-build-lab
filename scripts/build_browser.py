"""Package pinned PoB Lua/data into a static browser asset. No user data included."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'scripts'))
from setup_engine import checkout, PINS


def compat(source, name):
    """Expand this pinned revision's LuaJIT syntax extensions to Lua 5.4 syntax."""
    if name in ('Item.lua','BuildExportPoE2.lua'):
        lines = source.splitlines()
        counter = 0
        while True:
            ci = next((i for i,line in enumerate(lines) if re.search(r'^\s*continue\s*$|then continue end',line)),None)
            if ci is None:
                break
            candidates = [i for i in range(ci) if re.match(r'^\s*for .* do\s*$',lines[i]) and len(re.match(r'^\s*',lines[i])[0]) < len(re.match(r'^\s*',lines[ci])[0])]
            fi = max(candidates)
            indent = re.match(r'^\s*',lines[fi])[0]
            ei = next(i for i in range(ci+1,len(lines)) if lines[i] == indent+'end')
            counter += 1
            label = 'browser_continue_'+str(counter)
            lines[ci] = re.sub(r'\bcontinue\b','goto '+label,lines[ci])
            lines.insert(ei,indent+'\tend\n'+indent+'\t::'+label+'::')
            lines.insert(fi+1,indent+'\tdo')
        source = '\n'.join(lines)+'\n'
    source = re.sub(r'^#[^\n]*','',source)
    source = re.sub(r'(\b[\w.]+(?:\[[\w]+\])?)\s*([+-])=\s*(\d+|count)\b',r'\1 = \1 \2 (\3)',source)
    source = re.sub(r'y \+= (self.controls.displayItem(?:BaseVariant|Version):IsShown\(\) and 24 or 0)',r'y = y + (\1)',source)
    source = re.sub(r'^(\s*)(\w+) \.\.= (.+)$',r'\1\2 = \2 .. (\3)',source,flags=re.M)
    replacements = {
        'SkillType?.[skillTypeMap[skillTypeMaybe]]':'(SkillType and SkillType[skillTypeMap[skillTypeMaybe]])',
        'activeGem.gemData?.gameId':'(activeGem.gemData and activeGem.gemData.gameId)',
        'gem.gemData?.grantedEffect.support':'(gem.gemData and gem.gemData.grantedEffect.support)',
        'gem.gemData?.gameId':'(gem.gemData and gem.gemData.gameId)',
        'loadout?.specId':'(loadout and loadout.specId)',
        'loadout?.skillSetId':'(loadout and loadout.skillSetId)',
        'loadout?.itemSetId':'(loadout and loadout.itemSetId)',
        'displayInstance.gemData?.gemType':'(displayInstance.gemData and displayInstance.gemData.gemType)',
        '|_, key| -> skillCfg.skillCond[key] or cfg.skillCond[key]':'function(_, key) return skillCfg.skillCond[key] or cfg.skillCond[key] end',
    }
    for before,after in replacements.items():
        source = source.replace(before,after)
    if name == 'dkjson.lua':
        source = source.replace('local _ENV = nil','local table = table\nlocal _ENV = nil')
    if name == 'HeadlessWrapper.lua':
        source = source.replace('runCallback("OnFrame") -- Need at least one frame for everything to initialise', '-- Initial frame is deferred until an imported build is loaded.')
    return source


def main():
    checkout('pob2',ROOT / '.local/pob2')
    source = ROOT / '.local/pob2'
    files = {}
    for base,virtual in [(source/'src','/pob/src'),(source/'runtime/lua','/pob/runtime/lua')]:
        for path in sorted(base.rglob('*')):
            rel = path.relative_to(base)
            if not path.is_file() or path.suffix not in ('.lua','.json','.txt','.xml'):
                continue
            if 'Export' in rel.parts or (rel.parts[0]=='TreeData' and len(rel.parts)>1 and rel.parts[1] in ('0_1','0_2','0_3','0_4')):
                continue
            text = path.read_text()
            files[virtual+'/'+rel.as_posix()] = compat(text,path.name) if path.suffix=='.lua' else text
    files['/pob/manifest.xml'] = (source/'manifest.xml').read_text()
    files['/runner.lua'] = (ROOT/'engine/runner.lua').read_text()
    bundle = gzip.compress(json.dumps(files,separators=(',',':')).encode(),mtime=0)
    dist = ROOT/'dist'
    if dist.exists():
        shutil.rmtree(dist)
    shutil.copytree(ROOT/'web',dist)
    (dist/'.nojekyll').write_text('')
    (dist/'engine.pack').write_bytes(bundle)
    (dist/'compat.lua').write_text((ROOT/'browser/compat.lua').read_text())
    for file in ['build.js','engine-client.js','storage.js']:
        shutil.copyfile(ROOT/'browser'/file,dist/file)
    licenses = dist/'licenses'
    licenses.mkdir()
    shutil.copyfile(source/'LICENSE.md',licenses/'PoB2-LICENSE.md')
    shutil.copyfile(ROOT/'node_modules/wasmoon/LICENSE',licenses/'Wasmoon-LICENSE.txt')
    shutil.copyfile(ROOT/'browser/LUA-LICENSE.txt',licenses/'Lua-LICENSE.txt')
    manifest = dict(engineCommit=PINS['pob2']['commit'],sha256=hashlib.sha256(bundle).hexdigest(),bytes=len(bundle),runtime='wasmoon-1.16.0 / Lua 5.4',files=len(files))
    (dist/'engine-manifest.json').write_text(json.dumps(manifest))
    fingerprint = hashlib.sha256(bundle + b''.join(p.read_bytes() for folder in ('web','browser') for p in sorted((ROOT/folder).rglob('*')) if p.is_file()) + (ROOT/'package-lock.json').read_bytes()).hexdigest()[:16]
    sw = dist/'sw.js'
    sw.write_text(sw.read_text().replace('browser-v1-20261104','browser-v1-'+fingerprint))
    print(f'Static engine bundle: {len(files)} files, {len(bundle)/1024/1024:.2f} MiB gzip')

if __name__=='__main__':
    main()
