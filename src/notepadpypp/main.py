import sys
import os
import json
import re

from typing import Optional, Dict, Any

from PyQt6.QtGui import ( 
    QFont, QColor, QTextDocument, QIcon, QAction
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, 
    QTabWidget, QInputDialog, QDialog, QMenuBar, QMenu
)
from PyQt6.QtCore import QCoreApplication, Qt, QSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.Qsci import QsciScintilla, QsciLexer

from config import initialize_config, save_config
from file_types import get_lexer_for_file, LANGUAGES
from plugin_manager import PluginManager
from dialogs import SearchDialog

class NotepadPy(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = initialize_config()
        self.file_paths = {}
        self.modified_tabs = {}
        self.new_file_counter = 2
        self.last_search_options = None
        self.plugin_manager = PluginManager(self) 

        self.init_ui()
        self.plugin_manager.load_plugins()

        self.restore_session()

    def init_ui(self):
        """Initialize the main user interface."""
        self.setWindowTitle("NotepadPy++")
        self.resize(800, 600)
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
            ("Save As", "Ctrl+Shift+S", self.save_current_file_as, "icons/save_as.png"),
            ("Print", "Ctrl+P", self.print_file, "icons/print.png"),
            ("Exit", "Alt+F4", self.close_program, None)
        ]
        self.add_actions_to_menu(file_menu, file_actions)

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

        self.get_plugins_menu() 

        # About Menu
        about_menu = menu_bar.addMenu("?")
        about_action = about_menu.addAction("About")
        about_action.setShortcut("F1")
        about_action.triggered.connect(self.show_about_box)

    # Actions helper
    def add_actions_to_menu(self, menu, actions):
        """Helper to add actions to a menu."""
        for name, shortcut, handler, icon in actions:
            if icon:
                action = menu.addAction(QIcon(icon), name)
            else:
                action = menu.addAction(name)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(handler)

    # Create language menu
    def create_language_menu(self, language_menu):
        """Initializes the language selection menu."""
        self.language_actions = {}

        none_action = language_menu.addAction("None (Normal Text)")
        none_action.setCheckable(True)
        none_action.triggered.connect(lambda: self.set_language("None"))
        self.language_actions["None"] = none_action
        
        grouped_languages = {}
        for language in sorted(LANGUAGES.keys()):
            group = language[0].upper()
            grouped_languages.setdefault(group, []).append(language)

        for group, languages in grouped_languages.items():
            submenu = language_menu.addMenu(group)
            for language in languages:
                action = submenu.addAction(language)
                action.setCheckable(True)
                action.triggered.connect(lambda _, lang=language: self.set_language(lang))
                self.language_actions[language] = action

    # Create plugins menu
    def create_plugins_menu(self, plugins_menu):
        """Creates and populates the plugins menu."""
        plugin_actions = [
            ("Reload Plugins", None, self.reload_plugins, None),
        ]

        self.add_actions_to_menu(plugins_menu, plugin_actions)

        plugins_menu.addSeparator()

    def get_plugins_menu(self):
        """Get or create the Plugins menu."""
        # Try to find the Plugins menu
        plugins_menu = self.menuBar().findChild(QMenu, "Plugins")
        if not plugins_menu:
            # Create the Plugins menu only if it doesn't already exist
            plugins_menu = self.menuBar().addMenu("Plugins")
            plugins_menu.setObjectName("Plugins")  # Set an object name for consistent retrieval
            self.create_plugins_menu(plugins_menu)  # Initialize the Plugins menu
        return plugins_menu

    # Add Submenu to Plugins menu (for Plugins)
    def add_to_plugin_menu(self, plugin_name):
        """Adds a submenu to the Plugins menu."""
        plugins_menu = self.get_plugins_menu()

        for action in plugins_menu.actions():
            if action.menu() and action.text() == plugin_name:
                return action.menu()

        plugin_menu = plugins_menu.addMenu(plugin_name)
        return plugin_menu

    def add_action_to_plugin_menu(self, plugin_name, action_name, callback=None):
        """Adds an action under the specified plugin's submenu in the Plugins menu."""
        plugin_menu = self.add_to_plugin_menu(plugin_name)
        action = plugin_menu.addAction(action_name)
        if callback:
            action.triggered.connect(callback)
        return action

    # Reload plugins
    def reload_plugins(self):
        """Reloads all plugins and updates the Plugins menu."""
        plugins_menu = self.get_plugins_menu()
        plugins_menu.clear()

        self.create_plugins_menu(plugins_menu)

        self.plugin_manager.load_plugins()

        loaded_plugins = self.plugin_manager.get_loaded_plugins()
        for plugin in loaded_plugins:
            plugin_module = plugin.get("module")
            if hasattr(plugin_module, "register"):
                plugin_module.register(self)

        QMessageBox.information(self, "Plugins Reloaded", "Reloaded plugins successfully!")

    def create_toolbar(self):
        """Creates the toolbar below the menu."""
        toolbar = self.addToolBar("Main")
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

    def restore_session(self):
        """Restore open files from the previous session. TODO: Implement Notepad++ functionality where it restores modified files as well."""
        open_files = self.config.get("open_files", [])
        for file_path in open_files:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    editor = self.add_new_tab(content, os.path.basename(file_path), file_name=file_path)
                    
                    lexer_class = get_lexer_for_file(file_path)
                    if lexer_class:
                        language = next((language for language, cls in LANGUAGES.items() if cls == lexer_class), "None")
                        self.set_language(language)
                    else:
                        self.set_language("None")
            except IOError:
                self.config["open_files"].remove(file_path)
                save_config(self.config)
                
        if not open_files:
            self.add_new_tab()
                
    def add_new_tab(self, content="", title="new 1", file_name=""):
        editor = self.create_editor(content, file_name)
        editor.blockSignals(True)
        editor.setText(content)
        editor.blockSignals(False)
        index = self.tabs.addTab(editor, title)
        self.tabs.setCurrentIndex(index)

        if file_name:
            self.set_tab_file_path(editor, file_name)
            if file_name not in self.config["open_files"]:
                self.config["open_files"].append(file_name)
                save_config(self.config)

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

        def update_margin_width():
            """Dynamically adjust the width of the margin based on the number of lines in the open document."""
            total_lines = max(1, editor.lines())
            digits = len(str(total_lines))
            margin_width = editor.fontMetrics().horizontalAdvance("0") * digits + 6
            editor.setMarginWidth(0, f"{margin_width}px")

        update_margin_width()

        editor.linesChanged.connect(update_margin_width)
        editor.textChanged.connect(update_margin_width)

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

        editor.modificationChanged.connect(lambda: self.update_tab_modified_state(editor))

        lexer_class = get_lexer_for_file(file_name)
        if lexer_class:
            lexer = lexer_class()
            lexer.setFont(font)

            for style in range(128):
                lexer.setPaper(background_color, style)
                lexer.setColor(font_color, style)

            lexer.setPaper(background_color, lexer.Default)
            lexer.setColor(font_color, lexer.Default)

            editor.setLexer(lexer)
        else:
            editor.setPaper(background_color)
            editor.setColor(font_color)

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
            self.setWindowTitle(f"{file_name} - NotepadPy++")

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
        new_tab_title = f"new {self.new_file_counter}"
        self.new_file_counter += 1
        self.add_new_tab(title=new_tab_title)
    
    # open file (by path)
    def open_file_by_path(self, file_path): 
        """Opens a file by a path."""
        if not file_path:
            return

        for editor, path in self.file_paths.items():
            if path == file_path:
                QMessageBox.critical(
                    self, "Error", f"The file {os.path.basename(file_path)} is already open"
                )
                return 
        try:
            with open(file_path, "rb") as file:  # Open in binary mode
                binary_content = file.read()
                try:
                    content = binary_content.decode("utf-8")
                except UnicodeDecodeError:
                    content = binary_content.hex()
                    
                editor = self.add_new_tab(content, os.path.basename(file_path), file_name=file_path)
                editor.setText(content)

                # Set language for the file
                lexer_class = get_lexer_for_file(file_path)
                if lexer_class:
                    for language, cls in LANGUAGES.items():
                        if cls == lexer_class:
                            self.set_language(language)
                            break
                else:
                    self.set_language("None")

                editor.setModified(False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file '{file_path}':\n{str(e)}")

    # open file dialog
    def open_file_dialog(self):
        """Opens the file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All types (*)")
        if file_path:
            self.open_file_by_path(file_path)

    # open file (dropped)
    def open_dropped_file(self, file_path):
        """Handles a file dropped into Notepadpypp."""
        self.open_file_by_path(file_path)
                
    def save_file(self, editor):
        file_path = self.get_tab_file_path(editor)
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(editor.text())
                self.modified_tabs[editor] = False
                self.update_tab_title(editor, file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file!:\n{str(e)}")
        else:
            self.save_file_as(editor)
            
    def save_file_as(self, editor):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(editor.text())
                self.set_tab_file_path(editor, file_path)
                self.modified_tabs[editor] = False

                self.update_tab_title(editor, file_path)
                self.update_title()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file!:\n{str(e)}")
                
    def save_current_file(self):
        editor = self.tabs.currentWidget()
        if isinstance(editor, QsciScintilla):
            self.save_file(editor)

    def save_current_file_as(self):
        editor = self.tabs.currentWidget()
        if isinstance(editor, QsciScintilla):
            self.save_file_as(editor)

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
        """Load lexer colors from a JSON (and soon also XML) file."""
        lexer_file = os.path.join("lexer", f"{lexer_name}.json")
        if os.path.exists(lexer_file):
            with open(lexer_file, "r") as file:
                return json.load(file)
        else:
            # fallback
            return {}

    def set_language(self, language):
        for lang, action in self.language_actions.items():
            action.setChecked(lang == language)
    
        self.current_language = language
        
        editor = self.tabs.currentWidget()
        if not isinstance(editor, QsciScintilla):
            return
        
        if language == "None":
            editor.setLexer(None)
            editor.setText(editor.text())
            return
    
        lexer_class = LANGUAGES.get(language)
        if lexer_class and self.tabs.currentWidget():
            editor = self.tabs.currentWidget()
            lexer = lexer_class()

            scintilla_config = self.config.get("scintillaConfig", {})
            background_color = QColor(scintilla_config.get("color", "#FFFFFF"))
            font_color = QColor(scintilla_config.get("font_color", "#000000"))
            font = QFont(scintilla_config.get("font", "Courier New"), scintilla_config.get("font_size", 12))
            font.setFixedPitch(True)
            lexer.setFont(font)
            
            lexer_name = lexer.__class__.__name__.replace("QsciLexer", "")
            lexer_colors = self.load_lexer_colors(lexer_name)

            for style in range(128): 
                if lexer.description(style):
                    color = lexer_colors.get(lexer.description(style), font_color.name())
                    lexer.setColor(QColor(color), style)
                    lexer.setPaper(background_color, style)
                else: 
                    lexer.setPaper(background_color, style)

            lexer.setPaper(background_color, lexer.Default)
            lexer.setColor(font_color, lexer.Default)

            editor.setLexer(lexer)
    
            editor.setPaper(background_color)
            editor.setColor(font_color)
            editor.setMarginsBackgroundColor(QColor(scintilla_config.get("margins_color", "#c0c0c0")))
            editor.setMarginsForegroundColor(QColor(font_color))
            
    def close_tab(self, index):
        editor = self.tabs.widget(index)
        file_path = self.get_tab_file_path(editor)
    
        if editor.isModified():
            reply = QMessageBox.question(
                self, 
                "Save", 
                "Save file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
    
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file(editor)
                self.tabs.removeTab(index)
            elif reply == QMessageBox.StandardButton.No:
                self.tabs.removeTab(index)
        else:
            self.tabs.removeTab(index)
    
        if editor in self.modified_tabs:
            del self.modified_tabs[editor]
        if editor in self.file_paths:
            del self.file_paths[editor]
            
        if file_path and file_path in self.config["open_files"]:
            self.config["open_files"].remove(file_path)
            save_config(self.config)

        self.update_title()
        
        if self.tabs.count() == 0:
            if self.config.get("openNewTabOnLastClosed", True):
                self.add_new_tab()
            else:
                self.close()
            
    def update_tab_title(self, editor, file_path):
        index = self.tabs.indexOf(editor)
        if index != -1:
            tab_name = os.path.basename(file_path)
            self.tabs.setTabText(index, tab_name)
            
    def close_program(self):
        save_config(self.config)
        self.close()

    def toggle_word_wrap(self, checked):
        current_editor = self.tabs.currentWidget()
        if isinstance(current_editor, QsciScintilla):
            if checked:
                current_editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
            else:
                current_editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        
        self.config["wordWrap"] = checked
        save_config(self.config)
        
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
        self.update_title()
        
        editor = self.tabs.widget(index)
        
        # this will break specifying a lexer and switching tabs. need to invent a new method for this
        if isinstance(editor, QsciScintilla):
            file_path = self.get_tab_file_path(editor)
            if file_path:
                current_language = self.current_language
                lexer_class = get_lexer_for_file(file_path)
                if lexer_class:
                    for language, cls in LANGUAGES.items():
                        if cls == lexer_class and language != current_language:
                            self.set_language(language)
                            break
            else:
                self.set_language("None")
    
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
            "About NotepadPy++",
            "<h3><center>NotepadPy++ v0.0.1</center></h3>"
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
            save_config(self.config)
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

        print(f"Searching '{search_text}' | Regex: {use_regex} | Match case: {match_case} | Wrap around: {wrap_around} | Direction: {'down' if forward else 'up'}")
    
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
            QMessageBox.critical(self, "Regex Error", f"Invalid regular expression: {e}")

            
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
            print("ERROR: Only one insance of NotepadPy++ can run at a time")
            QMessageBox.critical(
                None, "Error", "Only one instance of NotepadPy++ can run at a time"
            )
            sys.exit(0)
        else:
            QLocalServer.removeServer(app_id)
            if not server.listen(app_id):
                print("ERROR: Failed to create server")
                QMessageBox.critical(
                    None, "Error", "Failed to create server"
                )
                sys.exit(1)
                
    return server

if __name__ == "__main__":
    # set up server 
    app = QApplication(sys.argv)
    single_instance_server = setup_single_instance_server(app_id="NotepadPy")
    window = NotepadPy()
    window.show()
    sys.exit(app.exec())