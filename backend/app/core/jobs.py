import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
from uuid import uuid4
import pandas as pd
from ..repositories.store import now
from ..services.excel import read_sheet, WorkbookError
from ..services.normalization import public_value

logger = logging.getLogger("datamap.jobs")

class JobManager:
    def __init__(self, store, registry):
        self.store, self.registry = store, registry
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="datamap")
        self.slots = BoundedSemaphore(4)

    def submit(self, request):
        if not self.slots.acquire(blocking=False):
            raise RuntimeError("The processing queue is full. Wait for a job to finish.")
        job = {"id": uuid4().hex, "module_id": request["module_id"], "status": "queued",
               "created_at": now(), "request": request, "error": None, "metrics": {}}
        try:
            self.store.put("jobs", job["id"], job)
            self.executor.submit(self.run, job)
        except Exception:
            self.slots.release()
            raise
        return job

    def run(self, job):
        output = self.store.root / "outputs" / f'{job["id"]}.xlsx'
        result_path = output.with_suffix(".json")
        temporary = output.with_suffix(".json.tmp")
        try:
            job = {**job, "status": "running"}
            self.store.put("jobs", job["id"], job)
            request = job["request"]
            module = self.registry.get(request["module_id"])
            config = module.config_model.model_validate(request["config"])
            inputs = {}
            for definition in module.metadata["inputs"]:
                selection = request["inputs"][definition["id"]]
                upload = self.store.get("uploads", selection["upload_id"])
                if upload is None:
                    raise ValueError("An input upload no longer exists. Upload it again.")
                path = self.store.root / "uploads" / upload["stored_name"]
                frame, _ = read_sheet(path, selection["sheet"], selection["header_row"])
                mapping = selection["mapping"]
                missing = [key for key in mapping.values() if key not in frame.columns]
                if missing:
                    raise ValueError("Mapped columns were not found. Review the selected sheet and header row.")
                # Preserve the entire original frame on attrs for future modules.
                mapped = pd.DataFrame({key: frame[column] for key, column in mapping.items()}, index=frame.index)
                mapped.attrs["source_frame"] = frame
                mapped.attrs["sheet"] = selection["sheet"]
                inputs[definition["id"]] = mapped
            module.validate(inputs, config)
            result = module.process(inputs, config)
            module.export(result, output)
            payload = {"metrics": result.metrics, "notes": result.notes, "tables": {
                name: {"columns": list(frame.columns),
                       "rows": [[public_value(v) for v in row] for row in frame.itertuples(index=False, name=None)]}
                for name, frame in result.tables.items()}}
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, allow_nan=False)
            os.replace(temporary, result_path)
            job.update(status="succeeded", finished_at=now(), metrics=result.metrics,
                       tables=[{"name": k, "row_count": len(v), "columns": list(v.columns)}
                               for k, v in result.tables.items()], notes=result.notes)
            self.store.put("jobs", job["id"], job)
        except Exception as exc:
            output.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)
            temporary.unlink(missing_ok=True)
            # Log the class and job ID only; exception bodies may contain source data.
            logger.error("Processing failed: job=%s exception=%s", job["id"], type(exc).__name__)
            safe = str(exc) if isinstance(exc, (ValueError, WorkbookError)) else "Processing failed. Check the workbook and try again."
            job.update(status="failed", error=safe, finished_at=now())
            self.store.put("jobs", job["id"], job)
        finally:
            self.slots.release()

    def close(self):
        self.executor.shutdown(wait=True)
