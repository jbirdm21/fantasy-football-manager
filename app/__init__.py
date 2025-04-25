"""
Fantasy Football Manager application initialization.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS, API_VERSION

# Initialize FastAPI app
app = FastAPI(
    title="Fantasy Football Manager",
    description="API for managing fantasy football leagues, teams, and players",
    version=API_VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import API routes
from app.api.routes import player, league, team, auth, draft

# Include API routes
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(player.router, prefix="/api", tags=["Players"])
app.include_router(league.router, prefix="/api", tags=["Leagues"])
app.include_router(team.router, prefix="/api", tags=["Teams"])
app.include_router(draft.router, prefix="/api", tags=["Drafts"])

@app.get("/")
async def root():
    """Root endpoint for the API."""
    return {
        "message": "Welcome to the Fantasy Football Manager API",
        "docs": "/docs",
        "version": API_VERSION
    } 