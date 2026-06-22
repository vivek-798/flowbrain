import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.integration import Integration

async def refresh_user_google_tokens(db: Session, user_id: int) -> str:
    """
    Refreshes Google OAuth access tokens for a user and updates all their google-related integrations.
    Returns the new access token.
    """
    # Fetch any Google-related integration to get the refresh token
    integration = db.query(Integration).filter(
        Integration.user_id == user_id,
        Integration.provider.in_(["gmail", "calendar", "google"]),
        Integration.refresh_token.isnot(None)
    ).first()
    
    if not integration or not integration.refresh_token:
        raise Exception("Google refresh token not found. Please log in again to authenticate.")
        
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": integration.refresh_token,
                "grant_type": "refresh_token",
            }
        )
        if res.status_code != 200:
            raise Exception(f"Google token refresh failed: {res.text}")
            
        token_data = res.json()
        new_access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token")
        
        # Update all google-related integrations for this user
        integrations = db.query(Integration).filter(
            Integration.user_id == user_id,
            Integration.provider.in_(["gmail", "calendar", "google"])
        ).all()
        
        for item in integrations:
            item.access_token = new_access_token
            if new_refresh_token:
                item.refresh_token = new_refresh_token
        
        db.commit()
        return new_access_token
