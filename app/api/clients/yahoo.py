"""
Yahoo Fantasy API client for the Fantasy Football Manager.
"""
import aiohttp
import logging
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.config import YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET

logger = logging.getLogger(__name__)

class YahooClient:
    """
    Client for the Yahoo Fantasy API.
    https://developer.yahoo.com/fantasysports/guide/
    """
    
    def __init__(
        self, 
        client_id: str = YAHOO_CLIENT_ID, 
        client_secret: str = YAHOO_CLIENT_SECRET
    ):
        """
        Initialize the Yahoo API client.
        
        Args:
            client_id: Yahoo OAuth client ID
            client_secret: Yahoo OAuth client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://fantasysports.yahooapis.com/fantasy/v2"
        self.token_url = "https://api.login.yahoo.com/oauth2/get_token"
        self.authorize_url = "https://api.login.yahoo.com/oauth2/request_auth"
        
        self.access_token = None
        self.token_expires_at = datetime.now()
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Get the URL for OAuth authorization.
        
        Args:
            redirect_uri: Redirect URI for OAuth callback
            
        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "language": "en-us"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange an authorization code for an access token.
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            Token response data
            
        Raises:
            Exception: If the token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        auth_header = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_header.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.token_url, data=data, headers=headers) as response:
                    response.raise_for_status()
                    token_data = await response.json()
                    
                    # Save token and expiration time
                    self.access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    return token_data
            except aiohttp.ClientError as e:
                logger.error(f"Error exchanging code for token: {e}")
                raise Exception(f"Failed to exchange code for token: {e}")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token.
        
        Args:
            refresh_token: Refresh token from previous token response
            
        Returns:
            Token response data
            
        Raises:
            Exception: If the token refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        auth_header = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_header.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.token_url, data=data, headers=headers) as response:
                    response.raise_for_status()
                    token_data = await response.json()
                    
                    # Save token and expiration time
                    self.access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    return token_data
            except aiohttp.ClientError as e:
                logger.error(f"Error refreshing token: {e}")
                raise Exception(f"Failed to refresh token: {e}")
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Yahoo Fantasy API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If the request fails or no access token is available
        """
        if not self.access_token or datetime.now() >= self.token_expires_at:
            raise Exception("No valid access token available. Please authorize first.")
        
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Error calling Yahoo API: {e}")
                raise Exception(f"Failed to call Yahoo API: {e}")
    
    async def get_user_leagues(self, game_key: str = "nfl") -> Dict[str, Any]:
        """
        Get leagues for the authenticated user.
        
        Args:
            game_key: Game key (default: "nfl")
            
        Returns:
            League data
        """
        return await self._make_request(f"users;use_login=1/games;game_keys={game_key}/leagues")
    
    async def get_league(self, league_key: str) -> Dict[str, Any]:
        """
        Get a league by key.
        
        Args:
            league_key: Yahoo league key
            
        Returns:
            League data
        """
        return await self._make_request(f"league/{league_key}")
    
    async def get_league_teams(self, league_key: str) -> Dict[str, Any]:
        """
        Get teams in a league.
        
        Args:
            league_key: Yahoo league key
            
        Returns:
            Team data
        """
        return await self._make_request(f"league/{league_key}/teams")
    
    async def get_team(self, team_key: str) -> Dict[str, Any]:
        """
        Get a team by key.
        
        Args:
            team_key: Yahoo team key
            
        Returns:
            Team data
        """
        return await self._make_request(f"team/{team_key}")
    
    async def get_team_roster(self, team_key: str) -> Dict[str, Any]:
        """
        Get roster for a team.
        
        Args:
            team_key: Yahoo team key
            
        Returns:
            Roster data
        """
        return await self._make_request(f"team/{team_key}/roster")
    
    async def get_players(
        self, 
        league_key: str, 
        position: Optional[str] = None,
        status: Optional[str] = None,
        count: int = 25,
        start: int = 0
    ) -> Dict[str, Any]:
        """
        Get players in a league.
        
        Args:
            league_key: Yahoo league key
            position: Filter by position (optional)
            status: Filter by status (optional)
            count: Number of players to return
            start: Start position for pagination
            
        Returns:
            Player data
        """
        filters = []
        
        if position:
            filters.append(f"position={position}")
        
        if status:
            filters.append(f"status={status}")
        
        filters_str = ";".join(filters)
        if filters_str:
            filters_str = f";{filters_str}"
        
        return await self._make_request(f"league/{league_key}/players{filters_str};count={count};start={start}")
    
    async def get_player(self, player_key: str) -> Dict[str, Any]:
        """
        Get a player by key.
        
        Args:
            player_key: Yahoo player key
            
        Returns:
            Player data
        """
        return await self._make_request(f"player/{player_key}")
    
    async def get_player_stats(self, player_key: str, week: Optional[int] = None) -> Dict[str, Any]:
        """
        Get stats for a player.
        
        Args:
            player_key: Yahoo player key
            week: Week number (optional, if not provided, season stats are returned)
            
        Returns:
            Player stats
        """
        if week:
            return await self._make_request(f"player/{player_key}/stats;type=week;week={week}")
        else:
            return await self._make_request(f"player/{player_key}/stats") 