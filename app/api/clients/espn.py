"""
ESPN API client for the Fantasy Football Manager.
"""
import aiohttp
import logging
from typing import Dict, List, Any, Optional

from app.config import ESPN_API_KEY

logger = logging.getLogger(__name__)

class ESPNClient:
    """
    Client for the ESPN Fantasy Football API.
    """
    
    def __init__(self, api_key: str = ESPN_API_KEY):
        """
        Initialize the ESPN API client.
        
        Args:
            api_key: ESPN API key
        """
        self.api_key = api_key
        self.base_url = "https://fantasy.espn.com/apis/v3/games/ffl"
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the ESPN API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params if available
        if self.api_key:
            if params is None:
                params = {}
            params["apikey"] = self.api_key
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Error calling ESPN API: {e}")
                raise Exception(f"Failed to call ESPN API: {e}")
    
    async def get_league(
        self, 
        league_id: str, 
        season: int,
        scoring_period: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get league information.
        
        Args:
            league_id: ESPN league ID
            season: Season year (e.g., 2023)
            scoring_period: Week number
            
        Returns:
            League data
        """
        params = {
            "view": ["mTeam", "mRoster", "mMatchup"]
        }
        
        if scoring_period:
            params["scoringPeriodId"] = scoring_period
        
        return await self._make_request(f"seasons/{season}/segments/0/leagues/{league_id}", params)
    
    async def get_players(
        self, 
        season: int, 
        scoring_period: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get player information.
        
        Args:
            season: Season year (e.g., 2023)
            scoring_period: Week number
            limit: Number of players to return
            offset: Offset for pagination
            
        Returns:
            Player data
        """
        params = {
            "view": "kona_player_info",
            "limit": limit,
            "offset": offset
        }
        
        if scoring_period:
            params["scoringPeriodId"] = scoring_period
        
        return await self._make_request(f"seasons/{season}/players", params)
    
    async def get_player_stats(
        self, 
        player_id: int, 
        season: int,
        scoring_period: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get player stats.
        
        Args:
            player_id: ESPN player ID
            season: Season year (e.g., 2023)
            scoring_period: Week number
            
        Returns:
            Player stats
        """
        params = {
            "view": ["kona_playercard"]
        }
        
        if scoring_period:
            params["scoringPeriodId"] = scoring_period
        
        return await self._make_request(f"seasons/{season}/players/{player_id}", params)
    
    async def get_free_agents(
        self, 
        league_id: str, 
        season: int,
        scoring_period: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get free agents in a league.
        
        Args:
            league_id: ESPN league ID
            season: Season year (e.g., 2023)
            scoring_period: Week number
            limit: Number of players to return
            offset: Offset for pagination
            
        Returns:
            Free agent data
        """
        params = {
            "view": "kona_player_info",
            "scoringPeriodId": scoring_period or 0,
            "limit": limit,
            "offset": offset
        }
        
        return await self._make_request(f"seasons/{season}/segments/0/leagues/{league_id}/players", params)
    
    async def get_scoreboard(
        self, 
        league_id: str, 
        season: int,
        scoring_period: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get scoreboard for a league.
        
        Args:
            league_id: ESPN league ID
            season: Season year (e.g., 2023)
            scoring_period: Week number
            
        Returns:
            Scoreboard data
        """
        params = {
            "view": ["mScoreboard", "mMatchupScore"]
        }
        
        if scoring_period:
            params["scoringPeriodId"] = scoring_period
        
        return await self._make_request(f"seasons/{season}/segments/0/leagues/{league_id}/scoreboard", params) 