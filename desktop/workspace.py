"""File-based access to the shared processing engine; no HTTP or browser."""
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4
from app.core.jobs import JobManager
from app.modules import default_registry
from app.repositories.store import Store, now
from app.services.excel import preview, sheet_names
from app.services.normalization import normalized

def local_path(value):
    path = Path(value).expanduser()
    if str(path).startswith(("\\\\", "//")):
        raise ValueError("Use a file on this computer, not a network share.")
    if os.name == "nt" and path.anchor:
        import ctypes
        if ctypes.windll.kernel32.GetDriveTypeW(path.anchor) == 4:
            raise ValueError("Network drives are not supported.")
    return path.resolve()

def default_storage():
    return local_path(os.environ.get("DATAMAP_STORAGE",
        Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "DataMapStudio"))

class Workspace:
    def __init__(self, root):
        self.store = Store(local_path(root))
        self.registry = default_registry()
        self.store.recover()
        self.manager = JobManager(self.store, self.registry)

    @property
    def root(self):
        return self.store.root

    def import_file(self, source):
        source = local_path(source)
        if source.suffix.lower() not in {".xls", ".xlsx"}:
            raise ValueError("Choose an Excel .xlsx or .xls workbook.")
        key = uuid4().hex
        target = self.root / "uploads" / (key + source.suffix.lower())
        temporary = self.root / "temp" / (key + ".tmp")
        try:
            count = 0
            with source.open("rb") as incoming, temporary.open("xb") as outgoing:
                while chunk := incoming.read(1024 * 1024):
                    count += len(chunk)
                    if count > 30 * 1024 * 1024:
                        raise ValueError("Workbook exceeds the 30 MB limit.")
                    outgoing.write(chunk)
            os.replace(temporary, target)
            record = {"id": key, "name": source.name, "size": count,
                      "sheets": sheet_names(target), "stored_name": target.name,
                      "original_path": str(source), "created_at": now()}
            self.store.put("uploads", key, record)
            return record
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            temporary.unlink(missing_ok=True)

    def preview(self, upload_id, sheet, input_id, header_row=None):
        upload = self.store.get("uploads", upload_id)
        if not upload:
            raise ValueError("Import this workbook again; its stored copy is missing.")
        result = preview(self.root / "uploads" / upload["stored_name"], sheet, header_row)
        definition = next(d for d in self.module().metadata["inputs"] if d["id"] == input_id)
        result["suggested_mapping"] = {}
        for field in definition["columns"]:
            match = next((c for c in result["columns"] if normalized(c) in
                          {normalized(v) for v in field["aliases"]}), None)
            if match:
                result["suggested_mapping"][field["key"]] = match
        return result

    def module(self):
        return self.registry.get("account-role-mapping")

    def validate(self, inputs, config):
        from app.api.schemas import JobRequest
        body = JobRequest.model_validate({"module_id": self.module().metadata["id"],
                                         "inputs": inputs, "config": config})
        config = self.module().config_model.model_validate(config).model_dump()
        if set(body.inputs) != {d["id"] for d in self.module().metadata["inputs"]}:
            raise ValueError("Select both required workbooks.")
        for definition in self.module().metadata["inputs"]:
            selection = body.inputs[definition["id"]]
            upload = self.store.get("uploads", selection.upload_id)
            if not upload or selection.sheet not in upload["sheets"]:
                raise ValueError("Select a valid imported workbook and worksheet.")
            required = {f["key"] for f in definition["columns"]}
            mapping = selection.mapping
            if set(mapping) != required or not all(mapping.values()):
                raise ValueError("Map all required columns before processing.")
            if len(set(mapping.values())) != len(mapping):
                raise ValueError("Each field must use a different source column.")
            for field in definition["columns"]:
                if normalized(mapping[field["key"]]) in {normalized(v) for v in field.get("forbidden_aliases", [])}:
                    raise ValueError(f'Invalid source column for {field["label"]}.')
        return {**body.model_dump(), "config": config}

    def submit(self, inputs, config):
        return self.manager.submit(self.validate(inputs, config))

    def save_template(self, name, inputs, config):
        request = self.validate(inputs, config)
        if not name.strip() or len(name) > 80:
            raise ValueError("Enter a template name of 1–80 characters.")
        record = {"id": uuid4().hex, "name": name.strip(), "module_id": request["module_id"],
                  "config": request["config"], "inputs": {}, "created_at": now()}
        for key, selection in request["inputs"].items():
            record["inputs"][key] = {k: v for k, v in selection.items() if k != "upload_id"}
        self.store.put("templates", record["id"], record)
        return record

    def settings(self):
        return {**self.module().config_model().model_dump(),
                **(self.store.get("preferences", "settings") or {})}

    def save_settings(self, config):
        config = self.module().config_model.model_validate(config).model_dump()
        self.store.put("preferences", "settings", config)

    def result(self, job_id):
        job = self.store.get("jobs", job_id)
        if not job or job["status"] != "succeeded":
            raise ValueError("This run has no completed report.")
        return json.loads((self.root / "outputs" / f"{job_id}.json").read_text(encoding="utf-8"))

    def save_report(self, job_id, destination):
        job = self.store.get("jobs", job_id)
        if not job or job["status"] != "succeeded":
            raise ValueError("This run has no completed report.")
        destination = local_path(destination).with_suffix(".xlsx")
        if self.root in destination.parents:
            raise ValueError("Save the report outside the application's data folder.")
        for record in self.store.list("uploads"):
            if record.get("original_path") and destination == Path(record["original_path"]):
                raise ValueError("Choose a new filename so the original workbook is preserved.")
        if destination.exists():
            raise FileExistsError("A file already exists at that destination. Choose a new report filename.")
        temporary = destination.parent / f".datamap-{uuid4().hex}.tmp"
        try:
            shutil.copyfile(self.root / "outputs" / f"{job_id}.xlsx", temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination

    def close(self):
        self.manager.close()
