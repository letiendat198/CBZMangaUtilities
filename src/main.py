import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from Popups import *


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Manga Helper")
        self.resize(1300, 800)

        self.menu_bar = MenuBar()
        self.setMenuBar(self.menu_bar)

        main_layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        workspace = Workspace()
        preview = Preview()

        sub_layout.addWidget(workspace, 60)
        sub_layout.addWidget(preview, 40)

        main_layout.addLayout(sub_layout)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

class Workspace(QScrollArea):
    def __init__(self):
        super(Workspace, self).__init__()

        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignTop)

        self.view = QGridLayout()
        self.default_label = QLabel("Nothing yet")
        self.l1 = QLabel("Grid Structure")

        self.view.addWidget(self.default_label, 0, 0)
        self.view.addWidget(self.l1, 0, 1)
        self.view.setRowStretch(self.view.count(), 1)
        # self.view.setColumnStretch(self.view.count(), 1)

        self.widget = QWidget()
        self.widget.setLayout(self.view)
        self.setWidget(self.widget)


class Preview(QLabel):
    def __init__(self):
        super(Preview, self).__init__()


class MenuBar(QMenuBar):
    def __init__(self):
        super(MenuBar, self).__init__()

        file_menu = QMenu("&File", self)
        self.import_action = QAction("Import...", file_menu)
        file_menu.addAction(self.import_action)

        self.addMenu(file_menu)

        self.import_action.triggered.connect(self.on_import_action)

    def on_import_action(self):
        self.file_chooser = GenericFileChooser("Choose a file", "Archive file (*.cbz *.zip)", Analyzer, threadpool)


if __name__ == "__main__":
    threadpool = QThreadPool()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
