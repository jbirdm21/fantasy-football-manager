"""
Sleeper API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional

from app.db.base import get_db
from app.api.clients.sleeper import SleeperClient
from app.api.auth.jwt import get_current_user
from app.models.league import User
from app.config import DEFAULT_SEASON

router = APIRouter()
sleeper_client = SleeperClient()

@router.get("/sleeper/nfl/players", response_model=Dict[str, Any])
async def get_all_nfl_players():
    """
    Get all NFL players from Sleeper.
    
    Returns:
        Dictionary of all NFL players
    """
    try:
        return await sleeper_client.get_all_nfl_players()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching NFL players from Sleeper: {str(e)}"
        )

@router.get("/sleeper/player/{player_id}", response_model=Dict[str, Any])
async def get_player(player_id: str):
    """
    Get a player by ID from Sleeper.
    
    Args:
        player_id: Sleeper player ID
        
    Returns:
        Player data
    """
    try:
        return await sleeper_client.get_player(player_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching player from Sleeper: {str(e)}"
        )

@router.get("/sleeper/nfl/state", response_model=Dict[str, Any])
async def get_nfl_state():
    """
    Get the current NFL state from Sleeper.
    
    Returns:
        NFL state data
    """
    try:
        return await sleeper_client.get_nfl_state()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching NFL state from Sleeper: {str(e)}"
        )

@router.get("/sleeper/user/{username}", response_model=Dict[str, Any])
async def get_user(username: str):
    """
    Get a user by username from Sleeper.
    
    Args:
        username: Sleeper username
        
    Returns:
        User data
    """
    try:
        return await sleeper_client.get_user(username)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user from Sleeper: {str(e)}"
        )

@router.get("/sleeper/user/{user_id}/leagues/nfl/{season}", response_model=List[Dict[str, Any]])
async def get_user_leagues(
    user_id: str,
    season: int = DEFAULT_SEASON
):
    """
    Get leagues for a user from Sleeper.
    
    Args:
        user_id: Sleeper user ID
        season: NFL season year
        
    Returns:
        List of leagues
    """
    try:
        return await sleeper_client.get_user_leagues(user_id, season)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user leagues from Sleeper: {str(e)}"
        )

@router.get("/sleeper/league/{league_id}", response_model=Dict[str, Any])
async def get_league(league_id: str):
    """
    Get a league by ID from Sleeper.
    
    Args:
        league_id: Sleeper league ID
        
    Returns:
        League data
    """
    try:
        return await sleeper_client.get_league(league_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching league from Sleeper: {str(e)}"
        )

@router.get("/sleeper/league/{league_id}/users", response_model=List[Dict[str, Any]])
async def get_league_users(league_id: str):
    """
    Get users in a league from Sleeper.
    
    Args:
        league_id: Sleeper league ID
        
    Returns:
        List of users
    """
    try:
        return await sleeper_client.get_league_users(league_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching league users from Sleeper: {str(e)}"
        )

@router.get("/sleeper/league/{league_id}/rosters", response_model=List[Dict[str, Any]])
async def get_league_rosters(league_id: str):
    """
    Get rosters in a league from Sleeper.
    
    Args:
        league_id: Sleeper league ID
        
    Returns:
        List of rosters
    """
    try:
        return await sleeper_client.get_league_rosters(league_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching league rosters from Sleeper: {str(e)}"
        )

@router.get("/sleeper/league/{league_id}/matchups/{week}", response_model=List[Dict[str, Any]])
async def get_league_matchups(
    league_id: str,
    week: int
):
    """
    Get matchups for a league and week from Sleeper.
    
    Args:
        league_id: Sleeper league ID
        week: Week number
        
    Returns:
        List of matchups
    """
    try:
        return await sleeper_client.get_league_matchups(league_id, week)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching league matchups from Sleeper: {str(e)}"
        )

@router.get("/sleeper/stats/nfl/regular/{season}/{week}", response_model=Dict[str, Any])
async def get_stats(
    season: int = DEFAULT_SEASON,
    week: int = 1
):
    """
    Get player stats for a week from Sleeper.
    
    Args:
        season: NFL season year
        week: Week number
        
    Returns:
        Player stats
    """
    try:
        return await sleeper_client.get_player_stats(season, week)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching player stats from Sleeper: {str(e)}"
        )

@router.get("/sleeper/projections/nfl/regular/{season}/{week}", response_model=Dict[str, Any])
async def get_projections(
    season: int = DEFAULT_SEASON,
    week: int = 1
):
    """
    Get player projections for a week from Sleeper.
    
    Args:
        season: NFL season year
        week: Week number
        
    Returns:
        Player projections
    """
    try:
        return await sleeper_client.get_player_projections(season, week)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching player projections from Sleeper: {str(e)}"
        ) 