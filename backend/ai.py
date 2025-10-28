import os
import pydantic
import tempfile
from openai import AzureOpenAI
from typing import Optional, List
from dotenv import load_dotenv
import json

from x import post_on_x
from models import MessageContent, PublicUser
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
async def ai_chat(user: PublicUser, content: List[MessageContent]):
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

    # Call model
    #model_res = client.chat.completions.create(
        #messages=messages,
        #max_tokens=4096,
        #temperature=1.3,
        #top_p=1.0,
        #model=DEPLOYMENT
    #)

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
                        "post_text": {"type": "string"}
                    },
                    "required": ["post_text"]
                }
            }
        ]
    )

    print("-----")
    print(response.output[0])
    output = response.output[0]
    print("-----")
    print(output)

    # Return the result
    if output.type == "function_call":
        if output.name == "publish_tweet":
            args = json.loads(output.arguments)
            post_on_x(args["post_text"])
    return output.content[0].text
