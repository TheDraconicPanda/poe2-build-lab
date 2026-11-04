"""Expose actionable test failures in public check annotations, not only logs."""
import subprocess
import sys

for test in ['tests/browser_static_smoke.py','tests/browser_engine_parity.py']:
    result=subprocess.run([sys.executable,test],capture_output=True,text=True)
    print(result.stdout,flush=True)
    print(result.stderr,file=sys.stderr,flush=True)
    if result.returncode:
        message=(result.stderr[-12000:]+'\n'+result.stdout[-3000:]).replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print(f'::error title={test}::{message}',flush=True)
        sys.exit(result.returncode)
