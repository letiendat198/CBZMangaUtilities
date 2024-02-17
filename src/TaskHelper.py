import re

from PyQt5.QtCore import *

from ThreadWorker import Worker, WorkerSignal
from MangaUtilities import *
from DataManager import *

data = DataManager()


class AnalyzeTask:
    def __init__(self, path, threadpool):
        self.signal = WorkerSignal()
        self.path = path  # Zip file path
        self.threadpool = threadpool
        self.utilities = MangaUtilities()

    def unpack_task(self):
        self.worker = Worker(self.utilities.unpack, self.path, os.getcwd())
        self.worker.signal.error.connect(self.signal.error.emit)
        self.worker.signal.result.connect(self.on_unpack_result)

        self.threadpool.start(self.worker)

    def analyze_task(self):
        self.iter_task = IterateTask()
        self.worker = Worker(self.iter_task.spawn_worker_from_iterable, self.utilities.grayscale_and_hash, self.utilities.target_files, "Quarter")
        self.iter_task.signal.error.connect(self.signal.error.emit)
        self.iter_task.signal.result.connect(self.on_analyze_result)
        self.worker.signal.finished.connect(self.on_analyze_finished)

        self.threadpool.start(self.worker)

    def on_unpack_result(self, res):  # Re-emit as progress signal to update GUI in format (update_code, content)
        work_files = res[1]
        self.signal.progress.emit((1, len(work_files)))

    def on_analyze_result(self, res):
        print(res)
        self.signal.progress.emit((2, 1))

    def on_analyze_finished(self):
        self.utilities.file_dict = dict(sorted(self.utilities.file_dict.items()))
        data.overwrite_dict(self.utilities.file_dict, 0)  # 0 for data.json
        data.overwrite_dict(self.utilities.hash_dict, 1)  # 1 for hash.json
        ExportData().reset()

        # TODO: Temporary group dict generation, VERY BLOCKING! Need to move
        group_dict = {
            "UC": [],
            "RC": [],
            "UBW": [],
            "RBW": []
        }
        group_dict_set = {
            "UC": set(),
            "RC": set(),
            "UBW": set(),
            "RBW": set()
        }
        for file in self.utilities.file_dict:
            xhash = self.utilities.file_dict[file]["hash"]
            group = self.utilities.file_dict[file]["group"]
            if xhash not in group_dict_set[group]:
                group_dict_set[group].add(xhash)
                group_dict[group].append(xhash)

        data.overwrite_dict(group_dict, 2)  # 2 for group.json

        self.signal.finished.emit()


class IterateTask:
    def __init__(self):
        self.signal = WorkerSignal()
        self.threadpool = QThreadPool()  # Need a separate threadpool to correctly wait for sub-thread

    def spawn_worker_from_iterable(self, fn, iterable, *args, **kwargs):
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


class ExportTask:
    def __init__(self, threadpool):
        self.threadpool = threadpool
        self.utilities = MangaUtilities()
        self.target_files = set()  # Use set to avoid duplicate when adding included files
        self.include = None
        self.exclude = None
        self.signal = WorkerSignal()

    def _load_target(self, progress_callback=None):
        file_dict = DataManager().get_dict(0)
        hash_dict = DataManager().get_dict(1)
        group_dict = DataManager().get_dict(2)

        export_dict = ExportData().get_dict()

        self.include = set(export_dict["Include"])
        self.exclude = set(export_dict["Exclude"])

        for group in group_dict:
            export_status = export_dict[group]
            hashes = group_dict[group]
            for file_hash in hashes:
                print("Loading hash", file_hash)
                if file_hash in self.exclude:
                    continue
                files_name = hash_dict[file_hash]
                if export_status == "Include":
                    for file in files_name:
                        self.target_files.add(file_dict[file]["path"])
                elif export_status == "Exclude":
                    break
                elif export_status == "Include first occurrence":
                    # Not guaranteed to be first occurrence because of how threading is
                    self.target_files.add(file_dict[files_name[0]]["path"])

        for file_hash in self.include:
            files_name = hash_dict[file_hash]
            for file_name in files_name:
                self.target_files.add(file_dict[file_name]["path"])

    def load_task(self):
        self.worker = Worker(self._load_target)
        self.worker.signal.finished.connect(lambda: self.signal.progress.emit((0, len(self.target_files))))
        self.worker.signal.error.connect(self.signal.error.emit)

        self.threadpool.start(self.worker)
        
    def compress_task(self, quality):
        self.iter_task = IterateTask()
        self.iter_task.signal.finished.connect(self.on_compress_progress)  # Child thread done compress, emit progress
        self.iter_task.signal.error.connect(self.signal.error.emit)
        self.worker = Worker(self.iter_task.spawn_worker_from_iterable, self.utilities.compress_jpeg, self.target_files, quality)
        self.worker.signal.finished.connect(lambda: self.signal.progress.emit((1, len(self.target_files))))

        self.threadpool.start(self.worker)

    def export_task(self, out):
        self.worker = Worker(self.utilities.repack, self.target_files, out)
        self.worker.signal.progress.connect(self.on_export_progress)
        self.worker.signal.finished.connect(self.signal.finished.emit)
        self.worker.signal.error.connect(self.signal.error.emit)

        self.threadpool.start(self.worker)

    def on_compress_progress(self):
        self.signal.progress.emit((1, 1))

    def on_export_progress(self):
        self.signal.progress.emit((2, 1))
