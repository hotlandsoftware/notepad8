import xml.etree.ElementTree as ET
import json
import os

class NotepadPlusPlusConverter:
    """Converts Notepad++ User Defined Language XML files to Notepad8 compatible JSON format."""
    
    def __init__(self):
        pass
    
    def convert_color(self, color_str):
        """Convert Notepad++ color format (BGR) to hex RGB."""
        if not color_str or color_str == "FFFFFF":
            return "#FFFFFF"
        
        if len(color_str) == 6:
            b = color_str[0:2]
            g = color_str[2:4]
            r = color_str[4:6]
            return f"#{r}{g}{b}".upper()
        return f"#{color_str}".upper()
    
    def parse_font_style(self, font_style_str):
        """Parse Notepad++ fontStyle attribute."""
        try:
            style = int(font_style_str or "0")
            return {
                "bold": style in (1, 3),
                "italic": style in (2, 3)
            }
        except:
            return {"bold": False, "italic": False}
    
    def convert_xml_to_json(self, xml_path, output_path=None):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            user_lang = root.find('.//UserLang')
            if user_lang is None:
                raise ValueError("UserLang element not found in XML")
            
            lang_name = user_lang.get('name', 'Unknown')
            extensions = user_lang.get('ext', '').split()
            extensions = [f".{ext}" if not ext.startswith('.') else ext for ext in extensions]
            
            settings = user_lang.find('.//Settings/Global')
            case_sensitive = settings.get('caseIgnored', 'yes').lower() != 'yes' if settings is not None else False
            
            keywords_elem = user_lang.find('.//KeywordLists')
            keywords1 = []
            keywords2 = []
            keywords3 = []
            keywords4 = []
            operators = []
            line_comment = ""
            block_comment_start = ""
            block_comment_end = ""
            string_delimiters = ['"']
            string2_delimiters = ["'"]
            
            if keywords_elem is not None:
                comments = keywords_elem.find('.//Keywords[@name="Comments"]')
                if comments is not None and comments.text:
                    comment_parts = comments.text.split()
                    if len(comment_parts) >= 2:
                        for i, part in enumerate(comment_parts):
                            if i == 0 and part != "00":
                                line_comment = part
                            elif i >= 2:
                                if comment_parts[i-1] == "03":
                                    block_comment_start = part
                                elif comment_parts[i-1] == "04":
                                    block_comment_end = part
                
                operators_elem = keywords_elem.find('.//Keywords[@name="Operators1"]')
                if operators_elem is not None and operators_elem.text:
                    operators = [op.strip() for op in operators_elem.text.split() if op.strip()]
                
                kw1 = keywords_elem.find('.//Keywords[@name="Keywords1"]')
                if kw1 is not None and kw1.text:
                    keywords1 = [kw.strip() for kw in kw1.text.split() if kw.strip()]
                
                kw2 = keywords_elem.find('.//Keywords[@name="Keywords2"]')
                if kw2 is not None and kw2.text:
                    keywords2 = [kw.strip() for kw in kw2.text.split() if kw.strip()]
                
                kw3 = keywords_elem.find('.//Keywords[@name="Keywords3"]')
                if kw3 is not None and kw3.text:
                    keywords3 = [kw.strip() for kw in kw3.text.split() if kw.strip()]
                
                kw4 = keywords_elem.find('.//Keywords[@name="Keywords4"]')
                if kw4 is not None and kw4.text:
                    keywords4 = [kw.strip() for kw in kw4.text.split() if kw.strip()]
            
            styles = {}
            styles_elem = user_lang.find('.//Styles')
            
            style_mapping = {
                'DEFAULT': 'Default',
                'COMMENTS': 'BlockComment',
                'LINE COMMENTS': 'LineComment',
                'NUMBERS': 'Number',
                'KEYWORDS1': 'Keyword1',
                'KEYWORDS2': 'Keyword2',
                'KEYWORDS3': 'Keyword3',
                'KEYWORDS4': 'Keyword4',
                'OPERATORS': 'Operator',
                'DELIMITERS1': 'String',
                'DELIMITERS2': 'String2',
            }
            
            if styles_elem is not None:
                for style_elem in styles_elem.findall('.//WordsStyle'):
                    npp_name = style_elem.get('name', '')
                    our_name = style_mapping.get(npp_name, npp_name)
                    
                    fg_color = self.convert_color(style_elem.get('fgColor', '000000'))
                    bg_color = self.convert_color(style_elem.get('bgColor', 'FFFFFF'))
                    font_style = self.parse_font_style(style_elem.get('fontStyle', '0'))
                    
                    styles[our_name] = {
                        'color': fg_color,
                        'background': bg_color,
                        'bold': font_style['bold'],
                        'italic': font_style['italic']
                    }
            
            config = {
                'name': lang_name,
                'extensions': extensions,
                'case_sensitive': case_sensitive,
                'detect_numbers': True,
                'line_comment': line_comment or '//',
                'block_comment_start': block_comment_start or '/*',
                'block_comment_end': block_comment_end or '*/',
                'string_delimiters': string_delimiters,
                'string2_delimiters': string2_delimiters,
                'property_pattern': False,
                'operators': operators,
                'keywords1': keywords1,
                'keywords2': keywords2,
                'keywords3': keywords3,
                'keywords4': keywords4,
                'styles': styles
            }
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                print(f"Converted {xml_path} to {output_path}")
            
            return config
            
        except Exception as e:
            print(f"Error converting {xml_path}: {e}")
            raise
    
    def convert_directory(self, input_dir, output_dir):
        """Convert all XML files in a directory."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        converted = []
        for filename in os.listdir(input_dir):
            if filename.endswith('.xml'):
                xml_path = os.path.join(input_dir, filename)
                json_filename = filename.replace('.xml', '_lang.json')
                json_path = os.path.join(output_dir, json_filename)
                
                try:
                    self.convert_xml_to_json(xml_path, json_path)
                    converted.append(json_filename)
                except Exception as e:
                    print(f"Failed to convert {filename}: {e}")
        
        return converted

if __name__ == "__main__":
    import sys
    
    converter = NotepadPlusPlusConverter()
    
    if len(sys.argv) < 2:
        print("USAGE:")
        print("python npp_converter.py input.xml [output.json] (converts a single fine)")
        print("python npp_converter.py -d input_dir output_dir (converts whole directory)")
        sys.exit(1)
    
    if sys.argv[1] == '-d':
        if len(sys.argv) < 4:
            print("Error: Directory conversion requires input and output directories!")
            sys.exit(1)
        converted = converter.convert_directory(sys.argv[2], sys.argv[3])
        print(f"Converted {len(converted)} files: {', '.join(converted)}")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.xml', '_lang.json')
        converter.convert_xml_to_json(input_file, output_file)