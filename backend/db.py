from pymongo import MongoClient

from models import PublicUser

# Connect to mongodb cluster
MONGO_URI = "mongodb+srv://Judd:qqzSuMisdxZYJqzs@cluster0.s4nnpra.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


client = MongoClient(MONGO_URI)
db = client["main"]
users = db["users"]
chats = db["chats"]


# Default filter sensitive data
def get_user(query):
    data = users.find_one(query)
    if data is None:
        return None
    return PublicUser(**data)

def get_users(query):
    data = users.find(query)
    wrapped = [ PublicUser(**entry) for entry in list(data) ]
    return wrapped
