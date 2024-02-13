import sys
import json
import os

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from FileHelper import *
from SettingsManager import *
from TaskHelper import *


class Analyzer(QWidget):
    def __init__(self, path, threadpool):
        super(Analyzer, self).__init__()

        self.setWindowTitle("Analyzing...")
        self.setWindowModality(Qt.ApplicationModal)

        self.view = QVBoxLayout()
        self.view.setAlignment(Qt.AlignCenter)

        # GUI starts here
        self.label = QLabel("Unpacking file: " + str(path) + "...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress = 0

        self.view.addWidget(self.label)
        self.view.addWidget(self.progress_bar)

        self.setLayout(self.view)

        self.task = AnalyzeTask(path, threadpool)
        self.task.signal.progress.connect(self.on_update)
        self.task.signal.error.connect(self.on_error)
        self.task.signal.finished.connect(self.on_finished)
        self.task.unpack_task()

    def on_update(self, prog):
        update_code = prog[0]
        content = prog[1]
        if update_code == 1:  # Update code 1: Unpack finished
            self.progress_bar.setMaximum(content)
            self.progress_bar.setMinimum(1)
            self.label.setText("Analyzing obtained files...")
            self.task.grayscale_check_task()

        if update_code == 2:  # Update code 2: Grayscale scan progress
            # if content > self.progress:
            #     self.progress = content
            self.progress += content
            print("Progress bar value:", self.progress)
            self.progress_bar.setValue(self.progress)

    def on_error(self, err):
        self.error_popup = GenericConfirmPopup("Error", str(err), self.close)
        self.error_popup.show()

    def on_finished(self):
        self.close()


class GenericFileChooser(QWidget):
    def __init__(self, title, file_type, callback, *args, **kwargs):
        super(GenericFileChooser, self).__init__()

        self.callback = callback
        self.args = args
        self.kwargs = kwargs

        path = QFileDialog.getOpenFileName(self, title, filter=file_type)[0]
        if path:
            self.fn = self.callback(path, *self.args, **self.kwargs)
            self.fn.show()
        self.close()


class GenericPathChooser(QWidget):
    def __init__(self, title, label):
        super(GenericPathChooser, self).__init__()

        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)

        self.view = QFormLayout()

        self.but_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.choose_path_but = QPushButton("...")
        self.but_row.addWidget(self.path_edit)
        self.but_row.addWidget(self.choose_path_but)
        self.view.addRow(label, self.but_row)

        self.confirm_but = QPushButton("Confirm")
        self.view.addWidget(self.confirm_but)

        self.setLayout(self.view)

        self.choose_path_but.clicked.connect(self.on_path_click)
        self.confirm_but.clicked.connect(self.on_confirm)

    def update_params(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def on_path_click(self):
        self.path = QFileDialog.getExistingDirectory(self, "Select a folder")
        if self.path:
            self.path_edit.setText(self.path)
            self.path_edit.setCursorPosition(0)

    def on_confirm(self):
        self.kwargs["path"] = self.path_edit.text()
        self.popup = self.fn(*self.args, **self.kwargs)
        self.popup.show()
        self.close()


class GenericConfirmPopup(QWidget):
    def __init__(self, title, label, fn, *args, **kwargs):
        super(GenericConfirmPopup, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)

        self.view = QVBoxLayout()

        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumWidth(300)
        self.label.setWordWrap(True)
        self.view.addWidget(self.label)

        self.button_row = QHBoxLayout()

        self.confirm = QPushButton("OK")
        self.confirm.clicked.connect(self.on_click)
        self.button_row.addStretch()
        self.button_row.addWidget(self.confirm)
        self.button_row.addStretch()

        self.view.addLayout(self.button_row)

        self.setLayout(self.view)

    def on_click(self):
        self.fn(*self.args, **self.kwargs)
        self.close()


class GenericTextPopup(QWidget):
    def __init__(self, title, label):
        super(GenericTextPopup, self).__init__()

        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)

        self.view = QVBoxLayout()
        self.view.setAlignment(Qt.AlignCenter)

        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumWidth(300)
        self.label.setWordWrap(True)
        self.view.addWidget(self.label)

        self.setLayout(self.view)

    def set_text(self, progress):
        self.label.setText(progress)
