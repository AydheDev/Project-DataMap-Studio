"""Exercise the actual native window and processing engine without a desktop takeover."""
import json
import socket
import time
from pathlib import Path

def verify(app, window, resources, output):
    def wait_for(predicate, timeout=60):
        start = time.monotonic()
        while not predicate():
            app.processEvents()
            if time.monotonic() - start > timeout:
                raise AssertionError("Native workflow timed out: " + window.message_label.text())
            time.sleep(.02)
        app.processEvents()

    assert window.stack.count() == 8
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.socket(family)
        except PermissionError:
            pass
        else:
            raise AssertionError("IP sockets must be disabled in the native app.")
    window.navigate(1)
    window.cards["source"].import_path(resources / "examples" / "sample-source.xlsx")
    window.cards["roles"].import_path(resources / "examples" / "sample-approved-roles.xlsx")
    wait_for(lambda: all(card.ready() for card in window.cards.values()))
    assert window.cards["source"].header.value() == 2
    assert window.cards["source"].mapping()["login"] == "Salesforce Last login"
    window.navigate(2)
    window.template_name.setText("Native verified template")
    window.save_template()
    assert window.workspace.store.list("templates")
    window.process()
    assert window.active_job
    wait_for(lambda: window.active_job is None)
    jobs = window.workspace.store.list("jobs")
    job = jobs[0]
    assert job["status"] == "succeeded", job.get("error")
    assert job["metrics"]["unique_mappings"] == 4
    assert job["metrics"]["duplicates_removed"] == 1
    wait_for(lambda: window.reports.loaded_id == job["id"])
    window.reports.sheet.setCurrentText("Role Counts")
    window.reports.change_table()
    window.reports.market.setCurrentText("UK")
    window.reports.role.setCurrentText("Agent")
    window.reports.reset_filter()
    columns, rows = window.reports.filtered_rows()
    assert rows == [["UK", "Agent", 2]]
    destination = window.workspace.save_report(job["id"], output / "verified-report.xlsx")
    assert destination.is_file()
    payload = window.workspace.result(job["id"])
    assert len(payload["tables"]) == 7
    excluded = payload["tables"]["Excluded Records"]
    assert "other@example.com" not in str(excluded)
    assert "[redacted]" in str(excluded)
    window.settings_panel.controls["include_zero_counts"].setChecked(False)
    window.save_settings()
    assert window.workspace.settings()["include_zero_counts"] is False
    window.settings_panel.controls["include_zero_counts"].setChecked(True)
    window.save_settings()
    wait_for(lambda: not window.tasks)
    for index in range(8):
        window.navigate(index)
        app.processEvents()
    window.navigate(4)
    app.processEvents()
    window.grab().save(str(output / "native-window.png"))
    result = {"status": "passed", "pages": 8, "unique_mappings": 4,
              "duplicates_removed": 1, "report_sheets": 7,
              "network_sockets": "blocked", "browser": False, "server": False}
    (output / "self-test.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    wait_for(lambda: not window.tasks)
    window.close()
    app.processEvents()
