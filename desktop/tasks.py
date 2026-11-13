from PySide6.QtCore import QObject, QRunnable, Signal, Slot

class Signals(QObject):
    done = Signal(object)
    failed = Signal(str)
    finished = Signal()

class Task(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = Signals()

    @Slot()
    def run(self):
        try:
            self.signals.done.emit(self.function())
        except (ValueError, LookupError, OSError) as error:
            self.signals.failed.emit(str(error))
        except Exception:
            self.signals.failed.emit("The operation failed. Check the workbook and try again.")
        finally:
            self.signals.finished.emit()
