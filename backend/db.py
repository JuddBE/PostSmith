from pymongo import MongoClient

# Connect to mongodb cluster
MONGO_URI = "mongodb+srv://Judd:qqzSuMisdxZYJqzs@cluster0.s4nnpra.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["main"]
users = db["users"]

users = {}
