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
