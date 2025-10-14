# api/X.py
from X import XAPI

### X API Example Usage ###
def example_text_plus_media():
    """Basic test to post a tweet with media."""
    x_api = XAPI()
    result = x_api.post_tweet("A beautiful image of a planet with rings and a moon. (Saturn) and a moon (Moon) in the background. The colors are vibrant and the details are stunning. #planet #moon #space #astronomy", media_paths=["./heic2312a.jpg"])
    print(f"Result of test: {result}")

def example_text_only():
    """Basic test to post a tweet."""
    x_api = XAPI()
    result = x_api.post_tweet("Hello, world! This is a test tweet from the PostSmith application. #testing #PostSmith")
    print(f"Result of test: {result}")

def example_user_analysis(): # Example of engagement analysis for new posts
    """Example: Analyze a user's activity"""
    x_api = XAPI()
    
    # User stats
    user_info = x_api.get_user_info("elonmusk")
    user_tweets = x_api.get_user_tweets("elonmusk", max_results=1)

    # Recent Tweets
    print(f"Recent tweets by {user_info['username']}:")
    for tweet in user_tweets:
        print(f"- {tweet['text']} (Likes: {tweet['likes']}, Retweets: {tweet['retweets']}, Replies: {tweet['replies']})")

    
    if 'error' not in user_info:
        print(f"User: {user_info['name']} (@{user_info['username']})")
        print(f"Followers: {user_info['followers']:,}")
        # print(f"Recent tweets average likes: {sum(t['likes'] for t in user_tweets) / len(user_tweets):.1f}")

def run_rate_limit_check():
    """Check current rate limits"""
    x_api = XAPI()
    
    limits = x_api.check_rate_limits()
    
    if limits['success']:
        print("Rate Limits:")
        for endpoint, data in limits['limits'].items():
            if data:
                remaining = data.get('remaining', '?')
                total = data.get('limit', '?')
                print(f"  {endpoint}: {remaining}/{total}")
    else:
        print(f"Error: {limits['error']}")

def example_user_analysis_direct():
    """Example using direct API calls"""
    x_api = XAPI()
    
    # User stats
    user_info = x_api.get_user_info("elonmusk")
    user_tweets = x_api.get_user_tweets_direct("elonmusk", max_results=1)  # Use direct method

    # Recent Tweets
    if user_tweets:
        print(f"Recent tweets by {user_info['username']}:")
        for tweet in user_tweets:
            print(f"- {tweet['text'][:100]}... (Likes: {tweet['likes']}, Retweets: {tweet['retweets']})")
    
    if 'error' not in user_info:
        print(f"User: {user_info['name']} (@{user_info['username']})")
        print(f"Followers: {user_info['followers']:,}")


if __name__ == "__main__":
    # Uncomment to test, should manage runs due to resource limits
    # example_text_plus_media()
    # example_text_only()
    # example_user_analysis() # NOTE: DONT USE, RATE LIMITS!!!!
    example_user_analysis_direct()
    run_rate_limit_check()
    pass