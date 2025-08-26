#!/usr/bin/env python3
"""
Database Schema Analysis Script
Checks current database schema and identifies missing columns
"""

import sqlite3
import os
from pathlib import Path

def check_database_schema():
    """Check current database schema and identify issues"""
    db_path = Path(__file__).parent / "docxp.db"
    
    if not db_path.exists():
        print(f"[ERROR] Database file not found: {db_path}")
        return False
    
    print(f"[OK] Database file found: {db_path}")
    print(f"[INFO] Database size: {db_path.stat().st_size} bytes")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n[INFO] Tables in database: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check documentation_jobs table specifically
        print("\n[INFO] DOCUMENTATION_JOBS Table Schema:")
        cursor.execute("PRAGMA table_info(documentation_jobs)")
        columns = cursor.fetchall()
        
        if not columns:
            print("[ERROR] documentation_jobs table does not exist!")
            return False
        
        existing_columns = {}
        for col in columns:
            cid, name, type_name, notnull, default_value, pk = col
            existing_columns[name] = {
                'type': type_name,
                'notnull': notnull,
                'default': default_value,
                'pk': pk
            }
            print(f"  {name}: {type_name} (notnull={notnull}, default={default_value}, pk={pk})")
        
        # Expected columns from the model
        expected_columns = {
            'id': 'INTEGER',
            'job_id': 'VARCHAR',
            'repository_path': 'VARCHAR',
            'status': 'VARCHAR',
            'created_at': 'DATETIME',
            'completed_at': 'DATETIME',
            'config': 'JSON',
            'progress_percentage': 'INTEGER',  # Missing
            'current_step': 'VARCHAR',        # Missing
            'step_description': 'VARCHAR',    # Missing
            'progress_data': 'JSON',          # Missing
            'entities_count': 'INTEGER',
            'business_rules_count': 'INTEGER',
            'files_processed': 'INTEGER',
            'output_path': 'VARCHAR',
            'processing_time_seconds': 'FLOAT',
            'error_message': 'TEXT'
        }
        
        # Check for missing columns
        missing_columns = []
        for col_name, col_type in expected_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"\n[ERROR] MISSING COLUMNS ({len(missing_columns)}):")
            for col_name, col_type in missing_columns:
                print(f"  - {col_name}: {col_type}")
        else:
            print("\n[OK] All expected columns are present!")
        
        # Check for any existing data
        cursor.execute("SELECT COUNT(*) FROM documentation_jobs")
        row_count = cursor.fetchone()[0]
        print(f"\n[INFO] Existing records: {row_count}")
        
        if row_count > 0:
            print("[INFO] Sample records:")
            cursor.execute("SELECT id, job_id, status, created_at FROM documentation_jobs LIMIT 3")
            for row in cursor.fetchall():
                print(f"  ID: {row[0]}, Job: {row[1]}, Status: {row[2]}, Created: {row[3]}")
        
        conn.close()
        return len(missing_columns) == 0
        
    except Exception as e:
        print(f"[ERROR] Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database_schema()