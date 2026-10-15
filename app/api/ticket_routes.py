"""HTML endpoints for the guided support workflow."""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.services.classifier import predict
from app.services.knowledge import GUIDES
from app.services.tickets import (OutOfScope, create_ticket, discard_ticket, get_ticket,
                                  history_matches, list_resolved, resolve_ticket)

router = APIRouter()

def render(request, name, **context):
    return request.app.state.templates.TemplateResponse(request=request, name=name, context=context)

@router.get('/', response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_session)):
    return render(request, 'ticket_home.html', tickets=list_resolved(db), error=None)

@router.post('/tickets', response_class=HTMLResponse)
def submit(request: Request, title: str = Form(...), db: Session = Depends(get_session)):
    try:
        ticket = create_ticket(db, title)
    except OutOfScope as exc:
        return render(request, 'ticket_home.html', tickets=list_resolved(db), error=str(exc), previous_title=title[:240])
    return RedirectResponse(f'/tickets/{ticket.id}', status_code=303)

@router.get('/tickets/{ticket_id}', response_class=HTMLResponse)
def detail(ticket_id: int, request: Request, db: Session = Depends(get_session)):
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(404, 'Ticket bulunamadı')
    options = [GUIDES[option.guide_id] for option in sorted(ticket.options, key=lambda o: o.rank)]
    matches = history_matches(db, ticket.title, ticket.category, ticket.target)
    return render(request, 'ticket_detail.html', ticket=ticket, options=options, matches=matches, guides=GUIDES)

@router.post('/tickets/{ticket_id}/resolve')
def resolve(ticket_id: int, guide_id: str = Form(...), notes: str = Form(''), db: Session = Depends(get_session)):
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(404, 'Ticket bulunamadı')
    try:
        resolve_ticket(db, ticket, guide_id, notes)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return RedirectResponse(f'/tickets/{ticket_id}', status_code=303)

@router.post('/tickets/{ticket_id}/discard')
def discard(ticket_id: int, db: Session = Depends(get_session)):
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(404, 'Ticket bulunamadı')
    try:
        discard_ticket(db, ticket)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return RedirectResponse('/', status_code=303)

@router.get('/health')
def health():
    return {'status': 'ok', 'ai_mode': 'local_machine_learning', 'paid_api': False}
