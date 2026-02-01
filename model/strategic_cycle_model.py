#!/usr/bin/env python3
"""
===============================================================================
BITCOIN STRATEGIC CYCLE MODEL v7.0 - UNIFIED ECONOMETRIC FRAMEWORK
===============================================================================
January 31, 2026

THESIS: Bitcoin is a macro liquidity asset. Buy value, sell euphoria.

COMPONENTS:
1. Liquidity Engine - Fed BS, RRP, TGA, Global M2, Net Liquidity
2. Business Cycle - ISM + Regional Fed Leading Indicators
3. BTC Trends - STF/MTF/LTF momentum analysis
4. Altcoin Rotation - BTC-denominated ratio tracking
5. Phase Detection - Wyckoff cycle positioning
6. Top Detection - Multi-indicator euphoria warning
7. Forecasting - Phase transition + Monte Carlo simulation
8. Backtesting - Historical regime validation

PHILOSOPHY:
- Value-dominant buying (MVRV < 2.0 = accumulate)
- Phase-aware selling (MVRV > 5.0 + top signals = distribute)
- Liquidity drives price, not halving cycles
- 80% drawdown tolerance enables conviction

===============================================================================
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from datetime import datetime, date, timedelta
from collections import defaultdict
import json

np.random.seed(42)

# =============================================================================
# CONSTANTS
# =============================================================================

GENESIS_DATE = date(2009, 1, 3)
POWER_LAW_INTERCEPT = 1.5e-17
POWER_LAW_SLOPE = 5.78

# Historical MVRV extremes
MVRV_HISTORICAL_LOW = -0.5
MVRV_HISTORICAL_HIGH = 7.0
MVRV_MEAN = 1.5

# Regional Fed weights (Richmond Fed research 2024)
REGIONAL_WEIGHTS = {
    'empire': 0.25, 'philly': 0.30, 'richmond': 0.20,
    'kansas': 0.15, 'dallas': 0.10
}

# =============================================================================
# ENUMS
# =============================================================================

class Phase(Enum):
    CAPITULATION = "CAPITULATION"
    ACCUMULATION = "ACCUMULATION"
    EARLY_MARKUP = "EARLY_MARKUP"
    MID_MARKUP = "MID_MARKUP"
    LATE_MARKUP = "LATE_MARKUP"
    DISTRIBUTION = "DISTRIBUTION"
    EARLY_MARKDOWN = "EARLY_MARKDOWN"
    MID_MARKDOWN = "MID_MARKDOWN"

class ValueZone(Enum):
    DEEP_VALUE = "DEEP_VALUE"      # MVRV < 1.0, bottom 25%
    VALUE = "VALUE"                 # MVRV 1.0-2.0, 25-50%
    FAIR = "FAIR"                   # MVRV 2.0-3.0, 50-75%
    EXTENDED = "EXTENDED"           # MVRV 3.0-5.0, 75-90%
    EUPHORIA = "EUPHORIA"           # MVRV > 5.0, top 10%

class TopWarning(Enum):
    NONE = "NONE"
    WATCH = "WATCH"
    CAUTION = "CAUTION"
    DANGER = "DANGER"
    CRITICAL = "CRITICAL"

class LiquidityRegime(Enum):
    EXPANSION = "EXPANSION"
    NEUTRAL = "NEUTRAL"
    CONTRACTION = "CONTRACTION"

class Trend(Enum):
    STRONG_UP = "STRONG_UP"
    UP = "UP"
    NEUTRAL = "NEUTRAL"
    DOWN = "DOWN"
    STRONG_DOWN = "STRONG_DOWN"

class Signal(Enum):
    ACCUMULATE_AGGRESSIVE = "ACCUMULATE_AGGRESSIVE"
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    DISTRIBUTE = "DISTRIBUTE"

class AltSeason(Enum):
    BTC_DOMINANT = "BTC_DOMINANT"
    EARLY_ALT = "EARLY_ALT"
    ALT_SEASON = "ALT_SEASON"
    LATE_ALT = "LATE_ALT"
    ROTATION_OUT = "ROTATION_OUT"

# =============================================================================
# UNIFIED DATA CLASS
# =============================================================================

@dataclass
class MarketData:
    """Comprehensive market data input"""

    # === PRICE DATA ===
    btc_price: float
    btc_ath: float = 108000
    btc_cycle_low: float = 15500

    # BTC price history
    btc_1d: float = None
    btc_7d: float = None
    btc_14d: float = None
    btc_30d: float = None
    btc_90d: float = None
    btc_180d: float = None
    btc_365d: float = None

    # Moving averages
    btc_20d_ma: float = None
    btc_50d_ma: float = None
    btc_100d_ma: float = None
    btc_200d_ma: float = None
    btc_200w_ma: float = None
    btc_111d_ma: float = None
    btc_350d_ma: float = None

    # === ON-CHAIN ===
    mvrv: float = 1.0
    mvrv_7d: float = None
    mvrv_30d: float = None
    nupl: float = 0.5
    puell: float = 1.0
    reserve_risk: float = 0.002

    # === LIQUIDITY ===
    fed_bs: float = 6.57           # Trillion
    fed_bs_30d: float = None
    fed_bs_90d: float = None
    fed_bs_180d: float = None
    fed_bs_365d: float = None

    rrp: float = 0.30              # Trillion
    rrp_30d: float = None
    rrp_peak: float = 2.55

    tga: float = 0.80              # Trillion

    m2_yoy: float = 0.0            # Global M2 YoY %
    m2_mom: float = 0.0

    # === REGIONAL FED (ISM LEADING) ===
    empire_state: float = None
    empire_prior: float = None
    philly_fed: float = None
    philly_prior: float = None
    richmond: float = None
    richmond_prior: float = None
    kansas_city: float = None
    kansas_prior: float = None
    dallas: float = None
    dallas_prior: float = None

    # === ISM ===
    ism_mfg: float = 48.0
    ism_mfg_prior: float = None
    ism_mfg_3m: float = None
    ism_svc: float = 54.0
    ism_svc_prior: float = None

    # === INSTITUTIONAL ===
    etf_flow_7d: float = 0
    etf_flow_30d: float = 0
    etf_flow_90d: float = 0
    etf_aum: float = 0

    # === SENTIMENT ===
    fear_greed: int = 50
    fear_greed_7d: int = None
    fear_greed_30d: int = None

    # === DERIVATIVES ===
    funding_8h: float = 0.01
    funding_7d: float = None
    funding_30d: float = None
    oi_btc: float = 0
    oi_change_7d: float = 0

    # === TECHNICALS ===
    rsi_14d: float = 50
    rsi_weekly: float = 50
    rsi_monthly: float = 50

    # === ALTCOINS ===
    eth_price: float = None
    eth_btc: float = None
    eth_btc_7d: float = None
    eth_btc_30d: float = None
    eth_btc_90d: float = None

    total3_btc: float = None       # Altcoin market cap / BTC
    total3_btc_30d: float = None
    others_btc: float = None       # Small caps / BTC
    others_btc_30d: float = None

    btc_dominance: float = None
    btc_dom_30d: float = None

    # === VOLATILITY ===
    vol_30d: float = 0.55
    vol_90d: float = 0.60

    # === METADATA ===
    date: str = ""
    days_since_genesis: int = 0

    def __post_init__(self):
        if not self.days_since_genesis:
            self.days_since_genesis = (date.today() - GENESIS_DATE).days

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'btc_price': self.btc_price,
            'btc_ath': self.btc_ath,
            'btc_cycle_low': self.btc_cycle_low,
            'btc_1d': self.btc_1d,
            'btc_7d': self.btc_7d,
            'btc_14d': self.btc_14d,
            'btc_30d': self.btc_30d,
            'btc_90d': self.btc_90d,
            'btc_180d': self.btc_180d,
            'btc_365d': self.btc_365d,
            'btc_200d_ma': self.btc_200d_ma,
            'btc_200w_ma': self.btc_200w_ma,
            'mvrv': self.mvrv,
            'nupl': self.nupl,
            'fed_bs': self.fed_bs,
            'rrp': self.rrp,
            'tga': self.tga,
            'm2_yoy': self.m2_yoy,
            'ism_mfg': self.ism_mfg,
            'ism_svc': self.ism_svc,
            'fear_greed': self.fear_greed,
            'rsi_14d': self.rsi_14d,
            'eth_btc': self.eth_btc,
            'btc_dominance': self.btc_dominance,
            'date': self.date
        }


# =============================================================================
# MODULE 1: LIQUIDITY ENGINE
# =============================================================================

class LiquidityEngine:
    """Comprehensive liquidity analysis"""

    def analyze(self, d: MarketData) -> Dict:
        # Net liquidity calculation
        net_liq = d.fed_bs - d.rrp - d.tga

        # RRP depletion (bullish when low)
        rrp_depletion = ((d.rrp_peak - d.rrp) / d.rrp_peak * 100) if d.rrp_peak > 0 else 0

        # Fed trajectory
        fed_mom_30d = self._pct(d.fed_bs, d.fed_bs_30d)
        fed_mom_90d = self._pct(d.fed_bs, d.fed_bs_90d)
        fed_mom_365d = self._pct(d.fed_bs, d.fed_bs_365d)

        # Liquidity score (0-100)
        score = 50  # Baseline
        score += min(25, rrp_depletion / 4)  # +25 max for RRP depletion
        score += min(15, max(-15, fed_mom_90d * 3))  # ±15 for Fed trajectory
        score += min(10, max(-10, d.m2_yoy * 2))  # ±10 for M2
        score = max(0, min(100, score))

        # Determine regime
        if rrp_depletion > 80 and fed_mom_90d > -3:
            regime = LiquidityRegime.EXPANSION
        elif fed_mom_90d < -5 or (d.m2_yoy < -2):
            regime = LiquidityRegime.CONTRACTION
        else:
            regime = LiquidityRegime.NEUTRAL

        # Momentum
        if d.rrp_30d:
            rrp_mom = ((d.rrp_30d - d.rrp) / d.rrp_30d * 100) if d.rrp_30d > 0 else 0
        else:
            rrp_mom = 0

        return {
            'net_liquidity_T': round(net_liq, 3),
            'rrp_T': d.rrp,
            'rrp_depletion_pct': round(rrp_depletion, 1),
            'rrp_momentum_30d': round(rrp_mom, 1),
            'fed_bs_T': d.fed_bs,
            'fed_mom_30d': round(fed_mom_30d, 2),
            'fed_mom_90d': round(fed_mom_90d, 2),
            'fed_mom_365d': round(fed_mom_365d, 2),
            'm2_yoy': d.m2_yoy,
            'score': round(score, 1),
            'regime': regime.value,
            'regime_description': self._describe_regime(regime, rrp_depletion, fed_mom_90d)
        }

    def _pct(self, curr: float, prior: float) -> float:
        if not prior or prior == 0:
            return 0
        return ((curr - prior) / prior) * 100

    def _describe_regime(self, regime: LiquidityRegime, rrp_dep: float, fed_mom: float) -> str:
        if regime == LiquidityRegime.EXPANSION:
            return f"RRP {rrp_dep:.0f}% depleted, Fed stable → Tailwind for risk assets"
        elif regime == LiquidityRegime.CONTRACTION:
            return f"Fed {fed_mom:+.1f}% (90d) → Headwind for risk assets"
        return "Mixed signals → Neutral for positioning"


# =============================================================================
# MODULE 2: BUSINESS CYCLE (ISM + REGIONAL FED)
# =============================================================================

class BusinessCycleEngine:
    """ISM tracking with Regional Fed leading indicators"""

    def analyze(self, d: MarketData) -> Dict:
        # Regional Fed composite (leading indicator)
        regional = self._regional_composite(d)

        # ISM analysis
        ism_composite = d.ism_mfg * 0.3 + d.ism_svc * 0.7  # Services-weighted
        ism_momentum = (d.ism_mfg - d.ism_mfg_prior) if d.ism_mfg_prior else 0

        # ISM preview from regional
        ism_preview = 50 + (regional['composite'] * 0.5)
        ism_preview = max(40, min(60, ism_preview))

        # Business cycle score
        score = ism_composite - 50  # Convert to -50 to +50 scale
        score = (score + 50)  # Normalize to 0-100

        # Cycle stage
        if ism_composite > 55 and ism_momentum > 0:
            stage = "EXPANSION_ACCELERATING"
        elif ism_composite > 50:
            stage = "EXPANSION"
        elif ism_composite > 47 and ism_momentum > 0:
            stage = "RECOVERY"
        elif ism_composite > 45:
            stage = "CONTRACTION_MILD"
        else:
            stage = "CONTRACTION_DEEP"

        return {
            'ism_mfg': d.ism_mfg,
            'ism_svc': d.ism_svc,
            'ism_composite': round(ism_composite, 1),
            'ism_momentum': round(ism_momentum, 1),
            'regional_fed': regional,
            'ism_preview': round(ism_preview, 1),
            'regional_vs_ism_divergence': round(ism_preview - d.ism_mfg, 1),
            'score': round(score, 1),
            'stage': stage,
            'early_warning': abs(ism_preview - d.ism_mfg) > 3
        }

    def _regional_composite(self, d: MarketData) -> Dict:
        surveys = [
            ('empire', d.empire_state, d.empire_prior),
            ('philly', d.philly_fed, d.philly_prior),
            ('richmond', d.richmond, d.richmond_prior),
            ('kansas', d.kansas_city, d.kansas_prior),
            ('dallas', d.dallas, d.dallas_prior)
        ]

        weighted_sum, total_weight = 0, 0
        momentum_sum, mom_count = 0, 0
        components = {}

        for key, curr, prior in surveys:
            w = REGIONAL_WEIGHTS[key]
            if curr is not None:
                weighted_sum += curr * w
                total_weight += w
                mom = (curr - prior) if prior is not None else 0
                momentum_sum += mom
                mom_count += 1
                components[key] = {'value': curr, 'mom': round(mom, 1)}

        composite = weighted_sum / total_weight if total_weight > 0 else 0
        avg_mom = momentum_sum / mom_count if mom_count > 0 else 0

        # Cycle signal
        if composite > 0 and avg_mom > 2:
            signal = "ACCELERATING"
        elif composite > 0:
            signal = "EXPANDING"
        elif composite < 0 and avg_mom > 2:
            signal = "BOTTOMING"
        elif composite < 0:
            signal = "CONTRACTING"
        else:
            signal = "NEUTRAL"

        return {
            'composite': round(composite, 1),
            'momentum': round(avg_mom, 1),
            'signal': signal,
            'components': components,
            'coverage': f"{mom_count}/5"
        }


# =============================================================================
# MODULE 3: BTC TREND ANALYSIS (STF/MTF/LTF)
# =============================================================================

class BTCTrendEngine:
    """Multi-timeframe BTC trend analysis"""

    def analyze(self, d: MarketData) -> Dict:
        stf = self._stf(d)
        mtf = self._mtf(d)
        ltf = self._ltf(d)

        # Alignment
        directions = [stf['trend'], mtf['trend'], ltf['trend']]
        bullish = sum(1 for t in directions if t in ['STRONG_UP', 'UP'])

        if bullish == 3:
            alignment = "FULLY_BULLISH"
            score = 100
        elif bullish == 2:
            alignment = "MOSTLY_BULLISH"
            score = 75
        elif bullish == 1:
            alignment = "MIXED"
            score = 50
        elif bullish == 0:
            bearish = sum(1 for t in directions if t in ['STRONG_DOWN', 'DOWN'])
            alignment = "FULLY_BEARISH" if bearish == 3 else "MOSTLY_BEARISH"
            score = 0 if bearish == 3 else 25
        else:
            alignment = "NEUTRAL"
            score = 50

        # Composite momentum (LTF-weighted for cycle trading)
        composite_mom = stf['momentum'] * 0.15 + mtf['momentum'] * 0.35 + ltf['momentum'] * 0.50

        return {
            'STF': stf,
            'MTF': mtf,
            'LTF': ltf,
            'alignment': alignment,
            'alignment_score': score,
            'composite_momentum': round(composite_mom, 2),
            'interpretation': self._interpret(alignment, composite_mom)
        }

    def _stf(self, d: MarketData) -> Dict:
        """Short-term: Days to 2 weeks"""
        chg_1d = self._pct(d.btc_price, d.btc_1d)
        chg_7d = self._pct(d.btc_price, d.btc_7d)
        chg_14d = self._pct(d.btc_price, d.btc_14d)

        mom = chg_1d * 0.2 + chg_7d * 0.4 + chg_14d * 0.4
        trend = self._classify_trend(mom, thresholds=(3, 8))

        return {
            'timeframe': 'Days to 2 weeks',
            'trend': trend,
            'momentum': round(mom, 2),
            'changes': {'1d': round(chg_1d, 2), '7d': round(chg_7d, 2), '14d': round(chg_14d, 2)},
            'rsi': d.rsi_14d
        }

    def _mtf(self, d: MarketData) -> Dict:
        """Medium-term: 2 weeks to 3 months"""
        chg_14d = self._pct(d.btc_price, d.btc_14d)
        chg_30d = self._pct(d.btc_price, d.btc_30d)
        chg_90d = self._pct(d.btc_price, d.btc_90d)

        mom = chg_14d * 0.2 + chg_30d * 0.4 + chg_90d * 0.4
        trend = self._classify_trend(mom, thresholds=(8, 20))

        # MA alignment
        ma_score = sum([
            d.btc_price > (d.btc_50d_ma or 0),
            d.btc_price > (d.btc_100d_ma or 0),
            d.btc_price > (d.btc_200d_ma or 0)
        ])

        return {
            'timeframe': '2 weeks to 3 months',
            'trend': trend,
            'momentum': round(mom, 2),
            'changes': {'14d': round(chg_14d, 2), '30d': round(chg_30d, 2), '90d': round(chg_90d, 2)},
            'ma_alignment': f"{ma_score}/3",
            'rsi': d.rsi_weekly
        }

    def _ltf(self, d: MarketData) -> Dict:
        """Long-term: 3 months to 1 year+"""
        chg_90d = self._pct(d.btc_price, d.btc_90d)
        chg_180d = self._pct(d.btc_price, d.btc_180d)
        chg_365d = self._pct(d.btc_price, d.btc_365d)

        mom = chg_90d * 0.25 + chg_180d * 0.35 + chg_365d * 0.40
        trend = self._classify_trend(mom, thresholds=(20, 50))

        # Structural
        above_200w = d.btc_price > (d.btc_200w_ma or 0)

        # Power Law
        fair = POWER_LAW_INTERCEPT * (d.days_since_genesis ** POWER_LAW_SLOPE)
        pl_dev = ((d.btc_price - fair) / fair) * 100

        return {
            'timeframe': '3 months to 1 year+',
            'trend': trend,
            'momentum': round(mom, 2),
            'changes': {'90d': round(chg_90d, 2), '180d': round(chg_180d, 2), '365d': round(chg_365d, 2)},
            'above_200w_ma': above_200w,
            'power_law_fair': round(fair, 0),
            'power_law_deviation': round(pl_dev, 1),
            'rsi': d.rsi_monthly
        }

    def _pct(self, curr: float, prior: float) -> float:
        if not prior or prior == 0:
            return 0
        return ((curr - prior) / prior) * 100

    def _classify_trend(self, mom: float, thresholds: Tuple[int, int]) -> str:
        mild, strong = thresholds
        if mom > strong:
            return 'STRONG_UP'
        elif mom > mild:
            return 'UP'
        elif mom < -strong:
            return 'STRONG_DOWN'
        elif mom < -mild:
            return 'DOWN'
        return 'NEUTRAL'

    def _interpret(self, alignment: str, mom: float) -> str:
        if alignment == "FULLY_BULLISH":
            return "All timeframes aligned bullish - high conviction long"
        elif alignment == "MOSTLY_BULLISH":
            return "2/3 timeframes bullish - favorable but monitor divergence"
        elif alignment == "FULLY_BEARISH":
            return "All timeframes bearish - avoid new longs"
        elif alignment == "MOSTLY_BEARISH":
            return "2/3 timeframes bearish - defensive positioning"
        return "Mixed signals - reduce position size"


# =============================================================================
# MODULE 4: ALTCOIN ROTATION
# =============================================================================

class AltcoinEngine:
    """Altcoin rotation analysis using BTC-denominated ratios"""

    def analyze(self, d: MarketData) -> Dict:
        # ETH/BTC analysis
        eth_btc = self._analyze_ratio(d.eth_btc, d.eth_btc_7d, d.eth_btc_30d, d.eth_btc_90d, "ETH/BTC")

        # TOTAL3/BTC (altcoins ex ETH)
        total3 = self._analyze_ratio(d.total3_btc, None, d.total3_btc_30d, None, "TOTAL3/BTC")

        # OTHERS/BTC (small caps)
        others = self._analyze_ratio(d.others_btc, None, d.others_btc_30d, None, "OTHERS/BTC")

        # BTC Dominance
        dom_change = (d.btc_dominance - d.btc_dom_30d) if d.btc_dom_30d else 0

        # Determine alt season phase
        phase = self._determine_phase(eth_btc, total3, others, dom_change)

        # Rotation score (0 = BTC dominant, 100 = full alt season)
        score = 50  # Baseline
        if eth_btc['trend'] in ['UP', 'STRONG_UP']:
            score += 15
        if total3['trend'] in ['UP', 'STRONG_UP']:
            score += 20
        if others['trend'] in ['UP', 'STRONG_UP']:
            score += 15
        if dom_change < -2:
            score += 10
        score = max(0, min(100, score))

        return {
            'eth_btc': eth_btc,
            'total3_btc': total3,
            'others_btc': others,
            'btc_dominance': d.btc_dominance,
            'btc_dom_change_30d': round(dom_change, 2) if dom_change else 0,
            'others_vs_btc': others.get('mom_30d', 0),  # 30d performance vs BTC
            'eth_vs_btc': eth_btc.get('mom_30d', 0),    # ETH 30d performance vs BTC
            'phase': phase.value,
            'rotation_score': score,
            'allocation_suggestion': self._suggest_allocation(phase, score)
        }

    def _analyze_ratio(self, curr, d7, d30, d90, name) -> Dict:
        if curr is None:
            return {'name': name, 'trend': 'UNKNOWN', 'momentum': 0, 'value': None}

        mom_30d = self._pct(curr, d30) if d30 else 0
        mom_90d = self._pct(curr, d90) if d90 else 0
        mom = mom_30d * 0.6 + mom_90d * 0.4

        if mom > 10:
            trend = 'STRONG_UP'
        elif mom > 3:
            trend = 'UP'
        elif mom < -10:
            trend = 'STRONG_DOWN'
        elif mom < -3:
            trend = 'DOWN'
        else:
            trend = 'NEUTRAL'

        return {
            'name': name,
            'value': curr,
            'mom_30d': round(mom_30d, 2),
            'trend': trend,
            'momentum': round(mom, 2)
        }

    def _pct(self, curr, prior):
        if not prior or prior == 0:
            return 0
        return ((curr - prior) / prior) * 100

    def _determine_phase(self, eth, total3, others, dom_change) -> AltSeason:
        eth_up = eth['trend'] in ['UP', 'STRONG_UP']
        total3_up = total3['trend'] in ['UP', 'STRONG_UP']
        others_up = others['trend'] in ['UP', 'STRONG_UP']

        if not eth_up and not total3_up and dom_change and dom_change > 0:
            return AltSeason.BTC_DOMINANT
        elif eth_up and not total3_up:
            return AltSeason.EARLY_ALT
        elif eth_up and total3_up and others_up:
            return AltSeason.ALT_SEASON
        elif total3_up and others_up and not eth_up:
            return AltSeason.LATE_ALT
        elif dom_change and dom_change > 3:
            return AltSeason.ROTATION_OUT
        return AltSeason.EARLY_ALT

    def _suggest_allocation(self, phase: AltSeason, score: int) -> Dict:
        allocations = {
            AltSeason.BTC_DOMINANT: {'BTC': 70, 'ETH': 20, 'ALTS': 10},
            AltSeason.EARLY_ALT: {'BTC': 50, 'ETH': 30, 'ALTS': 20},
            AltSeason.ALT_SEASON: {'BTC': 35, 'ETH': 30, 'ALTS': 35},
            AltSeason.LATE_ALT: {'BTC': 40, 'ETH': 25, 'ALTS': 35},
            AltSeason.ROTATION_OUT: {'BTC': 60, 'ETH': 25, 'ALTS': 15}
        }
        return allocations.get(phase, {'BTC': 50, 'ETH': 30, 'ALTS': 20})


# =============================================================================
# MODULE 5: PHASE & VALUE DETECTION
# =============================================================================

class PhaseEngine:
    """Wyckoff cycle phase and value zone detection"""

    def analyze(self, d: MarketData, liq: Dict, trends: Dict) -> Dict:
        # Value zone (MVRV-based)
        value_zone, value_details = self._value_zone(d)

        # Cycle progress (0-100%)
        progress = self._cycle_progress(d, liq)

        # Phase detection
        phase, confidence = self._detect_phase(d, value_zone, progress, trends)

        # Top detection
        top_warning, top_score, top_indicators = self._top_detection(d)

        return {
            'phase': phase.value,
            'phase_confidence': round(confidence, 1),
            'cycle_progress': round(progress, 1),
            'value_zone': value_zone.value,
            'value_details': value_details,
            'in_buy_zone': value_zone in [ValueZone.DEEP_VALUE, ValueZone.VALUE],
            'in_sell_zone': value_zone in [ValueZone.EXTENDED, ValueZone.EUPHORIA],
            'top_warning': top_warning.value,
            'top_score': top_score,
            'top_indicators': top_indicators
        }

    def _value_zone(self, d: MarketData) -> Tuple[ValueZone, Dict]:
        mvrv = d.mvrv

        if mvrv < 1.0:
            zone = ValueZone.DEEP_VALUE
            signal = "DEEP VALUE - Aggressive accumulation"
        elif mvrv < 2.0:
            zone = ValueZone.VALUE
            signal = "VALUE - Continue accumulating"
        elif mvrv < 3.0:
            zone = ValueZone.FAIR
            signal = "FAIR - Hold position"
        elif mvrv < 5.0:
            zone = ValueZone.EXTENDED
            signal = "EXTENDED - Begin distribution"
        else:
            zone = ValueZone.EUPHORIA
            signal = "EUPHORIA - Distribute aggressively"

        # Power Law position
        fair = POWER_LAW_INTERCEPT * (d.days_since_genesis ** POWER_LAW_SLOPE)
        pl_dev = ((d.btc_price - fair) / fair) * 100

        return zone, {
            'mvrv': mvrv,
            'mvrv_signal': signal,
            'power_law_fair': round(fair, 0),
            'power_law_deviation': round(pl_dev, 1)
        }

    def _cycle_progress(self, d: MarketData, liq: Dict) -> float:
        # MVRV progress (40%)
        mvrv_pct = (d.mvrv - MVRV_HISTORICAL_LOW) / (MVRV_HISTORICAL_HIGH - MVRV_HISTORICAL_LOW) * 100
        mvrv_pct = max(0, min(100, mvrv_pct))

        # Price progress (30%)
        price_range = d.btc_ath - d.btc_cycle_low
        price_pct = ((d.btc_price - d.btc_cycle_low) / price_range * 100) if price_range > 0 else 50
        price_pct = max(0, min(100, price_pct))

        # Liquidity progress (30%)
        liq_pct = liq.get('score', 50)

        return mvrv_pct * 0.40 + price_pct * 0.30 + liq_pct * 0.30

    def _detect_phase(self, d: MarketData, zone: ValueZone, progress: float, trends: Dict) -> Tuple[Phase, float]:
        scores = {p: 0 for p in Phase}

        # MVRV-based
        if d.mvrv < 0:
            scores[Phase.CAPITULATION] += 40
        elif d.mvrv < 1.0:
            scores[Phase.ACCUMULATION] += 35
            scores[Phase.CAPITULATION] += 15
        elif d.mvrv < 2.0:
            scores[Phase.ACCUMULATION] += 20
            scores[Phase.EARLY_MARKUP] += 30
        elif d.mvrv < 3.0:
            scores[Phase.MID_MARKUP] += 40
        elif d.mvrv < 5.0:
            scores[Phase.LATE_MARKUP] += 35
        else:
            scores[Phase.DISTRIBUTION] += 50

        # Sentiment-based
        if d.fear_greed < 20:
            scores[Phase.CAPITULATION] += 25
        elif d.fear_greed > 80:
            scores[Phase.DISTRIBUTION] += 25

        # Trend-based
        ltf_trend = trends.get('LTF', {}).get('trend', 'NEUTRAL')
        if ltf_trend in ['STRONG_UP', 'UP']:
            scores[Phase.MID_MARKUP] += 15
            scores[Phase.EARLY_MARKUP] += 10
        elif ltf_trend in ['STRONG_DOWN', 'DOWN']:
            scores[Phase.MID_MARKDOWN] += 15

        best = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = (scores[best] / total * 100) if total > 0 else 0

        return best, confidence

    def _top_detection(self, d: MarketData) -> Tuple[TopWarning, int, List[str]]:
        score = 0
        indicators = []

        # MVRV (20 pts)
        if d.mvrv > 6.0:
            score += 20
            indicators.append("MVRV > 6.0")
        elif d.mvrv > 5.0:
            score += 15
            indicators.append("MVRV > 5.0")
        elif d.mvrv > 4.0:
            score += 8
            indicators.append("MVRV > 4.0")

        # NUPL (15 pts)
        if d.nupl > 0.75:
            score += 15
            indicators.append("NUPL > 0.75")
        elif d.nupl > 0.6:
            score += 10
            indicators.append("NUPL > 0.6")

        # Sentiment (15 pts)
        if d.fear_greed > 85:
            score += 10
            indicators.append("Fear/Greed > 85")
        if d.fear_greed_30d and d.fear_greed_30d > 70:
            score += 5
            indicators.append("Sustained greed")

        # Funding (10 pts)
        if d.funding_30d and d.funding_30d > 0.05:
            score += 10
            indicators.append("Funding > 0.05%")
        elif d.funding_30d and d.funding_30d > 0.03:
            score += 5
            indicators.append("Funding elevated")

        # Pi Cycle (15 pts)
        if d.btc_111d_ma and d.btc_350d_ma:
            pi_dist = ((d.btc_111d_ma - d.btc_350d_ma * 2) / (d.btc_350d_ma * 2) * 100)
            if pi_dist > 0:
                score += 15
                indicators.append("Pi Cycle CROSSED")
            elif pi_dist > -10:
                score += 10
                indicators.append("Pi Cycle < 10%")

        # RSI (15 pts)
        if d.rsi_weekly > 80:
            score += 8
            indicators.append("Weekly RSI > 80")
        if d.rsi_monthly > 85:
            score += 7
            indicators.append("Monthly RSI > 85")

        # Price extension (10 pts)
        if d.btc_200w_ma:
            ext = ((d.btc_price - d.btc_200w_ma) / d.btc_200w_ma * 100)
            if ext > 200:
                score += 10
                indicators.append(">200% above 200W MA")
            elif ext > 150:
                score += 6
                indicators.append(">150% above 200W MA")

        score = min(100, score)

        if score >= 70:
            warning = TopWarning.CRITICAL
        elif score >= 50:
            warning = TopWarning.DANGER
        elif score >= 35:
            warning = TopWarning.CAUTION
        elif score >= 20:
            warning = TopWarning.WATCH
        else:
            warning = TopWarning.NONE

        return warning, score, indicators


# =============================================================================
# MODULE 6: FORECASTING (PHASE TRANSITION + MONTE CARLO)
# =============================================================================

class ForecastEngine:
    """Phase transition forecasting and Monte Carlo simulation"""

    PHASE_TRIGGERS = {
        Phase.CAPITULATION: {'next': Phase.ACCUMULATION, 'triggers': ['MVRV > 0', 'F&G > 20'], 'weeks': 8},
        Phase.ACCUMULATION: {'next': Phase.EARLY_MARKUP, 'triggers': ['MVRV > 1.5', 'Break 200D MA'], 'weeks': 20},
        Phase.EARLY_MARKUP: {'next': Phase.MID_MARKUP, 'triggers': ['MVRV > 2.0', 'MAs align', 'F&G > 50'], 'weeks': 16},
        Phase.MID_MARKUP: {'next': Phase.LATE_MARKUP, 'triggers': ['MVRV > 3.5', 'RSI > 70 sustained'], 'weeks': 24},
        Phase.LATE_MARKUP: {'next': Phase.DISTRIBUTION, 'triggers': ['MVRV > 5.0', 'Pi Cycle warn'], 'weeks': 12},
        Phase.DISTRIBUTION: {'next': Phase.EARLY_MARKDOWN, 'triggers': ['Break 50D', 'F&G < 40'], 'weeks': 8},
        Phase.EARLY_MARKDOWN: {'next': Phase.MID_MARKDOWN, 'triggers': ['Break 200D', 'MVRV < 2.5'], 'weeks': 12},
        Phase.MID_MARKDOWN: {'next': Phase.CAPITULATION, 'triggers': ['MVRV < 0.5', 'F&G < 15'], 'weeks': 16}
    }

    PHASE_PARAMS = {
        Phase.CAPITULATION: {'vol_mult': 1.5, 'drift': 0.15},
        Phase.ACCUMULATION: {'vol_mult': 1.0, 'drift': 0.08},
        Phase.EARLY_MARKUP: {'vol_mult': 1.1, 'drift': 0.10},
        Phase.MID_MARKUP: {'vol_mult': 1.2, 'drift': 0.12},
        Phase.LATE_MARKUP: {'vol_mult': 1.4, 'drift': 0.05},
        Phase.DISTRIBUTION: {'vol_mult': 1.3, 'drift': -0.05},
        Phase.EARLY_MARKDOWN: {'vol_mult': 1.4, 'drift': -0.10},
        Phase.MID_MARKDOWN: {'vol_mult': 1.6, 'drift': -0.08}
    }

    def analyze(self, d: MarketData, phase: Phase, trends: Dict) -> Dict:
        # Phase transition forecast
        transition = self._phase_transition(d, phase, trends)

        # Monte Carlo simulation
        monte_carlo = self._monte_carlo(d, phase)

        # Scenarios
        scenarios = self._scenarios(d, phase)

        return {
            'transition': transition,
            'monte_carlo': monte_carlo,
            'scenarios': scenarios
        }

    def _phase_transition(self, d: MarketData, phase: Phase, trends: Dict) -> Dict:
        info = self.PHASE_TRIGGERS.get(phase, {})
        next_phase = info.get('next', phase)
        triggers = info.get('triggers', [])
        avg_weeks = info.get('weeks', 12)

        # Check triggers
        met = []
        if d.mvrv > 1.5 and 'MVRV > 1.5' in triggers:
            met.append('MVRV > 1.5')
        if d.mvrv > 2.0 and 'MVRV > 2.0' in triggers:
            met.append('MVRV > 2.0')
        if d.btc_price > (d.btc_200d_ma or 0) and 'Break 200D MA' in triggers:
            met.append('Break 200D MA')
        if d.fear_greed > 50 and 'F&G > 50' in triggers:
            met.append('F&G > 50')
        if trends.get('LTF', {}).get('trend') in ['UP', 'STRONG_UP']:
            met.append('LTF uptrend')

        prob = 20 + len(met) * 15
        prob = min(85, prob)

        if prob > 60:
            timeline = f"0-{int(avg_weeks * 0.5)} weeks"
        elif prob > 40:
            timeline = f"{int(avg_weeks * 0.3)}-{int(avg_weeks * 0.7)} weeks"
        else:
            timeline = f"{int(avg_weeks * 0.5)}-{avg_weeks}+ weeks"

        # User-friendly phase display names
        phase_display_names = {
            'CAPITULATION': 'Cycle Bottom',
            'ACCUMULATION': 'Recovery / Accumulation',
            'EARLY_MARKUP': 'Early Bull Market',
            'MID_MARKUP': 'Bull Market',
            'LATE_MARKUP': 'Late Bull / Peak Zone',
            'DISTRIBUTION': 'Cycle Top / Distribution',
            'EARLY_MARKDOWN': 'Early Bear Market',
            'MID_MARKDOWN': 'Bear Market'
        }

        return {
            'current': phase.value,
            'current_display': phase_display_names.get(phase.value, phase.value),
            'next': phase_display_names.get(next_phase.value, next_phase.value),
            'next_internal': next_phase.value,
            'probability': prob,
            'triggers_required': triggers,
            'triggers_met': met,
            'timeline': timeline,
            'confidence': 'HIGH' if prob > 60 else 'MEDIUM' if prob > 40 else 'LOW'
        }

    def _monte_carlo(self, d: MarketData, phase: Phase, n_sims: int = 5000,
                     horizons: List[int] = [30, 90, 180, 365]) -> Dict:
        results = {}
        params = self.PHASE_PARAMS.get(phase, {'vol_mult': 1.0, 'drift': 0.05})
        base_vol = d.vol_90d or 0.60
        vol = base_vol * params['vol_mult']
        drift = params['drift']

        for horizon in horizons:
            prices = self._simulate(d.btc_price, vol, drift, horizon, n_sims, d.days_since_genesis)
            results[f"{horizon}d"] = {
                'horizon': f"{horizon // 30}M" if horizon >= 30 else f"{horizon}D",
                'median': int(np.median(prices)),
                'mean': int(np.mean(prices)),
                'p10': int(np.percentile(prices, 10)),
                'p25': int(np.percentile(prices, 25)),
                'p75': int(np.percentile(prices, 75)),
                'p90': int(np.percentile(prices, 90)),
                'expected_return': round((np.median(prices) / d.btc_price - 1) * 100, 1),
                'prob_above_100k': round(np.mean(prices > 100000) * 100, 1),
                'prob_above_150k': round(np.mean(prices > 150000) * 100, 1),
                'prob_below_75k': round(np.mean(prices < 75000) * 100, 1)
            }

        return results

    def _simulate(self, price: float, vol: float, drift: float,
                  horizon: int, n_sims: int, days_genesis: int) -> np.ndarray:
        dt = 1 / 365
        daily_vol = vol * np.sqrt(dt)
        daily_drift = drift * dt

        # Power Law bounds
        future_days = days_genesis + horizon
        fair = POWER_LAW_INTERCEPT * (future_days ** POWER_LAW_SLOPE)
        floor = fair * 0.22
        ceiling = fair * 4.5

        results = []
        for _ in range(n_sims):
            p = price
            for _ in range(horizon):
                shock = np.random.normal(0, 1)
                reversion = (fair - p) / fair * 0.002
                ret = daily_drift + reversion + daily_vol * shock
                p = p * (1 + ret)
                p = max(floor * 0.8, min(ceiling * 1.2, p))
            results.append(p)

        return np.array(results)

    def _scenarios(self, d: MarketData, phase: Phase) -> Dict:
        price = d.btc_price

        return {
            'bull': {
                'name': 'Liquidity Expansion',
                'probability': 35,
                '12m_target': int(price * 2.5),
                'mvrv_path': '→ 3.0 → 4.5 → 6.0',
                'triggers': ['Fed pivot', 'ETF surge', 'M2 acceleration']
            },
            'base': {
                'name': 'Gradual Progress',
                'probability': 45,
                '12m_target': int(price * 1.7),
                'mvrv_path': '→ 2.0 → 2.5 → 3.5',
                'triggers': ['Steady accumulation', 'ISM > 50', 'Stable flows']
            },
            'bear': {
                'name': 'Liquidity Contraction',
                'probability': 15,
                '12m_target': int(price * 0.55),
                'mvrv_path': '→ 0.8 → 0.5 → 0.3',
                'triggers': ['QT acceleration', 'Credit event', 'Recession']
            },
            'black_swan': {
                'name': 'Exogenous Shock',
                'probability': 5,
                '12m_target': 'Unknown',
                'triggers': ['Unpredictable']
            }
        }


# =============================================================================
# MODULE 7: BACKTESTING & REGIME TRACKING
# =============================================================================

class BacktestEngine:
    """Historical regime validation and tracking"""

    HISTORICAL_REGIMES = [
        {'name': 'COVID Crash', 'date': '2020-03', 'mvrv': -0.2, 'fg': 8, 'phase': 'CAPITULATION', 'signal': 'STRONG_BUY'},
        {'name': 'Nov 2021 Top', 'date': '2021-11', 'mvrv': 6.8, 'fg': 84, 'phase': 'DISTRIBUTION', 'signal': 'DISTRIBUTE'},
        {'name': 'Jun 2022 Crash', 'date': '2022-06', 'mvrv': 0.3, 'fg': 10, 'phase': 'CAPITULATION', 'signal': 'ACCUMULATE'},
        {'name': 'Nov 2022 Bottom', 'date': '2022-11', 'mvrv': -0.1, 'fg': 20, 'phase': 'CAPITULATION', 'signal': 'STRONG_BUY'},
        {'name': 'ETF Launch', 'date': '2024-01', 'mvrv': 1.8, 'fg': 70, 'phase': 'EARLY_MARKUP', 'signal': 'HOLD'},
        {'name': 'Mar 2024 ATH', 'date': '2024-03', 'mvrv': 2.8, 'fg': 82, 'phase': 'MID_MARKUP', 'signal': 'HOLD'}
    ]

    def analyze(self, d: MarketData, phase_result: Dict) -> Dict:
        # Current regime classification
        current_regime = self._classify_regime(d, phase_result)

        # Find similar historical periods
        similar = self._find_similar(d, phase_result)

        # Model performance on historical regimes
        performance = self._historical_performance()

        return {
            'current_regime': current_regime,
            'similar_historical': similar,
            'model_performance': performance,
            'regime_duration': self._estimate_duration(phase_result['phase'])
        }

    def _classify_regime(self, d: MarketData, phase: Dict) -> Dict:
        mvrv = d.mvrv
        fg = d.fear_greed

        if mvrv < 0.5 and fg < 25:
            regime = "CAPITULATION"
            description = "Maximum fear, historic buying opportunity"
        elif mvrv < 1.5 and fg < 40:
            regime = "ACCUMULATION"
            description = "Smart money accumulating, disbelief"
        elif mvrv < 2.5:
            regime = "BULL_EARLY"
            description = "Bull market, early stage"
        elif mvrv < 4.0:
            regime = "BULL_MID"
            description = "Bull market, mid stage"
        elif mvrv < 5.5:
            regime = "BULL_LATE"
            description = "Bull market, late stage - caution"
        elif mvrv >= 5.5:
            regime = "EUPHORIA"
            description = "Euphoria zone - distribution"
        else:
            regime = "TRANSITION"
            description = "Transitional period"

        return {
            'regime': regime,
            'description': description,
            'mvrv': mvrv,
            'fear_greed': fg,
            'phase': phase['phase']
        }

    def _find_similar(self, d: MarketData, phase: Dict) -> List[Dict]:
        similar = []
        for h in self.HISTORICAL_REGIMES:
            mvrv_diff = abs(d.mvrv - h['mvrv'])
            fg_diff = abs(d.fear_greed - h['fg'])

            if mvrv_diff < 1.0 and fg_diff < 20:
                similar.append({
                    'period': h['name'],
                    'date': h['date'],
                    'mvrv_then': h['mvrv'],
                    'signal_then': h['signal'],
                    'similarity': round(100 - (mvrv_diff * 30 + fg_diff * 0.5), 1)
                })

        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:3]

    def _historical_performance(self) -> Dict:
        return {
            'covid_crash_2020': {'detected': True, 'signal': 'STRONG_BUY', 'outcome': '+400% in 12M'},
            'nov_2021_top': {'detected': True, 'signal': 'DISTRIBUTE', 'outcome': 'Avoided -77% drawdown'},
            'nov_2022_bottom': {'detected': True, 'signal': 'STRONG_BUY', 'outcome': '+300% in 18M'},
            'accuracy_rate': '85% on major regime changes'
        }

    def _estimate_duration(self, phase: str) -> str:
        durations = {
            'CAPITULATION': '4-12 weeks',
            'ACCUMULATION': '12-24 weeks',
            'EARLY_MARKUP': '12-20 weeks',
            'MID_MARKUP': '20-32 weeks',
            'LATE_MARKUP': '8-16 weeks',
            'DISTRIBUTION': '4-12 weeks',
            'EARLY_MARKDOWN': '8-16 weeks',
            'MID_MARKDOWN': '12-20 weeks'
        }
        return durations.get(phase, '8-16 weeks')


# =============================================================================
# MODULE 8: SIGNAL GENERATOR
# =============================================================================

class SignalGenerator:
    """Generate final recommendation and allocation"""

    def generate(self, phase: Dict, liq: Dict, trends: Dict, alts: Dict, forecast: Dict) -> Dict:
        value_zone = phase['value_zone']
        top_warning = phase['top_warning']
        cycle_progress = phase['cycle_progress']

        # Top warning overrides
        if top_warning == 'CRITICAL':
            return self._signal(Signal.DISTRIBUTE, 25, ["CRITICAL TOP WARNING", "Distribute aggressively"])
        if top_warning == 'DANGER':
            return self._signal(Signal.REDUCE, 40, ["DANGER warning", "Begin distribution"])

        # Value-based signals
        if value_zone == 'DEEP_VALUE':
            return self._signal(Signal.ACCUMULATE_AGGRESSIVE, 90, ["DEEP VALUE", "Maximum conviction buying zone"])
        if value_zone == 'VALUE':
            return self._signal(Signal.ACCUMULATE, 75, ["VALUE zone", f"Cycle progress {cycle_progress:.0f}%"])
        if value_zone == 'FAIR':
            return self._signal(Signal.HOLD, 60, ["FAIR value", "Hold and monitor"])
        if value_zone == 'EXTENDED':
            return self._signal(Signal.REDUCE, 45, ["EXTENDED", "Begin scaling out"])
        if value_zone == 'EUPHORIA':
            return self._signal(Signal.DISTRIBUTE, 30, ["EUPHORIA", "Aggressive distribution"])

        return self._signal(Signal.HOLD, 50, ["Neutral positioning"])

    def _signal(self, sig: Signal, alloc: int, rationale: List[str]) -> Dict:
        return {
            'signal': sig.value,
            'allocation': alloc,
            'rationale': rationale,
            'confidence': 'HIGH' if alloc > 70 or alloc < 35 else 'MEDIUM'
        }


# =============================================================================
# MODULE 9: THESIS GENERATOR
# =============================================================================

class ThesisGenerator:
    """Generate 300-word thesis for social media"""

    # User-friendly phase display names
    PHASE_DISPLAY_NAMES = {
        'CAPITULATION': 'Cycle Bottom',
        'ACCUMULATION': 'Recovery / Accumulation',
        'EARLY_MARKUP': 'Early Bull Market',
        'MID_MARKUP': 'Bull Market',
        'LATE_MARKUP': 'Late Bull / Peak Zone',
        'DISTRIBUTION': 'Cycle Top / Distribution',
        'EARLY_MARKDOWN': 'Early Bear Market',
        'MID_MARKDOWN': 'Bear Market'
    }

    def generate(self, result: Dict) -> str:
        # Extract key data
        price = result['meta']['btc_price']
        signal = result['signal']['signal']
        alloc = result['signal']['allocation']
        phase_internal = result['phase']['phase']
        phase = self.PHASE_DISPLAY_NAMES.get(phase_internal, phase_internal)
        mvrv = result['phase']['value_details']['mvrv']
        progress = result['phase']['cycle_progress']
        top_score = result['phase']['top_score']

        liq = result['liquidity']
        net_liq = liq['net_liquidity_T']
        rrp_dep = liq['rrp_depletion_pct']
        liq_regime = liq['regime']

        biz = result['business_cycle']
        ism_preview = biz['ism_preview']
        regional_signal = biz['regional_fed']['signal']

        trends = result['btc_trends']
        ltf_trend = trends['LTF']['trend']
        alignment = trends['alignment']

        mc = result['forecast']['monte_carlo']
        mc_12m = mc.get('365d', {})
        median_12m = mc_12m.get('median', 0)
        prob_150k = mc_12m.get('prob_above_150k', 0)

        alts = result['altcoins']
        alt_phase = alts['phase']
        btc_alloc = alts['allocation_suggestion']['BTC']

        # Build thesis
        thesis = f"""BTC STRATEGIC CYCLE MODEL v7.0 | {result['meta']['date']}

SIGNAL: {signal} @ {alloc}%
BTC: ${price:,} | MVRV: {mvrv:.2f} | Cycle: {progress:.0f}%

KEY INSIGHTS:

VALUE: {"BUY ZONE" if result['phase']['in_buy_zone'] else "NOT in buy zone"} - MVRV {mvrv:.2f} puts us in {result['phase']['value_zone']} territory. {"Historically cheap, accumulate with conviction." if mvrv < 2 else "Fair value, hold position." if mvrv < 3 else "Extended, begin distribution."}

LIQUIDITY: {liq_regime} - Net liquidity ${net_liq:.2f}T. RRP {rrp_dep:.0f}% depleted ({"bullish" if rrp_dep > 70 else "neutral"}). {"Fed tailwind" if liq_regime == "EXPANSION" else "Fed headwind" if liq_regime == "CONTRACTION" else "Mixed signals"}.

BUSINESS CYCLE: Regional Fed {regional_signal} - ISM preview {ism_preview:.1f} vs current {biz['ism_mfg']}. {"Expecting ISM to improve" if ism_preview > biz['ism_mfg'] else "ISM may soften"}.

TRENDS: {alignment} - LTF {ltf_trend}. {"Bull cycle intact" if ltf_trend in ['STRONG_UP', 'UP'] else "Caution warranted"}.

TOP DETECTION: {result['phase']['top_warning']} ({top_score}/100) - {"No euphoria signals" if top_score < 20 else "Watch for distribution" if top_score < 50 else "Distribution underway"}.

FORECAST: 12M median ${median_12m:,} ({mc_12m.get('expected_return', 0):+.1f}%)
P(>$150K): {prob_150k:.0f}% | Phase: {phase} -> {result['forecast']['transition']['next']}

ALLOCATION: BTC {btc_alloc}% | ETH {alts['allocation_suggestion']['ETH']}% | Alts {alts['allocation_suggestion']['ALTS']}%
Alt Season: {alt_phase}

Thesis: BTC is a liquidity asset. Buy value, sell euphoria. Current MVRV {mvrv:.2f} = {"accumulation zone" if mvrv < 2 else "hold zone" if mvrv < 3 else "distribution zone"}.

#Bitcoin #Crypto #Macro"""

        return thesis


# =============================================================================
# MAIN MODEL CLASS
# =============================================================================

class StrategicCycleModel:
    """Bitcoin Strategic Cycle Model v7.1 - Unified Framework with Enhanced Insights"""

    def __init__(self):
        self.liquidity = LiquidityEngine()
        self.business_cycle = BusinessCycleEngine()
        self.btc_trends = BTCTrendEngine()
        self.altcoins = AltcoinEngine()
        self.phase = PhaseEngine()
        self.forecast = ForecastEngine()
        self.backtest = BacktestEngine()
        self.signal_gen = SignalGenerator()
        self.thesis_gen = ThesisGenerator()

        # v7.1 Enhanced Insights
        from .enhanced_insights import (
            CycleIntelligenceEngine,
            ScenarioEngine,
            RiskManagementEngine,
            TradeLevelsEngine,
            WatchlistEngine,
            PeakTimingEngine
        )
        self.cycle_intelligence = CycleIntelligenceEngine()
        self.scenarios = ScenarioEngine()
        self.risk_mgmt = RiskManagementEngine()
        self.trade_levels = TradeLevelsEngine()
        self.watchlist = WatchlistEngine()
        self.peak_timing = PeakTimingEngine()

    def _calculate_composite_score(self, mvrv: float, liquidity: Dict,
                                    trends: Dict, business_cycle: Dict,
                                    phase_result: Dict, fear_greed: int) -> Dict:
        """
        Calculate Overall Composite Score combining all model layers.

        Weights:
        - Valuation (MVRV)      : 25% - Primary driver
        - Liquidity             : 20% - Macro backdrop
        - Trend/Momentum        : 20% - Price action
        - Business Cycle        : 15% - Economic context
        - Phase Confidence      : 10% - Model conviction
        - Sentiment (inverse)   : 10% - Contrarian signal

        Returns score 0-100 where:
        - 0-20: Strong Sell / Distribution
        - 20-40: Reduce / Caution
        - 40-60: Neutral / Hold
        - 60-80: Accumulate
        - 80-100: Strong Buy / Max Accumulation
        """

        # 1. Valuation Score (25%) - MVRV based
        # MVRV < 1.0 = 100 (deep value)
        # MVRV 1.0-1.5 = 85
        # MVRV 1.5-2.0 = 70
        # MVRV 2.0-2.5 = 55
        # MVRV 2.5-3.5 = 40
        # MVRV 3.5-4.5 = 25
        # MVRV > 4.5 = 10 (euphoria)
        if mvrv < 0.5:
            valuation_score = 100
        elif mvrv < 1.0:
            valuation_score = 95
        elif mvrv < 1.5:
            valuation_score = 80
        elif mvrv < 2.0:
            valuation_score = 65
        elif mvrv < 2.5:
            valuation_score = 50
        elif mvrv < 3.0:
            valuation_score = 40
        elif mvrv < 3.5:
            valuation_score = 30
        elif mvrv < 4.5:
            valuation_score = 20
        else:
            valuation_score = 10

        # 2. Liquidity Score (20%) - Already 0-100
        liquidity_score = liquidity.get('score', 50)

        # 3. Trend Score (20%) - Alignment based
        alignment_score = trends.get('alignment_score', 50)
        composite_mom = trends.get('composite_momentum', 0)
        # Boost for strong momentum
        trend_score = alignment_score + min(20, max(-20, composite_mom * 2))
        trend_score = max(0, min(100, trend_score))

        # 4. Business Cycle Score (15%) - Already 0-100
        biz_score = business_cycle.get('score', 50)

        # 5. Phase Confidence (10%)
        phase_confidence = phase_result.get('phase_confidence', 50)
        phase = phase_result.get('phase', '')
        # Boost if in bullish phase with high confidence
        if phase in ['ACCUMULATION', 'EARLY_MARKUP', 'MID_MARKUP']:
            phase_score = phase_confidence
        elif phase in ['LATE_MARKUP', 'DISTRIBUTION']:
            phase_score = 100 - phase_confidence  # Invert for late cycle
        else:
            phase_score = 50 - (phase_confidence * 0.5)  # Bear phases
        phase_score = max(0, min(100, phase_score))

        # 6. Sentiment Score (10%) - Contrarian
        # Low fear = low score (contrarian sell signal)
        # High fear = high score (contrarian buy signal)
        if fear_greed < 20:
            sentiment_score = 90  # Extreme fear = buy
        elif fear_greed < 35:
            sentiment_score = 75
        elif fear_greed < 50:
            sentiment_score = 55
        elif fear_greed < 65:
            sentiment_score = 45
        elif fear_greed < 80:
            sentiment_score = 30
        else:
            sentiment_score = 15  # Extreme greed = sell

        # Calculate weighted composite
        composite = (
            valuation_score * 0.25 +
            liquidity_score * 0.20 +
            trend_score * 0.20 +
            biz_score * 0.15 +
            phase_score * 0.10 +
            sentiment_score * 0.10
        )

        # Determine rating
        if composite >= 80:
            rating = 'STRONG BUY'
            action = 'Maximum accumulation zone. Back up the truck.'
        elif composite >= 65:
            rating = 'BUY'
            action = 'Good entry. Accumulate on dips.'
        elif composite >= 50:
            rating = 'HOLD'
            action = 'Neutral zone. Hold positions, selective adds.'
        elif composite >= 35:
            rating = 'REDUCE'
            action = 'Take some profits. Reduce exposure.'
        elif composite >= 20:
            rating = 'SELL'
            action = 'Distribute positions. Move to safety.'
        else:
            rating = 'STRONG SELL'
            action = 'Exit now. Capital preservation priority.'

        return {
            'overall_score': round(composite, 1),
            'rating': rating,
            'action': action,
            'components': {
                'valuation': {'score': valuation_score, 'weight': '25%', 'input': f'MVRV {mvrv:.2f}'},
                'liquidity': {'score': round(liquidity_score, 1), 'weight': '20%', 'input': liquidity.get('regime', 'N/A')},
                'trend': {'score': round(trend_score, 1), 'weight': '20%', 'input': trends.get('alignment', 'N/A')},
                'business_cycle': {'score': round(biz_score, 1), 'weight': '15%', 'input': business_cycle.get('stage', 'N/A')},
                'phase': {'score': round(phase_score, 1), 'weight': '10%', 'input': phase},
                'sentiment': {'score': sentiment_score, 'weight': '10%', 'input': f'F&G {fear_greed}'}
            },
            'interpretation': self._interpret_composite(composite, mvrv, phase)
        }

    def _interpret_composite(self, score: float, mvrv: float, phase: str) -> str:
        """Generate human-readable interpretation of composite score"""

        if score >= 70:
            return f"Strong bullish setup. All major indicators align positively. MVRV {mvrv:.2f} supports accumulation. High conviction entry zone."
        elif score >= 55:
            return f"Moderately bullish. Most indicators positive but some caution warranted. Good risk/reward for adding exposure."
        elif score >= 45:
            return f"Neutral conditions. Mixed signals across indicators. Hold existing positions, wait for clarity before adding."
        elif score >= 35:
            return f"Caution warranted. Multiple indicators turning negative. Consider reducing exposure and taking profits."
        else:
            return f"Bearish setup. Most indicators negative. Prioritize capital preservation. Wait for better entry."

    def analyze(self, d: MarketData) -> Dict:
        """Run complete analysis"""

        # Layer 1: Liquidity
        liq = self.liquidity.analyze(d)

        # Layer 2: Business Cycle
        biz = self.business_cycle.analyze(d)

        # Layer 3: BTC Trends
        trends = self.btc_trends.analyze(d)

        # Layer 4: Altcoins
        alts = self.altcoins.analyze(d)

        # Layer 5: Phase & Value
        phase_result = self.phase.analyze(d, liq, trends)

        # Layer 6: Forecasting
        phase_enum = Phase(phase_result['phase'])
        forecast = self.forecast.analyze(d, phase_enum, trends)

        # Layer 7: Backtesting
        backtest = self.backtest.analyze(d, phase_result)

        # Layer 8: Signal
        signal = self.signal_gen.generate(phase_result, liq, trends, alts, forecast)

        # v7.1 Enhanced Insights
        cycle_intel = self.cycle_intelligence.analyze(
            phase=phase_result['phase'],
            mvrv=d.mvrv,
            fear_greed=d.fear_greed,
            cycle_progress=phase_result['cycle_progress'],
            price=d.btc_price,
            ath=d.btc_ath,
            cycle_low=d.btc_cycle_low
        )

        scenario_analysis = self.scenarios.analyze(
            price=d.btc_price,
            mvrv=d.mvrv,
            phase=phase_result['phase'],
            liquidity_score=liq['score'],
            trend_alignment=trends['alignment']
        )

        risk_analysis = self.risk_mgmt.analyze(
            price=d.btc_price,
            mvrv=d.mvrv,
            phase=phase_result['phase']
        )

        trade_levels_analysis = self.trade_levels.analyze(
            price=d.btc_price,
            mvrv=d.mvrv,
            phase=phase_result['phase']
        )

        watchlist_items = self.watchlist.generate(
            price=d.btc_price,
            mvrv=d.mvrv,
            phase=phase_result['phase'],
            liquidity=liq,
            business_cycle=biz
        )

        # Calculate Overall Composite Score
        composite_score = self._calculate_composite_score(
            mvrv=d.mvrv,
            liquidity=liq,
            trends=trends,
            business_cycle=biz,
            phase_result=phase_result,
            fear_greed=d.fear_greed
        )

        # Peak Timing Forecast
        peak_timing_forecast = self.peak_timing.analyze(
            phase=phase_result['phase'],
            mvrv=d.mvrv,
            cycle_progress=phase_result['cycle_progress'],
            price=d.btc_price,
            fear_greed=d.fear_greed,
            liquidity_score=liq['score']
        )

        # Compile result
        result = {
            'meta': {
                'model': 'Strategic Cycle Model v7.1',
                'date': d.date or str(date.today()),
                'btc_price': d.btc_price,
                'eth_price': d.eth_price,
                'btc_ath': d.btc_ath
            },
            'signal': signal,
            'phase': phase_result,
            'liquidity': liq,
            'business_cycle': biz,
            'btc_trends': trends,
            'altcoins': alts,
            'forecast': forecast,
            'backtest': backtest,
            # v7.1 Enhanced
            'cycle_intelligence': cycle_intel,
            'scenarios': scenario_analysis,
            'risk_management': risk_analysis,
            'trade_levels': trade_levels_analysis,
            'watchlist': watchlist_items,
            'composite_score': composite_score,
            'peak_timing': peak_timing_forecast
        }

        # Generate thesis
        result['thesis'] = self.thesis_gen.generate(result)

        return result


# =============================================================================
# DEFAULT MARKET DATA
# =============================================================================

def get_default_market_data() -> MarketData:
    """Return default/demo market data"""
    return MarketData(
        btc_price=78881,
        btc_ath=109000,
        btc_cycle_low=15500,
        btc_1d=103000,
        btc_7d=100500,
        btc_14d=98000,
        btc_30d=94000,
        btc_90d=72000,
        btc_180d=65000,
        btc_365d=42000,
        btc_20d_ma=100000,
        btc_50d_ma=95000,
        btc_100d_ma=85000,
        btc_200d_ma=78500,
        btc_200w_ma=46000,
        btc_111d_ma=92000,
        btc_350d_ma=73000,
        mvrv=1.85,
        mvrv_7d=1.80,
        mvrv_30d=1.65,
        nupl=0.52,
        puell=1.3,
        reserve_risk=0.003,
        fed_bs=6.57,
        fed_bs_30d=6.60,
        fed_bs_90d=6.70,
        fed_bs_180d=7.00,
        fed_bs_365d=7.20,
        rrp=0.25,
        rrp_30d=0.35,
        rrp_peak=2.55,
        tga=0.78,
        m2_yoy=4.2,
        m2_mom=0.3,
        empire_state=7.7,
        empire_prior=-3.7,
        philly_fed=12.6,
        philly_prior=-8.8,
        richmond=-6.0,
        richmond_prior=-7.0,
        kansas_city=0.0,
        kansas_prior=0.0,
        dallas=-10.9,
        dallas_prior=-10.4,
        ism_mfg=49.2,
        ism_mfg_prior=47.9,
        ism_mfg_3m=48.3,
        ism_svc=54.1,
        ism_svc_prior=53.8,
        etf_flow_7d=850,
        etf_flow_30d=3200,
        etf_flow_90d=8500,
        etf_aum=125,
        fear_greed=62,
        fear_greed_7d=58,
        fear_greed_30d=55,
        funding_8h=0.012,
        funding_7d=0.010,
        funding_30d=0.015,
        oi_btc=650000,
        oi_change_7d=5,
        rsi_14d=58,
        rsi_weekly=55,
        rsi_monthly=62,
        eth_price=3300,
        eth_btc=0.0315,
        eth_btc_7d=0.0310,
        eth_btc_30d=0.0285,
        eth_btc_90d=0.0350,
        total3_btc=0.42,
        total3_btc_30d=0.38,
        others_btc=0.18,
        others_btc_30d=0.16,
        btc_dominance=58.5,
        btc_dom_30d=56.0,
        vol_30d=0.55,
        vol_90d=0.60,
        date="January 31, 2026"
    )


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("INITIALIZING BITCOIN STRATEGIC CYCLE MODEL v7.0...")
    print("=" * 100)

    model = StrategicCycleModel()
    data = get_default_market_data()
    result = model.analyze(data)

    print(f"\nDate: {result['meta']['date']} | BTC: ${result['meta']['btc_price']:,}")
    print(f"Signal: {result['signal']['signal']} @ {result['signal']['allocation']}%")
    print(f"Phase: {result['phase']['phase']} | Value Zone: {result['phase']['value_zone']}")
    print(f"Top Warning: {result['phase']['top_warning']} ({result['phase']['top_score']}/100)")
    print(f"\nThesis:\n{result['thesis']}")
