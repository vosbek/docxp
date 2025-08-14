"""
Database migration script to add missing columns
"""
import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add missing columns to documentation_jobs table"""
    
    # Find the database file
    db_path = "docxp.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found, checking other locations...")
        # Try common locations
        possible_paths = [
            "backend/docxp.db",
            "app/docxp.db",
            "../docxp.db"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        else:
            print("No database file found. Creating new database with proper schema.")
            return
    
    print(f"Found database at: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(documentation_jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add missing columns if they don't exist
        missing_columns = [
            ("progress_percentage", "INTEGER DEFAULT 0"),
            ("current_step", "TEXT"),
            ("step_description", "TEXT"),
            ("progress_data", "TEXT")  # JSON stored as TEXT in SQLite
        ]
        
        for column_name, column_def in missing_columns:
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE documentation_jobs ADD COLUMN {column_name} {column_def}"
                    print(f"Adding column: {sql}")
                    cursor.execute(sql)
                    print(f"✅ Added column {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print(f"⚠️  Column {column_name} already exists")
                    else:
                        print(f"❌ Error adding column {column_name}: {e}")
            else:
                print(f"✅ Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        print("✅ Database migration completed successfully!")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(documentation_jobs)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"Updated columns: {new_columns}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()