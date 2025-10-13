from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import authenticate
from models import ProtectedUser, Message, PublicUser
from db import chats


# Define router
router = APIRouter()


# Data structures
class SendRequest(BaseModel):
    message: str


# Routes
@router.post("/send")
async def send(request: SendRequest,
               user: ProtectedUser = Depends(authenticate)):

    # The message the user sends
    messages = []
    incoming = Message(
        user_id=user.id,
        from_user=True,
        contents=request.message
    )
    result = chats.insert_one(incoming.model_dump(exclude_none=True))
    incoming.id = result.inserted_id


    # The response
    outgoing = Message(
        user_id=user.id,
        from_user=False,
        contents="Hello there"
    )
    result = chats.insert_one(outgoing.model_dump(exclude_none=True))
    outgoing.id = result.inserted_id

    # Return the sent and new for adding to the users chat
    return [incoming, outgoing]


@router.get("/messages")
async def get(start: str = None, limit: int = 50,
              user: ProtectedUser = Depends(authenticate)):
    query = { "_id": { "$lt": ObjectId(start) } } if start else {}
    query["user_id"] = user.id
    messages = [
        Message(**message) for message in
            chats.find(query)
                .sort("_id", -1)
                .limit(limit)
    ]
    messages.reverse()

    return messages;
