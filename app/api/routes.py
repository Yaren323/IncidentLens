from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_session
from app.services.incidents import create_incident, get_incident, list_incidents

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "ai_enabled": settings.ai_enabled}


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_session)):
    return request.app.state.templates.TemplateResponse(
        request=request, name="index.html", context={"incidents": list_incidents(db)}
    )


@router.post("/incidents")
async def submit_incident(
    title: str = Form(..., min_length=3, max_length=180),
    source: str = Form(...),
    log_file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    if source not in {"linux", "windows", "other"}:
        raise HTTPException(400, "Geçersiz kaynak")
    content = await log_file.read(settings.max_log_bytes + 1)
    if not content or len(content) > settings.max_log_bytes:
        raise HTTPException(400, "Log dosyası boş veya izin verilen boyuttan büyük")
    if not (log_file.filename or "").lower().endswith((".txt", ".log")):
        raise HTTPException(400, "Yalnızca .txt ve .log dosyaları desteklenir")
    try:
        log_text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "UTF-8 metin dosyası gerekli")
    incident = await create_incident(db, title.strip(), source, log_text)
    return RedirectResponse(f"/incidents/{incident.id}", status_code=303)


@router.get("/incidents/{incident_id}", response_class=HTMLResponse)
def incident_detail(incident_id: int, request: Request, db: Session = Depends(get_session)):
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(404, "Olay bulunamadı")
    return request.app.state.templates.TemplateResponse(
        request=request, name="detail.html", context={"incident": incident}
    )
