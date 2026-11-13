"""Run backend tests and a source-bytecode check using the active Python environment."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,"-m","compileall","-q","backend","scripts"],cwd=ROOT,check=True)
subprocess.run([sys.executable,"-m","pytest","-q"],cwd=ROOT,check=True)
