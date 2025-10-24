from fastapi import FastAPI, HTTPException, status, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import tempfile
from openai import AzureOpenAI
import tweepy
from typing import Optional, List
from dotenv import load_dotenv
import base64
import os

from models import User
from db import users
from auth import router as auth_router

load_dotenv()

# Full credentials, mix of v1.1 and v2
# api_key = os.getenv('API_KEY')
# api_secret = os.getenv('API_SECRET')
# access_token = os.getenv('ACCESS_TOKEN')
# access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')
# bearer_token = os.getenv('BEARER_TOKEN')

# # NOTE: Mix of v1.1 and v2 endpoints, they are still updating
# client = tweepy.Client(bearer_token=bearer_token,
#                             consumer_key=api_key,
#                             consumer_secret=api_secret,
#                             access_token=access_token,
#                             access_token_secret=access_token_secret,
#                             wait_on_rate_limit=True)

# Model endpoint config
endpoint = "https://postsmith-resource.cognitiveservices.azure.com/"
model_name = "gpt-4o-mini"
deployment = "gpt-4o-mini-2024-07-18"

subscription_key = os.getenv('AZURE_OPENAI_API_KEY')
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)


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

# @app.post("/process")
# def process_user_prompt(prompt: str, media_paths: Optional[List[str]] = File(None)):
#     """Process/handle user prompt to decide if post, reply, quote, like, or retweet, and which social media platform to use given user prompt or prior context.
#         Also handle media if provided, or if media generation is prompted.

#     Args:
#         prompt (str): User input prompt.
#         media_paths (Optional[str]): Optional media paths for image or video (user supplied).
        
#     Returns:
#         N/A
#     """
#     pass


def encode_image_to_data_url(path):
    with open(path, "rb") as f:
        img_bytes = f.read()
    encoded = base64.b64encode(img_bytes).decode("utf-8")
    ext = path.split(".")[-1].lower()
    mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
    return f"data:image/{mime};base64,{encoded}"

@app.post("/gen_post/")
async def generate_post(prompt: str, files: Optional[List[str]] = File(None)):
    """Handle logic for calling model endpoint to generate post content, including image handling (caption or generate), post/reply/quote handling,
        and social media platform handling (make post fit for desired platform)
        
    Args:
        prompt (str): User input prompt.
        media_paths (Optional[List[str]]): Optional media paths for image or video (user supplied).
    
    """
    # Make data URLs for images if any
    image_urls = []
    if files:
        for file in files:
            suffix = "." + file.filename.split(".")[-1]
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp.write(await file.read())
            temp.close()
            image_urls.append(encode_image_to_data_url(temp.name))

    if image_urls:
        # Setup message (image + text) for model
        message_content = [{"type": "text", "text": prompt}]
        for url in image_urls:
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": url
                }
            })
        messages=[
            {
                "role": "system",
                "content": "You are a chill social media user.Take the user's ideas for posts, dramatize it, and create extremely concise posts that reflect their choice of social media and a typical user from it. Sound as human as possible. Unless specified by the user, do not use any formal or fancy words. Do not use emojis, hashtags, or em dashes.",
            },
            {
                "role": "user",
                "content": message_content
            }
        ]

        # Call model
        model_res = client.chat.completions.create(
            messages=messages,
            max_tokens=4096,
            temperature=1.3,
            top_p=1.0,
            model=deployment
        )

        return {"post_content": model_res.choices[0].message['content']}
    else:
        # Setup message (text only) for model
        messages=[
            {
                "role": "system",
                "content": "You are a chill social media user.Take the user's ideas for posts, dramatize it, and create extremely concise posts that reflect their choice of social media and a typical user from it. Sound as human as possible. Unless specified by the user, do not use any formal or fancy words. Do not use emojis, hashtags, or em dashes.",
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Call model
        model_res = client.chat.completions.create(
            messages=messages,
            max_tokens=4096,
            temperature=1.3,
            top_p=1.0,
            model=deployment
        )

        return {"post_content": model_res.choices[0].message.content}
    

# @app.post("/xpost")
# def post_on_x(content: str, media_paths: Optional[List[str]] = File(None), reply_tweet_id: str = None, quote_tweet_id: str = None):
#     """Post tweet, quote tweet, or reply to tweet with mandatory text, optional media.
    
#     Args:
#         text (str): Tweet content (280 char max). #TODO: from LLM
#         media_paths: List of paths to media files. # TODO: from image gen

#     Returns:
#         Dictionary with tweet details.
#     """

#     try: # try to post tweet
#         # Conflict prevention
#         if reply_tweet_id and quote_tweet_id:
#             return {"success": False, "error": "A tweet cannot be both a reply and a quote at the same time."}

#         # NOTE: For text-only tweets, there would just be no media_paths in the call.
#         if not media_paths:
#             response = client.create_tweet(text=content, in_reply_to_tweet_id=reply_tweet_id, quote_tweet_id=quote_tweet_id)
#             return {"success": True, "tweet_id": response.data['id']}
        
#         # For media tweets, you still need to upload media first and get media_ids
#         # This requires v1.1 API for media upload, then pass media_ids to v2
#         # NOTE: Fixed
#         auth = tweepy.OAuthHandler(api_key, api_secret)
#         auth.set_access_token(access_token, access_token_secret)
#         api_v1 = tweepy.API(auth)
        
#         media_ids = []
#         for path in media_paths:
#             media = api_v1.media_upload(path) # upload media first
#             media_ids.append(media.media_id) # collect media IDs

#         response = client.create_tweet(text=content, media_ids=media_ids, in_reply_to_tweet_id=reply_tweet_id, quote_tweet_id=quote_tweet_id) # post tweet with media
#         return {"success": True, "tweet_id": response.data['id']}
        
#     except Exception as e: # grab if errors
#         return {"success": False, "error": str(e)}
    
# @app.post("/xlike")
# def like_tweet(tweet_id: str):
#     try:
#         user = client.get_me().data.id
#         client.like(user_id=user, tweet_id=tweet_id)
#         return {"status": True, "liked_tweet_id": tweet_id}
#     except Exception as e:
#         return {"success": False, "error": str(e)}
    
# @app.post("/xrepost")
# def retweet_tweet(tweet_id: str):
#     try:
#         user = client.get_me().data.id
#         client.retweet(user_id=user, tweet_id=tweet_id)
#         return {"status": True, "liked_tweet_id": tweet_id}
#     except Exception as e:
#         return {"success": False, "error": str(e)}

