"""Run regression vectors through the actual static app's WASM engine."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
XML=(ROOT/'tests/fixtures/abyssal-lich-0.5.5.xml').read_text()
CASES=json.loads((ROOT/'tests/fixtures/defence-scenarios.json').read_text())['cases']
with sync_playwright() as p:
    engine=os.environ.get('BROWSER_ENGINE','chromium')
    options={'headless':True}
    if engine=='chromium' and Path('/usr/bin/chromium').exists():
        options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    browser=getattr(p,engine).launch(**options)
    page=browser.new_page()
    posts=[]
    page.on('request',lambda req: posts.append(req.url) if req.method!='GET' else None)
    page.goto(os.environ.get('BROWSER_BASE_URL','http://127.0.0.1:8001'))
    def request(method, xml=XML, scenario=None):
        return page.evaluate('''async ({method,xml,scenario}) => {
          const {request}=await import('./engine-client.js');
          return request(method,{export:xml,scenario});
        }''',dict(method=method,xml=xml,scenario=scenario))
    for case in CASES:
        result=request('compare',scenario=case['scenario'])
        assert result['baseline']['totals']==dict(Life=1892,EnergyShield=6091),case['name']
        assert result['upgraded']['totals']==case['expected'],(case['name'],result['upgraded']['totals'])
        print('PASS',case['name'],result['upgraded']['totals'],flush=True)
    interactions=[('Iron Rune',6386,31),('Greater Iron Rune',6415,34),('Perfect Iron Rune',6453,38)]
    for rune,es,increase in interactions:
        result=request('compare',scenario={'darknessRune':{'socket':1,'rune':rune,'effectPercent':94}})
        assert result['upgraded']['totals']==dict(Life=1892,EnergyShield=es),rune
        rows=result['upgraded']['ledger']
        assert sum(r['value'] for r in rows if r['scope']=='Global' and r['source'].startswith('Item:8:') and r['stat']=='EnergyShield')==increase
        print('PASS',rune,flush=True)
    for left,right,life,es in [(30,20,1919,6122),(20,30,1922,6122),(30,30,1927,6129)]:
        result=request('compare',scenario={'ingenuity':{'leftPercent':left,'rightPercent':right,'charmSlots':3}})
        assert result['upgraded']['totals']==dict(Life=life,EnergyShield=es)
        assert any('insufficient Spirit' in s for s in result['warnings'])
        print('PASS','Ingenuity',left,right,flush=True)
    result=request('compare',xml=XML.replace('Rune: Fox Idol','Rune: Greater Iron Rune'),scenario={'darknessRune':{'socket':2,'rune':'Greater Iron Rune'}})
    assert result['upgraded']['totals']['EnergyShield']==6749
    result=request('calculate',xml=XML.replace('stat="Life" value="1892"','stat="Life" value="999999"').replace('stat="EnergyShield" value="6091"','stat="EnergyShield" value="1"'))
    assert result['totals']==dict(Life=1892,EnergyShield=6091) and not result['reconciled']
    result=request('calculate',xml=XML.replace('Luminous Shard','Éclat 测试'))
    assert result['totals']==dict(Life=1892,EnergyShield=6091)
    assert any('Éclat 测试' in row['source'] for row in result['ledger'])
    for scenario in [{'chestEnergyShield':True},{'jewels':{'mode':'one','itemId':'999','targetPercent':20}},{'darknessRune':{'socket':0,'rune':'Iron Rune'}},{'ingenuity':{'leftPercent':80,'rightPercent':80,'charmSlots':3}}]:
        failed=page.evaluate('''async ({xml,scenario})=>{const {request}=await import('./engine-client.js');try{await request('compare',{export:xml,scenario});return false;}catch{return true;}}''',dict(xml=XML,scenario=scenario))
        assert failed,scenario
    assert posts==[],posts
    browser.close()
print('Browser WASM parity passed; no POSTs or calculation server used.')
