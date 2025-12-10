"""
FastAPI Main Application
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
from app.db.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable UUID extension and create database tables
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logging.info("Database connection successful and tables created")
except Exception as e:
    logging.warning(f"Could not connect to database or create tables: {e}")
    logging.warning("Server will start but database features will be unavailable")

app = FastAPI(
    title="Security Scanner API",
    description="On-demand security scanning with Docker tools",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Security Scanner API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

