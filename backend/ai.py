from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Optional, List
import json
import os
import pydantic
import tempfile

from x import post_twitter
from reddit import reddit_post_text, reddit_query_subreddits
from models import MessageContent, PrivateUser, Message
from db import chats, users


# Load env
load_dotenv()

# Model endpoint config
ENDPOINT = "https://postsmith-resource.cognitiveservices.azure.com/"
IMAGE_ENDPOINT = "https://ju876-mhveyjts-eastus.cognitiveservices.azure.com/"
DEPLOYMENT = "gpt-4-1-mini-2025-04-14-ft-590d5256b8e5429890f8496fc0aeb00e"
DEPLOYMENT = "gpt-4o-mini-2024-07-18"
IMAGE_DEPLOYMENT = "dall-e-3"
SUBSCRIPTION_KEY = os.getenv('AZURE_OPENAI_API_KEY')
IMAGE_API_KEY = os.getenv('AZURE_OPENAI_API_KEY_IMAGE')
API_VERSION = "2025-03-01-preview"


SYSTEM_PROMPT = (
    "You are a chill social media user. Take the user's ideas for posts, "
        "dramatize it, and create extremely concise posts that reflect their "
        "choice of social media and a typical user from it. "
    "Sound as human as possible. "
    "Unless specified by the user, "
        "do not use any formal or fancy words. Do not use emojis, "
        "hashtags, or em dashes. Do not mention that you are an AI model. Do not swear. "
    "Ask for an explicit confirmation before using the posting functions."
)


# Create client
client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=ENDPOINT,
    api_key=SUBSCRIPTION_KEY,
)

image_client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=IMAGE_ENDPOINT,
    api_key=IMAGE_API_KEY,
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
        elif output.name == "reddit_post_text":
            subreddit = args.get("subreddit")
            title = args.get("post_title")
            text = args.get("post_text")

            return reddit_post_text(user, subreddit, title, text)
        elif output.name == "reddit_search_subreddits":
            query = args.get("query")

            return reddit_query_subreddits(user, query)
        elif output.name == "generate_image":
            prompt = args.get("prompt")

            # Call image generation
            img_response = image_client.images.generate(
                model=IMAGE_DEPLOYMENT,
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="b64_json"
            )

            # Get image data TODO: CHECK THIS WORKS!!!
            image_b64 = json.loads(img_response.model_dump_json())['data'][0]['b64_json']
            data_url = f"data:image/png;base64,{image_b64}"

            # Return as data URL
            return ("image", data_url)
        else:
            return "Bad function name."
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
    print(len(user.images))

    response = client.responses.create(
        model=DEPLOYMENT,
        input=messages,
        tools=[
            {
                "type": "function",
                "name": "publish_tweet",
                "description": ("Make a post to twitter. "
                                "Needs explicit user confirmation about the parameters"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_text": {"type": "string"},
                        "post_images": {
                            "type": "array",
                            "description": ("An array of image indexs from previously generated or "
                                " uploaded images that the user wants to include in the post"),
                            "items": {
                                "type": "integer",
                                "description": ("An index into the available image array. "
                                    "corresponding to which image the user wants to include")
                            }
                        }
                    },
                    "required": ["post_text"],
                }
            },
            {
                "type": "function",
                "name": "reddit_post_text",
                "description": ("Make a text-based post to Reddit. "
                                "Needs explicit user confirmation about the parameters"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subreddit": {
                            "type": "string",
                            "description": "The subreddit to be posted to. do not include the 'r/' or 'u/'"
                        },
                        "post_title": {"type": "string"},
                        "post_text": {"type": "string"},
                    },
                    "required": ["subreddit", "post_title", "post_text"],
                }
            },
            {
                "type": "function",
                "name": "reddit_search_subreddits",
                "description": "Search for the top subreddits under a given query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query for looking for subreddits. Keep this concise."
                        },
                    },
                    "required": ["query"],
                }
            },
            {
                "type": "function",
                "name": "generate_image",
                "description": (
                    "Generate an image from a user prompt. "
                    "Use when the user asks for a picture, drawing, artwork, or any visual content."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Description of the image to generate"},
                        "style": {
                            "type": "string",
                            "description": "Optional artistic style like 'vivid', 'natural', 'sketch', etc.",
                        },
                    },
                    "required": ["prompt"],
                },
            },
        ]
    )

    output = response.output[0]

    # Forward to processor
    if output.type == "function_call":
        response = await call_function(user, output)
    else:
        response = output.content[0].text

    # Format the response
    if isinstance(response, str):
        # Pure text response
        message = Message(
            user_id=user.id,
            role="assistant",
            content=[{"type": "output_text", "text": response}]
        )
    elif response[0] == "image":
        # Image generation
        message = Message(
            user_id=user.id,
            role="user",
            content=[{"type": "input_image", "image_url": response[1]}]
        )
        users.update_one({"_id": user.id}, {"$push": {"images": response[1]}})
    return message
