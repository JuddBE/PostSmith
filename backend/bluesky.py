from blueskysocial import Client, Post, Image
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel

from tools import image_to_file
from auth import authenticate
from models import ProtectedUser, PrivateUser
from db import users

# Environment
router = APIRouter()

async def bk_post(user, text, images):
    if not user.bk_username:
        return "To post to bluesky, first link your account in the settings panel."

    # Authenticate
    client = Client()
    try:
        client.authenticate(user.bk_username, user.bk_password)
    except Exception as e:
        await bk_unlink(user)
        return "Failed to authenticate with bluesky. Relink your account and make sure to use your app password, not your account password. \nError: " + str(e)

    # Format post
    if not images:
        post = Post(text)
    else:
        media = []
        files = [image_to_file(user, image, small=True) for image in images]
        for ind, file in enumerate(files):
            if file[0] == 1:
                return "Failed upload image(s) to bluesky: " + file[1]
            media.append(Image(file[1], alt_text="Image "+str(ind)))

        post = Post(text, with_attachments=media)

    # Make post
    try:
        result = client.post(post)
        # Get URL
        try:
            print(res)
            parts = res['uri'][5:].split("/")
            return f"Posted to Bluesky! View at https://profile/{parts[0]}/post/{parts[2]}"
        except:
            return "Posted to Bluesky!"
    except Exception as e:
        return "Failed to post: " + str(e)


# Routes
class SaveRequest(BaseModel):
    username: str
    password: str
@router.post("/save")
async def bk_save(request: SaveRequest, user: PrivateUser = Depends(authenticate)):
    users.update_one(
        {"_id": user.id},
        {"$set": {
            "bk_username": request.username,
            "bk_password": request.password,
        }}
    )

@router.post("/unlink")
async def bk_unlink(user: PrivateUser = Depends(authenticate)):
    users.update_one(
        {"_id": user.id},
        {"$unset": {
            "bk_username": 1,
            "bk_password": 1,
        }}
    )
