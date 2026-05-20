from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import users, emergency  # noqa: F401
from app.models import user, emergency as emergency_model  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")
    yield
    print("👋 Сервер остановлен")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Medicopter API

Бэкенд для приложения медицинской помощи жителям отдалённых районов.

### Возможности
- 👤 Регистрация и авторизация пациентов, врачей, диспетчеров
- 🔐 JWT аутентификация (access + refresh токены)
- 🩺 (Скоро) Онлайн-консультации с врачом
- 🚌 (Скоро) Запись на медицинский автобус
- 🚨 (Скоро) Экстренные вызовы
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://medicopter.kz"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API роутеры — подключаем ДО static, чтобы /api/* не перехватывался файлами
app.include_router(
    users.router,
    prefix="/api/v1",
    tags=["Auth & Users"],
)

app.include_router(
    emergency.router,
    prefix="/api/v1",
)


@app.get("/", tags=["Pages"], include_in_schema=False)
def index():
    """Главная страница приложения."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dispatcher", tags=["Pages"], include_in_schema=False)
def dispatcher():
    """Панель диспетчера."""
    return FileResponse(STATIC_DIR / "dispatcher.html")


@app.get("/demo", tags=["Pages"], include_in_schema=False)
def demo():
    """Демо-страница с двумя панелями."""
    return FileResponse(STATIC_DIR / "demo.html")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}


# Статические файлы — подключаем последними
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
