from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.db.models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def get_session():
    with SessionLocal() as session:
        yield session
