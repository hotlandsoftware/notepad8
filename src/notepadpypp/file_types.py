from PyQt6.Qsci import (
    QsciLexerPython, QsciLexerJava, QsciLexerJavaScript, QsciLexerLua, 
    QsciLexerHTML, QsciLexerJSON, QsciLexerCSS, QsciLexerCSharp, 
    QsciLexerBash, QsciLexerBatch, QsciLexerCMake, QsciLexerAsm, 
    QsciLexerCoffeeScript, QsciLexerCPP, QsciLexerD, QsciLexerDiff, 
    QsciLexerFortran, QsciLexerFortran77, QsciLexerMakefile, 
    QsciLexerMarkdown, QsciLexerMASM, QsciLexerOctave, QsciLexerPascal, 
    QsciLexerPerl, QsciLexerPostScript, QsciLexerRuby, QsciLexerMatlab, 
    QsciLexerXML, QsciLexerYAML
)

from custom_lexers import ( 
    BrainfuckLexer
)

LEXER_TYPES = {
    ".asm": QsciLexerAsm,
    ".bat": QsciLexerBatch,
    ".b": BrainfuckLexer,
    ".bf": BrainfuckLexer,
    ".cmake": QsciLexerCMake,
    ".cmd": QsciLexerBatch,
    ".C": QsciLexerCPP,
    ".cc": QsciLexerCPP,
    ".cpp": QsciLexerCPP,
    ".cxx": QsciLexerCPP,
    ".c++": QsciLexerCPP,
    ".h": QsciLexerCPP,
    ".H": QsciLexerCPP,
    ".hh": QsciLexerCPP,
    ".hpp": QsciLexerCPP,
    ".hxx": QsciLexerCPP,
    ".h++": QsciLexerCPP,
    ".cppm": QsciLexerCPP,
    ".ixx": QsciLexerCPP,
    ".coffee": QsciLexerCoffeeScript,
    ".litcoffee": QsciLexerCoffeeScript,
    ".css": QsciLexerCSS,
    ".cs": QsciLexerCSharp,
    ".d": QsciLexerD,
    ".diff": QsciLexerDiff,
    ".patch": QsciLexerDiff,
    ".f90": QsciLexerFortran,
    ".f": QsciLexerFortran,
    ".for": QsciLexerFortran,
    ".f77": QsciLexerFortran77,
    ".htm": QsciLexerHTML,
    ".html": QsciLexerHTML,
    ".java": QsciLexerJava,
    ".js": QsciLexerJavaScript,
    ".json": QsciLexerJSON,
    ".makefile": QsciLexerMakefile,
    ".md": QsciLexerMarkdown,
    ".m": QsciLexerMatlab,
    ".p": QsciLexerMatlab,
    ".lua": QsciLexerLua,
    ".pas": QsciLexerPascal,
    ".plx": QsciLexerPerl,
    ".pls": QsciLexerPerl,
    ".pl": QsciLexerPerl,
    ".pm": QsciLexerPerl,
    ".xs": QsciLexerPerl,
    ".t": QsciLexerPerl,
    ".pod": QsciLexerPerl,
    ".cgi": QsciLexerPerl,
    ".psgi": QsciLexerPerl,
    ".py": QsciLexerPython,
    ".ps": QsciLexerPostScript,
    ".xml": QsciLexerXML,
    ".yaml": QsciLexerYAML
}

LANGUAGES = {
    "Assembly (x86)": QsciLexerAsm,
    "Bash": QsciLexerBash,
    "Batch": QsciLexerBatch,
    "Brainfuck": BrainfuckLexer,
    "CMake": QsciLexerCMake,
    "C#": QsciLexerCSharp,
    "C++": QsciLexerCPP,
    "CoffeeScript": QsciLexerCoffeeScript,
    "CSS": QsciLexerCSS,
    "D": QsciLexerD,
    "Diff": QsciLexerDiff,
    "Fortran": QsciLexerFortran,
    "Fortran '77": QsciLexerFortran77,
    "HTML": QsciLexerHTML,
    "Java": QsciLexerJava,
    "JavaScript": QsciLexerJavaScript,
    "JSON": QsciLexerJSON,
    "Lua": QsciLexerLua,
    "Makefile": QsciLexerMakefile,
    "Markdown": QsciLexerMarkdown,
    "MASM": QsciLexerMASM,
    "Matlab": QsciLexerMatlab,
    "Pascal": QsciLexerPascal,
    "Perl": QsciLexerPerl,
    "PostScript": QsciLexerPostScript,
    "Python": QsciLexerPython,
    "Ruby": QsciLexerRuby,
    "XML": QsciLexerXML,
    "YAML": QsciLexerYAML
}

def get_lexer_for_file(file_name):
    for ext, lexer_class in LEXER_TYPES.items():
        if file_name.endswith(ext):
            return lexer_class
    return None
