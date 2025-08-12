"""
Base parser interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any

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
