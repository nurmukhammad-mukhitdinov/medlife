from datetime import datetime, timedelta
from typing import Optional

import logging
import jwt
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.database import get_async_db
from app.models.users import UserModel

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/auth/token",
    scheme_name="Phone/Password",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    # ensure "sub" is string
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt, int(expire.timestamp())


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> UserModel:
    logger.debug("Incoming token (HTTP): %r", token)

    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        logger.debug("Decoded payload: %r", payload)
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise creds_exc
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise creds_exc
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        raise creds_exc

    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    logger.debug("DB lookup result user: %r", user)

    if user is None:
        raise creds_exc

    return user


# ---------- WS-friendly auth dependency ----------
async def get_current_user_ws(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_db),
) -> UserModel:
    """
    Authenticate a WebSocket connection.

    Accepts:
      - Authorization: Bearer <token>
      - or 'access_token' cookie
    """
    # Header is case-insensitive but FastAPI gives canonical 'authorization'
    raw_auth = websocket.headers.get("authorization")
    token = None

    if raw_auth:
        parts = raw_auth.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if token is None:
        token = websocket.cookies.get("access_token")

    if not token:
        # Close with policy violation
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token")

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            await websocket.close(code=1008)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
