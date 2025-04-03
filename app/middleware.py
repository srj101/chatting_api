from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models.models import APIKey

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip middleware for authentication endpoints
        if request.url.path.startswith("/api/v1/auth") or request.url.path == "/docs" or request.url.path == "/":
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)
        
        # Validate API key
        db = SessionLocal()
        try:
            db_api_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
            if not db_api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            
            # Update last used timestamp
            db_api_key.last_used_at = datetime.utcnow()
            db.commit()
            
            # Add API key to request state
            request.state.api_key = db_api_key
            
        finally:
            db.close()
        
        return await call_next(request)