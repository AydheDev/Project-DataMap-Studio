from itertools import islice
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import pandas as pd
import openpyxl
import xlrd
from .normalization import ExcelFault, missing, public_value, text

MAX_ROWS = 1_000_000
MAX_COLUMNS = 256
# Applies to retained processing columns, never to a streamed preview.
MAX_CELLS = 8_000_000
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
            # Exporters may report a used range inflated by formatting, or one
            # smaller than the actual data. Read actual rows instead of trusting it.
            ws.reset_dimensions()
            formula_ws.reset_dimensions()
            for index, (cells, formulas) in enumerate(zip(ws.iter_rows(), formula_ws.iter_rows()), 1):
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
        for index, values in _raw_rows(path, sheet):
            if index > 1_048_576:
                raise WorkbookError("Worksheet contains rows outside the XLSX format limit.")
            while values and missing(values[-1]):
                values.pop()
            if len(values) > MAX_COLUMNS:
                raise WorkbookError(f"Worksheet contains data beyond column {MAX_COLUMNS:,}. Remove unused data columns.")
            yield index, values
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

def _sheet_records(path, sheet, header_row):
    """Yield headers followed by validated rows without retaining the worksheet."""
    headers = None
    count = 0
    stream = rows(path, sheet)
    try:
        for index, values in stream:
            if index < header_row:
                continue
            if index == header_row:
                if not values:
                    raise WorkbookError("Selected header row is empty.")
                headers, used = [], set()
                for i, v in enumerate(values, 1):
                    base = text(v) or f"Column {i}"
                    name, suffix = base, 2
                    while name in used:
                        name, suffix = f"{base} ({suffix})", suffix + 1
                    headers.append(name)
                    used.add(name)
                yield index, headers
                continue
            if headers is None or not values:
                continue
            width = len(headers)
            if len(values) > width:
                raise WorkbookError("Data extends beyond the selected headers. Choose the correct header row.")
            count += 1
            if count > MAX_ROWS:
                raise WorkbookError(f"Selected sheet exceeds {MAX_ROWS:,} non-empty data rows. Split it into smaller reporting periods.")
            yield index, values + [None] * (width - len(values))
        if headers is None:
            raise WorkbookError("Header row is outside this worksheet.")
    finally:
        stream.close()


def read_sheet(path, sheet, header_row=None, *, columns=None):
    """Materialize only requested columns; preserve original source row numbers.

    A row with content only in an unmapped column is still a source record and
    must reach validation/auditing rather than being silently discarded.
    """
    header_row = header_row or detect_header(path, sheet)
    stream = _sheet_records(path, sheet, header_row)
    try:
        _, headers = next(stream)
        selected = list(headers if columns is None else dict.fromkeys(columns))
        if any(name not in headers for name in selected):
            raise WorkbookError("Mapped columns were not found. Review the selected sheet and header row.")
        if not selected:
            raise WorkbookError("Select at least one column to process.")
        positions = [headers.index(name) for name in selected]
        records, references = [], []
        for index, values in stream:
            if (len(records) + 1) * len(selected) > MAX_CELLS:
                raise WorkbookError(f"Processing exceeds {MAX_CELLS:,} retained data cells across {len(selected):,} columns. Select fewer columns or split the reporting period.")
            records.append([values[i] for i in positions])
            references.append(index)
    finally:
        stream.close()
    frame = pd.DataFrame(records, columns=selected)
    frame.index = pd.Index(references, name="Source Row")
    return frame, header_row


def preview(path, sheet, header_row=None):
    header_row = header_row or detect_header(path, sheet)
    stream = _sheet_records(path, sheet, header_row)
    try:
        _, headers = next(stream)
        sample, count = [], 0
        for index, values in stream:
            count += 1
            if len(sample) < 20:
                sample.append({"source_row": index, "values": [public_value(v) for v in values]})
    finally:
        stream.close()
    return {"sheet": sheet, "header_row": header_row, "columns": headers,
            "row_count": count, "column_count": len(headers), "rows": sample}
