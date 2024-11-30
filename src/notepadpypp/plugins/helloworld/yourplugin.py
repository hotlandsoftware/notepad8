from PyQt6.QtWidgets import QMessageBox

def register(plugin_api):
    """Registers the Hello World plugin."""
    print("Hello World plugin loaded successfully!")

    plugin_api.add_action_to_plugin_menu(
        "Hello World", "Open File", plugin_api.app.open_file_dialog
    )
    plugin_api.add_action_to_plugin_menu(
        "Hello World", "About", lambda: about_box(plugin_api.app)
    )

def about_box(parent=None):
    """Displays an about box."""
    QMessageBox.about(
        parent,
        "Hello World",
        "<h3><center>HelloWorld</center></h3>"
        "<p>An example NotepadPypp plugin</p>"
        "<p>By Hotlands Software</p>"
    )