# DataMap Studio desktop

Double-click DataMapStudio.exe. No Python, Node, browser, internet connection or server is needed.

1. Open Data Import.
2. Choose the FDS / SSO-EIP workbook and the approved-role workbook. You can also drop a file onto its input card.
3. Select worksheets and check the header row. Use Apply after changing a header row.
4. Map every required column. Salesforce Last login is the eligibility field; Salesforce Fed ID must not be used.
5. Open Account Role Mapping, review the protected rules and options, then Generate report.
6. Use Reports or Data Quality to inspect results. Click Save Excel report to save all seven worksheets.

The sample-source workbook uses Current Period with header row 2.
The sample-approved-roles workbook uses Approved Roles with header row 1.
With the defaults, 16 source rows produce 5 eligible rows and 4 unique mappings, with 1 duplicate removed.

Templates save mappings and options for future reporting periods. Apply a template, select replacement files and review the mappings before running.
Settings defines defaults for NEW workflows; it does not change completed reports.
Processing History keeps completed and failed jobs after the app closes.

Blank, #N/A, error or invalid Salesforce Last login values are excluded. Unapproved roles are reported separately.
FDS Email is used first, with EIP Email as the fallback when FDS is missing.
An invalid populated FDS email does not fall back to EIP.
Deduplication uses Market + approved Role + normalized Email.
The same account can appear in different roles and markets.
The first eligible source occurrence is retained.

Quality flags can overlap. Each excluded row has one primary reason and all its detected issues.
Source rows = Excluded rows + Eligible rows.
Eligible rows = Duplicates removed + Final unique mappings.
Sum of Role Counts = Final unique mappings.

Audit emails are redacted by default. Unique Mapping includes full email addresses.
Imported originals are preserved. Save exported reports under a new filename.
Files and history are stored in %LOCALAPPDATA%\DataMapStudio.
Close the app before backing up that folder. Only one instance may use a data folder at a time.

The application does not use a browser, localhost server, network socket, cloud service or automatic updates.
Network shares and mapped network drives are not supported.
If a job is running, wait for it to finish before closing the app.

Limits: XLSX/XLS, 30 MB per file, 200,000 rows, 256 columns, 2,000,000 cells per selected sheet.
Formula cells without saved cached values are excluded; recalculate and save in Excel before importing.
