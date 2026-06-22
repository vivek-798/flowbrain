import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FlowBrain"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkeyhereforjwttokengenerationandencryption"
    JWT_SECRET_KEY: str = "supersecretkeyhereforjwttokengenerationandencryption"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520
    DATABASE_URL: str = "sqlite:///./flowbrain.db"
    
    # App URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    
    # Google OAuth Credentials
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    USE_AUTHLIB: bool = False

    @property
    def google_redirect_uri(self) -> str:
        if self.GOOGLE_REDIRECT_URI:
            return self.GOOGLE_REDIRECT_URI
        return f"{self.BACKEND_URL.rstrip('/')}{self.API_V1_STR}/auth/google/callback"
    
    # LLM Provider Key (LiteLLM)
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "gemini"
    MODEL: str = "gemini/gemini-2.5-flash"

    class Config:
        # Load from .env file
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        case_sensitive = True

settings = Settings()
