from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, get_db
from sqlalchemy.orm import Session

# Import models to register them with SQLAlchemy Base
from app.models.user import User
from app.models.integration import Integration
from app.models.briefing import Briefing
from app.models.project import Project
from app.models.email import Email
from app.models.calendar_event import CalendarEvent
from app.models.business_context import BusinessContext
from app.models.action_item import ActionItem


# Import API Routers
from app.api.routes.auth import router as auth_router
from app.api.routes.briefing import router as briefing_router, actions_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.history import router as history_router
from app.api.routes.settings import settings_router, insights_router
from app.api.routes.sync import router as sync_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.business_context import router as business_context_router
from app.api.routes.emails import router as emails_router


from starlette.middleware.sessions import SessionMiddleware

# Auto-create tables for local database (SQLite/PostgreSQL schema initialization)
# Base.metadata.create_all(bind=engine) # Handled by alembic migrations now

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FlowBrain MVP - AI Chief of Staff API for Founders",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Setup SessionMiddleware for Authlib OAuth state management
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Setup CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend URL in production (e.g. ["http://localhost:5173"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints under /api/v1
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(briefing_router, prefix=settings.API_V1_STR)
app.include_router(actions_router, prefix=settings.API_V1_STR)
app.include_router(integrations_router, prefix=settings.API_V1_STR)
app.include_router(history_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(insights_router, prefix=settings.API_V1_STR)
app.include_router(sync_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(business_context_router, prefix=settings.API_V1_STR)

app.include_router(emails_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs"
    }

@app.on_event("startup")
def startup_event():
    client_id = settings.GOOGLE_CLIENT_ID or ""
    client_id_display = f"{client_id[:5]}..." if client_id else "None"
    client_secret_present = bool(settings.GOOGLE_CLIENT_SECRET)
    print("Google OAuth Config Loaded", flush=True)
    print(f"Client ID: {client_id_display}", flush=True)
    print(f"Redirect URI: {settings.google_redirect_uri}", flush=True)
    print(f"Client Secret Present: {client_secret_present}", flush=True)
    
    # Dynamic DB migration check for briefings columns
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        if "briefings" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("briefings")]
            with engine.begin() as conn:
                if "headline" not in columns:
                    conn.execute(text("ALTER TABLE briefings ADD COLUMN headline VARCHAR"))
                    print("Migration: Added headline column to briefings table", flush=True)
                if "ignored_count" not in columns:
                    conn.execute(text("ALTER TABLE briefings ADD COLUMN ignored_count INTEGER DEFAULT 0"))
                    print("Migration: Added ignored_count column to briefings table", flush=True)
    except Exception as e:
        print("Error running dynamic startup DB check:", e, flush=True)


@app.get(f"{settings.API_V1_STR}/debug/oauth")
def debug_oauth():
    client_id = settings.GOOGLE_CLIENT_ID or ""
    return {
        "client_id_loaded": bool(client_id),
        "redirect_uri": settings.google_redirect_uri,
        "client_id_prefix": client_id[:5] if client_id else ""
    }

@app.get(f"{settings.API_V1_STR}/debug/briefing-status")
def debug_briefing_status(db: Session = Depends(get_db)):
    emails_count = db.query(Email).count()
    calendar_events_count = db.query(CalendarEvent).count()
    briefings_count = db.query(Briefing).count()
    latest_briefing = db.query(Briefing).order_by(Briefing.generated_at.desc()).first()
    return {
        "emails_count": emails_count,
        "calendar_events_count": calendar_events_count,
        "briefings_count": briefings_count,
        "latest_briefing_exists": latest_briefing is not None
    }
# Trigger reload for .env changes
