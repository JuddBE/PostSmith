import tweepy # simplified Twitter API client
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
import json
import requests

# Load env variables, the api keys
load_dotenv()

class XAPI:
    def __init__(self):
        """Environment variables for accessing the X API
        NOTE: These should not be hardcoded!
        NOTE: Add them to a .env file which is in .gitignore
        """

        # Full credentials, mix of v1.1 and v2
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('API_SECRET')
        self.access_token = os.getenv('ACCESS_TOKEN')
        self.access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('BEARER_TOKEN')
        self.client_id = os.getenv('ClientID')
        self.client_secret = os.getenv('ClientSecret')

        # NOTE: Mix of v1.1 and v2 endpoints, they are still updating
        self.client = tweepy.Client(bearer_token=self.bearer_token,
                                    consumer_key=self.api_key,
                                    consumer_secret=self.api_secret,
                                    access_token=self.access_token,
                                    access_token_secret=self.access_token_secret,
                                    wait_on_rate_limit=True)
        
    ####################################################
    ################## Posting & Other #################
    ####################################################  
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> Dict:
        """Post tweet with mandatory text, optional media.
        
        Args:
            text (str): Tweet content (280 char max). #TODO: from LLM
            media_paths: List of paths to media files. # TODO: from image gen

            Returns:
                Dictionary with tweet details.
        """

        try: # try to post tweet
            # NOTE: For text-only tweets, there would just be no media_paths in the call.
            if not media_paths:
                response = self.client.create_tweet(text=text)
                return {"success": True, "tweet_id": response.data['id']}
            
            # For media tweets, you still need to upload media first and get media_ids
            # This requires v1.1 API for media upload, then pass media_ids to v2
            # NOTE: Fixed
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)
            api_v1 = tweepy.API(auth)
            
            media_ids = []
            for path in media_paths:
                media = api_v1.media_upload(path) # upload media first
                media_ids.append(media.media_id) # collect media IDs

            response = self.client.create_tweet(text=text, media_ids=media_ids) # post tweet with media
            return {"success": True, "tweet_id": response.data['id']}
            
        except Exception as e: # grab if errors
            return {"success": False, "error": str(e)}
    ####################################################
    ####################################################
    ####################################################
    
    ####################################################
    ################## Data Retrieval ##################
    # ####################################################    
    def get_user_info(self, username: str) -> Dict:
        """Get user information by username"""
        try:
            user = self.client.get_user(
                username=username,
                user_fields=['public_metrics', 'description', 'created_at', 'verified']
            )
            
            return {
                'id': user.data.id,
                'username': user.data.username,
                'name': user.data.name,
                'description': user.data.description,
                'followers': user.data.public_metrics['followers_count'],
                'following': user.data.public_metrics['following_count'],
                'tweets': user.data.public_metrics['tweet_count'],
                'verified': user.data.verified,
                'created_at': str(user.data.created_at)
            }
        except Exception as e:
            return {"error": str(e)}
        
    def get_user_tweets(self, username: str, max_results: int = 1) -> List[Dict]: # NOTE: Says the upper limit is one for free account
        """Get recent tweets from a specific user"""
        try:
            user = self.client.get_user(username=username)
            tweets = self.client.get_users_tweets(
                id=user.data.id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            return [
                {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': str(tweet.created_at),
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count']
                }
                for tweet in tweets.data or []
            ]
        except Exception as e:
            print(f"Error getting user tweets: {e}")
            return []
        
    def get_user_tweets_direct(self, username: str, max_results: int = 1) -> List[Dict]:
        """Get user tweets using direct API calls (bypasses tweepy limits)"""
        try:
            # First get the user ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            user_headers = {
                "Authorization": f"Bearer {self.bearer_token}"
            }
            
            user_response = requests.get(user_url, headers=user_headers)
            if user_response.status_code != 200:
                print(f"Error getting user: {user_response.status_code} - {user_response.text}")
                return []
            
            user_data = user_response.json()
            user_id = user_data['data']['id']
            
            # Then get their tweets with max_results=1
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            tweets_params = {
                "max_results": max_results,  # Can be 1 with direct API
                "tweet.fields": "created_at,public_metrics"
            }
            tweets_headers = {
                "Authorization": f"Bearer {self.bearer_token}"
            }
            
            tweets_response = requests.get(tweets_url, headers=tweets_headers, params=tweets_params)
            
            if tweets_response.status_code != 200:
                print(f"Error getting tweets: {tweets_response.status_code} - {tweets_response.text}")
                return []
            
            tweets_data = tweets_response.json()
            
            if 'data' not in tweets_data:
                return []
            
            return [
                {
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'created_at': tweet.get('created_at', ''),
                    'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                    'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                    'replies': tweet.get('public_metrics', {}).get('reply_count', 0)
                }
                for tweet in tweets_data['data']
            ]
            
        except Exception as e:
            print(f"Error in direct API call: {e}")
            return []
    ####################################################
    ####################################################
    ####################################################

    def check_rate_limits(self) -> Dict:
        """Check current rate limit status for key endpoints"""
        try:
            # Use tweepy's built-in rate limit checking
            # This uses the v1.1 API which has rate limit status endpoint
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)
            api_v1 = tweepy.API(auth)
            
            # Get rate limit status
            rate_limits = api_v1.rate_limit_status()
            
            # Extract useful information
            resources = rate_limits['resources']
            
            # Key endpoints we care about
            important_limits = {
                'tweets_post': resources.get('statuses', {}).get('/statuses/update', {}),
                'user_lookup': resources.get('users', {}).get('/users/show/:id', {}),
                'user_timeline': resources.get('statuses', {}).get('/statuses/user_timeline', {}),
                'search': resources.get('search', {}).get('/search/tweets', {})
            }
            
            return {
                'success': True,
                'limits': important_limits,
                'raw_data': rate_limits  # Full data if needed
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
