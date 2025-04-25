"""
Team API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.models.league import Team, TeamPlayer

router = APIRouter()

@router.get("/teams", response_model=List[dict])
async def get_teams(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    league_id: Optional[int] = None
):
    """
    Get a list of teams.
    
    Args:
        db: Database session
        skip: Number of teams to skip
        limit: Maximum number of teams to return
        league_id: Filter by league ID
        
    Returns:
        List of teams
    """
    query = db.query(Team)
    
    if league_id:
        query = query.filter(Team.league_id == league_id)
    
    teams = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": team.id,
            "name": team.name,
            "logo_url": team.logo_url,
            "league_id": team.league_id,
            "draft_position": team.draft_position
        }
        for team in teams
    ] 