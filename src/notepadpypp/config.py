import os
import json

def get_config_path():
    """Determines the configuration path, based on the OS"""
    if os.name == 'nt': # Windows
        appdata = os.getenv('APPDATA', os.path.expanduser("~\\AppData\\Roaming"))
        config_dir = os.path.join(appdata, "NotepadPypp")
    else: # unix
        home = os.path.expanduser("~")
        config_dir = os.path.join(home, ".config", "NotepadPypp")

    os.makedirs(config_dir, exist_ok=True)

    return os.path.join(config_dir, "config.json")

CONFIG_PATH = get_config_path()

DEFAULT_CONFIG = {
    "debugMode": False, # Enable console debug mode
    "wordWrap": False, # Use word wrapping
    "wrapAroundSearch": False, # Search from top if not found on bottom in search (or vice versa)
    "useRegex": False, # Use regular expressions in search
    "restoreFilesOnClose": True, # Restore files upon closing
    "openNewTabOnLastClosed": True, # When closing the last tab, open a new tab to replicate Notepad++ behavior
    "lockTabs": False, # Add option to lock tabs
    "useQtDialogs": True, # For some reason KDE native dialogs won't work, so I added this option. Might be removed in future releases if I can fix the bug
    "window_size": [800, 600], # Window size
    "window_position": [100, 100], # Window position
    "scintillaConfig": {
        "color": "#ffffff", # background color
        "caret_color": "#e8e8ff", # highlight color
        "margins_color": "#e0e0e0", # margins color
        "font": "Courier New", # font
        "font_color": "#000", # font color
        "font_size": 12 # font size
    },
    "open_files": [] # open files
}

class Config:
    def __init__(self, config_path):
        self.config_path = config_path 
        self.data = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as file:
                    return json.load(file)
            except json.JSONDecodeError as e:
                print(f"failed to load config!: {e}")
                return DEFAULT_CONFIG 
        return DEFAULT_CONFIG 

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)
    
    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value 

    def add_open_file(self, file_path, is_modified=False, caret_position=(0, 0), lexer="None"):
        """Adds/updates open files in open_files."""
        for file_info in self.data["open_files"]:
            if file_info["file_path"] == file_path:
                file_info.update({
                    "is_modified": is_modified,
                    "caret_position": caret_position,
                    "lexer": lexer
                })
                break
        else:
            self.data["open_files"].append({
                "file_path": file_path,
                "is_modified": is_modified,
                "caret_position": caret_position,
                "lexer": lexer
            })
        
        self.save()

    def remove_open_file(self, file_path):
        """Removes files from open_files."""
        self.data["open_files"] = [
            file_info for file_info in self.data["open_files"] if file_info["file_path"] != file_path 
        ]
        self.save()

    def get_open_files(self):
        """Gets list of open files."""
        return self.data["open_files"]