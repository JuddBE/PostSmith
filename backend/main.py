from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional

from models import User
from db import users
from auth import router as auth_router


# Create app
app = FastAPI()
app.include_router(auth_router, prefix="/api/auth")

react_build = "../frontend/dist/"
app.mount("/assets", StaticFiles(directory=react_build + "assets"), name="assets")


@app.post("/api/test")
async def test():
    data = list(users.find())
    print(data)

# Page service
@app.get("/{full_path:path}")
async def serve(full_path: str):
    return FileResponse(react_build + "/index.html")
