from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_picture: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    profile_picture: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[UUID] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# API Key schemas
class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: UUID
    key: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Chat schemas
class ChatCreate(BaseModel):
    name: Optional[str] = None
    is_group: bool = False
    member_ids: List[UUID]

class ChatUpdate(BaseModel):
    name: Optional[str] = None

class ChatMemberResponse(BaseModel):
    user_id: UUID
    username: str
    is_admin: bool
    joined_at: datetime

    class Config:
        orm_mode = True

class ChatResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    is_group: bool
    created_at: datetime
    updated_at: datetime
    members: List[ChatMemberResponse]
    last_message: Optional["MessageResponse"] = None

    class Config:
        orm_mode = True

# Message schemas
class MessageCreate(BaseModel):
    content: str
    file_id: Optional[UUID] = None

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class MessageStatusUpdate(BaseModel):
    status: str

    @validator('status')
    def validate_status(cls, v):
        if v not in ['sent', 'delivered', 'seen']:
            raise ValueError('Status must be one of: sent, delivered, seen')
        return v

class MessageStatusResponse(BaseModel):
    user_id: UUID
    status: str
    updated_at: datetime

    class Config:
        orm_mode = True

class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    content: str
    file_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    statuses: List[MessageStatusResponse]

    class Config:
        orm_mode = True

# File schemas
class FileResponse(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime

    class Config:
        orm_mode = True

# Update forward references
ChatResponse.update_forward_refs()