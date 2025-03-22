from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os
from typing import Optional

from app.backend.database import get_db, User, AuthToken
from app.backend.models import MagicLinkRequest, MagicLinkResponse, TokenVerifyRequest, SessionResponse, CurrentUserResponse
from app.backend.mailer import send_magic_link_email

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

@router.post("/login", response_model=MagicLinkResponse)
async def login(request: MagicLinkRequest, db: Session = Depends(get_db)):
    """
    Request a magic link for authentication.
    
    Args:
        request: Magic link request with email
        db: Database session
        
    Returns:
        Message confirming the magic link was sent
    """
    # Get or create the user
    user = User.get_or_create(db, request.email)
    
    # Create an auth token
    auth_token = AuthToken.create_token(db, user.id)
    
    # Send the magic link email
    await send_magic_link_email(
        email=user.email,
        token=auth_token.token
    )
    
    return {"message": "Magic link sent to your email"}

@router.post("/verify", response_model=SessionResponse)
async def verify_token(request: TokenVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify a magic link token and return a JWT session token.
    
    Args:
        request: Token verification request
        db: Database session
        
    Returns:
        Session with access token and user data
        
    Raises:
        HTTPException: If token is invalid
    """
    # Validate the token
    user_id = AuthToken.validate_token(db, request.token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update last login time
    user.update_last_login(db)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user data
    """
    return current_user