from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.models import User, Chat, ChatMember, Message
from app.schemas.schemas import ChatCreate, ChatUpdate, ChatResponse
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat: ChatCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new chat
    """
    # Validate member IDs
    member_ids = set(chat.member_ids)
    member_ids.add(current_user.id)  # Add current user to members
    
    # Check if all members exist
    for member_id in member_ids:
        db_user = db.query(User).filter(User.id == member_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail=f"User with ID {member_id} not found")
    
    # For individual chat, check if chat already exists
    if not chat.is_group and len(member_ids) == 2:
        other_user_id = next(id for id in member_ids if id != current_user.id)
        
        # Check if chat already exists
        existing_chats = (
            db.query(Chat)
            .join(ChatMember, Chat.id == ChatMember.chat_id)
            .filter(Chat.is_group == False)
            .filter(ChatMember.user_id == current_user.id)
            .all()
        )
        
        for existing_chat in existing_chats:
            members = db.query(ChatMember).filter(ChatMember.chat_id == existing_chat.id).all()
            member_ids_set = {member.user_id for member in members}
            if len(member_ids_set) == 2 and other_user_id in member_ids_set:
                # Chat already exists, return it
                return get_chat_response(db, existing_chat.id, current_user.id)
    
    # Create new chat
    db_chat = Chat(
        name=chat.name,
        is_group=chat.is_group
    )
    db.add(db_chat)
    db.flush()
    
    # Add members
    for member_id in member_ids:
        is_admin = member_id == current_user.id  # Current user is admin
        db_chat_member = ChatMember(
            chat_id=db_chat.id,
            user_id=member_id,
            is_admin=is_admin
        )
        db.add(db_chat_member)
    
    db.commit()
    db.refresh(db_chat)
    
    return get_chat_response(db, db_chat.id, current_user.id)

@router.get("/", response_model=List[ChatResponse])
async def read_chats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of chats for current user
    """
    # Get chat IDs for current user
    chat_ids = (
        db.query(ChatMember.chat_id)
        .filter(ChatMember.user_id == current_user.id)
        .all()
    )
    chat_ids = [chat_id[0] for chat_id in chat_ids]
    
    # Get chats
    chats = []
    for chat_id in chat_ids:
        chat_response = get_chat_response(db, chat_id, current_user.id)
        chats.append(chat_response)
    
    return chats

@router.get("/{chat_id}", response_model=ChatResponse)
async def read_chat(
    chat_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get chat by ID
    """
    # Check if user is member of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return get_chat_response(db, chat_id, current_user.id)

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: UUID,
    chat_update: ChatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update chat information
    """
    # Check if user is admin of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id,
        ChatMember.is_admin == True
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=403, detail="Not authorized to update chat")
    
    # Get chat
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Update chat fields
    if chat_update.name is not None:
        db_chat.name = chat_update.name
    
    db.commit()
    db.refresh(db_chat)
    
    return get_chat_response(db, chat_id, current_user.id)

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chat
    """
    # Check if user is admin of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id,
        ChatMember.is_admin == True
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=403, detail="Not authorized to delete chat")
    
    # Delete chat
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(db_chat)
    db.commit()
    
    return None

@router.post("/{chat_id}/members/{user_id}", response_model=ChatResponse)
async def add_chat_member(
    chat_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a member to a chat
    """
    # Check if user is admin of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id,
        ChatMember.is_admin == True
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=403, detail="Not authorized to add members")
    
    # Check if chat is group
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if not db_chat.is_group:
        raise HTTPException(status_code=400, detail="Cannot add members to individual chat")
    
    # Check if user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already member
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == user_id
    ).first()
    if db_chat_member is not None:
        raise HTTPException(status_code=400, detail="User is already a member of chat")
    
    # Add member
    db_chat_member = ChatMember(
        chat_id=chat_id,
        user_id=user_id,
        is_admin=False
    )
    db.add(db_chat_member)
    db.commit()
    
    return get_chat_response(db, chat_id, current_user.id)

@router.delete("/{chat_id}/members/{user_id}", response_model=ChatResponse)
async def remove_chat_member(
    chat_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from a chat
    """
    # Check if user is admin of chat or removing self
    is_admin = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id,
        ChatMember.is_admin == True
    ).first() is not None
    is_self = current_user.id == user_id
    
    if not (is_admin or is_self):
        raise HTTPException(status_code=403, detail="Not authorized to remove members")
    
    # Check if chat is group
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if not db_chat.is_group:
        raise HTTPException(status_code=400, detail="Cannot remove members from individual chat")
    
    # Check if user is member
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == user_id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="User is not a member of chat")
    
    # Remove member
    db.delete(db_chat_member)
    db.commit()
    
    return get_chat_response(db, chat_id, current_user.id)

def get_chat_response(db: Session, chat_id: UUID, current_user_id: UUID):
    """
    Helper function to get chat response
    """
    # Get chat
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    
    # Get members
    db_chat_members = db.query(ChatMember).filter(ChatMember.chat_id == chat_id).all()
    
    # Get member details
    members = []
    for db_chat_member in db_chat_members:
        db_user = db.query(User).filter(User.id == db_chat_member.user_id).first()
        members.append({
            "user_id": db_user.id,
            "username": db_user.username,
            "is_admin": db_chat_member.is_admin,
            "joined_at": db_chat_member.joined_at
        })
    
    # Get last message
    db_last_message = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.desc()).first()
    
    # Create response
    chat_response = {
        "id": db_chat.id,
        "name": db_chat.name,
        "is_group": db_chat.is_group,
        "created_at": db_chat.created_at,
        "updated_at": db_chat.updated_at,
        "members": members,
        "last_message": db_last_message
    }
    
    return chat_response