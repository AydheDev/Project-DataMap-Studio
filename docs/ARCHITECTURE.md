# Architecture

## Implementation plan and completed phases

1. **Foundation:** application layout, shared interfaces, module registry, local persistence.
2. **Import:** XLSX/XLS validation, worksheets, header detection, row-preserving preview and column mappings.
3. **Processing:** account role module, login filter, approved role matching, normalized emails,
   composite-key deduplication, market and role summaries.
4. **Audit and export:** quality counts, unmatched roles, exclusions, duplicate audit,
   atomic seven-sheet Excel reports and safe text cells.
5. **Workspace:** dashboard, templates, preferences, history, report search/filter/sort/pagination.
6. **Delivery:** automated verification, synthetic workbooks, startup scripts and guides.

The repository was initially empty. No existing application behavior was replaced.
The requested stack was used; `xlrd` handles legacy XLS and `xlwt` generates legacy test fixtures.

## Responsibilities

| Layer | Location | Responsibility |
| --- | --- | --- |
| Presentation | frontend/src | Imports, mapping, configuration, results and workspace pages |
| HTTP API | backend/app/main.py, api/ | Request boundaries and orchestration endpoints |
| Application core | core/ | Module registration, job lifecycle, queue and execution |
| Feature module | modules/account_role_mapping/ | Business validation, transformation and output table definitions |
| Data services | services/ | Workbook parsing, normalization and safe atomic workbook writing |
| Storage | repositories/store.py | SQLite metadata and scoped filesystem directories |

Modules implement a shared `FeatureModule` protocol and return `ProcessingResult`:
named Pandas tables, numerical metrics and explanatory notes.
The job engine calls the selected module's validation, processing and export functions.
Account-role-specific filtering and aggregation live inside the module, not the job engine.

The app factory accepts a storage directory and module registry. Tests inject
isolated temporary storage. The production module list is explicitly assembled
in `modules/__init__.py`; uploaded code is never executable.

## Job lifecycle

`POST /api/jobs` checks configuration, input identities, worksheet selections and mapping completeness.
Jobs receive UUIDs and progress through queued → running → succeeded or failed.
Two worker threads run jobs, with at most four running/queued jobs combined.
Additional submissions receive HTTP 429.

Workers read selected inputs and preserve source row indices. Each module receives
mapped fields plus the full source DataFrame on `frame.attrs["source_frame"]`.
Modules choose how to validate, process and export the inputs.

A report is written to a randomly named temporary file and atomically renamed only
when complete. Result-table JSON is also written atomically. Success is stored
after both artifacts exist. Download endpoints require succeeded status.
Failed jobs remove their own outputs. Startup marks interrupted queued/running
jobs failed, and removes only partial `*.tmp` files in owned temp/output directories.

Run a single backend process. Multiple Uvicorn workers would independently own queues
and startup recovery; this release does not support that topology.

## Input and processing choices

- Original uploaded bytes are immutable, stored under unique names.
- Header detection scores the first 30 worksheet rows. It is a heuristic;
  users can explicitly choose rows 1–100. Empty/duplicate headers receive stable unique labels.
- Empty data rows are skipped, while original Excel row numbers are retained.
- XLSX sheets are streamed with OpenPyXL read-only mode. A parallel formula view
  distinguishes formula cells lacking cached values from ordinary blanks.
- Excel errors use typed `ExcelFault` values. Formulas are never evaluated.
- Selected sheets are materialized into bounded Pandas DataFrames for transformations.
  Processing is not an unlimited-memory streaming aggregation engine.
- Role comparison collapses repeated whitespace and ignores case. Canonical output
  uses the first approved spelling. Market whitespace is collapsed; market case is preserved.
- The first eligible occurrence of a market–role–email key is retained, including its login.
- Zero-count expansion is checked before building its Cartesian product.
- Original login values are retained in mappings and audits, rather than replaced
  with parsed timestamps.

## Persistence

SQLite stores uploads, jobs, templates and preferences. WAL mode and short,
per-operation connections permit concurrent readers and worker updates.
Filesystem paths are server-owned; the browser uses UUID references.
Templates exclude upload IDs, so they can be reused with replacement workbooks.
Module metadata includes a Pydantic-generated configuration schema.

The UI stores working selections in memory. Saved templates, history and defaults
survive reloads/restarts. Unsaved mapping edits do not survive a page reload.

## Safety and boundaries

Loopback binding, trusted Host validation and origin checks support the local use case.
There are no third-party analytics, external fonts, or online processing calls.
The UI does not upload workbooks anywhere beyond the local server.
Full emails are absent from application error logs, and access-log query strings
are stripped. Workbook strings are written as text, preventing formula execution
in exported results.

Client workbook previews display source data. Audit email redaction applies to
the Excluded Records sheet and its report API, not the original source preview
or the required Unique Mapping sheet.

See DEPLOYMENT.md for limits and server-deployment requirements.
