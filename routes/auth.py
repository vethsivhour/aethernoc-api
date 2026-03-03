from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlmodel import select
from pydantic import BaseModel, EmailStr

from database import get_session
from models import User, RefreshToken
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    Token,
    TokenData
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str
    is_active: bool


def get_current_user(token_data: TokenData = Depends(lambda: None)) -> User:
    if token_data is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with get_session() as session:
        user = session.get(User, token_data.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user


def get_optional_token_data(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
) -> Optional[TokenData]:
    if token:
        return decode_token(token)
    if authorization and authorization.startswith("Bearer "):
        return decode_token(authorization.split(" ", 1)[1])
    return None


@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest):
    with get_session() as session:
        existing = session.exec(select(User).where(User.email == request.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user = User(
            email=request.email,
            password_hash=get_password_hash(request.password),
            name=request.name,
            role="user"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active
        )


@router.post("/login", response_model=Token)
def login(request: LoginRequest):
    with get_session() as session:
        user = session.exec(select(User).where(User.email == request.email)).first()
        
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")
        
        token_data = {"sub": user.id, "email": user.email, "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        refresh = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        session.add(refresh)
        session.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )


@router.post("/refresh", response_model=Token)
def refresh(request: RefreshRequest):
    with get_session() as session:
        token_record = session.exec(
            select(RefreshToken).where(RefreshToken.token == request.refresh_token)
        ).first()
        
        if not token_record or token_record.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        token_data = decode_token(request.refresh_token)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = session.get(User, token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or disabled")
        
        session.delete(token_record)
        session.commit()
        
        new_token_data = {"sub": user.id, "email": user.email, "role": user.role}
        access_token = create_access_token(new_token_data)
        new_refresh_token = create_refresh_token(new_token_data)
        
        new_refresh = RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        session.add(new_refresh)
        session.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token
        )


@router.post("/logout")
def logout(request: RefreshRequest):
    with get_session() as session:
        token_record = session.exec(
            select(RefreshToken).where(RefreshToken.token == request.refresh_token)
        ).first()
        
        if token_record:
            session.delete(token_record)
            session.commit()
        
        return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(
    token_data: Optional[TokenData] = Depends(get_optional_token_data),
):
    if not token_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with get_session() as session:
        user = session.get(User, token_data.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active
        )
