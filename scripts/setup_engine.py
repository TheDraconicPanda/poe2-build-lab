"""Build pinned dependencies locally. Needs git, make, gcc and HTTPS access."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'
PINS = json.loads((ROOT / 'engine/pins.json').read_text())


def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)


def checkout(name, destination):
    pin = PINS[name]
    if not destination.exists():
        destination.mkdir(parents=True)
        run('git', 'init', str(destination))
        run('git', '-C', str(destination), 'remote', 'add', 'origin', pin['url'])
    head = subprocess.run(['git', '-C', str(destination), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    if head.returncode != 0 or head.stdout.strip() != pin['commit']:
        dirty = subprocess.check_output(['git', '-C', str(destination), 'status', '--porcelain'], text=True)
        if dirty:
            raise RuntimeError(f'Refusing to replace modified dependencies: {destination}')
        run('git', '-C', str(destination), 'fetch', '--depth', '1', 'origin', pin['commit'])
        run('git', '-C', str(destination), 'checkout', '--detach', pin['commit'])
    if subprocess.check_output(['git', '-C', str(destination), 'diff', 'HEAD', '--'], text=True):
        raise RuntimeError(f'Tracked dependency files are modified: {destination}')


if __name__ == '__main__':
    LOCAL.mkdir(exist_ok=True)
    checkout('pob2', LOCAL / 'pob2')
    checkout('luajit', LOCAL / 'sources/luajit')
    checkout('luautf8', LOCAL / 'sources/luautf8')
    prefix = LOCAL / 'luajit'
    run('make', '-j2', f'PREFIX={prefix}', 'install', cwd=LOCAL / 'sources/luajit')
    (LOCAL / 'lua').mkdir(exist_ok=True)
    run('gcc', '-O2', '-fPIC', '-shared', '-I' + str(prefix / 'include/luajit-2.1'),
        str(LOCAL / 'sources/luautf8/lutf8lib.c'), '-o', str(LOCAL / 'lua/lua-utf8.so'))
    run(str(prefix / 'bin/luajit'), '-e', 'assert(jit.version_num >= 20100)')
    print('Pinned engine and Lua dependencies installed in .local/.')
