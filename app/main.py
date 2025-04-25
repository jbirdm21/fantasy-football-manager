"""
Main entry point for the Fantasy Football Manager application.
"""
import uvicorn
from app import app
from app.db.base import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 