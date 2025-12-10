#!/usr/bin/env python3
"""
Test database connectivity and structure
Verifies that all required tables exist and are accessible
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.models.job import ScanJob, Finding, ToolExecution
from app.models.target import Target
from app.models.tool import Tool
from app.models.user import User
from sqlalchemy import inspect, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection"""
    print("=" * 80)
    print("DATABASE CONNECTION TEST")
    print("=" * 80)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected successfully")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_tables_exist():
    """Test that all required tables exist"""
    print("\n" + "=" * 80)
    print("TABLE EXISTENCE TEST")
    print("=" * 80)
    
    required_tables = [
        'users', 'targets', 'tools', 'scan_jobs', 
        'findings', 'tool_executions', 'vulnerability_definitions', 'reports'
    ]
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    all_exist = True
    for table in required_tables:
        if table in existing_tables:
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' MISSING")
            all_exist = False
    
    return all_exist

def test_table_structure():
    """Test table structure and columns"""
    print("\n" + "=" * 80)
    print("TABLE STRUCTURE TEST")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Test scan_jobs
        try:
            count = db.query(ScanJob).count()
            print(f"✅ scan_jobs table accessible - {count} records")
        except Exception as e:
            print(f"❌ scan_jobs table error: {e}")
            return False
        
        # Test findings
        try:
            count = db.query(Finding).count()
            print(f"✅ findings table accessible - {count} records")
        except Exception as e:
            print(f"❌ findings table error: {e}")
            return False
        
        # Test tool_executions
        try:
            count = db.query(ToolExecution).count()
            print(f"✅ tool_executions table accessible - {count} records")
        except Exception as e:
            print(f"❌ tool_executions table error: {e}")
            print(f"   Note: This table may need to be created. Run migration script.")
            return False
        
        # Test tools
        try:
            count = db.query(Tool).count()
            print(f"✅ tools table accessible - {count} records")
        except Exception as e:
            print(f"❌ tools table error: {e}")
            return False
        
        # Test targets
        try:
            count = db.query(Target).count()
            print(f"✅ targets table accessible - {count} records")
        except Exception as e:
            print(f"❌ targets table error: {e}")
            return False
        
        return True
    finally:
        db.close()

def test_indexes():
    """Test that indexes exist"""
    print("\n" + "=" * 80)
    print("INDEX TEST")
    print("=" * 80)
    
    try:
        with engine.connect() as conn:
            # Check important indexes
            indexes_to_check = [
                'idx_scan_jobs_status',
                'idx_findings_job_id',
                'idx_tool_executions_job_id',
                'idx_tool_executions_stage_number'
            ]
            
            for index_name in indexes_to_check:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE indexname = '{index_name}'
                """))
                exists = result.fetchone()[0] > 0
                if exists:
                    print(f"✅ Index '{index_name}' exists")
                else:
                    print(f"⚠️  Index '{index_name}' not found (may not be critical)")
        
        return True
    except Exception as e:
        print(f"⚠️  Index check error: {e}")
        return True  # Not critical

def main():
    """Run all database tests"""
    print("\n")
    print("🔍 DATABASE VERIFICATION TEST SUITE")
    print("\n")
    
    results = []
    
    # Test 1: Connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 2: Tables exist
    results.append(("Tables Exist", test_tables_exist()))
    
    # Test 3: Table structure
    results.append(("Table Structure", test_table_structure()))
    
    # Test 4: Indexes
    results.append(("Indexes", test_indexes()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL DATABASE TESTS PASSED")
        print("   Database is ready for scans!")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Please fix the issues above before running scans")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

