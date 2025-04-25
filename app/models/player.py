"""
Player model for Fantasy Football Manager.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship

from app.db.base import Base

class Player(Base):
    """Player model representing a football player."""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    position = Column(String, index=True)  # QB, RB, WR, TE, K, DEF
    team = Column(String, index=True)  # NFL team abbreviation
    jersey_number = Column(Integer, nullable=True)
    status = Column(String, default="Active")  # Active, Injured, Suspended
    height = Column(String, nullable=True)  # in feet and inches (e.g., "6'2")
    weight = Column(Integer, nullable=True)  # in pounds
    age = Column(Integer, nullable=True)
    college = Column(String, nullable=True)
    birthdate = Column(Date, nullable=True)
    years_pro = Column(Integer, default=0)
    
    # External IDs
    yahoo_id = Column(String, nullable=True, unique=True)
    espn_id = Column(String, nullable=True, unique=True)
    sleeper_id = Column(String, nullable=True, unique=True)
    
    # Stats relationships
    stats = relationship("PlayerStats", back_populates="player", cascade="all, delete-orphan")
    projections = relationship("PlayerProjection", back_populates="player", cascade="all, delete-orphan")
    
    # Team relationships
    league_teams = relationship("TeamPlayer", back_populates="player")
    
    def __repr__(self):
        return f"<Player {self.first_name} {self.last_name} ({self.position})>"

class PlayerStats(Base):
    """Player statistics model."""
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    season = Column(Integer, index=True)  # e.g., 2023
    week = Column(Integer, nullable=True, index=True)  # null for season stats
    
    # Common stats
    games_played = Column(Integer, default=0)
    games_started = Column(Integer, default=0)
    
    # Passing stats
    pass_attempts = Column(Integer, default=0)
    pass_completions = Column(Integer, default=0)
    pass_yards = Column(Integer, default=0)
    pass_touchdowns = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    sacks = Column(Integer, default=0)
    
    # Rushing stats
    rush_attempts = Column(Integer, default=0)
    rush_yards = Column(Integer, default=0)
    rush_touchdowns = Column(Integer, default=0)
    
    # Receiving stats
    targets = Column(Integer, default=0)
    receptions = Column(Integer, default=0)
    receiving_yards = Column(Integer, default=0)
    receiving_touchdowns = Column(Integer, default=0)
    
    # Kicking stats
    field_goals_made = Column(Integer, default=0)
    field_goals_attempted = Column(Integer, default=0)
    extra_points_made = Column(Integer, default=0)
    extra_points_attempted = Column(Integer, default=0)
    
    # Defense stats
    tackles = Column(Integer, default=0)
    sacks_defense = Column(Float, default=0.0)
    interceptions_defense = Column(Integer, default=0)
    fumble_recoveries = Column(Integer, default=0)
    safeties = Column(Integer, default=0)
    defensive_touchdowns = Column(Integer, default=0)
    
    # Fantasy points
    fantasy_points = Column(Float, default=0.0)
    
    # Relationship
    player = relationship("Player", back_populates="stats")
    
    def __repr__(self):
        week_info = f"Week {self.week}" if self.week else "Season"
        return f"<PlayerStats {self.player_id} - {self.season} {week_info}>"

class PlayerProjection(Base):
    """Player projection model for fantasy points."""
    __tablename__ = "player_projections"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    source = Column(String, index=True)  # Yahoo, ESPN, Sleeper, Custom
    season = Column(Integer, index=True)
    week = Column(Integer, nullable=True, index=True)  # null for season projections
    
    # Projected stats similar to PlayerStats
    proj_pass_yards = Column(Integer, default=0)
    proj_pass_touchdowns = Column(Integer, default=0)
    proj_interceptions = Column(Integer, default=0)
    proj_rush_yards = Column(Integer, default=0)
    proj_rush_touchdowns = Column(Integer, default=0)
    proj_receptions = Column(Integer, default=0)
    proj_receiving_yards = Column(Integer, default=0)
    proj_receiving_touchdowns = Column(Integer, default=0)
    
    # Projected fantasy points
    proj_fantasy_points = Column(Float, default=0.0)
    
    # Relationship
    player = relationship("Player", back_populates="projections")
    
    def __repr__(self):
        week_info = f"Week {self.week}" if self.week else "Season"
        return f"<PlayerProjection {self.player_id} - {self.source} {self.season} {week_info}>" 