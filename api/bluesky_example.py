from bluesky import BlueSkyAPI
from dotenv import load_dotenv
import os

load_dotenv()

def example_text_only():
    """Post text-only"""
    
    bsky = BlueSkyAPI()
    result = bsky.post("Hello Bluesky! Testing PostSmith integration. #bluesky #testing")
    
    if result["success"]:
        print(f"Posted successfully!")
        print(f"View at: {result['post_url']}")
    else:
        print(f"Failed: {result['error']}")


def example_with_image():
    """Post with image"""
    print("\n=== Post with Image ===")
    
    bsky = BlueSkyAPI()
    
    image_path = "space_image.jpg" # Random space image for testing
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return
    
    result = bsky.post(
        "Check out this amazing space image! #space #astronomy",
        media_path=image_path
    )
    
    if result["success"]:
        print(f"Posted with image!")
        print(f"View at: {result['post_url']}")
    else:
        print(f"Failed: {result['error']}")


def example_multiple_images():
    """Post with multiple images"""
    print("\n=== Post with Multiple Images ===")
    
    bsky = BlueSkyAPI()
    
    images = ["./image1.jpg", "./image2.jpg", "./image3.jpg"]
    
    result = bsky.post_multiple_images(
        "Multiple images test from PostSmith! #multipost",
        media_paths=images
    )
    
    if result["success"]:
        print(f"Posted {result['images_count']} images!")
        print(f"View at: {result['post_url']}")
    else:
        print(f"Failed: {result['error']}")


def example_get_profile():
    """Get profile info"""
    
    bsky = BlueSkyAPI()
    result = bsky.get_profile()
    
    if result["success"]:
        print(f"Handle: @{result['handle']}")
        print(f"Display Name: {result['display_name']}")
        print(f"Followers: {result['followers']}")
        print(f"Following: {result['following']}")
        print(f"Posts: {result['posts']}")
        print(f"Bio: {result['description']}")
    else:
        print(f"Failed: {result['error']}")


def example_get_timeline():
    """Get timeline"""
    
    bsky = BlueSkyAPI()
    result = bsky.get_timeline(limit=5)
    
    if result["success"]:
        for i, post in enumerate(result["posts"], 1):
            print(f"\n{i}. @{post['author']}")
            print(f"   {post['text'][:100]}...")
            print(f"   Likes: {post['likes']} | Reposts: {post['reposts']} | Replies: {post['replies']}")
    else:
        print(f"Failed: {result['error']}")


def interactive_post():
    """Interactive posting"""
    
    text = input("Enter your post text: ")
    if not text.strip():
        print("Empty post text")
        return
    
    include_image = input("Include an image? (y/n): ").lower() == 'y'
    
    bsky = BlueSkyAPI()
    
    if include_image:
        image_path = input("Enter image path: ")
        result = bsky.post(text, media_path=image_path)
    else:
        result = bsky.post(text)
    
    if result["success"]:
        print(f"\nPosted successfully!")
        print(f"View at: {result['post_url']}")
    else:
        print(f"\nFailed: {result['error']}")


if __name__ == "__main__":
    
    print("\nChoose a test:")
    print("1. Text-only post")
    print("2. Post with image")
    print("3. Post with multiple images")
    print("4. Get profile info")
    print("5. Get timeline")
    print("6. Interactive post")
    
    choice = input("\nEnter choice (1-6): ")
    
    if choice == "1":
        example_text_only()
    elif choice == "2":
        example_with_image()
    elif choice == "3":
        example_multiple_images()
    elif choice == "4":
        example_get_profile()
    elif choice == "5":
        example_get_timeline()
    elif choice == "6":
        interactive_post()
    else:
        print("Invalid choice")