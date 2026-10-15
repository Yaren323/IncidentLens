"""New tables: independent of the legacy v1 incidents schema."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models import Base

class Ticket(Base):
    __tablename__ = 'support_tickets'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    category: Mapped[str] = mapped_column(String(50))
    target: Mapped[str] = mapped_column(String(200), default='')
    state: Mapped[str] = mapped_column(String(20), default='open')
    engine: Mapped[str] = mapped_column(String(60), default='local_ml')
    resolution_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    options: Mapped[list['TicketOption']] = relationship(back_populates='ticket', cascade='all, delete-orphan')

class TicketOption(Base):
    __tablename__ = 'ticket_options'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('support_tickets.id', ondelete='CASCADE'), nullable=False)
    guide_id: Mapped[str] = mapped_column(String(80))
    rank: Mapped[int] = mapped_column(Integer)
    ticket: Mapped[Ticket] = relationship(back_populates='options')
