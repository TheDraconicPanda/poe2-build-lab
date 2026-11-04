"""Local PoB2 audit server. Python 3.12+, no external dependencies."""
import base64
import json
import math
import re
import zlib
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
LIMIT = 2_000_000


def decode_build(text):
    text = text.strip()
    if len(text) > LIMIT:
        raise ValueError('Import exceeds the 2 MB limit.')
    if text.startswith('<'):
        xml = text
    else:
        try:
            packed = base64.b64decode(text + '=' * (-len(text) % 4), altchars=b'-_', validate=True)
            decoder = zlib.decompressobj()
            raw = decoder.decompress(packed, LIMIT + 1)
            if len(raw) > LIMIT or not decoder.eof:
                raise ValueError('Invalid or oversized compressed export.')
            xml = raw.decode('utf-8')
        except (ValueError, zlib.error, UnicodeError) as exc:
            raise ValueError('Paste a PoB2 export code or XML file, rather than a share URL.') from exc
    if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
        raise ValueError('XML declarations containing entities are not supported.')
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ValueError('The export contains invalid XML.') from exc
    if root.tag != 'PathOfBuilding2':
        raise ValueError('Expected a PathOfBuilding2 export.')
    return root


def parse_build(text):
    root = decode_build(text)
    build = root.find('Build')
    if build is None:
        raise ValueError('Export has no Build section.')
    stats = {}
    for stat in build.findall('PlayerStat'):
        try:
            value = float(stat.get('value', ''))
        except ValueError:
            continue
        if math.isfinite(value):
            stats[stat.get('stat')] = value
    items = {}
    container = root.find('Items')
    if container is None:
        raise ValueError('Export has no Items section.')
    for item in container.findall('Item'):
        lines = [line.strip() for line in (item.text or '').splitlines() if line.strip()]
        if len(lines) < 3:
            raise ValueError('An item has incomplete text.')
        clean = [re.sub(r'\{[^}]+\}', '', line) for line in lines]
        match = next((re.fullmatch(r'(\d+)% increased maximum Energy Shield', line) for line in clean if re.fullmatch(r'(\d+)% increased maximum Energy Shield', line)), None)
        items[item.get('id')] = dict(id=item.get('id'), name=lines[1], base=lines[2], text='\n'.join(lines), esIncrease=int(match[1]) if match else None)
    active = container.get('activeItemSet')
    sets = container.findall('ItemSet')
    item_set = next((s for s in sets if s.get('id') == active), None)
    if item_set is None:
        raise ValueError('Active item set is missing; cannot determine equipped items.')
    tree = root.find('Tree')
    spec = next((s for s in tree.findall('Spec') if s.get('id') == tree.get('activeSpec')), None) if tree is not None else None
    # PoB commonly identifies specs by one-based position rather than an id.
    if spec is None and tree is not None:
        try:
            index = int(tree.get('activeSpec', '1')) - 1
            if index >= 0:
                spec = tree.findall('Spec')[index]
        except (ValueError, IndexError):
            pass
    equipped = []
    swap = item_set.get('useSecondWeaponSet', container.get('useSecondWeaponSet')) == 'true'
    for slot in item_set.findall('Slot'):
        name = slot.get('name', '')
        if name.startswith('Weapon') and (('Swap' in name) != swap):
            continue
        item = items.get(slot.get('itemId'))
        if item:
            equipped.append(dict(item, slot=name))
    jewels = []
    if spec is not None:
        nodes = set(spec.get('nodes', '').split(','))
        inactive_set = spec.find('WeaponSet1' if swap else 'WeaponSet2')
        active_set = spec.find('WeaponSet2' if swap else 'WeaponSet1')
        inactive_nodes = set(inactive_set.get('nodes', '').split(',')) if inactive_set is not None else set()
        active_nodes = set(active_set.get('nodes', '').split(',')) if active_set is not None else set()
        nodes -= inactive_nodes - active_nodes
        for socket in spec.findall('./Sockets/Socket'):
            item = items.get(socket.get('itemId'))
            if item and socket.get('nodeId') in nodes:
                jewels.append(dict(item, slot='Jewel ' + socket.get('nodeId')))
    config = root.find('Config')
    config_set = next((s for s in config.findall('ConfigSet') if s.get('id') == config.get('activeConfigSet')), None) if config is not None else None
    quests = [dict(name=i.get('name'), value=i.get('string')) for i in config_set.findall('Input') if i.get('name', '').startswith('quest')] if config_set is not None else []
    warnings = [
        'Life and ES below are saved PoB results, not independently calculated totals.',
        'Passive node IDs require matching versioned tree data; skills, conditions, conversions and rounding have not been evaluated.',
        'Equipment ES headers are exported item data; do not assume they are final local ES or multiply them again without checking PoB item calculations.',
    ]
    if spec is None:
        warnings.append('Active passive tree is missing. No socketed jewels could be resolved.')
    return dict(character=dict(level=build.get('level'), characterClass=build.get('className'), ascendancy=build.get('ascendClassName'), treeVersion=spec.get('treeVersion') if spec is not None else None), stats=stats, equipment=equipped, jewels=jewels, quests=quests, passiveNodeCount=len(spec.get('nodes', '').split(',')) if spec is not None and spec.get('nodes') else 0, warnings=warnings)



class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
        if self.path not in routes:
            self.send_error(404)
            return
        name, mime = routes[self.path]
        payload = (ROOT / 'web' / name).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != '/api/import':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= LIMIT:
                raise ValueError('Import must be between 1 byte and 2 MB.')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict) or not isinstance(data.get('export'), str):
                raise ValueError('Expected an export string.')
            result = parse_build(data['export'])
            status = 200
        except (ValueError, TypeError) as exc:
            result, status = dict(error=str(exc)), 400
        payload = json.dumps(result).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'PoE2 Build Lab listening on port {args.port}', flush=True)
    server.serve_forever()
