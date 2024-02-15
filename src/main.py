import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from typing import Optional

from Popups import *
from DataManager import *

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("CBZ Manga Utilities")
        self.resize(1500, 800)

        self.menu_bar = MenuBar()
        self.setMenuBar(self.menu_bar)

        main_layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        preview = Preview()
        workspace = Workspace(preview)

        sub_layout.addWidget(workspace, 60)
        sub_layout.addLayout(preview, 40)

        main_layout.addLayout(sub_layout)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)


class Workspace(QScrollArea):
    def __init__(self, preview_obj):
        super(Workspace, self).__init__()

        self.preview = preview_obj

        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignTop)

        self.group_view = QGridLayout()
        self.default_label = QLabel("Nothing yet")

        self.group_view.addWidget(self.default_label, 0, 0)
        self.group_view.setRowStretch(self.group_view.count(), 1)
        # self.view.setColumnStretch(self.view.count(), 1)

        self.widget = QWidget()
        self.widget.setLayout(self.group_view)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.widget)
        self.stacked_widget.setCurrentIndex(0)
        self.setWidget(self.stacked_widget)
        self.populate_groups()

        self.loaded_group = []

    def populate_groups(self):
        self.default_label.hide()

        groups = ["UC", "RC", "UBW", "RBW"]
        group_full_name = {
            "UC": "Unique Colored",
            "RC": "Repeating Colored",
            "UBW": "Unique B&W",
            "RBW": "Repeating B&W"
        }

        for idx, group in enumerate(groups):
            cell_layout = QVBoxLayout()
            front_image = StackedImagesFront()
            front_image.populate_by_group(group)
            front_image.signal.double_clicked.connect(self.switch_list_view)
            title = QLabel(group_full_name[group])
            combo_box = QComboBox()
            combo_box.addItem(QIcon("resources/delete.png"), "Exclude")
            combo_box.addItem(QIcon("resources/minus.png"), "Include first occurrence")
            combo_box.addItem(QIcon("resources/check.png"), "Include")

            cell_layout.addLayout(front_image)
            cell_layout.addStretch()
            cell_layout.addWidget(title)
            cell_layout.addWidget(combo_box)

            self.group_view.addLayout(cell_layout, 0, idx)

    def switch_list_view(self, group):
        print(group)
        if group in self.loaded_group:  # If group already loaded -> Load from stack widget instead
            self.stacked_widget.setCurrentIndex(self.loaded_group.index(group) + 1)
            return

        warning = GenericTextPopup("Warning", "Loading a lot of pictures, GUI may freeze!")
        warning.show()
        # Popup not initiated properly due to non-blocking nature of Qt, need to wait and process events
        QCoreApplication.instance().processEvents()

        self.list_view = QGridLayout()
        self.list_view.setAlignment(Qt.AlignTop)

        data_manager = DataManager()
        file_data = data_manager.get_dict(0)
        hash_data = data_manager.get_dict(1)
        group_data = data_manager.get_dict(2)

        return_layout = QHBoxLayout()
        return_button = QPushButton("Return")
        return_button.clicked.connect(self.on_return_clicked)
        return_layout.addStretch()
        return_layout.addWidget(return_button)
        return_layout.addStretch()
        self.list_view.addLayout(return_layout, 0, 0)

        current_row = 0
        current_column = 1
        if group in group_data:
            for h in group_data[group]:
                file_name = hash_data[h][0]
                file_path = file_data[file_name]["path"]

                cell_layout = QVBoxLayout()

                image = ImageLabel()
                image.set_image_from_file(file_path)
                image.signal.clicked.connect(self.on_image_clicked)

                image_title = QLabel(file_name)

                cell_layout.addWidget(image)
                cell_layout.addWidget(image_title)

                self.list_view.addLayout(cell_layout, current_row, current_column)
                current_column += 1
                if current_column == 4:
                    current_row += 1
                    current_column = 0

        self.list_widget = QWidget()
        self.list_widget.setLayout(self.list_view)
        self.stacked_widget.addWidget(self.list_widget)

        self.loaded_group.append(group)  # Record loaded group
        # Add to stack widget for easy navigation and later use by using current index in loaded_group
        self.stacked_widget.setCurrentIndex(len(self.loaded_group))

    def on_image_clicked(self, path):
        self.preview.set_image(path)

    def on_return_clicked(self):
        print("Returning")
        self.stacked_widget.setCurrentIndex(0)


class Preview(QVBoxLayout):
    def __init__(self):
        super(Preview, self).__init__()
        self.setAlignment(Qt.AlignCenter)
        self.image = ImageLabel()
        self.addWidget(self.image)

    def set_image(self, path):
        self.image.set_image_from_file(path)
        self.image.set_scale(600, 800, Qt.KeepAspectRatio)


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


class StackedImagesFront(QGridLayout):
    def __init__(self):
        super(StackedImagesFront, self).__init__()

        self.group = None
        self.image_1 = ImageLabel()
        self.image_2 = ImageLabel()
        self.image_3 = ImageLabel()
        self.image_list = [self.image_1, self.image_2, self.image_3]

        # self.image_2.setStyleSheet('padding-top: 30px; padding-left: 30xp')
        # self.image_3.setStyleSheet('padding-top: 50px; padding-left: 50xp')
        for image in self.image_list:
            image.signal.double_clicked.connect(self.on_click)

        self.addWidget(self.image_3, 0, 0)
        self.addWidget(self.image_2, 0, 0)
        self.addWidget(self.image_1, 0, 0)

        self.signal = LabelSignal()

    def populate_by_group(self, group):
        self.group = group
        data_manager = DataManager()
        file_data = data_manager.get_dict(0)
        hash_data = data_manager.get_dict(1)
        group_data = data_manager.get_dict(2)
        if group in group_data:
            print(group)
            hash_list = group_data[group]
            samples = hash_list[:3]
            for idx, sample in enumerate(samples):
                first_file_of_hash = hash_data[sample][0]
                path_of_file = file_data[first_file_of_hash]["path"]
                self.image_list[idx].set_image_from_file(path_of_file)

    def on_click(self):
        self.signal.double_clicked.emit(self.group)


class ImageLabel(QLabel):
    def __init__(self):
        super(ImageLabel, self).__init__()
        self.pixmap = QPixmap()
        self.signal = LabelSignal()
        self.path = None

    def mouseDoubleClickEvent(self, ev, QMouseEvent=None):
        self.signal.double_clicked.emit(self.path)

    def mousePressEvent(self, ev: Optional[QMouseEvent]) -> None:
        self.signal.clicked.emit(self.path)
        self.setStyleSheet("background-color : blue;")

    def set_image_from_file(self, path):
        self.path = path
        self.pixmap.load(path)
        # Do not rescale a scaled pixmap. BLURRY! Reserve original pixmap for later scaling and set scaled pixmap
        self.scaled_pixmap = self.pixmap.scaled(200, 200, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.scaled_pixmap)

    def set_scale(self, width, height, aspect_option):
        self.scaled_pixmap = self.pixmap.scaled(width, height, aspect_option, transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.scaled_pixmap)


class LabelSignal(QObject):
    clicked = pyqtSignal(object)
    double_clicked = pyqtSignal(object)


if __name__ == "__main__":
    threadpool = QThreadPool()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
