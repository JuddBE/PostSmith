from dotenv import load_dotenv
from typing import List, Dict, Optional

import base64
import io
import json
import os
import requests
import tempfile
import tweepy
import time

from models import PrivateUser
from oauth import x_get_token


# Load keys
load_dotenv()
CLIENT_ID = os.getenv('X_CLIENT_ID')
CLIENT_SECRET = os.getenv('X_CLIENT_SECRET')


async def post(user: PrivateUser, text: str, media_paths: Optional[List[str]] = None):
    # Get the users access token
    if user.x_access_token == None:
        return "To post to twitter, first link your account in the settings panel."
    access_token = await x_get_token(user)
    if access_token == None:
        return "Your twitter login expired. To post, relink your account in the settings."

    print(access_token)

    # Define API connections
    client = tweepy.Client(
        consumer_key=CLIENT_ID,
        consumer_secret=CLIENT_SECRET,
        access_token=access_token,
        wait_on_rate_limit=False
    )

    print(client.get_me().data)

    # Submit the post
    try:
        media_ids = []

        response = client.create_tweet(text=text, media_ids=media_ids)
        tid = response.data["id"]

        return (
            "Posted to X! View your tweet here: "
            f"https://x.com/{user.x_username}/status/{tid}"
        )
    except Exception as e:
        return "Failed to post: " + str(e)




        # For media tweets, you still need to upload media first and get media_ids
        # This requires v1.1 API for media upload, then pass media_ids to v2
        #auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
        #auth.set_access_token(self.access_token, self.access_token_secret)
        #api_v1 = tweepy.API(auth)
        #for path in media_paths:
            # Extract image bytes
            #_, encoded = path.split(",", 1)
            #needed_padding = len(encoded) % 4
            #if needed_padding != 0:
                #encoded += "=" * (4 - needed_padding)
            #image_data = base64.b64decode(encoded)

            # Get suffix
            #mime = path.split(";");
            #suffix = ".png"
            #if len(mime) != 0:
                #if "jpg" in mime[0] or "jpeg" in mime[0]:
                    #suffix = ".jpg"

            # Write to a temp file, upload it
            #with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
                #tmp.write(image_data)
                #tmp.flush()
                #media = api_v1.media_upload(filename=tmp.name) # upload media first
            #media_ids.append(media.media_id) # collect media IDs
