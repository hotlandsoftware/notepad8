from PyQt6.QtWidgets import QMenu, QMessageBox


class PluginAPI:
    def __init__(self, app, plugin_manager):
        self.app = app
        self.plugin_manager = plugin_manager
        self.__version__ = "0.0.1"

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

    ## Adds action (subsubmenu) to plugin
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
    
    ## Get NotepadPy++ version
    def get_program_version(self):
        """Returns the current version of the program."""
        return self.__version__