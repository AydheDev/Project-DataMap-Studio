import os
from datetime import datetime, date
from pathlib import Path
from uuid import uuid4
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill, Alignment
from .normalization import ExcelFault, missing

def write_workbook(tables, target: Path):
    """Stream formatted sheets, force untrusted strings to text, then atomically replace."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{uuid4().hex}.tmp"
    book = Workbook(write_only=True)
    try:
        for name, frame in tables.items():
            sheet = book.create_sheet(name)
            sheet.freeze_panes = "A2"
            for col, label in enumerate(frame.columns, 1):
                from openpyxl.utils import get_column_letter
                sheet.column_dimensions[get_column_letter(col)].width = min(45, max(19, len(str(label)) + 3))
            header = []
            for label in frame.columns:
                cell = WriteOnlyCell(sheet, str(label))
                cell.data_type = "s"
                cell.font = Font(name="Calibri", bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="173B3F")
                cell.alignment = Alignment(vertical="center")
                header.append(cell)
            sheet.append(header)
            for row in frame.itertuples(index=False, name=None):
                cells = []
                for value in row:
                    if isinstance(value, ExcelFault):
                        value = value.original or value.code
                    elif missing(value):
                        value = None
                    elif hasattr(value, "item"):
                        value = value.item()
                    if isinstance(value, datetime) and value.tzinfo:
                        value = value.isoformat()
                    cell = WriteOnlyCell(sheet, value)
                    # No generated cell may execute an input formula or be a live Excel error.
                    if isinstance(value, str):
                        cell.data_type = "s"
                    if isinstance(value, (date, datetime)):
                        cell.number_format = "yyyy-mm-dd hh:mm:ss"
                    cells.append(cell)
                sheet.append(cells)
            if len(frame.columns):
                from openpyxl.utils import get_column_letter
                sheet.auto_filter.ref = f"A1:{get_column_letter(len(frame.columns))}{max(1,len(frame)+1)}"
        book.save(temporary)
        os.replace(temporary, target)
    finally:
        book.close()
        temporary.unlink(missing_ok=True)
