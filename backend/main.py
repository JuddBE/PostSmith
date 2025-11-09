from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
import os

from auth import router as auth_router
from chat import router as chat_router
from oauth import router as oauth_router

load_dotenv()

# Create app
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_MIDDLEWARE_SECRET"))


# Link apis
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(oauth_router, prefix="/api/oauth")


# Link page service
react_build = "../frontend/dist/"
app.mount("/assets", StaticFiles(directory=react_build + "assets"), name="assets")
@app.get("/{full_path:path}")
async def serve(full_path: str):
    return FileResponse(react_build + "/index.html")
