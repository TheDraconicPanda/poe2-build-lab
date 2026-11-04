"""Compatibility entry point: the primary UI is now the static browser app."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('browser_static_smoke.py')),run_name='__main__')
