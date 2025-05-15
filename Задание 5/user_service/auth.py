from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from redis import Redis
import crud, schemas, models
from database import get_db, get_redis
from typing import Optional, Tuple
import os
import logging

# Logger setup
logger = logging.getLogger(__name__)

# Security config
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password context
pwd_context = CryptContext(
    schemes=["bcrypt", "argon2"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    argon2__hash_len=32
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "user": "Regular user permissions",
        "admin": "Admin privileges"
    }
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with fallback to bcrypt if argon2 fails"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate secure password hash"""
    return pwd_context.hash(password)

async def authenticate_user(
    db: Session,
    username: str,
    password: str,
    redis: Optional[Redis] = None
) -> Optional[models.User]:
    """Authenticate user with cache support"""
    cache_key = f"auth_user:{username}"
    
    # Try to get from cache
    if redis:
        cached_user = redis.get(cache_key)
        if cached_user:
            user_data = schemas.UserOut.from_redis_dict(json.loads(cached_user))
            if verify_password(password, user_data.password_hash):
                return user_data
    
    # Database lookup
    user = crud.get_user_by_username(db, username, redis=redis)
    if not user or not verify_password(password, user.password_hash):
        return None
    
    # Update cache
    if redis:
        redis.setex(
            cache_key,
            timedelta(minutes=5),
            json.dumps(user.to_redis_dict())
        )
    
    return user

def create_tokens(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    refresh_expires_delta: Optional[timedelta] = None
) -> Tuple[str, str]:
    """Create access and refresh tokens"""
    to_encode = data.copy()
    now = datetime.utcnow()
    
    # Access token
    access_expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": access_expire, "type": "access"})
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Refresh token
    refresh_expire = now + (refresh_expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": refresh_expire, "type": "refresh"})
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return access_token, refresh_token

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    token: str = Depends(oauth2_scheme)
) -> models.User:
    """Get current user from token with cache support"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    cache_key = f"user_token:{token}"
    if redis:
        cached_user = redis.get(cache_key)
        if cached_user:
            return schemas.UserOut.from_redis_dict(json.loads(cached_user))
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username, redis=redis)
    if user is None:
        raise credentials_exception
    
    # Verify token is not revoked
    if await is_token_revoked(token, redis):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # Cache user data
    if redis:
        redis.setex(
            cache_key,
            timedelta(minutes=5),
            json.dumps(user.to_redis_dict())
        )
    
    return user

async def is_token_revoked(token: str, redis: Redis) -> bool:
    """Check if token is in revocation list"""
    return redis.sismember("revoked_tokens", token)

async def revoke_token(token: str, redis: Redis) -> None:
    """Add token to revocation list"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expire_time = datetime.fromtimestamp(payload["exp"])
        ttl = (expire_time - datetime.utcnow()).total_seconds()
        if ttl > 0:
            redis.sadd("revoked_tokens", token)
            redis.expire("revoked_tokens", int(ttl))
    except JWTError:
        pass