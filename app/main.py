from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

from app.config import settings
from app.routers import stocks, analysis
from app.utils.cache import cache_manager

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Stock Analysis API...")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Redis URL: {settings.redis_url}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Stock Analysis API...")
    await cache_manager.close()


# Create FastAPI application
app = FastAPI(
    title="AI Stock Analysis API",
    description="A microservice for AI-powered stock and cryptocurrency analysis using yfinance and GPT-4o-mini",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router)
app.include_router(analysis.router)

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")
    logger.info(f"Frontend mounted at /frontend from: {frontend_path}")

@app.get("/frontend/")
async def serve_frontend():
    """Serve the frontend index.html at /frontend/"""
    frontend_index = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    else:
        raise HTTPException(status_code=404, detail=f"Frontend not found at: {frontend_index}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Stock Analysis API",
        "version": "1.0.0",
        "description": "AI-powered stock and cryptocurrency analysis using yfinance and GPT-4o-mini",
        "endpoints": {
            "stocks": "/api/v1/stocks",
            "analysis": "/api/v1/analysis",
            "frontend": "/frontend/",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "supported_markets": ["US", "ZA", "CRYPTO"],
        "features": [
            "Real-time stock data via yfinance",
            "Technical indicators (RSI, SMA, MACD)",
            "AI-powered analysis with GPT-4o-mini",
            "BUY/HOLD/SELL recommendations",
            "Portfolio analysis",
            "Stock comparison",
            "Redis caching for performance"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test cache connection
        cache_healthy = await cache_manager.exists("health_test")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": "operational",
                "cache": "operational" if cache_healthy is not None else "warning",
                "openai": "configured" if settings.openai_api_key else "not_configured"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Set to False in production
        log_level=settings.log_level.lower()
    )