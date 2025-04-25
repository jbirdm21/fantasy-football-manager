"""
League and Team models for Fantasy Football Manager.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Table, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class League(Base):
    """League model representing a fantasy football league."""
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    commissioner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    season = Column(Integer, index=True)  # e.g., 2023
    league_type = Column(String, default="standard")  # standard, ppr, half_ppr
    max_teams = Column(Integer, default=12)
    roster_size = Column(Integer, default=16)
    public = Column(Boolean, default=False)
    
    # Scoring settings
    pass_yards_point = Column(Float, default=0.04)  # 1 point per 25 yards
    pass_td_point = Column(Float, default=4.0)
    interception_point = Column(Float, default=-2.0)
    rush_yards_point = Column(Float, default=0.1)  # 1 point per 10 yards
    rush_td_point = Column(Float, default=6.0)
    reception_point = Column(Float, default=0.0)  # PPR = 1.0, Half PPR = 0.5
    receiving_yards_point = Column(Float, default=0.1)  # 1 point per 10 yards
    receiving_td_point = Column(Float, default=6.0)
    
    # Draft settings
    draft_date = Column(DateTime, nullable=True)
    draft_type = Column(String, default="snake")  # snake, auction
    
    # External IDs
    yahoo_league_id = Column(String, nullable=True)
    espn_league_id = Column(String, nullable=True)
    sleeper_league_id = Column(String, nullable=True)
    
    # Relationships
    teams = relationship("Team", back_populates="league", cascade="all, delete-orphan")
    commissioner = relationship("User", foreign_keys=[commissioner_id])
    
    def __repr__(self):
        return f"<League {self.name} ({self.season})>"

class Team(Base):
    """Team model representing a fantasy football team in a league."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    logo_url = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"), index=True)
    draft_position = Column(Integer, nullable=True)
    
    # Relationships
    league = relationship("League", back_populates="teams")
    owner = relationship("User")
    players = relationship("TeamPlayer", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Team {self.name} (League {self.league_id})>"

class TeamPlayer(Base):
    """Association table for players on a team."""
    __tablename__ = "team_players"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    position = Column(String)  # QB, RB, WR, TE, K, DEF, BENCH, IR
    date_added = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    player = relationship("Player", back_populates="league_teams")
    
    def __repr__(self):
        return f"<TeamPlayer {self.team_id} - {self.player_id} ({self.position})>"

class User(Base):
    """User model representing a fantasy football manager."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    owned_teams = relationship("Team", back_populates="owner", foreign_keys=[Team.owner_id])
    
    def __repr__(self):
        return f"<User {self.username}>"

class Draft(Base):
    """Draft model representing a fantasy football draft."""
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), index=True)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="scheduled")  # scheduled, in_progress, completed
    
    # Relationships
    league = relationship("League")
    picks = relationship("DraftPick", back_populates="draft", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Draft {self.id} (League {self.league_id})>"

class DraftPick(Base):
    """Draft pick model representing a pick in a fantasy football draft."""
    __tablename__ = "draft_picks"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    round = Column(Integer)
    pick_number = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    draft = relationship("Draft", back_populates="picks")
    team = relationship("Team")
    player = relationship("Player")
    
    def __repr__(self):
        return f"<DraftPick Round {self.round}.{self.pick_number} - {self.player_id}>" 