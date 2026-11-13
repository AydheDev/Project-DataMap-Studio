# Adding a feature module

Only trusted, installed source code may register a module. Do not add an executable
upload mechanism or import arbitrary files chosen in the browser.

## Backend

1. Copy `backend/app/modules/sample` to a new module directory.
2. Define a Pydantic configuration model with explicit defaults and validation.
   Prefer `ConfigDict(extra="forbid")`.
3. Supply unique metadata:
   - `id`, `name`, `description`, `version`, `enabled`
   - `ui_route`
   - `inputs`: input IDs, labels and required column definitions.
     Every column declares `key`, `label`, `aliases`, and optionally
     `forbidden_aliases` to prevent selecting known-incompatible headers.
4. Implement `validate(inputs, config)`, `process(inputs, config)`,
   and `export(result, target)`.
5. Register the class in `modules/__init__.py`.
6. Add isolated unit tests and an upload-to-report integration test.

Minimal shape:

```python
from pydantic import BaseModel, ConfigDict
from app.core.contracts import ProcessingResult
from app.services.export import write_workbook

class MyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_empty: bool = False

class MyModule:
    metadata = {
        "id": "my-module",
        "name": "My Module",
        "description": "A separate analytical workflow.",
        "version": "1.0.0",
        "enabled": True,
        "ui_route": "/my-module",
        "inputs": [{
            "id": "source",
            "label": "Source workbook",
            "columns": [{"key": "value", "label": "Value", "aliases": ["Value"]}]
        }],
    }
    config_model = MyConfig

    def validate(self, inputs, config):
        if inputs["source"].empty:
            raise ValueError("The selected worksheet has no data rows.")

    def process(self, inputs, config):
        frame = inputs["source"]
        return ProcessingResult(
            tables={"Values": frame[["value"]].copy()},
            metrics={"source_rows": len(frame)},
            notes=["Describe counting and exclusion rules here."],
        )

    def export(self, result, target):
        write_workbook(result.tables, target)
```

Module inputs are DataFrames keyed by the declared input IDs. Their indexes carry
original Excel row numbers. Required fields use canonical keys; the entire source
frame remains available in `frame.attrs["source_frame"]`.

Do not log source rows or full email addresses. User-facing validation errors should
describe the correction without embedding sensitive values. Avoid unbounded
cross-products. Use the shared atomic exporter or maintain its atomic and text-safe guarantees.

## Frontend

The existing module metadata is fetched from `GET /api/modules`.
Add your UI under `frontend/src/features/<module-id>/`, and wire its page entry in
`App.tsx` / `layouts/Shell.tsx`. Keep its configuration and business-specific UI
in that directory; do not modify Account Role Mapping's processor or components.

The first release has an explicit React route list rather than loading remote UI
bundles. When adding a second active module, add its route to the Page type and
route dispatcher, and use its declared `ui_route` from the module card.
Shared InputCard and ReportTable components can be extracted further if their
contracts suit the new feature. The API and job engine already dispatch by module ID.

Submit jobs with:
```json
{
  "module_id": "my-module",
  "inputs": {
    "source": {
      "upload_id": "<server-returned upload UUID>",
      "sheet": "Selected sheet",
      "header_row": 1,
      "mapping": {"value": "Actual workbook header"}
    }
  },
  "config": {"include_empty": false}
}
```

The generic report endpoints list each module's named tables, filter recognized
Market/Account Role columns, sort any column, paginate, and download the module's workbook.
Future modules can add feature-specific views without changing existing modules.

## Tests to add

Validate required inputs, empty data, invalid values, deterministic output,
metric reconciliation, export content, and API failure handling.
Keep a small synthetic workbook whose expected results are calculated independently.
