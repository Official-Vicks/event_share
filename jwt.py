# jwt.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from config import settings
from app.models.user_models import BlacklistedToken, User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid

def _make_payload_json_safe(payload: dict) -> dict:
    """Convert common non-JSON types to JSON-safe representations.

    - UUID -> str
    - datetime -> int (unix timestamp)
    - other types: call str() as fallback
    """
    safe = {}
    for k, v in payload.items():
        if isinstance(v, uuid.UUID):
            safe[k] = str(v)
        elif isinstance(v, datetime):
            safe[k] = int(v.timestamp())
        else:
            # preserve primitives (str, int, float, bool, None) unchanged
            # for other types, fallback to str() to avoid encoding errors
            if isinstance(v, (str, int, float, bool)) or v is None:
                safe[k] = v
            else:
                safe[k] = str(v)
    return safe

def create_access_token(data: dict, expire_timedelta: timedelta = None) -> str:
    now = datetime.now(timezone.utc)
    expiry_time = now + (expire_timedelta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)) 
    # copy to avoid mutating caller data 
    payload = {**data}
    payload["exp"] = expiry_time
    payload["scope"] = "access_token"
    payload = _make_payload_json_safe(payload)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict, expire_timedelta: timedelta = None) -> str:
    now = datetime.now(timezone.utc)
    expiry_time = now + (expire_timedelta or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))
    payload = {**data}
    payload["exp"] = expiry_time
    payload["scope"] = "refresh_token"
    payload = _make_payload_json_safe(payload)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str, db: Session, scope: str = "access_token") -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != scope:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token scope.")
        if db.query(BlacklistedToken).filter_by(token=token).first():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        return payload
    except JWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid access token.\nError: {error}")

def decode_refresh_token(token: str, db: Session, scope: str = "refresh_token") -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != scope:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token scope.")
        if db.query(BlacklistedToken).filter_by(token=token).first():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

def blacklist_token(db: Session, token: str):
    if not db.query(BlacklistedToken).filter_by(token=token).first():
        blacklist = BlacklistedToken(token=token)
        db.add(blacklist)
        db.commit()

def is_token_blacklisted(db: Session, token: str) -> bool:
    return db.query(BlacklistedToken).filter_by(token=token).first() is not None