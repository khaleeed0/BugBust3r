"""
Initialize database tables and create UUID extension
"""
from sqlalchemy import text
from app.db.database import engine, Base
from app.models.user import User
from app.models.target import Target
from app.models.tool import Tool
from app.models.job import ScanJob, ScanSchedule, VulnerabilityDefinition, Finding, Report

if __name__ == "__main__":
    # Enable UUID extension
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
