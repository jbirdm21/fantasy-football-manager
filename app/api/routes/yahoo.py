"""
Yahoo API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional

from app.db.base import get_db
from app.api.clients.yahoo import YahooClient
from app.config import DEFAULT_SEASON

router = APIRouter()
yahoo_client = YahooClient()

@router.get("/yahoo/authorize", response_model=Dict[str, str])
async def authorize():
    """
    Get the Yahoo OAuth authorization URL.
    
    Returns:
        Dict with authorization URL
    """
    try:
        return {"authorization_url": yahoo_client.get_authorization_url()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Yahoo authorization URL: {str(e)}"
        )

@router.post("/yahoo/token", response_model=Dict[str, str])
async def get_token(code: str = Query(..., description="Yahoo OAuth code")):
    """
    Exchange authorization code for access token.
    
    Args:
        code: Yahoo OAuth code
        
    Returns:
        Dict with access token
    """
    try:
        return {"access_token": yahoo_client.get_access_token(code)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Yahoo access token: {str(e)}"
        )

@router.get("/yahoo/leagues", response_model=List[Dict[str, Any]])
async def get_leagues(
    token: str = Query(..., description="Yahoo OAuth token"),
    season: int = Query(DEFAULT_SEASON, description="Season year")
):
    """
    Get leagues for a Yahoo user.
    
    Args:
        token: Yahoo OAuth token
        season: NFL season year
        
    Returns:
        List of leagues
    """
    try:
        return await yahoo_client.get_leagues(token, season)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching leagues from Yahoo: {str(e)}"
        )

@router.get("/yahoo/league/{league_id}", response_model=Dict[str, Any])
async def get_league(
    league_id: str,
    token: str = Query(..., description="Yahoo OAuth token")
):
    """
    Get a league by ID from Yahoo.
    
    Args:
        league_id: Yahoo league ID
        token: Yahoo OAuth token
        
    Returns:
        League data
    """
    try:
        return await yahoo_client.get_league(league_id, token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching league from Yahoo: {str(e)}"
        )

@router.get("/yahoo/league/{league_id}/teams", response_model=List[Dict[str, Any]])
async def get_teams(
    league_id: str,
    token: str = Query(..., description="Yahoo OAuth token")
):
    """
    Get teams in a league from Yahoo.
    
    Args:
        league_id: Yahoo league ID
        token: Yahoo OAuth token
        
    Returns:
        List of teams
    """
    try:
        return await yahoo_client.get_teams(league_id, token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching teams from Yahoo: {str(e)}"
        )

@router.get("/yahoo/team/{team_id}/roster", response_model=Dict[str, Any])
async def get_roster(
    league_id: str,
    team_id: str,
    token: str = Query(..., description="Yahoo OAuth token")
):
    """
    Get a team's roster from Yahoo.
    
    Args:
        league_id: Yahoo league ID
        team_id: Yahoo team ID
        token: Yahoo OAuth token
        
    Returns:
        Team roster data
    """
    try:
        return await yahoo_client.get_roster(league_id, team_id, token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching roster from Yahoo: {str(e)}"
        )

@router.get("/yahoo/league/{league_id}/free-agents", response_model=List[Dict[str, Any]])
async def get_free_agents(
    league_id: str,
    token: str = Query(..., description="Yahoo OAuth token"),
    position: Optional[str] = Query(None, description="Filter by position (QB, RB, WR, TE, K, DEF)")
):
    """
    Get free agents in a league from Yahoo.
    
    Args:
        league_id: Yahoo league ID
        token: Yahoo OAuth token
        position: Optional position filter
        
    Returns:
        List of free agents
    """
    try:
        return await yahoo_client.get_free_agents(league_id, token, position)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching free agents from Yahoo: {str(e)}"
        )

@router.get("/yahoo/league/{league_id}/scoreboard", response_model=Dict[str, Any])
async def get_scoreboard(
    league_id: str,
    token: str = Query(..., description="Yahoo OAuth token"),
    week: Optional[int] = Query(None, description="Week number")
):
    """
    Get scoreboard for a league from Yahoo.
    
    Args:
        league_id: Yahoo league ID
        token: Yahoo OAuth token
        week: Optional week number
        
    Returns:
        Scoreboard data
    """
    try:
        return await yahoo_client.get_scoreboard(league_id, token, week)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching scoreboard from Yahoo: {str(e)}"
        )

@router.get("/yahoo/player/{player_id}", response_model=Dict[str, Any])
async def get_player(
    player_id: str,
    token: str = Query(..., description="Yahoo OAuth token")
):
    """
    Get a player by ID from Yahoo.
    
    Args:
        player_id: Yahoo player ID
        token: Yahoo OAuth token
        
    Returns:
        Player data
    """
    try:
        return await yahoo_client.get_player(player_id, token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching player from Yahoo: {str(e)}"
        )
        
@router.get("/yahoo/player/{player_id}/stats", response_model=Dict[str, Any])
async def get_player_stats(
    player_id: str,
    token: str = Query(..., description="Yahoo OAuth token"),
    week: Optional[int] = Query(None, description="Week number")
):
    """
    Get stats for a player from Yahoo.
    
    Args:
        player_id: Yahoo player ID
        token: Yahoo OAuth token
        week: Optional week number
        
    Returns:
        Player stats data
    """
    try:
        return await yahoo_client.get_player_stats(player_id, token, week)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching player stats from Yahoo: {str(e)}"
        ) 