import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class User(Base):
    __tablename__ = "ostad_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    full_name = Column(String(100))
    profile_picture = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    chats = relationship("ChatMember", back_populates="user")
    messages = relationship("Message", back_populates="sender")
    message_statuses = relationship("MessageStatus", back_populates="user")

class APIKey(Base):
    __tablename__ = "ostad_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, index=True)
    name = Column(String(100))
    user_id = Column(UUID(as_uuid=True), ForeignKey("ostad_users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

class Chat(Base):
    __tablename__ = "ostad_chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=True)  # Null for individual chats
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("ChatMember", back_populates="chat")
    messages = relationship("Message", back_populates="chat")

class ChatMember(Base):
    __tablename__ = "ostad_chat_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("ostad_chats.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("ostad_users.id"))
    is_admin = Column(Boolean, default=False)  # For group chats
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat = relationship("Chat", back_populates="members")
    user = relationship("User", back_populates="chats")

class Message(Base):
    __tablename__ = "ostad_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("ostad_chats.id"))
    sender_id = Column(UUID(as_uuid=True), ForeignKey("ostad_users.id"))
    content = Column(Text)
    file_id = Column(UUID(as_uuid=True), ForeignKey("ostad_files.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    file = relationship("File", back_populates="message")
    statuses = relationship("MessageStatus", back_populates="message")

class MessageStatus(Base):
    __tablename__ = "ostad_message_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("ostad_messages.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("ostad_users.id"))
    status = Column(String(10))  # sent, delivered, seen
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    message = relationship("Message", back_populates="statuses")
    user = relationship("User", back_populates="message_statuses")

class File(Base):
    __tablename__ = "ostad_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255))
    content_type = Column(String(100))
    size = Column(Integer)  # Size in bytes
    data = Column(LargeBinary)  # File data
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="file", uselist=False)