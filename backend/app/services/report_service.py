from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.property_profile import PropertyProfile
from app.models.report import Report


def create_report(db: Session, property_id: int, user_id: int = 1) -> Report:
    prop = db.query(Property).filter(Property.id == property_id).first()
    profile = db.query(PropertyProfile).filter(PropertyProfile.property_id == property_id).first()

    title = f"Property Report - {prop.address if prop else 'Unknown'}"
    content = {
        "summary": profile.analysis_payload.get("briefing", "No profile available.") if profile else "No profile available.",
        "verified_facts": profile.verified_payload if profile else {},
        "analysis": profile.analysis_payload if profile else {},
    }

    report = db.query(Report).filter(Report.property_id == property_id, Report.user_id == user_id).first()
    if not report:
        report = Report(user_id=user_id, property_id=property_id, title=title, content=content)
        db.add(report)
    else:
        report.title = title
        report.content = content

    db.commit()
    db.refresh(report)
    return report


def build_pdf_bytes(title: str, content: dict) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 72

    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, y, title)
    y -= 28

    pdf.setFont("Helvetica", 10)
    lines = [
        content.get("summary", ""),
        "",
        "Verified Facts:",
        str(content.get("verified_facts", {})),
        "",
        "Analysis:",
        str(content.get("analysis", {})),
    ]
    for line in lines:
        for chunk in str(line).split("\n"):
            if y < 72:
                pdf.showPage()
                y = height - 72
                pdf.setFont("Helvetica", 10)
            pdf.drawString(72, y, chunk[:110])
            y -= 14

    pdf.save()
    buffer.seek(0)
    return buffer.read()
