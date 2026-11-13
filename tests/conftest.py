import pytest
import pandas as pd
from openpyxl import Workbook
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import create_app

HEADERS = ["Market", "FDS JobRole", "FDS Email", "EIP Email", "Salesforce Last login", "Salesforce Fed ID"]
SOURCE_ROWS = [
    ["UK", "Manager", " Alice@Example.com ", "", datetime(2026,10,30), ""],
    ["UK", " MANAGER ", "alice@example.com", "", datetime(2026,10,31), "present"],
    ["UK", "Agent", "alice@example.com", "", datetime(2026,10,30), ""],
    ["DE", "Manager", "alice@example.com", "", datetime(2026,10,30), ""],
    ["UK", "Agent", "  ", " Bob@Example.com ", datetime(2026,10,30), ""],
    ["UK", "Outsider", "other@example.com", "", datetime(2026,10,30), ""],
    ["UK", "", "blankrole@example.com", "", datetime(2026,10,30), ""],
    ["UK", "Agent", "blank@example.com", "", None, "present"],
    ["UK", "Agent", "na@example.com", "", "#N/A", "present"],
    ["UK", "Agent", "value@example.com", "", "#VALUE!", ""],
    ["UK", "Agent", "", "", datetime(2026,10,30), ""],
    ["UK", "Agent", "not-an-email", "good@example.com", datetime(2026,10,30), ""],
    [" ", "Agent", "market@example.com", "", datetime(2026,10,30), ""],
    ["UK", "Agent", "spaces@example.com", "", "  ", ""],
    ["UK", "Agent", "never@example.com", "", "never", ""],
    ["UK", "Agent", "formula@example.com", "", "=NA()", ""],
]
@pytest.fixture
def workbooks(tmp_path):
    source = tmp_path / "source.xlsx"
    book = Workbook()
    ws = book.active
    ws.title = "New reporting period"
    ws.append(["Report generated for testing"])
    ws.append(HEADERS)
    for row in SOURCE_ROWS:
        ws.append(row)
    other = book.create_sheet("Other")
    other.append(["Market", "Amount"])
    other.append(["FR", 12])
    book.save(source)
    roles = tmp_path / "roles.xlsx"
    book = Workbook()
    ws = book.active
    ws.title = "Approved"
    for row in [["Role Code"], ["Manager"], ["Agent"], ["Viewer"], [" manager "], [None]]:
        ws.append(row)
    book.save(roles)
    return source, roles

@pytest.fixture
def inputs():
    return {"source": pd.DataFrame([row[:5] for row in SOURCE_ROWS],
            columns=["market","role","fds_email","eip_email","login"], index=range(3,19)),
            "roles": pd.DataFrame({"role_code":["Manager","Agent","Viewer"," manager "]})}

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "storage")) as client:
        yield client
