"""Run static browser checks with an isolated, controllable file server."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
for test in ['tests/browser_static_smoke.py','tests/browser_engine_parity.py']:
    with tempfile.TemporaryDirectory(prefix='poe2-browser-site-') as directory:
        (Path(directory)/'poe2-build-lab').symlink_to(ROOT/'dist',target_is_directory=True)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',directory],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            url=f'http://127.0.0.1:{port}/poe2-build-lab/'
            for attempt in range(50):
                if server.poll() is not None:raise RuntimeError('Static test server failed to start')
                try:
                    with urllib.request.urlopen(url,timeout=1) as response:assert response.status==200
                    break
                except OSError:time.sleep(.1)
            else:raise RuntimeError('Static test server was not ready')
            env=os.environ.copy();env['BROWSER_BASE_URL']=url;env['STATIC_TEST_SERVER_PID']=str(server.pid)
            result=subprocess.run([sys.executable,test],capture_output=True,text=True,cwd=ROOT,env=env)
            print(result.stdout,flush=True);print(result.stderr,file=sys.stderr,flush=True)
            if result.returncode:
                message=(result.stderr[-12000:]+'\n'+result.stdout[-3000:]).replace('%','%25').replace('\r','%0D').replace('\n','%0A')
                print(f'::error title={test}::{message}',flush=True)
                sys.exit(result.returncode)
        finally:
            if server.poll() is None:server.terminate()
            server.wait(timeout=5)
