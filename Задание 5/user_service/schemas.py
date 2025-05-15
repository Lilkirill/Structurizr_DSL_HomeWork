from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import Optional, Dict, Any
from datetime import datetime
import json
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, 
                         regex="^[a-zA-Z0-9_]+$",
                         example="john_doe")
    email: EmailStr = Field(..., example="user@example.com")
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.USER)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UserRole: lambda v: v.value
        }

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="SecurePass123")
    
    @validator('password')
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = None

    @root_validator
    def check_at_least_one_field(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values

class UserOut(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "last_login": "2023-01-02T12:00:00"
            }
        }

    def to_redis_dict(self) -> Dict[str, Any]:
        """Convert model to dict suitable for Redis storage"""
        data = self.dict()
        data['created_at'] = data['created_at'].isoformat()
        if data['last_login']:
            data['last_login'] = data['last_login'].isoformat()
        return data

    @classmethod
    def from_redis_dict(cls, data: Dict[str, Any]):
        """Create model from Redis-stored dict"""
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_login' in data and data['last_login']:
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        return cls(**data)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str