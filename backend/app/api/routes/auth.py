import urllib.parse
import requests
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.models.user import User
from app.models.integration import Integration
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Initialize Authlib OAuth client with OIDC profile and read-only Gmail & Calendar scopes
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    client_kwargs={"scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly"},
)

@router.get("/google/login")
async def google_login(request: Request):
    """
    Redirects to Google OAuth page.
    Passes prompt=consent and access_type=offline to ensure we receive a refresh_token.
    """
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent"
    )

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles Google OAuth callback. Exchanges auth code for tokens,
    upserts User details, registers Gmail and Calendar integrations,
    and redirects to frontend with credentials.
    """
    print("CALLBACK URL:", request.url, flush=True)
    print("QUERY PARAMS:", request.query_params, flush=True)
    print("HEADERS:", request.headers, flush=True)
    
    if not settings.USE_AUTHLIB:
        # Manual token exchange
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code in query parameters."
            )
        
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri
        }
        
        try:
            print("MANUAL TOKEN EXCHANGE INITIATED", flush=True)
            response = requests.post(token_url, data=payload)
            token_response_json = response.json()
            print("GOOGLE TOKEN RESPONSE:", token_response_json, flush=True)
            
            if response.status_code != 200:
                error_description = token_response_json.get("error_description") or token_response_json.get("error") or "Unknown error"
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Google token exchange failed: {error_description}"
                )
            
            token = token_response_json
            # Parse userinfo from id_token using jwt
            id_token = token.get("id_token")
            if id_token:
                import jwt
                user_info = jwt.decode(id_token, options={"verify_signature": False})
                token["userinfo"] = user_info
            else:
                # Fallback to UserInfo endpoint if id_token is missing
                access_token = token.get("access_token")
                userinfo_res = requests.get(
                    "https://openidconnect.googleapis.com/v1/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if userinfo_res.status_code == 200:
                    token["userinfo"] = userinfo_res.json()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to retrieve user info from Google userinfo endpoint."
                    )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            import traceback
            print("GOOGLE TOKEN EXCHANGE ERROR", flush=True)
            print(str(e), flush=True)
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Google token exchange failed: {str(e)}"
            )
    else:
        # Existing Authlib implementation
        try:
            token = await oauth.google.authorize_access_token(request)
        except Exception as e:
            import traceback
            print("GOOGLE TOKEN EXCHANGE ERROR", flush=True)
            print(str(e), flush=True)
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Google token exchange failed: {str(e)}"
            )

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve user profile details from Google token"
        )

    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    avatar_url = user_info.get("picture")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google profile did not provide an email address"
        )

    # 3. Upsert User in database (checks email or google_id to avoid duplicates)
    user = db.query(User).filter((User.google_id == google_id) | (User.email == email)).first()
    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url
        )
        db.add(user)
    else:
        user.google_id = google_id
        user.name = name
        user.avatar_url = avatar_url
        user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    # 4. Upsert Gmail & Calendar integration records for the user
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    
    for provider in ["gmail", "calendar"]:
        integration = db.query(Integration).filter(
            Integration.user_id == user.id,
            Integration.provider == provider
        ).first()
        
        if not integration:
            integration = Integration(
                user_id=user.id,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                connected=True,
                last_sync=None
            )
            db.add(integration)
        else:
            integration.access_token = access_token
            # Google only sends refresh_token on prompt=consent
            if refresh_token:
                integration.refresh_token = refresh_token
            integration.connected = True
            
    # Also save the master "google" integration record for general reference
    google_integration = db.query(Integration).filter(
        Integration.user_id == user.id,
        Integration.provider == "google"
    ).first()
    if not google_integration:
        google_integration = Integration(
            user_id=user.id,
            provider="google",
            access_token=access_token,
            refresh_token=refresh_token,
            connected=True,
            last_sync=None
        )
        db.add(google_integration)
    else:
        google_integration.access_token = access_token
        if refresh_token:
            google_integration.refresh_token = refresh_token
        google_integration.connected = True
        
    db.commit()

    # 5. Generate FlowBrain JWT Token
    jwt_token = create_access_token(subject=user.email)

    # 6. Redirect back to frontend
    params = {
        "token": jwt_token,
        "name": user.name or "",
        "email": user.email,
        "avatar_url": user.avatar_url or ""
    }
    frontend_url = f"{settings.FRONTEND_URL.rstrip('/')}/login?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=frontend_url)

@router.post("/logout")
def logout():
    """
    Logs out user by returning a confirmation message.
    """
    return {"message": "Successfully logged out"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile details.
    """
    return {
        "id": current_user.id,
        "google_id": current_user.google_id,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

