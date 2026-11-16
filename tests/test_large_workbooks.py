"""Regression coverage for wide exports and bounded import memory."""
import re
from zipfile import ZipFile
import openpyxl
import pytest
from app.services import excel
from app.services.normalization import ExcelFault


def test_preview_streams_all_records_without_materializing_frame(workbooks, monkeypatch):
    def no_frame(*args, **kwargs):
        raise AssertionError('Preview must not materialize a DataFrame')
    monkeypatch.setattr(excel.pd, 'DataFrame', no_frame)
    monkeypatch.setattr(excel, 'MAX_CELLS', 1)
    result = excel.preview(workbooks[0], 'New reporting period', 2)
    assert result['row_count'] == 16
    assert result['column_count'] == 6
    assert result['rows'][-1]['source_row'] == 18
    assert result['rows'][-1]['values'][4]['error'] == '#UNCACHED_FORMULA!'


def test_projection_enforces_retained_cell_budget(workbooks, monkeypatch):
    monkeypatch.setattr(excel, 'MAX_CELLS', 32)
    with pytest.raises(excel.WorkbookError, match='32 retained data cells'):
        excel.read_sheet(workbooks[0], 'New reporting period', 2)
    frame, _ = excel.read_sheet(workbooks[0], 'New reporting period', 2,
                               columns=['Salesforce Last login', 'Market'])
    assert list(frame.columns) == ['Salesforce Last login', 'Market']
    assert len(frame) == 16
    assert frame.loc[18, 'Salesforce Last login'] == ExcelFault('#UNCACHED_FORMULA!', '=NA()')
    monkeypatch.setattr(excel, 'MAX_CELLS', 31)
    with pytest.raises(excel.WorkbookError, match='31 retained data cells'):
        excel.read_sheet(workbooks[0], 'New reporting period', 2,
                         columns=['Salesforce Last login', 'Market'])


def test_unknown_projection_rejected(workbooks):
    with pytest.raises(excel.WorkbookError, match='Mapped columns were not found'):
        excel.read_sheet(workbooks[0], 'New reporting period', 2, columns=['Absent'])


@pytest.mark.parametrize('dimension', ['A1:XFD1048576', 'A1:A1'])
def test_xlsx_dimension_metadata_does_not_hide_or_inflate_data(workbooks, tmp_path, dimension):
    target = tmp_path / 'dimensions.xlsx'
    with ZipFile(workbooks[0]) as source, ZipFile(target, 'w') as output:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == 'xl/worksheets/sheet1.xml':
                data = re.sub(rb'<dimension ref="[^"]+"', f'<dimension ref="{dimension}"'.encode(), data)
            output.writestr(info, data)
    result = excel.preview(target, 'New reporting period')
    assert result['header_row'] == 2
    assert result['row_count'] == 16
    assert result['column_count'] == 6


def test_blank_gaps_and_unmapped_only_records_keep_source_references(tmp_path, monkeypatch):
    path = tmp_path / 'gaps.xlsx'
    book = openpyxl.Workbook()
    ws = book.active
    ws.append(['Mapped', 'Other'])
    ws.append(['value', None])
    ws.cell(7, 2, 'Only unrelated content')
    ws.cell(1000, 300).number_format = '0.00'  # Formatting is not data.
    book.save(path)
    monkeypatch.setattr(excel, 'MAX_ROWS', 2)
    frame, _ = excel.read_sheet(path, 'Sheet', 1, columns=['Mapped'])
    assert list(frame.index) == [2, 7]
    assert excel.missing(frame.loc[7, 'Mapped'])
    assert excel.preview(path, 'Sheet', 1)['row_count'] == 2
    monkeypatch.setattr(excel, 'MAX_ROWS', 1)
    with pytest.raises(excel.WorkbookError, match='1 non-empty data rows'):
        excel.preview(path, 'Sheet', 1)


def test_preview_over_old_row_and_cell_limits_retains_only_twenty_rows(monkeypatch):
    def records(*args):
        yield 1, [f'Column {i}' for i in range(12)]
        for index in range(2, 200_003):
            yield index, [index] * 12
    monkeypatch.setattr(excel, 'rows', records)
    result = excel.preview(None, 'Sheet', 1)
    assert result['row_count'] == 200_001
    assert len(result['rows']) == 20
    assert result['rows'][-1]['source_row'] == 21


def test_projection_still_rejects_data_beyond_headers(tmp_path):
    path = tmp_path / 'bad-header.xlsx'
    book = openpyxl.Workbook()
    ws = book.active
    ws.append(['Header'])
    ws.append(['value', 'unheaded data'])
    book.save(path)
    with pytest.raises(excel.WorkbookError, match='Data extends beyond'):
        excel.read_sheet(path, 'Sheet', 1, columns=['Header'])


def test_invalid_physical_row_address_is_bounded(monkeypatch):
    monkeypatch.setattr(excel, '_raw_rows', lambda *args: iter([(1_048_577, [])]))
    with pytest.raises(excel.WorkbookError, match='outside the XLSX format limit'):
        list(excel.rows(None, 'Sheet'))
