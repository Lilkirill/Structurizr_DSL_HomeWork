import os
import redis
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging
from contextlib import contextmanager
from typing import Generator

# PostgreSQL Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres_db:5432/postgres")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_POOL_SIZE", "10"))

# PostgreSQL Engine Setup
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis Connection Pool
redis_pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=REDIS_MAX_CONNECTIONS,
    decode_responses=True
)

@contextmanager
def get_db() -> Generator:
    """PostgreSQL database session context manager"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logging.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_redis() -> Generator[redis.Redis, None, None]:
    """Redis connection context manager"""
    redis_conn = redis.Redis(connection_pool=redis_pool)
    try:
        yield redis_conn
    except redis.RedisError as e:
        logging.error(f"Redis error: {e}")
        raise
    finally:
        # Connection возвращается в пул автоматически
        pass