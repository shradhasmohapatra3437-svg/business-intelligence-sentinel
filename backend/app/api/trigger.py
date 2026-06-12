from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PipelineJob
from app.pipeline import run_pipeline

router = APIRouter()

@router.post("/api/trigger")
def trigger_pipeline(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger the pipeline asynchronously. 
    Returns a job_id immediately for the frontend to poll.
    """
    # Check if a job is already running
    active_job = db.query(PipelineJob).filter(PipelineJob.status == "running").first()
    if active_job:
        raise HTTPException(status_code=409, detail=f"Pipeline is already running (Job ID: {active_job.id})")
        
    # Create new job
    job = PipelineJob(trigger_type="manual")
    db.add(job)
    db.commit()
    
    # Enqueue pipeline run
    background_tasks.add_task(run_pipeline, job.id, "manual")
    
    return {
        "job_id": job.id,
        "status": "pending",
        "message": "Pipeline triggered successfully"
    }
