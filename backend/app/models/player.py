"""Player models for the database."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


class Player(Base):
    """Player model for database."""

    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    position = Column(String, index=True)
    team = Column(String, index=True)

    # External IDs for different platforms
    espn_id = Column(String, unique=True, nullable=True, index=True)
    yahoo_id = Column(String, unique=True, nullable=True, index=True)
    sleeper_id = Column(String, unique=True, nullable=True, index=True)

    # Relationships
    projections = relationship("PlayerProjection", back_populates="player")

    def __repr__(self):
        """String representation of the player."""
        return f"<Player(id={self.id}, name='{self.name}', position='{self.position}', team='{self.team}')>"


class PlayerProjection(Base):
    """Player projection model for database."""

    __tablename__ = "player_projections"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    source = Column(String, index=True)  # e.g., "ESPN", "Yahoo", "FantasyPros", "Custom"
    season = Column(Integer, index=True)
    week = Column(Integer, nullable=True, index=True)  # Null for season projections
    scoring_format = Column(String, index=True)  # "standard", "ppr", "half_ppr"

    # Projected stats
    projected_points = Column(Float)
    floor = Column(Float, nullable=True)
    ceiling = Column(Float, nullable=True)

    # Position-specific stats stored as JSON in the database implementation

    # Relationships
    player = relationship("Player", back_populates="projections")

    def __repr__(self):
        """String representation of the player projection."""
        return (
            f"<PlayerProjection(id={self.id}, player_id={self.player_id}, "
            f"source='{self.source}', season={self.season}, week={self.week}, "
            f"projected_points={self.projected_points})>"
        )
