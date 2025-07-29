from fastapi import APIRouter
from .endpoints import search

# Create the v1 API router
api_v1_router = APIRouter(prefix="/v1")

# Include endpoint routers
api_v1_router.include_router(search.router, prefix="/api", tags=["search"])

__all__ = ["api_v1_router"] 