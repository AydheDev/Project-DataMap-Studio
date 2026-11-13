from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QComboBox, QSpinBox, QFormLayout, QFileDialog, QCheckBox,
)

def text(value):
    if value is None:
        return ""
    if isinstance(value, dict) and "error" in value:
        return value["error"]
    return str(value)

def label(value, name=""):
    widget = QLabel(value)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    widget.setObjectName(name)
    return widget

def button(title, callback, secondary=False):
    widget = QPushButton(title)
    if secondary:
        widget.setObjectName("secondary")
    widget.clicked.connect(callback)
    return widget

def panel():
    widget = QFrame()
    widget.setObjectName("panel")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    return widget, layout

def heading(title, description):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(label(title, "heading"))
    layout.addWidget(label(description, "muted"))
    return widget

def table():
    widget = QTableWidget()
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.setAlternatingRowColors(True)
    widget.verticalHeader().setVisible(False)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    widget.setMinimumHeight(170)
    return widget

def fill_table(widget, columns, rows):
    widget.setSortingEnabled(False)
    widget.clear()
    widget.setColumnCount(len(columns))
    widget.setHorizontalHeaderLabels(columns)
    widget.setRowCount(len(rows))
    for row_index, values in enumerate(rows):
        for col_index, value in enumerate(values):
            item = QTableWidgetItem(text(value))
            if isinstance(value, (int, float)):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            widget.setItem(row_index, col_index, item)
    widget.resizeColumnsToContents()
    for index in range(len(columns)):
        widget.setColumnWidth(index, min(310, max(110, widget.columnWidth(index))))
    widget.horizontalHeader().setStretchLastSection(True)

CONFIG_FIELDS = [
    ("include_zero_counts", "Include zero-count approved roles",
     "Show all approved roles in each market with at least one eligible mapping."),
    ("exclude_invalid_emails", "Exclude invalid email formats",
     "Flag invalid addresses and exclude them from the final mapping."),
    ("login_day_first", "Day-first login dates",
     "Treat 03/04/2026 as 3 April. ISO dates retain their original meaning."),
    ("include_full_audit_emails", "Full emails in the excluded-record audit",
     "Off by default. Unique Mapping always contains full account emails."),
]

class ConfigPanel(QWidget):
    def __init__(self, config):
        super().__init__()
        self.controls = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for key, title, description in CONFIG_FIELDS:
            check = QCheckBox(title)
            check.setChecked(config[key])
            check.setAccessibleName(title)
            layout.addWidget(check)
            layout.addWidget(label(description, "muted"))
            layout.addSpacing(5)
            self.controls[key] = check

    def config(self):
        return {key: check.isChecked() for key, check in self.controls.items()}

    def set_config(self, config):
        for key, check in self.controls.items():
            check.setChecked(config[key])

class InputCard(QFrame):
    changed = Signal()

    def __init__(self, owner, definition):
        super().__init__()
        self.owner, self.definition = owner, definition
        self.workspace = owner.workspace
        self.record = None
        self.preview_data = None
        self.pending_template = None
        self.generation = 0
        self.busy = False
        self.setObjectName("panel")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(label(definition["label"], "subheading"))
        self.file_label = label("Choose or drop an Excel workbook here.", "muted")
        layout.addWidget(self.file_label)
        self.browse = button("Open workbook…", self.browse_file)
        layout.addWidget(self.browse)
        self.previous = QComboBox()
        self.previous.setAccessibleName(definition["label"] + " previous file")
        self.previous.activated.connect(self.use_previous)
        layout.addWidget(self.previous)
        row = QHBoxLayout()
        self.sheet = QComboBox()
        self.sheet.setAccessibleName(definition["label"] + " worksheet")
        self.sheet.activated.connect(lambda: self.refresh_preview())
        row.addWidget(self.sheet, 1)
        self.header = QSpinBox()
        self.header.setRange(1, 100)
        self.header.setPrefix("Header row ")
        self.header.setAccessibleName(definition["label"] + " header row")
        row.addWidget(self.header)
        self.apply = button("Apply", lambda: self.refresh_preview(self.header.value()), True)
        row.addWidget(self.apply)
        layout.addLayout(row)
        self.status = label("XLSX or XLS • Up to 30 MB per workbook", "muted")
        layout.addWidget(self.status)
        self.fields = {}
        form = QFormLayout()
        form.setSpacing(10)
        for field in definition["columns"]:
            combo = QComboBox()
            combo.setAccessibleName(definition["label"] + " " + field["label"])
            combo.currentIndexChanged.connect(self.changed.emit)
            form.addRow(field["label"], combo)
            self.fields[field["key"]] = combo
        layout.addLayout(form)
        layout.addWidget(label("Source preview · first 20 rows", "muted"))
        self.preview_table = table()
        self.preview_table.setMaximumHeight(220)
        layout.addWidget(self.preview_table)
        self.refresh_uploads()

    def refresh_uploads(self):
        current = self.record["id"] if self.record else None
        self.previous.blockSignals(True)
        self.previous.clear()
        self.previous.addItem("Choose a previously imported workbook", None)
        for record in self.workspace.store.list("uploads"):
            self.previous.addItem(record["name"] + " · " + record["id"][:6], record["id"])
        self.previous.setCurrentIndex(max(0, self.previous.findData(current)))
        self.previous.blockSignals(False)

    def set_busy(self, busy):
        self.busy = busy
        for control in [self.browse, self.previous, self.sheet, self.header, self.apply, *self.fields.values()]:
            control.setEnabled(not busy)
        if busy:
            self.status.setText("Reading workbook…")
        self.changed.emit()

    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Excel workbook", "", "Excel workbooks (*.xlsx *.xls)")
        if filename:
            self.import_path(filename)

    def import_path(self, filename):
        if self.busy:
            return
        self.generation += 1
        generation = self.generation
        self.set_busy(True)
        self.owner.run_task(lambda: self.workspace.import_file(filename),
                            lambda record: self.accept_record(record, generation),
                            lambda error: self.fail(error, generation))

    def use_previous(self):
        key = self.previous.currentData()
        if key:
            self.accept_record(self.workspace.store.get("uploads", key), self.generation)

    def accept_record(self, record, generation):
        if generation != self.generation:
            return
        self.record = record
        self.file_label.setText(record["name"] + f' · {record["size"] / 1024:,.1f} KB')
        self.sheet.blockSignals(True)
        self.sheet.clear()
        self.sheet.addItems(record["sheets"])
        template = self.pending_template
        if template and template["sheet"] in record["sheets"]:
            self.sheet.setCurrentText(template["sheet"])
        self.sheet.blockSignals(False)
        self.refresh_uploads()
        self.refresh_preview(template["header_row"] if template else None,
                             template["mapping"] if template else None)
        self.owner.refresh_dashboard()

    def refresh_preview(self, header_row=None, mapping=None):
        if not self.record:
            return
        self.generation += 1
        generation = self.generation
        preserved = mapping if mapping is not None else self.mapping()
        key, sheet = self.record["id"], self.sheet.currentText()
        self.preview_data = None
        self.set_busy(True)
        self.owner.run_task(
            lambda: self.workspace.preview(key, sheet, self.definition["id"], header_row),
            lambda result: self.accept_preview(result, preserved, generation),
            lambda error: self.fail(error, generation))

    def accept_preview(self, result, preserved, generation):
        if generation != self.generation:
            return
        self.preview_data = result
        self.header.setValue(result["header_row"])
        from app.services.normalization import normalized
        for definition in self.definition["columns"]:
            combo = self.fields[definition["key"]]
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Select source column", "")
            blocked = {normalized(v) for v in definition.get("forbidden_aliases", [])}
            for column in result["columns"]:
                combo.addItem(column, column)
                if normalized(column) in blocked:
                    combo.model().item(combo.count() - 1).setEnabled(False)
            selected = preserved.get(definition["key"]) or result["suggested_mapping"].get(definition["key"])
            if selected and normalized(selected) not in blocked:
                combo.setCurrentIndex(max(0, combo.findData(selected)))
            combo.blockSignals(False)
        fill_table(self.preview_table, ["Excel row"] + result["columns"],
                   [[r["source_row"]] + r["values"] for r in result["rows"]])
        self.status.setText(f'{result["row_count"]:,} data rows · {result["column_count"]} columns · header row {result["header_row"]}')
        self.pending_template = None
        self.set_busy(False)
        self.changed.emit()

    def fail(self, error, generation):
        if generation != self.generation:
            return
        self.preview_data = None
        self.set_busy(False)
        self.status.setText(error)
        self.owner.message(error, True)

    def mapping(self):
        return {key: combo.currentData() or "" for key, combo in self.fields.items()}

    def ready(self):
        values = list(self.mapping().values())
        return bool(self.record and self.preview_data and not self.busy and all(values)
                    and len(values) == len(set(values))
                    and all(v in self.preview_data["columns"] for v in values))

    def selection(self):
        return {"upload_id": self.record["id"] if self.record else "",
                "sheet": self.sheet.currentText(), "header_row": self.header.value(), "mapping": self.mapping()}

    def apply_template(self, template):
        self.pending_template = template
        if self.record:
            if template["sheet"] in self.record["sheets"]:
                self.sheet.setCurrentText(template["sheet"])
            self.refresh_preview(template["header_row"], template["mapping"])

    def reset(self):
        self.generation += 1
        self.record = self.preview_data = self.pending_template = None
        self.file_label.setText("Choose or drop an Excel workbook here.")
        self.sheet.clear()
        for combo in self.fields.values():
            combo.clear()
        fill_table(self.preview_table, [], [])
        self.set_busy(False)
        self.status.setText("XLSX or XLS • Up to 30 MB per workbook")
        self.refresh_uploads()

    def dragEnterEvent(self, event):
        if not self.busy and event.mimeData().hasUrls() and event.mimeData().urls()[0].isLocalFile():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.busy and event.mimeData().hasUrls():
            self.import_path(event.mimeData().urls()[0].toLocalFile())
            event.acceptProposedAction()
