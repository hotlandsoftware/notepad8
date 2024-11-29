#/bin/bash
pyinstaller --onefile --name "NotepadPypp" src/notepadpypp/main.py --hidden-import=PyQt6.Qsci