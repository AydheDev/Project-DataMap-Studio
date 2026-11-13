# Standalone desktop deployment

The supported user-facing distribution is **DataMapStudio.exe** for Windows x64.
It is a native PySide6/Qt Widgets application with the Python runtime and processing
dependencies bundled by PyInstaller. It does not use a browser, WebView, web server,
HTTP client, localhost transport, or Node runtime.

Download the Windows build artifact, extract it and run the executable.
No administrator rights or global Python installation are required for normal use.
The first launch may take a few seconds while the one-file package extracts its runtime.

## Local data

The default data directory is `%LOCALAPPDATA%\DataMapStudio`.
It contains immutable imported copies, report files, SQLite history, templates and settings.
Use `--storage <local-directory>` for another location. Close the application before
backing up or moving that directory. The packaged executable and data are separate;
replacing the executable does not delete the saved workspace.

QLockFile prevents two native instances from using the same data directory concurrently.
Do not open the same directory simultaneously with the earlier web prototype.

Imports are capped at 30 MB. Worksheet limits remain 200,000 rows, 256 columns and
2,000,000 data cells. XLSX expanded size is limited to 200 MB.
Excel formulas are not evaluated; saved cached values are used where available.

## No-network runtime

The native interface invokes the shared processing engine through Python function calls.
The desktop entry point installs a guard that rejects IPv4/IPv6 socket creation and DNS.
It does not reserve or listen on any port, including localhost.
Network shares and mapped network drives are not supported.
There are no accounts, online dependencies, external assets, telemetry or automatic updates.

This is an application-level guard, not an OS sandbox for hostile native extensions.
Only trusted feature modules are supported. The guard does not alter the computer's
network settings or other applications.

## Packaging and verification

The Windows workflow installs build dependencies, runs the existing processing tests,
runs the native GUI workflow offscreen, builds a one-file executable and runs the same
workflow from the executable itself. It also produces screenshots and JSON verification
records as build artifacts.

The distribution includes synthetic example workbooks, an offline user guide and
available third-party licence notices. The executable is not code-signed in this repository.
A local developer build uses `python scripts/build_desktop.py`.
Build dependency downloads are separate from runtime behavior.

The historical React/FastAPI implementation remains in source control for reference.
It is excluded from the packaged executable and is not launched by Start.cmd.
