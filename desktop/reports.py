from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QFileDialog
from .widgets import label, button, table, fill_table, text

class ReportView(QWidget):
    def __init__(self, owner, quality=False):
        super().__init__()
        self.owner, self.quality = owner, quality
        self.payload = None
        self.loaded_id = None
        self.generation = 0
        self.offset = 0
        self.sort_index = None
        self.descending = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        self.jobs = QComboBox()
        self.jobs.setAccessibleName("Report processing run")
        self.jobs.activated.connect(self.load_selected)
        top.addWidget(self.jobs, 1)
        self.export = button("Save Excel report…", self.save_report)
        top.addWidget(self.export)
        layout.addLayout(top)
        self.summary = label("Process your workbooks to create a report.", "status")
        layout.addWidget(self.summary)
        filters = QHBoxLayout()
        self.sheet = QComboBox()
        self.sheet.setAccessibleName("Report worksheet")
        self.sheet.activated.connect(self.change_table)
        filters.addWidget(self.sheet, 1)
        self.market, self.role = QComboBox(), QComboBox()
        self.market.setAccessibleName("Filter market")
        self.role.setAccessibleName("Filter role")
        for control in (self.market, self.role):
            control.activated.connect(self.reset_filter)
            filters.addWidget(control)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search this table…")
        self.search.setAccessibleName("Search report")
        self.search.textChanged.connect(self.reset_filter)
        filters.addWidget(self.search, 1)
        layout.addLayout(filters)
        self.table = table()
        self.table.horizontalHeader().sectionClicked.connect(self.sort_by)
        layout.addWidget(self.table, 1)
        pagination = QHBoxLayout()
        self.count = label("", "muted")
        pagination.addWidget(self.count, 1)
        self.previous = button("Previous", lambda: self.move_page(-50), True)
        self.next = button("Next", lambda: self.move_page(50), True)
        pagination.addWidget(self.previous)
        pagination.addWidget(self.next)
        layout.addLayout(pagination)
        self.notes = label("", "muted")
        layout.addWidget(self.notes)
        self.refresh()

    def refresh(self, job_id=None):
        previous = job_id or self.jobs.currentData()
        completed = [j for j in self.owner.workspace.store.list("jobs") if j["status"] == "succeeded"]
        self.jobs.blockSignals(True)
        self.jobs.clear()
        for job in completed:
            self.jobs.addItem(job["created_at"][:19].replace("T", " ") + " · " + job["id"][:8], job["id"])
        self.jobs.setCurrentIndex(max(0, self.jobs.findData(previous)))
        self.jobs.blockSignals(False)
        self.export.setEnabled(bool(completed))
        if self.jobs.currentData() != self.loaded_id:
            self.load_selected()
        elif not completed:
            self.export.setEnabled(False)

    def load_selected(self):
        key = self.jobs.currentData()
        self.generation += 1
        generation = self.generation
        self.payload = None
        self.export.setEnabled(False)
        fill_table(self.table, [], [])
        if not key:
            self.loaded_id = None
            return
        self.summary.setText("Loading report…")
        self.owner.run_task(lambda: self.owner.workspace.result(key),
                            lambda payload: self.accept_result(key, payload, generation),
                            lambda error: self.owner.message(error, True))

    def accept_result(self, key, payload, generation):
        if generation != self.generation:
            return
        self.loaded_id, self.payload = key, payload
        metrics = payload["metrics"]
        self.summary.setText(
            f'{metrics["source_rows"]:,} source rows   ·   {metrics["eligible_rows"]:,} eligible   ·   '
            f'{metrics["unique_mappings"]:,} unique mappings   ·   {metrics["duplicates_removed"]:,} duplicates removed')
        allowed = (["Data Quality", "Unmatched Roles", "Excluded Records", "Duplicate Audit"]
                   if self.quality else list(payload["tables"]))
        self.sheet.blockSignals(True)
        self.sheet.clear()
        self.sheet.addItems(allowed)
        self.sheet.blockSignals(False)
        self.notes.setText("\n".join(payload["notes"]))
        self.export.setEnabled(True)
        self.change_table()

    def change_table(self):
        if not self.payload:
            return
        data = self.payload["tables"][self.sheet.currentText()]
        for control, column, title in [(self.market, "Market", "All markets"),
                                       (self.role, "Account Role", "All roles")]:
            control.blockSignals(True)
            control.clear()
            control.addItem(title, "")
            if column in data["columns"]:
                index = data["columns"].index(column)
                for value in sorted({str(r[index]) for r in data["rows"]}):
                    control.addItem(value, value)
            control.setEnabled(control.count() > 1)
            control.blockSignals(False)
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.sort_index = None
        self.offset = 0
        self.render()

    def filtered_rows(self):
        if not self.payload:
            return [], []
        data = self.payload["tables"][self.sheet.currentText()]
        columns, rows = data["columns"], data["rows"]
        for control, column in [(self.market, "Market"), (self.role, "Account Role")]:
            if control.currentData() and column in columns:
                index = columns.index(column)
                rows = [r for r in rows if str(r[index]) == control.currentData()]
        search = self.search.text().strip().casefold()
        if search:
            rows = [r for r in rows if search in " ".join(text(v) for v in r).casefold()]
        if self.sort_index is not None:
            def sort_key(row):
                value = row[self.sort_index]
                return (0, value) if isinstance(value, (int, float)) else (1, text(value))
            rows = sorted(rows, key=sort_key, reverse=self.descending)
        return columns, rows

    def render(self):
        columns, rows = self.filtered_rows()
        self.offset = min(self.offset, max(0, ((len(rows) - 1) // 50) * 50))
        fill_table(self.table, columns, rows[self.offset:self.offset + 50])
        self.count.setText(f'{len(rows):,} matching records · Showing {self.offset + 1 if rows else 0}–{min(len(rows), self.offset + 50)}')
        self.previous.setEnabled(self.offset > 0)
        self.next.setEnabled(self.offset + 50 < len(rows))

    def reset_filter(self):
        self.offset = 0
        self.render()

    def move_page(self, amount):
        self.offset = max(0, self.offset + amount)
        self.render()

    def sort_by(self, index):
        self.descending = not self.descending if self.sort_index == index else False
        self.sort_index = index
        self.offset = 0
        self.render()

    def save_report(self):
        if not self.loaded_id:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save Excel report",
            f"DataMap-{self.loaded_id[:8]}.xlsx", "Excel workbook (*.xlsx)")
        if filename:
            key = self.loaded_id
            self.owner.run_task(lambda: self.owner.workspace.save_report(key, filename),
                                lambda destination: self.owner.message("Report saved: " + str(destination)))
