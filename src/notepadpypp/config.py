import os
import json

def get_config_path():
    """Determines the configuration path, based on the OS"""
    if os.name == 'nt': # Windows
        appdata = os.getenv('APPDATA', os.path.expanduser("~\\AppData\\Roaming"))
        config_dir = os.path.join(appdata, "NotepadPypp")
    else: # unix
        home = os.path.expanduser("~")
        config_dir = os.path.join(home, "config", "NotepadPypp")

    os.makedirs(config_dir, exist_ok=True)

    return os.path.join(config_dir, "config.json")

CONFIG_PATH = get_config_path()

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
