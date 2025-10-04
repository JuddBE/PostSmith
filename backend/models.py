from pydantic import BaseModel

class FullUser(BaseModel):
    email: str
    password: str
    seed: str

class User(BaseModel):
    email: str
