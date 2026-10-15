from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from urllib.parse import urlparse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.ticket_routes import router
from app.db.session import initialize_database
from app.db import tickets  # noqa: F401 - register new tables with SQLAlchemy

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield

app = FastAPI(title='IncidentLens', version='2.0.0', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
app.state.templates = Jinja2Templates(directory=BASE_DIR / 'templates')
app.include_router(router)

@app.middleware('http')
async def local_request_protection(request: Request, call_next):
    if request.method == 'POST':
        if int(request.headers.get('content-length', '0') or '0') > 8192:
            return PlainTextResponse('İstek çok büyük', status_code=413)
        origin = request.headers.get('origin') or request.headers.get('referer')
        if origin and urlparse(origin).netloc != request.headers.get('host'):
            return PlainTextResponse('Kaynak doğrulanamadı', status_code=403)
    return await call_next(request)
