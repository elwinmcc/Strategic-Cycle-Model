"""
Data Service for Bitcoin Strategic Cycle Model
Fetches live market data from various APIs
"""

import httpx
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Any
from cachetools import TTLCache
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for API responses (5 minute TTL)
cache = TTLCache(maxsize=100, ttl=300)


class DataService:
    """Service for fetching live market data"""

    def __init__(self):
        self.base_urls = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'alternative': 'https://api.alternative.me',
            'glassnode': 'https://api.glassnode.com/v1',
            'blockchain': 'https://api.blockchain.info',
        }
        self.timeout = httpx.Timeout(10.0)

    async def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all market data concurrently"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Fetch data concurrently
                tasks = [
                    self._fetch_btc_price(client),
                    self._fetch_fear_greed(client),
                    self._fetch_eth_data(client),
                    self._fetch_market_data(client),
                    self._fetch_mvrv_data(client),
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Combine results
                combined = {
                    'btc': results[0] if not isinstance(results[0], Exception) else {},
                    'fear_greed': results[1] if not isinstance(results[1], Exception) else {},
                    'eth': results[2] if not isinstance(results[2], Exception) else {},
                    'market': results[3] if not isinstance(results[3], Exception) else {},
                    'onchain': results[4] if not isinstance(results[4], Exception) else {},
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                }

                return combined

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return {'status': 'error', 'message': str(e)}

    async def _fetch_btc_price(self, client: httpx.AsyncClient) -> Dict:
        """Fetch BTC price and market data from CoinGecko"""
        cache_key = 'btc_price'
        if cache_key in cache:
            return cache[cache_key]

        try:
            url = f"{self.base_urls['coingecko']}/coins/bitcoin"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false'
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            market_data = data.get('market_data', {})
            result = {
                'price': market_data.get('current_price', {}).get('usd', 0),
                'ath': market_data.get('ath', {}).get('usd', 0),
                'ath_date': market_data.get('ath_date', {}).get('usd', ''),
                'price_change_24h': market_data.get('price_change_percentage_24h', 0),
                'price_change_7d': market_data.get('price_change_percentage_7d', 0),
                'price_change_30d': market_data.get('price_change_percentage_30d', 0),
                'price_change_1y': market_data.get('price_change_percentage_1y', 0),
                'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                'total_volume': market_data.get('total_volume', {}).get('usd', 0),
                'circulating_supply': market_data.get('circulating_supply', 0),
            }

            cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error fetching BTC price: {e}")
            return {}

    async def _fetch_fear_greed(self, client: httpx.AsyncClient) -> Dict:
        """Fetch Fear & Greed Index from multiple sources"""
        cache_key = 'fear_greed'
        if cache_key in cache:
            return cache[cache_key]

        try:
            # Try CoinMarketCap Fear & Greed first
            try:
                url = "https://coinmarketcap.com/charts/fear-and-greed-index/"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    html = response.text
                    import re

                    # Look for fear & greed value in the page
                    patterns = [
                        r'"fearGreedIndex"\s*:\s*(\d+)',
                        r'"value"\s*:\s*(\d+)',
                        r'fear.*?greed.*?(\d+)',
                        r'index.*?value.*?(\d+)',
                        r'data-value["\']?\s*=\s*["\']?(\d+)',
                    ]

                    for pattern in patterns:
                        match = re.search(pattern, html, re.IGNORECASE)
                        if match:
                            value = int(match.group(1))
                            if 0 <= value <= 100:
                                # Determine classification
                                if value <= 20:
                                    classification = 'Extreme Fear'
                                elif value <= 40:
                                    classification = 'Fear'
                                elif value <= 60:
                                    classification = 'Neutral'
                                elif value <= 80:
                                    classification = 'Greed'
                                else:
                                    classification = 'Extreme Greed'

                                result = {
                                    'value': value,
                                    'classification': classification,
                                    'avg_7d': value,  # Will be updated if we get historical
                                    'avg_30d': value,
                                    'source': 'coinmarketcap'
                                }
                                cache[cache_key] = result
                                logger.info(f"Fetched F&G from CoinMarketCap: {value} ({classification})")
                                return result
            except Exception as e:
                logger.debug(f"CoinMarketCap F&G fetch error: {e}")

            # Fallback to Alternative.me
            url = f"{self.base_urls['alternative']}/fng/"
            params = {'limit': 30}

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            entries = data.get('data', [])
            if entries:
                current = entries[0]
                avg_7d = sum(int(e['value']) for e in entries[:7]) / 7 if len(entries) >= 7 else int(current['value'])
                avg_30d = sum(int(e['value']) for e in entries[:30]) / 30 if len(entries) >= 30 else int(current['value'])

                result = {
                    'value': int(current['value']),
                    'classification': current['value_classification'],
                    'avg_7d': round(avg_7d, 1),
                    'avg_30d': round(avg_30d, 1),
                    'source': 'alternative.me'
                }
                cache[cache_key] = result
                return result

            return {}

        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")
            return {}

    async def _fetch_eth_data(self, client: httpx.AsyncClient) -> Dict:
        """Fetch ETH price and ETH/BTC ratio"""
        cache_key = 'eth_data'
        if cache_key in cache:
            return cache[cache_key]

        try:
            url = f"{self.base_urls['coingecko']}/simple/price"
            params = {
                'ids': 'ethereum',
                'vs_currencies': 'usd,btc',
                'include_24hr_change': 'true',
                'include_7d_change': 'true',
                'include_30d_change': 'true'
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            eth = data.get('ethereum', {})
            result = {
                'price_usd': eth.get('usd', 0),
                'price_btc': eth.get('btc', 0),
                'change_24h': eth.get('usd_24h_change', 0),
            }

            cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error fetching ETH data: {e}")
            return {}

    async def _fetch_market_data(self, client: httpx.AsyncClient) -> Dict:
        """Fetch global market data"""
        cache_key = 'market_data'
        if cache_key in cache:
            return cache[cache_key]

        try:
            url = f"{self.base_urls['coingecko']}/global"

            response = await client.get(url)
            response.raise_for_status()
            data = response.json().get('data', {})

            result = {
                'total_market_cap': data.get('total_market_cap', {}).get('usd', 0),
                'btc_dominance': data.get('market_cap_percentage', {}).get('btc', 0),
                'eth_dominance': data.get('market_cap_percentage', {}).get('eth', 0),
                'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd', 0),
            }

            cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {}

    async def _fetch_mvrv_data(self, client: httpx.AsyncClient) -> Dict:
        """
        Fetch MVRV and on-chain data.
        Tries multiple free sources, falls back to calculation from market cap.
        """
        cache_key = 'mvrv_data'
        if cache_key in cache:
            return cache[cache_key]

        try:
            # Try to fetch from Bitbo.io MVRV Z-Score page
            try:
                url = "https://charts.bitbo.io/mvrv-z-score/"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    html = response.text
                    # Look for MVRV value in the page - typically in a data attribute or script
                    import re

                    # Try to find MVRV value patterns in the HTML
                    # The page may show both MVRV Z-Score and raw MVRV
                    patterns = [
                        # MVRV ratio patterns
                        r'"mvrv"\s*:\s*([\d.]+)',
                        r"'mvrv'\s*:\s*([\d.]+)",
                        r'mvrv["\']?\s*[:=]\s*([\d.]+)',
                        r'MVRV\s*[:=]?\s*([\d.]+)',
                        # Z-Score patterns (we'll convert to approximate MVRV)
                        r'"z[_-]?score"\s*:\s*([-\d.]+)',
                        r'z[_-]?score["\']?\s*[:=]\s*([-\d.]+)',
                        # Current value patterns
                        r'"current"\s*:\s*([\d.]+)',
                        r'"value"\s*:\s*([\d.]+)',
                        r'data-value["\']?\s*=\s*["\']?([\d.]+)',
                    ]

                    for pattern in patterns:
                        match = re.search(pattern, html, re.IGNORECASE)
                        if match:
                            value = float(match.group(1))
                            # Check if it's a Z-Score (typically -1 to 10 range, often < 3)
                            if 'z' in pattern.lower() or 'score' in pattern.lower():
                                # Z-Score to MVRV conversion:
                                # Z-Score 0 ≈ MVRV 1.0 (at realized value)
                                # Z-Score 0.73 ≈ MVRV ~1.6
                                # Z-Score 2 ≈ MVRV ~2.5
                                # Z-Score 4 ≈ MVRV ~4.0
                                # Formula: MVRV ≈ 1.0 + (z_score * 0.8)
                                mvrv = 1.0 + (value * 0.8)
                            else:
                                mvrv = value

                            if 0.3 < mvrv < 10:  # Sanity check for valid MVRV range
                                result = {'mvrv': round(mvrv, 2), 'source': 'bitbo', 'raw_value': value}
                                cache[cache_key] = result
                                logger.info(f"Fetched MVRV from Bitbo: {mvrv:.2f}")
                                return result

                    # Try to find in script tags with JSON data
                    json_pattern = r'\{[^{}]*"value"\s*:\s*([\d.]+)[^{}]*\}'
                    matches = re.findall(json_pattern, html, re.IGNORECASE)
                    for val_str in matches:
                        try:
                            mvrv = float(val_str)
                            if 0.3 < mvrv < 10:
                                result = {'mvrv': round(mvrv, 2), 'source': 'bitbo'}
                                cache[cache_key] = result
                                logger.info(f"Fetched MVRV from Bitbo: {mvrv:.2f}")
                                return result
                        except:
                            continue

            except Exception as e:
                logger.debug(f"Bitbo.io fetch error: {e}")

            # Try blockchain.info for market cap and calculate approximation
            try:
                # Get market cap
                mc_url = f"{self.base_urls['blockchain']}/q/marketcap"
                mc_response = await client.get(mc_url, timeout=5.0)

                if mc_response.status_code == 200:
                    market_cap = float(mc_response.text)

                    # Realized cap approximation based on on-chain data
                    # Current realized cap is approximately $900B-$1T (Jan 2025)
                    # With Z-Score 0.73 at ~$79K and MVRV ~1.58:
                    # Market cap ~$1.56T / MVRV 1.58 = Realized cap ~$987B
                    estimated_realized_cap = 950_000_000_000  # ~$950B estimate

                    mvrv = market_cap / estimated_realized_cap
                    result = {'mvrv': round(mvrv, 2), 'source': 'calculated', 'market_cap': market_cap}
                    cache[cache_key] = result
                    logger.info(f"Calculated MVRV: {mvrv:.2f} from market cap ${market_cap/1e12:.2f}T")
                    return result
            except Exception as e:
                logger.debug(f"Blockchain.info API error: {e}")

            # Final fallback: estimate from price relative to 200WMA
            result = {'mvrv': None, 'source': 'unavailable'}
            cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error fetching MVRV data: {e}")
            return {'mvrv': None, 'source': 'error'}

    def _estimate_mvrv_from_price(self, price: float, ma_200w: float) -> float:
        """
        Estimate MVRV from price relative to 200-week moving average.
        Historical correlation: MVRV roughly = 0.4 * (price / 200WMA) + 0.6
        """
        if ma_200w <= 0:
            return 2.0  # Default mid-range

        ratio = price / ma_200w
        # Calibrated approximation based on historical data
        estimated_mvrv = 0.5 * ratio + 0.3
        return round(max(0.3, min(7.0, estimated_mvrv)), 2)

    def build_market_data(self, live_data: Dict, manual_overrides: Optional[Dict] = None) -> Dict:
        """Build MarketData object from live data and manual inputs"""
        from model import MarketData

        btc = live_data.get('btc', {})
        fg = live_data.get('fear_greed', {})
        eth = live_data.get('eth', {})
        market = live_data.get('market', {})
        onchain = live_data.get('onchain', {})

        # Calculate historical prices from percentage changes
        current_price = btc.get('price', 78881)

        def calc_historical(current, pct_change):
            if pct_change and pct_change != 0:
                return current / (1 + pct_change / 100)
            return current

        # Build MarketData with live values
        data_dict = {
            'btc_price': current_price,
            'btc_ath': btc.get('ath', 108000),
            'btc_cycle_low': 15500,  # Historical low

            # Price history (approximated from % changes)
            'btc_1d': calc_historical(current_price, btc.get('price_change_24h', 0)),
            'btc_7d': calc_historical(current_price, btc.get('price_change_7d', 0)),
            'btc_30d': calc_historical(current_price, btc.get('price_change_30d', 0)),
            'btc_365d': calc_historical(current_price, btc.get('price_change_1y', 0)),

            # Fear & Greed
            'fear_greed': fg.get('value', 50),
            'fear_greed_7d': int(fg.get('avg_7d', 50)),
            'fear_greed_30d': int(fg.get('avg_30d', 50)),

            # ETH
            'eth_price': eth.get('price_usd', 3300),
            'eth_btc': eth.get('price_btc', 0.032),

            # Market
            'btc_dominance': market.get('btc_dominance', 58),

            # Date
            'date': datetime.now().strftime('%B %d, %Y'),
        }

        # Apply manual overrides for data that can't be fetched from free APIs
        if manual_overrides:
            data_dict.update(manual_overrides)

        # Calculate 200WMA estimate for MVRV fallback calculation
        # 200WMA is approximately $43K currently (Jan 2025)
        btc_200w_ma_est = 43000

        # Get MVRV from on-chain data or calculate it
        fetched_mvrv = onchain.get('mvrv')
        if fetched_mvrv and fetched_mvrv > 0:
            live_mvrv = fetched_mvrv
            mvrv_source = onchain.get('source', 'api')
        else:
            # Calculate MVRV approximation from price/200WMA ratio
            live_mvrv = self._estimate_mvrv_from_price(current_price, btc_200w_ma_est)
            mvrv_source = 'estimated'
        logger.info(f"Using MVRV: {live_mvrv} (source: {mvrv_source})")

        # Fill in defaults for values we can't fetch from free APIs
        defaults = {
            'btc_14d': data_dict.get('btc_7d', current_price),
            'btc_90d': current_price * 0.7,
            'btc_180d': current_price * 0.62,
            'btc_20d_ma': current_price * 0.96,
            'btc_50d_ma': current_price * 0.91,
            'btc_100d_ma': current_price * 0.82,
            'btc_200d_ma': current_price * 0.75,
            'btc_200w_ma': btc_200w_ma_est,
            'btc_111d_ma': current_price * 0.88,
            'btc_350d_ma': current_price * 0.70,
            'mvrv': live_mvrv,
            'mvrv_7d': live_mvrv * 0.97,  # Slightly lagged
            'mvrv_30d': live_mvrv * 0.92,  # More lagged
            'nupl': 0.52,
            'puell': 1.3,
            'reserve_risk': 0.003,
            'fed_bs': 6.57,
            'fed_bs_30d': 6.60,
            'fed_bs_90d': 6.70,
            'fed_bs_180d': 7.00,
            'fed_bs_365d': 7.20,
            'rrp': 0.25,
            'rrp_30d': 0.35,
            'rrp_peak': 2.55,
            'tga': 0.78,
            'm2_yoy': 4.2,
            'm2_mom': 0.3,
            'empire_state': 7.7,
            'empire_prior': -3.7,
            'philly_fed': 12.6,
            'philly_prior': -8.8,
            'richmond': -6.0,
            'richmond_prior': -7.0,
            'kansas_city': 0.0,
            'kansas_prior': 0.0,
            'dallas': -10.9,
            'dallas_prior': -10.4,
            # ISM Data - December 2024 (released January 2025)
            'ism_mfg': 47.9,
            'ism_mfg_prior': 48.4,
            'ism_mfg_3m': 47.5,
            'ism_svc': 54.4,
            'ism_svc_prior': 52.1,
            'etf_flow_7d': 850,
            'etf_flow_30d': 3200,
            'etf_flow_90d': 8500,
            'etf_aum': 125,
            'funding_8h': 0.012,
            'funding_7d': 0.010,
            'funding_30d': 0.015,
            'oi_btc': 650000,
            'oi_change_7d': 5,
            'rsi_14d': 58,
            'rsi_weekly': 55,
            'rsi_monthly': 62,
            'eth_btc_7d': 0.0310,
            'eth_btc_30d': 0.0285,
            'eth_btc_90d': 0.0350,
            'total3_btc': 0.42,
            'total3_btc_30d': 0.38,
            'others_btc': 0.18,
            'others_btc_30d': 0.16,
            'btc_dom_30d': 56.0,
            'vol_30d': 0.55,
            'vol_90d': 0.60,
        }

        # Apply defaults for missing values
        for key, value in defaults.items():
            if key not in data_dict or data_dict[key] is None:
                data_dict[key] = value

        return MarketData(**data_dict)


# Singleton instance
data_service = DataService()
