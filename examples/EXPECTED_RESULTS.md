# Synthetic sample acceptance results

Upload `sample-source.xlsx`, choose **Current Period**, header row **2**.
Upload `sample-approved-roles.xlsx`, choose **Approved Roles**, header row **1**.
Use default processing settings. All addresses use the reserved example.com domain.

| Metric | Expected |
| --- | ---: |
| Source rows | 16 |
| Eligible rows before deduplication | 5 |
| Final unique mappings | 4 |
| Unique accounts across markets | 2 |
| Duplicate occurrences removed | 1 |
| Excluded rows before deduplication | 11 |
| Blank login | 2 |
| #N/A login | 1 |
| Other invalid login | 3 |
| Unapproved roles | 2 |
| Missing email | 1 |
| Invalid email | 1 |
| Blank market | 1 |

| Market | Unique accounts | Role assignments | Number of roles |
| --- | ---: | ---: | ---: |
| DE | 1 | 1 | 1 |
| UK | 2 | 3 | 2 |

Role Counts has six rows, including Viewer=0 in both markets and Agent=0 in DE.
UK Agent=2, UK Manager=1, DE Manager=1. Sum of counts=4.

The invalid FDS email is not replaced by its valid EIP email because FDS is populated.
The uncached formula is treated conservatively as invalid; this app never calculates Excel formulas.
The valid login with an empty Fed ID remains eligible.
Audit emails are redacted by default.

`sample-approved-roles.xls` exercises legacy Excel import.
`sample-next-period.xlsx` exercises manual mapping of renamed columns; with the same
approved roles and defaults it produces two FR mappings for one account.
