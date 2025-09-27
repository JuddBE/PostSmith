from typing import Optional
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

# Connect to mongodb cluster
MONGO_URI = "mongodb+srv://Judd:qqzSuMisdxZYJqzs@cluster0.s4nnpra.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["main"]
users = db["users"]

@app.get("/")
async def root():
    return {"users": list(users.find({"name": "James"}, {"_id": 0, "email": 1, "name": 1, "password": 1}))}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
