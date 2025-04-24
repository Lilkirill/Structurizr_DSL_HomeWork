import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging
from contextlib import contextmanager


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres_db:5432/postgres")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

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

@contextmanager
def get_db():

    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logging.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()