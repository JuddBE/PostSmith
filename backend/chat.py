from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

from auth import authenticate
from models import PrivateUser, Message, MessageContent
from ai import ai_chat
from db import chats, users


# Define router
router = APIRouter()


# Routes
@router.post("/send")
async def send(content: List[MessageContent],
               user: PrivateUser = Depends(authenticate)):
    # The response
    outgoing = await ai_chat(user, content)

    # Add to database and return value
    if len(content) == 0 or content[0].type != "input_text":
        raise HTTPException(status_code=400, detail="Bad input format")
    messages = []

    # Add any images seperately
    if len(content) > 1:
        images = Message(
            user_id=user.id,
            role="user",
            content=content[1:]
        )
        result = chats.insert_one(images.model_dump(exclude_none=True))
        images.id = result.inserted_id
        messages.append(images)
        users.update_one({"_id": user.id}, {"$push": {"images": {"$each":
            [cont.image_url for cont in content[1:]]}}})

    # Add the text input
    incoming = Message(
        user_id=user.id,
        role="user",
        content=content[:1]
    )
    result = chats.insert_one(incoming.model_dump(exclude_none=True))
    incoming.id = result.inserted_id
    messages.append(incoming)

    # Add the response
    result = chats.insert_one(outgoing.model_dump(exclude_none=True))
    outgoing.id = result.inserted_id
    messages.append(outgoing)

    print("returned structure")
    print(messages)

    # Return the sent and new for adding to the users chat
    return messages

@router.post("/clear")
async def clear(user: PrivateUser = Depends(authenticate)):
    chats.delete_many({"user_id": user.id});
    users.update_one({"_id": user.id}, {"$set": {"images": []}})

@router.get("/messages")
async def get(start: str = None, limit: int = 50,
              user: PrivateUser = Depends(authenticate)):
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
