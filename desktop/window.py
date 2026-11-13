from pathlib import Path
from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QScrollArea, QComboBox, QLineEdit, QMessageBox, QButtonGroup, QTextEdit, QDialog,
)
from .tasks import Task
from .widgets import label, button, panel, heading, table, fill_table, ConfigPanel, InputCard
from .reports import ReportView
from .style import STYLE

PAGES = ["Dashboard", "Data Import", "Account Role Mapping", "Data Quality",
         "Reports", "Processing History", "Module Management", "Settings"]

class MainWindow(QMainWindow):
    def __init__(self, workspace, resources):
        super().__init__()
        self.workspace, self.resources = workspace, Path(resources)
        self.tasks = {}
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(2)
        self.active_job = None
        self.closing = False
        self.setWindowTitle("DataMap Studio")
        self.resize(1240, 850)
        self.setMinimumSize(980, 650)
        self.setStyleSheet(STYLE)
        root = QWidget()
        root.setObjectName("workspace")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(20, 30, 20, 22)
        nav.setSpacing(8)
        nav.addWidget(label("DataMap", "brand"))
        nav.addWidget(label("S T U D I O", "sidebarHint"))
        nav.addSpacing(28)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        for index, title in enumerate(PAGES):
            control = button(title, lambda checked=False, i=index: self.navigate(i))
            control.setObjectName("nav")
            control.setCheckable(True)
            self.nav_group.addButton(control)
            nav.addWidget(control)
            self.nav_buttons.append(control)
        nav.addStretch()
        nav.addWidget(label("Standalone desktop\nNo browser. No server. No network.", "sidebarHint"))
        nav.addSpacing(15)
        nav.addWidget(button("User guide", self.show_guide, True))
        layout.addWidget(sidebar)
        body = QWidget()
        content = QVBoxLayout(body)
        content.setContentsMargins(28, 25, 28, 20)
        content.setSpacing(16)
        self.message_label = label("All files and processing stay on this computer.", "status")
        content.addWidget(self.message_label)
        self.stack = QStackedWidget()
        content.addWidget(self.stack, 1)
        layout.addWidget(body, 1)
        self.cards = {}
        self.make_dashboard()
        self.make_import()
        self.make_mapping()
        self.quality = ReportView(self, quality=True)
        self.add_page("Data quality", "Inspect exclusions, unmatched roles and duplicates.", self.quality, scroll=False)
        self.reports = ReportView(self)
        self.add_page("Reports", "Search, filter and save the complete seven-sheet Excel workbook.", self.reports, scroll=False)
        self.make_history()
        self.make_modules()
        self.make_settings()
        self.refresh_dashboard()
        self.refresh_history()
        self.refresh_templates()
        self.navigate(0)
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.poll_job)
        self.timer.start()
        self.statusBar().showMessage("Desktop 1.1.0 · Local data: " + str(workspace.root))

    def add_page(self, title, description, widget, scroll=True):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.addWidget(heading(title, description))
        if scroll:
            area = QScrollArea()
            area.setWidgetResizable(True)
            area.setWidget(widget)
            layout.addWidget(area, 1)
        else:
            layout.addWidget(widget, 1)
        self.stack.addWidget(page)

    def navigate(self, index):
        self.stack.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)
        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            for card in self.cards.values():
                card.refresh_uploads()
        elif index == 2:
            self.update_ready()
        elif index == 3:
            self.quality.refresh()
        elif index == 4:
            self.reports.refresh()
        elif index == 5:
            self.refresh_history()

    def message(self, value, error=False):
        self.message_label.setText(value)
        self.message_label.setStyleSheet("background:#fff0e8;color:#9a4e32;padding:12px;" if error else "")

    def run_task(self, function, callback, failed=None):
        task = Task(function)
        key = id(task)
        self.tasks[key] = task
        task.signals.done.connect(callback, Qt.ConnectionType.QueuedConnection)
        task.signals.failed.connect(failed or (lambda value: self.message(value, True)),
                                    Qt.ConnectionType.QueuedConnection)
        task.signals.finished.connect(lambda: self.tasks.pop(key, None), Qt.ConnectionType.QueuedConnection)
        self.pool.start(task)

    def make_dashboard(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 8, 8)
        card, body = panel()
        body.addWidget(label("From workbooks to a clearer picture.", "heading"))
        body.addWidget(label("Map approved roles, count unique accounts, and inspect every exclusion."))
        body.addWidget(button("Start a new workflow", self.new_workflow))
        layout.addWidget(card)
        self.dashboard_summary = label("", "status")
        layout.addWidget(self.dashboard_summary)
        card, body = panel()
        body.addWidget(label("Latest run", "subheading"))
        self.dashboard_latest = label("No completed runs yet.", "muted")
        body.addWidget(self.dashboard_latest)
        body.addWidget(button("View reports", lambda: self.navigate(4), True))
        layout.addWidget(card)
        layout.addStretch()
        self.add_page("Workspace overview", "A standalone tool for reliable Excel reporting.", widget)

    def refresh_dashboard(self):
        jobs = self.workspace.store.list("jobs")
        completed = [j for j in jobs if j["status"] == "succeeded"]
        files = self.workspace.store.list("uploads")
        self.dashboard_summary.setText(
            f"{len(files):,} imported workbooks    ·    {len(completed):,} completed runs    ·    1 active feature module")
        if completed:
            job = completed[0]
            metric = job["metrics"]
            self.dashboard_latest.setText(
                f'Completed {job["finished_at"][:19].replace("T", " ")}\n\n'
                f'{metric["source_rows"]:,} source rows · {metric["eligible_rows"]:,} eligible rows\n'
                f'{metric["unique_mappings"]:,} unique mappings · {metric["duplicates_removed"]:,} duplicates removed')

    def make_import(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 8, 8)
        for definition in self.workspace.module().metadata["inputs"]:
            card = InputCard(self, definition)
            card.changed.connect(self.update_ready)
            self.cards[definition["id"]] = card
            layout.addWidget(card)
        self.review_button = button("Review rules and process", lambda: self.navigate(2))
        layout.addWidget(self.review_button)
        layout.addStretch()
        self.add_page("Data import", "Open or drop your two workbooks, then select worksheets and match columns.", widget)

    def make_mapping(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 8, 8)
        self.mapping_summary = label("", "status")
        layout.addWidget(self.mapping_summary)
        row = QHBoxLayout()
        row.addWidget(button("Edit input workbooks", lambda: self.navigate(1), True))
        row.addWidget(button("New workflow", self.new_workflow, True))
        layout.addLayout(row)
        card, body = panel()
        body.addWidget(label("Protected processing rules", "subheading"))
        body.addWidget(label(
            "1. Eligibility uses Salesforce Last login, never Fed ID. Blank values and errors are excluded.\n\n"
            "2. Approved roles match the uploaded role list, ignoring case and repeated whitespace.\n\n"
            "3. Use FDS Email first, then EIP Email when missing. Trim and lowercase the selected email.\n\n"
            "4. Deduplicate Market + Role + Email. Keep different roles and markets for the same account."))
        layout.addWidget(card)
        card, body = panel()
        body.addWidget(label("Options for this run", "subheading"))
        self.config_panel = ConfigPanel(self.workspace.settings())
        body.addWidget(self.config_panel)
        layout.addWidget(card)
        card, body = panel()
        body.addWidget(label("Reusable templates", "subheading"))
        self.templates = QComboBox()
        self.templates.activated.connect(self.apply_template)
        body.addWidget(self.templates)
        row = QHBoxLayout()
        self.template_name = QLineEdit()
        self.template_name.setPlaceholderText("e.g. Monthly market report")
        self.template_name.setMaxLength(80)
        row.addWidget(self.template_name, 1)
        row.addWidget(button("Save template", self.save_template, True))
        body.addLayout(row)
        layout.addWidget(card)
        self.process_button = button("Generate report", self.process)
        layout.addWidget(self.process_button)
        self.add_page("Account role mapping", "Review your inputs and rules before generating the Excel report.", widget)

    def selections(self):
        return {key: card.selection() for key, card in self.cards.items()}

    def update_ready(self):
        ready = bool(self.cards) and all(card.ready() for card in self.cards.values())
        running = self.active_job is not None
        if hasattr(self, "review_button"):
            self.review_button.setEnabled(ready and not running)
        if hasattr(self, "process_button"):
            self.process_button.setEnabled(ready and not running)
            self.mapping_summary.setText("Both workbooks are mapped and ready." if ready else
                                         "Open both workbooks and map all required columns in Data Import.")

    def new_workflow(self):
        if self.active_job:
            self.message("Wait for the current run to finish before starting a new workflow.", True)
            return
        for card in self.cards.values():
            card.reset()
        self.config_panel.set_config(self.workspace.settings())
        self.message("Open your source and approved-role workbooks to begin.")
        self.navigate(1)

    def refresh_templates(self):
        current = self.templates.currentData()
        self.templates.clear()
        self.templates.addItem("Apply a saved template", None)
        for template in self.workspace.store.list("templates"):
            self.templates.addItem(template["name"], template["id"])
        self.templates.setCurrentIndex(max(0, self.templates.findData(current)))

    def save_template(self):
        try:
            self.workspace.save_template(self.template_name.text(), self.selections(), self.config_panel.config())
            self.template_name.clear()
            self.refresh_templates()
            self.message("Template saved for future reporting periods.")
        except (ValueError, LookupError) as error:
            self.message(str(error), True)

    def apply_template(self):
        key = self.templates.currentData()
        if not key:
            return
        template = self.workspace.store.get("templates", key)
        self.config_panel.set_config(template["config"])
        for input_id, settings in template["inputs"].items():
            self.cards[input_id].apply_template(settings)
        self.message("Template applied. Review the worksheet and column mappings.")
        self.navigate(1)

    def process(self):
        try:
            job = self.workspace.submit(self.selections(), self.config_panel.config())
            self.active_job = job["id"]
            self.update_ready()
            self.message("Processing your workbooks… You can browse other pages while the run completes.")
        except (ValueError, LookupError, RuntimeError) as error:
            self.message(str(error), True)

    def poll_job(self):
        if not self.active_job:
            return
        job = self.workspace.store.get("jobs", self.active_job)
        if job["status"] not in {"succeeded", "failed"}:
            return
        self.active_job = None
        self.update_ready()
        self.refresh_dashboard()
        self.refresh_history()
        if job["status"] == "succeeded":
            self.message("Report ready. Save the complete Excel workbook from Reports.")
            self.reports.refresh(job["id"])
            self.quality.refresh(job["id"])
            self.navigate(4)
        else:
            self.message(job.get("error") or "Processing failed.", True)

    def make_history(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button("Refresh history", self.refresh_history, True))
        self.history_table = table()
        self.history_table.cellDoubleClicked.connect(lambda row, col: self.open_history())
        layout.addWidget(self.history_table, 1)
        layout.addWidget(button("Open selected run", self.open_history))
        self.add_page("Processing history", "Completed and failed runs remain available after restarting the app.", widget, False)

    def refresh_history(self):
        if not hasattr(self, "history_table"):
            return
        self.history = self.workspace.store.list("jobs")
        fill_table(self.history_table, ["Run", "Started", "Status", "Unique mappings", "Details"],
                   [[j["id"][:8], j["created_at"][:19].replace("T", " "), j["status"],
                     j["metrics"].get("unique_mappings", "") if j.get("metrics") else "",
                     j.get("error") or ""] for j in self.history])

    def open_history(self):
        index = self.history_table.currentRow()
        if not 0 <= index < len(self.history):
            self.message("Select a processing run first.", True)
            return
        job = self.history[index]
        if job["status"] == "succeeded":
            self.reports.refresh(job["id"])
            self.navigate(4)
        else:
            self.message(job.get("error") or "This run is still processing.", job["status"] == "failed")

    def make_modules(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 8, 8)
        for module in self.workspace.registry.describe():
            card, body = panel()
            body.addWidget(label(module["name"], "subheading"))
            body.addWidget(label(module["description"]))
            body.addWidget(label(f'Version {module["version"]} · ' + ("Active" if module["enabled"] else "Disabled developer example"), "muted"))
            if module["enabled"]:
                body.addWidget(button("Open module", lambda: self.navigate(2)))
            layout.addWidget(card)
        layout.addStretch()
        self.add_page("Module management", "Trusted modules share the same local processing engine.", widget)

    def make_settings(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 8, 8)
        card, body = panel()
        body.addWidget(label("Defaults for new workflows", "subheading"))
        self.settings_panel = ConfigPanel(self.workspace.settings())
        body.addWidget(self.settings_panel)
        body.addWidget(button("Save defaults", self.save_settings))
        layout.addWidget(card)
        card, body = panel()
        body.addWidget(label("Local storage", "subheading"))
        body.addWidget(label(str(self.workspace.root)))
        body.addWidget(label("No browser, server, login, cloud storage, telemetry or automatic updates.\n"
                             "Original imported files are preserved. Close the app before backing up its data folder.", "muted"))
        layout.addWidget(card)
        layout.addStretch()
        self.add_page("Settings", "Preferences and data are saved on this computer.", widget)

    def save_settings(self):
        self.workspace.save_settings(self.settings_panel.config())
        self.message("Defaults saved. They apply when you start a new workflow.")

    def show_guide(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("DataMap Studio — User guide")
        dialog.resize(850, 650)
        layout = QVBoxLayout(dialog)
        view = QTextEdit()
        view.setReadOnly(True)
        guide = self.resources / "desktop" / "USER_GUIDE.md"
        view.setPlainText(guide.read_text(encoding="utf-8") if guide.exists() else
                          "Open both Excel workbooks in Data Import, match columns, then review rules and generate a report.")
        layout.addWidget(view)
        layout.addWidget(button("Close", dialog.accept))
        dialog.exec()

    def closeEvent(self, event: QCloseEvent):
        if self.active_job or self.tasks:
            self.message("Wait for the current file operation or processing run to finish before closing.", True)
            event.ignore()
            return
        self.timer.stop()
        self.pool.waitForDone()
        self.workspace.close()
        event.accept()
