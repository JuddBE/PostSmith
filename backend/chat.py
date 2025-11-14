from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import json

from auth import authenticate
from models import PrivateUser, Message
from ai import ai_chat, ai_describe
from db import chats, users


# Define router
router = APIRouter()


# Routes
class SendRequest(BaseModel):
    text: Optional[str] = ""
    imageuri: Optional[str] = ""
async def sendProcessor(request: SendRequest, user: PrivateUser):
    inputs = 0
    # If there was an image input, attempt to push it to the dataset
    if request.imageuri or "" != "":
        # Get a description of the image
        yield (json.dumps({"status": 1, "message": "Processing input..."}) + "\n").encode()
        await asyncio.sleep(0)
        description = await ai_describe(request.imageuri)
        index = len(user.images)
        users.update_one({"_id": user.id}, {"$push": {"images": request.imageuri}})
        user.images.append(request.imageuri)

        # Format image message
        message = Message(
                user_id=user.id,
                role="user",
                content_type="image",
                content=f"<IMAGE index={index}>\ntext_description: {description}\n</IMAGE>",
                imageuri=request.imageuri
            )

        # Push to database
        result = chats.insert_one(message.model_dump(exclude_none=True))
        message.id = result.inserted_id
        yield (message.json(exclude_none=True) + "\n").encode()
        await asyncio.sleep(0)
        inputs += 1


    # If there was a text input, attempt to push it to the dataset
    if (request.text or "").strip() != "":
        # Format text message
        message = Message(
                user_id=user.id,
                role="user",
                content_type="text",
                content=request.text
            )

        # Push to database and add to return value
        result = chats.insert_one(message.model_dump(exclude_none=True))
        message.id = result.inserted_id
        yield (message.json(exclude_none=True) + "\n").encode()
        await asyncio.sleep(0)
        inputs += 1


    # No changes, no reason to call model
    if inputs == 0:
        return

    # Call the chat model and push the result to the database
    message = None
    async for response in ai_chat(user):
        if isinstance(response, str):
            yield (json.dumps({"status": 1, "message": response}) + "\n").encode()
            await asyncio.sleep(0)
        else:
            message = response

    result = chats.insert_one(message.model_dump(exclude_none=True))
    message.id = result.inserted_id
    yield (message.json(exclude_none=True) + "\n").encode()
    await asyncio.sleep(0)
    return

@router.post("/send")
async def send(request: SendRequest,
               user: PrivateUser = Depends(authenticate)):
    return StreamingResponse(sendProcessor(request, user), media_type="text/plain")


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
