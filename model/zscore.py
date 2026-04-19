"""
Z-Score Scoring Utilities for BTC Econometric Model v7.7

Converts raw indicator values to 0-100 layer scores via z-score normalization
and logistic mapping.  Requires a historical time series to compute the
distribution parameters (mean, stdev).

Functions:
  z_score()        — Standard z-score: (value - mean) / stdev
  z_to_score()     — Logistic mapping: z-score -> 0-100 layer score
  percentile_rank() — Empirical percentile rank within a series
"""

from __future__ import annotations

import math
import statistics
from typing import List, Optional


def z_score(value: float, history: List[float]) -> Optional[float]:
    """Compute z-score of *value* relative to *history*.

    Returns None if history has fewer than 30 observations or zero stdev.
    """
    if len(history) < 30:
        return None
    mean = statistics.mean(history)
    sd = statistics.stdev(history)
    if sd == 0:
        return None
    return (value - mean) / sd


def z_to_score(z: float, k: float = 0.6, invert: bool = False) -> float:
    """Map a z-score to a 0-100 layer score via logistic function.

    score = 100 / (1 + exp(k * z))        when invert=True
    score = 100 / (1 + exp(-k * z))       when invert=False

    invert=True means higher raw values are bearish (MVRV, HY OAS, funding,
    ANFCI).  invert=False means higher raw values are bullish (ETF flows).

    k controls steepness: 0.6 = moderate, 0.8 = steep, 0.4 = gentle.
    """
    if invert:
        exponent = k * z
    else:
        exponent = -k * z
    exponent = max(-20, min(20, exponent))
    return 100.0 / (1.0 + math.exp(exponent))


def percentile_rank(value: float, history: List[float]) -> Optional[float]:
    """Empirical percentile rank of *value* within *history* (0-100).

    Returns None if history has fewer than 30 observations.
    """
    if len(history) < 30:
        return None
    n = len(history)
    below = sum(1 for v in history if v < value)
    equal = sum(1 for v in history if v == value)
    return (below + 0.5 * equal) / n * 100.0


def score_with_zscore(
    value: float,
    history: List[float],
    k: float = 0.6,
    invert: bool = False,
) -> dict:
    """Convenience: compute z-score, percentile, and layer score in one call.

    Returns dict with keys: z, percentile, score, method, history_len.
    Falls back to None values if history is insufficient.
    """
    z = z_score(value, history)
    pct = percentile_rank(value, history)

    if z is not None:
        score = round(z_to_score(z, k=k, invert=invert), 1)
    else:
        score = None

    return {
        "z": round(z, 3) if z is not None else None,
        "percentile": round(pct, 1) if pct is not None else None,
        "score": score,
        "method": "zscore" if z is not None else "fallback",
        "history_len": len(history),
    }
