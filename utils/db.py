
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["koral"]

users_collection = db["users"]
# listeria_collection = db["fresh"]
listeria_collection = db["listeria"]
