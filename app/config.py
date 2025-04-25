"""
Configuration settings for the Fantasy Football Manager.
"""
import os
from pathlib import Path
from typing import List

# Base directories
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / "app"

# API Settings
API_VERSION = "0.1.0"
API_PREFIX = "/api"

# Frontend URLs
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:3000",
]

# Add wildcard in development mode
if os.environ.get("ENVIRONMENT", "development") == "development":
    ALLOWED_ORIGINS.append("*")

# Database
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./fantasy_football.db"
)

# Authentication
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretkey")  # Change in production!
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# External API settings
YAHOO_CLIENT_ID = os.environ.get("YAHOO_CLIENT_ID", "")
YAHOO_CLIENT_SECRET = os.environ.get("YAHOO_CLIENT_SECRET", "")

ESPN_API_KEY = os.environ.get("ESPN_API_KEY", "")

SLEEPER_API_BASE_URL = "https://api.sleeper.app/v1"

# Player data
DEFAULT_SEASON = 2023 