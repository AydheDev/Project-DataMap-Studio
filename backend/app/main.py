import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.staticfiles import StaticFiles
from .api.schemas import JobRequest, TemplateRequest, Settings
from .api.local_docs import render_api_reference
from .core.local_only import CONTENT_SECURITY_POLICY, install_local_only_network_policy
from .core.jobs import JobManager
from .core.logging import protect_access_logs
from .modules import default_registry
from .repositories.store import Store, now
from .services.excel import sheet_names, preview, WorkbookError
from .services.normalization import normalized

ROOT = Path(__file__).resolve().parents[2]
MAX_UPLOAD_BYTES = 30 * 1024 * 1024

def create_app(storage_root=None, registry=None):
    protect_access_logs()
    root = Path(storage_root or os.environ.get("DATAMAP_STORAGE", ROOT / "storage"))
    store = Store(root)
    registry = registry or default_registry()
    manager = JobManager(store, registry)

    @asynccontextmanager
    async def lifespan(app):
        install_local_only_network_policy()
        store.recover()
        yield
        manager.close()

    app = FastAPI(title="DataMap Studio", version="1.0.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, swagger_ui_oauth2_redirect_url=None)
    app.state.store, app.state.manager = store, manager
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]", "testserver"])
    app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
                       allow_methods=["GET", "POST", "PUT"], allow_headers=["Content-Type"])

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        content_length = request.headers.get("content-length", "0")
        if content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES + 1024 * 1024:
            return JSONResponse({"detail": "Request exceeds the 30 MB upload limit."}, status_code=413)
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            parsed = urlparse(origin)
            if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
                return JSONResponse({"detail": "Requests must originate from the local DataMap application."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        return response

    def upload_or_404(upload_id):
        record = store.get("uploads", upload_id)
        if record is None:
            raise HTTPException(404, "Upload not found.")
        return record

    def job_or_404(job_id):
        record = store.get("jobs", job_id)
        if record is None:
            raise HTTPException(404, "Job not found.")
        return record

    def result_for(job_id):
        job = job_or_404(job_id)
        if job["status"] != "succeeded":
            raise HTTPException(409, "This job has no completed report.")
        target = store.root / "outputs" / f'{job["id"]}.json'
        if not target.is_file():
            raise HTTPException(410, "Report data is missing. Run the job again.")
        return json.loads(target.read_text(encoding="utf-8"))

    @app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
    def local_api_reference():
        return render_api_reference(app.openapi())

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/api/modules")
    def modules():
        return registry.describe()

    @app.get("/api/uploads")
    def uploads():
        return store.list("uploads")

    @app.post("/api/uploads", status_code=201)
    async def upload(file: UploadFile = File(...)):
        filename = (file.filename or "workbook").replace("\\", "/").split("/")[-1]
        suffix = Path(filename).suffix.lower()
        if suffix not in (".xlsx", ".xls"):
            await file.close()
            raise HTTPException(415, "Upload an Excel .xlsx or .xls file.")
        key = uuid4().hex
        target = store.root / "uploads" / f"{key}{suffix}"
        temporary = store.root / "temp" / f"{key}.tmp"
        count = 0
        try:
            with temporary.open("wb") as handle:
                while chunk := await file.read(1024 * 1024):
                    count += len(chunk)
                    if count > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, "Workbook exceeds the 30 MB upload limit.")
                    handle.write(chunk)
            os.replace(temporary, target)
            sheets = await run_in_threadpool(sheet_names, target)
            record = {"id": key, "name": filename, "size": count, "sheets": sheets,
                      "stored_name": target.name, "created_at": now()}
            store.put("uploads", key, record)
            return record
        except HTTPException:
            target.unlink(missing_ok=True)
            raise
        except WorkbookError as exc:
            target.unlink(missing_ok=True)
            raise HTTPException(422, str(exc))
        except Exception:
            target.unlink(missing_ok=True)
            raise HTTPException(422, "Cannot import workbook. Check that it is valid and not encrypted.")
        finally:
            temporary.unlink(missing_ok=True)
            await file.close()

    @app.get("/api/uploads/{upload_id}/preview")
    def get_preview(upload_id: str, sheet: str, header_row: int | None = Query(None, ge=1, le=100),
                    module_id: str = "account-role-mapping", input_id: str = "source"):
        record = upload_or_404(upload_id)
        try:
            result = preview(store.root / "uploads" / record["stored_name"], sheet, header_row)
            module = registry.get(module_id)
            definition = next((d for d in module.metadata["inputs"] if d["id"] == input_id), None)
            if definition is None:
                raise ValueError("Unknown module input.")
            suggestions = {}
            for column in definition["columns"]:
                aliases = {normalized(v) for v in column["aliases"]}
                match = next((name for name in result["columns"] if normalized(name) in aliases), None)
                if match:
                    suggestions[column["key"]] = match
            result["suggested_mapping"] = suggestions
            result["missing_fields"] = [c["label"] for c in definition["columns"] if c["key"] not in suggestions]
            return result
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    @app.post("/api/jobs", status_code=202)
    def create_job(body: JobRequest):
        try:
            module = registry.get(body.module_id)
            if not module.metadata["enabled"]:
                raise ValueError("This module is not enabled.")
            config = module.config_model.model_validate(body.config).model_dump()
            expected = {d["id"] for d in module.metadata["inputs"]}
            if set(body.inputs) != expected:
                raise ValueError("Provide every required module input.")
            for definition in module.metadata["inputs"]:
                selection = body.inputs[definition["id"]]
                record = upload_or_404(selection.upload_id)
                if selection.sheet not in record["sheets"]:
                    raise ValueError("A selected worksheet does not exist.")
                required = {c["key"] for c in definition["columns"]}
                if set(selection.mapping) != required or not all(selection.mapping.values()):
                    raise ValueError("Map every required field before processing.")
                if len(set(selection.mapping.values())) != len(selection.mapping):
                    raise ValueError("Each required field must use a different source column.")
                for column in definition["columns"]:
                    blocked = {normalized(v) for v in column.get("forbidden_aliases", [])}
                    if normalized(selection.mapping[column["key"]]) in blocked:
                        raise ValueError(f'The selected column cannot be used for {column["label"]}.')
            request = body.model_dump()
            request["config"] = config
            return manager.submit(request)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        except RuntimeError as exc:
            raise HTTPException(429, str(exc))

    @app.get("/api/jobs")
    def jobs(limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0)):
        all_jobs = store.list("jobs")
        return {"total": len(all_jobs), "items": all_jobs[offset:offset+limit]}

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str):
        return job_or_404(job_id)

    @app.get("/api/jobs/{job_id}/tables/{table}")
    def table(job_id: str, table: str, market: str = "", role: str = "", search: str = "",
              sort: str = "", descending: bool = False,
              limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0)):
        payload = result_for(job_id)
        data = payload["tables"].get(table)
        if data is None:
            raise HTTPException(404, "Report table not found.")
        columns, records = data["columns"], data["rows"]
        market_index = columns.index("Market") if "Market" in columns else None
        role_index = columns.index("Account Role") if "Account Role" in columns else None
        markets = sorted({str(r[market_index]) for r in records}) if market_index is not None else []
        roles = sorted({str(r[role_index]) for r in records}) if role_index is not None else []
        if market and market_index is not None:
            records = [r for r in records if r[market_index] == market]
        if role and role_index is not None:
            records = [r for r in records if r[role_index] == role]
        if search:
            records = [r for r in records if search.casefold() in " ".join(str(v) for v in r).casefold()]
        if sort:
            if sort not in columns:
                raise HTTPException(422, "Unknown sort column.")
            idx = columns.index(sort)
            records = sorted(records, key=lambda row: (row[idx] is None, row[idx] if isinstance(row[idx], (float, int)) else str(row[idx])), reverse=descending)
        return {"columns": columns, "rows": records[offset:offset+limit], "total": len(records),
                "markets": markets, "roles": roles, "offset": offset}

    @app.get("/api/jobs/{job_id}/download")
    def download(job_id: str):
        job = job_or_404(job_id)
        if job["status"] != "succeeded":
            raise HTTPException(409, "Report is not ready for download.")
        target = store.root / "outputs" / f'{job["id"]}.xlsx'
        if not target.is_file():
            raise HTTPException(410, "Report file is missing. Run the job again.")
        return FileResponse(target, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            filename=f'DataMap-{job["created_at"][:10]}-{job["id"][:8]}.xlsx')

    @app.get("/api/dashboard")
    def dashboard():
        jobs = store.list("jobs")
        completed = [j for j in jobs if j["status"] == "succeeded"]
        return {"processed_files": len({v["upload_id"] for j in completed for v in j["request"]["inputs"].values()}),
                "uploaded_files": len(store.list("uploads")), "completed_jobs": len(completed),
                "latest_processing_date": completed[0]["finished_at"] if completed else None,
                "latest_metrics": completed[0]["metrics"] if completed else {},
                "module_count": sum(m["enabled"] for m in registry.describe()), "recent_jobs": jobs[:5]}

    @app.get("/api/templates")
    def templates():
        return store.list("templates")

    @app.post("/api/templates", status_code=201)
    def save_template(body: TemplateRequest):
        try:
            module = registry.get(body.module_id)
            config = module.config_model.model_validate(body.config).model_dump()
            safe_inputs = {}
            for definition in module.metadata["inputs"]:
                item = body.inputs.get(definition["id"], {})
                mapping = item.get("mapping", {})
                required = {c["key"] for c in definition["columns"]}
                if set(mapping) != required or any(not isinstance(v, str) or not v for v in mapping.values()):
                    raise ValueError("Complete the column mapping before saving a template.")
                if len(set(mapping.values())) != len(mapping):
                    raise ValueError("Each required field must use a different source column.")
                header_row = item.get("header_row", 1)
                if not isinstance(header_row, int) or not 1 <= header_row <= 100:
                    raise ValueError("Header row must be between 1 and 100.")
                safe_inputs[definition["id"]] = {"mapping": mapping, "header_row": header_row,
                                                 "sheet": str(item.get("sheet", ""))[:128]}
            record = {"id": uuid4().hex, "name": body.name.strip(), "module_id": body.module_id,
                      "config": config, "inputs": safe_inputs, "created_at": now()}
            if not record["name"]:
                raise ValueError("Give the template a name.")
            store.put("templates", record["id"], record)
            return record
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    @app.get("/api/settings")
    def settings():
        return store.get("preferences", "settings") or Settings().model_dump()

    @app.put("/api/settings")
    def save_settings(body: Settings):
        store.put("preferences", "settings", body.model_dump())
        return body.model_dump()

    built = ROOT / "frontend" / "dist"
    if built.is_dir():
        app.mount("/assets", StaticFiles(directory=built / "assets"), name="assets")
        @app.get("/{path:path}")
        def frontend(path: str):
            if path.startswith("api/"):
                raise HTTPException(404, "API endpoint not found.")
            return FileResponse(built / "index.html")
    return app

app = create_app()
