from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import hmac, hashlib, secrets
import jwt

from models import User
from db import users

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
def create_token(user: User):
    package = {
        "sub": user.email,
        "exp": datetime.utcnow() + timedelta(weeks=2)
    }
    token = jwt.encode(package, TOKEN_SECRET, algorithm=TOKEN_ALGORITHM)
    print(token);
    return token

def authenticate(packed: HTTPAuthorizationCredentials = Depends(security)):
    try:
        print(packed.credentials)
        payload = jwt.decode(
            packed.credentials, TOKEN_SECRET, algorithms=[TOKEN_ALGORITHM]
        )
        print
        if payload["sub"] in users:
            return User(**users[payload["sub"]])
        raise Exception()
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad token"
        )


# Routes
@router.post("/token")
async def token(user: User = Depends(authenticate)):
    return {
        "email": user.email
    }

@router.post("/login")
async def login(request: LoginRequest):
    # Get user
    if request.email not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad email or password"
        )

    # Check password
    user = User(**users[request.email])
    password = hmac.new(
        user.seed.encode(), request.password.encode(), PASSWORD_HASH
    ).hexdigest()
    if password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad email or password"
        )

    # Return token
    return { "token": create_token(user) }

@router.post("/register")
async def register(request: RegistrationRequest):
    # Check for conflicts
    if request.email in users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email in use"
        )

    # Add user
    seed = secrets.token_hex(32)
    password = hmac.new(
        seed.encode(), request.password.encode(), PASSWORD_HASH
    ).hexdigest()

    user = User(
        email=request.email,
        password=password,
        seed=seed
    )
    users[request.email] = user.dict()

    #return token
    return { "token": create_token(user) }
