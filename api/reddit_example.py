from reddit import RedditAPI, get_reddit_auth_url, exchange_code_for_token
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import secrets
import os
import time

"""
Example of it all working
"""

# Store the code temporarily
auth_code = None
auth_state = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    
    def do_GET(self):
        global auth_code, auth_state
        
        # Parse the callback URL
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params and 'state' in params:
            auth_code = params['code'][0]
            received_state = params['state'][0]
            
            # Verify state matches
            if received_state == auth_state:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                        <body>
                            <h1>Authorization Successful!</h1>
                            <p>You can close this window and return to the terminal.</p>
                        </body>
                    </html>
                """)
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State mismatch error")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed")
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass


def oauth_login() -> str: # This may need to be different for PostSmith app??????? Probably does. I am not familiar with the whole process.
    """Perform OAuth login and return refresh token"""
    global auth_code, auth_state
    
    # Generate state for CSRF protection
    auth_state = secrets.token_urlsafe(32)
    
    # Get authorization URL
    auth_url = get_reddit_auth_url(auth_state)
    
    print("Opening browser for Reddit authorization...")
    print(f"If browser doesn't open, go to: {auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to handle callback
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    
    print("Waiting for authorization...")
    
    # Wait for callback (timeout after 2 minutes)
    start_time = time.time()
    while auth_code is None and time.time() - start_time < 120:
        server.handle_request()
    
    if auth_code:
        print("Authorization code received!")
        
        # Exchange code for token
        result = exchange_code_for_token(auth_code)
        
        if result["success"]:
            print(f"Successfully authenticated as u/{result['username']}")
            return result["refresh_token"]
        else:
            print(f"Token exchange failed: {result['error']}")
            return None
    else:
        print("Authorization timeout")
        return None


# Token saving. This may need to be different for the app. For example saving to database?
def save_token(token: str):
    """Save refresh token to file"""
    with open('.reddit_token', 'w') as f:
        f.write(token)
    print("Token saved to .reddit_token")
def load_token() -> str:
    """Load refresh token from file"""
    if os.path.exists('.reddit_token'):
        with open('.reddit_token', 'r') as f:
            return f.read().strip()
    return None


def example_oauth_post():
    """Example using OAuth"""
    
    # Try to load existing token
    token = load_token()
    
    if not token:
        print("No saved token found. Starting OAuth flow...\n")
        token = oauth_login()
        
        if token:
            save_token(token)
        else:
            print("OAuth failed")
            return
    else:
        print("Using saved token")
    
    # Create API instance with token
    reddit = RedditAPI(refresh_token=token)
    
    if not reddit.reddit:
        print("Failed to authenticate. Starting new OAuth flow...")
        token = oauth_login()
        if token:
            save_token(token)
            reddit = RedditAPI(refresh_token=token)
        else:
            return
    
    # Get user info to verify token works
    user_info = reddit.get_user_info()
    if user_info["success"]:
        print(f"\nLogged in as: u/{user_info['username']}")
        print(f"Karma: {user_info['link_karma']} link, {user_info['comment_karma']} comment\n")
    
    # Testing the various post types
    subreddit = input("Enter subreddit (default: test): ") or "test" # We can maybe make our own subreddit for testing but ive used r/test for now. Just enter test.
    title = input("Enter post title: ") # Title of the post to the subreddit.
    
    if not title.strip():
        print("Title required")
        return
    
    # Currently just basic posting. These can be swapped in easily to take in the model information for the post. Very similar to X API.
    print("\nPost type:")
    print("1. Text post")
    print("2. Link post")
    print("3. Image post")
    
    choice = input("Choose (1-3): ")
    
    if choice == "1":
        text = input("Enter post text: ")
        result = reddit.post_text(subreddit, title, text)
    elif choice == "2":
        url = input("Enter URL: ")
        result = reddit.post_link(subreddit, title, url)
    elif choice == "3":
        image_path = input("Enter image path: ")
        result = reddit.post_image(subreddit, title, image_path)
    else:
        print("Invalid choice")
        return
    
    if result["success"]:
        print(f"\nPosted successfully!")
        print(f"View at: {result['post_url']}")
    else:
        print(f"\nFailed: {result['error']}")


def clear_saved_token(): # Maybe clear from database? Its an option we can use but might not need.
    """Clear saved token"""
    if os.path.exists('.reddit_token'):
        os.remove('.reddit_token')
        print("Saved token cleared")
    else:
        print("No saved token found")


if __name__ == "__main__":
    print("Reddit API Test Example\n")
    print("Choose an option:")
    print("1. Post using OAuth")
    print("2. Clear saved token (force re-authentication)") # This is for testing but this is flow for clearing if needed
    
    choice = input("\nEnter choice (1-2): ")
    
    if choice == "1":
        example_oauth_post()
    elif choice == "2":
        clear_saved_token()
    else:
        print("Invalid choice")