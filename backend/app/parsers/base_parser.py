"""
Base parser interface with robust file validation
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """Abstract base class for language parsers"""
    
    @abstractmethod
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse file and return list of entities"""
        pass
    
    @abstractmethod
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from file"""
        pass
    
    def create_entity(
        self,
        name: str,
        entity_type: str,
        file_path: str,
        line_number: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Create standard entity dictionary"""
        entity = {
            'name': name,
            'type': entity_type,
            'file_path': file_path,
            'line_number': line_number
        }
        entity.update(kwargs)
        return entity
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate if file exists and is readable"""
        try:
            if not file_path.exists():
                logger.debug(f"File does not exist: {file_path}")
                return False
                
            if not file_path.is_file():
                logger.debug(f"Path is not a file: {file_path}")
                return False
                
            if file_path.stat().st_size == 0:
                logger.debug(f"File is empty: {file_path}")
                return False
                
            # Try to read first few bytes to check readability
            try:
                with open(file_path, 'rb') as f:
                    f.read(10)
                return True
            except (OSError, PermissionError) as e:
                logger.debug(f"File not readable: {file_path}, error: {e}")
                return False
                
        except Exception as e:
            logger.debug(f"File validation failed for {file_path}: {e}")
            return False
    
    def validate_xml_content(self, file_path: Path) -> Optional[str]:
        """Validate XML file content and return content if valid"""
        try:
            if not self.validate_file(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
            
            if not content:
                logger.debug(f"XML file is empty or whitespace only: {file_path}")
                return None
            
            # Basic XML validation - must start with < and contain closing tag
            if not content.startswith('<'):
                logger.debug(f"XML file does not start with '<': {file_path}")
                return None
                
            # Check for basic XML structure
            if not ('>' in content and '</' in content):
                logger.debug(f"XML file lacks basic structure: {file_path}")
                return None
                
            return content
            
        except Exception as e:
            logger.debug(f"XML content validation failed for {file_path}: {e}")
            return None
    
    def read_file_safe(self, file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
        """Safely read file content with validation"""
        try:
            if not self.validate_file(file_path):
                return None
                
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
                
            if not content.strip():
                logger.debug(f"File is empty or whitespace only: {file_path}")
                return None
                
            return content
            
        except Exception as e:
            logger.debug(f"Safe file read failed for {file_path}: {e}")
            return None
