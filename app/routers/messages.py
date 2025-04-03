from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.models import User, Chat, ChatMember, Message, MessageStatus, File
from app.schemas.schemas import MessageCreate, MessageUpdate, MessageResponse, MessageStatusUpdate
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["Messages"])

@router.post("/", response_model=MessageResponse)
async def create_message(
    chat_id: UUID,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new message in a chat
    """
    # Check if user is member of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if file exists if file_id is provided
    if message.file_id:
        db_file = db.query(File).filter(File.id == message.file_id).first()
        if db_file is None:
            raise HTTPException(status_code=404, detail="File not found")
    
    # Create new message
    db_message = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=message.content,
        file_id=message.file_id
    )
    db.add(db_message)
    db.flush()
    
    # Create message status for all members
    chat_members = db.query(ChatMember).filter(ChatMember.chat_id == chat_id).all()
    for chat_member in chat_members:
        status = "seen" if chat_member.user_id == current_user.id else "sent"
        db_message_status = MessageStatus(
            message_id=db_message.id,
            user_id=chat_member.user_id,
            status=status
        )
        db.add(db_message_status)
    
    db.commit()
    db.refresh(db_message)
    
    return get_message_response(db, db_message.id)

@router.get("/", response_model=List[MessageResponse])
async def read_messages(
    chat_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of messages in a chat
    """
    # Check if user is member of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get messages
    db_messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Create response
    messages = []
    for db_message in db_messages:
        message_response = get_message_response(db, db_message.id)
        messages.append(message_response)
    
    return messages

@router.get("/{message_id}", response_model=MessageResponse)
async def read_message(
    chat_id: UUID,
    message_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a message by ID
    """
    # Check if user is member of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get message
    db_message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return get_message_response(db, message_id)

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    chat_id: UUID,
    message_id: UUID,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a message
    """
    # Check if user is member of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get message
    db_message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is sender
    if db_message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update message")
    
    # Update message fields
    if message_update.content is not None:
        db_message.content = message_update.content
    
    db.commit()
    db.refresh(db_message)
    
    return get_message_response(db, message_id)

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    chat_id: UUID,
    message_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a message
    """
    # Check if user is member of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get message
    db_message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is sender or admin
    is_sender = db_message.sender_id == current_user.id
    is_admin = db_chat_member.is_admin
    
    if not (is_sender or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to delete message")
    
    # Delete message
    db.delete(db_message)
    db.commit()
    
    return None

@router.put("/{message_id}/status", response_model=MessageResponse)
async def update_message_status(
    chat_id: UUID,
    message_id: UUID,
    status_update: MessageStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update message status
    """
    # Check if user is member of chat
    db_chat_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()
    if db_chat_member is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get message
    db_message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get message status
    db_message_status = db.query(MessageStatus).filter(
        MessageStatus.message_id == message_id,
        MessageStatus.user_id == current_user.id
    ).first()
    
    if db_message_status is None:
        # Create message status if it doesn't exist
        db_message_status = MessageStatus(
            message_id=message_id,
            user_id=current_user.id,
            status=status_update.status
        )
        db.add(db_message_status)
    else:
        # Update message status
        db_message_status.status = status_update.status
    
    db.commit()
    db.refresh(db_message_status)
    
    return get_message_response(db, message_id)

def get_message_response(db: Session, message_id: UUID):
    """
    Helper function to get message response
    """
    # Get message
    db_message = db.query(Message).filter(Message.id == message_id).first()
    
    # Get message statuses
    db_message_statuses = db.query(MessageStatus).filter(MessageStatus.message_id == message_id).all()
    
    # Create response
    message_response = {
        "id": db_message.id,
        "chat_id": db_message.chat_id,
        "sender_id": db_message.sender_id,
        "content": db_message.content,
        "file_id": db_message.file_id,
        "created_at": db_message.created_at,
        "updated_at": db_message.updated_at,
        "statuses": [
            {
                "user_id": status.user_id,
                "status": status.status,
                "updated_at": status.updated_at
            }
            for status in db_message_statuses
        ]
    }
    
    return message_response