from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from pydantic import BaseModel
from typing import Optional, List
import base64
import os
import time

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
    client_id=os.getenv("X_CLIENT_ID"),
    client_secret=os.getenv("X_CLIENT_SECRET"),
    access_token_url="https://api.twitter.com/2/oauth2/token",
    access_token_params=None,
    authorize_url="https://twitter.com/i/oauth2/authorize",
    authorize_params=None,
    api_base_url="https://api.twitter.com/2/",
    client_kwargs={
        "scope": "tweet.write tweet.read users.read offline.access",
        "token_endpoint_auth_method": "client_secret_basic",
        "code_challenge_method": "S256"
    }
)

# Utils
async def x_get_token(user: PrivateUser):
    # Doesn't need a refresh
    # change to or
    if user.x_expiration == None or time.time() < user.x_expiration - 30:
        return user.x_access_token

    # Attempt refresh
    try:
        print("going into")

        async with AsyncClient() as client:
            print("pre-response")
            auth_header = base64.b64encode(
                f"{x_oauth.client_id}:{x_oauth.client_secret}".encode()
            ).decode()

            response = await client.post(
                x_oauth.access_token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": user.x_refresh_token,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {auth_header}"
                },
            )
            print("response", response)
            response.raise_for_status()
        print("RESPONSE", response)
        token = response.json()
        users.update_one(
            {"_id": user.id},
            {"$set": {
                "x_access_token": token["access_token"],
                "x_expiration": token["expires_at"]
            }}
        )

        return token["access_token"]
    except Exception as e:
        print(e)
        #users.update_one(
            #{"_id": user.id},
            #{"$unset": {
                #"x_username": 1,
                #"x_access_token": 1,
                #"x_refresh_token": 1,
                #"x_expiration": 1
            #}}
        #)
        return None


async def post_twitter(user: PrivateUser, text: str, media_paths: Optional[List[str]] = None):
    # Get the access token
    if user.x_access_token == None:
        return "To post to twitter, first link your account in the settings panel."
    access_token = await x_get_token(user)
    if access_token == None:
        return "Your twitter login expired. To post, relink your account in the settings."

    # Make the post
    response = await x_oauth.post(
        "https://api.twitter.com/2/tweets",
        token={"access_token": access_token, "token_type": "bearer"},
        json={"text": text}
    )

    # Ensure succeeded
    if response.status_code != 201:
        return "Failed to post with error: " + response.text

    data = response.json().get("data", {})
    tid = data.get("id")
    if tid:
        return (
            "Posted to X! View your tweet here: "
            f"https://x.com/{user.x_username}/status/{tid}"
        )
    else:
        return "Posted to X!"


# Routes
@router.get("/x/login")
async def x_login(request: Request):
    redirect_uri = request.url_for("x_callback")
    return await x_oauth.authorize_redirect(request, redirect_uri)

@router.get("/x/cb")
async def x_callback(request: Request):
    base = str(request.base_url).rstrip("/")
    try:
        token = await x_oauth.authorize_access_token(request)
        user = await x_oauth.get("users/me", token=token)
    except Exception as e:
        return RedirectResponse(f"{base}/")

    frontend_uri = (
            f"{base}/oauth/x"
            f"?access_token={token['access_token']}"
            f"&refresh_token={token['refresh_token']}"
            f"&expires_at={token['expires_at']}"
            f"&username={user.json()['data']['username']}"
    )
    print("@redirecting", frontend_uri)
    return RedirectResponse(frontend_uri)

class SaveRequest(BaseModel):
    access_token: str
    refresh_token: str
    username: str
    expires_at: float
@router.post("/x/save")
async def x_save(request: SaveRequest, user: PrivateUser = Depends(authenticate)):
    users.update_one(
        {"_id": user.id},
        {"$set": {
            "x_access_token": request.access_token,
            "x_refresh_token": request.refresh_token,
            "x_expiration": request.expires_at,
            "x_username": request.username
        }}
    )


