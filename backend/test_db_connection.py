"""Test database connection and tables"""
from app.db.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Check connection
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Database connected!")
        print(f"   PostgreSQL: {version.split(',')[0]}")
        
        # Check tables
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        ))
        table_count = result.fetchone()[0]
        print(f"✅ Tables in database: {table_count}")
        
        # List tables
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result.fetchall()]
        if tables:
            print(f"   Tables: {', '.join(tables)}")
        else:
            print("   No tables found yet")
        
except Exception as e:
    print(f"❌ Database connection error: {e}")

