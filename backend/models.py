from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


# Create a field that can take a string or ObjectId, stores as ObjectId
class IdField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, info):
        if isinstance(value, ObjectId):
            return value
        elif isinstance(value, str):
            return ObjectId(value)
        else:
            raise TypeError("IdField must be ObjectId or string")


# Base model that includes an _id.
#   .json() -> all to string, for http responses
#   .dict() -> retains ObjectId, for mongo use
#   .id     -> for accessing _id directly from the model
class MongoBaseModel(BaseModel):
    id: Optional[IdField] = Field(default=None, alias="_id")
    class Config:
        json_encoders = {
            IdField: str
        }
    def model_dump(self, **kwargs):
        kwargs["by_alias"] = True
        return super().model_dump(**kwargs)
    def dict(self, **kwargs):
        kwargs["by_alias"] = True
        return super().dict(**kwargs)
    def json(self, **kwargs):
        kwargs["by_alias"] = True
        return super().json(**kwargs)


# Contains public facing information about a user.
class PublicUser(MongoBaseModel):
    pass


# Contains all of the information a user should be able
# to obtain about themselves.
class ProtectedUser(PublicUser):
    email: str


# Contains restricted information that should be used
# only during creation or verification.
class PrivateUser(ProtectedUser):
    password: str
    seed: str


# Messages between a user and the service
class MessageContent(BaseModel):
    type: str
    text: Optional[str] = None
    image_url: Optional[str] = None

class Message(MongoBaseModel):
    user_id: IdField
    role: str
    content: List[MessageContent]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
