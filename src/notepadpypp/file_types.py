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

from generic_lexer import GenericLexer
import json
import os


def load_generic_lexers():
    """Load all *_lang.json files from the lexer directory."""
    lexer_dir = os.path.join(os.path.dirname(__file__), "lexer")
    generic_lexers = {}
    
    if not os.path.exists(lexer_dir):
        return generic_lexers
    
    for filename in os.listdir(lexer_dir):
        if filename.endswith("_lang.json"):
            filepath = os.path.join(lexer_dir, filename)
            try:
                with open(filepath, "r") as f:
                    config = json.load(f)
                    lang_name = config.get("name", filename.replace("_lang.json", ""))
                    
                    def make_lexer_class(cfg, name):
                        class CustomGenericLexer(GenericLexer):
                            def __init__(self, parent=None):
                                super().__init__(parent, lang_name=name, config=cfg)
                        CustomGenericLexer.__name__ = f"{name}Lexer"
                        return CustomGenericLexer
                    
                    lexer_class = make_lexer_class(config, lang_name)
                    generic_lexers[lang_name] = {
                        "class": lexer_class,
                        "extensions": config.get("extensions", []),
                        "config": config
                    }
            except Exception as e:
                print(f"Failed to load generic lexer {filename}: {e}")
    
    return generic_lexers

GENERIC_LEXERS = load_generic_lexers()

DEFAULT_LEXER_TYPES = {
    ".asm": QsciLexerAsm,
    ".bat": QsciLexerBatch,
    # TODO: convert this
    #".b": BrainfuckLexer,
    #".bf": BrainfuckLexer,
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

for lang_name, lexer_info in GENERIC_LEXERS.items():
    for ext in lexer_info["extensions"]:
        DEFAULT_LEXER_TYPES[ext] = lexer_info["class"]

DEFAULT_LANGUAGES = {
    "Assembly (x86)": QsciLexerAsm,
    "Bash": QsciLexerBash,
    "Batch": QsciLexerBatch,
    #"Brainfuck": BrainfuckLexer,
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

for lang_name, lexer_info in GENERIC_LEXERS.items():
    DEFAULT_LANGUAGES[lang_name] = lexer_info["class"]

def get_lexer_for_file(file_name):
    for ext, lexer_class in DEFAULT_LEXER_TYPES.items():
        if file_name.endswith(ext):
            return lexer_class
    return None