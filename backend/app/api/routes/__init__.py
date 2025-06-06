"""Route definitions for the UPFFM API."""
from backend.app.api.routes.espn import router as espn_router
from backend.app.api.routes.yahoo import router as yahoo_router
from backend.app.api.routes.sleeper import router as sleeper_router
from backend.app.api.routes.projections import router as projections_router

__all__ = ["espn_router", "yahoo_router", "sleeper_router", "projections_router"]
