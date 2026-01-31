"""
Bitcoin Strategic Cycle Model - Web Dashboard
FastAPI Application
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for model imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Optional
import json
import logging

from model import StrategicCycleModel, MarketData, get_default_market_data
from app.data_service import data_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bitcoin Strategic Cycle Model",
    description="Live dashboard for the Bitcoin Strategic Cycle Model v7.0",
    version="7.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
static_path = Path(__file__).parent.parent / "static"
templates_path = Path(__file__).parent.parent / "templates"

static_path.mkdir(exist_ok=True)
templates_path.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Initialize model
model = StrategicCycleModel()

# Store for manual data overrides
manual_overrides: Dict = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/analyze")
async def analyze():
    """Run model analysis with live data"""
    try:
        # Fetch live data
        live_data = await data_service.fetch_all_data()

        # Build market data with live values and manual overrides
        market_data = data_service.build_market_data(live_data, manual_overrides)

        # Run analysis
        result = model.analyze(market_data)

        # Add live data status
        result['data_source'] = {
            'live_data_status': live_data.get('status', 'unknown'),
            'timestamp': live_data.get('timestamp', datetime.now().isoformat()),
            'has_manual_overrides': bool(manual_overrides)
        }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyze/default")
async def analyze_default():
    """Run model analysis with default/demo data"""
    try:
        market_data = get_default_market_data()
        result = model.analyze(market_data)
        result['data_source'] = {
            'live_data_status': 'demo',
            'timestamp': datetime.now().isoformat(),
            'has_manual_overrides': False
        }
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live-data")
async def get_live_data():
    """Get live market data without running full analysis"""
    try:
        live_data = await data_service.fetch_all_data()
        return JSONResponse(content=live_data)

    except Exception as e:
        logger.error(f"Live data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/overrides")
async def set_overrides(request: Request):
    """Set manual data overrides for values not available from free APIs"""
    global manual_overrides
    try:
        data = await request.json()
        manual_overrides.update(data)
        return JSONResponse(content={
            "status": "success",
            "overrides": manual_overrides
        })

    except Exception as e:
        logger.error(f"Override error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/overrides")
async def get_overrides():
    """Get current manual data overrides"""
    return JSONResponse(content=manual_overrides)


@app.delete("/api/overrides")
async def clear_overrides():
    """Clear all manual data overrides"""
    global manual_overrides
    manual_overrides = {}
    return JSONResponse(content={"status": "cleared"})


@app.get("/api/thesis")
async def get_thesis():
    """Get just the thesis text"""
    try:
        live_data = await data_service.fetch_all_data()
        market_data = data_service.build_market_data(live_data, manual_overrides)
        result = model.analyze(market_data)

        return JSONResponse(content={
            "thesis": result.get("thesis", ""),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Thesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signal")
async def get_signal():
    """Get just the current signal"""
    try:
        live_data = await data_service.fetch_all_data()
        market_data = data_service.build_market_data(live_data, manual_overrides)
        result = model.analyze(market_data)

        return JSONResponse(content={
            "signal": result.get("signal", {}),
            "phase": result.get("phase", {}),
            "price": result.get("meta", {}).get("btc_price", 0),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Signal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "model_version": "7.0.0",
        "timestamp": datetime.now().isoformat()
    })


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
