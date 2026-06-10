from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import admin, auth, health, recipes, weeks

app = FastAPI(title="DailyDiet API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_DIR = Path(__file__).resolve().parent.parent.parent / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
(PUBLIC_DIR / "recipes").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(weeks.router)
app.include_router(recipes.router)
app.include_router(admin.router)