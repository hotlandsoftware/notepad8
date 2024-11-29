import os
import json

# Get absolute path for the config file (TODO: change this to the tmp directory instead)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "wordWrap": False, # Use word wrapping
    "wrapAroundSearch": False, # Search from top if not found on bottom in search (or vice versa)
    "useRegex": False, # Use regular expressions in search
    "restoreFilesOnClose": True, # Restore files upon closing
    "openNewTabOnLastClosed": True, # When closing the last tab, open a new tab to replicate Notepad++ behavior
    "lockTabs": True, # Add option to lock tabs
    "useQtDialogs": True, # For some reason KDE native dialogs won't work, so I added this option. Might be removed in future releases if I can fix the bug
    "scintillaConfig": {
        "color": "#ffffff", # background color
        "caret_color": "#e8e8ff", # highlight color
        "margins_color": "#c0c0c0", # margins color
        "font": "Courier New", # font
        "font_color": "#000", # font color
        "font_size": 12 # font size
    },
    "open_files": [] # open files
}

def initialize_config():
    print("initializing configuration")
    if not os.path.exists(CONFIG_PATH):
        print("config file not found - creating it")
        with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump(DEFAULT_CONFIG, config_file, indent=4)

    print("loading config from file")
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)

def save_config(config):
    print("saving config to file")
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)
