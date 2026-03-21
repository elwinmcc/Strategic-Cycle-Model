# BTC Econometric Model v7.6

**12-Layer Scoring Engine** — Fully automated, zero manual inputs.

## Data Sources

- **CoinGlass API v4** (Startup plan) — derivatives, on-chain, ETF, options
- **FRED API** — macro/credit/cycle indicators

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
export COINGLASS_API_KEY="your_key_here"
export FRED_API_KEY="your_key_here"

# Run the dashboard
python run.py
```

Then open http://localhost:8000.

## 12-Layer Model

| Layer | Weight | Source |
|-------|--------|--------|
| Institutional (ETF flows) | 25% | CoinGlass ETF |
| Leverage Fragility | 15% | CoinGlass Funding/L-S |
| Derivatives | 12% | CoinGlass Basis |
| MVRV | 12% | CoinGlass On-Chain |
| Cycle Phase | 10% | FRED (ANFCI/Claims/2s10s) |
| Global Liquidity | 8% | FRED (Fed BS/RRP/TGA) |
| Options Sentiment | 6% | CoinGlass Options |
| Credit | 5% | FRED (HY OAS) |
| Macro-Liquidity | 3% | FRED Composite |
| Support | 2% | CoinGlass Realized Price |
| Momentum | 1% | CoinGlass OHLC |
| Sentiment | 1% | CoinGlass F&G |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/api/analyze` | GET | Full v7.6 analysis with live data |
| `/api/analyze/default` | GET | Analysis with demo data |
| `/api/live-data` | GET | Raw market data |
| `/api/signal` | GET | Current signal only |
| `/api/overrides` | GET/POST/DELETE | Manual data overrides |
| `/api/health` | GET | Health check |

## Signals

The model outputs one of 8 signals based on the final composite score (0-100):

| Score | Signal |
|-------|--------|
| 85+ | AGGRESSIVE_BUY |
| 75-84 | STRONG_BUY |
| 65-74 | BUY |
| 55-64 | ACCUMULATE |
| 45-54 | HOLD |
| 35-44 | REDUCE |
| 25-34 | SELL |
| <25 | STRONG_SELL |

## Project Structure

```
Strategic-Cycle-Model/
├── app/
│   ├── main.py           # FastAPI routes
│   └── data_service.py   # CoinGlass + FRED async client
├── model/
│   ├── __init__.py
│   └── btc_model_v76.py  # 12-layer scoring engine
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
├── requirements.txt
├── run.py
└── README.md
```

## Disclaimer

Educational and informational purposes only. Not financial advice.
