from itertools import islice, zip_longest
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import pandas as pd
import openpyxl
import xlrd
from .normalization import ExcelFault, missing, public_value, text

MAX_ROWS = 200_000
MAX_COLUMNS = 256
MAX_CELLS = 2_000_000
MAX_EXPANDED_BYTES = 200 * 1024 * 1024

class WorkbookError(ValueError):
    pass

def check_container(path: Path):
    signature = path.read_bytes()[:8] if path.stat().st_size < 8 else None
    if signature is None:
        with path.open("rb") as handle:
            signature = handle.read(8)
    if path.suffix == ".xlsx":
        if not signature.startswith(b"PK"):
            raise WorkbookError("This file is not a valid XLSX workbook.")
        try:
            with ZipFile(path) as archive:
                if sum(i.file_size for i in archive.infolist()) > MAX_EXPANDED_BYTES:
                    raise WorkbookError("Workbook expands beyond the 200 MB safety limit.")
                if len(archive.infolist()) > 10_000:
                    raise WorkbookError("Workbook contains too many internal entries.")
        except BadZipFile as exc:
            raise WorkbookError("The XLSX workbook is corrupt.") from exc
    elif path.suffix == ".xls":
        if not signature.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
            raise WorkbookError("This file is not a valid legacy XLS workbook.")
    else:
        raise WorkbookError("Only .xlsx and .xls workbooks are supported.")

def sheet_names(path):
    check_container(path)
    book = None
    try:
        book = (xlrd.open_workbook(path, on_demand=True) if path.suffix == ".xls"
                else openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False))
        names = book.sheet_names() if path.suffix == ".xls" else book.sheetnames
        if not names:
            raise WorkbookError("Workbook contains no worksheets.")
        return names
    except WorkbookError:
        raise
    except Exception as exc:
        raise WorkbookError("Cannot open workbook. Check that it is valid and not encrypted.") from exc
    finally:
        if book is not None:
            book.release_resources() if path.suffix == ".xls" else book.close()

def _raw_rows(path, sheet):
    if sheet not in sheet_names(path):
        raise WorkbookError("Selected worksheet does not exist.")
    if path.suffix == ".xls":
        book = xlrd.open_workbook(path, on_demand=True)
        try:
            ws = book.sheet_by_name(sheet)
            if ws.ncols > MAX_COLUMNS or ws.nrows > MAX_ROWS + 100:
                raise WorkbookError("Worksheet exceeds the supported row or column limit.")
            for index in range(ws.nrows):
                values = []
                for cell in ws.row(index):
                    if cell.ctype == xlrd.XL_CELL_ERROR:
                        value = ExcelFault(xlrd.error_text_from_code.get(cell.value, "#VALUE!"))
                    elif cell.ctype == xlrd.XL_CELL_DATE:
                        value = xlrd.xldate_as_datetime(cell.value, book.datemode)
                    elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                        value = bool(cell.value)
                    else:
                        value = cell.value
                    values.append(value)
                yield index + 1, values
        finally:
            book.release_resources()
    else:
        values_book = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False)
        formulas_book = openpyxl.load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            ws, formula_ws = values_book[sheet], formulas_book[sheet]
            if (ws.max_column or 0) > MAX_COLUMNS or (ws.max_row or 0) > MAX_ROWS + 100:
                raise WorkbookError("Worksheet exceeds the supported row or column limit.")
            for index, (cells, formulas) in enumerate(zip(ws.iter_rows(), formula_ws.iter_rows()), 1):
                if index > MAX_ROWS + 100 or len(cells) > MAX_COLUMNS:
                    raise WorkbookError("Worksheet exceeds the supported row or column limit.")
                values = []
                for cell, formula in zip(cells, formulas):
                    value = cell.value
                    if cell.data_type == "e":
                        value = ExcelFault(str(value), formula.value if formula.data_type == "f" else None)
                    elif formula.data_type == "f" and value is None:
                        value = ExcelFault("#UNCACHED_FORMULA!", formula.value)
                    values.append(value)
                yield index, values
        finally:
            values_book.close()
            formulas_book.close()

def rows(path, sheet):
    try:
        yield from _raw_rows(path, sheet)
    except WorkbookError:
        raise
    except Exception as exc:
        raise WorkbookError("Cannot read worksheet data. Check the workbook for corruption or unsupported content.") from exc

def detect_header(path, sheet):
    stream = rows(path, sheet)
    try:
        candidates = list(islice(stream, 30))
    finally:
        stream.close()
    if not candidates:
        raise WorkbookError("Worksheet is empty.")
    def score(item):
        values = [text(v) for v in item[1] if not missing(v)]
        return sum(isinstance(v, str) for v in item[1]) + len(set(values))
    return max(candidates, key=score)[0]

def read_sheet(path, sheet, header_row=None):
    header_row = header_row or detect_header(path, sheet)
    headers, records, references = None, [], []
    width = 0
    for index, values in rows(path, sheet):
        if index < header_row:
            continue
        if index == header_row:
            while values and missing(values[-1]):
                values.pop()
            if not values:
                raise WorkbookError("Selected header row is empty.")
            headers = []
            used = set()
            for i, v in enumerate(values, 1):
                base = text(v) or f"Column {i}"
                name, suffix = base, 2
                while name in used:
                    name, suffix = f"{base} ({suffix})", suffix + 1
                headers.append(name)
                used.add(name)
            width = len(headers)
            continue
        if headers is None or all(missing(v) for v in values):
            continue
        if len(values) > width and any(not missing(v) for v in values[width:]):
            raise WorkbookError("Data extends beyond the selected headers. Choose the correct header row.")
        values = values[:width] + [None] * max(0, width-len(values))
        records.append(values)
        references.append(index)
        if len(records) > MAX_ROWS or len(records) * width > MAX_CELLS:
            raise WorkbookError("Selected sheet exceeds 200,000 rows or 2,000,000 cells. Split the workbook.")
    if headers is None:
        raise WorkbookError("Header row is outside this worksheet.")
    frame = pd.DataFrame(records, columns=headers)
    frame.index = pd.Index(references, name="Source Row")
    return frame, header_row

def preview(path, sheet, header_row=None):
    frame, detected = read_sheet(path, sheet, header_row)
    return {"sheet": sheet, "header_row": detected, "columns": list(frame.columns),
            "row_count": len(frame), "column_count": len(frame.columns),
            "rows": [{"source_row": int(i), "values": [public_value(v) for v in row]}
                     for i, row in frame.head(20).iterrows()]}
