"""Apply Pydantic v2 migration changes to files.

Run this script from the repository root with the same Python environment used by the project:

    d:\iccs-backend\.venv\Scripts\python.exe apply_pydantic_v2_changes.py

It will overwrite the relevant files with the intended content. After running, commit the changes with Git.
"""
from pathlib import Path

files = {
    "app/core/config.py": r'''from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Provide a sensible default DATABASE_URL so the application can start
# without requiring an environment variable during development/testing.
# For production, set the `DATABASE_URL` environment variable or `.env` file.
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./iccs.db"
    REDIS_URL: str = "redis://localhost:6379"
    # Secret settings for JWT; set these in production via env or .env
    SECRET_KEY: str = "change-me-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = ConfigDict(env_file=".env")

settings = Settings()
''',

    "app/schemas/routers/user.py": r'''from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict
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
        raise HTTPException(status_code=400, detail="Username or email already exists")
    except Exception as e:
        # Log the actual exception for debugging and return a sanitized
        # HTTP 500 response to the client.
        logger.error(f"Error creating user: {e}", exc_info=True)
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
''',

    "app/schemas/inventory.py": r'''from pydantic import BaseModel, ConfigDict
from typing import Optional

class InventoryBase(BaseModel):
    product_id: int
    quantity: int
    location: Optional[str] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    location: Optional[str] = None

class Inventory(InventoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
''',

    "app/test_hash.py": r'''from app.core.security import get_password_hash, verify_password


def test_password_hash_and_verify():
	"""Hash a password with the project's context and verify it."""
	password = "Paris@224"
	hashed = get_password_hash(password)
	assert verify_password(password, hashed)
	assert not verify_password("wrong-password", hashed)
''',

    "commit_changes.bat": r'''@echo off
REM Commit workspace changes (run this in the repository root where Git is installed and in PATH)
 git add -A
 git commit -m "pydantic(v2): migrate class Config to model_config; add password test"
 echo Commit complete. If this failed, ensure Git is installed and on PATH.
 pause
'''
}

root = Path(__file__).resolve().parent
for relpath, content in files.items():
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path}")

print('Done. Review the files and run: git add -A && git commit -m "pydantic(v2): migrate class Config to model_config; add password test"')
