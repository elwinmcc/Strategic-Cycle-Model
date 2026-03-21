"""
Data Service for BTC Econometric Model v7.6
Primary: CoinGlass API v4 (verified against live responses)
Secondary: FRED API (macro/credit/cycle)

IMPORTANT: coins-markets and spot-markets require upgraded plan (401).
BTC price is obtained from on-chain endpoints (sth-realized-price).
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

    All endpoints and field names verified against live API responses.
    coins-markets requires upgraded plan; BTC price comes from on-chain data.
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

    # ── Funding Rates ───────────────────────────────────────────────
    # Response: {"data": [{"symbol":"BTC", "stablecoin_margin_list":[{"exchange":"Binance","funding_rate":0.001,...},...]}]}

    async def get_funding_rates(self, client, symbol="BTC"):
        return await self._get(client, "futures/funding-rate/exchange-list", {"symbol": symbol})

    # ── Liquidations ────────────────────────────────────────────────
    # Requires exchange_list param. Response: [{"time":...,"aggregated_long_liquidation_usd":...,"aggregated_short_liquidation_usd":...}]

    async def get_liquidations(self, client, symbol="BTC"):
        return await self._get(client, "futures/liquidation/aggregated-history", {
            "symbol": symbol, "interval": "1d", "limit": 1, "exchange_list": "Binance,OKX,Bybit"
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
    # max-pain requires exchange param. Response: [{"date":"...","max_pain_price":"70500","call_open_interest":2325,"put_open_interest":3252}]

    async def get_options_info(self, client, symbol="BTC"):
        return await self._get(client, "option/info", {"symbol": symbol})

    async def get_options_max_pain(self, client, symbol="BTC"):
        return await self._get(client, "option/max-pain", {"symbol": symbol, "exchange": "Deribit"})

    # ── On-Chain ────────────────────────────────────────────────────
    # STH response: [{"timestamp":...,"price":71250,"sth_realized_price":85974}]  (price = BTC price!)
    # LTH response: [{"timestamp":...,"price":71250,"lth_realized_price":...}]
    # NUPL response: [{"price":...,"net_unpnl":0.52,"timestamp":...}]

    async def get_sth_realized(self, client):
        return await self._get(client, "index/bitcoin-sth-realized-price")

    async def get_lth_realized(self, client):
        return await self._get(client, "index/bitcoin-lth-realized-price")

    async def get_nupl(self, client):
        return await self._get(client, "index/bitcoin-net-unrealized-profit-loss")

    # ── Fear & Greed ────────────────────────────────────────────────
    # Response: {"data_list":[30,15,40,...], "price_list":[...], "time_list":[...]}  (dict, not list!)

    async def get_fear_greed(self, client):
        return await self._get(client, "index/fear-greed-history")

    # ── Coinbase Premium ────────────────────────────────────────────
    # Response: [{"time":...,"premium":-13.72,"premium_rate":-0.0195}]

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
            self.cg.get_funding_rates(client),       # 0
            self.cg.get_liquidations(client),         # 1
            self.cg.get_etf_flows(client, 10),        # 2
            self.cg.get_etf_list(client),             # 3
            self.cg.get_options_info(client),          # 4
            self.cg.get_options_max_pain(client),      # 5
            self.cg.get_sth_realized(client),          # 6
            self.cg.get_lth_realized(client),          # 7
            self.cg.get_nupl(client),                  # 8
            self.cg.get_fear_greed(client),            # 9
            self.cg.get_dominance(client),             # 10
            self.cg.get_coinbase_premium(client),      # 11
            self.cg.get_global_m2(client),             # 12
            return_exceptions=True,
        )

        (funding, liq, etf_flows, etf_list, opt_info, max_pain,
         sth, lth, nupl_data, fg, dom, prem, m2) = results

        # Parse in order: STH first (provides BTC price)
        self._parse_sth(inputs, sth)
        self._parse_lth(inputs, lth)
        self._compute_mvrv(inputs)
        self._parse_nupl(inputs, nupl_data)
        self._parse_funding(inputs, funding)
        self._parse_liquidations(inputs, liq)
        self._parse_etf_flows(inputs, etf_flows)
        self._parse_etf_list(inputs, etf_list)
        self._parse_options(inputs, opt_info)
        self._parse_max_pain(inputs, max_pain)
        self._parse_fear_greed(inputs, fg)
        self._parse_dominance(inputs, dom)
        self._parse_premium(inputs, prem)
        self._parse_m2(inputs, m2)

    # ── Parse: STH Realized Price (also provides BTC price) ────────
    # Live response: [{"timestamp":..., "price":71250, "sth_realized_price":85974}, ...]

    def _parse_sth(self, inputs, sth):
        if not sth or isinstance(sth, Exception):
            return
        if isinstance(sth, list) and len(sth) > 0:
            entry = sth[-1]
            if isinstance(entry, dict):
                inputs.sth_realized_price = float(entry.get("sth_realized_price", 0))
                # BTC price from this endpoint (coins-markets is 401 on startup plan)
                price = float(entry.get("price", 0))
                if price > 0:
                    inputs.btc_price = price
                    inputs.sources["btc_price"] = "CoinGlass v4 STH (on-chain)"
                    inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)
                if inputs.sth_realized_price > 0:
                    inputs.sources["sth_price"] = "CoinGlass v4 STH RP"
                # Also get 30d ago price for momentum
                if len(sth) >= 30:
                    old_entry = sth[-30]
                    if isinstance(old_entry, dict):
                        inputs.price_30d_ago = float(old_entry.get("price", 0))
                        inputs.sources["price_history"] = "CoinGlass v4 STH (30d)"

    # ── Parse: LTH Realized Price ──────────────────────────────────
    # Live response: [{"timestamp":..., "price":71250, "lth_realized_price":...}, ...]

    def _parse_lth(self, inputs, lth):
        if not lth or isinstance(lth, Exception):
            return
        if isinstance(lth, list) and len(lth) > 0:
            entry = lth[-1]
            if isinstance(entry, dict):
                inputs.lth_realized_price = float(entry.get("lth_realized_price", 0))
                if inputs.lth_realized_price > 0:
                    inputs.sources["lth_price"] = "CoinGlass v4 LTH RP"
                # Also get ETH price from LTH if BTC price not yet set
                if inputs.btc_price == 0:
                    price = float(entry.get("price", 0))
                    if price > 0:
                        inputs.btc_price = price
                        inputs.sources["btc_price"] = "CoinGlass v4 LTH (on-chain)"
                        inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)

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
        if isinstance(nupl_data, list) and len(nupl_data) > 0:
            entry = nupl_data[-1]
            if isinstance(entry, dict):
                inputs.nupl = float(entry.get("net_unpnl", 0))
                inputs.sources["nupl"] = "CoinGlass v4 NUPL"

    # ── Parse: Funding Rates ───────────────────────────────────────
    # Live response: [{"symbol":"BTC","stablecoin_margin_list":[{"exchange":"Binance","funding_rate":0.002,...},...]}]

    def _parse_funding(self, inputs, funding):
        if not funding or isinstance(funding, Exception):
            return
        rates = []
        if isinstance(funding, list) and len(funding) > 0:
            first = funding[0]
            if isinstance(first, dict):
                # v4 nests rates inside stablecoin_margin_list
                margin_list = first.get("stablecoin_margin_list", [])
                if margin_list:
                    for item in margin_list:
                        if isinstance(item, dict):
                            r = item.get("funding_rate")
                            if r is not None:
                                try:
                                    rates.append(float(r))
                                except (ValueError, TypeError):
                                    pass
                # Also check token_margin_list
                token_list = first.get("token_margin_list", [])
                for item in (token_list or []):
                    if isinstance(item, dict):
                        r = item.get("funding_rate")
                        if r is not None:
                            try:
                                rates.append(float(r))
                            except (ValueError, TypeError):
                                pass
        if rates:
            inputs.funding_rate = round(sum(rates) / len(rates), 6)
            inputs.sources["funding_rate"] = f"CoinGlass v4 ({len(rates)} exchanges)"

    # ── Parse: Liquidations ────────────────────────────────────────
    # Live response: [{"time":...,"aggregated_long_liquidation_usd":989010,"aggregated_short_liquidation_usd":956545}]

    def _parse_liquidations(self, inputs, liq):
        if not liq or isinstance(liq, Exception):
            return
        if isinstance(liq, list) and len(liq) > 0:
            entry = liq[0]
            if isinstance(entry, dict):
                long_liq = float(entry.get("aggregated_long_liquidation_usd", 0))
                short_liq = float(entry.get("aggregated_short_liquidation_usd", 0))
                inputs.liquidation_24h = long_liq + short_liq
                if long_liq + short_liq > 0:
                    # Derive long/short ratio from liquidation data as approximation
                    if inputs.long_short_ratio == 1.0 and short_liq > 0:
                        inputs.long_short_ratio = round(long_liq / short_liq, 2)
                        inputs.sources["long_short"] = "CoinGlass v4 Liq Ratio"
                inputs.sources["liquidation"] = "CoinGlass v4"

    # ── Parse: ETF Flows ───────────────────────────────────────────
    # Live response: [{"timestamp":..., "flow_usd":655300000, "price_usd":46663, "etf_flows":[...]}, ...]

    def _parse_etf_flows(self, inputs, etf_flows):
        if not etf_flows or isinstance(etf_flows, Exception):
            return
        if isinstance(etf_flows, list):
            daily_flows = []
            for entry in etf_flows[:10]:
                if isinstance(entry, dict):
                    flow = float(entry.get("flow_usd", 0))
                    daily_flows.append(flow)
            if daily_flows:
                inputs.etf_flow_daily = daily_flows[0]
                inputs.etf_flow_weekly = sum(daily_flows[:5])
                inputs.sources["etf_flows"] = f"CoinGlass v4 ETF ({len(daily_flows)} days)"

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
        # v4 returns a dict with data_list, not a list
        if isinstance(fg, dict):
            data_list = fg.get("data_list", [])
            if data_list and isinstance(data_list, list) and len(data_list) > 0:
                inputs.fear_greed = int(float(data_list[-1]))
                inputs.fear_greed_label = self._classify_fear_greed(inputs.fear_greed)
                inputs.sources["fear_greed"] = "CoinGlass v4 F&G"
        elif isinstance(fg, list) and len(fg) > 0:
            # Fallback if wrapped in list
            first = fg[0] if isinstance(fg[0], dict) else {}
            data_list = first.get("data_list", [])
            if data_list:
                inputs.fear_greed = int(float(data_list[-1]))
                inputs.fear_greed_label = self._classify_fear_greed(inputs.fear_greed)
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
        if isinstance(dom, list) and len(dom) > 0:
            entry = dom[-1]
            if isinstance(entry, dict):
                inputs.btc_dominance = float(entry.get("bitcoin_dominance", 0))
                inputs.sources["dominance"] = "CoinGlass v4"
                # Derive ETH price from market data if available
                if inputs.btc_price > 0:
                    mkt_cap = float(entry.get("market_cap", 0))
                    if mkt_cap > 0:
                        inputs.btc_market_cap = mkt_cap

    # ── Parse: Coinbase Premium ────────────────────────────────────
    # Live response: [{"time":...,"premium":-13.72,"premium_rate":-0.0195}]

    def _parse_premium(self, inputs, prem):
        if not prem or isinstance(prem, Exception):
            return
        if isinstance(prem, list) and len(prem) > 0:
            entry = prem[-1]
            if isinstance(entry, dict):
                inputs.coinbase_premium = float(entry.get("premium_rate", 0))
                inputs.sources["cb_premium"] = "CoinGlass v4"

    # ── Parse: Global M2 ──────────────────────────────────────────
    # Live response: [{"timestamp":...,"price":...,"global_m2_yoy_growth":5.56,"global_m2_supply":...}, ...]

    def _parse_m2(self, inputs, m2):
        if not m2 or isinstance(m2, Exception):
            return
        if isinstance(m2, list) and len(m2) > 0:
            entry = m2[-1]
            if isinstance(entry, dict):
                inputs.global_m2_growth = float(entry.get("global_m2_yoy_growth", 0))
                inputs.sources["global_m2"] = "CoinGlass v4 M2"

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
            return_exceptions=True,
        )

        hy, yc, claims, anfci, fed, rrp, tga = results

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


# Singleton instance
data_service = DataServiceV76()
