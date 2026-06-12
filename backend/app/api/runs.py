from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PipelineJob

router = APIRouter()

@router.get("/api/runs")
def get_runs(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    runs = (db.query(PipelineJob)
            .order_by(PipelineJob.started_at.desc().nullslast())
            .offset(offset).limit(limit).all())
            
    return [
        {
            "id": r.id,
            "status": r.status,
            "trigger_type": r.trigger_type,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "duration_seconds": r.duration_seconds,
            "total_tokens": r.total_tokens,
            "model_used": r.model_used
        }
        for r in runs
    ]

@router.get("/api/runs/{run_id}")
def get_run_detail(run_id: str, db: Session = Depends(get_db)):
    run = db.query(PipelineJob).filter(PipelineJob.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return {
        "id": run.id,
        "status": run.status,
        "trigger_type": run.trigger_type,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "duration_seconds": run.duration_seconds,
        "error_message": run.error_message,
        "total_tokens": run.total_tokens,
        "model_used": run.model_used
    }
