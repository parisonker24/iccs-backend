from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

# SINGLE oauth2 scheme (ONLY ONE)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("sub") or payload.get("user_id")

    class _SimpleUser:
        pass

    user = _SimpleUser()
    try:
        user.id = int(user_id) if user_id is not None else None
    except Exception:
        user.id = user_id

    return user


async def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)):
    """Dependency that validates JWT and ensures the user is an admin.

    This helper reads the token from the Authorization header, cookies, or
    the `token` query parameter using `get_token_from_request` to make it
    easier to debug via Swagger (you can append `?token=<JWT>`).

    Raises:
        HTTPException 401: when token is invalid or user not found
        HTTPException 403: when user exists but is not an admin

    Returns the full User ORM object when successful.
    """
    # attempt to extract token from header/cookie/query
    token = get_token_from_request(request)

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("sub") or payload.get("user_id")

    try:
        _uid = int(user_id) if user_id is not None else None
    except Exception:
        _uid = user_id

    # import crud at runtime to avoid circular imports
    crud_user = __import__("app.crud.crud_user", fromlist=["get_user"])
    db_user = await crud_user.get_user(db, _uid)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Import UserRole here to avoid module-level cycles
    from app.models.user import UserRole

    if getattr(db_user, "role", None) != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    return db_user


def get_token_from_request(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if auth:
        parts = auth.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    token = request.cookies.get("access_token") or request.query_params.get("token")
    if token:
        return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
