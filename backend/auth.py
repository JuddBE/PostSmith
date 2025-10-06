from bson import ObjectId
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import hmac, hashlib, secrets
import jwt

from models import User, FullUser
from db import users, get_user

# Auth parameters
TOKEN_SECRET = "replacethiskey"
TOKEN_ALGORITHM = "HS256"
PASSWORD_HASH = hashlib.sha256
security = HTTPBearer()


# Define router
router = APIRouter()


# Data structures
class LoginRequest(BaseModel):
    email: str
    password: str
class RegistrationRequest(BaseModel):
    email: str
    password: str


# Tokens
def create_token(user_id: str):
    package = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(weeks=2)
    }
    token = jwt.encode(package, TOKEN_SECRET, algorithm=TOKEN_ALGORITHM)
    return token

def authenticate(packed: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Decode payload
        payload = jwt.decode(
            packed.credentials,
            TOKEN_SECRET,
            algorithms=[TOKEN_ALGORITHM]
        )

        # Return user or bad token
        user = get_user({"_id": ObjectId(payload["sub"])})
        if user == None:
            raise Exception()
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad token"
        )


# Routes
@router.post("/token")
async def token(user: User = Depends(authenticate)):
    return user.dict()

@router.post("/login")
async def login(request: LoginRequest):
    # Get user from the attempt
    user = users.find_one({"email": request.email}, {"password": 1, "seed": 1})
    if (user == None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad email or password"
        )

    # Check password
    password = hmac.new(
        user["seed"].encode(), request.password.encode(), PASSWORD_HASH
    ).hexdigest()
    if password != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad email or password"
        )

    # Return token
    return { "token": create_token(str(user["_id"])) }

@router.post("/register")
async def register(request: RegistrationRequest):
    # Check for conflicts
    existing = get_user({"email": request.email})
    if existing != None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email in use"
        )

    # Create seed and encode password
    seed = secrets.token_hex(32)
    password = hmac.new(
        seed.encode(), request.password.encode(), PASSWORD_HASH
    ).hexdigest()

    # Create user
    user = FullUser(
        email=request.email,
        password=password,
        seed=seed
    )
    result = users.insert_one(user.dict())

    #return token
    return { "token": create_token(str(result.inserted_id)) }
