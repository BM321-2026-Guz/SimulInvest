from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (tabloların Base'e kaydı için)
from app.config import settings
from app.database import Base, engine
from app.errors import register_error_handlers
from app.routers import assets, auth, portfolio, trades


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Şimdilik tablolar açılışta oluşturuluyor; şema değişmeye başlayınca Alembic'e geçilecek.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="SimulInvest API",
    version="1.1.0",
    description="Yapay zeka destekli sanal borsa ve portföy simülasyonu.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)

app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(assets.router)
app.include_router(trades.router)


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}
