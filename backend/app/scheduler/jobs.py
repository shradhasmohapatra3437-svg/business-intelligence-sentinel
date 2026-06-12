import logging
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.models import PipelineJob
from app.database import SessionLocal
from app.pipeline import run_pipeline

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def run_scheduled_pipeline():
    """Wrapper to run pipeline from APScheduler"""
    db = SessionLocal()
    try:
        # Check if already running
        active_job = db.query(PipelineJob).filter(PipelineJob.status == "running").first()
        if active_job:
            logger.warning(f"Scheduled run skipped: Pipeline already running (Job {active_job.id})")
            return
            
        job = PipelineJob(trigger_type="scheduled")
        db.add(job)
        db.commit()
        
        job_id = job.id
    except Exception as e:
        logger.error(f"Failed to create scheduled job record: {e}")
        return
    finally:
        db.close()
        
    try:
        # Run pipeline synchronously in this scheduler thread
        run_pipeline(job_id, "scheduled")
    except Exception as e:
        logger.error(f"Scheduled pipeline run failed: {e}")

def start_scheduler():
    """Start the APScheduler for local dev"""
    from app.config import settings
    # For local dev we just run it every 4 hours if left running
    # In prod, cron-job.org hits the /api/trigger endpoint
    scheduler.add_job(run_scheduled_pipeline, 'interval', hours=4, id='pipeline_job', replace_existing=True)
    scheduler.start()
    logger.info("APScheduler started (local dev mode)")
