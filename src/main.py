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
        self.resize(1400, 800)

        preview = Preview()
        workspace = Workspace(preview)

        self.menu_bar = MenuBar(workspace)
        self.setMenuBar(self.menu_bar)

        main_layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        sub_layout.addWidget(workspace, 70)
        sub_layout.addLayout(preview, 30)

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
        self.default_label = QLabel("Nothing yet! Import a file to get started")

        self.group_view.addWidget(self.default_label, 0, 0)
        self.group_view.setRowStretch(self.group_view.count(), 1)
        # self.view.setColumnStretch(self.view.count(), 1)

        self.widget = QWidget()
        self.widget.setLayout(self.group_view)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.widget)
        self.stacked_widget.setCurrentIndex(0)
        self.setWidget(self.stacked_widget)
        group_data = DataManager().get_dict(2)

        self.loaded_group = []
        self.combo_box_dict = {}

        if len(group_data) > 0:
            self.populate_groups()

    def populate_groups(self):
        self.default_label.hide()

        groups = ["UC", "RC", "UBW", "RBW"]
        group_full_name = {
            "UC": "Unique Colored",
            "RC": "Repeating Colored",
            "UBW": "Unique B&W",
            "RBW": "Repeating B&W"
        }
        recommended_settings = {
            "UC": 2,
            "RC": 0,
            "UBW": 2,
            "RBW": 1,
        }

        front_image_group = ImageGroup()

        for idx, group in enumerate(groups):
            cell_layout = QVBoxLayout()
            front_image = StackedImagesFront()
            front_image.populate_by_group(group)
            front_image.signal.double_clicked.connect(self.switch_list_view)
            front_image.signal.clicked.connect(front_image_group.on_image_select)
            front_image_group.add(front_image, group)
            title = QLabel(group_full_name[group])
            title.setAlignment(Qt.AlignCenter)
            combo_box = QComboBox()
            combo_box.addItem(QIcon("resources/delete.png"), "Exclude")
            combo_box.addItem(QIcon("resources/minus.png"), "Include first occurrence")
            combo_box.addItem(QIcon("resources/check.png"), "Include")
            combo_box.setCurrentIndex(recommended_settings[group])
            self.combo_box_dict[group] = combo_box  # Save combo box reference for later use

            cell_layout.addWidget(front_image)
            cell_layout.addStretch()
            cell_layout.addWidget(title)
            cell_layout.addWidget(combo_box)

            self.group_view.addLayout(cell_layout, 0, idx)

        self.group_view.addWidget(front_image_group)

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
        self.list_view.setColumnStretch(4, 1)  # Set a stretch at 5th column

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

        image_group = ImageGroup()
        status = self.combo_box_dict[group].currentText()

        current_row = 0
        current_column = 1
        if group in group_data:
            for h in group_data[group]:
                file_name = hash_data[h][0]
                file_path = file_data[file_name]["path"]

                cell_layout = QVBoxLayout()
                cell_layout.setAlignment(Qt.AlignCenter)

                image = ImageLabel()
                image.setAlignment(Qt.AlignCenter)
                image.status = status
                image.set_image_from_file(file_path, h)  # WILL RE-SET STATUS FOR INCLUDED/EXCLUDED IMAGE
                image.signal.clicked.connect(self.on_image_clicked)
                image.signal.clicked.connect(image_group.on_image_select)
                image.clear_highlight()
                image_group.add(image, h)

                image_title = QLabel(file_name)
                image_title.setAlignment(Qt.AlignCenter)

                cell_layout.addWidget(image)
                cell_layout.addWidget(image_title)

                self.list_view.addLayout(cell_layout, current_row, current_column)
                current_column += 1
                if current_column == 4:
                    current_row += 1
                    current_column = 0
        self.list_view.addWidget(image_group)
        self.list_widget = QWidget()
        self.list_widget.setLayout(self.list_view)
        self.stacked_widget.addWidget(self.list_widget)

        self.loaded_group.append(group)  # Record loaded group
        # Add to stack widget for easy navigation and later use by using current index in loaded_group
        self.stacked_widget.setCurrentIndex(len(self.loaded_group))

    def on_image_clicked(self, image_data):
        path = image_data[0]
        self.preview.set_image(path)

    def on_return_clicked(self):
        print("Returning")
        self.stacked_widget.setCurrentIndex(0)


class Preview(QVBoxLayout):
    def __init__(self):
        super(Preview, self).__init__()
        self.setAlignment(Qt.AlignCenter)
        self.image = SimpleImageLabel()
        self.addWidget(self.image)

    def set_image(self, path):
        self.image.set_image_from_file(path)
        self.image.set_scale(480, 600, Qt.KeepAspectRatio)


class MenuBar(QMenuBar):
    def __init__(self, workspace):
        super(MenuBar, self).__init__()

        self.workspace = workspace

        file_menu = QMenu("&File", self)
        self.import_action = QAction("Import...", file_menu)
        file_menu.addAction(self.import_action)
        self.export_action = QAction("Export...", file_menu)
        file_menu.addAction(self.export_action)

        self.addMenu(file_menu)

        self.import_action.triggered.connect(self.on_import_action)
        self.export_action.triggered.connect(self.on_export_action)

    def on_import_action(self):
        self.file_chooser = GenericFileChooser("Choose a file", "Archive file (*.cbz *.zip)", Analyzer, threadpool, self.workspace.populate_groups)

    def on_export_action(self):
        self.export_popup = ExportPopup(threadpool, self.workspace.combo_box_dict)
        self.export_popup.show()


class StackedImagesFront(QWidget):
    def __init__(self):
        super(StackedImagesFront, self).__init__()

        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignCenter)

        self.group = None
        self.image_1 = SimpleImageLabel()
        self.image_2 = SimpleImageLabel()
        self.image_3 = SimpleImageLabel()
        self.image_list = [self.image_1, self.image_2, self.image_3]

        # self.image_2.setStyleSheet('padding-top: 30px; padding-left: 30xp')
        # self.image_3.setStyleSheet('padding-top: 50px; padding-left: 50xp')
        for image in self.image_list:
            image.setAlignment(Qt.AlignCenter)
            image.setMargin(10)
            image.signal.clicked.connect(self.on_click)
            image.signal.double_clicked.connect(self.on_double_click)

        self.layout.addWidget(self.image_3, 0, 0)
        self.layout.addWidget(self.image_2, 0, 0)
        self.layout.addWidget(self.image_1, 0, 0)

        self.setLayout(self.layout)

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

    def on_double_click(self):
        self.signal.double_clicked.emit(self.group)

    def on_click(self):
        self.signal.clicked.emit((0, self.group))

    def set_highlight(self):
        self.setStyleSheet("background-color: lightblue")

    def clear_highlight(self):
        self.setStyleSheet("")


class ImageLabel(QLabel):
    def __init__(self):
        super(ImageLabel, self).__init__()
        self.pixmap = QPixmap()
        self.signal = LabelSignal()
        self.setMargin(10)
        self.path = None
        self.file_hash = None
        self.status = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def set_image_from_file(self, path, file_hash):
        self.file_hash = file_hash
        self.path = path
        self.pixmap.load(path)
        # Do not rescale a scaled pixmap. BLURRY! Reserve original pixmap for later scaling and set scaled pixmap
        self.scaled_pixmap = self.pixmap.scaled(200, 200, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.scaled_pixmap)

        if ExportData().check_include(file_hash):
            self.status = "Include"
        elif ExportData().check_exclude(file_hash):
            self.status = "Exclude"

    def set_scale(self, width, height, aspect_option):
        self.scaled_pixmap = self.pixmap.scaled(width, height, aspect_option, transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.scaled_pixmap)

    def set_highlight(self):
        if self.status == "Include":
            self.setStyleSheet("background-color: limegreen")
        elif self.status == "Exclude":
            self.setStyleSheet("background-color: crimson")
        elif self.status == "Include first occurrence":
            self.setStyleSheet("background-color: yellow")
        else:
            self.setStyleSheet("background-color: lightblue")

    def clear_highlight(self):
        if self.status == "Exclude":
            self.setStyleSheet("background-color: lightpink")
        elif self.status == "Include":
            self.setStyleSheet("background-color: lightgreen")
        elif self.status == "Include first occurrence":
            self.setStyleSheet("background-color: lemonchiffon")
        else:
            self.setStyleSheet("")

    def mouseDoubleClickEvent(self, ev, QMouseEvent=None):
        self.signal.double_clicked.emit(self.path)

    def mousePressEvent(self, ev: Optional[QMouseEvent]) -> None:
        self.signal.clicked.emit((self.path, self.file_hash))

    def open_context_menu(self, pos):
        self.context_menu = QMenu()
        self.include_action = QAction("Include", self.context_menu)
        self.exclude_action = QAction("Exclude", self.context_menu)

        # May cause problem because connect can be called multiple times. Nothing for now
        self.include_action.triggered.connect(self.on_image_context_include)
        self.exclude_action.triggered.connect(self.on_image_context_exclude)

        self.context_menu.addAction(self.include_action)
        self.context_menu.addAction(self.exclude_action)
        self.context_menu.exec(self.mapToGlobal(pos))

    def on_image_context_include(self):
        print("Include", self.path)
        self.status = "Include"
        self.set_highlight()
        ExportData().add_inclusion(self.file_hash)

    def on_image_context_exclude(self):
        print("Exclude", self.path)
        self.status = "Exclude"
        self.set_highlight()
        ExportData().add_exclusion(self.file_hash)


class SimpleImageLabel(QLabel):
    def __init__(self):
        super(SimpleImageLabel, self).__init__()
        self.pixmap = QPixmap()
        self.signal = LabelSignal()
        self.path = None

    def set_image_from_file(self, path):
        self.path = path
        self.pixmap.load(path)
        # Do not rescale a scaled pixmap. BLURRY! Reserve original pixmap for later scaling and set scaled pixmap
        self.scaled_pixmap = self.pixmap.scaled(200, 200, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.scaled_pixmap)

    def set_scale(self, width, height, aspect_option):
        self.scaled_pixmap = self.pixmap.scaled(width, height, aspect_option, transformMode=Qt.SmoothTransformation)
        self.setPixmap(self.scaled_pixmap)

    def mouseDoubleClickEvent(self, ev, QMouseEvent=None):
        self.signal.double_clicked.emit(self.path)

    def mousePressEvent(self, ev: Optional[QMouseEvent]) -> None:
        self.signal.clicked.emit(self.path)


class ImageGroup(QWidget):  # Need to be a QWidget to hook into layout to survive and revive
    def __init__(self):
        super(ImageGroup, self).__init__()

        self.collection = {}
        self.prev = None
        self.current = None

    def add(self, image_obj, file_hash):
        self.collection[file_hash] = image_obj

    def on_image_select(self, img_data):
        path = img_data[0]
        file_hash = img_data[1]
        print(path, file_hash)

        self.prev = self.current
        self.current = self.collection[file_hash]
        print(self.prev, self.current)

        self.current.set_highlight()
        if self.prev is not None and self.prev != self.current:
            self.prev.clear_highlight()


class LabelSignal(QObject):
    clicked = pyqtSignal(object)
    double_clicked = pyqtSignal(object)


if __name__ == "__main__":
    threadpool = QThreadPool()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
