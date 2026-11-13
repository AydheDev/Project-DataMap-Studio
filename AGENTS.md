# DataMap Studio repository guidance

- Read README.md and docs/ARCHITECTURE.md before changing architecture.
- Keep account-role business rules inside backend/app/modules/account_role_mapping.
- Salesforce Last login is the eligibility filter. Never substitute Salesforce Fed ID.
- Deduplicate Market + approved Role + normalized Account Email; preserve cross-role and cross-market assignments.
- Keep original source row references and original login values for audit.
- Never commit uploads, generated reports, SQLite databases, runtime logs or real business data.
- Never log full emails or report-search query strings.
- Formula/error strings in generated Excel must remain inert text.
- New modules implement the core contract and register explicitly. Never execute uploaded code.
- Run backend tests for processing/API changes; frontend tests and production build for UI changes.
- Run the browser suite only with isolated test storage and no existing app on its test port.
- Do not treat synthetic-fixture checks as verification of production workbooks.
- Local-only deployment is the default. Do not publish or expose the app publicly without an explicit request.

- The application must operate fully offline. No internet/LAN calls, CDN assets, telemetry or automatic update checks.
- Preserve the loopback-only runtime guard, same-origin browser policy and self-contained API docs.
- The local browser UI may communicate with its local Python processor over 127.0.0.1 only.
