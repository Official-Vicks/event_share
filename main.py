from fastapi import FastAPI
from sqlalchemy import text
from app.routes.user import router as auth_router
from app.routes.admin import admin_router as admin_router
from app.routes.event import router as event_router
from app.routes.moments_routes import router as moments_router
from db import Base, engine, SessionLocal
from config import settings
from fastapi.staticfiles import StaticFiles
import os
import app.models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
os.makedirs(os.path.join(settings.MEDIA_DIR, "avi"), exist_ok=True)
app.mount("/static/avi", StaticFiles(directory=os.path.join(settings.MEDIA_DIR, "avi")), name="avi")
app.mount(
    "/static/event_banners",
    StaticFiles(directory=os.path.join(settings.MEDIA_DIR, "event_banners")),
    name="event_banners"
)
# Include routers

Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(event_router)
app.include_router(moments_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)