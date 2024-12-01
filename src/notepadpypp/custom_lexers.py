from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont

class BrainfuckLexer(QsciLexerCustom):
    Default = 0
    PointerOps = 1
    ArithmeticOps = 2
    LoopOps = 3
    IOOps = 4

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define styles
        self.setColor(QColor("#FFCC00"), self.PointerOps)  # Yellow
        self.setColor(QColor("#008000"), self.ArithmeticOps)  # Green
        self.setColor(QColor("#FF0000"), self.LoopOps)  # Red
        self.setColor(QColor("#0000FF"), self.IOOps)  # Blue
        self.setColor(QColor("#FFFFFF"), self.Default)  # White
        self.setPaper(QColor("#000000"), self.Default)  # Black background

        self.setDefaultFont(QFont("Courier New", 12))  # Fixed-width font

    def language(self):
        return "Brainfuck"

    def description(self, style):
        descriptions = {
            self.Default: "Default",
            self.PointerOps: "Pointer Operations",
            self.ArithmeticOps: "Arithmetic Operations",
            self.LoopOps: "Loop Operations",
            self.IOOps: "I/O Operations",
        }
        return descriptions.get(style, "")

    def styleText(self, start, end):
        editor = self.editor()
        if not editor:
            return

        text = editor.text()[start:end]
        print(f"Text to style: '{text}'")

        self.startStyling(start, 0xFF)

        for char in text:
            if char in "><":  # Pointer operations
                style = self.PointerOps
            elif char in "+-":  # Arithmetic operations
                style = self.ArithmeticOps
            elif char in "[]":  # Loop operations
                style = self.LoopOps
            elif char in ".,":  # I/O operations
                style = self.IOOps
            else:
                style = self.Default
            self.setStyling(1, style)
