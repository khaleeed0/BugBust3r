"""
Task queue using Celery for async job processing
"""
from celery import Celery
from app.core.config import settings
from app.db.database import SessionLocal
from app.services.scan_service import ScanService
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "security_scanner",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.task_routes = {
    'app.services.task_queue.execute_scan_task': {'queue': 'scans'},
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name='app.services.task_queue.execute_scan_task')
def execute_scan_task(job_id: int):
    """Celery task to execute a scan job"""
    db = SessionLocal()
    try:
        scan_service = ScanService(db)
        result = scan_service.execute_scan(job_id)
        logger.info(f"Scan task {job_id} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Scan task {job_id} failed: {e}")
        raise
    finally:
        db.close()


