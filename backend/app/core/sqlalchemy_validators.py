"""
SQLAlchemy Reserved Word Validation Utility
Prevents using reserved words in SQLAlchemy models and provides alternatives
"""

import logging
from typing import List, Dict, Set, Any
import inspect
from sqlalchemy.orm import DeclarativeMeta

logger = logging.getLogger(__name__)

# Comprehensive list of SQLAlchemy and database reserved words
SQLALCHEMY_RESERVED_WORDS = {
    # SQLAlchemy Core reserved attributes
    'metadata', 'registry', 'mapper', 'class_registry', 
    
    # SQLAlchemy ORM reserved attributes  
    '__mapper__', '__table__', '__tablename__', '__mapper_args__',
    '__table_args__', '__abstract__', '__mapper_cls__',
    
    # Common SQL reserved words that can cause issues
    'select', 'insert', 'update', 'delete', 'from', 'where', 'join',
    'inner', 'outer', 'left', 'right', 'on', 'as', 'table', 'column',
    'index', 'primary', 'foreign', 'key', 'constraint', 'unique',
    'not', 'null', 'default', 'check', 'references', 'cascade',
    
    # Python reserved words that can cause confusion
    'class', 'def', 'if', 'else', 'elif', 'for', 'while', 'try',
    'except', 'finally', 'with', 'as', 'import', 'from', 'lambda',
    'return', 'yield', 'raise', 'assert', 'del', 'pass', 'break',
    'continue', 'global', 'nonlocal', 'and', 'or', 'not', 'in', 'is',
    
    # Common problematic field names
    'type', 'id', 'name', 'value', 'data', 'info', 'config'
}

# Suggested alternatives for common reserved words
ALTERNATIVE_SUGGESTIONS = {
    'metadata': ['entity_metadata', 'meta_data', 'properties', 'attributes'],
    'type': ['entity_type', 'record_type', 'item_type', 'category'],
    'id': ['entity_id', 'record_id', 'identifier', 'pk'],
    'data': ['entity_data', 'content', 'payload', 'information'],
    'config': ['configuration', 'settings', 'options', 'params'],
    'info': ['information', 'details', 'meta_info', 'properties'],
    'name': ['entity_name', 'display_name', 'title', 'label'],
    'value': ['entity_value', 'content_value', 'data_value', 'amount'],
    'class': ['entity_class', 'classification', 'category', 'group'],
    'table': ['data_table', 'table_name', 'table_ref', 'relation'],
    'column': ['column_name', 'field_name', 'attribute', 'property'],
    'select': ['selection', 'query_select', 'choose', 'pick'],
    'update': ['modification', 'change', 'revision', 'edit'],
    'delete': ['removal', 'deletion', 'destroy', 'remove'],
    'insert': ['addition', 'creation', 'new_record', 'add']
}

class SQLAlchemyValidator:
    """Validates SQLAlchemy models for reserved word usage"""
    
    def __init__(self):
        self.reserved_words = SQLALCHEMY_RESERVED_WORDS
        self.alternatives = ALTERNATIVE_SUGGESTIONS
    
    def validate_model(self, model_class: DeclarativeMeta) -> Dict[str, Any]:
        """Validate a single SQLAlchemy model for reserved word usage"""
        issues = []
        suggestions = []
        
        # Check class name
        if model_class.__name__.lower() in self.reserved_words:
            issues.append(f"Class name '{model_class.__name__}' is a reserved word")
            suggestions.append(f"Consider renaming to '{model_class.__name__}Model' or '{model_class.__name__}Entity'")
        
        # Check table name
        if hasattr(model_class, '__tablename__'):
            table_name = model_class.__tablename__
            if table_name.lower() in self.reserved_words:
                issues.append(f"Table name '{table_name}' is a reserved word")
                suggestions.append(f"Consider renaming table to '{table_name}_table' or '{table_name}_data'")
        
        # Check column names
        if hasattr(model_class, '__table__'):
            for column in model_class.__table__.columns:
                column_name = column.name
                if column_name.lower() in self.reserved_words:
                    issues.append(f"Column name '{column_name}' is a reserved word")
                    if column_name.lower() in self.alternatives:
                        alts = self.alternatives[column_name.lower()]
                        suggestions.append(f"For '{column_name}', consider: {', '.join(alts)}")
                    else:
                        suggestions.append(f"For '{column_name}', consider: {column_name}_value, {column_name}_data, entity_{column_name}")
        
        return {
            'model_name': model_class.__name__,
            'table_name': getattr(model_class, '__tablename__', None),
            'issues': issues,
            'suggestions': suggestions,
            'is_valid': len(issues) == 0
        }
    
    def validate_all_models(self, base_class: DeclarativeMeta) -> Dict[str, Any]:
        """Validate all models that inherit from the given base class"""
        results = []
        total_issues = 0
        
        # Find all model classes
        for cls in base_class.registry.mappers:
            model_class = cls.class_
            validation_result = self.validate_model(model_class)
            results.append(validation_result)
            total_issues += len(validation_result['issues'])
        
        return {
            'total_models': len(results),
            'total_issues': total_issues,
            'models': results,
            'is_valid': total_issues == 0
        }
    
    def check_reserved_word(self, word: str) -> Dict[str, Any]:
        """Check if a single word is reserved and get suggestions"""
        word_lower = word.lower()
        is_reserved = word_lower in self.reserved_words
        
        suggestions = []
        if is_reserved and word_lower in self.alternatives:
            suggestions = self.alternatives[word_lower]
        elif is_reserved:
            suggestions = [f"{word}_value", f"{word}_data", f"entity_{word}"]
        
        return {
            'word': word,
            'is_reserved': is_reserved,
            'suggestions': suggestions
        }
    
    def generate_validation_report(self, base_class: DeclarativeMeta) -> str:
        """Generate a comprehensive validation report"""
        results = self.validate_all_models(base_class)
        
        report_lines = []
        report_lines.append("SQLAlchemy Reserved Word Validation Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Total Models: {results['total_models']}")
        report_lines.append(f"Total Issues: {results['total_issues']}")
        report_lines.append(f"Overall Status: {'PASSED' if results['is_valid'] else 'FAILED'}")
        report_lines.append("")
        
        if results['total_issues'] > 0:
            report_lines.append("Issues Found:")
            report_lines.append("-" * 20)
            
            for model_result in results['models']:
                if model_result['issues']:
                    report_lines.append(f"\nModel: {model_result['model_name']}")
                    report_lines.append(f"Table: {model_result['table_name']}")
                    
                    for issue in model_result['issues']:
                        report_lines.append(f"  ❌ {issue}")
                    
                    for suggestion in model_result['suggestions']:
                        report_lines.append(f"  💡 {suggestion}")
        else:
            report_lines.append("✅ No reserved word conflicts found!")
        
        return "\n".join(report_lines)

# Global validator instance
validator = SQLAlchemyValidator()

def validate_model(model_class: DeclarativeMeta) -> Dict[str, Any]:
    """Validate a single model for reserved words"""
    return validator.validate_model(model_class)

def validate_all_models(base_class: DeclarativeMeta) -> Dict[str, Any]:
    """Validate all models for reserved words"""
    return validator.validate_all_models(base_class)

def check_word(word: str) -> Dict[str, Any]:
    """Check if a word is reserved"""
    return validator.check_reserved_word(word)

def generate_report(base_class: DeclarativeMeta) -> str:
    """Generate validation report"""
    return validator.generate_validation_report(base_class)

# Usage example:
if __name__ == "__main__":
    # This would be used to validate models
    print("SQLAlchemy Reserved Word Validator")
    print("Usage:")
    print("  from app.core.sqlalchemy_validators import validate_all_models, generate_report")
    print("  from app.core.database import Base")
    print("  print(generate_report(Base))")