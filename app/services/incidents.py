from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.db.models import Finding, Incident
from app.services.ai import explain_with_local_ai
from app.services.analyzer import analyze_log, summarize


async def create_incident(db: Session, title: str, source: str, log_text: str) -> Incident:
    results = analyze_log(log_text)
    ai_summary = await explain_with_local_ai(results)
    incident = Incident(title=title, source=source, raw_log=log_text,
                        summary=summarize(results), ai_summary=ai_summary)
    for result in results:
        incident.findings.append(Finding(
            rule_id=result.rule_id, category=result.category,
            evidence_line=result.evidence_line, evidence=result.evidence,
            explanation=result.explanation, verification=result.verification,
        ))
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def list_incidents(db: Session) -> list[Incident]:
    return list(db.scalars(select(Incident).order_by(Incident.id.desc()).limit(50)).all())


def get_incident(db: Session, incident_id: int) -> Incident | None:
    return db.scalar(select(Incident).options(selectinload(Incident.findings)).where(Incident.id == incident_id))
