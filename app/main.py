from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.routes import insights, mock_llm, async_insights, monitoring
from app.utils.rate_limiter import limiter
from app.config import get_settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

settings = get_settings()

app = FastAPI(
    title="Pythia AI Insights Service",
    description="AI-powered data insights and anomaly detection",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(insights.router)
app.include_router(mock_llm.router)
app.include_router(async_insights.router)
app.include_router(monitoring.router)

@app.get("/health")
@limiter.limit("100/minute")  # Rate limit health checks too
async def health_check(request: Request):
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "service": "Pythia AI Insights",
        "docs": "/docs",
        "health": "/health",
        "async_endpoints": "/api/v1/async"
    }

