#!/bin/bash

PYQT6_PATH=$(python -c "import PyQt6; import os; print(os.path.dirname(PyQt6.__file__))")
QSCI_PATH=$(python -c "import PyQt6.Qsci; import os; print(os.path.dirname(PyQt6.Qsci.__file__))")

echo "PyQt6 path: $PYQT6_PATH"
echo "QScintilla path: $QSCI_PATH"

pyinstaller --name "NotepadPypp" \
    --hidden-import=PyQt6.Qsci \
    --collect-all PyQt6.Qsci \
    src/notepadpypp/main.py
