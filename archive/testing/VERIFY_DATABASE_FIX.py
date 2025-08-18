#!/usr/bin/env python3
"""
VERIFICATION SCRIPT FOR DATABASE FIX
Quick test to verify the database schema is correct
"""

import sqlite3
import os
import json
from datetime import datetime

def verify_database():
    """Verify database schema and test basic operations"""
    
    print("🔍 VERIFYING DATABASE SCHEMA")
    print("="*40)
    
    db_path = "docxp.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documentation_jobs'")
        if not cursor.fetchone():
            print("❌ documentation_jobs table not found!")
            return False
        
        # Check all required columns exist
        cursor.execute("PRAGMA table_info(documentation_jobs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = [
            'id', 'job_id', 'repository_path', 'status', 'created_at', 'completed_at',
            'config', 'progress_percentage', 'current_step', 'step_description', 
            'progress_data', 'entities_count', 'business_rules_count', 
            'files_processed', 'output_path', 'processing_time_seconds', 'error_message'
        ]
        
        missing = [col for col in required_columns if col not in column_names]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
        
        print("✅ All required columns present!")
        print(f"   Columns: {column_names}")
        
        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM documentation_jobs")
        count = cursor.fetchone()[0]
        print(f"✅ Database query test passed! ({count} jobs)")
        
        # Test the problematic columns specifically
        cursor.execute("SELECT progress_percentage, current_step, step_description FROM documentation_jobs LIMIT 1")
        print("✅ Progress tracking columns accessible!")
        
        conn.close()
        
        print("\n🎉 DATABASE VERIFICATION SUCCESSFUL!")
        print("✅ Your database is ready for DocXP application")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_database()
    if success:
        print("\n✅ Ready to start DocXP application!")
    else:
        print("\n❌ Database needs to be fixed first!")
        print("Run: python CRITICAL_DATABASE_FIX.py")