import sys
import os
import subprocess
import platform
import shutil
import json
import re
import hashlib 
import time 

from typing import Optional, Dict, Any

try:
    from PyQt6.QtGui import ( 
        QFont, QColor, QTextDocument, QIcon, QAction
    )

    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QFileDialog, QMessageBox, 
        QTabWidget, QInputDialog, QDialog, QMenuBar, QMenu
    )

    from PyQt6.QtCore import QCoreApplication, Qt, QSize, QTimer
except ImportError as e:
    print(f"PyQt6 import failed! {e}")
    raise SystemExit("PyQt6 is required to run Notepad8. Please refer to your distro's manual for instructions.")

try:
    from PyQt6.Qsci import QsciScintilla, QsciLexer
except ImportError as e:
    print(f"Scintilla import failed! {e}")
    raise SystemExit("QsciScintilla is required to run Notepad8. Please refer to your distro's manual for instructions.")

print_support = True
network_support = True 
# used numbers
used_numbers = set()

try:
    from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
except ImportError:
    print_support = False 
    print(f"Failed to import QtPrintSupport. {e}\nPrinting functions will be unavailable.")

try:
    from PyQt6.QtNetwork import QLocalServer, QLocalSocket
except ImportError:
    network_support = False 
    print(f"Failed to import QtNetwork. {e}\nNetworking functions will be unavailable.")

from config import Config, CONFIG_PATH
from plugin_api import PluginAPI
from file_types import get_lexer_for_file, DEFAULT_LANGUAGES
from plugin_manager import PluginManager
from dialogs import SearchDialog

# additional projects go here
from charset_normalizer import from_bytes

class NotepadPy(QMainWindow):
    def __init__(self):
        super().__init__()

        # make backup path
        self.backup_path = os.path.join(os.path.dirname(CONFIG_PATH), "backup")
        os.makedirs(self.backup_path, exist_ok=True)

        self.config = Config(CONFIG_PATH)
        self.file_paths = {}
        self.backup_files = {}
        self.modified_tabs = {}
        self.tab_settings = {}
        self.new_file_counter = 1
        self.last_search_options = None
        self.current_language = "None"

        self.plugin_manager = PluginManager(self)
        self.plugin_api = PluginAPI(self, self.plugin_manager)
        self.plugin_manager.plugin_api = self.plugin_api

        self.init_ui()
        self.plugin_manager.load_plugins()

        self.restore_session()
        self.cleanup_orphaned_backups()
        self.setup_backup_timer()

    def init_ui(self):
        """Initialize the main user interface."""
        self.setWindowTitle("Notepad8")
        self.resize(640, 480)
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(not self.config.get("lockTabs", False))
        self.setAcceptDrops(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_title_on_tab_change)
        self.setCentralWidget(self.tabs)

        # for some reason, native dialogs in KDE do NOT work using pyinstaller. I don't know why yet.
        # For now, I've compromised by disabling native file dialogs by default (can be enabled back in config.json)
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, self.config.get("useQtDialogs", True))

        # create menu bar
        self.create_menu_bar()

        # create toolbar
        self.create_toolbar()

    def create_menu_bar(self):
        """Initialize the menu bar, and populate it with menus/actions."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")
        file_actions = [
            ("New", "Ctrl+N", self.new_file, "icons/new.png"),
            ("Open", "Ctrl+O", self.open_file_dialog, "icons/open.png"),
            ("Save", "Ctrl+S", self.save_current_file, "icons/save.png"),
            ("Save As...", "Ctrl+Shift+S", self.save_current_file_as, "icons/save_as.png"),
            ("Save Copy...", "Ctrl+Shift+F6", self.save_current_file_as_copy, "icons/save_as.png"),
            ("Print", "Ctrl+P", self.print_file, "icons/print.png"),
            ("_Launch", None, None, [
                ("New Window...", "Ctrl+Shift+N", self.launch_new_window, None),
                ("New Terminal...", "Ctrl+Shift+T", self.launch_new_terminal, None),
            ]),
            ("Exit", "Alt+F4", self.close_program, None)
        ]
        self.add_actions_to_menu(file_menu, file_actions)

        # Edit Menu
        edit_menu = menu_bar.addMenu("Edit")
        edit_actions = [
            ("Undo", "Ctrl+Z", self.plugin_api.undo, None),
            ("Redo", "Ctrl+R", self.plugin_api.redo, None),
            ("Cut", "Ctrl+X", self.plugin_api.cut, None),
            ("Copy", "Ctrl+C", self.plugin_api.copy, None),
            ("Paste", "Ctrl+V", self.plugin_api.paste, None),
            ("Delete", "Del", self.plugin_api.delete_selection, None),
            ("Select All", "Del", self.plugin_api.select_all, None),
        ]
        self.add_actions_to_menu(edit_menu, edit_actions)

        # Search Menu
        search_menu = menu_bar.addMenu("Search")
        search_actions = [
            ("Find", "Ctrl+F", self.find_dialog, "icons/search.png"),
            ("Find Next", "F3", self.find_next, None),
            ("Find Previous", "Shift+F3", self.find_previous, None),
            ("Go to Line", "Ctrl+G", self.goto_line, None)
        ]
        self.add_actions_to_menu(search_menu, search_actions)

        # View Menu
        view_menu = menu_bar.addMenu("View")
        self.word_wrap_action = view_menu.addAction("Word Wrap")
        self.word_wrap_action.setCheckable(True)
        self.word_wrap_action.setChecked(self.config.get("wordWrap", False))
        self.word_wrap_action.triggered.connect(self.toggle_word_wrap)

        # Language Menu
        self.create_language_menu(menu_bar.addMenu("Language"))

        self.plugin_api.get_plugins_menu()

        # About Menu
        about_menu = menu_bar.addMenu("?")
        about_action = about_menu.addAction("About")
        about_action.setShortcut("F1")
        about_action.triggered.connect(self.show_about_box)

    # Actions helper
    def add_actions_to_menu(self, menu, actions):
        """Helper to add actions to a menu."""
        for name, shortcut, handler, icon in actions:
            if isinstance(icon, list):
                submenu = menu.addMenu(name.replace("_", ""))
                self.add_actions_to_menu(submenu, icon)
                continue

            if name is None:
                menu.addSeparator()
                continue

            action = menu.addAction(name)
            if shortcut:
                action.setShortcut(shortcut)
            if handler:
                action.triggered.connect(handler)
            if icon and isinstance(icon, str):
                action.setIcon(QIcon(icon))


    # Create language menu
    def create_language_menu(self, language_menu):
        """Initializes the language selection menu."""
        self.language_actions = {}

        none_action = language_menu.addAction("None (Normal Text)")
        none_action.setCheckable(True)
        none_action.triggered.connect(lambda: self.set_language("None"))
        self.language_actions["None"] = none_action
        
        grouped_languages = {}
        for language in sorted(DEFAULT_LANGUAGES.keys()):
            group = language[0].upper()
            grouped_languages.setdefault(group, []).append(language)

        for group, languages in grouped_languages.items():
            submenu = language_menu.addMenu(group)
            for language in languages:
                action = submenu.addAction(language)
                action.setCheckable(True)
                action.triggered.connect(lambda _, lang=language: self.set_language(lang))
                self.language_actions[language] = action

        language_menu.addSeparator()
        import_action = language_menu.addAction("Import Notepad++ Language Style...")
        import_action.triggered.connect(self.import_npp_language)
                
    def create_toolbar(self):
        """Creates the toolbar below the menu."""
        toolbar = self.addToolBar("Main Menu")
        toolbar.setMovable(False) # todo: add an unlocking feature

        toolbar.setIconSize(QSize(16, 16))

        toolbar_actions = [
            ("New", "icons/new.png", self.new_file, "New"),
            ("Open", "icons/open.png", self.open_file_dialog, "Open"),
            ("Save", "icons/save.png", self.save_current_file, "Save"),
            ("Save As", "icons/save_as.png", self.save_current_file_as, "Save As"),
            ("Print", "icons/print.png", self.print_file, "Print"),
        ]

        self.add_actions_to_toolbar(toolbar, toolbar_actions)

    def add_actions_to_toolbar(self, toolbar, actions):
        """Helper to add actions to a toolbar."""
        for name, icon, handler, tooltip in actions:
            action = QAction(QIcon(icon), name, self)
            action.triggered.connect(handler)
            action.setToolTip(tooltip)
            toolbar.addAction(action)

    def save_backup(self, editor):
        """Saves or updates a backup of a modified document."""
        tab_index = self.tabs.indexOf(editor)
        if tab_index == -1:
            return

        tab_title = self.tabs.tabText(tab_index).replace("&", "").lstrip("*")
        content = editor.text()

        original_path = self.get_tab_file_path(editor)
        if original_path:
            backup_base_name = os.path.basename(original_path)
        else:
            backup_base_name = tab_title

        if not backup_base_name.endswith(".bak"):
            backup_base_name += ".bak"

        backup_file = os.path.join(self.backup_path, backup_base_name)

        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        last_hash = getattr(editor, "last_backup_hash", None)
        last_backup_time = getattr(editor, "last_backup_time", 0)

        if content_hash == last_hash and (time.time() - last_backup_time) < 60:
            return

        with open(backup_file, "w", encoding="utf-8") as file:
            file.write(content)

        editor.last_backup_hash = content_hash
        editor.last_backup_time = time.time()
        self.plugin_api.log(f"Backup saved to: {backup_file}")

        if original_path:
            self.plugin_api.log(f"Saving backup for {original_path} as {backup_file}")
            self.backup_files[original_path] = backup_file
        else:
            self.backup_files[tab_title] = backup_file

        if original_path:
            self.config.add_open_file(
                file_path=original_path,
                is_modified=editor.isModified(),
                caret_position=editor.getCursorPosition(),
                lexer=self.get_lexer_for_editor(editor)
            )

        self.config.save()

    def setup_backup_timer(self):
        """Setup a timer to periodically save backups."""
        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self.save_all_backups)
        self.backup_timer.start(60000)
    
    def save_all_backups(self):
        """Save backups for the modified documents"""
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if isinstance(editor, QsciScintilla) and editor.isModified():
                self.save_backup(editor)

    def restore_session(self):
        """Restore open files from the previous session."""
        backup_files = os.listdir(self.backup_path)
        self.plugin_api.log(f"Backup files found in directory: {backup_files}")

        open_files = [
            f for f in self.config.get("open_files", [])
            if os.path.exists(f["file_path"])
        ]
        self.config.data["open_files"] = open_files
        self.config.save()

        restored_any = False

        for file_info in open_files:
            file_path = file_info["file_path"]
            is_modified = file_info.get("is_modified", False)
            caret_position = file_info.get("caret_position", (0, 0))
            lexer = file_info.get("lexer", "None")

            try:
                is_temp_backup = (
                    file_path.endswith(".bak") and # check for 'new '?
                    os.path.dirname(file_path) == self.backup_path
                )

                if is_temp_backup:
                    with open(file_path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    tab_title = os.path.splitext(os.path.basename(file_path))[0]

                    editor = self.add_new_tab(content, tab_title, file_name=file_path)
                
                else:
                    backup_name = f"{os.path.basename(file_path)}.bak"
                    backup_file = os.path.join(self.backup_path, backup_name)
                    
                    if os.path.exists(backup_file):
                        with open(backup_file, "r", encoding="utf-8") as fh:
                            content = fh.read()
                        self.plugin_api.log(f"Restoring {file_path} from backup {backup_file}")
                    elif os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8") as fh:
                            content = fh.read()
                        self.plugin_api.log(f"Restoring {file_path} from original file")
                    else:
                        self.plugin_api.log(f"No backup or original for {file_path}. Removing from config.")
                        self.config.remove_open_file(file_path)
                        continue

                    tab_title = os.path.basename(file_path)
                    editor = self.add_new_tab(content, tab_title, file_name=file_path)

                editor.blockSignals(True)
                editor.setText(content)
                editor.blockSignals(False)

                if is_modified:
                    editor.setModified(True)
                if caret_position:
                    editor.setCursorPosition(*caret_position)

                if hasattr(editor, '_margin_timer'):
                    editor._margin_timer.timeout.emit()

                if lexer and lexer != "None":
                    self.set_language(lexer)
                else:
                    self.set_language("None")

                self.set_language(lexer)
                restored_any = True
                
            except Exception as e:
                self.plugin_api.log(f"Failed to restore {file_path or backup_name}: {e}")

        if not restored_any:
            self.plugin_api.log("no files to restore; opening new blank tab")
            self.add_new_tab()

    def add_new_tab(self, content="", title="new 1", file_name=""):
        """Add a new tab to the editor."""
        if not file_name:
            file_name = os.path.join(self.backup_path, f"{title}.bak")

        editor = self.create_editor(content, file_name)
        editor.blockSignals(True)
        editor.setText(content)
        editor.blockSignals(False)

        index = self.tabs.addTab(editor, title)
        self.tabs.setCurrentIndex(index)

        text_icon = QIcon("icons/text.png")
        self.tabs.setTabIcon(index, text_icon)

        if file_name:
            self.set_tab_file_path(editor, file_name)

        if title not in self.backup_files:
            self.backup_files[title] = file_name

        self.config.add_open_file(file_path=file_name, is_modified=editor.isModified(), caret_position=editor.getCursorPosition(), lexer="None")
        self.config.save()

        self.update_title()
        editor.setModified(False)

        return editor

    def create_editor(self, content="", file_name=""):
        editor = QsciScintilla()
        scintilla_config = self.config.get("scintillaConfig", {})

        # Drag and drop support
        editor.setAcceptDrops(True)

        def dragEnterEvent(event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def dropEvent(event):
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    self.open_file_by_path(file_path)

        editor.dragEnterEvent = dragEnterEvent
        editor.dropEvent = dropEvent

        editor._margin_timer = QTimer()
        editor._margin_timer.setSingleShot(True)
        editor._margin_timer.setInterval(50)

        def update_margin_width():
            """Dynamically adjust the width of the margin based on the number of lines in the open document."""
            total_lines = max(1, editor.lines())
            digits = len(str(total_lines))
            sample_text = "0" * digits
            margin_width = editor.fontMetrics().horizontalAdvance(sample_text) + 16
            editor.setMarginWidth(0, margin_width)

        editor._margin_timer.timeout.connect(update_margin_width)

        def schedule_margin_update():
            editor._margin_timer.start()

        update_margin_width()

        editor.linesChanged.connect(schedule_margin_update)

        font = QFont(scintilla_config.get("font", "Courier New"), scintilla_config.get("font_size", 12))
        font.setFixedPitch(True)
        editor.setFont(font)
        editor.setMarginsFont(font)

        background_color = QColor(scintilla_config.get("color", "#FFFFFF"))
        font_color = QColor(scintilla_config.get("font_color", "#000000"))
        caret_color = QColor(scintilla_config.get("caret_color", "#e8e8ff"))
        margins_color = QColor(scintilla_config.get("margins_color", "#e0e0e0"))

        editor.setPaper(background_color)
        editor.setColor(font_color)
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(caret_color)
        editor.setMarginsBackgroundColor(QColor(scintilla_config.get("margins_color", "#c0c0c0")))
        editor.setMarginsForegroundColor(font_color)

        editor.setFolding(QsciScintilla.FoldStyle.BoxedFoldStyle)
        editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        editor.setAutoCompletionThreshold(2)

        editor.setIndentationsUseTabs(False)
        editor.setAutoIndent(self.config.get("autoIndent", True))
        editor.setTabWidth(4) 

        editor.modificationChanged.connect(lambda: self.update_tab_modified_state(editor))

        if self.config.get("wordWrap", False):
            editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        else:
            editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)

        editor.textChanged.connect(self.text_changed)
        
        return editor

    def update_title(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            file_name = self.tabs.tabText(self.tabs.currentIndex()).replace("&", "") # ugly hack, but it adds an & and I cannot for the life of me figure out why
            self.setWindowTitle(f"{file_name} - Notepad8")

    def text_changed(self):
        current_tab_index = self.tabs.currentIndex()
        current_tab_name = self.tabs.tabText(current_tab_index)
        current_editor = self.tabs.currentWidget()
        
        if isinstance(current_editor, QsciScintilla):
            self.modified_tabs[current_editor] = True
            if not current_tab_name.startswith("*"):
                self.tabs.setTabText(current_tab_index, f"*{current_tab_name}")
            self.update_title()

    # new file
    def new_file(self):
        """Creates a new tab with the next available number."""
        pattern = re.compile(r"^new (\d+)", re.IGNORECASE)

        for i in range(self.tabs.count()):
            title = self.tabs.tabText(i).replace("&", "")
            match = pattern.match(title)
            if match:
                used_numbers.add(int(match.group(1)))

        for file_name in os.listdir(self.backup_path):
            match = pattern.match(file_name)
            if match:
                used_numbers.add(int(match.group(1)))

        for file_info in self.config.get("open_files", []):
            base = os.path.basename(file_info["file_path"])
            match = pattern.match(base)
            if match:
                used_numbers.add(int(match.group(1)))

        new_number = 1
        while new_number in used_numbers:
            new_number += 1

        new_tab_title = f"new {new_number}"
        file_path = os.path.join(self.backup_path, f"{new_tab_title}.bak")

        self.plugin_api.log(f"Creating new tab: {new_tab_title}")
        self.add_new_tab(title=new_tab_title, file_name=file_path)

    def open_file_by_path(self, file_path): 
        """Opens a file by a path."""
        if not file_path:
            return

        for editor, path in self.file_paths.items():
            if path == file_path:
                self.plugin_api.show_error(
                    "Error", f"The file {os.path.basename(file_path)} is already open"
                )
                return 
    
        try:
            with open(file_path, "rb") as file:
                binary_content = file.read()
                detected = from_bytes(binary_content).best()
            
                if detected:
                    encoding = detected.encoding
                    try: 
                        content = binary_content.decode(encoding)
                    except UnicodeDecodeError:
                        content = binary_content.hex()
                else:    
                    content = binary_content.hex()
        
            editor = self.add_new_tab(content, os.path.basename(file_path), file_name=file_path)

            if hasattr(editor, '_margin_timer'):
                editor._margin_timer.timeout.emit()
        
            lexer_class = get_lexer_for_file(file_path)
            lexer_name = "None"
        
            if lexer_class:
                for language, cls in DEFAULT_LANGUAGES.items():
                    if cls == lexer_class:
                        lexer_name = language
                        break
        
            self.set_language(lexer_name)
        
            self.config.add_open_file(file_path, is_modified=False, lexer=lexer_name)
            self.config.save()
        
            editor.setModified(False)
        
            self.plugin_api.log(f"Opened: {file_path} with lexer: {lexer_name}")

        except Exception as e:
            self.plugin_api.show_error("Error", f"Failed to open file '{file_path}':\n{str(e)}")

    # open file dialog
    def open_file_dialog(self):
        """Opens the file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All types (*)")
        if file_path:
            self.open_file_by_path(file_path)

    # open file (dropped)
    def open_dropped_file(self, file_path):
        """Handles a file dropped into Notepad8."""
        self.open_file_by_path(file_path)
                
    def save_file(self, editor):
        """Saves the current file."""
        file_path = self.get_tab_file_path(editor)

        # TODO: this is ok for "new" files, but backed up files should save over the original
        if not file_path or file_path.startswith(self.backup_path):
            self.save_file_as(editor)
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(editor.text())

            backup_file = self.backup_files.pop(file_path, None)
            if backup_file and os.path.exists(backup_file):
                os.remove(backup_file)

            editor.setModified(False)
            self.plugin_api.log(f"File saved: {file_path}")

        except Exception as e:
            self.plugin_api.show_error("Error", f"Failed to save file '{file_path}': {e}")

            
    def save_file_as(self, editor):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8", newline='') as file:
                    file.write(editor.text())
                    editor.setModified(False)
                self.set_tab_file_path(editor, file_path)
                self.modified_tabs[editor] = False

                self.config.add_open_file(file_path, is_modified=False, lexer=self.get_lexer_for_editor(editor))
                self.config.save()

                self.update_tab_title(editor, file_path)
                self.update_title()
            except Exception as e:
                self.plugin_api.show_error("Error", f"Failed to save file!:\n{str(e)}")
            
    def save_file_as_copy(self, editor):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Copy As", "", "All Files (*)")
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8", newline='') as file:
                file.write(editor.text())

            self.plugin_api.log(f"Saved copy of current file to: {file_path}")

        except Exception as e:
            self.plugin_api.show_error("Error", f"Failed to save file copy:\n{file_path}", e)
                
    def save_current_file(self):
        editor = self.tabs.currentWidget()
        if isinstance(editor, QsciScintilla):
            self.save_file(editor)

    def save_current_file_as(self):
        editor = self.tabs.currentWidget()
        if isinstance(editor, QsciScintilla):
            self.save_file_as(editor)

    def save_current_file_as_copy(self):
        editor = self.tabs.currentWidget()
        if isinstance(editor, QsciScintilla):
            self.save_file_as_copy(editor)

    # drag event
    def dragEnterEvent(self, event):
        """Handles the drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # drop event
    def dropEvent(self, event):
        """Handles the drop event."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self.open_dropped_file(file_path)

    def load_lexer_colors(self, lexer_name):
        """Load lexer colors from a JSON file or _lang.json config."""
        from file_types import GENERIC_LEXERS
        for lang_name, lexer_info in GENERIC_LEXERS.items():
            if lexer_name == f"{lang_name}Lexer" or lexer_name == lang_name:
                if "styles" in lexer_info["config"]:
                    return lexer_info["config"]["styles"]
                elif "colors" in lexer_info["config"]:
                    colors = lexer_info["config"]["colors"]
                    return {k: {"color": v} for k, v in colors.items()}
    
        lexer_name = lexer_name.replace("Lexer", "")
        if lexer_name.startswith("custom_lexers"):
            lexer_name = lexer_name.split(".")[-1]

        lexer_dir = os.path.join(os.path.dirname(__file__), "lexer")
        lexer_file = os.path.join(lexer_dir, f"{lexer_name}.json")

        if not os.path.exists(lexer_file):
            return {}

        try:
            with open(lexer_file, "r") as file:
                data = json.load(file)
                if isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
                    return data
                else:
                    return {k: {"color": v} for k, v in data.items()}
        except json.JSONDecodeError as e:
            self.plugin_api.log(f"error parsing JSON file for {lexer_file}! {e}")
            return {}

    def get_lexer_for_editor(self, editor):
        """Retrieve the current lexer for the given editor."""
        lexer = editor.lexer()
        if lexer:
            return lexer.language()
        return "None"

    def apply_lexer_styling(self, editor, lexer):
        """Apply complete styling configuration to a lexer and editor."""
        scintilla_config = self.config.get("scintillaConfig", {})
        default_background = QColor(scintilla_config.get("color", "#FFFFFF"))
        default_font_color = QColor(scintilla_config.get("font_color", "#000000"))
        font = QFont(scintilla_config.get("font", "Courier New"), scintilla_config.get("font_size", 12))
        font.setFixedPitch(True)
    
        lexer.setFont(font)
    
        lexer_name = lexer.__class__.__name__
        if lexer_name.startswith("QsciLexer"):
            lexer_name = lexer_name.replace("QsciLexer", "")
    
        lexer_styles = self.load_lexer_colors(lexer_name)
    
        for style in range(128):
            desc = lexer.description(style)
            if desc and desc in lexer_styles:
                style_def = lexer_styles[desc]
            
                if isinstance(style_def, str):
                    color = QColor(style_def)
                    background = default_background
                    style_font = QFont(font)
                else:
                    color = QColor(style_def.get("color", default_font_color.name()))
                    background = QColor(style_def.get("background", default_background.name()))
                
                    style_font = QFont(font)
                    if style_def.get("bold", False):
                        style_font.setBold(True)
                    if style_def.get("italic", False):
                        style_font.setItalic(True)
            
                lexer.setColor(color, style)
                lexer.setPaper(background, style)
                lexer.setFont(style_font, style)
            else:
                lexer.setPaper(default_background, style)
                lexer.setFont(font, style)
    
        default_style = 0
        if hasattr(lexer, 'Default'):
            default_style = lexer.Default
        elif hasattr(lexer, 'DEFAULT'):
            default_style = lexer.DEFAULT
    
        lexer.setPaper(default_background, default_style)
        lexer.setColor(default_font_color, default_style)
        lexer.setFont(font, default_style)
    
        editor.setLexer(lexer)
    
        editor.setMarginsBackgroundColor(QColor(scintilla_config.get("margins_color", "#c0c0c0")))
        editor.setMarginsForegroundColor(default_font_color)

        # Only do the expensive re-style if the document isn't already styled
        # Check if document already has styling applied
        if not hasattr(editor, '_lexer_applied') or editor._lexer_applied != lexer_name:
            # Force complete re-styling of the entire document
            editor.SendScintilla(QsciScintilla.SCI_SETLEXER, editor.SendScintilla(QsciScintilla.SCI_GETLEXER))
            editor.SendScintilla(QsciScintilla.SCI_COLOURISE, 0, -1)
        
            # Additional force: trigger styleText manually for custom lexers
            if hasattr(lexer, 'styleText'):
                text_length = editor.length()
                lexer.styleText(0, text_length)
        
            # Mark as styled
            editor._lexer_applied = lexer_name

        editor.update()

        return font

    def set_language(self, language):
        """Set the syntax highlighting language for the current editor."""
        for lang, action in self.language_actions.items():
            action.setChecked(lang == language)
    
        self.current_language = language
    
        editor = self.tabs.currentWidget()
        if not isinstance(editor, QsciScintilla):
            return
    
        if language == "None":
            editor.setLexer(None)
            self.tab_settings[editor] = {'language': 'None', 'font': editor.font()}
            return
    
        lexer_class = DEFAULT_LANGUAGES.get(language)
        if not lexer_class:
            self.plugin_api.log(f"No lexer class found for language: {language}")
            return
    
        lexer = lexer_class(editor)
        font = self.apply_lexer_styling(editor, lexer)
    
        self.tab_settings[editor] = {
            'language': language,
            'font': font
        }
    
        self.plugin_api.log(f"Set language to {language}")

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        file_path = self.get_tab_file_path(editor)

        if editor.isModified():
            reply = QMessageBox.question(
                self, 
                "Save", 
                "Do you want to save the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.save_file(editor)
            elif reply == QMessageBox.StandardButton.No:
                pass
            else:
                return

        self.tabs.removeTab(index)

        if editor in self.modified_tabs:
            del self.modified_tabs[editor]
        if editor in self.file_paths:
            del self.file_paths[editor]
        if editor in self.tab_settings:
            del self.tab_settings[editor]
    
        if file_path:
            self.config.remove_open_file(file_path)
            self.config.save()

            is_backup = file_path.startswith(self.backup_path) and file_path.endswith('.bak')
        
            if is_backup and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.plugin_api.log(f"Deleted backup file: {file_path}")
                except Exception as e:
                    self.plugin_api.log(f"Failed to delete backup {file_path}: {e}")
        
            if not is_backup:
                backup_name = f"{os.path.basename(file_path)}.bak"
                backup_file = os.path.join(self.backup_path, backup_name)
                if os.path.exists(backup_file):
                    try:
                        os.remove(backup_file)
                        self.plugin_api.log(f"Deleted associated backup: {backup_file}")
                    except Exception as e:
                        self.plugin_api.log(f"Failed to delete backup {backup_file}: {e}")
        
            if file_path in self.backup_files:
                del self.backup_files[file_path]
    
        self.update_title()
    
        if self.tabs.count() == 0:
            if self.config.get("openNewTabOnLastClosed", True):
                self.add_new_tab()
            else:
                self.close()

    def cleanup_orphaned_backups(self):
        """Remove backup files that are no longer in the open_files config."""
        if not os.path.exists(self.backup_path):
            return
    
        open_file_paths = {f["file_path"] for f in self.config.get("open_files", [])}

        for backup_file in os.listdir(self.backup_path):
            backup_path = os.path.join(self.backup_path, backup_file)
        
            if backup_path not in open_file_paths:
                original_name = backup_file.replace('.bak', '')
                is_referenced = any(
                    os.path.basename(f) == original_name or 
                    f"{os.path.basename(f)}.bak" == backup_file 
                    for f in open_file_paths
                )
            
                if not is_referenced:
                    try:
                        os.remove(backup_path)
                        self.plugin_api.log(f"Cleaned up orphaned backup: {backup_path}")
                    except Exception as e:
                        self.plugin_api.log(f"Failed to cleanup {backup_path}: {e}")
            
    def update_tab_title(self, editor, file_path):
        index = self.tabs.indexOf(editor)
        if index != -1:
            tab_name = os.path.basename(file_path)
            self.tabs.setTabText(index, tab_name)
            
    def close_program(self):
        self.config.save()
        self.close()

    def toggle_word_wrap(self, checked):
        current_editor = self.tabs.currentWidget()
        if isinstance(current_editor, QsciScintilla):
            if checked:
                current_editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
            else:
                current_editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        
        self.config.set("wordWrap", checked)
        self.config.save()
        
    def word_wrap_all_tabs(self):
        wrap_enabled = self.config.get("wordWrap", False)
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if isinstance(editor, QsciScintilla):
                if self.config.get("wordWrap", False):
                    editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
                else:
                    editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)
                    
    def get_tab_file_path(self, editor):
        return self.file_paths.get(editor, None)
    
    def set_tab_file_path(self, editor, file_path):
        self.file_paths[editor] = file_path
    
    def goto_line(self):
        current_editor = self.tabs.currentWidget()
        if not isinstance(current_editor, QsciScintilla):
            QMessageBox.warning(self, "Error", "There is no active editor.")
            return

        total_lines = current_editor.lines()

        line_number, ok = QInputDialog.getInt(
            self,
            "Go To...",
            f"Enter a line (1 - {total_lines}):",
            1,
            1,
            total_lines
        )

        if ok and 1 <= line_number <= total_lines:
            current_editor.setCursorPosition(line_number - 1, 0)

    def update_title_on_tab_change(self, index):
        """Update window title and restore tab settings when switching tabs."""
        self.update_title()

        editor = self.tabs.widget(index)
        if not isinstance(editor, QsciScintilla):
            return

        settings = self.tab_settings.get(editor, {})
        language = settings.get("language", "None")
        
        current_lexer = editor.lexer()
        needs_lexer_update = False
    
        if language == "None":
            if current_lexer is not None:
                needs_lexer_update = True
        else:
            if current_lexer is None:
                needs_lexer_update = True
            else:
                current_lang = current_lexer.language()
                if current_lang != language:
                    needs_lexer_update = True
    
        if needs_lexer_update:
            self.set_language(language)
        else:
            for lang, action in self.language_actions.items():
                action.setChecked(lang == language)
            self.current_language = language

    def update_tab_modified_state(self, editor):
        """Changes the tab icon, as well as adds a *, if the file is modified."""
        index = self.tabs.indexOf(editor)
        file_name = self.tabs.tabText(index)
        
        unmodified_icon = QIcon("icons/text.png")
        modified_icon = QIcon("icons/text_modified.png")
        
        if file_name.startswith("*"):
            file_name = file_name[1:]
        
        if editor.isModified():
            self.tabs.setTabText(index, f"*{file_name}")
            self.tabs.setTabIcon(index, modified_icon)
        else:
            self.tabs.setTabText(index, file_name)
            self.tabs.setTabIcon(index, unmodified_icon)
        self.update_title()
        
    def print_file(self):
        """Opens the print dialog box."""
        # TODO: i could not figure out how to print from Scintilla, so this will lack syntax highlighting for now
        if not print_support:
            self.plugin_api.show_error("Printing Unavailable", "QtPrintSupport failed to load. Printing is unavailable for this session. Refer to your distro's manual for further instructions.")
            return

        editor = self.tabs.currentWidget()
        if not isinstance(editor, QsciScintilla):
            return
        
        print_text = editor.text()
        
        if not print_text.strip():
            reply = QMessageBox.question(
                self, 
                "Empty document", 
                "Document is empty. Print anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            doc = QTextDocument()
            doc.setPlainText(print_text)
            doc.print(printer)

    # About Box
    def show_about_box(self):
        """Displays the about box for the program."""
        QMessageBox.about(
            self,
            "About Notepad8",
            "<h3><center>Notepad8 v0.0.1</center></h3>"
            "<p>The ass-backwards Notepad++ clone for *nix!</p>"
            "<p>By Hotlands Software</p>"
            "<p><b>THIS PROGRAM IS UNSTABLE</b>. It may crash, break, and future updates might not be compatible with eachother!!!</p>"
            "<p>GitHub: <a href='https://github.com/hotlandsoftware/notepadpypp'>https://github.com/hotlandsoftware/notepadpypp</a></p>"
        )
        
    # Search Dialog
    def find_dialog(self):
        """Opens the search dialog."""
        editor = self.tabs.currentWidget()
        if not isinstance(editor, QsciScintilla):
            return

        dialog = SearchDialog(
            self,
            wrap_around=self.config.get("wrapAroundSearch", False),
            use_regex=self.config.get("useRegex", False),
            last_search_text=self.get_last_search()["text"]
        )
        if dialog.show() == QDialog.DialogCode.Accepted:
            options = dialog.get_search_options()
            self.config["wrapAroundSearch"] = options["wrap_around"]
            self.config["useRegex"] = options["use_regex"]
            self.config.save()
            self.last_search_options = options
            self.find_text_in_editor(editor, options)

    # Get Last Search
    def get_last_search(self):
        """Returns the last search option (returns defaults if none exist)."""
        if self.last_search_options is None:
            self.last_search_options = {
                "text": "",
                "match_case": False,
                "wrap_around": False,
                "use_regex": False,
                "direction": "down",
            }
        return self.last_search_options
            
    def find_text_in_editor(self, editor, options):
        search_text = options["text"]
        match_case = options["match_case"]
        wrap_around = options["wrap_around"]
        use_regex = options["use_regex"]
        forward = options["direction"] == "down"

        full_text = editor.text()
        current_position = editor.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)

        if self.config.get("debugMode", True):
            self.plugin_api.log(f"Searching '{search_text}' | Regex: {use_regex} | Match case: {match_case} | Wrap around: {wrap_around} | Direction: {'down' if forward else 'up'}")
    
        flags = 0 if match_case else re.IGNORECASE
        
        try:
            if use_regex:
                pattern = re.compile(search_text, flags)
            else:
                pattern = re.compile(re.escape(search_text), flags)

            match = None

            if forward:
                match = pattern.search(full_text, pos=current_position)
                if not match and wrap_around:
                    match = pattern.search(full_text, pos=0)
            else:
                matches = list(pattern.finditer(full_text[:current_position]))
                if matches:
                    match = matches[-1]
                elif wrap_around:
                    matches = list(pattern.finditer(full_text))
                    if matches:
                        match = matches[-1]

            if match:
                start, end = match.span()

                if forward:
                    editor.SendScintilla(QsciScintilla.SCI_SETSEL, start, end)
                else:
                    editor.SendScintilla(QsciScintilla.SCI_SETSEL, end, start)
                    
            else:
                direction_text = "upwards" if not forward else "downwards"
                if wrap_around:
                    QMessageBox.information(self, "Find", f"'{search_text}' not found in the entire file.")
                else:
                    QMessageBox.information(self, "Find", f"'{search_text}' not found {direction_text} from the caret position.")
        except re.error as e:
            self.plugin_api.show_error("Regex Error", f"Invalid regular expression: {e}")

            
    def find_next(self):
        """Finds the next occurrence in a specified search."""
        editor = self.tabs.currentWidget()
        if not isinstance(editor, QsciScintilla):
            return 
        
        options = self.get_last_search()
        options["direction"] = "down"
        self.find_text_in_editor(editor, options)
    
    # we can probably do this in one function
    def find_previous(self):
        """Finds the previous occurrence in a specified search."""
        editor = self.tabs.currentWidget()
        if not isinstance(editor, QsciScintilla):
            return 
        
        options = self.get_last_search()
        options["direction"] = "up"
        self.find_text_in_editor(editor, options)
    
    def launch_new_window(self):
        """Launches a new Notepad8 instance."""
        win = NotepadPy()
        app = QApplication.instance()

        if not hasattr(app, "_np_windows"):
            app._np_windows = []
        app._np_windows.append(win)

        win.show()
    
    def launch_new_terminal(self):
        system = platform.system()

        try:
            if system == "Windows":
                subprocess.Popen(["start", "cmd"], shell=True)
        
            elif system == "Darwin": # mac
                subprocess.Popen(["open", "-a", "Terminal"])
            
            # there is absolutely a better way to do this
            else: # unix
                for term in ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "xterm", "alacritty", "kitty"]:
                    if shutil.which(term):
                        subprocess.Popen([term])
                        break
                else:
                    self.plugin_api.show_error("Error", "No terminal emulator found in PATH.")

        except Exception as e:
            self.plugin_api.show_error("Error", f"Failed to launch terminal:\n{str(e)}")
        
    def import_npp_language(self):
        """Import a Notepad++ User Defined Language XML file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Notepad++ Language", 
            "", 
            "XML Files (*.xml);;All Files (*)"
        )

        if not file_path:
            return

        try:
            from npp_converter import NotepadPlusPlusConverter

            converter = NotepadPlusPlusConverter()
            config = converter.convert_xml_to_json(file_path)
        
            lexer_dir = os.path.join(os.path.dirname(__file__), "lexer")
            os.makedirs(lexer_dir, exist_ok=True)

            lang_name = config['name']
            output_path = os.path.join(lexer_dir, f"{lang_name}_lang.json")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)

            self.plugin_api.sohw_info(
                "Import Successful",
                f"Successfully imported language: {lang_name}\n\n"
                f"Saved to: {output_path}\n\n"
                f"Extensions: {', '.join(config['extensions'])}\n\n"
                "Please restart the application to use the new language."
            )
        
            self.plugin_api.log(f"Imported Notepad++ User Language: {lang_name}")

        except Exception as e:
            self.plugin_api.show_error(
                "Import Failed",
                f"Failed to import Notepad++ language file:\n{str(e)}"
            )

# only allow a single instance to run
def check_duplicate_instance(app_id="NotepadPy"):
    socket = QLocalSocket()
    socket.connectToServer(app_id)
    
    if socket.waitForConnected(100):
        return True
    
    socket.close()
    return False
    
def setup_single_instance_server(app_id="NotepadPy"):
    server = QLocalServer()
    if not server.listen(app_id):
        existing_instance = QLocalSocket()
        existing_instance.connectToServer(app_id)
        
        if existing_instance.waitForConnected(1000):
            # todo: make it focus on window, like notepad++ does
            print("Only one insance of NotepadPy++ can run at a time")
            sys.exit(0)
        else:
            QLocalServer.removeServer(app_id)
            if not server.listen(app_id):
                print("Failed to create server")
                sys.exit(1)
                
    return server

if __name__ == "__main__":
    # set up server 
    app = QApplication(sys.argv)
    single_instance_server = setup_single_instance_server(app_id="NotepadPy")
    window = NotepadPy()
    window.show()
    sys.exit(app.exec())