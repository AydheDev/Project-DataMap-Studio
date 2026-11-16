# Verification record

## Native standalone Windows application

The Windows desktop workflow verifies the native source and packaged executable independently:

1. Existing backend processing/API regression suite.
2. Source native-window self-test using real synthetic XLSX files.
3. PyInstaller one-file Windows executable build.
4. The same native-window self-test launched from DataMapStudio.exe.
5. Archive inspection excluding the web runtime.
6. Native preview and machine-readable verification artifacts.

The native self-test checks all eight pages, header detection, manual field state,
template saving, the real processing engine, report counts, role/market filtering,
Excel export, audit email redaction, settings persistence and blocked IP socket creation.
The sample result is four unique mappings and one removed duplicate.
The exact workflow status and downloadable output are recorded in GitHub Actions.

The first native build passed the backend suite, source workflow and packaged-executable workflow
on Windows. Subsequent changes are verified by the same workflow before acceptance.

## Earlier web implementation

Before the desktop conversion:
- 51 backend tests passed, including offline-operation checks.
- 7 React frontend tests and the production build passed.
- 2 browser tests passed before the local browser preview was declined.

The React/FastAPI interface is retained separately for reference.
It is not used by the standalone executable.

## Verification limits

All workbooks used for testing were synthetic. Production business workbooks were not supplied.
Full-scale performance testing at the maximum worksheet size has not been performed.
The native application targets Windows x64; macOS/Linux distributions were not built.
The user's Windows workspace disconnected during the conversion, so packaging and executable
verification were performed on the repository's Windows runner. Installation on the user's
disconnected PC has not been performed.

## Desktop 1.1.1 — large-workbook import fix (2026-11-16)

- Preview now streams all source rows and retains at most 20 sample rows, without building a full DataFrame.
- Account Role Mapping materializes only mapped fields. Other modules retain full-source access by default.
- Limits are 1,000,000 non-empty data rows, 256 populated columns and 8,000,000 retained processing cells; file and expanded-archive limits remain in place.
- Importer regression checks cover projected memory limits, preserved error/formula values and source row numbers, unmapped-only records, blank formatting, inaccurate XLSX dimensions and invalid physical row addresses.
- Local processing/API suite: 61 passing tests. Retained web interface: 7 tests and production build.
- A generated XLSX with 200,001 records was previewed and imported successfully.
- Native self-test additionally imports a real 10,001-row, 201-column XLSX (over the former two-million-cell threshold), processes it and exports its report. The Windows workflow repeats this test from the packaged executable before publishing an artifact.
- The user's production workbook was not provided. The screenshot's old size-limit failure is reproduced with synthetic data; this is not a claim of validation against the user's file.
