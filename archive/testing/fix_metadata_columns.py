#!/usr/bin/env python3
"""
Fix Reserved 'metadata' Column Names
Replace all 'metadata' columns with 'meta_data' to avoid SQLAlchemy conflicts
"""

import os
import re

def fix_metadata_in_file(file_path):
    """Fix metadata column references in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace Column declarations
    content = re.sub(r'metadata = Column\(JSON\)', 'meta_data = Column(JSON)', content)
    content = re.sub(r'metadata = Column\(JSON, default=\{\}\)', 'meta_data = Column(JSON, default={})', content)
    
    # Replace in Pydantic schemas
    content = re.sub(r'metadata: Optional\[Dict\[str, Any\]\] = \{\}', 'meta_data: Optional[Dict[str, Any]] = {}', content)
    content = re.sub(r'metadata: Optional\[Dict\[str, Any\]\] = None', 'meta_data: Optional[Dict[str, Any]] = None', content)
    content = re.sub(r'metadata: Dict\[str, Any\] = \{\}', 'meta_data: Dict[str, Any] = {}', content)
    
    # Replace in comments
    content = re.sub(r'# Metadata\n', '# Metadata\n', content)
    
    # Update references but keep some comments intact
    content = re.sub(r'"metadata":', '"meta_data":', content)
    content = re.sub(r"'metadata':", "'meta_data':", content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed metadata columns in: {file_path}")
        return True
    return False

def main():
    """Fix metadata columns in all model files"""
    model_files = [
        'app/models/business_rule_trace.py',
        'app/models/business_domains.py', 
        'app/models/architectural_insight.py',
        'app/models/project.py',
        'app/models/graph_entities.py'
    ]
    
    fixed_count = 0
    for file_path in model_files:
        if os.path.exists(file_path):
            if fix_metadata_in_file(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()