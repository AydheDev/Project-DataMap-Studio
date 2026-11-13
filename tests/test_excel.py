import io
import pandas as pd
import pytest
import openpyxl
import xlwt
from app.services.excel import read_sheet, sheet_names, WorkbookError, preview
from app.services.normalization import ExcelFault
from app.services.export import write_workbook

def test_import_preserves_rows_and_errors(workbooks):
    source, _ = workbooks
    assert sheet_names(source) == ["New reporting period", "Other"]
    frame, header = read_sheet(source, "New reporting period")
    assert header == 2
    assert len(frame) == 16
    assert frame.index[0] == 3
    assert frame.loc[11,"Salesforce Last login"] == ExcelFault("#N/A")
    assert frame.loc[18,"Salesforce Last login"] == ExcelFault("#UNCACHED_FORMULA!", "=NA()")
    assert preview(source, "Other", 1)["row_count"] == 1
    with pytest.raises(WorkbookError, match="does not exist"):
        read_sheet(source, "Missing")
    with pytest.raises(WorkbookError):
        read_sheet(source, "Other", 99)

def test_xls_support(tmp_path):
    path = tmp_path / "legacy.xls"
    book = xlwt.Workbook()
    sheet = book.add_sheet("Legacy")
    for i, row in enumerate([["Market","Email"],["UK","alice@example.com"]]):
        for j, value in enumerate(row):
            sheet.write(i,j,value)
    book.save(str(path))
    frame, header = read_sheet(path,"Legacy")
    assert header == 1
    assert frame.iloc[0]["Market"] == "UK"

def test_corrupt_and_spoofed(tmp_path):
    path = tmp_path / "fake.xlsx"
    path.write_text("This is not Excel")
    with pytest.raises(WorkbookError):
        sheet_names(path)

def test_safe_export_and_atomic_failure(tmp_path, monkeypatch):
    target = tmp_path / "safe.xlsx"
    frame = pd.DataFrame({"Input":["=HYPERLINK(\"bad\")", "+cmd", "@formula", "#N/A", ExcelFault("#VALUE!")],
                          "Count":[1,2,3,4,5]})
    write_workbook({"Test":frame}, target)
    with target.open("rb") as handle:
        book = openpyxl.load_workbook(handle, data_only=False)
        ws=book["Test"]
        assert ws["A2"].data_type == "s"
        assert ws["A5"].data_type == "s"
        assert ws.freeze_panes == "A2"
        assert ws.auto_filter.ref == "A1:B6"
        book.close()
    previous = target.read_bytes()
    def fail(*args):
        raise OSError("Simulated disk failure")
    monkeypatch.setattr("app.services.export.os.replace", fail)
    with pytest.raises(OSError):
        write_workbook({"Test":frame},target)
    assert target.read_bytes() == previous
    assert not list(tmp_path.glob("*.tmp"))
