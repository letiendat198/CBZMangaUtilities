import re

from PyQt5.QtCore import *

from ThreadWorker import Worker, WorkerSignal
from MangaUtilities import *


class AnalyzeTask:
    def __init__(self, path, threadpool):
        self.signal = WorkerSignal()
        self.path = path  # Zip file path
        self.threadpool = threadpool
        self.utilities = MangaUtilities()

    def unpack_task(self):
        self.worker = Worker(self.utilities.unpack, self.path, os.getcwd())
        self.worker.signal.error.connect(self.signal.error.emit)
        self.worker.signal.result.connect(self.on_unpack_result)  # Receive result signal from self.worker

        self.threadpool.start(self.worker)

    def grayscale_check_task(self):
        # TODO: Make a new thread to distribute load instead of scanning all files in one thread
        self.iter_task = IterateTask()
        self.worker = Worker(self.iter_task.iterating_to_worker_task, self.utilities.target_files, self.utilities.check_grayscale, "Quarter")
        self.iter_task.signal.error.connect(self.signal.error.emit)
        self.iter_task.signal.result.connect(self.on_grayscale_result)  # Receive result signal from self.worker

        self.threadpool.start(self.worker)

    def on_unpack_result(self, res):  # Re-emit as progress signal to update GUI in format (update_code, content)
        work_files = res[1]
        self.signal.progress.emit((1, len(work_files)))

    def on_grayscale_result(self, res):
        # file = res[0]
        # status = res[1]
        # image_count = re.findall(r'\d+', os.path.basename(file))
        # print("Emitting", int(image_count[0]))
        # No need for hacky progress tracking with file name
        self.signal.progress.emit((2, 1))


class IterateTask:
    def __init__(self):
        self.signal = WorkerSignal()
        self.threadpool = QThreadPool()  # Need a separate threadpool to correctly wait for sub-thread

    def iterating_to_worker_task(self, iterable, fn, *args, **kwargs):
        count = 0
        for item in iterable:  # for loop will block event processing (emitting)
            QCoreApplication.instance().processEvents()  # Need this to allow event processing
            print("Adding worker for item", item)
            self.worker = Worker(fn, item, *args, **kwargs)
            self.worker.signal.error.connect(self.signal.error.emit)
            self.worker.signal.result.connect(self.signal.result.emit)
            self.worker.signal.finished.connect(self.signal.finished.emit)
            self.worker.signal.progress.connect(self.signal.progress.emit)

            self.threadpool.start(self.worker)
            count += 1
            if count == self.threadpool.maxThreadCount():
                # Waiting for a batch of 12 jobs (or whatever maxThreadCount is) to finish before queue up new jobs
                self.threadpool.waitForDone()
                QCoreApplication.instance().processEvents()  # Process signal for the last 12 jobs
                count = 0
        self.threadpool.waitForDone()  # Catch the last batch of jobs and disallow the function to return
        QCoreApplication.instance().processEvents()  # Process final batch of events

