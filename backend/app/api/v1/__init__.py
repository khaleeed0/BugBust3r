"""
API v1 router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, scans, jobs, reports, targets

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(targets.router, prefix="/targets", tags=["targets"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])


