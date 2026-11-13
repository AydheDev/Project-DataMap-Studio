import logging
import zipfile
import pytest
from app.core.logging import RedactAccessQuery
from app.services.normalization import login_problem
from app.services.excel import sheet_names, WorkbookError
from app.main import create_app
from app.repositories.store import Store
from test_api import upload, request_for

@pytest.mark.parametrize("value", ["2026-10", "October 2026", "2026", "10/2026", "2026-02-30"])
def test_incomplete_or_impossible_date_is_not_inferred(value):
    assert login_problem(value) == "invalid_login"

def test_fed_id_cannot_be_mapped_as_login(client, workbooks):
    source,roles=[upload(client,p) for p in workbooks]
    body=request_for(source,roles)
    body["inputs"]["source"]["mapping"]["login"]="Salesforce Fed ID"
    response=client.post("/api/jobs",json=body)
    assert response.status_code == 422
    assert "cannot be used" in response.json()["detail"]

def test_access_log_strips_search_email():
    record=logging.LogRecord("uvicorn.access",20,"",0,'%s - "%s %s HTTP/%s" %d',
                             ("127.0.0.1","GET","/api/jobs/a/tables/Unique%20Mapping?search=alice@example.com","1.1",200),None)
    assert RedactAccessQuery().filter(record)
    assert "alice@example.com" not in record.getMessage()
    assert "/api/jobs/a/tables/" in record.getMessage()

def test_upload_size_guard(client):
    response=client.post("/api/uploads",content=b"",headers={"Content-Length":str(32*1024*1024)})
    assert response.status_code == 413

def test_expanded_workbook_limit(tmp_path, monkeypatch):
    target=tmp_path/"large.xlsx"
    with zipfile.ZipFile(target,"w") as archive:
        archive.writestr("oversize",b"x"*1024)
    monkeypatch.setattr("app.services.excel.MAX_EXPANDED_BYTES",512)
    with pytest.raises(WorkbookError,match="expands"):
        sheet_names(target)

def test_safe_temp_cleanup_does_not_touch_originals(tmp_path):
    store=Store(tmp_path)
    original=tmp_path/"uploads"/"original.xlsx"
    report=tmp_path/"outputs"/"complete.xlsx"
    pending=tmp_path/"outputs"/".partial.tmp"
    for file in [original,report,pending]:
        file.write_bytes(b"keep" if file!=pending else b"incomplete")
    store.recover()
    assert original.exists() and report.exists()
    assert not pending.exists()
