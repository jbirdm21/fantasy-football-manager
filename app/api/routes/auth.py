"""
Authentication API routes for the Fantasy Football Manager.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict

from app.db.base import get_db
from app.models.league import User
from app.api.auth.jwt import create_access_token, get_current_user
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/token", response_model=Dict[str, str])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Generate a token for authentication.
    
    Args:
        form_data: Form data with username and password
        db: Database session
        
    Returns:
        Token
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In a real app, you would verify the password here
    # if not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(status_code=401, detail="Invalid password")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/users/me", response_model=Dict[str, str])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User information
    """
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email
    } 