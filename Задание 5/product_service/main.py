from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from schemas import Product, ProductIn
from crud import (
    create_product,
    get_product,
    get_all_products,
    update_product,
    delete_product
)
from database import init_db, db

app = FastAPI(title="Product Service (MongoDB)")

@app.on_event("startup")
async def startup_db():
    await init_db()

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.post("/products/", response_model=Product)
async def create(product_in: ProductIn):
    return await create_product(product_in)

@app.get("/products/", response_model=list[Product])
async def list_products():
    return await get_all_products()

@app.get("/products/{product_id}", response_model=Product)
async def read(product_id: str):
    product = await get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=Product)
async def update(product_id: str, product_in: ProductIn):
    updated = await update_product(product_id, product_in)
    if updated is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated

@app.delete("/products/{product_id}")
async def delete(product_id: str):
    success = await delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Deleted"}