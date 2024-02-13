import traceback, sys

from PyQt5.QtCore import *


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signal = WorkerSignal()

        self.kwargs['progress_callback'] = self.signal.progress

    def run(self):
        try:
            self.res = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signal.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signal.result.emit(self.res)
        finally:
            self.signal.finished.emit()


class WorkerSignal(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(object)
    error = pyqtSignal(tuple)
    progress = pyqtSignal(object)
