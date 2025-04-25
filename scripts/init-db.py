#!/usr/bin/env python3
"""
Script to initialize the database with sample data.
"""
import os
import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
import random

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")

# Import app modules
from app.db.base import engine, Base, SessionLocal
from app.models.league import League, Team, TeamPlayer, User, Draft, DraftPick
from app.models.player import Player, PlayerStats

# Sample data
SAMPLE_USERS = [
    {"username": "admin", "email": "admin@example.com", "hashed_password": "hashed_admin_password"},
    {"username": "user1", "email": "user1@example.com", "hashed_password": "hashed_user1_password"},
    {"username": "user2", "email": "user2@example.com", "hashed_password": "hashed_user2_password"},
]

SAMPLE_LEAGUES = [
    {
        "name": "Fantasy Football 2023",
        "description": "Our 2023 fantasy football league",
        "season": 2023,
        "league_type": "half_ppr",
        "max_teams": 10,
        "roster_size": 16,
        "public": True,
    },
    {
        "name": "Friends League 2023",
        "description": "Private league for friends",
        "season": 2023,
        "league_type": "ppr",
        "max_teams": 8,
        "roster_size": 18,
        "public": False,
    },
]

SAMPLE_PLAYERS = [
    {"first_name": "Patrick", "last_name": "Mahomes", "position": "QB", "team": "KC"},
    {"first_name": "Josh", "last_name": "Allen", "position": "QB", "team": "BUF"},
    {"first_name": "Justin", "last_name": "Jefferson", "position": "WR", "team": "MIN"},
    {"first_name": "Cooper", "last_name": "Kupp", "position": "WR", "team": "LAR"},
    {"first_name": "Christian", "last_name": "McCaffrey", "position": "RB", "team": "SF"},
    {"first_name": "Saquon", "last_name": "Barkley", "position": "RB", "team": "NYG"},
    {"first_name": "Travis", "last_name": "Kelce", "position": "TE", "team": "KC"},
    {"first_name": "Mark", "last_name": "Andrews", "position": "TE", "team": "BAL"},
]

def create_sample_data():
    """
    Create sample data in the database.
    """
    logger.info("Creating sample data...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if users already exist
        if db.query(User).count() > 0:
            logger.info("Database already contains data. Skipping sample data creation.")
            return
        
        # Create users
        users = []
        for user_data in SAMPLE_USERS:
            user = User(**user_data)
            db.add(user)
            db.flush()
            users.append(user)
        
        # Create leagues
        leagues = []
        for league_data in SAMPLE_LEAGUES:
            league = League(**league_data, commissioner_id=users[0].id)
            db.add(league)
            db.flush()
            leagues.append(league)
        
        # Create teams
        teams = []
        for i, user in enumerate(users):
            for league in leagues:
                team = Team(
                    name=f"{user.username}'s Team",
                    owner_id=user.id,
                    league_id=league.id,
                    draft_position=i+1
                )
                db.add(team)
                db.flush()
                teams.append(team)
        
        # Create players
        players = []
        for player_data in SAMPLE_PLAYERS:
            player = Player(**player_data)
            db.add(player)
            db.flush()
            players.append(player)
            
            # Add stats for each player
            for season in [2021, 2022, 2023]:
                # Season stats
                stats = PlayerStats(
                    player_id=player.id,
                    season=season,
                    games_played=17,
                    fantasy_points=random.uniform(50, 350)
                )
                db.add(stats)
                
                # Weekly stats for current season
                if season == 2023:
                    for week in range(1, 18):
                        weekly_stats = PlayerStats(
                            player_id=player.id,
                            season=season,
                            week=week,
                            games_played=1,
                            fantasy_points=random.uniform(0, 30)
                        )
                        db.add(weekly_stats)
        
        # Create draft
        draft = Draft(
            league_id=leagues[0].id,
            date=datetime.utcnow() - timedelta(days=30),
            status="completed"
        )
        db.add(draft)
        db.flush()
        
        # Create draft picks
        for round_num in range(1, 3):  # 2 rounds for sample
            for pick_num, team in enumerate(teams[:len(leagues[0].teams)], 1):
                player_index = (round_num - 1) * len(teams[:len(leagues[0].teams)]) + pick_num - 1
                if player_index < len(players):
                    pick = DraftPick(
                        draft_id=draft.id,
                        team_id=team.id,
                        player_id=players[player_index].id,
                        round=round_num,
                        pick_number=pick_num
                    )
                    db.add(pick)
                    
                    # Add player to team
                    team_player = TeamPlayer(
                        team_id=team.id,
                        player_id=players[player_index].id,
                        position=players[player_index].position
                    )
                    db.add(team_player)
        
        db.commit()
        logger.info("Sample data created successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sample data: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data() 