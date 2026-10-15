"""Ticket lifecycle, trusted historical retrieval, and guide selection."""
from datetime import datetime, timezone
from difflib import SequenceMatcher
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.db.tickets import Ticket, TicketOption
from app.services.classifier import predict
from app.services.knowledge import CATEGORY_GUIDES, GUIDES

class OutOfScope(ValueError):
    pass

def history_matches(db: Session, title: str, category: str, target: str):
    """Find resolved tickets by technical tokens and wording similarity."""
    import re
    import unicodedata

    stopwords = {
        'bir', 've', 'ile', 'icin', 'gibi', 'olan', 'olarak', 'hatasi',
        'hata', 'aliyorum', 'alindi', 'sorun', 'sorunu', 'servisi',
        'servis', 'baslatilamiyor', 'baslamiyor', 'calismiyor',
        'tarafindan', 'kullaniliyor', 'kullanildigi', 'baska',
        'ortaminda', 'ortamda', 'test', 'uygulama', 'uygulamasi',
        'numarali', 'numara', 'portu', 'port', 'sunucu', 'sunucuda',
        'the', 'and', 'from', 'error', 'failed', 'cannot', 'connection',
    }

    def tokens(value: str):
        value = unicodedata.normalize('NFKD', value.casefold())
        value = ''.join(ch for ch in value if not unicodedata.combining(ch))
        return {word for word in re.findall(r'[a-z0-9]+', value)
                if len(word) >= 2 and word not in stopwords}

    past = db.scalars(
        select(Ticket)
        .options(selectinload(Ticket.options))
        .where(Ticket.state == 'resolved', Ticket.category == category)
        .order_by(Ticket.id.desc())
        .limit(100)
    ).all()

    current_tokens = tokens(title)
    matches = []
    for ticket in past:
        if target and ticket.target and target != ticket.target:
            continue
        old_tokens = tokens(ticket.title)
        shared = current_tokens & old_tokens
        overlap = len(shared) / max(1, min(len(current_tokens), len(old_tokens)))
        wording = SequenceMatcher(None, title.casefold(), ticket.title.casefold()).ratio()
        same_target = bool(target and ticket.target and target == ticket.target)

        # Require meaningful shared terms to avoid matching only by category.
        if len(shared) >= 2 and (overlap >= 0.50 or wording >= 0.68):
            score = max(overlap, wording)
        elif same_target and len(shared) >= 1 and wording >= 0.45:
            score = max(0.90, wording)
        else:
            continue
        matches.append((score, ticket))

    return [ticket for _, ticket in sorted(matches, key=lambda item: item[0], reverse=True)[:3]]

def create_ticket(db: Session, title: str) -> Ticket:
    prediction = predict(title)
    if prediction is None:
        raise OutOfScope('Talep tanınan BT altyapısı kapsamına girmiyor veya yeterince açık değil. Lütfen teknik sorunu ve belirtisini yazın.')
    matches = history_matches(db, title, prediction.category, prediction.target)
    ticket = Ticket(title=title.strip(), category=prediction.category, target=prediction.target,
                    engine='saved_case' if matches else 'local_ml')
    ordered = []
    if matches and matches[0].resolution_id in GUIDES:
        ordered.append(matches[0].resolution_id)
    ordered.extend(CATEGORY_GUIDES[prediction.category])
    for i, guide_id in enumerate(dict.fromkeys(ordered)):
        ticket.options.append(TicketOption(guide_id=guide_id, rank=i))
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def get_ticket(db: Session, ticket_id: int):
    return db.scalar(select(Ticket).options(selectinload(Ticket.options)).where(Ticket.id == ticket_id))

def list_resolved(db: Session):
    return list(db.scalars(select(Ticket).where(Ticket.state == 'resolved').order_by(Ticket.resolved_at.desc()).limit(40)).all())

def resolve_ticket(db: Session, ticket: Ticket, guide_id: str, notes: str):
    if ticket.state != 'open':
        raise ValueError('Ticket zaten sonlandırılmış')
    if guide_id not in {opt.guide_id for opt in ticket.options}:
        raise ValueError('Seçilen çözüm yolu bu ticket içinde yok')
    ticket.state = 'resolved'
    ticket.resolution_id = guide_id
    ticket.resolution_notes = notes.strip()[:1000]
    ticket.resolved_at = datetime.now(timezone.utc)
    db.commit()

def discard_ticket(db: Session, ticket: Ticket):
    if ticket.state != 'open':
        raise ValueError('Tamamlanmış ticket silinemez')
    db.delete(ticket)
    db.commit()
