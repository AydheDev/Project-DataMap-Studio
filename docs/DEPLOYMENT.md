# Deployment and data handling

## Local runtime

The supported initial deployment is one FastAPI process on 127.0.0.1.
Run `scripts/run_local.py` after building the frontend. It serves the built UI
and the API from the same origin, and disables access logging by default.
The app also strips query strings from Uvicorn access logs if logging is enabled.

Tested here: Windows, Python 3.14.8, Node 24.22.1, pnpm 11.25.0 and Chrome.
Dependency versions are recorded in backend/requirements-lock.txt and frontend/pnpm-lock.yaml.
Setup.ps1 is the Windows bootstrap; a clean-machine installation was not exercised.
Other OS instructions are provided but were not executed in this Windows environment.

Runtime data defaults to repository-root `storage/`:
- `uploads/`: immutable original workbook bytes.
- `outputs/`: completed XLSX and report-table JSON files.
- `temp/`: partial uploads.
- `datamap.sqlite3`: metadata, job history, templates and defaults.

Set the absolute `DATAMAP_STORAGE` environment variable before launch to use a different
directory. Keep this directory on a trusted local disk with appropriate OS account access.
The application does not encrypt files at rest or implement multiple user accounts.

## Limits

| Resource | Limit |
| --- | ---: |
| Uploaded workbook | 30 MB |
| Expanded XLSX archive | 200 MB |
| XLSX archive entries | 10,000 |
| Rows in one selected sheet | 200,000 data rows |
| Columns in one selected sheet | 256 |
| Selected-sheet data cells | 2,000,000 |
| Header row | 1–100 |
| Automatic header search | First 30 rows |
| Preview rows | 20 |
| Zero-count market/role combinations | 500,000 |
| Concurrent running jobs | 2 |
| Running + queued jobs | 4 |
| Report API page | 200 rows maximum |

XLSX reading and export stream where practical. Pandas aggregation uses an in-memory,
bounded selected-sheet representation. Report-table JSON is also materialized when
browsing results. These limits target internal desktop workflows, not very large
data lakes. Actual throughput depends on workbook complexity and available memory.

## Data lifecycle

Data is retained until the operator deliberately removes the project storage.
There is no automatic deletion of source workbooks, completed reports or history.
Startup cleans only partial `*.tmp` files in the owned temp/output directories.
Do not remove originals or SQLite rows independently while jobs are running.

For backup, stop the app and copy the entire storage directory. Keep the SQLite
database and files together. Restore the directory as a unit.
Source code, examples, lock files and docs are tracked in Git; storage, logs,
virtual environments and built frontend output are ignored.

## Offline-only runtime boundary

No LAN or internet service is used by the application. The only HTTP communication is
between the browser and the processor on this computer's loopback interface.
The built UI has a same-origin Content Security Policy. Its API client rejects external
URLs and redirects. The API reference is self-contained HTML and local OpenAPI JSON;
Swagger/ReDoc CDN pages are disabled.

A Python audit hook rejects non-loopback socket connects, binds, datagram destinations
and hostname resolution. This applies to the normal launcher and API lifespan startup.
It is an application guard for standard Python networking, not an OS sandbox for
malicious native code or subprocesses. Only trusted feature modules are supported.
No API calls or health checks are made to external services. The launcher waits for the
local server's in-process readiness flag before opening the browser.

First-time developer setup can download dependencies. Once installed, Start.cmd and
all processing work without internet. There is no automatic update or telemetry mechanism.
The guard does not change the user's browser or operating system networking settings.

Public hosting, LAN sharing and multi-user server deployment are not supported.
Do not run multiple Uvicorn workers against the shared local storage.
