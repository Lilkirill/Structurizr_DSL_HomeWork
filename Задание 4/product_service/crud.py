from database import db
from schemas import ProductIn
from bson import ObjectId

collection = db["products"]

def serialize(product) -> dict:
    product["_id"] = str(product["_id"])
    return product

async def create_product(data: ProductIn):
    result = await collection.insert_one(data.dict())
    return serialize(await collection.find_one({"_id": result.inserted_id}))

async def get_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        return None
    product = await collection.find_one({"_id": ObjectId(product_id)})
    return serialize(product) if product else None

async def get_all_products():
    cursor = collection.find()
    return [serialize(doc) async for doc in cursor]

async def update_product(product_id: str, data: ProductIn):
    if not ObjectId.is_valid(product_id):
        return None
    await collection.update_one({"_id": ObjectId(product_id)}, {"$set": data.dict()})
    return await get_product(product_id)

async def delete_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        return False
    result = await collection.delete_one({"_id": ObjectId(product_id)})
    return result.deleted_count == 1
