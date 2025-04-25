"""
League API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.models.league import League

router = APIRouter()

@router.get("/leagues", response_model=List[dict])
async def get_leagues(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get a list of leagues.
    
    Args:
        db: Database session
        skip: Number of leagues to skip
        limit: Maximum number of leagues to return
        
    Returns:
        List of leagues
    """
    leagues = db.query(League).offset(skip).limit(limit).all()
    
    return [
        {
            "id": league.id,
            "name": league.name,
            "season": league.season,
            "league_type": league.league_type,
            "max_teams": league.max_teams,
            "public": league.public
        }
        for league in leagues
    ] 