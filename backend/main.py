from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import tweepy
from typing import Optional
from dotenv import load_dotenv
import os

from models import User
from db import users
from auth import router as auth_router

load_dotenv()

# Full credentials, mix of v1.1 and v2
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
access_token = os.getenv('ACCESS_TOKEN')
access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')
bearer_token = os.getenv('BEARER_TOKEN')

# NOTE: Mix of v1.1 and v2 endpoints, they are still updating
client = tweepy.Client(bearer_token=bearer_token,
                            consumer_key=api_key,
                            consumer_secret=api_secret,
                            access_token=access_token,
                            access_token_secret=access_token_secret,
                            wait_on_rate_limit=True)

# Create app
app = FastAPI()
app.include_router(auth_router, prefix="/api/auth")

react_build = "../frontend/dist/"
app.mount("/assets", StaticFiles(directory=react_build + "assets"), name="assets")


@app.post("/api/test")
async def test():
    data = list(users.find())
    print(data)

# Page service
@app.get("/{full_path:path}")
async def serve(full_path: str):
    return FileResponse(react_build + "/index.html")

@app.post("/process")
def process_user_prompt(prompt: str, media_paths: Optional[str] = None):
    """Process/handle user prompt to decide if post, reply, quote, like, or retweet, and which social media platform to use given user prompt or prior context.
        Also handle media if provided, or if media generation is prompted.

    Args:
        prompt (str): User input prompt.
        media_paths (Optional[str]): Optional media paths for image or video (user supplied).
        
    Returns:
        N/A
    """
    pass

@app.post("/gen_post")
def generate_post(prompt: str, media_paths: Optional[str] = None):
    """Handle logic for calling model endpoint to generate post content, including image handling (caption or generate), post/reply/quote handling,
        and social media platform handling (make post fit for desired platform)
        
    Args:
        prompt (str): User input prompt.
        media_paths (Optional[str]): Optional media paths for image or video (user supplied).
    
    """
    pass

@app.post("/xpost")
def post_on_x(content: str, media_paths: Optional[str] = None, reply_tweet_id: str = None, quote_tweet_id: str = None):
    """Post tweet, quote tweet, or reply to tweet with mandatory text, optional media.
    
    Args:
        text (str): Tweet content (280 char max). #TODO: from LLM
        media_paths: List of paths to media files. # TODO: from image gen

    Returns:
        Dictionary with tweet details.
    """

    try: # try to post tweet
        # Conflict prevention
        if reply_tweet_id and quote_tweet_id:
            return {"success": False, "error": "A tweet cannot be both a reply and a quote at the same time."}

        # NOTE: For text-only tweets, there would just be no media_paths in the call.
        if not media_paths:
            response = client.create_tweet(text=content, in_reply_to_tweet_id=reply_tweet_id, quote_tweet_id=quote_tweet_id)
            return {"success": True, "tweet_id": response.data['id']}
        
        # For media tweets, you still need to upload media first and get media_ids
        # This requires v1.1 API for media upload, then pass media_ids to v2
        # NOTE: Fixed
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        api_v1 = tweepy.API(auth)
        
        media_ids = []
        for path in media_paths:
            media = api_v1.media_upload(path) # upload media first
            media_ids.append(media.media_id) # collect media IDs

        response = client.create_tweet(text=content, media_ids=media_ids, in_reply_to_tweet_id=reply_tweet_id, quote_tweet_id=quote_tweet_id) # post tweet with media
        return {"success": True, "tweet_id": response.data['id']}
        
    except Exception as e: # grab if errors
        return {"success": False, "error": str(e)}
    
@app.post("/xlike")
def like_tweet(tweet_id: str):
    try:
        user = client.get_me().data.id
        client.like(user_id=user, tweet_id=tweet_id)
        return {"status": True, "liked_tweet_id": tweet_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@app.post("/xrepost")
def retweet_tweet(tweet_id: str):
    try:
        user = client.get_me().data.id
        client.retweet(user_id=user, tweet_id=tweet_id)
        return {"status": True, "liked_tweet_id": tweet_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

