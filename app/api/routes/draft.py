"""
Draft API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.models.league import Draft, DraftPick

router = APIRouter()

@router.get("/drafts", response_model=List[dict])
async def get_drafts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    league_id: Optional[int] = None
):
    """
    Get a list of drafts.
    
    Args:
        db: Database session
        skip: Number of drafts to skip
        limit: Maximum number of drafts to return
        league_id: Filter by league ID
        
    Returns:
        List of drafts
    """
    query = db.query(Draft)
    
    if league_id:
        query = query.filter(Draft.league_id == league_id)
    
    drafts = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": draft.id,
            "league_id": draft.league_id,
            "date": draft.date,
            "status": draft.status
        }
        for draft in drafts
    ] 