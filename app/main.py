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

from model.btc_model_v76 import ModelInputs
from model.btc_model_v77 import run_analysis
from app.data_service import data_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BTC Econometric Model",
    description="Live dashboard for the BTC Econometric Model v7.7",
    version="7.7.0"
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

        # If no meaningful data was fetched (no API keys or all calls failed),
        # fall back to demo data so the dashboard isn't blank
        if inputs.btc_price == 0 and not inputs.sources:
            logger.warning("No live data fetched — falling back to demo data. Set COINGLASS_API_KEY and FRED_API_KEY env vars.")
            inputs = _create_demo_inputs()
            inputs.warnings.append("Using demo data — set COINGLASS_API_KEY and FRED_API_KEY environment variables for live data")
            for key, value in manual_overrides.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)

        result = run_analysis(inputs)

        live_status = "live" if "demo" not in str(inputs.sources) else "demo"
        result["data_source"] = {
            "live_data_status": live_status,
            "timestamp": inputs.timestamp,
            "has_manual_overrides": bool(manual_overrides),
            "sources_count": len(inputs.sources),
        }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _create_demo_inputs() -> ModelInputs:
    """Create demo ModelInputs with realistic sample data."""
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
        options_oi=12000000000,
        etf_flow_daily=50000000,
        etf_flow_weekly=200000000,
        etf_cumulative=35000000000,
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
    return inputs


@app.get("/api/analyze/default")
async def analyze_default():
    """Run model analysis with default/demo data."""
    try:
        inputs = _create_demo_inputs()

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
    import os
    cg_key = os.environ.get("COINGLASS_API_KEY", "")
    fred_key = os.environ.get("FRED_API_KEY", "")
    return JSONResponse(content={
        "status": "healthy",
        "model_version": "7.7.0",
        "timestamp": datetime.now().isoformat(),
        "api_keys": {
            "coinglass": f"{'SET (' + cg_key[:4] + '...)' if cg_key else 'NOT SET'}",
            "fred": f"{'SET (' + fred_key[:4] + '...)' if fred_key else 'NOT SET'}",
        }
    })


@app.get("/api/debug")
async def debug_data():
    """Debug endpoint showing raw data fetch results and field population status."""
    try:
        # Clear cache to force fresh fetch
        from app.data_service import cache
        cache.clear()

        inputs = await data_service.collect_all_data()
        fields = {}
        for field_name in [
            "btc_price", "mvrv", "realized_price", "sth_realized_price", "lth_realized_price",
            "nupl", "fear_greed", "funding_rate", "long_short_ratio", "liquidation_24h",
            "futures_basis", "put_call_ratio", "max_pain", "options_oi",
            "etf_flow_daily", "etf_flow_weekly", "etf_cumulative",
            "coinbase_premium", "btc_dominance", "eth_price", "eth_btc",
            "oi_total", "oi_change_24h_pct",
            "hy_oas", "yield_curve_2s10s", "initial_claims", "anfci",
            "fed_bs", "rrp", "tga", "wti_price", "global_m2_growth", "price_30d_ago",
        ]:
            val = getattr(inputs, field_name, None)
            fields[field_name] = {"value": val, "populated": val is not None and val != 0}

        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "sources": inputs.sources,
            "warnings": inputs.warnings,
            "fields": fields,
            "populated_count": sum(1 for f in fields.values() if f["populated"]),
            "total_fields": len(fields),
        })
    except Exception as e:
        logger.error(f"Debug error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/debug/raw")
async def debug_raw_api():
    """Test a single CoinGlass API call and return the raw response for debugging."""
    import httpx
    from app.data_service import COINGLASS_API_KEY, COINGLASS_BASE

    results = {}
    results["api_key_set"] = bool(COINGLASS_API_KEY)
    results["api_key_prefix"] = COINGLASS_API_KEY[:8] + "..." if len(COINGLASS_API_KEY) > 8 else "(too short or empty)"

    if not COINGLASS_API_KEY:
        return JSONResponse(content=results)

    headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
    endpoints = {
        "futures_coins_markets": ("futures/coins-markets", {"per_page": 2, "page": 1}),
        "spot_coins_markets": ("spot/coins-markets", {"per_page": 2, "page": 1}),
        "oi_aggregated": ("futures/open-interest/aggregated-history", {"symbol": "BTC", "interval": "1d", "limit": 2}),
        "basis": ("futures/basis/history", {"symbol": "BTC", "exchange": "Binance", "interval": "1d", "limit": 1}),
        "etf_flows": ("etf/bitcoin/flow-history", {"limit": 2}),
    }

    async with httpx.AsyncClient() as client:
        for name, (endpoint, params) in endpoints.items():
            url = f"{COINGLASS_BASE}/{endpoint}"
            try:
                resp = await client.get(url, headers=headers, params=params, timeout=15)
                raw = resp.json()
                results[name] = {
                    "status_code": resp.status_code,
                    "response_code": raw.get("code"),
                    "response_msg": raw.get("msg"),
                    "response_success": raw.get("success"),
                    "data_type": type(raw.get("data")).__name__ if "data" in raw else "missing",
                    "data_preview": str(raw.get("data", ""))[:500],
                }
            except Exception as e:
                results[name] = {"error": str(e)}

    return JSONResponse(content=results)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=404, content={"detail": "Not found"})


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
