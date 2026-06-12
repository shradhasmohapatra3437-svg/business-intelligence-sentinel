from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Report

router = APIRouter()

@router.get("/api/reports")
def get_reports(
    limit: int = 20, 
    offset: int = 0, 
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Report).order_by(Report.created_at.desc())
    
    if risk_level:
        query = query.filter(Report.risk_level == risk_level)
        
    reports = query.offset(offset).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "title": r.title,
            "summary": r.summary,
            "risk_level": r.risk_level,
            "created_at": r.created_at.isoformat(),
            "run_id": r.run_id
        }
        for r in reports
    ]

@router.get("/api/reports/{report_id}")
def get_report_detail(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Also fetch the related job token usage if available
    token_usage = report.token_usage or {}
    
    return {
        "id": report.id,
        "title": report.title,
        "content_markdown": report.content_markdown,
        "summary": report.summary,
        "risk_level": report.risk_level,
        "key_findings": report.key_findings,
        "sources_used": report.sources_used,
        "token_usage": token_usage,
        "created_at": report.created_at.isoformat(),
        "run_id": report.run_id
    }
