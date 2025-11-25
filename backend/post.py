# backend/post.py
import os, sys, re, base64, tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from auth import authenticate
from models import ProtectedUser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.X import XAPI  # <- import your adapter

router = APIRouter()

class PostRequest(BaseModel):
    platform: str  # "x" (later: "reddit", "bluesky")
    text: str
    images: Optional[List[str]] = None  # data URLs like "data:image/png;base64,...."

DATA_URL_RE = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<b64>.+)$")

def _data_url_to_file(data_url: str) -> str:
    m = DATA_URL_RE.match(data_url)
    if not m:
        raise ValueError("Invalid data URL")
    mime = m.group("mime")
    b64 = m.group("b64")
    raw = base64.b64decode(b64)
    # pick extension from mime type
    ext = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp"
    }.get(mime, ".bin")
    fd, path = tempfile.mkstemp(prefix="postsmith_", suffix=ext)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
    return path

@router.post("/publish")
async def publish(req: PostRequest, user: ProtectedUser = Depends(authenticate)):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Missing text")
    platform = req.platform.lower()

    media_paths: List[str] = []
    try:
        for img in (req.images or []):
            media_paths.append(_data_url_to_file(img))

        if platform == "x":
            x = XAPI()
            result = x.post_tweet(text=req.text.strip(), media_paths=media_paths or None)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform '{platform}'")

        if not result.get("success", False):
            raise HTTPException(status_code=502, detail=f"Post failed: {result.get('error','unknown error')}")

        # Optionally: persist a “posted” message to chats for history/traceability
        # (reuse your Message model if desired)

        return {"ok": True, "platform": platform, "result": result}
    finally:
        # cleanup temp files
        for p in media_paths:
            try:
                os.remove(p)
            except Exception:
                pass
