from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_user
from app.core.security import verify_password, create_access_token
from app.db.session import async_session_maker
from typing import Optional
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

async def get_db():
    async with async_session_maker() as session:
        yield session

@router.post("/login", response_model=TokenResponse)
async def login(login_req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await crud_user.get_user_by_email(db, login_req.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return TokenResponse(access_token=access_token)


@router.post("/token", response_model=TokenResponse)
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # OAuth2 password flow expects 'username' and 'password' form fields.
    # We treat 'username' as the user's email for compatibility with existing login.
    email = form_data.username
    password = form_data.password

    user = await crud_user.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return TokenResponse(access_token=access_token)
