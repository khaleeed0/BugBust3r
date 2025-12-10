#!/usr/bin/env python3
"""
Diagnostic script to check database connection and scan job issues
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.core.config import settings
from app.models.job import ScanJob, JobStatus
from app.models.target import Target
from app.models.user import User
from sqlalchemy import text, inspect, func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check database connection"""
    print("=" * 80)
    print("DATABASE CONNECTION CHECK")
    print("=" * 80)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected")
            print(f"   Connection string: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'hidden'}")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Connection string: {settings.DATABASE_URL}")
        return False

def check_tables():
    """Check if all required tables exist"""
    print("\n" + "=" * 80)
    print("TABLE CHECK")
    print("=" * 80)
    
    required_tables = [
        'users', 'targets', 'tools', 'scan_jobs',
        'findings', 'tool_executions', 'vulnerability_definitions'
    ]
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    all_exist = True
    for table in required_tables:
        if table in existing_tables:
            print(f"✅ {table}")
        else:
            print(f"❌ {table} - MISSING")
            all_exist = False
    
    return all_exist

def check_target_issue():
    """Check for target URL uniqueness issues"""
    print("\n" + "=" * 80)
    print("TARGET URL UNIQUENESS CHECK")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Check for duplicate URLs
        from sqlalchemy import func
        duplicates = db.query(
            Target.url,
            func.count(Target.id).label('count'),
            func.array_agg(Target.user_id).label('user_ids')
        ).group_by(Target.url).having(func.count(Target.id) > 1).all()
        
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} URLs with multiple targets:")
            for url, count, user_ids in duplicates:
                print(f"   {url}: {count} targets (users: {user_ids})")
            return False
        else:
            print("✅ No duplicate URLs found")
            return True
    except Exception as e:
        print(f"⚠️  Could not check duplicates: {e}")
        return True
    finally:
        db.close()

def check_scan_jobs():
    """Check scan job status and errors"""
    print("\n" + "=" * 80)
    print("SCAN JOB CHECK")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Count jobs by status
        jobs_by_status = db.query(
            ScanJob.status,
            func.count(ScanJob.id).label('count')
        ).group_by(ScanJob.status).all()
        
        print("Jobs by status:")
        for status, count in jobs_by_status:
            print(f"   {status}: {count}")
        
        # Check for stuck jobs
        from datetime import datetime, timedelta
        stuck_jobs = db.query(ScanJob).filter(
            ScanJob.status == JobStatus.RUNNING.value,
            ScanJob.created_at < datetime.utcnow() - timedelta(hours=2)
        ).all()
        
        if stuck_jobs:
            print(f"\n⚠️  Found {len(stuck_jobs)} potentially stuck jobs:")
            for job in stuck_jobs:
                print(f"   Job {job.job_id}: Running since {job.created_at}")
        
        # Check recent failed jobs
        recent_failed = db.query(ScanJob).filter(
            ScanJob.status == JobStatus.FAILED.value
        ).order_by(ScanJob.created_at.desc()).limit(5).all()
        
        if recent_failed:
            print(f"\n⚠️  Recent failed jobs: {len(recent_failed)}")
            for job in recent_failed:
                target = db.query(Target).filter(Target.id == job.target_id).first()
                print(f"   Job {job.job_id}: {target.url if target else 'Unknown'} - Failed at {job.completed_at}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking scan jobs: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def check_celery_connection():
    """Check Celery/Redis connection"""
    print("\n" + "=" * 80)
    print("CELERY/REDIS CHECK")
    print("=" * 80)
    
    try:
        import redis
        from urllib.parse import urlparse
        parsed = urlparse(settings.REDIS_URL)
        r = redis.Redis(host=parsed.hostname or 'localhost', port=parsed.port or 6379)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"   Redis URL: {settings.REDIS_URL}")
        return False

def main():
    """Run all diagnostics"""
    print("\n")
    print("🔍 DIAGNOSTIC CHECK")
    print("\n")
    
    results = []
    
    results.append(("Database Connection", check_database_connection()))
    results.append(("Tables", check_tables()))
    results.append(("Target URLs", check_target_issue()))
    results.append(("Scan Jobs", check_scan_jobs()))
    results.append(("Celery/Redis", check_celery_connection()))
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print("\n" + "=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

