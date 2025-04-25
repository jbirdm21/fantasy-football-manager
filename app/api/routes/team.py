"""
Team API routes for the Fantasy Football Manager.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db.base import get_db
from app.models.league import Team, TeamPlayer, User

router = APIRouter()

# Pydantic models for request/response
class TeamBase(BaseModel):
    name: str
    logo_url: Optional[str] = None
    league_id: int
    owner_id: int
    draft_position: Optional[int] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    draft_position: Optional[int] = None

class TeamResponse(TeamBase):
    id: int
    
    class Config:
        orm_mode = True

class TeamPlayerBase(BaseModel):
    player_id: int
    position: str

class TeamPlayerCreate(TeamPlayerBase):
    pass

class TeamPlayerResponse(TeamPlayerBase):
    id: int
    team_id: int
    date_added: str
    
    class Config:
        orm_mode = True

@router.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    league_id: Optional[int] = None,
    owner_id: Optional[int] = None
):
    """
    Get a list of teams.
    
    Args:
        db: Database session
        skip: Number of teams to skip
        limit: Maximum number of teams to return
        league_id: Filter by league ID
        owner_id: Filter by owner ID
        
    Returns:
        List of teams
    """
    query = db.query(Team)
    
    if league_id:
        query = query.filter(Team.league_id == league_id)
    
    if owner_id:
        query = query.filter(Team.owner_id == owner_id)
    
    teams = query.offset(skip).limit(limit).all()
    return teams

@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new team.
    
    Args:
        team: Team data
        db: Database session
        
    Returns:
        Created team
    """
    # Check if league exists
    league = db.query(Team).filter(Team.id == team.league_id).first()
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == team.owner_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create team
    db_team = Team(
        name=team.name,
        logo_url=team.logo_url,
        league_id=team.league_id,
        owner_id=team.owner_id,
        draft_position=team.draft_position
    )
    
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    return db_team

@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a team by ID.
    
    Args:
        team_id: Team ID
        db: Database session
        
    Returns:
        Team details
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return team

@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a team.
    
    Args:
        team_id: Team ID
        team_update: Team update data
        db: Database session
        
    Returns:
        Updated team
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Update fields if provided
    if team_update.name is not None:
        team.name = team_update.name
    
    if team_update.logo_url is not None:
        team.logo_url = team_update.logo_url
        
    if team_update.draft_position is not None:
        team.draft_position = team_update.draft_position
    
    db.commit()
    db.refresh(team)
    
    return team

@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a team.
    
    Args:
        team_id: Team ID
        db: Database session
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Delete the team
    db.delete(team)
    db.commit()
    
    return None

@router.get("/teams/{team_id}/players", response_model=List[TeamPlayerResponse])
async def get_team_players(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get players for a team.
    
    Args:
        team_id: Team ID
        db: Database session
        
    Returns:
        List of players on the team
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    team_players = db.query(TeamPlayer).filter(TeamPlayer.team_id == team_id).all()
    
    return team_players

@router.post("/teams/{team_id}/players", response_model=TeamPlayerResponse, status_code=status.HTTP_201_CREATED)
async def add_player_to_team(
    team_id: int,
    player: TeamPlayerCreate,
    db: Session = Depends(get_db)
):
    """
    Add a player to a team.
    
    Args:
        team_id: Team ID
        player: Player data
        db: Database session
        
    Returns:
        Created team player association
    """
    # Check if team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Create team player association
    team_player = TeamPlayer(
        team_id=team_id,
        player_id=player.player_id,
        position=player.position
    )
    
    db.add(team_player)
    db.commit()
    db.refresh(team_player)
    
    return team_player

@router.delete("/teams/{team_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_player_from_team(
    team_id: int,
    player_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a player from a team.
    
    Args:
        team_id: Team ID
        player_id: Player ID
        db: Database session
    """
    team_player = db.query(TeamPlayer).filter(
        TeamPlayer.team_id == team_id,
        TeamPlayer.player_id == player_id
    ).first()
    
    if not team_player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found on team"
        )
    
    # Delete the team player association
    db.delete(team_player)
    db.commit()
    
    return None 