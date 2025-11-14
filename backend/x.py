from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from pydantic import BaseModel
from typing import Optional, List
import base64
import datetime
import logging
import os
import time
import tweepy

from tools import image_to_file
from auth import authenticate
from models import ProtectedUser, PrivateUser
from db import users, get_user


# Initialize environment
load_dotenv()
router = APIRouter()
oauth = OAuth()


# X OAUTH
x_oauth = oauth.register(
    name="oauth",
    client_id=os.getenv("X_CONSUMER_KEY"),
    client_secret=os.getenv("X_CONSUMER_SECRET"),
    access_token_url="https://api.twitter.com/oauth/access_token",
    authorize_url="https://api.twitter.com/oauth/authorize",
    request_token_url="https://api.twitter.com/oauth/request_token",
    api_base_url="https://api.twitter.com/1.1/",
)

# Utils
async def post_twitter(user: PrivateUser, text: str, image_indices: Optional[List[str]] = None):
    # Get the access token
    if user.x_token == None:
        return "To post to twitter, first link your account in the settings panel."

    # Create client
    client = tweepy.Client(
                    consumer_key=os.getenv("X_CONSUMER_KEY"),
                    consumer_secret=os.getenv("X_CONSUMER_SECRET"),
                    access_token=user.x_token,
                    access_token_secret=user.x_token_secret
            )

    # Handle any images
    media = []
    if image_indices:
        api = tweepy.API(
                tweepy.OAuth1UserHandler(
                    os.getenv("X_CONSUMER_KEY"),
                    os.getenv("X_CONSUMER_SECRET"),
                    user.x_token,
                    user.x_token_secret
                ),
                wait_on_rate_limit=False
            )
        try:
            files = [image_to_file(user, image) for image in image_indices]
            for file in files:
                if file[0] == 1:
                    return "Failed to post to twitter: " + file[1]
                media.append(api.media_upload(filename=file[1]).media_id_string)
                print(media)
                os.remove(file[1])
        except Exception as e:
            logging.error("Failed to upload medias to Twitter. %s", e)
            return "Internal error, failed to upload image(s) to twitter"



    # Make the post
    try:
        if len(media) != 0:
            response = client.create_tweet(text=text, media_ids=media)
        else:
            response = client.create_tweet(text=text)
    except tweepy.TooManyRequests as e:
        reset = datetime.datetime.fromtimestamp(ereset_time)
        return "Failed to post, rate limit reached. Reset at: " + reset
    except Exception as e:
        return "Failed to post: " + str(e)

    return (
        "Posted to X! View your tweet here: "
        f"https://x.com/{user.x_username}/status/{response.data['id']}"
    )


# Routes
@router.get("/login")
async def x_login(request: Request):
    redirect_uri = str(request.url_for("x_callback"))
    return await x_oauth.authorize_redirect(request, redirect_uri)


@router.get("/cb")
async def x_callback(request: Request):
    base = str(request.base_url).rstrip("/")
    try:
        token = await x_oauth.authorize_access_token(request)
    except Exception as e:
        logging.error("callback error", e)
        return RedirectResponse(f"{base}/")

    frontend_uri = (
            f"{base}/oauth/x"
            f"?token={token['oauth_token']}"
            f"&token_secret={token['oauth_token_secret']}"
            f"&username={token['screen_name']}"
    )
    return RedirectResponse(frontend_uri)

class SaveRequest(BaseModel):
    token: str
    token_secret: str
    username: str
@router.post("/save")
async def x_save(request: SaveRequest, user: PrivateUser = Depends(authenticate)):
    users.update_one(
        {"_id": user.id},
        {"$set": {
            "x_token": request.token,
            "x_token_secret": request.token_secret,
            "x_username": request.username
        }}
    )


