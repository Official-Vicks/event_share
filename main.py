from fastapi import FastAPI
from sqlalchemy import text
from app.routes.user import router as auth_router
from app.routes.admin import admin_router as admin_router
from app.routes.event import router as event_router
from app.routes.moments_routes import router as moments_router
from app.routes.event_participation import router as event_participation_router
from db import Base, engine, SessionLocal
from config import settings
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
import os
import app.models
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

app = FastAPI()
os.makedirs(os.path.join(settings.MEDIA_DIR, "avi"), exist_ok=True)
app.mount("/static/avi", StaticFiles(directory=os.path.join(settings.MEDIA_DIR, "avi")), name="avi")
app.mount(
    "/static/event_banners",
    StaticFiles(directory=os.path.join(settings.MEDIA_DIR, "event_banners")),
    name="event_banners"
)

app.mount(
    "/static/admin",
    StaticFiles(directory=os.path.join(settings.MEDIA_DIR, "admin")),
    name="admin"
)

app.mount(
    "/static/moments",
    StaticFiles(directory=os.path.join(settings.MOMENT_MEDIA_DIR, "moments")),
    name="moments"
)
# Include routers

# Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(event_router)
app.include_router(moments_router)
app.include_router(event_participation_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Event Share API",
        version="1.0.0",
        description="Event Share API docs",
        routes=app.routes,
    )

    # Add JWT Bearer Authentication
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Apply BearerAuth globally to all endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema

    return app.openapi_schema

app.openapi = custom_openapi