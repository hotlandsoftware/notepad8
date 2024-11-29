import os
import json

# Get absolute path for the config file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "wordWrap": False,
    "wrapAroundSearch": False,
    "useRegex": False,
    "restoreFilesOnClose": True,
    "openNewTabOnLastClosed": True,
    "lockTabs": True,
    "scintillaConfig": {
        "color": "#ffffff",
        "caret_color": "#e8e8ff",
        "margins_color": "#c0c0c0",
        "font": "Courier New",
        "font_color": "#000",
        "font_size": 12
    },
    "open_files": []
}

def initialize_config():
    print("initializing configuration")
    if not os.path.exists(CONFIG_PATH):
        print("config file not found - creating it")
        with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump(DEFAULT_CONFIG, config_file, indent=4)

    # Load and return the configuration
    print("loading config from file")
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)

def save_config(config):
    print("saving config to file")
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)
