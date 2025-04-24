from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional


app = FastAPI(
    title="Product Service API",
    description="API для управления товарами",
    version="1.0.0",
    contact={
        "name": "Поддержка",
        "email": "support@example.com"
    }
)


fake_products_db = [
    {"id": 1, "name": "Ноутбук", "price": 50000, "stock": 10},
    {"id": 2, "name": "Смартфон", "price": 30000, "stock": 15}
]

class ProductBase(BaseModel):
    name: str
    price: float
    stock: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Ноутбук",
                "price": 50000,
                "stock": 10
            }
        }

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "product_service",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/products", 
         response_model=List[Product],
         tags=["Products"])
def get_products(
    skip: Optional[int] = 0,
    limit: Optional[int] = 100,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):

    result = fake_products_db[skip : skip + limit]
    
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    
    return result


@app.get("/products/{product_id}", 
         response_model=Product,
         tags=["Products"])
def get_product(product_id: int):

    for product in fake_products_db:
        if product["id"] == product_id:
            return product
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Product not found"
    )


@app.post("/products",  
          response_model=Product,
          status_code=status.HTTP_201_CREATED,
          tags=["Products"])
def create_product(product: ProductCreate):

    if product.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be positive"
        )
    if product.stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock cannot be negative"
        )
    
    new_id = max(p["id"] for p in fake_products_db) + 1 if fake_products_db else 1
    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock
    }
    fake_products_db.append(new_product)
    return new_product


@app.get("/health", tags=["Health"])
async def health_check():

    return {
        "status": "OK",
        "service": "product_service",
        "product_count": len(fake_products_db)
    }