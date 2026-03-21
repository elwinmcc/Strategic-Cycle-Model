"""
BTC Econometric Model v7.6 — Web Dashboard
FastAPI Application
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict
import logging

from model.btc_model_v76 import ModelInputs, run_analysis
from app.data_service import data_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BTC Econometric Model",
    description="Live dashboard for the BTC Econometric Model v7.6",
    version="7.6.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent.parent / "static"
templates_path = Path(__file__).parent.parent / "templates"
static_path.mkdir(exist_ok=True)
templates_path.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Store for manual data overrides
manual_overrides: Dict = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/analyze")
async def analyze():
    """Run v7.6 model analysis with live CoinGlass + FRED data."""
    try:
        inputs = await data_service.collect_all_data()

        # Apply manual overrides
        for key, value in manual_overrides.items():
            if hasattr(inputs, key):
                setattr(inputs, key, value)

        result = run_analysis(inputs)

        result["data_source"] = {
            "live_data_status": "live",
            "timestamp": inputs.timestamp,
            "has_manual_overrides": bool(manual_overrides),
            "sources_count": len(inputs.sources),
        }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyze/default")
async def analyze_default():
    """Run model analysis with default/demo data."""
    try:
        inputs = ModelInputs(
            btc_price=84000,
            btc_ath=126080,
            drawdown_pct=-33.4,
            mvrv=1.8,
            realized_price=46667,
            sth_realized_price=52000,
            lth_realized_price=38000,
            nupl=0.52,
            fear_greed=25,
            fear_greed_label="Extreme Fear",
            coinbase_premium=0.1,
            funding_rate=0.005,
            oi_total=28000000000,
            long_short_ratio=1.1,
            liquidation_24h=150000000,
            futures_basis=8.0,
            put_call_ratio=0.65,
            max_pain=85000,
            etf_flow_daily=50000000,
            etf_flow_weekly=200000000,
            hy_oas=3.5,
            yield_curve_2s10s=0.25,
            initial_claims=220000,
            anfci=-0.15,
            fed_bs=6800,
            rrp=200,
            tga=750,
            rsi_daily=42,
            price_30d_ago=90000,
            global_m2_growth=3.0,
            eth_price=2100,
            eth_btc=0.025,
            btc_dominance=61.5,
            timestamp=datetime.now().isoformat(),
        )
        inputs.sources = {"demo": "Default values"}

        result = run_analysis(inputs)
        result["data_source"] = {
            "live_data_status": "demo",
            "timestamp": datetime.now().isoformat(),
            "has_manual_overrides": False,
            "sources_count": 0,
        }
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Default analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live-data")
async def get_live_data():
    """Get live market data without running analysis."""
    try:
        inputs = await data_service.collect_all_data()
        return JSONResponse(content=inputs.to_dict())
    except Exception as e:
        logger.error(f"Live data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/overrides")
async def set_overrides(request: Request):
    """Set manual data overrides."""
    global manual_overrides
    try:
        data = await request.json()
        manual_overrides.update(data)
        return JSONResponse(content={"status": "success", "overrides": manual_overrides})
    except Exception as e:
        logger.error(f"Override error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/overrides")
async def get_overrides():
    """Get current manual data overrides."""
    return JSONResponse(content=manual_overrides)


@app.delete("/api/overrides")
async def clear_overrides():
    """Clear all manual data overrides."""
    global manual_overrides
    manual_overrides = {}
    return JSONResponse(content={"status": "cleared"})


@app.get("/api/signal")
async def get_signal():
    """Get just the current signal."""
    try:
        inputs = await data_service.collect_all_data()
        for key, value in manual_overrides.items():
            if hasattr(inputs, key):
                setattr(inputs, key, value)
        result = run_analysis(inputs)
        return JSONResponse(content={
            "signal": result.get("signal", {}),
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Signal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={
        "status": "healthy",
        "model_version": "7.6.0",
        "timestamp": datetime.now().isoformat(),
    })


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=404, content={"detail": "Not found"})


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
