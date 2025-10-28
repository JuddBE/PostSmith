import tweepy
import os
from typing import Optional, List
from fastapi import File
from dotenv import load_dotenv

# Load env
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
                            wait_on_rate_limit=False)

# On rate limit, update database with until reset time
# Then select a new API st. reset time < current time

# On user post, if they are currently using a valid API, use their token,
# otherwise have them resign in



# Functions should just take a ProtectedUser
def post_on_x(content: str, media_paths: Optional[List[str]] = File(None), reply_tweet_id: str = None, quote_tweet_id: str = None):
    """Post tweet, quote tweet, or reply to tweet with mandatory text, optional media.

    Args:
        text (str): Tweet content (280 char max). #TODO: from LLM
        media_paths: List of paths to media files. # TODO: from image gen

    Returns:
        Dictionary with tweet details.
    """
    print("Posting on X with content: ", content)
    print(media_paths)
    try: # try to post tweet
        # Conflict prevention
        print("1")
        if reply_tweet_id and quote_tweet_id:
            return {"success": False, "error": "A tweet cannot be both a reply and a quote at the same time."}
        print("2")
        # NOTE: For text-only tweets, there would just be no media_paths in the call.
        if not media_paths:
            response = client.create_tweet(text=content, in_reply_to_tweet_id=reply_tweet_id, quote_tweet_id=quote_tweet_id)
            print("Posted Tweet. Response: ", str(response))
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

def like_tweet(tweet_id: str):
    try:
        user = client.get_me().data.id
        client.like(user_id=user, tweet_id=tweet_id)
        return {"status": True, "liked_tweet_id": tweet_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

def retweet_tweet(tweet_id: str):
    try:
        user = client.get_me().data.id
        client.retweet(user_id=user, tweet_id=tweet_id)
        return {"status": True, "liked_tweet_id": tweet_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
