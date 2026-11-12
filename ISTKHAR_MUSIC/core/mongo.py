from motor.motor_asyncio import AsyncIOMotorClient as _mongo_client_
from pymongo import MongoClient

import config

if not config.MONGO_DB_URI:
    raise SystemExit(
        "MONGO_DB_URI is not set. Create a free MongoDB Atlas database and add its URL."
    )

_mongo_async_ = _mongo_client_(config.MONGO_DB_URI)
_mongo_sync_ = MongoClient(config.MONGO_DB_URI)
mongodb = _mongo_async_.Anon
pymongodb = _mongo_sync_.Anon
