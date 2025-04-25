"""
Authentication API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict

from app.db.base import get_db
from app.models.league import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
    
    return {
        "access_token": f"example_token_{user.id}",
        "token_type": "bearer"
    } 