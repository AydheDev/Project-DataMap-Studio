@echo off
cd /d "%~dp0"
if exist "dist\DataMapStudio.exe" (
  start "" "%~dp0dist\DataMapStudio.exe"
  exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
  start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0desktop\launch.py"
  exit /b 0
)
echo Download the Windows standalone application or run Setup.cmd first.
pause
