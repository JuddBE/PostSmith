from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

from auth import authenticate
from models import ProtectedUser, PublicUser, Message, MessageContent
from ai import ai_chat
from db import chats


# Define router
router = APIRouter()


# Routes
@router.post("/send")
async def send(content: List[MessageContent],
               user: ProtectedUser = Depends(authenticate)):
    # The message the user sends
    messages = []
    incoming = Message(
        user_id=user.id,
        role="user",
        content=content
    )

    # The response
    response = await ai_chat(user, content)

    result = chats.insert_one(incoming.model_dump(exclude_none=True))
    incoming.id = result.inserted_id

    outgoing = Message(
        user_id=user.id,
        role="assistant",
        content=[{"type": "output_text", "text": response}]
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

    return messages
