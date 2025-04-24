from motor.motor_asyncio import AsyncIOMotorClient
import os
from test_data import test_products

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client["product_db"]

async def init_db():
    collection = db["products"]
    count = await collection.count_documents({})
    if count == 0:
        await collection.insert_many(test_products)
        await collection.create_index("name")
