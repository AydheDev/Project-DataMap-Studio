# User guide

## Import and map

Use **Data Import** to drop or browse for two Excel workbooks: the combined FDS /
SSO-EIP source and the approved account-role list. File and worksheet names are
not fixed. You may select a previously uploaded workbook.

Pick each worksheet. Headers are detected from the first 30 rows; enter a different
**Header row** and click **Apply** if the preview is incorrect.
The preview shows the first 20 records, total non-empty data rows, column count,
and original Excel row references.

Map all five source fields and the role-list field. Every required field needs a
different source column. Renamed headers can be selected manually.
Known Salesforce Fed ID headers cannot be mapped as Last login.

## Review rules

1. **Salesforce Last login:** blank/null/whitespace, #N/A, Excel errors, uncached formulas,
   impossible dates and unrecognized text are excluded.
   Complete date strings, Excel serial dates (1–2,958,465), and native Excel dates are accepted.
   Day-first parsing is enabled by default for ambiguous strings; ISO dates retain ISO meaning.
   Salesforce Fed ID is never an eligibility condition.
2. **Approved roles:** compare with the uploaded Role Code list, ignoring case and
   collapsing whitespace. Blank/unapproved roles are excluded and counted separately.
3. **Email:** use FDS Email when populated, otherwise EIP Email; trim and lowercase.
   Excel error values are treated as unavailable email values. If both are missing, exclude the row.
   A populated but invalid FDS email does **not** fall back to a populated EIP email.
4. **Invalid email:** a basic syntactic check flags spaces, missing @ or missing domain suffix.
   Flagged emails are excluded by default. Turning that option off retains them but still reports the flag.
   This is a format check, not proof that a mailbox exists.
5. **Market:** blank or Excel-error markets are excluded. Outer/repeated whitespace is normalized;
   market capitalization is preserved, so UK and uk remain separate markets.
6. **Deduplication:** retain the first eligible Market + approved Role + normalized Email
   combination. Multiple roles or markets for one account are retained.

## Save and reuse a workflow

Enter a **Template name** on the review page and select **Save template**.
A template saves column mappings, preferred worksheet/header choices and options,
but never pins the old upload IDs.

For a new reporting period, choose **New workflow**, upload new files and apply
the template. Check that every mapped header is still correct.
Selecting a replacement file tries to preserve compatible mappings and re-detects headers.

Settings stores defaults for new workflows. Changing defaults does not silently
change an existing run or a saved template. Unsaved edits are not persisted across page reloads.

## Generate and inspect

Select **Generate report**. The job runs in the background and opens Reports when done.
Failures appear with an actionable message and remain visible in Processing History.
Original uploads are preserved. Correct the selection/mapping and submit a new job
rather than editing an old report.

Each table supports text search and column sorting. Market and role filters appear
where the table contains those columns. Results are paged in groups of 50.
Select another successful run from the report selector.
The complete Excel workbook is downloaded separately; table filters do not alter it.

## Report worksheets

| Worksheet | Meaning |
| --- | --- |
| Market Summary | Distinct emails per market, total role assignments, count of represented approved roles |
| Role Counts | Unique email count per market/role; optionally includes zero-count approved roles |
| Unique Mapping | Eligible deduplicated market, role, full email and original login value |
| Duplicate Audit | Eligible raw rows, distinct accounts and removed duplicate occurrences per market/role |
| Data Quality | Source totals, quality flags, eligibility, exclusions, duplicates and final mappings |
| Unmatched Roles | Normalized unapproved role values and their counts across all source rows |
| Excluded Records | Original source row, relevant fields, primary exclusion reason and all detected issues |

**Eligible rows** pass all configured filters, before deduplication.
**Excluded rows** fail at least one rule; each has exactly one primary exclusion reason.
**Quality counts overlap** because a source row can have several problems.
They must not be added together as if they were mutually exclusive.
The primary reason follows login → approved role → missing/invalid email → market.

`Source rows = Excluded rows + Eligible rows`

`Eligible rows = Duplicate occurrences removed + Final unique mappings`

`Sum of Role Counts = Final unique mappings`

One email can hold several roles, so role assignments may exceed unique market accounts.
Zero-count combinations cover only markets with at least one final eligible mapping.
Number of Roles counts roles actually represented in the cleaned market.

Excluded-record email addresses are redacted by default. Enable full audit emails only
when needed. Unique Mapping always includes full emails as required by the report.
Source previews show the original supplied values.

## Troubleshooting

- **Unreadable workbook:** open it in Excel and save a valid, unencrypted XLSX copy.
- **Formula without a cached result:** recalculate and save the workbook in Excel,
  then upload the saved copy. DataMap never evaluates formulas.
- **Missing field:** check the worksheet, header row and manual mapping.
- **No approved roles:** ensure Role Code points to a populated role-code column.
- **No mappings:** inspect Data Quality and Excluded Records for the filtering reasons.
- **Large file:** split the source into a smaller worksheet within the documented limits.
- **Interrupted run:** restart the app, then start a new job. The old run remains failed.
- **Port already in use:** close the other DataMap console or run
  `python scripts/run_local.py --port 8001` with the project environment.
