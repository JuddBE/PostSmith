from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
import base64
import logging
import os
import praw
import time

from tools import image_to_file
from auth import authenticate
from models import ProtectedUser, PrivateUser
from db import users, get_user

load_dotenv()
router = APIRouter()
oauth = OAuth()

# Reddit OAuth Configuration
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "PostSmith/1.0"


r_oauth = oauth.register(
    name="reddit",
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    authorize_url="https://www.reddit.com/api/v1/authorize",
    access_token_url="https://www.reddit.com/api/v1/access_token",
    api_base_url="https://oauth.reddit.com",
    client_kwargs={
        "scope": "identity submit read",
        "token_endpoint_auth_method": "client_secret_basic"
    }
)


def reddit_post_text(user, subreddit, title, content):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            refresh_token=user.r_refresh_token,
            user_agent=REDDIT_USER_AGENT
        )

        post = reddit.subreddit(subreddit).submit(title=title, selftext=content)
        return "Posted to Reddit! View your post here: " + post.url
    except Exception as e:
        logging.error(e)
        try:
            return "Failed to post. " + str(e)
        except:
            return "Failed to post. Maybe a bad subreddit."

def reddit_post_image(user, subreddit, title, image):
    try:
        file = image_to_file(user, image)
        if file[0] == 1:
            raise Exception(file[1])

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            refresh_token=user.r_refresh_token,
            user_agent=REDDIT_USER_AGENT
        )

        post = reddit.subreddit(subreddit).submit_image(title=title, image_path=file[1])
        os.remove(file[1])
        return "Posted to Reddit! View your post here: " + post.url
    except Exception as e:
        logging.error(e)
        try:
            return "Failed to post. " + str(e)
        except:
            return "Failed to post. Maybe a bad subreddit."


def reddit_query_subreddits(user, query):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            refresh_token=user.r_refresh_token,
            user_agent=REDDIT_USER_AGENT
        )

        subreddits = reddit.subreddits.search(query, limit=5)

        results = ["Top results:"]
        for ind, sub in enumerate(subreddits):
            results.append(f"    {ind + 1}. r/{sub.display_name}  \"{sub.title}\"  Users: {sub.subscribers}")
        if (len(results) == 1):
            return "None found."
        return "\n".join(results)
    except Exception as e:
        logging.error("Failed to query subreddits")
        logging.error(e)
        return "Failed to search for subreddits."




# Routes
@router.get("/login")
async def reddit_login(request: Request):
    redirect_uri = str(request.url_for("reddit_callback"))
    print(redirect_uri)
    return await r_oauth.authorize_redirect(
        request, redirect_uri, duration="permanent")


@router.get("/cb")
async def reddit_callback(request: Request):
    base = str(request.base_url).rstrip("/")


    try:
        token = await r_oauth.authorize_access_token(request)
        user = await r_oauth.get("api/v1/me", token=token)
        username = user.json()["name"]
        refresh_token = token.get("refresh_token")
    except Exception as e:
        logging.error("Failed to obtain token %s", e)
        return RedirectResponse(f"{base}/")

    frontend_uri = (
            f"{base}/oauth/reddit"
            f"?refresh_token={refresh_token}"
            f"&username={username}"
    )
    return RedirectResponse(frontend_uri)

class SaveRequest(BaseModel):
    refresh_token: str
    username: str
@router.post("/save")
async def reddit_save(request: SaveRequest, user: PrivateUser = Depends(authenticate)):
    users.update_one(
        {"_id": user.id},
        {"$set": {
            "r_refresh_token": request.refresh_token,
            "r_username": request.username
        }}
    )


@router.post("/unlink")
async def reddit_unlink(user: PrivateUser = Depends(authenticate)):
    users.update_one(
        {"_id": user.id},
        {"$unset": {
            "r_refresh_token": 1,
            "r_username": 1
        }}
    )


