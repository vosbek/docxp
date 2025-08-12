"""
Python language parser using AST
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class PythonParser(BaseParser):
    """Parser for Python source files"""
    
    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Python file and extract entities"""
        entities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    entity = self._extract_class(node, str(file_path))
                    entities.append(entity)
                
                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions (not methods)
                    if not self._is_method(node, tree):
                        entity = self._extract_function(node, str(file_path))
                        entities.append(entity)
        
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
        
        return entities
    
    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract import statements from Python file"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
        
        except Exception as e:
            logger.warning(f"Error extracting dependencies from {file_path}: {e}")
        
        return list(set(dependencies))

    
    def _extract_class(self, node: ast.ClassDef, file_path: str) -> Dict[str, Any]:
        """Extract class information"""
        methods = []
        properties = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        properties.append(target.id)
        
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr)
        
        return self.create_entity(
            name=node.name,
            entity_type='class',
            file_path=file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            methods=methods,
            properties=properties,
            dependencies=bases,
            complexity=self._calculate_class_complexity(node)
        )
    
    def _extract_function(self, node: ast.FunctionDef, file_path: str) -> Dict[str, Any]:
        """Extract function information"""
        parameters = []
        
        for arg in node.args.args:
            parameters.append(arg.arg)
        
        return self.create_entity(
            name=node.name,
            entity_type='function',
            file_path=file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            complexity=self._calculate_complexity(node),
            is_async=isinstance(node, ast.AsyncFunctionDef)
        )
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        """Check if function is a method inside a class"""
        for item in ast.walk(tree):
            if isinstance(item, ast.ClassDef):
                for class_item in item.body:
                    if class_item == node:
                        return True
        return False
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_class_complexity(self, node: ast.ClassDef) -> int:
        """Calculate complexity of a class"""
        total_complexity = 0
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                total_complexity += self._calculate_complexity(item)
        
        return total_complexity
