import time

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from application.api import api_router
from application.core.logging import get_logger
from application.core.dependencies import close_database_connections

# Initialize logging
logger = get_logger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    logger.info("Shutting down application...")
    close_database_connections()
    logger.info("Application shutdown complete.")

# Create FastAPI application
application = FastAPI(
    title="Moovzmatch API",
    description="A sophisticated media identification system using speech-to-text, vector embeddings, and multiple external APIs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@application.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Add exception handler
@application.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include API routes
application.include_router(api_router)

# Health check endpoint
@application.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "moovzmatch"}

# Root endpoint
@application.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Moovzmatch API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "application.app:application",
#         host="0.0.0.0",
#         port=8000,
#         reload=settings.DEBUG_MODE
#     )