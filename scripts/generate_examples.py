"""Create synthetic workbooks with intentionally challenging records; no personal data."""
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import xlwt

ROOT = Path(__file__).resolve().parents[1]

def write_book(path, sheet, headers, rows, preamble=None):
    book=Workbook()
    ws=book.active
    ws.title=sheet
    if preamble:
        ws.append([preamble])
    ws.append(headers)
    header_row=ws.max_row
    for cell in ws[header_row]:
        cell.font=Font(bold=True,color="FFFFFF")
        cell.fill=PatternFill("solid",fgColor="173B3F")
    for row in rows:
        ws.append(row)
    ws.freeze_panes=f"A{header_row+1}"
    for col in "ABCDEF":
        ws.column_dimensions[col].width=26
    book.save(path)

def generate():
    target=ROOT/"examples"
    target.mkdir(exist_ok=True)
    login=datetime(2026,10,30,9,15)
    rows=[
        ["UK","Manager"," Alice@Example.com ","",login,""],
        ["UK"," MANAGER ","alice@example.com","",datetime(2026,10,31),"F-100"],
        ["UK","Agent","alice@example.com","",login,""],
        ["DE","Manager","alice@example.com","",login,""],
        ["UK","Agent"," "," Bob@Example.com ",login,""],
        ["UK","Unknown","other@example.com","",login,""],
        ["UK","","blankrole@example.com","",login,""],
        ["UK","Agent","blank@example.com","",None,"F-101"],
        ["UK","Agent","na@example.com","","#N/A","F-102"],
        ["UK","Agent","error@example.com","","#VALUE!",""],
        ["UK","Agent","","",login,""],
        ["UK","Agent","invalid-email","fallback@example.com",login,""],
        [" ","Agent","market@example.com","",login,""],
        ["UK","Agent","spaces@example.com",""," ",""],
        ["UK","Agent","never@example.com","","never",""],
        ["UK","Agent","formula@example.com","","=NA()",""],
    ]
    write_book(target/"sample-source.xlsx","Current Period",
        ["Market","FDS JobRole","FDS Email","EIP Email","Salesforce Last login","Salesforce Fed ID"],
        rows,preamble="Synthetic test data — source headers begin on row 2")
    write_book(target/"sample-approved-roles.xlsx","Approved Roles",["Role Code"],
        [["Manager"],["Agent"],["Viewer"],[" manager "]])
    write_book(target/"sample-next-period.xlsx","Next Period",
        ["Country","Assigned Role","Primary Email","Backup Email","Login Timestamp"],
        [["FR","Agent"," new@example.com ","","2026-11-01"],["FR","Manager","new@example.com","","2026-11-01"]])
    book=xlwt.Workbook()
    sheet=book.add_sheet("Approved Legacy")
    for i,value in enumerate(["Role Code","Manager","Agent","Viewer"]):
        sheet.write(i,0,value)
    book.save(str(target/"sample-approved-roles.xls"))
    print(f"Created four synthetic workbooks in {target}")

if __name__=="__main__":
    generate()
