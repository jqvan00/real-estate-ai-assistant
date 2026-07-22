from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.report import Report
from app.schemas.report import ReportOut
from app.services.report_service import build_pdf_bytes, create_report

router = APIRouter()


@router.post("/{property_id}", response_model=ReportOut)
def build_report(property_id: int, db: Session = Depends(get_db)):
    report = create_report(db, property_id)
    return ReportOut(id=report.id, title=report.title, content=report.content)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportOut(id=report.id, title=report.title, content=report.content)


@router.get("/{report_id}/pdf")
def download_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    pdf_bytes = build_pdf_bytes(report.title, report.content)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
    )
