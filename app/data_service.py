"""
Data Service for BTC Econometric Model v7.6
Primary: CoinGlass API v4 (Startup plan)
Secondary: FRED API (macro/credit/cycle)
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

COINGLASS_BASE = "https://open-api-v3.coinglass.com/api"
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


class CoinGlassClient:
    """Async client for CoinGlass API v4 (Startup plan)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = COINGLASS_BASE
        self.headers = {
            "accept": "application/json",
            "CG-API-KEY": api_key,
            "coinglassSecret": api_key,
        }

    async def _get(self, client: httpx.AsyncClient, endpoint: str, params: dict = None) -> Any:
        """Make authenticated GET request."""
        url = f"{self.base}/{endpoint}"
        try:
            resp = await client.get(url, headers=self.headers, params=params or {}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == "0" or data.get("success"):
                return data.get("data", data)
            else:
                logger.warning(f"CoinGlass warning on {endpoint}: {data.get('msg', 'unknown')}")
                return data.get("data", {})
        except Exception as e:
            logger.error(f"CoinGlass error on {endpoint}: {e}")
            return {}

    # Price & Market
    async def get_coins_markets(self, client, symbol="BTC"):
        return await self._get(client, "futures/coins-markets", {"symbol": symbol})

    async def get_price_ohlc(self, client, symbol="BTC", interval="1d", limit=30):
        return await self._get(client, "futures/price-ohlc-history", {"symbol": symbol, "interval": interval, "limit": limit})

    # Funding
    async def get_funding_rate_exchange_list(self, client, symbol="BTC"):
        return await self._get(client, "futures/funding-rate/exchange-list", {"symbol": symbol})

    # OI
    async def get_oi_aggregated(self, client, symbol="BTC", interval="1d", limit=30):
        return await self._get(client, "futures/open-interest/ohlc-aggregated-history", {"symbol": symbol, "interval": interval, "limit": limit})

    # Liquidations
    async def get_liquidation_history(self, client, symbol="BTC", interval="1d", limit=1):
        return await self._get(client, "futures/liquidation/aggregated-history", {"symbol": symbol, "interval": interval, "limit": limit})

    # Long/Short
    async def get_long_short_ratio(self, client, symbol="BTC"):
        return await self._get(client, "futures/long-short-ratio/global-account-ratio", {"symbol": symbol, "interval": "h4", "limit": 1})

    # ETF
    async def get_btc_etf_flows(self, client, limit=10):
        return await self._get(client, "etf/bitcoin/etf-flows-history", {"limit": limit})

    async def get_btc_etf_list(self, client):
        return await self._get(client, "etf/bitcoin/etf-list")

    # Options
    async def get_options_info(self, client, symbol="BTC"):
        return await self._get(client, "options/info", {"symbol": symbol})

    async def get_options_max_pain(self, client, symbol="BTC"):
        return await self._get(client, "options/max-pain", {"symbol": symbol})

    # On-Chain
    async def get_fear_greed(self, client, limit=3):
        return await self._get(client, "index/fear-greed-history", {"limit": limit})

    async def get_coinbase_premium(self, client):
        return await self._get(client, "indicator/coinbase-premium", {})

    async def get_bitcoin_dominance(self, client, limit=3):
        return await self._get(client, "indicator/bitcoin-dominance", {"limit": limit})

    async def get_sth_realized_price(self, client):
        return await self._get(client, "indicator/bitcoin-short-term-holder-realized-price", {"limit": 7})

    async def get_lth_realized_price(self, client):
        return await self._get(client, "indicator/bitcoin-long-term-holder-realized-price", {"limit": 7})

    async def get_nupl(self, client):
        return await self._get(client, "indicator/bitcoin-net-unrealized-pnl", {"limit": 7})

    async def get_futures_basis(self, client, symbol="BTC"):
        return await self._get(client, "indicator/basis", {"symbol": symbol})

    async def get_global_m2(self, client, limit=7):
        return await self._get(client, "indicator/bitcoin-vs-global-m2-supply-growth", {"limit": limit})


class FREDClient:
    """Async client for FRED API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = FRED_BASE

    async def get_latest(self, client: httpx.AsyncClient, series_id: str, lookback_days: int = 30) -> Optional[float]:
        """Get the most recent observation for a FRED series."""
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
            resp.raise_for_status()
            data = resp.json()
            for o in data.get("observations", []):
                val = o.get("value", ".")
                if val != ".":
                    return float(val)
            return None
        except Exception as e:
            logger.error(f"FRED error on {series_id}: {e}")
            return None


class DataServiceV76:
    """Data service for BTC Model v7.6 — CoinGlass + FRED."""

    def __init__(self):
        self.cg = CoinGlassClient(COINGLASS_API_KEY)
        self.fred = FREDClient(FRED_API_KEY)
        self.timeout = httpx.Timeout(20.0)

    async def collect_all_data(self) -> ModelInputs:
        """Fetch all model inputs from CoinGlass + FRED APIs."""
        cache_key = "model_inputs_v76"
        if cache_key in cache:
            return cache[cache_key]

        inputs = ModelInputs()
        inputs.timestamp = datetime.now().isoformat()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Run CoinGlass and FRED fetches concurrently
            await asyncio.gather(
                self._fetch_coinglass_data(client, inputs),
                self._fetch_fred_data(client, inputs),
                return_exceptions=True,
            )

        cache[cache_key] = inputs
        return inputs

    async def _fetch_coinglass_data(self, client: httpx.AsyncClient, inputs: ModelInputs):
        """Fetch all CoinGlass data concurrently."""
        logger.info("Fetching CoinGlass data...")

        # Fire all CoinGlass requests concurrently
        results = await asyncio.gather(
            self.cg.get_coins_markets(client, "BTC"),
            self.cg.get_funding_rate_exchange_list(client, "BTC"),
            self.cg.get_liquidation_history(client, "BTC", "1d", 1),
            self.cg.get_long_short_ratio(client, "BTC"),
            self.cg.get_btc_etf_flows(client, 10),
            self.cg.get_btc_etf_list(client),
            self.cg.get_options_info(client, "BTC"),
            self.cg.get_options_max_pain(client, "BTC"),
            self.cg.get_sth_realized_price(client),
            self.cg.get_lth_realized_price(client),
            self.cg.get_nupl(client),
            self.cg.get_fear_greed(client, 3),
            self.cg.get_bitcoin_dominance(client, 3),
            self.cg.get_coinbase_premium(client),
            self.cg.get_futures_basis(client, "BTC"),
            self.cg.get_global_m2(client, 7),
            self.cg.get_price_ohlc(client, "BTC", "1d", 35),
            self.cg.get_coins_markets(client, "ETH"),
            return_exceptions=True,
        )

        (markets, fr_data, liq_data, ls_data, etf_flows, etf_list,
         opt_info, max_pain, sth, lth, nupl_data, fg, dom, prem,
         basis, m2, ohlc, eth_markets) = results

        # -- Parse BTC Price & Market --
        self._parse_markets(inputs, markets)
        # -- Funding --
        self._parse_funding(inputs, fr_data)
        # -- Liquidations --
        self._parse_liquidations(inputs, liq_data)
        # -- Long/Short --
        self._parse_long_short(inputs, ls_data)
        # -- ETF Flows --
        self._parse_etf_flows(inputs, etf_flows)
        self._parse_etf_list(inputs, etf_list)
        # -- Options --
        self._parse_options(inputs, opt_info)
        self._parse_max_pain(inputs, max_pain)
        # -- On-Chain --
        self._parse_sth(inputs, sth)
        self._parse_lth(inputs, lth)
        self._compute_realized_mvrv(inputs)
        self._parse_nupl(inputs, nupl_data)
        # -- Fear & Greed --
        self._parse_fear_greed(inputs, fg)
        # -- Dominance --
        self._parse_dominance(inputs, dom)
        # -- Coinbase Premium --
        self._parse_premium(inputs, prem)
        # -- Futures Basis --
        self._parse_basis(inputs, basis)
        # -- Global M2 --
        self._parse_m2(inputs, m2)
        # -- Price History --
        self._parse_ohlc(inputs, ohlc)
        # -- ETH --
        self._parse_eth(inputs, eth_markets)

    def _parse_markets(self, inputs, markets):
        if not markets or isinstance(markets, Exception):
            return
        if isinstance(markets, list) and len(markets) > 0:
            m = markets[0] if isinstance(markets[0], dict) else {}
        elif isinstance(markets, dict):
            m = markets
        else:
            return
        inputs.btc_price = float(m.get("price", m.get("lastPrice", 0)))
        inputs.btc_market_cap = float(m.get("marketCap", 0))
        inputs.oi_total = float(m.get("openInterest", m.get("oiUSD", 0)))
        inputs.oi_change_24h_pct = float(m.get("oiChange24h", m.get("oiChg24h", 0)))
        inputs.sources["btc_price"] = "CoinGlass Markets"
        if inputs.btc_price > 0:
            inputs.drawdown_pct = round((inputs.btc_price - inputs.btc_ath) / inputs.btc_ath * 100, 1)

    def _parse_funding(self, inputs, fr_data):
        if isinstance(fr_data, Exception):
            return
        if fr_data and isinstance(fr_data, list):
            rates = [float(x.get("rate", x.get("fundingRate", 0))) for x in fr_data if x.get("rate") or x.get("fundingRate")]
            if rates:
                inputs.funding_rate = round(sum(rates) / len(rates), 6)
                inputs.sources["funding_rate"] = f"CoinGlass ({len(rates)} exchanges)"
        elif isinstance(fr_data, dict):
            inputs.funding_rate = float(fr_data.get("avgRate", fr_data.get("rate", 0)))
            inputs.sources["funding_rate"] = "CoinGlass Funding"

    def _parse_liquidations(self, inputs, liq_data):
        if isinstance(liq_data, Exception):
            return
        if liq_data and isinstance(liq_data, list) and len(liq_data) > 0:
            liq = liq_data[0] if isinstance(liq_data[0], dict) else {}
            inputs.liquidation_24h = float(liq.get("volUsd", liq.get("liquidationUsd", 0)))
            inputs.sources["liquidation"] = "CoinGlass"

    def _parse_long_short(self, inputs, ls_data):
        if isinstance(ls_data, Exception):
            return
        if ls_data:
            if isinstance(ls_data, list) and len(ls_data) > 0:
                ls = ls_data[-1] if isinstance(ls_data[-1], dict) else {}
                long_rate = float(ls.get("longRate", 0.5))
                short_rate = max(float(ls.get("shortRate", 0.5)), 0.01)
                inputs.long_short_ratio = long_rate / short_rate
            elif isinstance(ls_data, dict):
                inputs.long_short_ratio = float(ls_data.get("longShortRatio", ls_data.get("ratio", 1.0)))
            inputs.sources["long_short"] = "CoinGlass L/S"

    def _parse_etf_flows(self, inputs, etf_flows):
        if isinstance(etf_flows, Exception):
            return
        if etf_flows and isinstance(etf_flows, list):
            daily_flows = []
            for entry in etf_flows[:10]:
                if isinstance(entry, dict):
                    flow = float(entry.get("totalNetFlow", entry.get("netFlow", entry.get("totalFlow", 0))))
                    daily_flows.append(flow)
            if daily_flows:
                inputs.etf_flow_daily = daily_flows[0]
                inputs.etf_flow_weekly = sum(daily_flows[:5])
                inputs.sources["etf_flows"] = f"CoinGlass ETF ({len(daily_flows)} days)"

    def _parse_etf_list(self, inputs, etf_list):
        if isinstance(etf_list, Exception):
            return
        if etf_list and isinstance(etf_list, list):
            inputs.etf_cumulative = sum(
                float(e.get("totalNetFlow", e.get("cumulativeFlow", 0)))
                for e in etf_list if isinstance(e, dict)
            )
        elif isinstance(etf_list, dict):
            inputs.etf_cumulative = float(etf_list.get("totalNetFlow", 0))

    def _parse_options(self, inputs, opt_info):
        if isinstance(opt_info, Exception):
            return
        if opt_info:
            if isinstance(opt_info, dict):
                inputs.put_call_ratio = float(opt_info.get("putCallRatio", opt_info.get("pcRatio", 0)))
                inputs.options_oi = float(opt_info.get("openInterest", opt_info.get("totalOI", 0)))
                inputs.sources["options"] = "CoinGlass Options"
            elif isinstance(opt_info, list) and len(opt_info) > 0:
                inputs.put_call_ratio = float(opt_info[0].get("putCallRatio", 0))

    def _parse_max_pain(self, inputs, max_pain):
        if isinstance(max_pain, Exception):
            return
        if max_pain:
            if isinstance(max_pain, dict):
                inputs.max_pain = float(max_pain.get("maxPain", max_pain.get("price", 0)))
            elif isinstance(max_pain, list) and len(max_pain) > 0:
                inputs.max_pain = float(max_pain[0].get("maxPain", max_pain[0].get("strikePrice", 0)))
            inputs.sources["max_pain"] = "CoinGlass Max Pain"

    def _parse_sth(self, inputs, sth):
        if isinstance(sth, Exception):
            return
        if sth and isinstance(sth, list) and len(sth) > 0:
            entry = sth[-1] if isinstance(sth[-1], dict) else sth[0]
            inputs.sth_realized_price = float(entry.get("price", entry.get("value", 0)))
            inputs.sources["sth_price"] = "CoinGlass STH RP"

    def _parse_lth(self, inputs, lth):
        if isinstance(lth, Exception):
            return
        if lth and isinstance(lth, list) and len(lth) > 0:
            entry = lth[-1] if isinstance(lth[-1], dict) else lth[0]
            inputs.lth_realized_price = float(entry.get("price", entry.get("value", 0)))
            inputs.sources["lth_price"] = "CoinGlass LTH RP"

    def _compute_realized_mvrv(self, inputs):
        if inputs.sth_realized_price > 0 and inputs.lth_realized_price > 0:
            inputs.realized_price = (inputs.sth_realized_price * 0.4 + inputs.lth_realized_price * 0.6)
        elif inputs.sth_realized_price > 0:
            inputs.realized_price = inputs.sth_realized_price

        if inputs.realized_price > 0 and inputs.btc_price > 0:
            inputs.mvrv = round(inputs.btc_price / inputs.realized_price, 3)
            inputs.sources["mvrv"] = "Calculated (Price / Realized Price)"
        else:
            inputs.warnings.append("MVRV: Could not calculate - missing realized price data")

    def _parse_nupl(self, inputs, nupl_data):
        if isinstance(nupl_data, Exception):
            return
        if nupl_data and isinstance(nupl_data, list) and len(nupl_data) > 0:
            entry = nupl_data[-1] if isinstance(nupl_data[-1], dict) else nupl_data[0]
            inputs.nupl = float(entry.get("nupl", entry.get("value", 0)))
            inputs.sources["nupl"] = "CoinGlass NUPL"

    def _parse_fear_greed(self, inputs, fg):
        if isinstance(fg, Exception):
            return
        if fg and isinstance(fg, list) and len(fg) > 0:
            entry = fg[0] if isinstance(fg[0], dict) else {}
            inputs.fear_greed = int(float(entry.get("value", entry.get("score", 50))))
            inputs.fear_greed_label = entry.get("valueClassification", entry.get("label", ""))
            inputs.sources["fear_greed"] = "CoinGlass F&G"
        elif isinstance(fg, dict):
            inputs.fear_greed = int(float(fg.get("value", fg.get("score", 50))))

    def _parse_dominance(self, inputs, dom):
        if isinstance(dom, Exception):
            return
        if dom and isinstance(dom, list) and len(dom) > 0:
            entry = dom[-1] if isinstance(dom[-1], dict) else dom[0]
            inputs.btc_dominance = float(entry.get("dominance", entry.get("value", 0)))
            inputs.sources["dominance"] = "CoinGlass"

    def _parse_premium(self, inputs, prem):
        if isinstance(prem, Exception):
            return
        if prem:
            if isinstance(prem, dict):
                inputs.coinbase_premium = float(prem.get("premium", prem.get("value", 0)))
            elif isinstance(prem, list) and len(prem) > 0:
                inputs.coinbase_premium = float(prem[-1].get("premium", 0))
            inputs.sources["cb_premium"] = "CoinGlass"

    def _parse_basis(self, inputs, basis):
        if isinstance(basis, Exception):
            return
        if basis:
            if isinstance(basis, dict):
                inputs.futures_basis = float(basis.get("basis", basis.get("annualizedBasis", 0)))
            elif isinstance(basis, list) and len(basis) > 0:
                inputs.futures_basis = float(basis[0].get("basis", 0))
            inputs.sources["basis"] = "CoinGlass Basis"

    def _parse_m2(self, inputs, m2):
        if isinstance(m2, Exception):
            return
        if m2 and isinstance(m2, list) and len(m2) > 0:
            entry = m2[-1] if isinstance(m2[-1], dict) else m2[0]
            inputs.global_m2_growth = float(entry.get("m2Growth", entry.get("growthRate", entry.get("value", 0))))
            inputs.sources["global_m2"] = "CoinGlass M2"

    def _parse_ohlc(self, inputs, ohlc):
        if isinstance(ohlc, Exception):
            return
        if ohlc and isinstance(ohlc, list) and len(ohlc) > 25:
            if isinstance(ohlc[0], dict):
                inputs.price_30d_ago = float(ohlc[-30].get("close", ohlc[-30].get("c", 0)))
                inputs.sources["price_history"] = "CoinGlass OHLC"

    def _parse_eth(self, inputs, eth_markets):
        if isinstance(eth_markets, Exception):
            return
        if eth_markets:
            if isinstance(eth_markets, list) and len(eth_markets) > 0:
                em = eth_markets[0] if isinstance(eth_markets[0], dict) else {}
            elif isinstance(eth_markets, dict):
                em = eth_markets
            else:
                return
            inputs.eth_price = float(em.get("price", em.get("lastPrice", 0)))
            if inputs.btc_price > 0 and inputs.eth_price > 0:
                inputs.eth_btc = round(inputs.eth_price / inputs.btc_price, 5)
            inputs.sources["eth_price"] = "CoinGlass Markets"

    async def _fetch_fred_data(self, client: httpx.AsyncClient, inputs: ModelInputs):
        """Fetch all FRED data concurrently."""
        if not FRED_API_KEY:
            logger.warning("FRED API key not set, skipping macro data")
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
            inputs.fed_bs = fed / 1000  # to billions
            inputs.sources["fed_bs"] = "FRED WALCL"

        if not isinstance(rrp, Exception) and rrp is not None:
            inputs.rrp = rrp / 1000
            inputs.sources["rrp"] = "FRED RRPONTSYD"

        if not isinstance(tga, Exception) and tga is not None:
            inputs.tga = tga / 1000
            inputs.sources["tga"] = "FRED WTREGEN"


# Singleton instance
data_service = DataServiceV76()
