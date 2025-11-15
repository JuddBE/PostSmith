from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
import os

from auth import router as auth_router
from chat import router as chat_router
from x import router as x_router
from reddit import router as r_router
from bluesky import router as bluesky_router


load_dotenv()

# Create app
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_MIDDLEWARE_SECRET"))


# Link apis
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(x_router, prefix="/api/oauth/x")
app.include_router(r_router, prefix="/api/oauth/reddit")
app.include_router(bluesky_router, prefix="/api/bk")


# Link page service
react_build = "../frontend/dist/"
app.mount("/assets", StaticFiles(directory=react_build + "assets"), name="assets")
@app.get("/{full_path:path}")
async def serve(full_path: str):
    return FileResponse(react_build + "/index.html")
