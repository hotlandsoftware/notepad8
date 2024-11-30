import os 
import json 
import importlib.util 

class PluginManager:
    def __init__(self, app, plugins_dir="plugins"):
        """Initializes the PluginManager"""
        self.app = app 
        self.plugins_dir = plugins_dir 
        self.plugins = []

    def load_plugins(self):
        """Loads plugins from the plugins directory."""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)

        for plugin_name in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, plugin_name)
            if os.path.isdir(plugin_path):
                plugin_json_path = os.path.join(plugin_path, "plugin.json")
                if not os.path.exists(plugin_json_path):
                    print(f"not loading {plugin_name} due to missing plugin.json")
                    continue

                with open(plugin_json_path, "r") as file:
                    try:
                        plugin_metadata = json.load(file)
                    except json.JSONDecodeError:
                        print(f"not loading {plugin_name} due to invalid plugin.json")
                        continue

                for file_name in os.listdir(plugin_path):
                    if file_name.endswith(".py"):
                        plugin_file_path = os.path.join(plugin_path, file_name)
                        self.load_plugin(plugin_file_path, plugin_metadata)

    def load_plugin(self, file_path, metadata):
        """Loads a plugin."""
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "register"):
                module.register(self.app)
                self.plugins.append({
                    "metadata": metadata,
                    "module": module,
                })
                print(f"loaded plugin: {metadata['name']} by {metadata['author']} successfully!")
            else:
                print(f"skipping {metadata['name']}: no 'register' function found!")
        except Exception as e:
            print(f"Failed to load plugin {metadata['name']}: {e}")

    def get_loaded_plugins(self):
        """Returns a list of loaded plugins, and their metadata."""
        return [plugin["metadata"] for plugin in self.plugins]