"""
Player API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.models.player import Player, PlayerStats, PlayerProjection

router = APIRouter()

@router.get("/players", response_model=List[dict])
async def get_players(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    position: Optional[str] = None
):
    """
    Get a list of players.
    
    Args:
        db: Database session
        skip: Number of players to skip
        limit: Maximum number of players to return
        position: Filter by player position
        
    Returns:
        List of players
    """
    query = db.query(Player)
    
    if position:
        query = query.filter(Player.position == position)
    
    players = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": player.id,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "position": player.position,
            "team": player.team,
            "status": player.status
        }
        for player in players
    ]

@router.get("/players/{player_id}", response_model=dict)
async def get_player(player_id: int, db: Session = Depends(get_db)):
    """
    Get a player by ID.
    
    Args:
        player_id: Player ID
        db: Database session
        
    Returns:
        Player details
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    return {
        "id": player.id,
        "first_name": player.first_name,
        "last_name": player.last_name,
        "position": player.position,
        "team": player.team,
        "status": player.status,
        "jersey_number": player.jersey_number,
        "height": player.height,
        "weight": player.weight,
        "age": player.age,
        "college": player.college,
        "years_pro": player.years_pro
    }

@router.get("/players/{player_id}/stats", response_model=List[dict])
async def get_player_stats(
    player_id: int,
    db: Session = Depends(get_db),
    season: Optional[int] = None
):
    """
    Get stats for a player.
    
    Args:
        player_id: Player ID
        db: Database session
        season: Filter by season
        
    Returns:
        Player stats
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    query = db.query(PlayerStats).filter(PlayerStats.player_id == player_id)
    
    if season:
        query = query.filter(PlayerStats.season == season)
    
    stats = query.all()
    
    return [
        {
            "id": stat.id,
            "season": stat.season,
            "week": stat.week,
            "games_played": stat.games_played,
            "fantasy_points": stat.fantasy_points,
            
            # Position-specific stats
            "pass_yards": stat.pass_yards if player.position == "QB" else None,
            "pass_touchdowns": stat.pass_touchdowns if player.position == "QB" else None,
            "interceptions": stat.interceptions if player.position == "QB" else None,
            
            "rush_yards": stat.rush_yards,
            "rush_touchdowns": stat.rush_touchdowns,
            
            "receptions": stat.receptions if player.position in ["WR", "TE", "RB"] else None,
            "receiving_yards": stat.receiving_yards if player.position in ["WR", "TE", "RB"] else None,
            "receiving_touchdowns": stat.receiving_touchdowns if player.position in ["WR", "TE", "RB"] else None,
        }
        for stat in stats
    ] 