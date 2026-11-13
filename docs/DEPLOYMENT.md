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

## Future hosted deployment

Before serving multiple people, add:
- Authentication and per-user/organization authorization.
- TLS, explicit approved origins and hostnames.
- Secure retention policies, protected backups and appropriate encryption.
- A process-independent worker/queue and crash recovery with ownership leases.
- Database migrations and scalable result storage/pagination.
- Server-side request rate limits and streaming multipart request caps.
- Server resources and load testing sized to actual workbook volumes.

Do not run several Uvicorn worker processes against this release's shared storage:
its in-process queues and startup recovery assume a single process.
These items are future infrastructure boundaries, not partially enabled features.
