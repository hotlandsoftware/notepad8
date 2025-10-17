import logging
from PyQt6.QtWidgets import QMenu, QMessageBox

class PluginAPI:
    def __init__(self, app, plugin_manager):
        self.app = app
        self.plugin_manager = plugin_manager
        self.__version__ = "0.0.1"
        logging.basicConfig(
            level=logging.DEBUG if getattr(app, "config", {}).get("debugMode", False) else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("NotepadPypp")

    ## Creates the Plugins Menu
    def create_plugins_menu(self, plugins_menu):
        """Creates and populates the plugins menu. Introduced in version: v0.0.1"""
        plugin_actions = [("Reload Plugins", None, self.reload_plugins, None)]
        self.app.add_actions_to_menu(plugins_menu, plugin_actions)
        plugins_menu.addSeparator()

    ## Gets the Plugins Menu
    def get_plugins_menu(self):
        """Get or create the Plugins menu. Introduced in version: v0.0.1"""
        plugins_menu = self.app.menuBar().findChild(QMenu, "Plugins")
        if not plugins_menu:
            plugins_menu = self.app.menuBar().addMenu("Plugins")
            plugins_menu.setObjectName("Plugins")
            self.create_plugins_menu(plugins_menu)
        return plugins_menu

    ## Add Submenu to Plugins Menu
    def add_to_plugin_menu(self, plugin_name):
        """Adds a submenu to the Plugins menu. Introduced in version: v0.0.1"""
        plugins_menu = self.get_plugins_menu()
        for action in plugins_menu.actions():
            if action.menu() and action.text() == plugin_name:
                return action.menu()

        plugin_menu = plugins_menu.addMenu(plugin_name)
        return plugin_menu

    ## Adds action (subsubmenu) to Plugins Menu
    def add_action_to_plugin_menu(self, plugin_name, action_name, callback=None):
        """Adds an action under the specified plugin's submenu in the Plugins menu. Introduced in version: v0.0.1"""
        plugin_menu = self.add_to_plugin_menu(plugin_name)
        action = plugin_menu.addAction(action_name)
        if callback:
            action.triggered.connect(callback)
        return action

    ## Reload Plugins
    def reload_plugins(self):
        """Reloads all plugins and updates the Plugins menu. Introduced in version: v0.0.1"""
        plugins_menu = self.get_plugins_menu()
        plugins_menu.clear()
        self.create_plugins_menu(plugins_menu)
        self.plugin_manager.load_plugins()

        loaded_plugins = self.plugin_manager.get_loaded_plugins()
        for plugin in loaded_plugins:
            plugin_module = plugin.get("module")
            if hasattr(plugin_module, "register"):
                plugin_module.register(self)

        QMessageBox.information(self.app, "Plugins Reloaded", "Reloaded plugins successfully")

    ## Get Text of Document
    def get_text_of_document(self):
        """Returns the complete text of the active document. Introduced in version: v0.0.1"""
        current_editor = self.app.tabs.currentWidget()
        if current_editor.__class__.__name__ == "QsciScintilla":
            return current_editor.text()
        else:
            return None

    ## Log
    def log(self, message: str, level: str = "info"):
        """Logs a message to the console. Introduced in version: v0.0.1"""
        if hasattr(self.logger, level):
            getattr(self.logger, level)(message)
        else:
            self.logger.info(message)

    ## Show Error
    def show_error(self, title, message, exc=None):
        """Shows error box. Introduced in version: v0.0.1"""
        full_msg = message
        if exc:
            full_msg += f"\n\n{type(exc).__name__}: {exc}"
            self.logger.error(f"{title}: {exc}", exc_info=True)
        else:
            self.logger.error(f"{title}: {message}")
        QMessageBox.critical(self.app, title, full_msg)

    ## Show Info
    def show_info(self, title, message, exc=None):
        """Shows information box. Introduced in version: v0.0.1"""
        full_msg = message
        if exc:
            full_msg += f"\n\n{type(exc).__name__}: {exc}"
            self.logger.info(f"{title}: {exc}", exc_info=True)
        else:
            self.logger.info(f"{title}: {message}")
        QMessageBox.information(self.app, title, full_msg)
    
    ## Get NotepadPy++ version
    def get_program_version(self):
        """Returns the current version of the program. Introduced in version: v0.0.1"""
        return self.__version__

    ## Get Current Editor
    def get_current_editor(self):
        """Returns the active QsciScintilla editor or None."""
        editor = self.app.tabs.currentWidget()
        if editor and editor.__class__.__name__ == "QsciScintilla":
            return editor
        return None

    ## Undo
    def undo(self):
        """Undo last edit in active editor. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            editor.undo()

    ## Redo
    def redo(self):
        """Redo last undone edit in active editor. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            editor.redo()

    ## Cut
    def cut(self):
        """Cut selection to clipboard. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            editor.cut()

    ## Copy
    def copy(self):
        """Copy selection to clipboard. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            editor.copy()

    ## Paste
    def paste(self):
        """Paste clipboard contents. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            editor.paste()

    ## Delete Selection
    def delete_selection(self):
        """Delete selected text. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            editor.removeSelectedText()

    ## Select All
    def select_all(self):
        """Select all text in the editor. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            editor.selectAll()

    ## Get Selected Text
    def get_selected_text(self):
        """Return the currently selected text in the active editor. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if editor:
            return editor.selectedText()
        return ""

    ## Replace Selected Text
    def replace_selected_text(self, new_text: str):
        """Replace the currently selected text with new_text. Introduced in version: v0.0.1"""
        editor = self.get_current_editor()
        if not editor:
            return
        if not editor.hasSelectedText():
            editor.insert(new_text)
        else:
            editor.replaceSelectedText(new_text)

    ## New File
    def new_file(self):
        """Create a new unsaved file (delegates to main app). Introduced in version: v0.0.1"""
        if hasattr(self.app, "new_file"):
            self.app.new_file()

    ## Open File
    def open_file(self, file_path=None):
        """Open a file; if no path given, open the file dialog. Introduced in version: v0.0.1"""
        if file_path:
            if hasattr(self.app, "open_file_by_path"):
                self.app.open_file_by_path(file_path)
        elif hasattr(self.app, "open_file_dialog"):
            self.app.open_file_dialog()

    ## Save Current File
    def save_current_file(self):
        """Save the currently active file. Introduced in version: v0.0.1"""
        if hasattr(self.app, "save_current_file"):
            self.app.save_current_file()
    
    ## Save Current File As
    def save_current_file_as(self):
        """Save the current file under a new name. Introduced in version: v0.0.1"""
        if hasattr(self.app, "save_current_file_as"):
            self.app.save_current_file_as()

    ## Print File
    def print_current_file(self):
        """Print the current file using the app's print dialog. Introduced in version: v0.0.1"""
        if hasattr(self.app, "print_file"):
            self.app.print_file()

    ## Close Application
    def close_application(self):
        """Close Notepad8 cleanly. Introduced in version: v0.0.1"""
        if hasattr(self.app, "close_program"):
            self.app.close_program()