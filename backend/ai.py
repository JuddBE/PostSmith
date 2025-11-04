from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Optional, List
import json
import os
import pydantic
import tempfile

from oauth import post_twitter
from models import MessageContent, PrivateUser
from db import chats


# Load env
load_dotenv()

# Model endpoint config
ENDPOINT = "https://postsmith-resource.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-4o-mini-2024-07-18"
SUBSCRIPTION_KEY = os.getenv('AZURE_OPENAI_API_KEY')
API_VERSION = "2025-03-01-preview"

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
async def call_function(user, output):
    try:
        args = json.loads(output.arguments)
        if output.name == "publish_tweet":
            text = args.get("post_text")
            images = args.get("post_images")
            if text == None:
                return "Missing post text, try again later."

            return await post_twitter(user, text, images)
        else:
            return "Missing post text."
    except Exception as e:
        return "Failed to call function, " + str(e)


async def ai_chat(user: PrivateUser, content: List[MessageContent]):
    """Handle logic for calling model endpoint to generate post content,
        including image handling (caption or generate), post/reply/quote handling,
        and social media platform handling (make post fit for desired platform)

    Args:
        content (List[MessageContent]: User input prompt.
    """
    # Get a list of system, then history of conversation, then the new user message
    history = chats.find(
            {"user_id": user.id}, {"_id": 0, "role": 1, "content": 1}
    ).sort("_id")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": [
            e.model_dump(exclude_none=True) for e in content
        ]}
    ]

    response = client.responses.create(
        model=DEPLOYMENT,
        input=messages,
        tools=[
            {
                "type": "function",
                "name": "publish_tweet",
                "description": "Make a post to twitter. Needs user confirmation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_text": {"type": "string"},
                        "post_images": {
                            "type": "array",
                            "description": ("An array of images, each provided as a data URL, "
                                "images that the user sends or that the assistant generates, that "
                                "the user wants to include in the tweet"),
                            "items": {
                                "type": "string",
                                "description": "A single image encoded as a data URL"
                            }
                        }
                    },
                    "required": ["post_text"],
                }
            }
        ]
    )

    output = response.output[0]

    # Forward to processor
    if output.type == "function_call":
        return await call_function(user, output)

    # Continue conversation
    return output.content[0].text
