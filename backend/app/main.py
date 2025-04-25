"""Main FastAPI application entrypoint."""
from backend.app.api.routes import espn_router, yahoo_router, sleeper_router, projections_router
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ultimate Personal Fantasy Football Manager",
    description="API for managing fantasy football leagues and teams",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app initialization to avoid circular imports

# Include routers
app.include_router(espn_router, prefix="/api/espn", tags=["ESPN"])
app.include_router(yahoo_router, prefix="/api/yahoo", tags=["Yahoo"])
app.include_router(sleeper_router, prefix="/api/sleeper", tags=["Sleeper"])
app.include_router(projections_router, prefix="/api/projections", tags=["Projections"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "UPFFM API is running"}


@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting up UPFFM backend...")
    # Add initialization code here
    # e.g., database connections, cache initialization, etc.


@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    logger.info("Shutting down UPFFM backend...")
    # Add cleanup code here
