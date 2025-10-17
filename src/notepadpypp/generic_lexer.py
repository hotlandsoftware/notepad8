from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
import re
import json
import os

class GenericLexer(QsciLexerCustom):
    """A generic lexer that can be configured via JSON files."""
    
    def __init__(self, parent=None, lang_name="Generic", config=None):
        super().__init__(parent)
        
        self.lang_name = lang_name
        self.config = config or {}
        
        self.DEFAULT = 0
        self.COMMENT = 1
        self.LINE_COMMENT = 2
        self.NUMBER = 3
        self.KEYWORD1 = 4
        self.KEYWORD2 = 5
        self.KEYWORD3 = 6
        self.KEYWORD4 = 7
        self.OPERATOR = 8
        self.STRING = 9
        self.STRING2 = 10
        self.PROPERTY = 11
        self.ERROR = 12
        
        self.style_names = {
            self.DEFAULT: "Default",
            self.COMMENT: "BlockComment",
            self.LINE_COMMENT: "LineComment",
            self.NUMBER: "Number",
            self.KEYWORD1: "Keyword1",
            self.KEYWORD2: "Keyword2",
            self.KEYWORD3: "Keyword3",
            self.KEYWORD4: "Keyword4",
            self.OPERATOR: "Operator",
            self.STRING: "String",
            self.STRING2: "String2",
            self.PROPERTY: "Property",
            self.ERROR: "Error"
        }
        
        self.keywords1 = set(self.config.get("keywords1", []))
        self.keywords2 = set(self.config.get("keywords2", []))
        self.keywords3 = set(self.config.get("keywords3", []))
        self.keywords4 = set(self.config.get("keywords4", []))
        self.operators = self.config.get("operators", [])
        self.string_delimiters = self.config.get("string_delimiters", ['"'])
        self.string2_delimiters = self.config.get("string2_delimiters", ["'"])
        self.line_comment = self.config.get("line_comment", "//")
        self.block_comment_start = self.config.get("block_comment_start", "/*")
        self.block_comment_end = self.config.get("block_comment_end", "*/")
        self.case_sensitive = self.config.get("case_sensitive", True)
        self.detect_numbers = self.config.get("detect_numbers", True)
        self.property_pattern = self.config.get("property_pattern", None)
        
        self.setDefaultFont(QFont("Courier New", 12))

    def language(self):
        return self.lang_name

    def description(self, style):
        return self.style_names.get(style, "")

    def styleText(self, start, end):
        editor = self.editor()
        if not editor:
            return

        full_text = editor.text()
        
        line_start = 0
        if start > 0:
            line_start = full_text.rfind('\n', 0, start)
            if line_start == -1:
                line_start = 0
            else:
                line_start += 1
        
        self.startStyling(line_start, 0xFF)
        
        i = line_start
        in_string = False
        in_string2 = False
        string_delimiter = None
        in_block_comment = False
        
        while i < len(full_text) and i < end:
            if not in_string and not in_string2 and self.block_comment_start:
                if full_text[i:i+len(self.block_comment_start)] == self.block_comment_start:
                    in_block_comment = True
                    comment_end = full_text.find(self.block_comment_end, i + len(self.block_comment_start))
                    if comment_end == -1:
                        comment_len = len(full_text) - i
                    else:
                        comment_len = comment_end - i + len(self.block_comment_end)
                    self.setStyling(comment_len, self.COMMENT)
                    i += comment_len
                    continue
            
            if not in_string and not in_string2 and self.line_comment:
                if full_text[i:i+len(self.line_comment)] == self.line_comment:
                    line_end = full_text.find('\n', i)
                    if line_end == -1:
                        line_end = len(full_text)
                    self.setStyling(line_end - i, self.LINE_COMMENT)
                    i = line_end
                    continue
            
            if full_text[i] in self.string_delimiters:
                if not in_string2:
                    if in_string and full_text[i] == string_delimiter:
                        if i > 0 and full_text[i-1] == '\\':
                            self.setStyling(1, self.STRING)
                            i += 1
                            continue
                        in_string = False
                        string_delimiter = None
                        
                        is_property = False
                        if self.property_pattern:
                            j = i + 1
                            while j < len(full_text) and full_text[j] in ' \t':
                                j += 1
                            if j < len(full_text) and full_text[j] == ':':
                                is_property = True
                        
                        self.setStyling(1, self.PROPERTY if is_property else self.STRING)
                    else:
                        in_string = True
                        string_delimiter = full_text[i]
                        
                        is_property = False
                        if self.property_pattern:
                            quote_end = full_text.find(string_delimiter, i + 1)
                            if quote_end != -1:
                                j = quote_end + 1
                                while j < len(full_text) and full_text[j] in ' \t':
                                    j += 1
                                if j < len(full_text) and full_text[j] == ':':
                                    is_property = True
                        
                        self.setStyling(1, self.PROPERTY if is_property else self.STRING)
                    i += 1
                    continue
            
            elif full_text[i] in self.string2_delimiters:
                if not in_string:
                    if in_string2 and full_text[i] == string_delimiter:
                        if i > 0 and full_text[i-1] == '\\':
                            self.setStyling(1, self.STRING2)
                            i += 1
                            continue
                        in_string2 = False
                        string_delimiter = None
                        self.setStyling(1, self.STRING2)
                    else:
                        in_string2 = True
                        string_delimiter = full_text[i]
                        self.setStyling(1, self.STRING2)
                    i += 1
                    continue
            
            if in_string:
                self.setStyling(1, self.STRING)
                i += 1
                continue
            elif in_string2:
                self.setStyling(1, self.STRING2)
                i += 1
                continue
            
            if self.detect_numbers and (full_text[i].isdigit() or 
                (full_text[i] == '-' and i < len(full_text) - 1 and full_text[i+1].isdigit())):
                num_match = re.match(r'-?\d+\.?\d*([eE][+-]?\d+)?', full_text[i:])
                if num_match:
                    num_len = len(num_match.group())
                    self.setStyling(num_len, self.NUMBER)
                    i += num_len
                    continue
            
            if full_text[i].isalpha() or full_text[i] == '_':
                word_match = re.match(r'[\w]+', full_text[i:])
                if word_match:
                    word = word_match.group()
                    word_len = len(word)
                    
                    word_check = word if self.case_sensitive else word.lower()
                    keywords_check1 = self.keywords1 if self.case_sensitive else {k.lower() for k in self.keywords1}
                    keywords_check2 = self.keywords2 if self.case_sensitive else {k.lower() for k in self.keywords2}
                    keywords_check3 = self.keywords3 if self.case_sensitive else {k.lower() for k in self.keywords3}
                    keywords_check4 = self.keywords4 if self.case_sensitive else {k.lower() for k in self.keywords4}
                    
                    if word_check in keywords_check1:
                        self.setStyling(word_len, self.KEYWORD1)
                    elif word_check in keywords_check2:
                        self.setStyling(word_len, self.KEYWORD2)
                    elif word_check in keywords_check3:
                        self.setStyling(word_len, self.KEYWORD3)
                    elif word_check in keywords_check4:
                        self.setStyling(word_len, self.KEYWORD4)
                    else:
                        self.setStyling(word_len, self.DEFAULT)
                    
                    i += word_len
                    continue
            
            matched_op = False
            for op in sorted(self.operators, key=len, reverse=True):
                if full_text[i:i+len(op)] == op:
                    self.setStyling(len(op), self.OPERATOR)
                    i += len(op)
                    matched_op = True
                    break
            
            if matched_op:
                continue
            
            self.setStyling(1, self.DEFAULT)
            i += 1