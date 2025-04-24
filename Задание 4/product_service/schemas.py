from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class ProductIn(BaseModel):
    name: str
    description: str
    price: float

class Product(ProductIn):
    id: str = Field(..., alias="_id")
