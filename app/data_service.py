"""
Data Service for BTC Econometric Model v7.7
CoinGlass API v4 + FRED API — NO FALLBACKS (one source per data point)

COINGLASS ENDPOINTS:
  spot/pairs-markets (Binance BTCUSDT)               — BTC spot price
  spot/pairs-markets (Binance ETHUSDT)               — ETH spot price
  futures/open-interest/history (Binance BTCUSDT)    — OI + OI 24h change
  futures/funding-rate/history (Binance BTCUSDT)     — Funding rate
  futures/liquidation/history (Binance BTCUSDT)      — Liquidation 24h
  futures/global-long-short-account-ratio/history    — Long/Short ratio (Binance BTCUSDT)
  futures/basis/history (Binance BTCUSDT)            — Futures basis
  option/exchange-oi-history                         — OI change (aggregated)
  option/info                                        — Options OI
  option/max-pain                                    — Max pain + put/call ratio
  etf/bitcoin/flow-history                           — ETF flows
  etf/bitcoin/list                                   — ETF cumulative AUM
  index/bitcoin-lth-realized-price                   — LTH realized price
  index/bitcoin-net-unrealized-profit-loss            — NUPL
  index/fear-greed-history                           — Fear & Greed
  index/bitcoin-dominance                            — BTC dominance
  index/bitcoin-vs-global-m2-growth                  — Global M2
  coinbase-premium-index                             — Coinbase premium
  MVRV: calculated from STH/LTH realized prices

FRED: BAMLH0A0HYM2, T10Y2Y, ICSA, ANFCI, WALCL, RRPONTSYD, WTREGEN, DCOILWTICO
"""

import os
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple
from cachetools import TTLCache
import logging

from model.btc_model_v76 import ModelInputs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache: 5 min for live data
cache = TTLCache(maxsize=100, ttl=300)

# API Keys from environment
COINGLASS_API_KEY = os.environ.get("COINGLASS_API_KEY", "")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# CoinGlass v4 base URL
COINGLASS_BASE = "https://open-api-v4.coinglass.com/api"
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


class CoinGlassClient:
    """Async client for CoinGlass API v4.

    Per-exchange endpoints use exchange=Binance, symbol=BTCUSDT.
    Aggregated endpoints use symbol=BTC.
    No fallbacks — one source per data point.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = COINGLASS_BASE
        self.headers = {
            "accept": "application/json",
            "CG-API-KEY": api_key,
        }

    async def _get(self, client: httpx.AsyncClient, endpoint: str, params: dict = None) -> Any:
        url = f"{self.base}/{endpoint}"
        try:
            resp = await client.get(url, headers=self.headers, params=params or {}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            code = data.get("code")
            if code in ("0", 0) or data.get("success"):
                result = data.get("data", data)
                logger.info(f"CG OK: {endpoint} -> {type(result).__name__}")
                return result
            else:
                logger.warning(f"CG error {endpoint}: code={code}, msg={data.get('msg', '?')}")
                return None
        except Exception as e:
            logger.error(f"CG exception {endpoint}: {e}")
            return None

    # ── Spot Pairs Markets (BTC + ETH prices) ──────────────────────
    # Endpoint: spot/pairs-markets

    async def get_spot_btc(self, client):
        return await self._get(client, "spot/pairs-markets", {"symbol": "BTC"})

    async def get_spot_eth(self, client):
        return await self._get(client, "spot/pairs-markets", {"symbol": "ETH"})

    # ── OI History (Binance BTCUSDT) ────────────────────────────────
    # Response: [{"time":...,"open":"2644845344","high":"...","low":"...","close":"2608846475"}]

    async def get_oi_history(self, client, exchange="Binance", symbol="BTCUSDT"):
        return await self._get(client, "futures/open-interest/history", {
            "exchange": exchange, "symbol": symbol, "interval": "1d",
            "limit": 3, "unit": "usd",
        })

    # ── Long/Short Ratio (Binance BTCUSDT) ─────────────────────────
    # Response: [{"time":...,"global_account_long_percent":73.88,
    #   "global_account_short_percent":26.12,"global_account_long_short_ratio":2.83}]
    # NOTE: API default interval is 4h; 1d may not return data for all exchanges

    async def get_long_short_ratio(self, client, exchange="Binance", symbol="BTCUSDT"):
        return await self._get(client, "futures/global-long-short-account-ratio/history", {
            "exchange": exchange, "symbol": symbol, "interval": "4h", "limit": 1,
        })

    # ── Funding Rate History (Binance BTCUSDT) ────────────────────
    # Response: [{"time":1658880000000,"open":"0.004603","high":"0.009388","low":"-0.005063","close":"0.009229"}]

    async def get_funding_rate_history(self, client, exchange="Binance", symbol="BTCUSDT"):
        return await self._get(client, "futures/funding-rate/history", {
            "exchange": exchange, "symbol": symbol, "interval": "1d", "limit": 1,
        })

    # ── Liquidation History (Binance BTCUSDT) ─────────────────────
    # Response: [{"time":...,"long_liquidation_usd":"2369935.19562","short_liquidation_usd":"6947459.43674"}]

    async def get_liquidation_history(self, client, exchange="Binance", symbol="BTCUSDT"):
        return await self._get(client, "futures/liquidation/history", {
            "exchange": exchange, "symbol": symbol, "interval": "1d", "limit": 1,
        })

    # ── ETF ─────────────────────────────────────────────────────────
    # flow-history response: [{"timestamp":...,"flow_usd":655300000,"price_usd":46663,"etf_flows":[...]}]
    # list response: [{"ticker":"GBTC","volume_usd":...,"price_usd":...,"asset_details":{"net_asset_value_usd":...,...}}]

    async def get_etf_flows(self, client, limit=10):
        return await self._get(client, "etf/bitcoin/flow-history", {"limit": limit})

    async def get_etf_list(self, client):
        return await self._get(client, "etf/bitcoin/list")

    # ── Options ─────────────────────────────────────────────────────
    # option/info response: [{"exchange_name":"All","open_interest_usd":...,"volume_usd_24h":...}]
    # max-pain response: [{"date":"260322","max_pain_price":"70500","call_open_interest":2325,"put_open_interest":3252}]

    async def get_options_info(self, client, symbol="BTC"):
        return await self._get(client, "option/info", {"symbol": symbol})

    async def get_options_max_pain(self, client, symbol="BTC"):
        return await self._get(client, "option/max-pain", {"symbol": symbol, "exchange": "Deribit"})

    # ── On-Chain ────────────────────────────────────────────────────
    # STH response: [{"timestamp":...,"price":71250,"sth_realized_price":85974}]
    # LTH response: [{"timestamp":...,"price":71250,"lth_realized_price":...}]
    # NUPL response: [{"price":...,"net_unpnl":0.52,"timestamp":...}]

    async def get_sth_realized(self, client):
        return await self._get(client, "index/bitcoin-sth-realized-price")

    async def get_lth_realized(self, client):
        return await self._get(client, "index/bitcoin-lth-realized-price")

    async def get_nupl(self, client):
        return await self._get(client, "index/bitcoin-net-unrealized-profit-loss")

    # ── Fear & Greed ────────────────────────────────────────────────
    # Response: {"data_list":[30,15,40,...], "price_list":[...], "time_list":[...]}

    async def get_fear_greed(self, client):
        return await self._get(client, "index/fear-greed-history")

    # ── Coinbase Premium ────────────────────────────────────────────
    # Response: [{"time":...,"premium":5.55,"premium_rate":0.0261}]

    async def get_coinbase_premium(self, client):
        return await self._get(client, "coinbase-premium-index", {"interval": "1d", "limit": 1})

    # ── Bitcoin Dominance ───────────────────────────────────────────
    # Response: [{"timestamp":...,"price":...,"bitcoin_dominance":94.35,"market_cap":...}]

    async def get_dominance(self, client):
        return await self._get(client, "index/bitcoin-dominance")

    # ── Global M2 ──────────────────────────────────────────────────
    # Response: [{"timestamp":...,"price":...,"global_m2_yoy_growth":5.56,"global_m2_supply":...}]

    async def get_global_m2(self, client):
        return await self._get(client, "index/bitcoin-vs-global-m2-growth")

    # ── Futures Basis ────────────────────────────────────────────────
    # Response: [{"time":...,"open_basis":0.0504,"close_basis":0.0445,"open_change":39.5,"close_change":34.56}]
    # Requires: exchange (default Binance), symbol as trading pair (default BTCUSDT), interval

    async def get_futures_basis(self, client, exchange="Binance", symbol="BTCUSDT"):
        return await self._get(client, "futures/basis/history", {
            "exchange": exchange, "symbol": symbol, "interval": "1d", "limit": 1,
        })

    # ── Option OI History (aggregated across exchanges) ────────────
    # Response: [{"time_list":[1691460000000,...],"price_list":[29140.9,...],
    #   "data_map":{"huobi":[15167.03,...],"gate":[23412.72,...],...}}]

    async def get_option_oi_history(self, client, symbol="BTC"):
        return await self._get(client, "option/exchange-oi-history", {
            "symbol": symbol, "unit": "USD",
        })


class FREDClient:
    """Async client for FRED API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = FRED_BASE

    async def get_latest(self, client: httpx.AsyncClient, series_id: str, lookback_days: int = 30) -> Optional[float]:
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        try:
            resp = await client.get(self.base, params={
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "observation_start": start_date,
                "sort_order": "desc",
                "limit": 5,
            }, timeout=10)
            if resp.status_code != 200:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                logger.warning(f"FRED {series_id}: HTTP {resp.status_code} - {data.get('error_message', 'unknown error')}")
                return None
            data = resp.json()
            for o in data.get("observations", []):
                val = o.get("value", ".")
                if val != ".":
                    return float(val)
            return None
        except Exception as e:
            logger.error(f"FRED error {series_id}: {e}")
            return None


class DataServiceV76:
    """Data service for BTC Model v7.6 — CoinGlass v4 + FRED."""

    def __init__(self):
        self.cg = CoinGlassClient(COINGLASS_API_KEY)
        self.fred = FREDClient(FRED_API_KEY)
        self.timeout = httpx.Timeout(20.0)

    async def collect_all_data(self) -> ModelInputs:
        cache_key = "model_inputs_v76"
        if cache_key in cache:
            return cache[cache_key]

        inputs = ModelInputs()
        inputs.timestamp = datetime.now().isoformat()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            results = await asyncio.gather(
                self._fetch_coinglass_data(client, inputs),
                self._fetch_fred_data(client, inputs),
                return_exceptions=True,
            )
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    logger.error(f"Data fetch error (task {i}): {r}")

        # Log population summary
        key_fields = {
            "btc_price": inputs.btc_price,
            "funding_rate": inputs.funding_rate,
            "mvrv": inputs.mvrv,
            "fear_greed": inputs.fear_greed,
            "put_call_ratio": inputs.put_call_ratio,
            "etf_flow_weekly": inputs.etf_flow_weekly,
            "hy_oas": inputs.hy_oas,
        }
        populated = [k for k, v in key_fields.items() if v and v != 0 and v != 50]
        missing = [k for k, v in key_fields.items() if not v or v == 0 or v == 50]
        logger.info(f"Data: {len(populated)}/{len(key_fields)} key fields populated: {', '.join(populated)}")
        if missing:
            logger.warning(f"Data missing: {', '.join(missing)}")

        cache[cache_key] = inputs
        return inputs

    async def _fetch_coinglass_data(self, client: httpx.AsyncClient, inputs: ModelInputs):
        if not COINGLASS_API_KEY:
            logger.warning("COINGLASS_API_KEY not set, skipping CoinGlass data")
            return

        logger.info("Fetching CoinGlass v4 data...")

        results = await asyncio.gather(
            self.cg.get_spot_btc(client),                 # 0  BTC spot price
            self.cg.get_spot_eth(client),                 # 1  ETH spot price
            self.cg.get_oi_history(client),               # 2  OI + OI 24h change (Binance BTCUSDT)
            self.cg.get_funding_rate_history(client),     # 3  Funding rate (Binance BTCUSDT)
            self.cg.get_liquidation_history(client),      # 4  Liquidation 24h (Binance BTCUSDT)
            self.cg.get_long_short_ratio(client),         # 5  L/S ratio (Binance BTCUSDT)
            self.cg.get_futures_basis(client),            # 6  Futures basis (Binance BTCUSDT)
            self.cg.get_etf_flows(client, 10),            # 7  ETF flows
            self.cg.get_etf_list(client),                 # 8  ETF cumulative
            self.cg.get_options_info(client),              # 9  Options OI
            self.cg.get_options_max_pain(client),          # 10 Max pain + put/call
            self.cg.get_sth_realized(client),              # 11 STH realized price
            self.cg.get_lth_realized(client),              # 12 LTH realized price
            self.cg.get_nupl(client),                      # 13 NUPL
            self.cg.get_fear_greed(client),                # 14 Fear & Greed
            self.cg.get_dominance(client),                 # 15 BTC dominance
            self.cg.get_coinbase_premium(client),          # 16 Coinbase premium
            self.cg.get_global_m2(client),                 # 17 Global M2
            self.cg.get_option_oi_history(client),        # 18 Option OI history (for OI change)
            return_exceptions=True,
        )

        (spot_btc, spot_eth, oi_hist, funding_hist, liq_hist, ls_hist,
         basis, etf_flows, etf_list, opt_info, max_pain, sth, lth,
         nupl_data, fg, dom, prem, m2, opt_oi_hist) = results

        # Spot prices
        self._parse_spot_price(inputs, spot_btc, "BTC")
        self._parse_spot_price(inputs, spot_eth, "ETH")
        # Derivatives (all Binance BTCUSDT — one source each)
        self._parse_oi_history(inputs, oi_hist)
        self._parse_option_oi_history(inputs, opt_oi_hist)
        self._parse_funding_history(inputs, funding_hist)
        self._parse_liquidation_history(inputs, liq_hist)
        self._parse_long_short_history(inputs, ls_hist)
        self._parse_futures_basis(inputs, basis)
        # Institutional
        self._parse_etf_flows(inputs, etf_flows)
        self._parse_etf_list(inputs, etf_list)
        self._parse_options(inputs, opt_info)
        self._parse_max_pain(inputs, max_pain)
        # On-chain
        self._parse_sth(inputs, sth)
        self._parse_lth(inputs, lth)
        self._compute_mvrv(inputs)
        self._parse_nupl(inputs, nupl_data)
        # Sentiment / macro
        self._parse_fear_greed(inputs, fg)
        self._parse_dominance(inputs, dom)
        self._parse_premium(inputs, prem)
        self._parse_m2(inputs, m2)

    # ── Parse: Spot Pairs Markets (BTC or ETH price) ─────────────────
    # Response: [{"symbol":"BTC/USDT","exchange_name":"Binance","current_price":87503.55,
    #   "price_change_24h":2735.79,"price_change_percent_24h":3.23,
    #   "volume_usd_24h":1585522232.603,...}]

    def _parse_spot_price(self, inputs, data, coin):
        if not data or isinstance(data, Exception):
            logger.warning(f"Spot {coin}: no data or exception")
            return
        entry = None
        if isinstance(data, list) and len(data) > 0:
            # Find Binance USDT pair first, else use first entry
            for row in data:
                if isinstance(row, dict) and row.get("exchange_name") == "Binance":
                    entry = row
                    break
            if not entry:
                entry = data[0]
        elif isinstance(data, dict):
            entry = data
        if not isinstance(entry, dict):
            logger.warning(f"Spot {coin}: unexpected data type {type(data).__name__}")
            return
        price = float(entry.get("current_price", 0))
        if price <= 0:
            logger.warning(f"Spot {coin}: no current_price. Keys: {list(entry.keys())}")
            return
        if coin == "BTC":
            inputs.btc_price = round(price, 2)
            inputs.sources["btc_price"] = "CoinGlass v4 spot/pairs-markets (Binance)"
            inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)
            logger.info(f"Spot BTC: ${inputs.btc_price}")
        elif coin == "ETH":
            inputs.eth_price = round(price, 2)
            inputs.sources["eth_price"] = "CoinGlass v4 spot/pairs-markets (Binance)"
            if inputs.btc_price > 0:
                inputs.eth_btc = round(price / inputs.btc_price, 6)
                inputs.sources["eth_btc"] = "Calculated (ETH/BTC)"
            logger.info(f"Spot ETH: ${inputs.eth_price}, ETH/BTC={inputs.eth_btc}")

    # ── Parse: OI History (Binance BTCUSDT) ────────────────────────
    # Response: [{"time":...,"open":"2644845344","high":"...","low":"...","close":"2608846475"}, ...]

    def _parse_oi_history(self, inputs, data):
        if not data or isinstance(data, Exception):
            logger.warning(f"OI history: no data or exception: {data}")
            return
        if not isinstance(data, list) or len(data) == 0:
            logger.warning(f"OI history: not a list or empty, type={type(data).__name__}")
            return
        logger.info(f"OI history: got {len(data)} entries, keys={list(data[0].keys()) if data else '?'}")
        curr = data[-1] if isinstance(data[-1], dict) else None
        if not curr:
            return
        curr_oi = float(curr.get("close", curr.get("c", 0)))
        if curr_oi > 0:
            inputs.oi_total = curr_oi
            inputs.sources["futures_oi"] = "CoinGlass v4 OI History (Binance BTCUSDT)"
        if len(data) >= 2:
            prev = data[-2] if isinstance(data[-2], dict) else None
            if prev:
                prev_oi = float(prev.get("close", prev.get("c", 0)))
                logger.info(f"OI history: prev={prev_oi}, curr={curr_oi}")
                if prev_oi > 0 and curr_oi > 0:
                    pct_change = (curr_oi - prev_oi) / prev_oi * 100
                    inputs.oi_change_24h_pct = round(pct_change, 2)
                    inputs.sources["oi_change"] = "CoinGlass v4 OI History (Binance BTCUSDT)"
                    logger.info(f"OI 24h change: {inputs.oi_change_24h_pct}%")
        else:
            logger.warning(f"OI history: only {len(data)} entries, need 2+ for change calc")

    # ── Parse: Liquidation History (Binance BTCUSDT) ─────────────────
    # Response: [{"time":...,"long_liquidation_usd":"2369935.19562","short_liquidation_usd":"6947459.43674"}]

    def _parse_liquidation_history(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        if not isinstance(data, list) or len(data) == 0:
            return
        entry = data[-1] if isinstance(data[-1], dict) else None
        if not entry:
            return
        long_liq = float(entry.get("long_liquidation_usd", 0))
        short_liq = float(entry.get("short_liquidation_usd", 0))
        total = long_liq + short_liq
        if total > 0:
            inputs.liquidation_24h = total
            inputs.sources["liquidation"] = "CoinGlass v4 Liquidation History (Binance BTCUSDT)"

    # ── Parse: Long/Short Ratio (Binance BTCUSDT) ──────────────────
    # Response: [{"time":...,"global_account_long_short_ratio":2.83,
    #   "global_account_long_percent":73.88,"global_account_short_percent":26.12}]

    def _parse_long_short_history(self, inputs, data):
        if not data or isinstance(data, Exception):
            logger.warning(f"L/S ratio: no data or exception: {type(data).__name__}")
            return
        if not isinstance(data, list) or len(data) == 0:
            logger.warning(f"L/S ratio: not a list or empty, type={type(data).__name__}")
            return
        entry = data[-1] if isinstance(data[-1], dict) else None
        if not entry:
            return
        logger.info(f"L/S ratio entry keys: {list(entry.keys())}")
        ratio = float(entry.get("global_account_long_short_ratio", 0))
        if ratio > 0:
            inputs.long_short_ratio = round(ratio, 3)
            inputs.sources["long_short"] = "CoinGlass v4 L/S Ratio (Binance BTCUSDT)"
            logger.info(f"L/S ratio: {inputs.long_short_ratio}")
        else:
            logger.warning(f"L/S ratio: field not found or 0. Entry: {entry}")

    # ── Parse: STH Realized Price ─────────────────────────────────
    # Response: [{"timestamp":..., "price":71250, "sth_realized_price":85974}, ...]

    def _parse_sth(self, inputs, sth):
        if not sth or isinstance(sth, Exception):
            return
        if isinstance(sth, list) and len(sth) > 0:
            entry = sth[-1]
            if isinstance(entry, dict):
                sth_price = None
                for key in ("sth_realized_price", "sthRealizedPrice", "value"):
                    if key in entry and entry[key] is not None:
                        sth_price = float(entry[key])
                        break
                if sth_price and sth_price > 0:
                    inputs.sth_realized_price = sth_price
                    inputs.sources["sth_price"] = "CoinGlass v4 STH RP"
                else:
                    logger.warning(f"STH RP field not found. Available keys: {list(entry.keys())}")
                # 30d ago price for momentum
                if len(sth) >= 30:
                    old_entry = sth[-30]
                    if isinstance(old_entry, dict):
                        inputs.price_30d_ago = float(old_entry.get("price", 0))
                        inputs.sources["price_history"] = "CoinGlass v4 STH (30d)"

    # ── Parse: LTH Realized Price ──────────────────────────────────
    # Response: [{"timestamp":..., "price":71250, "lth_realized_price":...}, ...]

    def _parse_lth(self, inputs, lth):
        if not lth or isinstance(lth, Exception):
            return
        if isinstance(lth, list) and len(lth) > 0:
            entry = lth[-1]
            if isinstance(entry, dict):
                lth_price = None
                for key in ("lth_realized_price", "lthRealizedPrice", "value"):
                    if key in entry and entry[key] is not None:
                        lth_price = float(entry[key])
                        break
                if lth_price and lth_price > 0:
                    inputs.lth_realized_price = lth_price
                    inputs.sources["lth_price"] = "CoinGlass v4 LTH RP"
                else:
                    logger.warning(f"LTH RP field not found. Available keys: {list(entry.keys())}")

    def _compute_mvrv(self, inputs):
        if inputs.sth_realized_price > 0 and inputs.lth_realized_price > 0:
            inputs.realized_price = (inputs.sth_realized_price * 0.4 + inputs.lth_realized_price * 0.6)
        elif inputs.sth_realized_price > 0:
            inputs.realized_price = inputs.sth_realized_price

        if inputs.realized_price > 0 and inputs.btc_price > 0:
            inputs.mvrv = round(inputs.btc_price / inputs.realized_price, 3)
            inputs.sources["mvrv"] = "Calculated (Price / Realized Price)"
        else:
            inputs.warnings.append("MVRV: Could not calculate - missing data")

    # ── Parse: NUPL ────────────────────────────────────────────────
    # Live response: [{"price":..., "net_unpnl":0.52, "timestamp":...}, ...]

    def _parse_nupl(self, inputs, nupl_data):
        if not nupl_data or isinstance(nupl_data, Exception):
            return
        entry = None
        if isinstance(nupl_data, list) and len(nupl_data) > 0:
            entry = nupl_data[-1]
        elif isinstance(nupl_data, dict):
            entry = nupl_data
        if not isinstance(entry, dict):
            return
        nupl = None
        for key in ("net_unpnl", "nupl", "NUPL", "netUnrealizedPnl", "value"):
            if key in entry and entry[key] is not None:
                nupl = float(entry[key])
                break
        if nupl is not None:
            inputs.nupl = nupl
            inputs.sources["nupl"] = "CoinGlass v4 NUPL"
        else:
            logger.warning(f"NUPL field not found. Available keys: {list(entry.keys())}")

    # ── Parse: Funding Rate History (Binance BTCUSDT) ────────────────
    # Response: [{"time":1658880000000,"open":"0.004603","high":"0.009388",
    #             "low":"-0.005063","close":"0.009229"}]

    def _parse_funding_history(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        entry = None
        if isinstance(data, list) and len(data) > 0:
            entry = data[-1] if isinstance(data[-1], dict) else data[0]
        elif isinstance(data, dict):
            entry = data
        if not isinstance(entry, dict):
            return
        rate = None
        for key in ("close", "open", "c", "o"):
            if key in entry and entry[key] is not None:
                try:
                    rate = float(entry[key])
                    break
                except (ValueError, TypeError):
                    pass
        if rate is not None:
            inputs.funding_rate = round(rate, 6)
            inputs.sources["funding_rate"] = "CoinGlass v4 Funding Rate (Binance BTCUSDT)"

    # ── Parse: Futures Basis ─────────────────────────────────────────
    # v4 response: [{"time":...,"open_basis":0.0504,"close_basis":0.0445,"open_change":39.5,"close_change":34.56}]
    # Basis values are percentages (e.g. 0.0504 = 5.04%)

    def _parse_futures_basis(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        entry = None
        if isinstance(data, list) and len(data) > 0:
            entry = data[-1] if isinstance(data[-1], dict) else data[0]
        elif isinstance(data, dict):
            entry = data
        if not isinstance(entry, dict):
            return
        basis = None
        for key in ("close_basis", "open_basis", "closeBasis", "openBasis",
                     "annualizedBasis", "annualized_basis", "basis", "basisRate"):
            if key in entry and entry[key] is not None:
                basis = float(entry[key])
                break
        if basis is not None:
            # API returns basis as a decimal ratio (0.0504 = 5.04%), model expects percentage
            if abs(basis) < 1:
                basis = basis * 100
            inputs.futures_basis = round(basis, 2)
            inputs.sources["futures_basis"] = "CoinGlass v4 Futures Basis"
        else:
            logger.warning(f"Basis field not found. Available keys: {list(entry.keys())}")

    # ── Parse: Option OI History (aggregated — for OI change) ────────
    # Response: [{"time_list":[ts1,ts2,...],"price_list":[p1,p2,...],
    #   "data_map":{"huobi":[oi1,oi2,...],"gate":[oi1,oi2,...],...}}]
    # Sum all exchanges at last two timestamps to compute OI and 24h change.

    def _parse_option_oi_history(self, inputs, data):
        if not data or isinstance(data, Exception):
            logger.warning(f"Option OI history: no data or exception")
            return
        entry = None
        if isinstance(data, list) and len(data) > 0:
            entry = data[0]
        elif isinstance(data, dict):
            entry = data
        if not isinstance(entry, dict):
            return
        time_list = entry.get("time_list", [])
        data_map = entry.get("data_map", {})
        if not time_list or not data_map:
            logger.warning(f"Option OI history: missing time_list or data_map")
            return
        n = len(time_list)
        if n < 2:
            logger.warning(f"Option OI history: only {n} timestamps, need 2+")
            return
        # Sum OI across all exchanges at last two timestamps
        curr_total = 0.0
        prev_total = 0.0
        for exchange, oi_list in data_map.items():
            if not isinstance(oi_list, list) or len(oi_list) < n:
                continue
            curr_val = oi_list[-1] if oi_list[-1] is not None else 0
            prev_val = oi_list[-2] if oi_list[-2] is not None else 0
            curr_total += float(curr_val)
            prev_total += float(prev_val)
        if curr_total > 0 and inputs.oi_total == 0:
            inputs.oi_total = curr_total
            inputs.sources["futures_oi"] = "CoinGlass v4 Option OI History"
        if prev_total > 0 and curr_total > 0 and "oi_change" not in inputs.sources:
            pct_change = (curr_total - prev_total) / prev_total * 100
            inputs.oi_change_24h_pct = round(pct_change, 2)
            inputs.sources["oi_change"] = "CoinGlass v4 Option OI History"
            logger.info(f"Option OI change: prev={prev_total:.0f}, curr={curr_total:.0f}, change={inputs.oi_change_24h_pct}%")

    # ── Parse: ETF Flows ───────────────────────────────────────────
    # Response: [{"timestamp":..., "flow_usd":655300000, "price_usd":69887.4, "etf_flows":[...]}, ...]

    def _parse_etf_flows(self, inputs, etf_flows):
        if not etf_flows or isinstance(etf_flows, Exception):
            return
        if isinstance(etf_flows, list):
            sorted_flows = sorted(
                [e for e in etf_flows if isinstance(e, dict)],
                key=lambda x: x.get("timestamp", x.get("date", x.get("t", 0))),
                reverse=True,
            )
            daily_flows = []
            for entry in sorted_flows:
                flow = 0.0
                for key in ("flow_usd", "totalNetFlow", "netFlow", "total_net_flow", "value"):
                    if key in entry and entry[key] is not None:
                        flow = float(entry[key])
                        break
                daily_flows.append(flow)
            if daily_flows:
                inputs.etf_flow_daily = daily_flows[0]
                inputs.etf_flow_weekly = sum(daily_flows[:5])
                inputs.sources["etf_flows"] = f"CoinGlass v4 ETF ({len(daily_flows)} days)"
                if inputs.etf_flow_daily == 0 and sorted_flows:
                    logger.warning(f"ETF flow field not found. Keys: {list(sorted_flows[0].keys())}")

    # ── Parse: ETF List ────────────────────────────────────────────
    # Live response: [{"ticker":"GBTC","asset_details":{"net_asset_value_usd":...,"holding_quantity":...}, ...}]

    def _parse_etf_list(self, inputs, etf_list):
        if not etf_list or isinstance(etf_list, Exception):
            return
        if isinstance(etf_list, list):
            total_nav = 0
            for e in etf_list:
                if not isinstance(e, dict):
                    continue
                details = e.get("asset_details", {})
                if isinstance(details, dict):
                    nav = details.get("net_asset_value_usd", 0)
                    if nav:
                        total_nav += float(nav)
            if total_nav > 0:
                inputs.etf_cumulative = total_nav

    # ── Parse: Options Info ────────────────────────────────────────
    # Live response: [{"exchange_name":"All","open_interest_usd":42579833237,...}, {"exchange_name":"Deribit",...}]

    def _parse_options(self, inputs, opt_info):
        if not opt_info or isinstance(opt_info, Exception):
            return
        if isinstance(opt_info, list):
            for item in opt_info:
                if not isinstance(item, dict):
                    continue
                # Use "All" aggregate row if available
                if item.get("exchange_name") == "All":
                    inputs.options_oi = float(item.get("open_interest_usd", 0))
                    inputs.sources["options"] = "CoinGlass v4 Options"
                    break
                # Otherwise sum
                inputs.options_oi += float(item.get("open_interest_usd", 0))
            if inputs.options_oi > 0 and "options" not in inputs.sources:
                inputs.sources["options"] = "CoinGlass v4 Options"

    # ── Parse: Max Pain ────────────────────────────────────────────
    # Live response: [{"date":"260322","max_pain_price":"70500","call_open_interest":2325,"put_open_interest":3252,...}]

    def _parse_max_pain(self, inputs, max_pain):
        if not max_pain or isinstance(max_pain, Exception):
            return
        if isinstance(max_pain, list) and len(max_pain) > 0:
            # Use the nearest expiry (first entry)
            entry = max_pain[0]
            if isinstance(entry, dict):
                mp = entry.get("max_pain_price", 0)
                inputs.max_pain = float(mp)
                inputs.sources["max_pain"] = "CoinGlass v4 Max Pain"
                # Compute put/call ratio from this data
                call_oi = float(entry.get("call_open_interest", 0))
                put_oi = float(entry.get("put_open_interest", 0))
                if call_oi > 0 and put_oi > 0:
                    inputs.put_call_ratio = round(put_oi / call_oi, 3)
                    inputs.sources["put_call"] = "CoinGlass v4 Max Pain (put/call OI)"

    # ── Parse: Fear & Greed ────────────────────────────────────────
    # Live response: {"data_list":[30,15,40,...], "price_list":[...], "time_list":[...]}  (dict!)

    def _parse_fear_greed(self, inputs, fg):
        if not fg or isinstance(fg, Exception):
            return
        value = None
        # Format 1: dict with data_list array
        if isinstance(fg, dict):
            data_list = fg.get("data_list", [])
            if data_list and isinstance(data_list, list) and len(data_list) > 0:
                value = int(float(data_list[-1]))
            else:
                # Format 2: dict with value/classification directly
                for key in ("value", "fgi", "fear_greed"):
                    if key in fg and fg[key] is not None:
                        value = int(float(fg[key]))
                        break
        elif isinstance(fg, list) and len(fg) > 0:
            entry = fg[-1] if isinstance(fg[-1], dict) else fg[0] if isinstance(fg[0], dict) else {}
            # Format 3: list of dicts with data_list
            data_list = entry.get("data_list", [])
            if data_list:
                value = int(float(data_list[-1]))
            else:
                # Format 4: list of dicts with value field
                for key in ("value", "fgi", "fear_greed"):
                    if key in entry and entry[key] is not None:
                        value = int(float(entry[key]))
                        break
        if value is not None:
            inputs.fear_greed = value
            inputs.fear_greed_label = self._classify_fear_greed(value)
            inputs.sources["fear_greed"] = "CoinGlass v4 F&G"

    @staticmethod
    def _classify_fear_greed(value: int) -> str:
        if value <= 20: return "Extreme Fear"
        if value <= 40: return "Fear"
        if value <= 60: return "Neutral"
        if value <= 80: return "Greed"
        return "Extreme Greed"

    # ── Parse: Dominance ───────────────────────────────────────────
    # Live response: [{"timestamp":...,"price":...,"bitcoin_dominance":94.35,"market_cap":...}, ...]

    def _parse_dominance(self, inputs, dom):
        if not dom or isinstance(dom, Exception):
            return
        entry = None
        if isinstance(dom, list) and len(dom) > 0:
            entry = dom[-1] if isinstance(dom[-1], dict) else None
        elif isinstance(dom, dict):
            entry = dom
        if not isinstance(entry, dict):
            return
        dom_val = None
        for key in ("bitcoin_dominance", "dominance", "btcDominance", "value"):
            if key in entry and entry[key] is not None:
                dom_val = float(entry[key])
                break
        if dom_val is not None:
            inputs.btc_dominance = dom_val
            inputs.sources["dominance"] = "CoinGlass v4"
            if inputs.btc_price > 0:
                mkt_cap = float(entry.get("market_cap", entry.get("marketCap", 0)))
                if mkt_cap > 0:
                    inputs.btc_market_cap = mkt_cap
        else:
            logger.warning(f"Dominance field not found. Available keys: {list(entry.keys())}")

    # ── Parse: Coinbase Premium ────────────────────────────────────
    # Response: [{"time":...,"premium":5.55,"premium_rate":0.0261,"coinbase_price":30772.93}]
    # premium_rate is decimal (0.0261 = 2.61%), model expects percentage

    def _parse_premium(self, inputs, prem):
        if not prem or isinstance(prem, Exception):
            logger.warning(f"Coinbase premium: no data or exception: {type(prem).__name__ if prem else 'None'}")
            return
        entry = None
        if isinstance(prem, list) and len(prem) > 0:
            entry = prem[-1] if isinstance(prem[-1], dict) else None
        elif isinstance(prem, dict):
            entry = prem
        if not isinstance(entry, dict):
            return
        logger.info(f"Coinbase premium entry keys: {list(entry.keys())}")
        # Prefer premium_rate (decimal -> percentage)
        rate = entry.get("premium_rate")
        if rate is not None:
            inputs.coinbase_premium = round(float(rate) * 100, 4)
            inputs.sources["cb_premium"] = "CoinGlass v4 Coinbase Premium"
            logger.info(f"Coinbase premium: rate={rate}, stored={inputs.coinbase_premium}%")
        else:
            # Fallback: use raw premium (USD)
            premium = entry.get("premium")
            if premium is not None:
                inputs.coinbase_premium = float(premium)
                inputs.sources["cb_premium"] = "CoinGlass v4 Coinbase Premium (USD)"
            else:
                logger.warning(f"Premium fields not found. Keys: {list(entry.keys())}")

    # ── Parse: Global M2 ──────────────────────────────────────────
    # Live response: [{"timestamp":...,"price":...,"global_m2_yoy_growth":5.56,"global_m2_supply":...}, ...]

    def _parse_m2(self, inputs, m2):
        if not m2 or isinstance(m2, Exception):
            return
        entry = None
        if isinstance(m2, list) and len(m2) > 0:
            entry = m2[-1] if isinstance(m2[-1], dict) else None
        elif isinstance(m2, dict):
            entry = m2
        if not isinstance(entry, dict):
            return
        growth = None
        for key in ("global_m2_yoy_growth", "m2Growth", "m2_growth", "globalM2YoyGrowth", "value"):
            if key in entry and entry[key] is not None:
                growth = float(entry[key])
                break
        if growth is not None:
            inputs.global_m2_growth = growth
            inputs.sources["global_m2"] = "CoinGlass v4 M2"
        else:
            logger.warning(f"M2 growth field not found. Available keys: {list(entry.keys())}")

    # ── FRED Data ───────────────────────────────────────────────────

    async def _fetch_fred_data(self, client: httpx.AsyncClient, inputs: ModelInputs):
        if not FRED_API_KEY:
            logger.warning("FRED_API_KEY not set, skipping macro data")
            return

        logger.info("Fetching FRED data...")

        results = await asyncio.gather(
            self.fred.get_latest(client, "BAMLH0A0HYM2"),
            self.fred.get_latest(client, "T10Y2Y"),
            self.fred.get_latest(client, "ICSA"),
            self.fred.get_latest(client, "ANFCI", lookback_days=45),
            self.fred.get_latest(client, "WALCL", lookback_days=14),
            self.fred.get_latest(client, "RRPONTSYD", lookback_days=14),
            self.fred.get_latest(client, "WTREGEN", lookback_days=14),
            self.fred.get_latest(client, "DCOILWTICO", lookback_days=7),
            return_exceptions=True,
        )

        hy, yc, claims, anfci, fed, rrp, tga, wti = results

        if not isinstance(hy, Exception) and hy is not None:
            inputs.hy_oas = hy
            inputs.sources["hy_oas"] = "FRED BAMLH0A0HYM2"

        if not isinstance(yc, Exception) and yc is not None:
            inputs.yield_curve_2s10s = yc
            inputs.sources["2s10s"] = "FRED T10Y2Y"

        if not isinstance(claims, Exception) and claims is not None:
            inputs.initial_claims = claims
            inputs.sources["claims"] = "FRED ICSA"

        if not isinstance(anfci, Exception) and anfci is not None:
            inputs.anfci = anfci
            inputs.sources["anfci"] = "FRED ANFCI"

        if not isinstance(fed, Exception) and fed is not None:
            inputs.fed_bs = fed / 1000  # millions -> billions
            inputs.sources["fed_bs"] = "FRED WALCL"

        if not isinstance(rrp, Exception) and rrp is not None:
            inputs.rrp = rrp / 1000
            inputs.sources["rrp"] = "FRED RRPONTSYD"

        if not isinstance(tga, Exception) and tga is not None:
            inputs.tga = tga / 1000
            inputs.sources["tga"] = "FRED WTREGEN"

        if not isinstance(wti, Exception) and wti is not None:
            inputs.wti_price = wti
            inputs.sources["wti"] = "FRED DCOILWTICO"


# Singleton instance
data_service = DataServiceV76()
