from PyQt6.QtWidgets import QMessageBox

def register(app):
    """Registers the Hello World plugin."""
    print("Hello World plugin registered!")

    app.add_action_to_plugin_menu("Hello World", "Open File", app.open_file_dialog) # demonstrating you can call functions from notepadpypp
    app.add_action_to_plugin_menu("Hello World", "About", lambda: about_box(app))

def about_box(parent):
    """Displays an about box."""
    QMessageBox.about(
        parent,
        "Hello World",
        "<h3><center>Hello World!</center></h3>"
        "<p>This is an example NotepadPypp plugin</p>"
        "<p>By Hotlands Software</p>"
    )
