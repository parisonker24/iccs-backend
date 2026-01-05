from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict
import os
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_user
from app.db.session import async_session_maker
from app.models.user import User
import logging

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

async def get_db():
    async with async_session_maker() as session:
        yield session

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await crud_user.create_user(db, user_in.username, user_in.email, user_in.password)
        return user
    except IntegrityError as e:
        # This will catch unique constraint errors from the DB, e.g., duplicate username or email
        logger.warning(f"IntegrityError creating user: {e}")
        raise HTTPException(status_code=400, detail="Username or email already exists")
    except Exception as e:
        # Log the full traceback for debugging. If DEBUG=1 is set in the
        # environment, include the exception message in the HTTP response
        # to make local debugging easier. Do NOT enable DEBUG in production.
        logger.exception("Error creating user")
        if os.getenv("DEBUG") == "1":
            # Return a development-friendly error message (stringified exception).
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=List[UserOut])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    users = await crud_user.get_users(db, skip, limit)
    return users

@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
