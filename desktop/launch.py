"""Native executable entry point. No browser, web server or socket transport."""
import argparse
import json
import os
from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_ROOT))
sys.path.insert(0, str(SOURCE_ROOT / "backend"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage", help="Optional local data directory")
    parser.add_argument("--self-test", metavar="DIRECTORY", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_test:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from desktop.network import install_no_network_policy
    install_no_network_policy()
    from PySide6.QtCore import QLockFile
    from PySide6.QtWidgets import QApplication, QMessageBox
    from desktop.workspace import Workspace, default_storage, local_path
    from desktop.window import MainWindow
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("DataMap Studio")
    app.setOrganizationName("AydheDev")
    app.setStyle("Fusion")
    resources = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
    root = local_path(args.storage) if args.storage else default_storage()
    if args.self_test:
        root = local_path(args.self_test) / "workspace"
    root.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(root / "desktop.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        if args.self_test:
            raise RuntimeError("The test workspace is already open.")
        QMessageBox.information(None, "DataMap Studio", "This data folder is already open in another DataMap Studio window.")
        return 2
    workspace = Workspace(root)
    window = MainWindow(workspace, resources)
    window.show()
    try:
        if args.self_test:
            from desktop.self_test import verify
            verify(app, window, resources, local_path(args.self_test))
            return 0
        return app.exec()
    finally:
        workspace.close()
        lock.unlock()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    try:
        raise SystemExit(main())
    except Exception:
        import traceback
        if "--self-test" in sys.argv:
            output = Path(sys.argv[sys.argv.index("--self-test") + 1])
            output.mkdir(parents=True, exist_ok=True)
            (output / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        else:
            from PySide6.QtWidgets import QApplication, QMessageBox
            application = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "DataMap Studio", "The application could not start. Check that its local data folder is writable.")
        raise SystemExit(1)
