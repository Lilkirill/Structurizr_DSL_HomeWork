from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List
from jose import jwt
from fastapi.openapi.utils import get_openapi

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth_service:8000/token")

SECRET_KEY = "ozon-secret-key-2024"
ALGORITHM = "HS256"

class User(BaseModel):
    username: str
    email: str
    role: str = "customer"

fake_db = {
    "admin": User(username="admin", email="admin@ozon.ru", role="admin").dict()
}

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

@app.get("/users/", response_model=List[User],
         summary="List all users",
         description="Requires admin privileges")
async def get_users(payload: dict = Depends(verify_token)):
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return list(fake_db.values())

@app.post("/users/", response_model=User,
          status_code=201,
          summary="Create new user")
async def create_user(user: User, payload: dict = Depends(verify_token)):
    if user.username in fake_db:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )
    fake_db[user.username] = user.dict()
    return user

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Ozon User Service",
        version="1.0.0",
        description="User Management API",
        routes=app.routes,
    )
    
    openapi_schema["components"] = {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        }
    }
    
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi