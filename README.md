# Bitcoin Strategic Cycle Model v7.0

**"The Liquidity Thesis"** - A comprehensive Bitcoin cycle analysis dashboard.

## Overview

This is a live web dashboard for the Bitcoin Strategic Cycle Model, designed to help traders and investors make informed decisions based on:

- **Liquidity Analysis** - Fed Balance Sheet, RRP, TGA, Global M2
- **Business Cycle** - ISM Manufacturing/Services + Regional Fed Leading Indicators
- **Valuation** - MVRV, Power Law, On-Chain Metrics
- **Multi-Timeframe Trends** - STF/MTF/LTF Momentum Analysis
- **Alt Rotation** - ETH/BTC, TOTAL3/BTC, Capital Flow
- **Phase Detection** - Wyckoff Cycle with Transition Forecasting
- **Top Detection** - 10-Indicator Distribution Warning System
- **Monte Carlo** - Cycle-Aware Price Simulation

## Core Thesis

> Bitcoin is a macro liquidity asset. Buy value, sell euphoria.

- Value-dominant buying (MVRV < 2.0 = accumulate)
- Phase-aware selling (MVRV > 5.0 + top signals = distribute)
- 80% drawdown tolerance enables conviction
- Liquidity drives price, not halving cycles

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Strategic-Cycle-Model

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Dashboard

```bash
# Start the server
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/api/analyze` | GET | Full analysis with live data |
| `/api/analyze/default` | GET | Analysis with demo data |
| `/api/live-data` | GET | Live market data only |
| `/api/signal` | GET | Current signal only |
| `/api/thesis` | GET | Generated thesis text |
| `/api/overrides` | GET/POST/DELETE | Manual data overrides |
| `/api/health` | GET | Health check |

## Data Sources

The dashboard fetches live data from:
- **CoinGecko** - BTC/ETH prices, market cap, dominance
- **Alternative.me** - Fear & Greed Index

Some data requires manual input (via the Overrides panel):
- MVRV, NUPL, Puell Multiple (on-chain metrics)
- Fed Balance Sheet, RRP, TGA (liquidity data)
- ISM Manufacturing/Services
- Regional Fed surveys

## Project Structure

```
Strategic-Cycle-Model/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   └── data_service.py   # Data fetching service
├── model/
│   ├── __init__.py
│   └── strategic_cycle_model.py  # Core model
├── static/
│   ├── css/
│   │   └── style.css     # Dashboard styles
│   └── js/
│       └── app.js        # Dashboard JavaScript
├── templates/
│   └── index.html        # Dashboard HTML
├── requirements.txt
├── run.py
└── README.md
```

## Model Components

1. **Liquidity Engine** - Net liquidity, RRP depletion, Fed trajectory
2. **Business Cycle Engine** - ISM + Regional Fed composite
3. **BTC Trend Engine** - Multi-timeframe momentum analysis
4. **Altcoin Engine** - Rotation phase detection
5. **Phase Engine** - Wyckoff cycle detection, MVRV zones
6. **Forecast Engine** - Monte Carlo simulation, phase transitions
7. **Backtest Engine** - Historical regime tracking
8. **Signal Generator** - Final recommendation
9. **Thesis Generator** - Social media output

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## Disclaimer

This model is for educational and informational purposes only. It is not financial advice. Always do your own research and consult with qualified financial advisors before making investment decisions.

## License

MIT License
