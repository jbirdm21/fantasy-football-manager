"""League models for the database."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from backend.app.db.base import Base


class League(Base):
    """League model for database."""

    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    platform = Column(String, index=True)  # "ESPN", "Yahoo", "Sleeper"
    season = Column(Integer, index=True)
    platform_league_id = Column(String, index=True)

    # League settings
    scoring_format = Column(String, index=True)  # "standard", "ppr", "half_ppr"
    roster_settings = Column(JSON, nullable=True)  # JSON with roster position limits
    draft_settings = Column(JSON, nullable=True)  # JSON with draft type, order, etc.

    # Ownership (user who added this league)
    user_id = Column(String, index=True)

    # Auth data (encrypted in the database implementation)
    auth_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    teams = relationship("Team", back_populates="league")

    def __repr__(self):
        """String representation of the league."""
        return (
            f"<League(id={self.id}, name='{self.name}', "
            f"platform='{self.platform}', season={self.season})>"
        )


class Team(Base):
    """Team model for database."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), index=True)
    name = Column(String, index=True)
    owner_name = Column(String, index=True)
    platform_team_id = Column(String, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    league = relationship("League", back_populates="teams")

    def __repr__(self):
        """String representation of the team."""
        return (
            f"<Team(id={self.id}, league_id={self.league_id}, "
            f"name='{self.name}', owner_name='{self.owner_name}')>"
        )
