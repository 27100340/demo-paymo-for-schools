from pymongo import MongoClient
uri = "mongodb+srv://baqarhassan702:<Binance-1-9090>@demo-paymo-for-schoolsd.qgwhvhy.mongodb.net/"
client = MongoClient(uri)
try:
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print(f"Error: {e}")

import logging
logging.basicConfig(level=logging.DEBUG)