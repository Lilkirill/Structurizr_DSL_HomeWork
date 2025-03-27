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

class Product(BaseModel):
    id: int
    name: str
    price: float
    category: str

products_db = [
    {"id": 1, "name": "Smartphone", "price": 599.99, "category": "electronics"},
    {"id": 2, "name": "Laptop", "price": 1299.99, "category": "electronics"}
]

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

@app.get("/products/", response_model=List[Product],
         summary="Get all products")
async def get_products(_: dict = Depends(verify_token)):
    return products_db

@app.post("/products/", response_model=Product,
          status_code=201,
          summary="Create new product")
async def create_product(product: Product, payload: dict = Depends(verify_token)):
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    products_db.append(product.dict())
    return product

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Ozon Product Service",
        version="1.0.0",
        description="Product Management API",
        routes=app.routes,
    )
    
    openapi_schema["paths"]["/products/"]["post"]["requestBody"] = {
        "content": {
            "application/json": {
                "examples": {
                    "exampleProduct": {
                        "summary": "Example product",
                        "value": {
                            "id": 3,
                            "name": "Tablet",
                            "price": 399.99,
                            "category": "electronics"
                        }
                    }
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi