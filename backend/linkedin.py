from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import logging
import os
import json
import requests

from auth import authenticate
from models import PrivateUser
from db import users

# Load environment variables
load_dotenv()

# Router
router = APIRouter()

# OAuth manager
oauth = OAuth()


###############################################################
################### LINKEDIN OAUTH SETUP ######################
###############################################################

"""
This file mirrors the structure of x.py and reddit.py, handling:

    - LinkedIn OAuth2 login
    - Callback + token exchange
    - Fetching the user's LinkedIn profile ID
    - Saving LinkedIn tokens to the database
    - Posting on behalf of authenticated users

NOTE:
LinkedIn DOES NOT support full OpenID Connect.
We use standard OAuth2 Authorization Code Flow.
"""

linkedin_oauth = oauth.register(
    name="linkedin",
    client_id=os.getenv("LINKEDIN_CLIENT_ID"),
    client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
    access_token_url="https://www.linkedin.com/oauth/v2/accessToken",
    authorize_url="https://www.linkedin.com/oauth/v2/authorization",
    api_base_url="https://api.linkedin.com/v2",
    client_kwargs={
        # Required for profile fetch + posting permissions
        "scope": "r_liteprofile w_member_social",
        "token_endpoint_auth_method": "client_secret_post",
    }
)


###############################################################
################### LINKEDIN POST FUNCTION #####################
###############################################################

async def post_linkedin(user: PrivateUser, text: str):
    """
    Create a text-only LinkedIn post on behalf of an authenticated user.

    Params:
        user (PrivateUser): Logged-in PostSmith user with saved tokens
        text (str): LLM-generated post content

    Returns:
        Success message or error string
    """

    # Ensure LinkedIn account is linked
    if not user.linkedin_access_token:
        return "Please link your LinkedIn account in settings before posting."

    access_token = user.linkedin_access_token

    ####################################################
    # STEP 1 — Fetch LinkedIn user URN (required to post)
    ####################################################
    try:
        profile_res = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if profile_res.status_code != 200:
            return f"Failed to fetch LinkedIn profile: {profile_res.text}"

        profile_data = profile_res.json()
        person_urn = f"urn:li:person:{profile_data['id']}"

    except Exception as e:
        logging.error("LinkedIn profile fetch error: %s", e)
        return "Internal error fetching LinkedIn profile."

    ####################################################
    # STEP 2 — UGC Post Creation (text only)           #
    ####################################################
    post_body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    try:
        post_res = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(post_body)
        )

        if post_res.status_code not in (200, 201):
            logging.error("LinkedIn post error: %s", post_res.text)
            return f"Failed to post to LinkedIn: {post_res.text}"

        return "Successfully posted to LinkedIn!"

    except Exception as e:
        logging.error("LinkedIn post failed: %s", e)
        return "Internal posting error."


###############################################################
############################ ROUTES ############################
###############################################################

@router.get("/login")
async def linkedin_login(request: Request):
    """
    Redirects user to LinkedIn's OAuth2 consent screen.
    """
    redirect_uri = str(request.url_for("linkedin_callback"))
    return await linkedin_oauth.authorize_redirect(request, redirect_uri)


@router.get("/cb")
async def linkedin_callback(request: Request):
    """
    OAuth2 callback route.
    
    - Exchanges authorization code for tokens
    - Fetches LinkedIn profile ID
    - Redirects user back to frontend with token info
    """

    base_url = str(request.base_url).rstrip("/")

    try:
        # Exchange code → access token
        token = await linkedin_oauth.authorize_access_token(request)
        access_token = token.get("access_token")
        refresh_token = token.get("refresh_token", "")

        # Identify user by LinkedIn ID
        profile = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        linkedin_id = profile.get("id")

    except Exception as e:
        logging.error("LinkedIn callback error: %s", e)
        return RedirectResponse(f"{base_url}/")

    # Redirect back to frontend (same flow as X + Reddit)
    frontend_redirect = (
        f"{base_url}/oauth/linkedin"
        f"?access_token={access_token}"
        f"&refresh_token={refresh_token}"
        f"&linkedin_id={linkedin_id}"
    )

    return RedirectResponse(frontend_redirect)


###############################################################
##################### SAVE / UNLINK ############################
###############################################################

class SaveRequest(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    linkedin_id: str


@router.post("/save")
async def linkedin_save(
    req: SaveRequest, 
    user: PrivateUser = Depends(authenticate)
):
    """
    Store LinkedIn OAuth tokens in the user's profile.
    Mirrors Reddit + X save functions.
    """
    users.update_one(
        {"_id": user.id},
        {"$set": {
            "linkedin_access_token": req.access_token,
            "linkedin_refresh_token": req.refresh_token,
            "linkedin_id": req.linkedin_id
        }}
    )
    return {"status": "ok"}


@router.post("/unlink")
async def linkedin_unlink(
    user: PrivateUser = Depends(authenticate)
):
    """
    Remove LinkedIn integration from the user's account.
    """
    users.update_one(
        {"_id": user.id},
        {"$unset": {
            "linkedin_access_token": 1,
            "linkedin_refresh_token": 1,
            "linkedin_id": 1
        }}
    )
    return {"status": "ok"}
