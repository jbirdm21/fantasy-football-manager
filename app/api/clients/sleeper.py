"""
Sleeper API client for the Fantasy Football Manager.
"""
import aiohttp
import logging
from typing import Dict, List, Any, Optional

from app.config import SLEEPER_API_BASE_URL

logger = logging.getLogger(__name__)

class SleeperClient:
    """
    Client for the Sleeper API.
    https://docs.sleeper.app/
    """
    
    def __init__(self, base_url: str = SLEEPER_API_BASE_URL):
        """
        Initialize the Sleeper API client.
        
        Args:
            base_url: Base URL for the Sleeper API
        """
        self.base_url = base_url
    
    async def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a request to the Sleeper API.
        
        Args:
            endpoint: API endpoint to call
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Error calling Sleeper API: {e}")
                raise Exception(f"Failed to call Sleeper API: {e}")
    
    async def get_all_nfl_players(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all NFL players from Sleeper.
        
        Returns:
            Dictionary of players by player ID
        """
        return await self._make_request("players/nfl")
    
    async def get_player(self, player_id: str) -> Dict[str, Any]:
        """
        Get a specific player by ID.
        
        Args:
            player_id: Sleeper player ID
            
        Returns:
            Player data
        """
        players = await self.get_all_nfl_players()
        return players.get(player_id, {})
    
    async def get_nfl_state(self) -> Dict[str, Any]:
        """
        Get the current NFL state (season, week, etc.).
        
        Returns:
            NFL state data
        """
        return await self._make_request("state/nfl")
    
    async def get_user(self, username: str) -> Dict[str, Any]:
        """
        Get a user by username.
        
        Args:
            username: Sleeper username
            
        Returns:
            User data
        """
        return await self._make_request(f"user/{username}")
    
    async def get_user_leagues(self, user_id: str, season: str) -> List[Dict[str, Any]]:
        """
        Get leagues for a user in a specific season.
        
        Args:
            user_id: Sleeper user ID
            season: Season (e.g., "2023")
            
        Returns:
            List of leagues
        """
        return await self._make_request(f"user/{user_id}/leagues/nfl/{season}")
    
    async def get_league(self, league_id: str) -> Dict[str, Any]:
        """
        Get a league by ID.
        
        Args:
            league_id: Sleeper league ID
            
        Returns:
            League data
        """
        return await self._make_request(f"league/{league_id}")
    
    async def get_league_users(self, league_id: str) -> List[Dict[str, Any]]:
        """
        Get users in a league.
        
        Args:
            league_id: Sleeper league ID
            
        Returns:
            List of users
        """
        return await self._make_request(f"league/{league_id}/users")
    
    async def get_league_rosters(self, league_id: str) -> List[Dict[str, Any]]:
        """
        Get rosters in a league.
        
        Args:
            league_id: Sleeper league ID
            
        Returns:
            List of rosters
        """
        return await self._make_request(f"league/{league_id}/rosters")
    
    async def get_league_matchups(self, league_id: str, week: int) -> List[Dict[str, Any]]:
        """
        Get matchups for a specific week in a league.
        
        Args:
            league_id: Sleeper league ID
            week: Week number
            
        Returns:
            List of matchups
        """
        return await self._make_request(f"league/{league_id}/matchups/{week}")
    
    async def get_player_stats(self, season: str, week: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get player stats for a season or week.
        
        Args:
            season: Season (e.g., "2023")
            week: Week number (optional, if not provided, season stats are returned)
            
        Returns:
            Dictionary of player stats by player ID
        """
        endpoint = f"stats/nfl/regular/{season}"
        if week is not None:
            endpoint += f"/{week}"
        
        return await self._make_request(endpoint)
    
    async def get_player_projections(self, season: str, week: int) -> Dict[str, Dict[str, Any]]:
        """
        Get player projections for a week.
        
        Args:
            season: Season (e.g., "2023")
            week: Week number
            
        Returns:
            Dictionary of player projections by player ID
        """
        return await self._make_request(f"projections/nfl/regular/{season}/{week}") 