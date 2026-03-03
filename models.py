from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str = Field(index=True)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[str] = Field(default=None)
