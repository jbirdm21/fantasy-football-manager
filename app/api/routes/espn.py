"""
ESPN API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional

from app.db.base import get_db
from app.api.clients.espn import ESPNClient
from app.api.auth.jwt import get_current_user
from app.models.league import User
from app.config import DEFAULT_SEASON

router = APIRouter()
espn_client = ESPNClient()

@router.get("/espn/leagues", response_model=List[Dict[str, Any]])
async def get_leagues(
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year")
):
    """
    Get leagues for an ESPN user.
    
    Args:
        username: ESPN username
        password: ESPN password
        season: NFL season year
        
    Returns:
        List of leagues
    """
    try:
        return await espn_client.get_leagues(username, password, season)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching leagues from ESPN: {str(e)}"
        )

@router.get("/espn/league/{league_id}", response_model=Dict[str, Any])
async def get_league(
    league_id: int,
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year")
):
    """
    Get a league by ID from ESPN.
    
    Args:
        league_id: ESPN league ID
        username: ESPN username
        password: ESPN password
        season: NFL season year
        
    Returns:
        League data
    """
    try:
        return await espn_client.get_league(league_id, username, password, season)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching league from ESPN: {str(e)}"
        )

@router.get("/espn/league/{league_id}/teams", response_model=List[Dict[str, Any]])
async def get_teams(
    league_id: int,
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year")
):
    """
    Get teams in a league from ESPN.
    
    Args:
        league_id: ESPN league ID
        username: ESPN username
        password: ESPN password
        season: NFL season year
        
    Returns:
        List of teams
    """
    try:
        return await espn_client.get_teams(league_id, username, password, season)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching teams from ESPN: {str(e)}"
        )

@router.get("/espn/team/{team_id}/roster", response_model=Dict[str, Any])
async def get_roster(
    league_id: int,
    team_id: int,
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year")
):
    """
    Get a team's roster from ESPN.
    
    Args:
        league_id: ESPN league ID
        team_id: ESPN team ID
        username: ESPN username
        password: ESPN password
        season: NFL season year
        
    Returns:
        Team roster data
    """
    try:
        return await espn_client.get_roster(league_id, team_id, username, password, season)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching roster from ESPN: {str(e)}"
        )

@router.get("/espn/league/{league_id}/free-agents", response_model=List[Dict[str, Any]])
async def get_free_agents(
    league_id: int,
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year"),
    position: Optional[str] = Query(None, description="Filter by position (QB, RB, WR, TE, K, DST)")
):
    """
    Get free agents in a league from ESPN.
    
    Args:
        league_id: ESPN league ID
        username: ESPN username
        password: ESPN password
        season: NFL season year
        position: Optional position filter
        
    Returns:
        List of free agents
    """
    try:
        return await espn_client.get_free_agents(league_id, username, password, season, position)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching free agents from ESPN: {str(e)}"
        )

@router.get("/espn/league/{league_id}/scoreboard", response_model=Dict[str, Any])
async def get_scoreboard(
    league_id: int,
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year"),
    week: Optional[int] = Query(None, description="Week number")
):
    """
    Get scoreboard for a league from ESPN.
    
    Args:
        league_id: ESPN league ID
        username: ESPN username
        password: ESPN password
        season: NFL season year
        week: Optional week number
        
    Returns:
        Scoreboard data
    """
    try:
        return await espn_client.get_scoreboard(league_id, username, password, season, week)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching scoreboard from ESPN: {str(e)}"
        )

@router.get("/espn/player/{player_id}", response_model=Dict[str, Any])
async def get_player(
    player_id: int,
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year")
):
    """
    Get a player by ID from ESPN.
    
    Args:
        player_id: ESPN player ID
        username: ESPN username
        password: ESPN password
        season: NFL season year
        
    Returns:
        Player data
    """
    try:
        return await espn_client.get_player(player_id, username, password, season)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching player from ESPN: {str(e)}"
        )
        
@router.get("/espn/player/{player_id}/stats", response_model=Dict[str, Any])
async def get_player_stats(
    player_id: int,
    username: str = Query(..., description="ESPN username"),
    password: str = Query(..., description="ESPN password"),
    season: int = Query(DEFAULT_SEASON, description="Season year"),
    week: Optional[int] = Query(None, description="Week number")
):
    """
    Get stats for a player from ESPN.
    
    Args:
        player_id: ESPN player ID
        username: ESPN username
        password: ESPN password
        season: NFL season year
        week: Optional week number
        
    Returns:
        Player stats data
    """
    try:
        return await espn_client.get_player_stats(player_id, username, password, season, week)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching player stats from ESPN: {str(e)}"
        ) 