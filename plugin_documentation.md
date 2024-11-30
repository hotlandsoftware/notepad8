# Plugin Documentation (wip)
Make a folder in the ``plugins`` folder with your plugin name

Create a plugin.json like this:
```
{
    "name": "Hello World",
    "author": "Hotlands Software",
    "description": "Hello World! A test of the Notepadpypp plugin system",
    "version": "1.0.0"
}
```

Then create a file named ``yourPluginName.py`` (can be anything) and define it like so:

```
def register(app):
    """Registers the application."""
    print("Hello World has been registered!")
```

## Tutorials
### Adding a submenu within the Plugins menu

Example of how to add a submenu into the Plugins menu:
```py
def register(app):
    """Registers the Hello World plugin."""
    print("Hello World plugin registered!")

    app.add_action_to_plugin_menu("Hello World", "Say Hello", lambda: print("Hello, World!"))
    app.add_action_to_plugin_menu("Hello World", "Open File", app.open_file_dialog)
```

### Adding a menu to the menu bar
Example of how to add a menu with an action:
```py
def register(app):
    plugin_menu = app.menuBar().addMenu("Hello World")
    plugin_action = plugin_menu.addAction("Test")
    plugin_action.triggered.connect(lambda: print("Plugin1 Action Triggered"))

    # or, for example, make it open the file dialog
    plugin_action.triggered.connect(app.open_file_dialog)
```