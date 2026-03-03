from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlmodel import select
from fastapi import APIRouter, HTTPException

from database import get_session, init_db
from models import ChatMessage

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessageCreate(BaseModel):
    role: str
    content: str
    sources: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    sources: Optional[str] = None


@router.on_event("startup")
def startup():
    init_db()


@router.post("/messages", response_model=ChatMessageResponse)
def create_message(message: ChatMessageCreate):
    with get_session() as session:
        db_message = ChatMessage(**message.dict())
        session.add(db_message)
        session.commit()
        session.refresh(db_message)
        return db_message


@router.get("/messages", response_model=List[ChatMessageResponse])
def get_messages(limit: int = 50):
    with get_session() as session:
        statements = select(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(limit)
        messages = session.exec(statements).all()
        return list(reversed(messages))


@router.delete("/messages")
def clear_messages():
    with get_session() as session:
        statements = select(ChatMessage)
        messages = session.exec(statements).all()
        for msg in messages:
            session.delete(msg)
        session.commit()
        return {"status": "cleared"}
