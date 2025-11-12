from atproto import Client as BlueskyClient
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Bluesky Configuration (using app passwords for now as I cant get a good OAuth flow working, pretty sure its not released yet officially)
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")


class BlueSkyAPI:
    def __init__(self, handle: str = None, app_password: str = None):
        """Initialize Bluesky client with handle and app password"""
        self.handle = handle or BLUESKY_HANDLE
        self.app_password = app_password or BLUESKY_APP_PASSWORD
        self.client = None
        
        if self.handle and self.app_password:
            self._login()
    
    def _login(self):
        """Login to Bluesky"""
        try:
            self.client = BlueskyClient()
            self.client.login(self.handle, self.app_password)
            print(f"Logged in as @{self.handle}")
        except Exception as e:
            print(f"Failed to login: {e}")
            self.client = None
    
    def post(self, text: str, media_path: Optional[str] = None) -> dict:
        """Post to Bluesky"""
        if not self.client:
            return {
                "success": False,
                "error": "Not logged in to Bluesky"
            }
        
        try:
            # Handle media if provided
            if media_path and os.path.exists(media_path):
                with open(media_path, 'rb') as f:
                    img_data = f.read()
                
                # Upload image
                upload = self.client.upload_blob(img_data)
                
                # Create post with image
                response = self.client.send_post(
                    text=text,
                    embed={
                        '$type': 'app.bsky.embed.images',
                        'images': [{
                            'alt': '',
                            'image': upload.blob
                        }]
                    }
                )
            else:
                # Text-only post
                response = self.client.send_post(text=text)
            
            # Get post URI and create URL - Can be useful to quickly view the post
            post_id = response.uri.split('/')[-1]
            post_url = f"https://bsky.app/profile/{self.handle}/post/{post_id}"
            
            return { # Return the post URL and ID for reference and maybe for future use
                "success": True,
                "post_id": post_id,
                "post_url": post_url,
                "uri": response.uri
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def post_multiple_images(self, text: str, media_paths: list[str]) -> dict:
        """Post with multiple images (max 4)"""
        if not self.client:
            return {"success": False, "error": "Not logged in"}
        
        try:
            # Filter existing images and limit to 4
            existing_paths = [p for p in media_paths if os.path.exists(p)][:4]
            
            if not existing_paths:
                return {"success": False, "error": "No valid image paths provided"}
            
            # Upload all images
            images = []
            for img_path in existing_paths:
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                upload = self.client.upload_blob(img_data)
                images.append({
                    'alt': f'Image {len(images) + 1}',
                    'image': upload.blob
                })
            
            # Create post with multiple images
            response = self.client.send_post(
                text=text,
                embed={
                    '$type': 'app.bsky.embed.images',
                    'images': images
                }
            )
            
            post_id = response.uri.split('/')[-1]
            post_url = f"https://bsky.app/profile/{self.handle}/post/{post_id}"
            
            return {
                "success": True,
                "post_id": post_id,
                "post_url": post_url,
                "images_count": len(images)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_profile(self) -> dict:
        """Get profile information"""
        if not self.client:
            return {"success": False, "error": "Not logged in"}
        
        try:
            profile = self.client.get_profile(self.handle)
            
            return {
                "success": True,
                "handle": profile.handle,
                "display_name": profile.display_name,
                "followers": profile.followers_count,
                "following": profile.follows_count,
                "posts": profile.posts_count,
                "description": profile.description,
                "avatar": profile.avatar
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_timeline(self, limit: int = 10) -> dict:
        """Get home timeline"""
        if not self.client:
            return {"success": False, "error": "Not logged in"}
        
        try:
            timeline = self.client.get_timeline(limit=limit)
            
            posts = []
            for item in timeline.feed:
                posts.append({
                    "author": item.post.author.handle,
                    "text": item.post.record.text,
                    "created_at": item.post.record.created_at,
                    "likes": item.post.like_count,
                    "reposts": item.post.repost_count,
                    "replies": item.post.reply_count
                })
            
            return {
                "success": True,
                "posts": posts
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}