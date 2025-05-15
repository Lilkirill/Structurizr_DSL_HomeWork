from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List


app = FastAPI(
    title="Cart Service API",
    description="API для корзины покупок",
    version="1.0.0"
)


fake_cart = []

class CartItem(BaseModel):
    product_id: int
    quantity: int

    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "quantity": 2
            }
        }


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/cart", 
         response_model=List[CartItem],
         tags=["Cart"])
def get_cart():
    return fake_cart


@app.post("/cart", 
          response_model=CartItem,
          status_code=status.HTTP_201_CREATED,
          tags=["Cart"])
def add_to_cart(item: CartItem):
    if item.quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Минимум 1"
        )
    fake_cart.append(item)
    return item


@app.delete("/cart", 
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Cart"])
def clear_cart():
    fake_cart.clear()
    return None


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "OK",
        "service": "cart_service",
        "items_in_cart": len(fake_cart)
    }