"""
Data Service for BTC Econometric Model v7.6
Primary: CoinGlass API v4 (verified against live responses)
Secondary: FRED API (macro/credit/cycle)

BTC price: coins-markets (primary), on-chain STH/LTH (fallback)
Long/short ratio: global-long-short-account-ratio/history
Futures basis: futures/basis/history
RSI: futures/rsi/list
Put/call ratio: derived from option/max-pain OI (no dedicated endpoint)
MVRV: calculated from STH/LTH realized prices (not available via API)
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
    BTC price: coins-markets (primary), OI ratio / on-chain (fallbacks).
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

    # ── Futures OI Exchange List ────────────────────────────────────
    # Response: [{"exchange":"All","symbol":"BTC","open_interest_usd":46817313373,"open_interest_quantity":665799,...}]

    async def get_oi_exchange_list(self, client, symbol="BTC"):
        return await self._get(client, "futures/open-interest/exchange-list", {"symbol": symbol})

    # ── OI Aggregated OHLC History (for 24h change calculation) ───
    # Response: [{"t":...,"o":46000000000,"h":47000000000,"l":45000000000,"c":46500000000}]

    async def get_oi_ohlc_history(self, client, symbol="BTC"):
        return await self._get(client, "futures/openInterest/ohlc-aggregated-history", {
            "symbol": symbol, "interval": "1d", "limit": 2,
        })

    # ── Funding Rates ───────────────────────────────────────────────
    # Response: {"data": [{"symbol":"BTC", "stablecoin_margin_list":[{"exchange":"Binance","funding_rate":0.001,...},...]}]}

    async def get_funding_rates(self, client, symbol="BTC"):
        return await self._get(client, "futures/fundingRate/exchange-list", {"symbol": symbol})

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
        return await self._get(client, "bitcoin/etf/flow-history", {"limit": limit})

    async def get_etf_list(self, client):
        return await self._get(client, "bitcoin/etf/list")

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
        return await self._get(client, "indicator/bitcoin-short-term-holder-realized-price")

    async def get_lth_realized(self, client):
        return await self._get(client, "indicator/bitcoin-long-term-holder-realized-price")

    async def get_nupl(self, client):
        return await self._get(client, "indicator/bitcoin-net-unrealized-pnl")

    # ── Fear & Greed ────────────────────────────────────────────────
    # Response: {"data_list":[30,15,40,...], "price_list":[...], "time_list":[...]}  (dict, not list!)

    async def get_fear_greed(self, client):
        return await self._get(client, "index/fear-greed-history")

    # ── Coinbase Premium ────────────────────────────────────────────
    # Response: [{"time":...,"premium":-13.72,"premium_rate":-0.0195}]

    async def get_coinbase_premium(self, client):
        return await self._get(client, "indicator/coinbase-premium")

    # ── Bitcoin Dominance ───────────────────────────────────────────
    # Response: [{"timestamp":...,"price":...,"bitcoin_dominance":94.35,"market_cap":...}]

    async def get_dominance(self, client):
        return await self._get(client, "indicator/bitcoin-dominance")

    # ── Global M2 ──────────────────────────────────────────────────
    # Response: [{"timestamp":...,"price":...,"global_m2_yoy_growth":5.56,"global_m2_supply":...}]

    async def get_global_m2(self, client):
        return await self._get(client, "indicator/bitcoin-vs-global-m2-supply-growth")

    # ── Coins Markets (proper BTC price) ────────────────────────────
    # Response: [{"symbol":"BTC","price":84500.12,"priceChangePercent24H":-1.2,...}]

    async def get_coins_markets(self, client, symbol="BTC"):
        return await self._get(client, "futures/coins-markets", {"symbol": symbol})

    # ── Long/Short Ratio ─────────────────────────────────────────────
    # Response: [{"time":...,"longRate":0.5123,"shortRate":0.4877,"longShortRatio":1.05}]

    async def get_long_short_ratio(self, client, symbol="BTC"):
        return await self._get(client, "futures/globalLongShortAccountRatio/history", {
            "symbol": symbol, "interval": "h4", "limit": 6,
        })

    # ── Futures Basis ────────────────────────────────────────────────
    # Response: [{"time":...,"openBasis":5.2,"closeBasis":5.1,"annualizedBasis":8.3,...}]

    async def get_futures_basis(self, client, symbol="BTC"):
        return await self._get(client, "indicator/basis", {"symbol": symbol})

    # ── RSI ──────────────────────────────────────────────────────────
    # Response: [{"symbol":"BTC","rsi_24h":55.3,...}]

    async def get_rsi(self, client, symbol="BTC"):
        return await self._get(client, "indicator/futures-rsi-list")


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
            self.cg.get_coins_markets(client),         # 0  ← proper BTC price
            self.cg.get_oi_exchange_list(client),      # 1  ← futures OI
            self.cg.get_funding_rates(client),         # 2
            self.cg.get_liquidations(client),          # 3
            self.cg.get_etf_flows(client, 10),         # 4
            self.cg.get_etf_list(client),              # 5
            self.cg.get_options_info(client),           # 6
            self.cg.get_options_max_pain(client),       # 7
            self.cg.get_sth_realized(client),           # 8
            self.cg.get_lth_realized(client),           # 9
            self.cg.get_nupl(client),                   # 10
            self.cg.get_fear_greed(client),             # 11
            self.cg.get_dominance(client),              # 12
            self.cg.get_coinbase_premium(client),       # 13
            self.cg.get_global_m2(client),              # 14
            self.cg.get_long_short_ratio(client),       # 15
            self.cg.get_futures_basis(client),          # 16
            self.cg.get_rsi(client),                    # 17
            self.cg.get_coins_markets(client, "ETH"),  # 18  ← ETH price
            self.cg.get_oi_ohlc_history(client),       # 19  ← OI OHLC for 24h change
            return_exceptions=True,
        )

        (coins_mkts, oi_exch, funding, liq, etf_flows, etf_list, opt_info,
         max_pain, sth, lth, nupl_data, fg, dom, prem, m2,
         ls_ratio, basis, rsi, eth_mkts, oi_ohlc) = results

        # Parse in order: coins-markets first (proper BTC price)
        self._parse_coins_markets(inputs, coins_mkts)
        self._parse_oi_exchange_list(inputs, oi_exch)
        self._parse_oi_ohlc(inputs, oi_ohlc)
        self._parse_etf_flows(inputs, etf_flows)
        self._parse_sth(inputs, sth)
        self._parse_lth(inputs, lth)
        self._compute_mvrv(inputs)
        self._parse_nupl(inputs, nupl_data)
        self._parse_funding(inputs, funding)
        self._parse_liquidations(inputs, liq)
        self._parse_long_short_ratio(inputs, ls_ratio)
        self._parse_futures_basis(inputs, basis)
        self._parse_rsi(inputs, rsi)
        self._parse_etf_list(inputs, etf_list)
        self._parse_options(inputs, opt_info)
        self._parse_max_pain(inputs, max_pain)
        self._parse_fear_greed(inputs, fg)
        self._parse_dominance(inputs, dom)
        self._parse_premium(inputs, prem)
        self._parse_m2(inputs, m2)
        self._parse_eth_markets(inputs, eth_mkts)

    # ── Parse: Coins Markets (primary BTC price) ───────────────────
    # Live response: [{"symbol":"BTC","price":84500.12,...}]

    def _parse_coins_markets(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        if isinstance(data, list):
            for row in data:
                if not isinstance(row, dict):
                    continue
                price = float(row.get("price", 0))
                if price > 0:
                    inputs.btc_price = round(price, 2)
                    inputs.sources["btc_price"] = "CoinGlass v4 coins-markets"
                    inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)
                    break
        elif isinstance(data, dict):
            price = float(data.get("price", 0))
            if price > 0:
                inputs.btc_price = round(price, 2)
                inputs.sources["btc_price"] = "CoinGlass v4 coins-markets"
                inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)

    # ── Parse: ETH Markets (ETH price + ETH/BTC) ───────────────────
    # Same endpoint as BTC coins-markets but with symbol=ETH

    def _parse_eth_markets(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        eth_price = 0.0
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    p = float(row.get("price", 0))
                    if p > 0:
                        eth_price = p
                        break
        elif isinstance(data, dict):
            eth_price = float(data.get("price", 0))
        if eth_price > 0:
            inputs.eth_price = round(eth_price, 2)
            inputs.sources["eth_price"] = "CoinGlass v4 coins-markets (ETH)"
            if inputs.btc_price > 0:
                inputs.eth_btc = round(eth_price / inputs.btc_price, 6)
                inputs.sources["eth_btc"] = "Calculated (ETH/BTC)"

    # ── Parse: Futures OI Exchange List ──────────────────────────────
    # Live response: [{"exchange":"All","symbol":"BTC","open_interest_usd":46817313373,"open_interest_quantity":665799,...}]
    # Provides OI data; BTC price fallback if coins-markets unavailable.

    def _parse_oi_exchange_list(self, inputs, oi_data):
        if not oi_data or isinstance(oi_data, Exception):
            return
        if not isinstance(oi_data, list):
            return
        for row in oi_data:
            if not isinstance(row, dict):
                continue
            if row.get("exchange") == "All":
                oi_usd = float(row.get("open_interest_usd", 0))
                oi_qty = float(row.get("open_interest_quantity", 0))
                # Fallback price from OI ratio if coins-markets didn't provide one
                if inputs.btc_price == 0 and oi_usd > 0 and oi_qty > 0:
                    price = oi_usd / oi_qty
                    inputs.btc_price = round(price, 2)
                    inputs.sources["btc_price"] = "CoinGlass v4 Futures OI (fallback)"
                    inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)
                # Store futures OI data
                inputs.oi_total = oi_usd
                # Try known field name variants for 24h OI change
                oi_chg = None
                for key in ("open_interest_change_percent_24h", "h24OiChangePercent",
                            "oiChangePercent24H", "oiChangePercent", "changePercent24H"):
                    if key in row and row[key] is not None:
                        oi_chg = float(row[key])
                        break
                if oi_chg is not None:
                    inputs.oi_change_24h_pct = oi_chg
                else:
                    # Log all keys so we can identify the correct field
                    logger.warning(f"OI change field not found. Available keys: {list(row.keys())}")
                inputs.sources["futures_oi"] = "CoinGlass v4 OI Exchange List"
                break

    # ── Parse: OI Aggregated OHLC History (24h change) ─────────────
    # Response: [{"t":...,"o":46000000000,"h":47000000000,"l":45000000000,"c":46500000000}]
    # We compute 24h change as (latest_close - prev_close) / prev_close * 100

    def _parse_oi_ohlc(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        if not isinstance(data, list) or len(data) < 2:
            if isinstance(data, list) and len(data) == 1:
                logger.warning("OI OHLC: only 1 entry, cannot compute 24h change")
            return
        # Get last two entries for daily change
        prev = data[-2] if isinstance(data[-2], dict) else None
        curr = data[-1] if isinstance(data[-1], dict) else None
        if not prev or not curr:
            return
        # Try known field names for close OI
        prev_oi = None
        curr_oi = None
        for key in ("c", "close", "closeOi", "close_oi", "openInterest"):
            if key in curr and curr[key] is not None:
                curr_oi = float(curr[key])
                prev_oi = float(prev.get(key, 0))
                break
        if curr_oi and prev_oi and prev_oi > 0:
            pct_change = (curr_oi - prev_oi) / prev_oi * 100
            inputs.oi_change_24h_pct = round(pct_change, 2)
            inputs.sources["oi_change"] = "CoinGlass v4 OI OHLC Aggregated"
        else:
            logger.warning(f"OI OHLC field not found. Keys: {list(curr.keys())}")

    # ── Parse: STH Realized Price ─────────────────────────────────
    # Live response: [{"timestamp":..., "price":71250, "sth_realized_price":85974}, ...]
    # NOTE: "price" field is on-chain derived — used as fallback only if ETF price unavailable.

    def _parse_sth(self, inputs, sth):
        if not sth or isinstance(sth, Exception):
            return
        if isinstance(sth, list) and len(sth) > 0:
            entry = sth[-1]
            if isinstance(entry, dict):
                sth_price = None
                for key in ("sth_realized_price", "sthRealizedPrice", "price", "value"):
                    if key in entry and entry[key] is not None and key != "price":
                        sth_price = float(entry[key])
                        break
                if sth_price and sth_price > 0:
                    inputs.sth_realized_price = sth_price
                    inputs.sources["sth_price"] = "CoinGlass v4 STH RP"
                else:
                    logger.warning(f"STH RP field not found. Available keys: {list(entry.keys())}")
                # Fallback: use on-chain price only if ETF price wasn't set
                if inputs.btc_price == 0:
                    price = float(entry.get("price", 0))
                    if price > 0:
                        inputs.btc_price = price
                        inputs.sources["btc_price"] = "CoinGlass v4 STH (on-chain fallback)"
                        inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)
                # 30d ago price for momentum
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
                # Also get BTC price from LTH if not yet set
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
                inputs.sources["liquidation"] = "CoinGlass v4"

    # ── Parse: Long/Short Ratio (proper endpoint) ──────────────────
    # Live response: [{"time":...,"longRate":0.5123,"shortRate":0.4877,"longShortRatio":1.05}]

    def _parse_long_short_ratio(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        if isinstance(data, list) and len(data) > 0:
            entry = data[-1] if isinstance(data[-1], dict) else data[0]
            if isinstance(entry, dict):
                # Try known field name variants
                ratio = None
                for key in ("longShortRatio", "long_short_ratio", "longShortAccountRatio"):
                    if key in entry and entry[key] is not None:
                        ratio = float(entry[key])
                        break
                if ratio is not None:
                    inputs.long_short_ratio = round(ratio, 2)
                    inputs.sources["long_short"] = "CoinGlass v4 Global L/S Ratio"
                else:
                    # Fallback: compute from longRate/shortRate
                    long_r = float(entry.get("longRate", entry.get("long_rate", 0)))
                    short_r = float(entry.get("shortRate", entry.get("short_rate", 0)))
                    if short_r > 0:
                        inputs.long_short_ratio = round(long_r / short_r, 2)
                        inputs.sources["long_short"] = "CoinGlass v4 Global L/S Ratio"
                    else:
                        logger.warning(f"L/S ratio field not found. Available keys: {list(entry.keys())}")

    # ── Parse: Futures Basis ─────────────────────────────────────────
    # Live response: [{"time":...,"openBasis":5.2,"closeBasis":5.1,"annualizedBasis":8.3,...}]

    def _parse_futures_basis(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        # Handle both list and dict responses
        entry = None
        if isinstance(data, list) and len(data) > 0:
            entry = data[-1] if isinstance(data[-1], dict) else data[0]
        elif isinstance(data, dict):
            entry = data
        if not isinstance(entry, dict):
            return
        # Try known field name variants for basis value
        basis = None
        for key in ("annualizedBasis", "closeBasis", "openBasis", "basis",
                     "annualized_basis", "close_basis", "basisRate", "basis_rate"):
            if key in entry and entry[key] is not None:
                basis = float(entry[key])
                break
        if basis is not None:
            inputs.futures_basis = round(basis, 2)
            inputs.sources["futures_basis"] = "CoinGlass v4 Futures Basis"
        else:
            logger.warning(f"Basis field not found. Available keys: {list(entry.keys())}")

    # ── Parse: RSI ───────────────────────────────────────────────────
    # Live response: [{"symbol":"BTC","rsi_24h":55.3,...}]

    def _parse_rsi(self, inputs, data):
        if not data or isinstance(data, Exception):
            return
        # Extract entry from list or dict
        entry = None
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    entry = row
                    break
        elif isinstance(data, dict):
            entry = data
        if not isinstance(entry, dict):
            return
        # Try known field name variants
        rsi = None
        for key in ("rsi_24h", "rsi24H", "rsi", "RSI", "rsi_1d", "rsiValue"):
            if key in entry and entry[key] is not None:
                rsi = float(entry[key])
                break
        if rsi is not None:
            inputs.rsi_daily = round(rsi, 1)
            inputs.sources["rsi"] = "CoinGlass v4 RSI"
        else:
            logger.warning(f"RSI field not found. Available keys: {list(entry.keys())}")

    # ── Parse: ETF Flows ───────────────────────────────────────────
    # Live response: [{"timestamp":..., "flow_usd":655300000, "price_usd":69887.4, "etf_flows":[...]}, ...]
    # price_usd is ETF close price — used as fallback if futures OI price unavailable.

    def _parse_etf_flows(self, inputs, etf_flows):
        if not etf_flows or isinstance(etf_flows, Exception):
            return
        if isinstance(etf_flows, list):
            sorted_flows = sorted(
                [e for e in etf_flows if isinstance(e, dict)],
                key=lambda x: x.get("timestamp", x.get("date", x.get("t", 0))),
                reverse=True,
            )
            # Fallback price from ETF if futures OI didn't provide one
            if inputs.btc_price == 0 and sorted_flows:
                price = float(sorted_flows[0].get("price_usd", sorted_flows[0].get("price", 0)))
                if price > 0:
                    inputs.btc_price = price
                    inputs.sources["btc_price"] = "CoinGlass v4 ETF (fallback)"
                    inputs.drawdown_pct = round((price - inputs.btc_ath) / inputs.btc_ath * 100, 1)
            # Compute flows — try known field names
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
    # Live response: [{"time":...,"premium":-13.72,"premium_rate":-0.0195}]

    def _parse_premium(self, inputs, prem):
        if not prem or isinstance(prem, Exception):
            return
        entry = None
        if isinstance(prem, list) and len(prem) > 0:
            entry = prem[-1] if isinstance(prem[-1], dict) else None
        elif isinstance(prem, dict):
            entry = prem
        if not isinstance(entry, dict):
            return
        premium = None
        for key in ("premium_rate", "premiumRate", "premium", "value"):
            if key in entry and entry[key] is not None:
                premium = float(entry[key])
                break
        if premium is not None:
            inputs.coinbase_premium = premium
            inputs.sources["cb_premium"] = "CoinGlass v4"
        else:
            logger.warning(f"Premium field not found. Available keys: {list(entry.keys())}")

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
