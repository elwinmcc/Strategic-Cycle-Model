#!/usr/bin/env python3
"""
===============================================================================
BTC ECONOMETRIC MODEL v7.6 — 12-Layer Scoring Engine
===============================================================================

Data Sources:
  - CoinGlass API v4 (Startup plan) — derivatives, on-chain, ETF, options
  - FRED API — macro/credit/cycle indicators

Zero manual inputs. Zero estimated data.
===============================================================================
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime


# =============================================================================
# MODEL INPUTS
# =============================================================================

@dataclass
class ModelInputs:
    """All inputs required by the BTC Model v7.6."""
    # Price & Market
    btc_price: float = 0.0
    btc_ath: float = 126080.0
    drawdown_pct: float = 0.0
    btc_market_cap: float = 0.0
    btc_dominance: float = 0.0

    # On-Chain
    mvrv: float = 0.0
    realized_price: float = 0.0
    sth_realized_price: float = 0.0
    lth_realized_price: float = 0.0
    nupl: float = 0.0

    # Sentiment
    fear_greed: int = 50
    fear_greed_label: str = "Neutral"
    coinbase_premium: float = 0.0

    # Derivatives
    funding_rate: float = 0.0
    oi_total: float = 0.0
    oi_change_24h_pct: float = 0.0
    long_short_ratio: float = 1.0
    liquidation_24h: float = 0.0
    futures_basis: float = 0.0

    # Options
    put_call_ratio: float = 0.0
    options_oi: float = 0.0
    max_pain: float = 0.0

    # ETF
    etf_flow_daily: float = 0.0
    etf_flow_weekly: float = 0.0
    etf_cumulative: float = 0.0
    eth_etf_flow_daily: float = 0.0
    eth_etf_cumulative: float = 0.0

    # Macro (FRED)
    hy_oas: float = 0.0
    yield_curve_2s10s: float = 0.0
    initial_claims: float = 0.0
    anfci: float = 0.0
    fed_bs: float = 0.0
    rrp: float = 0.0
    tga: float = 0.0

    # Technical
    rsi_daily: float = 50.0
    price_30d_ago: float = 0.0

    # Energy
    wti_price: float = 0.0

    # Global
    global_m2_growth: float = 0.0

    # ETH
    eth_price: float = 0.0
    eth_btc: float = 0.0

    # Data quality tracking
    sources: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "btc_price": self.btc_price,
            "btc_ath": self.btc_ath,
            "drawdown_pct": self.drawdown_pct,
            "btc_market_cap": self.btc_market_cap,
            "btc_dominance": self.btc_dominance,
            "mvrv": self.mvrv,
            "realized_price": self.realized_price,
            "sth_realized_price": self.sth_realized_price,
            "lth_realized_price": self.lth_realized_price,
            "nupl": self.nupl,
            "fear_greed": self.fear_greed,
            "fear_greed_label": self.fear_greed_label,
            "coinbase_premium": self.coinbase_premium,
            "funding_rate": self.funding_rate,
            "oi_total": self.oi_total,
            "oi_change_24h_pct": self.oi_change_24h_pct,
            "long_short_ratio": self.long_short_ratio,
            "liquidation_24h": self.liquidation_24h,
            "futures_basis": self.futures_basis,
            "put_call_ratio": self.put_call_ratio,
            "options_oi": self.options_oi,
            "max_pain": self.max_pain,
            "etf_flow_daily": self.etf_flow_daily,
            "etf_flow_weekly": self.etf_flow_weekly,
            "etf_cumulative": self.etf_cumulative,
            "eth_etf_flow_daily": self.eth_etf_flow_daily,
            "eth_etf_cumulative": self.eth_etf_cumulative,
            "hy_oas": self.hy_oas,
            "yield_curve_2s10s": self.yield_curve_2s10s,
            "initial_claims": self.initial_claims,
            "anfci": self.anfci,
            "fed_bs": self.fed_bs,
            "rrp": self.rrp,
            "tga": self.tga,
            "rsi_daily": self.rsi_daily,
            "price_30d_ago": self.price_30d_ago,
            "wti_price": self.wti_price,
            "global_m2_growth": self.global_m2_growth,
            "eth_price": self.eth_price,
            "eth_btc": self.eth_btc,
            "sources": self.sources,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# LAYER WEIGHTS
# =============================================================================

LAYER_WEIGHTS = {
    "institutional":       0.25,
    "leverage_fragility":  0.15,
    "derivatives":         0.12,
    "mvrv":                0.12,
    "cycle_phase":         0.10,
    "global_liquidity":    0.08,
    "options_sentiment":   0.06,
    "credit":              0.05,
    "macro_liquidity":     0.03,
    "support":             0.02,
    "momentum":            0.01,
    "sentiment":           0.01,
}


# =============================================================================
# SCORING UTILITIES
# =============================================================================

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def interp(value, breakpoints):
    """Linear interpolation between breakpoints [(val, score), ...]."""
    breakpoints = sorted(breakpoints, key=lambda x: x[0])
    if value <= breakpoints[0][0]:
        return breakpoints[0][1]
    if value >= breakpoints[-1][0]:
        return breakpoints[-1][1]
    for i in range(len(breakpoints) - 1):
        x0, y0 = breakpoints[i]
        x1, y1 = breakpoints[i + 1]
        if x0 <= value <= x1:
            t = (value - x0) / (x1 - x0) if x1 != x0 else 0
            return y0 + t * (y1 - y0)
    return 50


# =============================================================================
# 12-LAYER SCORING ENGINE
# =============================================================================

def score_all_layers(inp: ModelInputs) -> Tuple[Dict[str, dict], str]:
    """Score all 12 layers from model inputs. Returns (layers, macro_phase)."""
    layers = {}

    # -- 1. INSTITUTIONAL (25%) --
    wf = inp.etf_flow_weekly / 1e6 if abs(inp.etf_flow_weekly) > 1e5 else inp.etf_flow_weekly
    etf_score = interp(wf, [(-500, 15), (-100, 35), (0, 50), (100, 65), (500, 80), (1000, 92)])
    prem_adj = 3 if inp.coinbase_premium > 0.5 else -3 if inp.coinbase_premium < -0.5 else 0
    inst = clamp(etf_score + prem_adj)
    layers["institutional"] = {
        "score": round(inst), "weight": 0.25,
        "contribution": round(inst * 0.25, 2),
        "reasoning": f"ETF weekly flow: ${wf:+.0f}M -> base {etf_score:.0f}. Coinbase premium {inp.coinbase_premium:+.2f}% -> adj {prem_adj:+d}.",
    }

    # -- 2. LEVERAGE FRAGILITY (15%) --
    fr_score = interp(inp.funding_rate * 100, [
        (-0.05, 90), (-0.02, 75), (0, 60), (0.02, 50), (0.05, 35), (0.1, 15)
    ])
    ls_adj = -5 if inp.long_short_ratio > 2.0 else 5 if inp.long_short_ratio < 0.8 else 0
    lev = clamp(fr_score + ls_adj)
    layers["leverage_fragility"] = {
        "score": round(lev), "weight": 0.15,
        "contribution": round(lev * 0.15, 2),
        "reasoning": f"Funding {inp.funding_rate*100:.4f}% -> {fr_score:.0f}. L/S ratio {inp.long_short_ratio:.2f} -> adj {ls_adj:+d}.",
    }

    # -- 3. DERIVATIVES (12%) --
    basis_score = interp(inp.futures_basis, [
        (-5, 80), (0, 65), (5, 55), (10, 45), (20, 30), (30, 15)
    ])
    deriv = clamp(0.5 * basis_score + 0.5 * fr_score)
    layers["derivatives"] = {
        "score": round(deriv), "weight": 0.12,
        "contribution": round(deriv * 0.12, 2),
        "reasoning": f"Basis {inp.futures_basis:.1f}% -> {basis_score:.0f}. Funding component -> {fr_score:.0f}. Composite: {deriv:.0f}.",
    }

    # -- 4. MVRV (12%) --
    mvrv_score = interp(inp.mvrv, [
        (0.5, 98), (0.8, 95), (1.0, 85), (1.2, 70), (1.5, 55),
        (2.0, 40), (2.5, 25), (3.0, 15), (3.7, 5)
    ])
    layers["mvrv"] = {
        "score": round(mvrv_score), "weight": 0.12,
        "contribution": round(mvrv_score * 0.12, 2),
        "reasoning": f"MVRV {inp.mvrv:.3f} -> score {mvrv_score:.0f}. Realized price ${inp.realized_price:,.0f}.",
    }

    # -- 5. CYCLE PHASE (10%) --
    anfci_score = interp(inp.anfci, [(-0.8, 90), (-0.5, 75), (-0.2, 60), (0, 50), (0.2, 35), (0.5, 15)])
    yc_score = interp(inp.yield_curve_2s10s, [(-1.0, 15), (-0.5, 30), (0, 50), (0.5, 65), (1.0, 75), (2.0, 85)])
    claims_k = inp.initial_claims / 1000
    claims_score = interp(claims_k, [(180, 70), (210, 65), (250, 55), (300, 45), (350, 30), (450, 15)])

    cycle = clamp(0.40 * anfci_score + 0.30 * claims_score + 0.30 * yc_score)

    if inp.anfci < -0.3 and inp.yield_curve_2s10s > 0 and claims_k < 250:
        phase = "EARLY_RECOVERY"
    elif inp.anfci < 0 and inp.yield_curve_2s10s > -0.5:
        phase = "EXPANSION"
    elif inp.anfci > 0.2 or claims_k > 300:
        phase = "CONTRACTION"
    else:
        phase = "LATE_CYCLE"

    layers["cycle_phase"] = {
        "score": round(cycle), "weight": 0.10,
        "contribution": round(cycle * 0.10, 2),
        "reasoning": f"ANFCI {inp.anfci:.2f} -> {anfci_score:.0f}. 2s10s {inp.yield_curve_2s10s:+.2f}% -> {yc_score:.0f}. Claims {claims_k:.0f}K -> {claims_score:.0f}. Phase: {phase}.",
        "phase": phase,
    }

    # -- 6. GLOBAL LIQUIDITY (8%) --
    net_liq = inp.fed_bs - inp.rrp - inp.tga if (inp.fed_bs and inp.rrp is not None and inp.tga is not None) else 0
    nl_score = interp(net_liq / 1000, [
        (4.5, 20), (5.0, 35), (5.5, 50), (6.0, 65), (6.5, 75), (7.0, 85)
    ]) if net_liq > 0 else 50
    m2_adj = 5 if inp.global_m2_growth > 5 else -5 if inp.global_m2_growth < 0 else 0
    gl = clamp(nl_score + m2_adj)
    layers["global_liquidity"] = {
        "score": round(gl), "weight": 0.08,
        "contribution": round(gl * 0.08, 2),
        "reasoning": f"Net liquidity ${net_liq:,.0f}B -> {nl_score:.0f}. M2 growth {inp.global_m2_growth:.1f}% -> adj {m2_adj:+d}.",
    }

    # -- 7. OPTIONS SENTIMENT (6%) --
    pc_score = interp(inp.put_call_ratio, [
        (0.3, 20), (0.5, 35), (0.7, 50), (0.9, 60), (1.1, 70), (1.3, 78), (1.5, 85)
    ])
    layers["options_sentiment"] = {
        "score": round(pc_score), "weight": 0.06,
        "contribution": round(pc_score * 0.06, 2),
        "reasoning": f"Put/Call {inp.put_call_ratio:.2f} -> {pc_score:.0f} (contrarian: high P/C = bullish). Max pain ${inp.max_pain:,.0f}.",
    }

    # -- 8. CREDIT (5%) --
    credit = interp(inp.hy_oas, [
        (2.0, 90), (2.5, 82), (3.0, 72), (3.5, 62), (4.0, 50), (5.0, 35), (6.0, 20), (8.0, 10)
    ])
    layers["credit"] = {
        "score": round(credit), "weight": 0.05,
        "contribution": round(credit * 0.05, 2),
        "reasoning": f"HY OAS {inp.hy_oas:.2f}% -> {credit:.0f}. {'Orderly' if inp.hy_oas < 4.5 else 'Stress'}.",
    }

    # -- 9. MACRO-LIQUIDITY (3%) --
    macro = clamp(0.5 * anfci_score + 0.5 * yc_score)
    layers["macro_liquidity"] = {
        "score": round(macro), "weight": 0.03,
        "contribution": round(macro * 0.03, 2),
        "reasoning": f"ANFCI {inp.anfci:.2f} + 2s10s {inp.yield_curve_2s10s:+.2f}% composite -> {macro:.0f}.",
    }

    # -- 10. SUPPORT (2%) --
    if inp.realized_price > 0 and inp.btc_price > 0:
        buffer = (inp.btc_price - inp.realized_price) / inp.btc_price * 100
        support = interp(buffer, [(-10, 90), (0, 70), (10, 55), (20, 45), (30, 40), (50, 35)])
    else:
        support = 50
        buffer = 0
    layers["support"] = {
        "score": round(support), "weight": 0.02,
        "contribution": round(support * 0.02, 2),
        "reasoning": f"Price ${inp.btc_price:,.0f}, realized ${inp.realized_price:,.0f}. Buffer {buffer:.1f}%.",
    }

    # -- 11. MOMENTUM (1%) --
    if inp.price_30d_ago > 0 and inp.btc_price > 0:
        roc_30d = (inp.btc_price - inp.price_30d_ago) / inp.price_30d_ago * 100
    else:
        roc_30d = 0
    mom = interp(roc_30d, [
        (-40, 85), (-20, 70), (-10, 60), (0, 50), (10, 45), (30, 30), (50, 15)
    ])
    layers["momentum"] = {
        "score": round(mom), "weight": 0.01,
        "contribution": round(mom * 0.01, 2),
        "reasoning": f"30d ROC {roc_30d:+.1f}% -> {mom:.0f}.",
    }

    # -- 12. SENTIMENT (1%) --
    sent = interp(inp.fear_greed, [
        (0, 98), (10, 92), (20, 78), (30, 60), (50, 50), (70, 35), (85, 18), (100, 5)
    ])
    layers["sentiment"] = {
        "score": round(sent), "weight": 0.01,
        "contribution": round(sent * 0.01, 2),
        "reasoning": f"F&G {inp.fear_greed} ({inp.fear_greed_label}) -> {sent:.0f} (contrarian).",
    }

    return layers, phase


# =============================================================================
# SIGNAL GENERATION
# =============================================================================

def generate_signal(layers: dict, inputs: ModelInputs, phase: str) -> dict:
    """Calculate final score, adjustments, and signal."""
    base_score = sum(l["contribution"] for l in layers.values())

    phase_adj = 10 if phase == "EARLY_RECOVERY" else 0
    mvrv_adj = 4 if 1.0 <= inputs.mvrv <= 1.5 else 0
    fear_adj = 4 if inputs.fear_greed < 20 else 0

    final = base_score + phase_adj + mvrv_adj + fear_adj

    if final >= 85:
        signal = "AGGRESSIVE_BUY"
    elif final >= 75:
        signal = "STRONG_BUY"
    elif final >= 65:
        signal = "BUY"
    elif final >= 55:
        signal = "ACCUMULATE"
    elif final >= 45:
        signal = "HOLD"
    elif final >= 35:
        signal = "REDUCE"
    elif final >= 25:
        signal = "SELL"
    else:
        signal = "STRONG_SELL"

    # BTC cycle phase from MVRV
    if inputs.mvrv < 0.8:
        btc_cycle = "CAPITULATION"
    elif inputs.mvrv < 1.0:
        btc_cycle = "DEEP_ACCUMULATION"
    elif inputs.mvrv < 1.5:
        btc_cycle = "ACCUMULATION"
    elif inputs.mvrv < 2.0:
        btc_cycle = "EARLY_BULL"
    elif inputs.mvrv < 2.5:
        btc_cycle = "MID_BULL"
    elif inputs.mvrv < 3.0:
        btc_cycle = "LATE_BULL"
    else:
        btc_cycle = "EUPHORIA"

    # Allocation percentage
    if final >= 85:
        allocation = 100
    elif final >= 75:
        allocation = 90
    elif final >= 65:
        allocation = 75
    elif final >= 55:
        allocation = 60
    elif final >= 45:
        allocation = 40
    elif final >= 35:
        allocation = 25
    elif final >= 25:
        allocation = 10
    else:
        allocation = 0

    # Confidence
    confidence = "HIGH" if final >= 70 or final <= 30 else "MEDIUM" if final >= 60 or final <= 40 else "LOW"

    # Build rationale
    top_layers = sorted(layers.items(), key=lambda x: x[1]["contribution"], reverse=True)[:3]
    rationale = [f"{name}: {info['score']}/100 ({info['weight']*100:.0f}%)" for name, info in top_layers]

    return {
        "base_score": round(base_score, 2),
        "phase_adjustment": phase_adj,
        "mvrv_adjustment": mvrv_adj,
        "fear_adjustment": fear_adj,
        "final_score": round(final, 2),
        "signal": signal,
        "macro_phase": phase,
        "btc_cycle": btc_cycle,
        "allocation": allocation,
        "confidence": confidence,
        "rationale": rationale,
    }


# =============================================================================
# FULL ANALYSIS
# =============================================================================

def run_analysis(inputs: ModelInputs) -> dict:
    """Run full v7.6 analysis and return structured result for the web dashboard."""
    layers, phase = score_all_layers(inputs)
    result = generate_signal(layers, inputs, phase)

    # Net liquidity
    net_liq = inputs.fed_bs - inputs.rrp - inputs.tga if inputs.fed_bs else 0

    return {
        "model_version": "7.6",
        "timestamp": inputs.timestamp or datetime.now().isoformat(),
        "signal": result,
        "layers": layers,
        "inputs": inputs.to_dict(),
        "market_data": {
            "btc_price": inputs.btc_price,
            "drawdown_pct": inputs.drawdown_pct,
            "mvrv": inputs.mvrv,
            "realized_price": inputs.realized_price,
            "sth_realized_price": inputs.sth_realized_price,
            "lth_realized_price": inputs.lth_realized_price,
            "nupl": inputs.nupl,
            "fear_greed": inputs.fear_greed,
            "fear_greed_label": inputs.fear_greed_label,
            "hy_oas": inputs.hy_oas,
            "yield_curve_2s10s": inputs.yield_curve_2s10s,
            "initial_claims": inputs.initial_claims,
            "anfci": inputs.anfci,
            "etf_flow_daily": inputs.etf_flow_daily,
            "etf_flow_weekly": inputs.etf_flow_weekly,
            "etf_cumulative": inputs.etf_cumulative,
            "funding_rate": inputs.funding_rate,
            "put_call_ratio": inputs.put_call_ratio,
            "options_oi": inputs.options_oi,
            "max_pain": inputs.max_pain,
            "btc_dominance": inputs.btc_dominance,
            "eth_btc": inputs.eth_btc,
            "eth_price": inputs.eth_price,
            "coinbase_premium": inputs.coinbase_premium,
            "long_short_ratio": inputs.long_short_ratio,
            "liquidation_24h": inputs.liquidation_24h,
            "futures_basis": inputs.futures_basis,
            "net_liquidity_b": net_liq,
            "fed_bs": inputs.fed_bs,
            "rrp": inputs.rrp,
            "tga": inputs.tga,
            "global_m2_growth": inputs.global_m2_growth,
            "wti_price": inputs.wti_price,
        },
        "sources": inputs.sources,
        "warnings": inputs.warnings,
    }
