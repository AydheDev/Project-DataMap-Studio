# DataMap Studio

A local Excel data intelligence application with independent feature modules.
The first complete module maps approved account roles per market from FDS / SSO-EIP
workbooks. It produces an auditable, seven-sheet Excel report.

## Start on this Windows computer

The application has been built in this checkout. Double-click **Start.cmd**.
Keep the console window open while using the application. It opens
**http://127.0.0.1:8000** in your browser. Close it or press Ctrl+C to stop.

For a fresh checkout, install **Python 3.14** and **Node.js 22.12+** with npm on PATH,
then double-click **Setup.cmd** once. Setup installs Python dependencies into
`.venv`, installs the locked frontend dependencies through pnpm, and builds the UI.
Then use **Start.cmd**.

The installed application works fully offline. Files, calculations, templates and history stay
on this computer. The browser communicates only with the local processor at 127.0.0.1;
there are no internet/LAN services, CDN assets, accounts, analytics or update checks.
Runtime guards block non-loopback Python socket connections and DNS, and the built UI
restricts connections and assets to its own local origin. API documentation is also local.

Only first-time developer setup downloads dependencies. Start.cmd never downloads or installs anything.

## First workflow

1. Open **Data Import**.
2. Upload `examples/sample-source.xlsx` and `examples/sample-approved-roles.xlsx`.
3. Choose **Current Period**, header row **2**, and **Approved Roles**, header row **1**.
4. Review the detected columns. In particular, use **Salesforce Last login**, never Fed ID.
5. Continue to **Review & process**, then **Generate report**.
6. Explore **Reports** and **Data Quality**, or download the formatted Excel workbook.

Expected sample result: **16 source rows → 5 eligible rows → 4 unique mappings**,
with **1 duplicate removed**. There are two distinct accounts across all markets.
See [sample expectations](examples/EXPECTED_RESULTS.md).

The supplied workbooks contain synthetic examples only. Production FDS/SSO-EIP
workbooks were not provided and have not been validated in this checkout.

## What is included

- React + TypeScript + Vite + Tailwind, with Radix accessible report tabs and shared UI components.
- FastAPI application with a trusted module registry and bounded background job queue.
- Streaming XLSX reading, XLS support, sheet/header selection, data preview and manual column mapping.
- Approved-role matching, email fallback, login validation, composite-key deduplication and accurate unique counts.
- Atomic, formula-safe Excel export with all seven requested report worksheets.
- SQLite processing history, reusable mapping templates and defaults.
- Search, market/role filters, sorting, pagination, and report downloads.
- Backend unit/integration tests, frontend interaction tests, and full browser workflow tests.
- Windows launchers and cross-platform CLI instructions.

## Local development

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload --no-access-log
```

In another terminal:

```powershell
cd frontend
npx --yes --package=pnpm@11.25.0 pnpm install --frozen-lockfile
npx --yes --package=pnpm@11.25.0 pnpm dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to the local backend.
If pnpm is installed, `pnpm install --frozen-lockfile` and `pnpm dev` are equivalent.

Linux/macOS: use `python3.14 -m venv .venv` and `.venv/bin/python` in place of the Windows interpreter path.
Use Node.js 22.12+ and pnpm 11.25.0. The same FastAPI/Vite commands apply.

## Production build for local use

```powershell
cd frontend
npx --yes --package=pnpm@11.25.0 pnpm build
cd ..
.\.venv\Scripts\python.exe scripts/run_local.py
```

The backend serves `frontend/dist` and the API from one loopback port.
Node is only needed to build, not to run the built application.
Use `--port 8001` or `--no-browser` with `run_local.py` if needed.
API reference: http://127.0.0.1:8000/docs.

This is a **single-user, offline application**. LAN and internet hosting are outside its scope.
The runtime rejects listening on non-loopback interfaces. See [local deployment notes](docs/DEPLOYMENT.md).

## Verification

```powershell
.\.venv\Scripts\python.exe scripts/verify.py
cd frontend
npx --yes --package=pnpm@11.25.0 pnpm test
npx --yes --package=pnpm@11.25.0 pnpm build
npx --yes --package=pnpm@11.25.0 pnpm exec playwright install chromium
npx --yes --package=pnpm@11.25.0 pnpm test:e2e
```

The browser suite starts its own backend using `storage/e2e`. Stop an existing
port-8000 server first to keep browser-test records separate from normal work.
To use an installed browser instead of downloading Chromium, set
`BROWSER_EXECUTABLE` to its absolute executable path.

## Project map

```text
backend/app/
  api/                         Request schemas
  core/                        Module contracts, registry, jobs, safe logging
  services/                    Excel import/export and normalization
  repositories/                SQLite persistence
  modules/account_role_mapping/ Business rules and module metadata
  modules/sample/              Disabled developer example
frontend/src/
  components/                  Shared UI and report tables
  layouts/                     Application shell
  pages/                       Dashboard, reports, history, modules, settings
  features/account-role-mapping/ Workbook mapping and rule configuration
  services/                    Typed API access and formatting
  types/                       Frontend contracts
tests/                         Backend unit and workflow tests
frontend/e2e/                  Browser workflow tests
examples/                      Synthetic XLS/XLSX workbooks and expected results
scripts/                       Setup, launch, verification, sample generation
docs/                          Architecture, module guide, user guide, deployment
storage/                       Runtime files and SQLite (ignored by Git)
```

## Guides

- [Architecture and design decisions](docs/ARCHITECTURE.md)
- [Add a feature module](docs/MODULES.md)
- [User guide and business-rule definitions](docs/USER_GUIDE.md)
- [Deployment, limits and data handling](docs/DEPLOYMENT.md)
- [Verification record](docs/VERIFICATION.md)
