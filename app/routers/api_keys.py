import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import User, APIKey
from app.schemas.schemas import APIKeyCreate, APIKeyResponse
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    api_key: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key
    """
    # Generate a random API key
    key = secrets.token_hex(32)
    
    # Create new API key
    db_api_key = APIKey(
        key=key,
        name=api_key.name,
        user_id=current_user.id
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return db_api_key

@router.get("/", response_model=List[APIKeyResponse])
async def read_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of API keys for current user
    """
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return api_keys

@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an API key
    """
    db_api_key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == current_user.id).first()
    if db_api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(db_api_key)
    db.commit()
    
    return None