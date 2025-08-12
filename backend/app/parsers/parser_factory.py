"""
Parser factory for selecting appropriate language parsers
"""

from pathlib import Path
from typing import Optional

from app.parsers.python_parser import PythonParser
from app.parsers.base_parser import BaseParser

class ParserFactory:
    """Factory for creating language-specific parsers"""
    
    def __init__(self):
        self.parsers = {
            '.py': PythonParser(),
            # Add more parsers as implemented
            # '.java': JavaParser(),
            # '.js': JavaScriptParser(),
            # '.ts': TypeScriptParser(),
            # '.pl': PerlParser(),
        }
    
    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Get appropriate parser for file"""
        extension = file_path.suffix.lower()
        return self.parsers.get(extension)
    
    def is_supported(self, file_path: Path) -> bool:
        """Check if file type is supported"""
        return file_path.suffix.lower() in self.parsers
