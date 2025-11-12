import praw
import os
from typing import Optional
from dotenv import load_dotenv

"""
I am not sure if reddit has similar limitations to the X API

This can also be expanded but is main basic stuff
"""

load_dotenv()

# Reddit OAuth Configuration
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_REDIRECT_URI = os.getenv("REDDIT_REDIRECT_URI", "http://localhost:8000/auth/reddit/callback")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "PostSmith/1.0")


class RedditAPI:
    def __init__(self, refresh_token: str = None):
        """Initialize Reddit client with OAuth refresh token"""
        self.refresh_token = refresh_token
        self.reddit = None
        
        if refresh_token:
            self._login_with_token(refresh_token)
    
    def _login_with_token(self, refresh_token: str):
        """Login using OAuth refresh token"""
        try:
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                refresh_token=refresh_token,
                user_agent=REDDIT_USER_AGENT
            )
            
            # Verify token is active, if not it will raise an exception
            self.reddit.user.me()
            print(f"Logged in as u/{self.reddit.user.me().name}")
            
        except Exception as e:
            print(f"Failed to login with token: {e}")
            self.reddit = None
    
    def post_text(self, subreddit: str, title: str, text: str) -> dict:
        """Post text to a subreddit"""
        if not self.reddit:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            submission = self.reddit.subreddit(subreddit).submit(
                title=title,
                selftext=text
            )
            
            return {
                "success": True,
                "post_id": submission.id,
                "post_url": f"https://reddit.com{submission.permalink}",
                "subreddit": subreddit
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def post_link(self, subreddit: str, title: str, url: str) -> dict:
        """Post a link to a subreddit"""
        if not self.reddit:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            submission = self.reddit.subreddit(subreddit).submit(
                title=title,
                url=url
            )
            
            return {
                "success": True,
                "post_id": submission.id,
                "post_url": f"https://reddit.com{submission.permalink}",
                "subreddit": subreddit
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def post_image(self, subreddit: str, title: str, image_path: str) -> dict:
        """Post an image to a subreddit"""
        if not self.reddit:
            return {"success": False, "error": "Not authenticated"}
        
        if not os.path.exists(image_path):
            return {"success": False, "error": f"Image not found: {image_path}"}
        
        try:
            submission = self.reddit.subreddit(subreddit).submit_image(
                title=title,
                image_path=image_path
            )
            
            return {
                "success": True,
                "post_id": submission.id,
                "post_url": f"https://reddit.com{submission.permalink}",
                "subreddit": subreddit
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_info(self) -> dict: # Have tested this on own account and it works, not sure about others.
        """Get current user information"""
        if not self.reddit:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            me = self.reddit.user.me()
            
            return {
                "success": True,
                "username": me.name,
                "link_karma": me.link_karma,
                "comment_karma": me.comment_karma,
                "created_utc": me.created_utc,
                "is_gold": me.is_gold
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_reddit_auth_url(state: str) -> str:
    """Get Reddit OAuth authorization URL"""
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        redirect_uri=REDDIT_REDIRECT_URI,
        user_agent=REDDIT_USER_AGENT
    )
    
    # Request necessary scopes
    scopes = ["identity", "submit", "read", "mysubreddits"]
    
    return reddit.auth.url(scopes=scopes, state=state, duration="permanent")


def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for refresh token"""
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            redirect_uri=REDDIT_REDIRECT_URI,
            user_agent=REDDIT_USER_AGENT
        )
        
        # Exchange code for refresh token
        refresh_token = reddit.auth.authorize(code)
        
        # Get user info
        user = reddit.user.me()
        
        return {
            "success": True,
            "refresh_token": refresh_token,
            "username": user.name
        }
        
    except Exception as e:
        print(f"Token exchange failed: {e}")
        return {"success": False, "error": str(e)}