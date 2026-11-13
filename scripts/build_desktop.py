"""Build a portable Windows executable using the active Python environment."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
command = [
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
    "--windowed", "--name", "DataMapStudio",
    "--distpath", str(DIST), "--workpath", str(ROOT / "build" / "desktop"),
    "--specpath", str(ROOT / "build"),
    "--paths", str(ROOT), "--paths", str(ROOT / "backend"),
    "--add-data", str(ROOT / "examples") + ";examples",
    "--add-data", str(ROOT / "desktop" / "USER_GUIDE.md") + ";desktop",
    "--hidden-import", "desktop.self_test",
    "--exclude-module", "fastapi", "--exclude-module", "uvicorn",
    "--exclude-module", "httpx", "--exclude-module", "httpx2",
    "--exclude-module", "PySide6.QtNetwork",
    "--exclude-module", "PySide6.QtWebEngineCore",
    "--exclude-module", "PySide6.QtWebEngineWidgets",
    "--exclude-module", "PySide6.QtQml", "--exclude-module", "PySide6.QtQuick",
    "--exclude-module", "pytest",
    str(ROOT / "desktop" / "launch.py"),
]
subprocess.run(command, cwd=ROOT, check=True)
shutil.copyfile(ROOT / "desktop" / "USER_GUIDE.md", DIST / "USER_GUIDE.md")
shutil.copytree(ROOT / "examples", DIST / "examples", dirs_exist_ok=True)
# Preserve bundled dependency licence notices alongside the distributable.
import importlib.metadata
licenses = DIST / "third-party-licenses"
for name in ["PySide6-Essentials", "shiboken6", "pandas", "numpy", "openpyxl", "xlrd", "pydantic", "pyinstaller", "defusedxml"]:
    distribution = importlib.metadata.distribution(name)
    for item in distribution.files or []:
        if ("license" in str(item).lower() or "copying" in str(item).lower()) and ".dist-info" in str(item):
            source = Path(distribution.locate_file(item))
            if source.is_file():
                target = licenses / name / Path(str(item).split(".dist-info/", 1)[-1])
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
print("Built", DIST / "DataMapStudio.exe")
