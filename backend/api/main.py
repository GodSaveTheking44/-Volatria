import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.core.config import settings
from backend.database.db import engine, Base

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Institutional-grade Quantitative Research and Trading Workspace"
)

# Register CORSMiddleware for frontend cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 routers (to be created next)
from backend.api.v1 import (
    market_data,
    strategies,
    backtests,
    portfolio,
    risk,
    models,
    research,
    trading
)

app.include_router(market_data.router, prefix=settings.API_V1_STR)
app.include_router(strategies.router, prefix=settings.API_V1_STR)
app.include_router(backtests.router, prefix=settings.API_V1_STR)
app.include_router(portfolio.router, prefix=settings.API_V1_STR)
app.include_router(risk.router, prefix=settings.API_V1_STR)
app.include_router(models.router, prefix=settings.API_V1_STR)
app.include_router(research.router, prefix=settings.API_V1_STR)
app.include_router(trading.router, prefix=settings.API_V1_STR)

# Global API usage counter for Prometheus endpoint
api_calls_counter = 0

@app.middleware("http")
async def count_requests(request, call_next):
    global api_calls_counter
    api_calls_counter += 1
    response = await call_next(request)
    return response

@app.get("/metrics")
def get_metrics():
    """
    Exposes system metrics in standard Prometheus formatting.
    """
    return (
        f"# HELP volatria_api_calls_total Total count of API requests\n"
        f"# TYPE volatria_api_calls_total counter\n"
        f"volatria_api_calls_total {api_calls_counter}\n"
    )

# Serve SPA Frontend static files
frontend_dir = os.path.abspath("frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
