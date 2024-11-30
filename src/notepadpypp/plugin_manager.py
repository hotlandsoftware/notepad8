import os 
import json 
import importlib.util 

class PluginManager:
    def __init__(self, app, plugins_dir=None):
        """Initializes the PluginManager"""
        self.app = app 
        self.plugin_api = None
        self.plugins_dir = plugins_dir or self.get_plugins_dir()
        self.plugins = []

    def get_plugins_dir(self):
        """Retrieves the plugin directory path."""
        if os.name == 'nt': # Windows
            appdata = os.getenv('APPDATA', os.path.expanduser("~\\AppData\\Roaming"))
            plugins_dir = os.path.join(appdata, "NotepadPypp", "plugins")
        else: # linux/mac/whatever
            home = os.path.expanduser("~")
            plugins_dir = os.path.join(home, ".config", "NotepadPypp", "plugins")

        os.makedirs(plugins_dir, exist_ok=True)
        return plugins_dir

    # not working because its a piece of shit
    def load_plugins(self):
        """Loads plugins from the plugins directory."""
        print(f"Loading plugins from: {self.plugins_dir}")

        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            print(f"Plugins directory created at: {self.plugins_dir}")
            return  # No plugins to load

        for plugin_name in os.listdir(self.plugins_dir):
            print(f"Checking plugin: {plugin_name}")
            plugin_path = os.path.join(self.plugins_dir, plugin_name)

            if os.path.isdir(plugin_path):
                plugin_json_path = os.path.join(plugin_path, "plugin.json")
                if not os.path.exists(plugin_json_path):
                    print(f"Skipping {plugin_name}: No plugin.json found")
                    continue

                try:
                    with open(plugin_json_path, "r") as file:
                        plugin_metadata = json.load(file)
                        print(f"loaded metadata for {plugin_name}: {plugin_metadata}")
                except json.JSONDecodeError as e:
                    print(f"skipping {plugin_name} due to invalid plugin.json ({e})")
                    continue

                plugin_files = plugin_metadata.get("files", [])
                for file_name in plugin_files:
                    plugin_file_path = os.path.join(plugin_path, file_name)
                    print(f"checking file {file_name}")
                    if os.path.isfile(plugin_file_path):
                        print(f"loading file {file_name}")
                        self.load_plugin(plugin_file_path, plugin_metadata)
                    else:
                        print(f"file not found {file_name}")

    def load_plugin(self, file_path, metadata):
        """Loads a plugin."""
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "register"):
                module.register(self.plugin_api)
                self.plugins.append({
                    "metadata": metadata,
                    "module": module,
                })
                print(f"loaded plugin: {metadata['name']} by {metadata['author']} successfully!")
            else:
                print(f"skipping {metadata['name']}: (no 'register' function found)")
        except Exception as e:
            print(f"failed to load plugin {metadata['name']} {e}")

    def get_loaded_plugins(self):
        """Returns a list of loaded plugins, and their metadata."""
        return [plugin["metadata"] for plugin in self.plugins]