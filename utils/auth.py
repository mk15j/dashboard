
import bcrypt
from utils.db import users_collection

def authenticate(username, password):
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return user
    return None
