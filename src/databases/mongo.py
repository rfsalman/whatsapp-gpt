from motor.motor_asyncio import AsyncIOMotorClient
from src.config import config

client = AsyncIOMotorClient(config.MONGODB_URI)
db = client[config.MONGO_INITDB_DATABASE]
