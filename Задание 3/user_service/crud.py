from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate, UserUpdate
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    try:
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name
        )
        db_user.set_password(user.password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise

def update_user(db: Session, user_id: int, user: UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user.dict(exclude_unset=True)
    if 'password' in update_data:
        db_user.set_password(update_data['password'])
    
    for key, value in update_data.items():
        if key != 'password':
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user