from typing import Optional, List
import base64
import os
import tempfile


# Model endpoint config
ENDPOINT = "https://postsmith-resource.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-4o-mini-2024-07-18"
SUBSCRIPTION_KEY = os.getenv('AZURE_OPENAI_API_KEY')
API_VERSION = "2024-12-01-preview"

SYSTEM_PROMPT = (
    "You are a chill social media user.Take the user's ideas for posts, "
        "dramatize it, and create extremely concise posts that reflect their "
        "choice of social media and a typical user from it. "
    "Sound as human as possible. "
    "Unless specified by the user, "
        "do not use any formal or fancy words. Do not use emojis, "
        "hashtags, or em dashes."
)


# Create client
client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=ENDPOINT,
    api_key=SUBSCRIPTION_KEY,
)


# Main functionality
async def chat(prompt: str = Form(...), files: Optional[List[str]] = File(None)):
    """Handle logic for calling model endpoint to generate post content,
        including image handling (caption or generate), post/reply/quote handling,
        and social media platform handling (make post fit for desired platform)

    Args:
        prompt (str): User input prompt.
        media_paths (Optional[List[str]]):
            Optional media paths for image or video (user supplied).
    """

    message_content = [{"type": "text", "text": prompt}]

    # Convert any images to data URIs
    ## MOVE TO FRONTEND
    image_urls = []
    if files:
        for file in files:
            suffix = "." + file.filename.split(".")[-1]
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp.write(await file.read())
            temp.close()
            image_urls.append(encode_image_to_data_url(temp.name))

    # Add URIs to prompt
    for url in image_urls:
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": url
            }
        })

    # Define messages
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
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
        model=DEPLOYMENT
    )

    # Return the result
    return {"post_content": model_res.choices[0].message['content']}


# Utility functions
def encode_image_to_data_url(path):
    with open(path, "rb") as f:
        img_bytes = f.read()
    encoded = base64.b64encode(img_bytes).decode("utf-8")
    ext = path.split(".")[-1].lower()
    mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
    return f"data:image/{mime};base64,{encoded}"
