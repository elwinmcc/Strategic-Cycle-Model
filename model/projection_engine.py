"""
===============================================================================
BTC PROJECTION ENGINE — Multi-Method Price Projections
===============================================================================

Four methodologically distinct projection methods, triangulated into a
composite.  Designed for the v7.7 Cycle Intelligence Engine.

Theoretical basis:
  - BTC is treated as a liquidity-driven macro asset (Pal / Gromen / Alden /
    Zeberg framework).
  - NO halving-cycle logic anywhere.  All projections are derived from the
    model's existing data inputs (CoinGlass v4 + FRED).
  - Every hardcoded return / magnitude table is THEORETICAL — pending walk-
    forward backtest validation.

Methods:
  1. MVRV-Anchored            (primary — highest weight)
  2. Score-to-Forward-Return   (model signal → expected range)
  3. Liquidity Beta            (Pal: M2 growth × phase-adjusted β)
  4. Catalyst-Weighted         (probability × magnitude from easing mechanisms)
===============================================================================
"""

from __future__ import annotations

import math
import statistics
from typing import Dict, List, Optional, Tuple

from model.btc_model_v76 import ModelInputs


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

HORIZONS = ["30d", "90d", "180d", "365d", "540d", "730d"]
HORIZON_DAYS = {"30d": 30, "90d": 90, "180d": 180, "365d": 365, "540d": 540, "730d": 730}

METHOD_WEIGHTS = {
    "mvrv_anchored":    0.40,
    "score_to_return":  0.25,
    "liquidity_beta":   0.15,
    "catalyst_weighted": 0.20,
}

DISCLAIMERS = [
    "Methods not walk-forward backtested",
    "Projections compound uncertainty over time",
    "Assumes no regime breaks (war, sovereign crisis, regulatory action)",
    "Score-to-return map is theoretical pending backtest validation",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation: a when t=0, b when t=1."""
    return a + (b - a) * max(0.0, min(1.0, t))


def _compound(price: float, annual_rate_pct: float, days: int) -> float:
    """Compound *price* at *annual_rate_pct* for *days*."""
    if annual_rate_pct == 0:
        return price
    return price * (1 + annual_rate_pct / 100) ** (days / 365.0)


def _fmt_k(v: float) -> str:
    """$120,345 → '$120K'."""
    return f"${v / 1000:.0f}K"


def _safe_round(v: Optional[float]) -> Optional[int]:
    """Round to int, None-safe."""
    return round(v) if v is not None else None


# ─────────────────────────────────────────────────────────────────────────────
# Method 1 — MVRV-Anchored (Primary)
# ─────────────────────────────────────────────────────────────────────────────

# Annualised realized-price growth rates by BTC cycle phase {bear, base, bull}
RP_GROWTH = {
    "CAPITULATION":        (5,  5,   5),
    "DEEP_ACCUMULATION":   (5,  5,   5),
    "ACCUMULATION":        (25, 35,  50),
    "EARLY_BULL":          (40, 55,  75),
    "MID_BULL":            (55, 75, 100),
    "LATE_BULL":           (40, 55,  70),
    "EUPHORIA":            (20, 30,  40),
}

# Projected MVRV target at the *end* of each phase {bear, base, bull}
MVRV_TARGETS = {
    "ACCUMULATION":        (1.2, 1.5, 1.8),
    "EARLY_BULL":          (1.7, 2.0, 2.3),
    "MID_BULL":            (2.2, 2.5, 2.8),
    "LATE_BULL":           (2.7, 3.0, 3.3),
    "EUPHORIA":            (3.3, 3.7, 4.0),
}

# Phase order and typical durations (months) — derived from liquidity-driven
# cycle model, NOT halving periodicity.
PHASE_ORDER = ["ACCUMULATION", "EARLY_BULL", "MID_BULL", "LATE_BULL", "EUPHORIA"]
PHASE_DURATIONS_MO = {
    "ACCUMULATION": 6,
    "EARLY_BULL":   4,
    "MID_BULL":     5,
    "LATE_BULL":    4,
    "EUPHORIA":     3,
}


def _phase_at_horizon(current_phase: str, months_into_phase: float, horizon_days: int) -> str:
    """Estimate which BTC cycle phase applies at *horizon_days* in the future."""
    if current_phase not in PHASE_ORDER:
        return current_phase

    idx = PHASE_ORDER.index(current_phase)
    remaining_mo = max(0, PHASE_DURATIONS_MO.get(current_phase, 4) - months_into_phase)
    horizon_mo = horizon_days / 30.44
    elapsed = 0.0

    # Walk forward through phases
    elapsed += remaining_mo
    while elapsed < horizon_mo and idx < len(PHASE_ORDER) - 1:
        idx += 1
        elapsed += PHASE_DURATIONS_MO.get(PHASE_ORDER[idx], 4)

    return PHASE_ORDER[idx]


def _months_into_current_phase(mvrv: float, phase: str) -> float:
    """Rough estimate of how far through the current phase we are based on MVRV."""
    targets = MVRV_TARGETS.get(phase)
    if not targets:
        return 0.0
    # Use base target; measure fraction of range covered
    prev_phase_idx = max(0, PHASE_ORDER.index(phase) - 1) if phase in PHASE_ORDER else 0
    prev_target = MVRV_TARGETS.get(PHASE_ORDER[prev_phase_idx], (1.0, 1.0, 1.0))[1]
    base_target = targets[1]
    if base_target <= prev_target:
        return 0.0
    frac = max(0.0, min(1.0, (mvrv - prev_target) / (base_target - prev_target)))
    duration = PHASE_DURATIONS_MO.get(phase, 4)
    return frac * duration


def mvrv_anchored(inp: ModelInputs, cycle: dict, projected_phases: list) -> Optional[dict]:
    """Method 1: Price = MVRV × Realized Price, projected forward independently.

    Both terms are grown at phase-appropriate rates, with MVRV interpolated
    linearly toward the phase target at each horizon.

    Returns None if MVRV or Realized Price data is missing.
    """
    if inp.mvrv <= 0 or inp.realized_price <= 0:
        return None

    current_mvrv = inp.mvrv
    current_rp = inp.realized_price
    btc_phase = cycle.get("btc_phase", "ACCUMULATION")

    months_in = _months_into_current_phase(current_mvrv, btc_phase)

    result = {}
    for h in HORIZONS:
        days = HORIZON_DAYS[h]
        future_phase = _phase_at_horizon(btc_phase, months_in, days)

        # Realized Price growth
        rp_rates = RP_GROWTH.get(future_phase, RP_GROWTH["ACCUMULATION"])
        rp_bear = _compound(current_rp, rp_rates[0], days)
        rp_base = _compound(current_rp, rp_rates[1], days)
        rp_bull = _compound(current_rp, rp_rates[2], days)

        # MVRV target interpolation
        targets = MVRV_TARGETS.get(future_phase, MVRV_TARGETS["ACCUMULATION"])
        # Fraction of time to target: from current into the projected phase
        phase_dur_days = PHASE_DURATIONS_MO.get(future_phase, 4) * 30.44
        # How far *into* the future phase this horizon lands
        t = min(1.0, days / max(phase_dur_days, 1))

        mvrv_bear = _lerp(current_mvrv, targets[0], t)
        mvrv_base = _lerp(current_mvrv, targets[1], t)
        mvrv_bull = _lerp(current_mvrv, targets[2], t)

        bear_price = max(0, round(mvrv_bear * rp_bear))
        base_price = max(0, round(mvrv_base * rp_base))
        bull_price = max(0, round(mvrv_bull * rp_bull))

        result[h] = {
            "bear": bear_price,
            "base": base_price,
            "bull": bull_price,
            "notes": (
                f"Phase {future_phase}: RP ${rp_base:,.0f} "
                f"(+{rp_rates[1]}%/yr), MVRV {mvrv_base:.2f}"
            ),
        }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Method 2 — Score-to-Forward-Return Mapping
# ─────────────────────────────────────────────────────────────────────────────

# THEORETICAL — pending backtest validation.
# Maps composite score → (low%, high%) expected forward return per horizon.
SCORE_RETURN_MAP = {
    85: {"30d": (8, 15),   "90d": (25, 50),  "180d": (60, 120),  "365d": (100, 250)},
    75: {"30d": (5, 10),   "90d": (15, 30),  "180d": (30, 60),   "365d": (60, 150)},
    65: {"30d": (2, 6),    "90d": (8, 20),   "180d": (15, 35),   "365d": (30, 80)},
    55: {"30d": (0, 4),    "90d": (3, 12),   "180d": (5, 20),    "365d": (10, 40)},
    45: {"30d": (-3, 3),   "90d": (-8, 8),   "180d": (-15, 15),  "365d": (-20, 20)},
    35: {"30d": (-6, 0),   "90d": (-15, -3), "180d": (-30, -10), "365d": (-50, -15)},
    25: {"30d": (-10, -3), "90d": (-25, -8), "180d": (-45, -20), "365d": (-65, -30)},
}

_SCORE_KEYS = sorted(SCORE_RETURN_MAP.keys())


def _interpolate_return_range(score: float, horizon: str) -> Optional[Tuple[float, float]]:
    """Linearly interpolate between score buckets for a given horizon."""
    if horizon not in ("30d", "90d", "180d", "365d"):
        return None
    if score >= _SCORE_KEYS[-1]:
        return SCORE_RETURN_MAP[_SCORE_KEYS[-1]][horizon]
    if score <= _SCORE_KEYS[0]:
        return SCORE_RETURN_MAP[_SCORE_KEYS[0]][horizon]

    for i in range(len(_SCORE_KEYS) - 1):
        lo, hi = _SCORE_KEYS[i], _SCORE_KEYS[i + 1]
        if lo <= score <= hi:
            t = (score - lo) / (hi - lo)
            lo_range = SCORE_RETURN_MAP[lo][horizon]
            hi_range = SCORE_RETURN_MAP[hi][horizon]
            low_pct = _lerp(lo_range[0], hi_range[0], t)
            high_pct = _lerp(lo_range[1], hi_range[1], t)
            return (low_pct, high_pct)
    return None


def score_to_return(inp: ModelInputs, signal: dict) -> Optional[dict]:
    """Method 2: Map final composite score to expected forward return ranges.

    THEORETICAL — the score-to-return mapping has not been walk-forward
    backtested.  Returns are interpolated linearly between score buckets.
    Beyond 365d, compound decay (40% per additional year) is applied to
    prevent extrapolation runaway.
    """
    score = signal.get("final_score", 0)
    btc = inp.btc_price
    if btc <= 0 or score <= 0:
        return None

    # Base horizons (have explicit map entries)
    mapped_horizons = ["30d", "90d", "180d", "365d"]
    raw_ranges: Dict[str, Tuple[float, float]] = {}
    for h in mapped_horizons:
        rng = _interpolate_return_range(score, h)
        if rng is not None:
            raw_ranges[h] = rng

    if not raw_ranges:
        return None

    result = {}
    for h in HORIZONS:
        days = HORIZON_DAYS[h]
        if h in raw_ranges:
            lo, hi = raw_ranges[h]
        else:
            # Extend beyond 365d using compound decay on the 365d range.
            # Return rates shrink 40% per additional year.
            base_range = raw_ranges.get("365d")
            if base_range is None:
                continue
            extra_years = (days - 365) / 365.0
            decay = 0.60 ** extra_years  # 40% shrinkage per extra year
            lo = base_range[0] + (base_range[0] * extra_years * decay)
            hi = base_range[1] + (base_range[1] * extra_years * decay)

        bear_price = max(0, round(btc * (1 + lo / 100)))
        bull_price = max(0, round(btc * (1 + hi / 100)))
        base_price = max(0, round(btc * (1 + (lo + hi) / 200)))

        result[h] = {
            "bear": bear_price,
            "base": base_price,
            "bull": bull_price,
            "notes": f"Score {score:.1f} -> {lo:+.1f}% / {hi:+.1f}% (theoretical)",
        }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Method 3 — Liquidity Beta (Pal Framework)
# ─────────────────────────────────────────────────────────────────────────────

# Phase-adjusted beta (BTC return ÷ M2 growth).
# THEORETICAL — pending backtest validation.
PHASE_BETA = {
    "CAPITULATION":      4.0,
    "DEEP_ACCUMULATION": 4.5,
    "ACCUMULATION":      5.0,
    "EARLY_BULL":        7.0,
    "MID_BULL":          8.0,
    "LATE_BULL":         6.0,
    "EUPHORIA":          4.0,
}


def liquidity_beta(inp: ModelInputs, cycle: dict) -> Optional[dict]:
    """Method 3: Expected Return = M2_Growth × Beta with ~70-100 day lag.

    Pal framework — BTC as a high-beta liquidity play.  Uses
    inp.global_m2_growth as annualised rate; quarterly rate = annual / 4.
    Compounds quarterly out to each horizon.

    Returns None if M2 data is unavailable.
    """
    if inp.global_m2_growth == 0:
        return None

    btc = inp.btc_price
    if btc <= 0:
        return None

    phase = cycle.get("btc_phase", "ACCUMULATION")
    base_beta = PHASE_BETA.get(phase, 5.0)

    # Quarterly M2 return (M2 growth is provided as annualised %)
    m2_qtr = inp.global_m2_growth / 4.0

    result = {}
    for h in HORIZONS:
        days = HORIZON_DAYS[h]
        # Number of quarterly compounding periods, with ~80-day lag offset
        effective_days = max(0, days - 80)
        quarters = effective_days / 91.25

        if quarters <= 0:
            # Within the lag window — current beta implies near-flat
            bear_ret = m2_qtr * base_beta * 0.7 * (days / 91.25)
            base_ret = m2_qtr * base_beta * 1.0 * (days / 91.25)
            bull_ret = m2_qtr * base_beta * 1.3 * (days / 91.25)
        else:
            qtr_return_bear = m2_qtr * base_beta * 0.7 / 100
            qtr_return_base = m2_qtr * base_beta * 1.0 / 100
            qtr_return_bull = m2_qtr * base_beta * 1.3 / 100

            bear_ret = ((1 + qtr_return_bear) ** quarters - 1) * 100
            base_ret = ((1 + qtr_return_base) ** quarters - 1) * 100
            bull_ret = ((1 + qtr_return_bull) ** quarters - 1) * 100

        bear_price = max(0, round(btc * (1 + bear_ret / 100)))
        base_price = max(0, round(btc * (1 + base_ret / 100)))
        bull_price = max(0, round(btc * (1 + bull_ret / 100)))

        result[h] = {
            "bear": bear_price,
            "base": base_price,
            "bull": bull_price,
            "notes": (
                f"M2 {inp.global_m2_growth:.1f}%/yr × β{base_beta:.1f} "
                f"over {quarters:.1f}Q eff"
            ),
        }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Method 4 — Catalyst-Weighted Probability × Magnitude
# ─────────────────────────────────────────────────────────────────────────────

# Price magnitude impact per catalyst (thousands USD), (low, high).
# THEORETICAL — pending backtest validation.
CATALYST_MAGNITUDES = {
    "Treasury stealth":      (3, 8),
    "Bank deregulation":     (10, 20),
    "Rate cuts":             (15, 30),
    "Regulatory catalysts":  (10, 25),
    "Yield curve management": (20, 40),
    "Full QE":               (50, 100),
}

# Fraction of total 12-18 month impact captured at each horizon.
HORIZON_CAPTURE = {
    "30d":  0.05,
    "90d":  0.15,
    "180d": 0.30,
    "365d": 0.70,
    "540d": 1.00,
    "730d": 1.00,
}


def _match_catalyst(mechanism_name: str) -> Optional[str]:
    """Match easing mechanism name to CATALYST_MAGNITUDES key by substring."""
    lower = mechanism_name.lower()
    for key in CATALYST_MAGNITUDES:
        if key.lower() in lower:
            return key
    return None


def catalyst_weighted(inp: ModelInputs, intelligence: dict) -> Optional[dict]:
    """Method 4: Sum probability-weighted price impacts from easing mechanisms.

    Each mechanism's probability × magnitude gives an expected-value
    contribution.  Summed across all mechanisms, then allocated to horizons
    by a capture fraction (6m = 30%, 12m = 70%, 18m+ = 100%).
    """
    easing = intelligence.get("easing_mechanisms", [])
    btc = inp.btc_price
    if btc <= 0 or not easing:
        return None

    total_ev_lo = 0.0
    total_ev_hi = 0.0

    for em in easing:
        name = em.get("mechanism", "")
        prob = em.get("probability", 0) / 100.0
        key = _match_catalyst(name)
        if key is None:
            continue
        mag_lo, mag_hi = CATALYST_MAGNITUDES[key]
        total_ev_lo += mag_lo * 1000 * prob
        total_ev_hi += mag_hi * 1000 * prob

    if total_ev_lo == 0 and total_ev_hi == 0:
        return None

    result = {}
    for h in HORIZONS:
        capture = HORIZON_CAPTURE.get(h, 1.0)
        bear_price = max(0, round(btc + total_ev_lo * capture))
        bull_price = max(0, round(btc + total_ev_hi * capture))
        base_price = max(0, round(btc + (total_ev_lo + total_ev_hi) / 2 * capture))

        result[h] = {
            "bear": bear_price,
            "base": base_price,
            "bull": bull_price,
            "notes": (
                f"EV ${total_ev_lo / 1000:.0f}K-${total_ev_hi / 1000:.0f}K "
                f"× {capture:.0%} capture"
            ),
        }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Composite Triangulation
# ─────────────────────────────────────────────────────────────────────────────

def _composite_projection(methods: Dict[str, Optional[dict]]) -> dict:
    """Triangulate across methods for each horizon.

    - Composite bear / base / bull = median of values across valid methods.
    - Convergence = stdev(base values) / median(base values) × 100.
    - Confidence tier: HIGH < 15%, MODERATE 15-30%, LOW > 30%.
    """
    composite: Dict[str, dict] = {}

    for h in HORIZONS:
        bears, bases, bulls = [], [], []
        for name, m in methods.items():
            if m is None or h not in m:
                continue
            entry = m[h]
            bears.append(entry["bear"])
            bases.append(entry["base"])
            bulls.append(entry["bull"])

        if not bases:
            continue

        med_base = statistics.median(bases)
        med_bear = statistics.median(bears)
        med_bull = statistics.median(bulls)

        if len(bases) >= 2:
            sd = statistics.stdev(bases)
            convergence = (sd / med_base * 100) if med_base > 0 else 999.0
        else:
            convergence = 999.0  # single method — no convergence data

        if convergence < 15:
            confidence = "HIGH_CONFIDENCE"
        elif convergence < 30:
            confidence = "MODERATE_CONFIDENCE"
        else:
            confidence = "LOW_CONFIDENCE"

        composite[h] = {
            "bear": round(med_bear),
            "base": round(med_base),
            "bull": round(med_bull),
            "confidence": confidence,
            "convergence_pct": round(convergence, 1),
        }

    return composite


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_projections(
    inp: ModelInputs,
    cycle: dict,
    intelligence: dict,
    signal: dict,
) -> dict:
    """Generate multi-method Bitcoin price projections and composite.

    Called from run_analysis() after intelligence is built.  Each method is
    independently testable; any can return None (missing data) without
    breaking the composite.

    Args:
        inp:          Live ModelInputs from data_service.
        cycle:        Cycle assessment from score_all_layers().
        intelligence: Output of generate_cycle_intelligence().
        signal:       Output of generate_signal() (includes final_score).

    Returns:
        Full projections dict ready for JSON serialisation.
    """
    projected_phases = intelligence.get("projected_phases", [])

    methods = {
        "mvrv_anchored":    mvrv_anchored(inp, cycle, projected_phases),
        "score_to_return":  score_to_return(inp, signal),
        "liquidity_beta":   liquidity_beta(inp, cycle),
        "catalyst_weighted": catalyst_weighted(inp, intelligence),
    }

    composite = _composite_projection(methods)

    # Assumptions snapshot (for transparency on the dashboard)
    phase = cycle.get("btc_phase", "ACCUMULATION")
    rp_rates = RP_GROWTH.get(phase, RP_GROWTH["ACCUMULATION"])
    beta_used = PHASE_BETA.get(phase, 5.0)
    mvrv_target = MVRV_TARGETS.get(phase, (0, 0, 0))

    return {
        "horizons": HORIZONS,
        "methods": methods,
        "composite": composite,
        "method_weights": METHOD_WEIGHTS,
        "disclaimers": DISCLAIMERS,
        "assumptions": {
            "current_mvrv": round(inp.mvrv, 3) if inp.mvrv else 0,
            "current_rp": round(inp.realized_price) if inp.realized_price else 0,
            "current_phase": phase,
            "projected_rp_growth_annual": rp_rates[1],
            "projected_peak_mvrv": mvrv_target[1],
            "beta_used": beta_used,
        },
    }
