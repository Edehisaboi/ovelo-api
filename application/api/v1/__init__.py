from fastapi import APIRouter
from .endpoints.http import search
from .endpoints.ws import identification

# Create the v1 API router
api_v1_router = APIRouter(prefix="/v1")

# Include endpoint routers
api_v1_router.include_router(search.router, prefix="/api", tags=["search"])
api_v1_router.include_router(identification.router, tags=["websocket", "identification"])

__all__ = ["api_v1_router"] 