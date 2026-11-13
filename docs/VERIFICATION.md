# Verification record

Verified locally on 13 November 2026 using Windows, Python 3.14.8,
Node 24.22.1, pnpm 11.25.0 and an installed Chrome browser.

## Results

- **39 backend tests passed.**
- **5 frontend interaction tests passed.**
- **2 browser tests passed.**
- Python source compilation passed.
- TypeScript checking and Vite production build passed.

Backend coverage includes login blanks/errors and real dates, incomplete date rejection,
approved-role filtering, normalized email fallback, multi-role/cross-market preservation,
composite deduplication, count reconciliation, zero counts, empty/all-excluded inputs,
XLS/XLSX import, original row references, formula/error handling, formatted export,
formula-safe cells, atomic failure behavior, complete upload-to-download jobs,
reusable templates, persistent settings/history, restart recovery, missing inputs,
corrupt files, size/expansion limits, Fed ID mapping rejection, source retention and private access logging.

Frontend component tests exercise mapping completeness, duplicate/stale header rejection,
worksheet changes, manual mapping, source previews, audit redaction defaults,
server-side report filtering/sorting and request retry behavior.

Browser tests uploaded the real synthetic example files, confirmed detected headers,
saved a template, generated and downloaded the report, filtered UK/Agent counts,
checked excluded-record redaction, opened history and modules, and saved/reloaded settings.
The mobile test checked navigation/import at 390 px width without page-level horizontal overflow.
No browser page errors were observed in the full workflow.

## Limits of verification

- Production business workbooks were not supplied; all processing tests used synthetic data.
- Full-scale performance/load testing at the documented maximum limits was not performed.
- A fresh-machine execution of Setup.cmd was not performed.
- Linux/macOS execution was not tested.
- The optional interactive ChatGPT browser preview was declined. No visual screenshot review
  was completed through that browser. Automated Chrome workflow tests had already passed.
- The application is a local, single-user release; no public/server deployment was attempted.
