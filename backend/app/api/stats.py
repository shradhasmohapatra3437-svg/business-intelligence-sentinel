from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import PipelineJob, Report

router = APIRouter()

@router.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_runs = db.query(func.count(PipelineJob.id)).scalar() or 0
    successful_runs = db.query(func.count(PipelineJob.id)).filter(PipelineJob.status == "complete").scalar() or 0
    
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    avg_duration = db.query(func.avg(PipelineJob.duration_seconds)).filter(PipelineJob.status == "complete").scalar() or 0
    
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    
    # Last 14 runs for cost tracker
    recent_runs = (db.query(PipelineJob)
                   .filter(PipelineJob.status == "complete")
                   .order_by(PipelineJob.finished_at.desc())
                   .limit(14).all())
                   
    token_usage_history = []
    for r in recent_runs:
        if r.report and r.report.token_usage:
            usage = r.report.token_usage
            token_usage_history.append({
                "date": r.finished_at.strftime("%Y-%m-%d %H:%M") if r.finished_at else "",
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "model": r.model_used
            })
            
    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "success_rate": round(success_rate, 1),
        "avg_duration_seconds": round(avg_duration, 1),
        "total_reports": total_reports,
        "token_usage_history": token_usage_history
    }
