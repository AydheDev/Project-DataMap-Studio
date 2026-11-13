# DataMap Studio

**A standalone Windows application for Excel mapping and auditable market reports.**

## Run the application

1. Download **DataMapStudio-Windows-x64** from a successful [Windows desktop build](https://github.com/AydheDev/Project-DataMap-Studio/actions/workflows/windows-desktop.yml).
2. Extract the ZIP into a local folder.
3. Double-click **DataMapStudio.exe**.

No Python, Node.js, browser, web server, localhost connection or internet connection is needed.
The executable bundles the processing engine and native Qt interface.
The application does not have telemetry, cloud storage, sign-in or automatic updates.
Keep the included user guide and third-party licence notices with the distribution.

## First workflow

1. Open **Data Import**.
2. Open `examples/sample-source.xlsx` and `examples/sample-approved-roles.xlsx`.
3. Choose **Current Period**, header row **2**, and **Approved Roles**, header row **1**.
4. Review all column mappings. Eligibility uses **Salesforce Last login**, never Fed ID.
5. Open **Account Role Mapping**, review the rules, and select **Generate report**.
6. Explore **Reports** / **Data Quality**, then select **Save Excel report**.

Expected sample result: **16 source rows → 5 eligible rows → 4 unique mappings**,
with **1 duplicate removed**. See [sample expectations](examples/EXPECTED_RESULTS.md).

Samples are synthetic; production business workbooks were not supplied for validation.

## Features

- Native Windows window, file dialogs, drag-and-drop input and report tables.
- XLSX/XLS import, worksheet/header selection, preview and manual column mappings.
- Approved-role matching, login validation, normalized email fallback and composite-key deduplication.
- Accurate market summaries and role counts, with optional zero counts.
- Seven formatted, auditable Excel worksheets.
- Reusable templates, processing history, configuration and report search/filter/sort.
- Background imports and processing so the interface remains responsive.
- Local SQLite/filesystem storage under `%LOCALAPPDATA%\DataMapStudio`.
- One instance per data folder, protected originals and atomic report generation.
- No IP sockets, including localhost, in the native runtime.

The first active module is Account Role Mapping per Market.
Other modules can use the existing trusted module registry and processing contract.

## Data and backups

Files, reports, templates and history stay on this computer.
Close the app and copy the entire `%LOCALAPPDATA%\DataMapStudio` folder to back it up.
Use `DataMapStudio.exe --storage C:\path\to\local-folder` to select another local data directory.
Network shares and mapped network drives are unsupported.

Existing files from the earlier web prototype remain untouched. To use an existing
storage directory with the desktop app, close the old server first and pass that
directory with `--storage`. Both interfaces use the same SQLite and file layout.

## Developer setup and packaging

End users only need the packaged executable. Developers need Python 3.14 on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desktop/requirements.txt
.\.venv\Scripts\python.exe desktop/launch.py
.\.venv\Scripts\python.exe scripts/build_desktop.py
```

The executable is written to `dist/DataMapStudio.exe`.
`Setup.cmd` installs the desktop dependencies and builds it.
`Start.cmd` opens the packaged executable if present, otherwise the native Python interface.
Developer setup downloads build dependencies; the installed application never does.

For the original backend regression tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe scripts/verify.py
```

For the actual native-window workflow and packaged smoke test:

```powershell
.\.venv\Scripts\python.exe desktop/launch.py --self-test build/source-test
.\dist\DataMapStudio.exe --self-test build/packaged-test
```

The self-test uses the synthetic examples and an isolated data directory.
It exercises the actual native window, imports, mappings, templates, processing,
filtering, export, settings and the no-network guard.
GitHub Actions performs these checks on Windows and publishes the executable artifact.

## Project layout

| Location | Purpose |
| --- | --- |
| desktop/ | Native Qt interface, direct workflow adapter, no-network guard and entry point |
| backend/app/core/ | Shared module contracts and background jobs |
| backend/app/modules/ | Account Role Mapping and disabled sample extension |
| backend/app/services/ | Excel import/export and normalization |
| backend/app/repositories/ | SQLite persistence |
| scripts/build_desktop.py | Windows executable packaging |
| examples/ | Synthetic workbooks and expected results |
| tests/ | Processing/API regression tests |
| .github/workflows/windows-desktop.yml | Native Windows build and executable verification |
| frontend/ and backend/app/main.py | Earlier browser prototype, retained for development reference; not bundled or started by the desktop app |

## Guides

- [Desktop user guide](desktop/USER_GUIDE.md)
- [Business rules and report definitions](docs/USER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Adding modules](docs/MODULES.md)
- [Desktop packaging and data handling](docs/DEPLOYMENT.md)
- [Verification record](docs/VERIFICATION.md)
