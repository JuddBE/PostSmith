from fastapi import FastAPI, HTTPException, status, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openai import AzureOpenAI
from dotenv import load_dotenv

from auth import router as auth_router
from chat import router as chat_router


# Load env
load_dotenv()


# Create app
app = FastAPI()
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api/chat")

react_build = "../frontend/dist/"
app.mount("/assets", StaticFiles(directory=react_build + "assets"), name="assets")


# Page service
@app.get("/{full_path:path}")
async def serve(full_path: str):
    return FileResponse(react_build + "/index.html")
