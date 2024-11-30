from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QCheckBox, QRadioButton, QPushButton, QHBoxLayout,
    QGroupBox
)

class SearchDialog(QDialog):
    def __init__(self, parent=None, wrap_around=False, use_regex=False):
        super().__init__(parent)
        self.setWindowTitle("Find")
        self.resize(400, 200)

        self.setWindowModality(Qt.WindowModality.NonModal)

        layout = QVBoxLayout(self)

        self.search_label = QLabel("Find what:")
        self.search_input = QLineEdit(self)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_input)

        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.match_case = QCheckBox("Match case", self)
        self.wrap_around = QCheckBox("Wrap around", self)
        self.use_regex = QCheckBox("Regular expression", self)

        options_layout.addWidget(self.match_case)
        options_layout.addWidget(self.wrap_around)
        options_layout.addWidget(self.use_regex)

        self.wrap_around.setChecked(wrap_around)
        self.use_regex.setChecked(use_regex)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        direction_group = QGroupBox("Direction")
        direction_layout = QHBoxLayout()

        self.up_direction = QRadioButton("Up", self)
        self.down_direction = QRadioButton("Down", self)
        self.down_direction.setChecked(True)

        direction_layout.addWidget(self.up_direction)
        direction_layout.addWidget(self.down_direction)
        direction_group.setLayout(direction_layout)
        layout.addWidget(direction_group)

        button_layout = QHBoxLayout()
        self.find_next_button = QPushButton("Find Next", self)
        self.close_button = QPushButton("Close", self)
        button_layout.addWidget(self.find_next_button)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        self.find_next_button.clicked.connect(self.on_find_next)
        self.close_button.clicked.connect(self.reject)

    def on_find_next(self):
        self.find_next_button.setEnabled(False)
        self.parent().find_text_in_editor(self.parent().tabs.currentWidget(), self.get_search_options())
        self.find_next_button.setEnabled(True)

    def get_search_options(self):
        return {
            "text": self.search_input.text(),
            "match_case": self.match_case.isChecked(),
            "wrap_around": self.wrap_around.isChecked(),
            "use_regex": self.use_regex.isChecked(),
            "direction": "up" if self.up_direction.isChecked() else "down",
        }
