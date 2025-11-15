from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Optional, List
import json
import os
import pydantic
import tempfile

from x import post_twitter
from reddit import reddit_post_text, reddit_post_image, reddit_query_subreddits
from models import PrivateUser, Message
from db import chats, users


# Load env
load_dotenv()

# Model endpoint config
ENDPOINT = "https://postsmith-resource.cognitiveservices.azure.com/"
IMAGE_ENDPOINT = "https://ju876-mhveyjts-eastus.cognitiveservices.azure.com/"
CHAT_DEPLOYMENT = "gpt-4-1-mini-2025-04-14-ft-590d5256b8e5429890f8496fc0aeb00e"
DESCRIBE_DEPLOYMENT = "gpt-4o-mini-2024-07-18"
IMAGE_DEPLOYMENT = "dall-e-3"
SUBSCRIPTION_KEY = os.getenv('AZURE_OPENAI_API_KEY')
IMAGE_API_KEY = os.getenv('AZURE_OPENAI_API_KEY_IMAGE')
API_VERSION = "2025-03-01-preview"


SYSTEM_PROMPT = (
    "You are a chill social media user. Take the user's ideas for posts, "
        "dramatize it, and create extremely concise posts that reflect their "
        "choice of social media and a typical user from it. You are able to post to Twitter or Reddit. "
    "Sound as human as possible. "
    "Never generate content that would be innapropriate in a university context. "
    "Always steer conversations towards creating or improving posts. "
    "If the user speaks about unrelated topis, politely redirect the conversation back to generating posts. "
    "Be cooporative and helpful to the user, but avoid casual chitchat, greetings, or small talk. "
    "Unless specified by the user, "
        "do not use any formal or fancy words. Do not use emojis, "
        "hashtags, or em dashes. Do not mention that you are an AI model. Do not swear. "
    "Ask for an explicit confirmation before using the posting functions. "
    "Images are provided to you in the following structure: "
    "<IMAGE index={number}>\n"
    "text_description: {description of the image}\n"
    "</IMAGE> "
    "The 'index' is the authoritative reference to the externel image storage. "
    "The 'text_description' is a human-readable interpretation of the image, *not* a replacement "
    "for the actual image. "
    "When reasoning about images, the description can be guidance, but the index is the actual "
    "identity. "
    "When a tool function requires an image, always provide the numeric index exactly as given. "
    "Do not rewrite or alter the '<IMAGE>' tag format when generating responses. "
    "Never generate content including this image tag, if the user ever asks for an image, always "
    "assume they are talking about the generate image tool. "
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
        match output.name:
            case "publish_tweet":
                text = args.get("post_text")
                images = args.get("post_images")
                if text == None:
                    return "Missing post text, try again later."

                return await post_twitter(user, text, images)
            case "reddit_post_text":
                subreddit = args.get("subreddit")
                title = args.get("post_title")
                text = args.get("post_text")

                return reddit_post_text(user, subreddit, title, text)
            case "reddit_post_image":
                subreddit = args.get("subreddit")
                title = args.get("post_title")
                image = args.get("post_image")

                return reddit_post_image(user, subreddit, title, image)
            case "reddit_search_subreddits":
                query = args.get("query")

                return reddit_query_subreddits(user, query)
            case "generate_image":
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
            case _:
                return "Bad function name."
    except Exception as e:
        return "Failed to call function, " + str(e)


async def ai_describe(imageuri):
    response = client.responses.create(
            model=DESCRIBE_DEPLOYMENT,
            input=[
                {
                    "role": "system",
                    "content": ("You are a visual analyst. Describe and interpret any image "
                        "you receive clearly and accurately.")
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Describe this image in detail."},
                        {"type": "input_image", "image_url": imageuri}
                    ]
                }
            ],
        )
    return response.output[0].content[0].text



async def ai_chat(user: PrivateUser):
    # Get a list of system descr, then history of conversation, then the new user message
    yield "Recalling"
    history = chats.find(
            {"user_id": user.id}, {"_id": 0, "role": 1, "content": 1}
    ).sort("_id")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *[
            { "role": message["role"], "content": message["content"] }
            for message in history
        ],
    ]

    yield "Thinking"
    response = client.responses.create(
        model=CHAT_DEPLOYMENT,
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
                                "description": "An image index"
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
                "name": "reddit_post_image",
                "description": ("Make a image-based post to Reddit. "
                                "Needs explicit user confirmation about the parameters"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subreddit": {
                            "type": "string",
                            "description": "The subreddit to be posted to. do not include the 'r/' or 'u/'"
                        },
                        "post_title": {"type": "string"},
                        "post_image": {
                            "type": "integer",
                            "description": ("An image index that the user wants to post. Must be "
                                "from a previously generated or uploaded image.")
                        },
                    },
                    "required": ["subreddit", "post_title", "post_image"],
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
        yield "Using tool"
        response = await call_function(user, output)
    else:
        response = output.content[0].text

    # Format the response
    # Pure text response
    if isinstance(response, str):
        yield Message(
                user_id=user.id,
                role="assistant",
                content_type="text",
                content=response
            )
    # Image generation
    elif response[0] == "image":
        # Get a description of the image
        yield "Processing generated image"
        description = await ai_describe(response[1])
        index = len(user.images)
        users.update_one({"_id": user.id}, {"$push": {"images": response[1]}})
        user.images.append(response[1])

        # Format for an image description/submission
        yield Message(
                user_id=user.id,
                role="assistant",
                content_type="image",
                content=f"<IMAGE index={index}>\ntext_description: {description}\n</IMAGE>",
                imageuri=response[1]
            )
    return
