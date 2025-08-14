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
        """Extract comprehensive class information including implementation details"""
        methods = []
        properties = []
        class_methods = []
        static_methods = []
        
        # Enhanced method analysis
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    'name': item.name,
                    'line': item.lineno,
                    'is_private': item.name.startswith('_'),
                    'is_magic': item.name.startswith('__') and item.name.endswith('__'),
                    'has_decorators': bool(item.decorator_list),
                    'parameter_count': len(item.args.args),
                    'complexity': self._calculate_complexity(item)
                }
                
                # Check for class/static method decorators
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id == 'classmethod':
                            class_methods.append(method_info)
                        elif decorator.id == 'staticmethod':
                            static_methods.append(method_info)
                        elif decorator.id == 'property':
                            properties.append({
                                'name': item.name,
                                'type': 'property',
                                'line': item.lineno
                            })
                
                methods.append(method_info)
                
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        properties.append({
                            'name': target.id,
                            'type': 'class_attribute',
                            'line': item.lineno,
                            'is_private': target.id.startswith('_')
                        })
        
        # Extract base classes with more detail
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append({'name': base.id, 'type': 'class'})
            elif isinstance(base, ast.Attribute):
                full_name = f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr
                bases.append({'name': full_name, 'type': 'class'})
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(f"{decorator.value.id}.{decorator.attr}" if isinstance(decorator.value, ast.Name) else decorator.attr)
        
        # Enhanced class analysis
        class_analysis = self._analyze_class_implementation(node, file_path)
        
        return self.create_entity(
            name=node.name,
            entity_type='class',
            file_path=file_path,
            line_number=node.lineno,
            end_line_number=node.end_lineno if hasattr(node, 'end_lineno') else None,
            docstring=ast.get_docstring(node),
            methods=methods,
            properties=properties,
            class_methods=class_methods,
            static_methods=static_methods,
            base_classes=bases,
            decorators=decorators,
            complexity=self._calculate_class_complexity(node),
            **class_analysis
        )
    
    def _analyze_class_implementation(self, node: ast.ClassDef, file_path: str) -> Dict[str, Any]:
        """Analyze class implementation for architectural patterns"""
        analysis = {
            'design_patterns': self._detect_design_patterns(node),
            'is_data_class': self._is_data_class(node),
            'is_abstract_class': self._is_abstract_class(node),
            'has_constructor': self._has_constructor(node),
            'constructor_complexity': self._analyze_constructor(node),
            'method_distribution': self._analyze_method_distribution(node),
            'inheritance_depth': len(node.bases),
            'interface_methods': self._extract_interface_methods(node)
        }
        
        return analysis
    
    def _detect_design_patterns(self, node: ast.ClassDef) -> List[str]:
        """Detect common design patterns in class"""
        patterns = []
        
        # Singleton pattern detection
        if self._has_singleton_pattern(node):
            patterns.append('Singleton')
        
        # Factory pattern detection
        if self._has_factory_pattern(node):
            patterns.append('Factory')
        
        # Observer pattern detection  
        if self._has_observer_pattern(node):
            patterns.append('Observer')
        
        # Builder pattern detection
        if self._has_builder_pattern(node):
            patterns.append('Builder')
        
        return patterns
    
    def _is_data_class(self, node: ast.ClassDef) -> bool:
        """Check if class appears to be a data class"""
        # Look for dataclass decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                return True
        
        # Heuristic: mostly properties/attributes, few methods
        method_count = sum(1 for item in node.body if isinstance(item, ast.FunctionDef))
        attr_count = sum(1 for item in node.body if isinstance(item, ast.Assign))
        
        return attr_count > method_count and method_count <= 3
    
    def _is_abstract_class(self, node: ast.ClassDef) -> bool:
        """Check if class is abstract"""
        # Look for ABC inheritance
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ['ABC', 'AbstractBase']:
                return True
            elif isinstance(base, ast.Attribute) and base.attr in ['ABC', 'AbstractBase']:
                return True
        
        # Look for abstract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and 'abstract' in decorator.id:
                        return True
        
        return False
    
    def _has_constructor(self, node: ast.ClassDef) -> bool:
        """Check if class has a constructor"""
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                return True
        return False
    
    def _analyze_constructor(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze constructor complexity and patterns"""
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                return {
                    'parameter_count': len(item.args.args) - 1,  # Exclude self
                    'complexity': self._calculate_complexity(item),
                    'has_validation': self._has_parameter_validation(item),
                    'has_default_values': bool(item.args.defaults)
                }
        
        return {'parameter_count': 0, 'complexity': 0, 'has_validation': False, 'has_default_values': False}
    
    def _analyze_method_distribution(self, node: ast.ClassDef) -> Dict[str, int]:
        """Analyze method distribution"""
        distribution = {
            'public_methods': 0,
            'private_methods': 0,
            'magic_methods': 0,
            'property_methods': 0
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.startswith('__') and item.name.endswith('__'):
                    distribution['magic_methods'] += 1
                elif item.name.startswith('_'):
                    distribution['private_methods'] += 1
                else:
                    distribution['public_methods'] += 1
                    
                # Check for property decorator
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'property':
                        distribution['property_methods'] += 1
        
        return distribution
    
    def _extract_interface_methods(self, node: ast.ClassDef) -> List[Dict[str, Any]]:
        """Extract public interface methods"""
        interface_methods = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                interface_methods.append({
                    'name': item.name,
                    'parameter_count': len(item.args.args) - 1,  # Exclude self
                    'has_docstring': bool(ast.get_docstring(item)),
                    'returns_value': self._method_returns_value(item)
                })
        
        return interface_methods
    
    # Helper methods for pattern detection
    def _has_singleton_pattern(self, node: ast.ClassDef) -> bool:
        """Detect singleton pattern"""
        has_instance_attr = False
        has_new_method = False
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and 'instance' in target.id.lower():
                        has_instance_attr = True
            elif isinstance(item, ast.FunctionDef) and item.name == '__new__':
                has_new_method = True
        
        return has_instance_attr or has_new_method
    
    def _has_factory_pattern(self, node: ast.ClassDef) -> bool:
        """Detect factory pattern"""
        factory_methods = ['create', 'build', 'make', 'get_instance', 'factory']
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name.lower()
                if any(factory_term in method_name for factory_term in factory_methods):
                    return True
        
        return False
    
    def _has_observer_pattern(self, node: ast.ClassDef) -> bool:
        """Detect observer pattern"""
        observer_methods = ['notify', 'update', 'subscribe', 'unsubscribe', 'add_observer', 'remove_observer']
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.lower() in observer_methods:
                    return True
        
        return False
    
    def _has_builder_pattern(self, node: ast.ClassDef) -> bool:
        """Detect builder pattern"""
        has_build_method = False
        has_with_methods = 0
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.lower() in ['build', 'create']:
                    has_build_method = True
                elif item.name.startswith('with_') or item.name.startswith('set_'):
                    has_with_methods += 1
        
        return has_build_method and has_with_methods > 2
    
    def _has_parameter_validation(self, method_node: ast.FunctionDef) -> bool:
        """Check if method has parameter validation"""
        for child in ast.walk(method_node):
            if isinstance(child, ast.If):
                # Simple heuristic: if statements in constructor often indicate validation
                return True
        return False
    
    def _method_returns_value(self, method_node: ast.FunctionDef) -> bool:
        """Check if method returns a value"""
        for child in ast.walk(method_node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False
    
    def _extract_function(self, node: ast.FunctionDef, file_path: str) -> Dict[str, Any]:
        """Extract comprehensive function information including implementation details"""
        parameters = []
        
        for arg in node.args.args:
            parameters.append(arg.arg)
        
        # Extract enhanced implementation details
        implementation_analysis = self._analyze_function_implementation(node, file_path)
        
        return self.create_entity(
            name=node.name,
            entity_type='function',
            file_path=file_path,
            line_number=node.lineno,
            end_line_number=node.end_lineno if hasattr(node, 'end_lineno') else None,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            complexity=self._calculate_complexity(node),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            **implementation_analysis
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
    
    def _analyze_function_implementation(self, node: ast.FunctionDef, file_path: str) -> Dict[str, Any]:
        """Analyze function implementation for business logic patterns and detailed context"""
        analysis = {
            'source_code': self._extract_source_code(node, file_path),
            'business_logic_patterns': self._extract_business_logic_patterns(node),
            'exception_handling': self._analyze_exception_handling(node),
            'variable_assignments': self._extract_variable_assignments(node),
            'function_calls': self._extract_function_calls(node),
            'return_statements': self._analyze_return_statements(node),
            'conditional_logic': self._analyze_conditional_logic(node),
            'loop_constructs': self._analyze_loop_constructs(node),
            'decorators': self._extract_decorators(node),
            'type_hints': self._extract_type_hints(node)
        }
        
        return analysis
    
    def _extract_source_code(self, node: ast.FunctionDef, file_path: str) -> str:
        """Extract the source code of the function"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            start_line = node.lineno - 1  # Convert to 0-based indexing
            end_line = getattr(node, 'end_lineno', start_line + 10) if hasattr(node, 'end_lineno') else start_line + 10
            
            if start_line < len(lines) and end_line <= len(lines):
                source_lines = lines[start_line:end_line]
                return ''.join(source_lines).strip()
            
            return ""
        except Exception as e:
            logger.debug(f"Could not extract source code for {node.name} in {file_path}: {e}")
            return ""
    
    def _extract_business_logic_patterns(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract business logic patterns from function"""
        patterns = []
        
        for child in ast.walk(node):
            # Validation patterns
            if isinstance(child, ast.If) and self._is_validation_pattern(child):
                patterns.append({
                    'type': 'validation',
                    'line': child.lineno,
                    'description': self._describe_validation_pattern(child)
                })
            
            # Calculation patterns
            elif isinstance(child, (ast.BinOp, ast.AugAssign)) and self._is_calculation_pattern(child):
                patterns.append({
                    'type': 'calculation',
                    'line': child.lineno,
                    'description': self._describe_calculation_pattern(child)
                })
            
            # State transition patterns
            elif isinstance(child, ast.Assign) and self._is_state_transition(child):
                patterns.append({
                    'type': 'state_transition',
                    'line': child.lineno,
                    'description': self._describe_state_transition(child)
                })
        
        return patterns
    
    def _analyze_exception_handling(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze exception handling patterns"""
        try_blocks = []
        exception_types = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                handlers = []
                for handler in child.handlers:
                    exception_type = 'Exception'
                    if handler.type:
                        if isinstance(handler.type, ast.Name):
                            exception_type = handler.type.id
                        elif isinstance(handler.type, ast.Attribute):
                            exception_type = f"{handler.type.value.id}.{handler.type.attr}"
                    
                    exception_types.add(exception_type)
                    handlers.append({
                        'exception_type': exception_type,
                        'line': handler.lineno,
                        'has_custom_handling': len(handler.body) > 1 or not isinstance(handler.body[0], ast.Pass)
                    })
                
                try_blocks.append({
                    'line': child.lineno,
                    'handlers': handlers,
                    'has_finally': bool(child.finalbody),
                    'has_else': bool(child.orelse)
                })
        
        return {
            'try_blocks_count': len(try_blocks),
            'exception_types': list(exception_types),
            'try_blocks': try_blocks
        }
    
    def _extract_variable_assignments(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract variable assignments that might represent business logic"""
        assignments = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assignments.append({
                            'variable': target.id,
                            'line': child.lineno,
                            'type': 'assignment',
                            'is_business_relevant': self._is_business_relevant_assignment(child)
                        })
                    elif isinstance(target, ast.Attribute):
                        assignments.append({
                            'variable': f"{target.value.id}.{target.attr}" if isinstance(target.value, ast.Name) else target.attr,
                            'line': child.lineno,
                            'type': 'attribute_assignment',
                            'is_business_relevant': self._is_business_relevant_assignment(child)
                        })
        
        return assignments
    
    def _extract_function_calls(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract function calls to understand dependencies"""
        calls = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_info = self._analyze_function_call(child)
                if call_info:
                    calls.append(call_info)
        
        return calls
    
    def _analyze_return_statements(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze return statements"""
        returns = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                return_type = 'None'
                return_description = 'void'
                
                if child.value:
                    if isinstance(child.value, ast.Constant):
                        return_type = type(child.value.value).__name__
                        return_description = f"constant: {child.value.value}"
                    elif isinstance(child.value, ast.Name):
                        return_type = 'variable'
                        return_description = f"variable: {child.value.id}"
                    elif isinstance(child.value, ast.Dict):
                        return_type = 'dict'
                        return_description = "dictionary"
                    elif isinstance(child.value, ast.List):
                        return_type = 'list'
                        return_description = "list"
                
                returns.append({
                    'line': child.lineno,
                    'type': return_type,
                    'description': return_description
                })
        
        return {
            'return_count': len(returns),
            'returns': returns,
            'has_multiple_returns': len(returns) > 1
        }
    
    def _analyze_conditional_logic(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Analyze conditional logic that might represent business rules"""
        conditions = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                condition_info = {
                    'line': child.lineno,
                    'has_else': bool(child.orelse),
                    'is_business_logic': self._is_business_logic_condition(child)
                }
                conditions.append(condition_info)
        
        return conditions
    
    def _analyze_loop_constructs(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Analyze loop constructs"""
        loops = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.For):
                loops.append({
                    'type': 'for',
                    'line': child.lineno,
                    'has_else': bool(child.orelse)
                })
            elif isinstance(child, ast.While):
                loops.append({
                    'type': 'while',
                    'line': child.lineno,
                    'has_else': bool(child.orelse)
                })
        
        return loops
    
    def _extract_decorators(self, node: ast.FunctionDef) -> List[str]:
        """Extract function decorators"""
        decorators = []
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(f"{decorator.value.id}.{decorator.attr}" if isinstance(decorator.value, ast.Name) else decorator.attr)
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                decorators.append(f"{decorator.func.id}()")
        
        return decorators
    
    def _extract_type_hints(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract type hints from function signature"""
        type_hints = {
            'return_type': None,
            'parameter_types': {}
        }
        
        # Return type annotation
        if node.returns:
            if isinstance(node.returns, ast.Name):
                type_hints['return_type'] = node.returns.id
            elif isinstance(node.returns, ast.Constant):
                type_hints['return_type'] = str(node.returns.value)
        
        # Parameter type annotations
        for arg in node.args.args:
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    type_hints['parameter_types'][arg.arg] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    type_hints['parameter_types'][arg.arg] = str(arg.annotation.value)
        
        return type_hints
    
    # Helper methods for pattern recognition
    def _is_validation_pattern(self, if_node: ast.If) -> bool:
        """Check if an if statement represents a validation pattern"""
        # Look for common validation patterns
        test = if_node.test
        
        if isinstance(test, ast.Compare):
            # Look for None checks, length checks, type checks
            return True
        elif isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            # Look for "not" conditions which often represent validation
            return True
        elif isinstance(test, ast.Call):
            # Look for validation function calls
            return True
        
        return False
    
    def _is_calculation_pattern(self, node: ast.AST) -> bool:
        """Check if a node represents a calculation pattern"""
        if isinstance(node, ast.BinOp):
            return isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod))
        return False
    
    def _is_state_transition(self, assign_node: ast.Assign) -> bool:
        """Check if an assignment represents a state transition"""
        # Look for assignments to status, state, or similar attributes
        for target in assign_node.targets:
            if isinstance(target, ast.Attribute):
                attr_name = target.attr.lower()
                if any(keyword in attr_name for keyword in ['status', 'state', 'mode', 'phase']):
                    return True
        return False
    
    def _is_business_relevant_assignment(self, assign_node: ast.Assign) -> bool:
        """Check if an assignment is business-relevant"""
        # Simple heuristic: assignments involving calculations or business terms
        if isinstance(assign_node.value, (ast.BinOp, ast.Call)):
            return True
        
        # Look for business-relevant variable names
        for target in assign_node.targets:
            if isinstance(target, ast.Name):
                name = target.id.lower()
                business_terms = ['total', 'amount', 'price', 'cost', 'fee', 'rate', 'discount', 'tax', 'balance']
                if any(term in name for term in business_terms):
                    return True
        
        return False
    
    def _analyze_function_call(self, call_node: ast.Call) -> Dict[str, Any]:
        """Analyze a function call"""
        call_info = {'line': call_node.lineno}
        
        if isinstance(call_node.func, ast.Name):
            call_info['function'] = call_node.func.id
            call_info['type'] = 'function_call'
        elif isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                call_info['function'] = f"{call_node.func.value.id}.{call_node.func.attr}"
                call_info['type'] = 'method_call'
        
        call_info['arg_count'] = len(call_node.args) + len(call_node.keywords)
        
        return call_info
    
    def _is_business_logic_condition(self, if_node: ast.If) -> bool:
        """Determine if a conditional represents business logic"""
        # Simple heuristic based on complexity and context
        return True  # For now, consider all conditions as potentially business-relevant
    
    def _describe_validation_pattern(self, if_node: ast.If) -> str:
        """Describe a validation pattern"""
        return "Input validation or constraint check"
    
    def _describe_calculation_pattern(self, node: ast.AST) -> str:
        """Describe a calculation pattern"""
        if isinstance(node, ast.BinOp):
            op_name = type(node.op).__name__
            return f"Mathematical operation: {op_name}"
        return "Calculation"
    
    def _describe_state_transition(self, assign_node: ast.Assign) -> str:
        """Describe a state transition"""
        return "State or status change"
