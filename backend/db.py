from pymongo import MongoClient

from models import User

# Connect to mongodb cluster
MONGO_URI = "mongodb+srv://Judd:qqzSuMisdxZYJqzs@cluster0.s4nnpra.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


client = MongoClient(MONGO_URI)
db = client["main"]
users = db["users"]


# Default filter sensitive data
USER_FILTER = { "password": 0, "seed": 0 }
def get_user(query):
    data = users.find_one(query, USER_FILTER)
    if data == None:
        return None
    return User(**data)

def get_users(query):
    data = users.find(query, USER_FILTER)
    wrapped = [ User(**entry) for entry in list(data) ]
    return wrapped
