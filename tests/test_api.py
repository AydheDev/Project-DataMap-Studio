import time
import io
import openpyxl
from app.repositories.store import Store
from app.main import create_app
from fastapi.testclient import TestClient

def upload(client, path):
    with path.open("rb") as handle:
        response = client.post("/api/uploads", files={"file": (path.name, handle)})
    assert response.status_code == 201, response.text
    return response.json()

def request_for(source, roles):
    return {"module_id": "account-role-mapping", "inputs": {
        "source": {"upload_id": source["id"], "sheet": "New reporting period", "header_row":2,
                   "mapping":{"market":"Market","role":"FDS JobRole","fds_email":"FDS Email",
                              "eip_email":"EIP Email","login":"Salesforce Last login"}},
        "roles": {"upload_id":roles["id"], "sheet":"Approved", "header_row":1,
                  "mapping":{"role_code":"Role Code"}}}, "config":{}}

def wait(client, id):
    for _ in range(100):
        job=client.get(f"/api/jobs/{id}").json()
        if job["status"] in ("succeeded","failed"):
            return job
        time.sleep(.03)
    raise AssertionError("Job did not complete")

def test_complete_workflow(client, workbooks):
    source, roles = [upload(client, file) for file in workbooks]
    preview=client.get(f'/api/uploads/{source["id"]}/preview', params={"sheet":"New reporting period"}).json()
    assert preview["header_row"] == 2
    assert preview["suggested_mapping"]["login"] == "Salesforce Last login"
    body=request_for(source,roles)
    response=client.post("/api/jobs",json=body)
    assert response.status_code == 202, response.text
    job=wait(client,response.json()["id"])
    assert job["status"] == "succeeded", job
    assert job["metrics"]["unique_mappings"] == 4
    report=client.get(f'/api/jobs/{job["id"]}/download')
    assert report.status_code == 200
    book=openpyxl.load_workbook(io.BytesIO(report.content))
    assert book.sheetnames == ["Market Summary","Role Counts","Unique Mapping","Duplicate Audit",
                              "Data Quality","Unmatched Roles","Excluded Records"]
    assert book["Unique Mapping"].max_row == 5
    assert "[redacted]" in [r[3].value for r in list(book["Excluded Records"].rows)[1:]]
    book.close()
    table=client.get(f'/api/jobs/{job["id"]}/tables/Role Counts',
                    params={"market":"UK","sort":"Unique Account Count","descending":True,"limit":1}).json()
    assert table["total"] == 3
    assert table["rows"][0] == ["UK","Agent",2]
    assert client.get("/api/dashboard").json()["processed_files"] == 2
    assert client.get("/api/jobs").json()["total"] == 1
    template=client.post("/api/templates",json={"name":"Monthly","module_id":body["module_id"],
                                              "config":body["config"],"inputs":body["inputs"]})
    assert template.status_code == 201
    assert "upload_id" not in template.json()["inputs"]["source"]
    assert len(client.get("/api/templates").json()) == 1
    settings=client.put("/api/settings",json={"include_zero_counts":False})
    assert settings.status_code == 200
    assert client.get("/api/settings").json()["include_zero_counts"] is False
    # Same mapping/config must support a fresh reporting period.
    again=client.post("/api/jobs",json=body)
    assert wait(client,again.json()["id"])["metrics"] == job["metrics"]

def test_errors_and_safety(client, workbooks):
    assert client.post("/api/uploads",files={"file":("script.py",b"bad")}).status_code == 415
    assert client.post("/api/uploads",files={"file":("broken.xlsx",b"bad")}).status_code == 422
    assert client.post("/api/uploads",files={"file":("source.xlsx",b"bad")},
                       headers={"Origin":"https://untrusted.example"}).status_code == 403
    source,roles=[upload(client,p) for p in workbooks]
    assert client.get(f'/api/uploads/{source["id"]}/preview',params={"sheet":"Missing"}).status_code == 422
    body=request_for(source,roles)
    body["inputs"]["source"]["mapping"].pop("login")
    assert client.post("/api/jobs",json=body).status_code == 422
    body=request_for(source,roles)
    body["inputs"]["source"]["mapping"]["login"]="Missing column"
    response=client.post("/api/jobs",json=body)
    job=wait(client,response.json()["id"])
    assert job["status"] == "failed"
    assert client.get(f'/api/jobs/{job["id"]}/download').status_code == 409
    assert not (client.app.state.store.root / "outputs" / f'{job["id"]}.xlsx').exists()
    assert client.get("/api/jobs/not-found").status_code == 404
    assert client.post("/api/jobs",json={"module_id":"sample","inputs":{}}).status_code == 422

def test_restart_persistence_and_recovery(tmp_path):
    root=tmp_path/"persistent"
    store=Store(root)
    store.put("jobs","interrupted",{"id":"interrupted","status":"running"})
    store.put("preferences","settings",{"include_zero_counts":False})
    with TestClient(create_app(root)) as client:
        assert client.get("/api/jobs/interrupted").json()["status"] == "failed"
        assert client.get("/api/settings").json()["include_zero_counts"] is False
