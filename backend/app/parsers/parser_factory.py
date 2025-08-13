"""
Parser factory for selecting appropriate language parsers
"""

from pathlib import Path
from typing import Optional

from app.parsers.python_parser import PythonParser
from app.parsers.angular_parser import AngularParser
from app.parsers.struts_parser import StrutsParser
from app.parsers.struts2_parser import Struts2Parser
from app.parsers.corba_parser import CorbaParser
from app.parsers.base_parser import BaseParser

class ParserFactory:
    """Factory for creating language-specific parsers"""
    
    def __init__(self):
        # Initialize parsers
        self.python_parser = PythonParser()
        self.angular_parser = AngularParser()
        self.struts_parser = StrutsParser()
        self.struts2_parser = Struts2Parser()
        self.corba_parser = CorbaParser()
        
        # Map file extensions to parsers
        self.parsers = {
            '.py': self.python_parser,
            '.ts': self.angular_parser,
            '.idl': self.corba_parser,
            # Java files might be Struts, Struts2, or regular Java
            '.java': self.struts2_parser,  # Default to Struts2 for Java
            '.xml': self.struts2_parser,   # struts.xml configuration
            '.jsp': self.struts2_parser,   # JSP files with Struts tags
        }
        
        # Additional mappings for specific frameworks
        self.framework_patterns = {
            'struts-config.xml': self.struts_parser,
            'struts.xml': self.struts2_parser,
            'struts2.xml': self.struts2_parser,
            '*.component.ts': self.angular_parser,
            '*.service.ts': self.angular_parser,
            '*.module.ts': self.angular_parser,
        }
    
    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Get appropriate parser for file"""
        
        # Check specific framework patterns first
        for pattern, parser in self.framework_patterns.items():
            if '*' in pattern:
                # Handle wildcard patterns
                pattern_suffix = pattern.replace('*', '')
                if str(file_path).endswith(pattern_suffix):
                    return parser
            elif file_path.name == pattern:
                return parser
        
        # Check file content for framework indicators if Java file
        if file_path.suffix == '.java':
            parser = self._detect_java_framework(file_path)
            if parser:
                return parser
        
        # Fall back to extension-based selection
        extension = file_path.suffix.lower()
        return self.parsers.get(extension)
    
    def _detect_java_framework(self, file_path: Path) -> Optional[BaseParser]:
        """Detect which Java framework is used in the file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 100 lines for framework detection
                lines = []
                for i, line in enumerate(f):
                    if i >= 100:
                        break
                    lines.append(line)
                content = ''.join(lines)
            
            # Check for Struts2 indicators
            if any(indicator in content for indicator in [
                'extends ActionSupport',
                'import org.apache.struts2',
                '@Action',
                '@Result',
                'com.opensymphony.xwork2'
            ]):
                return self.struts2_parser
            
            # Check for Struts1 indicators
            if any(indicator in content for indicator in [
                'extends Action',
                'import org.apache.struts.action',
                'extends DispatchAction',
                'import javax.servlet.http.HttpServletRequest'
            ]):
                return self.struts_parser
            
            # Default to Struts2 for Java files
            return self.struts2_parser
            
        except Exception:
            # If we can't read the file, default to Struts2
            return self.struts2_parser
    
    def is_supported(self, file_path: Path) -> bool:
        """Check if file type is supported"""
        # Check specific patterns
        for pattern in self.framework_patterns:
            if '*' in pattern:
                pattern_suffix = pattern.replace('*', '')
                if str(file_path).endswith(pattern_suffix):
                    return True
            elif file_path.name == pattern:
                return True
        
        # Check extensions
        return file_path.suffix.lower() in self.parsers
