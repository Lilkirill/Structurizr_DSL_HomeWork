from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from fastapi.openapi.utils import get_openapi

app = FastAPI()

SECRET_KEY = "ozon-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserAuth(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

MASTER_USER = {
    "username": "admin",
    "password": "secret",
    "role": "admin"
}

@app.post("/token", response_model=Token)
async def login(user_auth: UserAuth):
    if user_auth.username != MASTER_USER["username"] or user_auth.password != MASTER_USER["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token_data = {
        "sub": MASTER_USER["username"],
        "role": MASTER_USER["role"],
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    
    return {
        "access_token": jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM),
        "token_type": "bearer"
    }

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Ozon Auth Service",
        version="1.0.0",
        description="JWT Authentication Service",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi