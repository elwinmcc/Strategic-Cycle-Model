#!/usr/bin/env python3
"""
===============================================================================
BTC ECONOMETRIC MODEL v7.7 — 14-Layer Cycle Intelligence Engine
===============================================================================

Upgrade from v7.6:
  - NEW: Liquidity Regime Layer (8%) — QT/neutral/QE detection
  - NEW: Fed Policy Transition Layer (5%) — Chair regime + rate path
  - NEW: Oil/Energy Risk Layer (3%) — Inflation constraint on Fed
  - NEW: Cycle Intelligence Engine — phase detection + timeline projection
  - NEW: Impulse Probability Score — timing overlay
  - IMPROVED: Institutional split (Flow 15% + Structure 10%)
  - IMPROVED: Nonlinear Sentiment scoring (extreme-only signal)
  - IMPROVED: Realized Price Band system for Support
  - REMOVED: Macro-Liquidity (3%) — merged into Liquidity Regime
  - REMOVED: Momentum (1%) — low signal-to-noise

Data: CoinGlass API v4 + FRED API (via data_service.py)
===============================================================================
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

from model.btc_model_v76 import ModelInputs, clamp, interp
from model.projection_engine import generate_projections
from model.zscore import score_with_zscore


# =============================================================================
# v7.7 LAYER WEIGHTS (14 layers, sum = 1.00)
# =============================================================================

LAYER_WEIGHTS_V77 = {
    "institutional_flow":    0.15,
    "institutional_struct":  0.10,
    "leverage_fragility":    0.13,
    "derivatives":           0.10,
    "mvrv":                  0.12,
    "liquidity_regime":      0.08,
    "cycle_phase":           0.05,
    "fed_transition":        0.05,
    "global_liquidity":      0.05,
    "options_sentiment":     0.06,
    "credit":                0.05,
    "oil_energy":            0.03,
    "support":               0.02,
    "sentiment":             0.01,
}


# =============================================================================
# 14-LAYER SCORING ENGINE
# =============================================================================

def score_all_layers(inp: ModelInputs) -> Tuple[Dict[str, dict], dict]:
    """Score all 14 layers. Returns (layers_dict, cycle_assessment)."""
    layers = {}

    # -- 1. INSTITUTIONAL FLOW (15%) -- z-score scoring with interp fallback
    wf = inp.etf_flow_weekly / 1e6 if abs(inp.etf_flow_weekly) > 1e5 else inp.etf_flow_weekly
    etf_hist = inp.zscore_histories.get("etf_weekly", [])
    etf_zdata = score_with_zscore(wf, etf_hist[-365:], k=0.6, invert=False)
    if etf_zdata["score"] is not None:
        etf_s = etf_zdata["score"]
    else:
        # LEGACY fallback: raw threshold interpolation
        etf_s = interp(wf, [(-500, 15), (-100, 35), (0, 50), (100, 65), (500, 80), (1000, 92)])
    layers["institutional_flow"] = {
        "score": round(etf_s), "weight": 0.15,
        "contribution": round(etf_s * 0.15, 2),
        "reasoning": f"ETF weekly ${wf:+.0f}M -> {etf_s:.0f}.",
        "zscore": etf_zdata,
    }

    # -- 2. INSTITUTIONAL STRUCTURE (10%) --
    cum_score = 70 if inp.etf_cumulative > 50e9 else 55 if inp.etf_cumulative > 30e9 else 40
    prem_adj = 3 if inp.coinbase_premium > 0.5 else -3 if inp.coinbase_premium < -0.5 else 0
    struct = clamp(cum_score + prem_adj)
    layers["institutional_struct"] = {
        "score": round(struct), "weight": 0.10,
        "contribution": round(struct * 0.10, 2),
        "reasoning": f"Cumulative ${inp.etf_cumulative/1e9:.1f}B -> {cum_score}. CB premium {inp.coinbase_premium:+.2f}% adj {prem_adj:+d}.",
    }

    # -- 3. LEVERAGE FRAGILITY (13%) -- z-score scoring with interp fallback
    fr_hist = inp.zscore_histories.get("funding_rate", [])
    fr_zdata = score_with_zscore(inp.funding_rate, fr_hist[-365:], k=0.6, invert=True)
    if fr_zdata["score"] is not None:
        fr_s = fr_zdata["score"]
    else:
        # LEGACY fallback: raw threshold interpolation
        fr_s = interp(inp.funding_rate * 100, [(-5, 90), (-2, 75), (0, 60), (2, 50), (5, 35), (10, 15)])
    ls_adj = -5 if inp.long_short_ratio > 2.0 else 5 if inp.long_short_ratio < 0.8 else 0
    lev = clamp(fr_s + ls_adj)
    layers["leverage_fragility"] = {
        "score": round(lev), "weight": 0.13,
        "contribution": round(lev * 0.13, 2),
        "reasoning": f"Funding {inp.funding_rate*100:.4f}% -> {fr_s:.0f}. L/S {inp.long_short_ratio:.2f} adj {ls_adj:+d}.",
        "zscore": fr_zdata,
    }

    # -- 4. DERIVATIVES (10%) --
    basis_s = interp(inp.futures_basis, [(-5, 80), (0, 65), (5, 55), (10, 45), (20, 30), (30, 15)])
    deriv = clamp(0.5 * basis_s + 0.5 * fr_s)
    layers["derivatives"] = {
        "score": round(deriv), "weight": 0.10,
        "contribution": round(deriv * 0.10, 2),
        "reasoning": f"Basis {inp.futures_basis:.1f}% -> {basis_s:.0f}. Funding component {fr_s:.0f}.",
    }

    # -- 5. MVRV (12%) -- z-score scoring with interp fallback
    mvrv_hist = inp.zscore_histories.get("mvrv", [])
    mvrv_zdata = score_with_zscore(inp.mvrv, mvrv_hist[-730:], k=0.6, invert=True)
    if mvrv_zdata["score"] is not None:
        mvrv_s = mvrv_zdata["score"]
    else:
        # LEGACY fallback: raw threshold interpolation
        mvrv_s = interp(inp.mvrv, [
            (0.5, 98), (0.8, 95), (1.0, 85), (1.2, 70), (1.5, 55),
            (2.0, 40), (2.5, 25), (3.0, 15), (3.7, 5)
        ])
    layers["mvrv"] = {
        "score": round(mvrv_s), "weight": 0.12,
        "contribution": round(mvrv_s * 0.12, 2),
        "reasoning": f"MVRV {inp.mvrv:.3f} -> {mvrv_s:.0f}. RP ${inp.realized_price:,.0f}. STH ${inp.sth_realized_price:,.0f}, LTH ${inp.lth_realized_price:,.0f}.",
        "zscore": mvrv_zdata,
    }

    # -- 6. LIQUIDITY REGIME (8%) --
    # Data-driven regime detection from Fed balance sheet level and net liquidity
    net_liq = inp.fed_bs - inp.rrp - inp.tga if inp.fed_bs else 0

    # Regime detection: purely from observable balance sheet size (trillions)
    bs_t = inp.fed_bs / 1000 if inp.fed_bs else 0
    if bs_t < 6.5:
        regime_s = 35
        regime_label = "TIGHTENING"
    elif bs_t < 7.0:
        regime_s = 50
        regime_label = "NEUTRAL"
    elif bs_t < 7.5:
        regime_s = 65
        regime_label = "ACCOMMODATIVE"
    else:
        regime_s = 80
        regime_label = "EXPANSIONARY"

    # Net liquidity adjustment: RRP drawdown or TGA changes affect available liquidity
    if net_liq > 0:
        nl_t = net_liq / 1000
        nl_adj = interp(nl_t, [(4.5, -10), (5.0, -5), (5.5, 0), (6.0, 5), (6.5, 10), (7.0, 15)])
    else:
        nl_adj = 0

    liq_regime = clamp(regime_s + nl_adj)
    layers["liquidity_regime"] = {
        "score": round(liq_regime), "weight": 0.08,
        "contribution": round(liq_regime * 0.08, 2),
        "reasoning": f"Regime: {regime_label}. Fed BS ${inp.fed_bs:,.0f}B ({bs_t:.2f}T). Net liq adj {nl_adj:+.0f}.",
        "regime": regime_label,
    }

    # -- 7. CYCLE PHASE (5%) -- ANFCI uses z-score scoring with interp fallback
    anfci_hist = inp.zscore_histories.get("anfci", [])
    anfci_zdata = score_with_zscore(inp.anfci, anfci_hist[-1825:], k=0.6, invert=True)
    if anfci_zdata["score"] is not None:
        anfci_s = anfci_zdata["score"]
    else:
        # LEGACY fallback: raw threshold interpolation
        anfci_s = interp(inp.anfci, [(-0.8, 90), (-0.5, 75), (-0.2, 60), (0, 50), (0.2, 35), (0.5, 15)])
    yc_s = interp(inp.yield_curve_2s10s, [(-1.0, 15), (-0.5, 30), (0, 50), (0.5, 65), (1.0, 75), (2.0, 85)])
    claims_k = inp.initial_claims / 1000
    claims_s = interp(claims_k, [(180, 70), (210, 65), (250, 55), (300, 45), (350, 30), (450, 15)])
    cycle = clamp(0.40 * anfci_s + 0.30 * claims_s + 0.30 * yc_s)

    if inp.anfci < -0.3 and inp.yield_curve_2s10s > 0 and claims_k < 250:
        biz_phase = "EARLY_RECOVERY"
    elif inp.anfci < 0 and inp.yield_curve_2s10s > -0.5:
        biz_phase = "EXPANSION"
    elif inp.anfci > 0.2 or claims_k > 300:
        biz_phase = "CONTRACTION"
    else:
        biz_phase = "LATE_CYCLE"

    layers["cycle_phase"] = {
        "score": round(cycle), "weight": 0.05,
        "contribution": round(cycle * 0.05, 2),
        "reasoning": f"ANFCI {inp.anfci:.2f}->{anfci_s:.0f}. 2s10s {inp.yield_curve_2s10s:+.2f}%->{yc_s:.0f}. Claims {claims_k:.0f}K->{claims_s:.0f}. Phase: {biz_phase}.",
        "phase": biz_phase,
        "zscore_anfci": anfci_zdata,
    }

    # -- 8. FED TRANSITION (5%) --
    # Chair transition is a calendar fact; policy stance derived from data
    now = datetime.now()
    if now >= datetime(2026, 5, 15):
        chair = "Warsh"
    else:
        chair = "Powell"

    # Chair regime inferred from observable financial conditions, not assumed
    if inp.anfci < -0.3:
        chair_regime = "ACCOMMODATIVE"
        chair_s = 65
    elif inp.anfci < 0:
        chair_regime = "NEUTRAL_LOOSE"
        chair_s = 55
    elif inp.anfci < 0.2:
        chair_regime = "NEUTRAL"
        chair_s = 50
    else:
        chair_regime = "RESTRICTIVE"
        chair_s = 35

    # Rate path: derived from yield curve slope (market pricing of future rates)
    # Steeper curve = market pricing more cuts; inverted = market pricing tightness
    yc_rate_s = interp(inp.yield_curve_2s10s, [(-1.0, 20), (-0.5, 30), (0, 50), (0.5, 65), (1.0, 75), (2.0, 85)])

    # Credit conditions as proxy for policy effectiveness
    credit_cond_s = interp(inp.hy_oas, [
        (2.0, 70), (3.0, 60), (4.0, 50), (5.0, 35), (6.0, 20)
    ]) if inp.hy_oas > 0 else 50

    fed_trans = clamp(0.40 * chair_s + 0.30 * yc_rate_s + 0.30 * credit_cond_s)
    layers["fed_transition"] = {
        "score": round(fed_trans), "weight": 0.05,
        "contribution": round(fed_trans * 0.05, 2),
        "reasoning": f"Chair: {chair}. Conditions: {chair_regime} (ANFCI {inp.anfci:.2f})->{chair_s}. Yield curve {inp.yield_curve_2s10s:+.2f}%->{yc_rate_s:.0f}. Credit cond->{credit_cond_s:.0f}.",
    }

    # -- 9. GLOBAL LIQUIDITY (5%) --
    nl_s = interp(net_liq / 1000, [
        (4.5, 20), (5.0, 35), (5.5, 50), (6.0, 65), (6.5, 75), (7.0, 85)
    ]) if net_liq > 0 else 50
    m2_adj = 5 if inp.global_m2_growth > 5 else -5 if inp.global_m2_growth < 0 else 0
    gl = clamp(nl_s + m2_adj)
    layers["global_liquidity"] = {
        "score": round(gl), "weight": 0.05,
        "contribution": round(gl * 0.05, 2),
        "reasoning": f"Net liq ${net_liq:,.0f}B -> {nl_s:.0f}. M2 growth {inp.global_m2_growth:.1f}% adj {m2_adj:+d}.",
    }

    # -- 10. OPTIONS SENTIMENT (6%) --
    pc_s = interp(inp.put_call_ratio, [
        (0.3, 20), (0.5, 35), (0.7, 50), (0.9, 60), (1.1, 70), (1.3, 78), (1.5, 85)
    ])
    layers["options_sentiment"] = {
        "score": round(pc_s), "weight": 0.06,
        "contribution": round(pc_s * 0.06, 2),
        "reasoning": f"P/C {inp.put_call_ratio:.2f} -> {pc_s:.0f} (contrarian). Max pain ${inp.max_pain:,.0f}.",
    }

    # -- 11. CREDIT (5%) -- z-score scoring with interp fallback
    hy_hist = inp.zscore_histories.get("hy_oas", [])
    hy_zdata = score_with_zscore(inp.hy_oas, hy_hist[-1825:], k=0.6, invert=True)
    if hy_zdata["score"] is not None:
        credit_s = hy_zdata["score"]
    else:
        # LEGACY fallback: raw threshold interpolation
        credit_s = interp(inp.hy_oas, [
            (2.0, 90), (2.5, 82), (3.0, 72), (3.5, 62), (4.0, 50), (5.0, 35), (6.0, 20), (8.0, 10)
        ])
    layers["credit"] = {
        "score": round(credit_s), "weight": 0.05,
        "contribution": round(credit_s * 0.05, 2),
        "reasoning": f"HY OAS {inp.hy_oas:.2f}% -> {credit_s:.0f}. {'Orderly' if inp.hy_oas < 4.5 else 'Stress'}.",
        "zscore": hy_zdata,
    }

    # -- 12. OIL/ENERGY RISK (3%) --
    oil_s = interp(inp.wti_price, [
        (40, 90), (60, 80), (70, 70), (80, 60), (90, 45), (100, 30), (120, 15), (150, 5)
    ]) if inp.wti_price > 0 else 60  # Default neutral if no data
    layers["oil_energy"] = {
        "score": round(oil_s), "weight": 0.03,
        "contribution": round(oil_s * 0.03, 2),
        "reasoning": f"WTI ${inp.wti_price:.0f} -> {oil_s:.0f}. {'Tailwind' if inp.wti_price < 70 else 'Neutral' if inp.wti_price < 90 else 'Headwind'}." if inp.wti_price > 0 else "No WTI data -> neutral 60.",
    }

    # -- 13. SUPPORT (2%) — Realized Price Bands --
    if inp.btc_price > 0 and inp.sth_realized_price > 0 and inp.lth_realized_price > 0:
        if inp.btc_price > inp.sth_realized_price:
            sup_s = 35  # Everyone in profit = distribution risk
        elif inp.btc_price > inp.realized_price:
            sup_s = 55  # Between overall and STH RP
        elif inp.btc_price > inp.lth_realized_price:
            sup_s = 75  # Deep value
        else:
            sup_s = 95  # Below LTH RP = capitulation
    elif inp.realized_price > 0 and inp.btc_price > 0:
        buffer = (inp.btc_price - inp.realized_price) / inp.btc_price * 100
        sup_s = interp(buffer, [(-10, 90), (0, 70), (10, 55), (20, 45), (30, 40), (50, 35)])
    else:
        sup_s = 50
    layers["support"] = {
        "score": round(sup_s), "weight": 0.02,
        "contribution": round(sup_s * 0.02, 2),
        "reasoning": f"Price ${inp.btc_price:,.0f}. STH RP ${inp.sth_realized_price:,.0f}, LTH RP ${inp.lth_realized_price:,.0f}, RP ${inp.realized_price:,.0f}.",
    }

    # -- 14. SENTIMENT (1%) — Nonlinear extreme-only --
    if inp.fear_greed <= 10:
        sent_s = 95
    elif inp.fear_greed <= 20:
        sent_s = 82
    elif inp.fear_greed <= 30:
        sent_s = 62
    elif inp.fear_greed <= 70:
        sent_s = 50  # Flat zone — no signal
    elif inp.fear_greed <= 85:
        sent_s = 30
    elif inp.fear_greed <= 95:
        sent_s = 15
    else:
        sent_s = 5
    layers["sentiment"] = {
        "score": round(sent_s), "weight": 0.01,
        "contribution": round(sent_s * 0.01, 2),
        "reasoning": f"F&G {inp.fear_greed} ({inp.fear_greed_label}) -> {sent_s} (nonlinear, extreme-only).",
    }

    # -- BTC Cycle Phase --
    if inp.mvrv < 0.8:
        btc_phase = "CAPITULATION"
    elif inp.mvrv < 1.0:
        btc_phase = "DEEP_ACCUMULATION"
    elif inp.mvrv < 1.5:
        btc_phase = "ACCUMULATION"
    elif inp.mvrv < 2.0:
        btc_phase = "EARLY_BULL"
    elif inp.mvrv < 2.5:
        btc_phase = "MID_BULL"
    elif inp.mvrv < 3.0:
        btc_phase = "LATE_BULL"
    else:
        btc_phase = "EUPHORIA"

    cycle_assessment = {
        "liquidity_regime": regime_label,
        "business_phase": biz_phase,
        "btc_phase": btc_phase,
        "fed_chair": chair,
        "chair_regime": chair_regime,
        "net_liquidity_b": net_liq,
        "fed_bs_t": bs_t,
    }

    return layers, cycle_assessment


# =============================================================================
# SIGNAL GENERATION + IMPULSE PROBABILITY
# =============================================================================

def generate_signal(layers: dict, inp: ModelInputs, cycle: dict) -> dict:
    """Calculate final score, adjustments, signal, and impulse probability."""
    base = sum(l["contribution"] for l in layers.values())

    phase_adj = 10 if cycle["business_phase"] == "EARLY_RECOVERY" else 0
    mvrv_adj = 4 if 1.0 <= inp.mvrv <= 1.5 else 0
    fear_adj = 4 if inp.fear_greed < 20 else 0

    final = base + phase_adj + mvrv_adj + fear_adj

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

    # Allocation
    if final >= 85: allocation = 100
    elif final >= 75: allocation = 90
    elif final >= 65: allocation = 75
    elif final >= 55: allocation = 60
    elif final >= 45: allocation = 40
    elif final >= 35: allocation = 25
    elif final >= 25: allocation = 10
    else: allocation = 0

    confidence = "HIGH" if final >= 70 or final <= 30 else "MEDIUM" if final >= 60 or final <= 40 else "LOW"

    top_layers = sorted(layers.items(), key=lambda x: x[1]["contribution"], reverse=True)[:3]
    rationale = [f"{name}: {info['score']}/100 ({info['weight']*100:.0f}%)" for name, info in top_layers]

    # -- IMPULSE PROBABILITY (10 data-driven catalysts) --
    fed_bs_t = cycle.get("fed_bs_t", 0)
    catalysts = {
        "tga_drawdown": inp.tga < 500 if inp.tga > 0 else False,
        "fed_bs_expanding": fed_bs_t > 7.0,
        "conditions_loose": inp.anfci < -0.2,
        "oil_benign": inp.wti_price < 85 if inp.wti_price > 0 else False,
        "mvrv_value": 1.0 <= inp.mvrv <= 1.5,
        "sentiment_extreme": inp.fear_greed < 20,
        "etf_inflows": inp.etf_flow_weekly > 0,
        "yield_curve_positive": inp.yield_curve_2s10s > 0,
        "funding_neutral": abs(inp.funding_rate) < 0.01 if inp.funding_rate else False,
        "credit_orderly": inp.hy_oas < 4.0 if inp.hy_oas > 0 else False,
    }
    aligned = sum(1 for v in catalysts.values() if v)

    if aligned >= 9:
        imp = {"1m": 30, "3m": 55, "6m": 80, "12m": 90}
        window = "OPEN"
    elif aligned >= 8:
        imp = {"1m": 15, "3m": 35, "6m": 60, "12m": 80}
        window = "OPEN"
    elif aligned >= 6:
        imp = {"1m": 10, "3m": 30, "6m": 55, "12m": 75}
        window = "FORMING"
    elif aligned >= 4:
        imp = {"1m": 5, "3m": 15, "6m": 35, "12m": 55}
        window = "FORMING"
    else:
        imp = {"1m": 2, "3m": 8, "6m": 20, "12m": 35}
        window = "NOT_OPEN"

    return {
        "base_score": round(base, 2),
        "phase_adjustment": phase_adj,
        "mvrv_adjustment": mvrv_adj,
        "fear_adjustment": fear_adj,
        "final_score": round(final, 2),
        "signal": signal,
        "macro_phase": cycle["business_phase"],
        "btc_cycle": cycle["btc_phase"],
        "allocation": allocation,
        "confidence": confidence,
        "rationale": rationale,
        "impulse_probability": imp,
        "impulse_window": window,
        "catalysts_aligned": aligned,
        "catalysts_total": len(catalysts),
        "catalysts_detail": catalysts,
    }


# =============================================================================
# CYCLE INTELLIGENCE ENGINE
# =============================================================================

def generate_cycle_intelligence(inp: ModelInputs, cycle: dict) -> dict:
    """Data-driven cycle position, projected phases, and timing assessment.
    All assessments derived from observable market data — no thesis assumptions."""
    now = datetime.now()
    fed_bs_t = cycle.get("fed_bs_t", 0)

    position = {
        "liquidity_regime": cycle["liquidity_regime"],
        "business_cycle": cycle["business_phase"],
        "btc_cycle": cycle["btc_phase"],
        "mvrv": inp.mvrv,
        "fed_chair": cycle["fed_chair"],
        "chair_regime": cycle["chair_regime"],
        "net_liquidity_b": cycle.get("net_liquidity_b", 0),
    }

    # ── Policy condition indicators (derived from data, not assumed) ──
    # Rate cut likelihood from yield curve + financial conditions
    rate_cut_signal = "LIKELY" if inp.yield_curve_2s10s > 0.5 and inp.anfci < 0 else \
                      "POSSIBLE" if inp.yield_curve_2s10s > 0 or inp.anfci < -0.2 else \
                      "UNLIKELY"
    rate_cut_prob = 70 if rate_cut_signal == "LIKELY" else 45 if rate_cut_signal == "POSSIBLE" else 25
    if inp.wti_price > 100:
        rate_cut_prob = max(20, rate_cut_prob - 25)

    # TGA status from observable level
    tga_status = "ACTIVE" if inp.tga < 400 else "NEUTRAL" if inp.tga < 600 else "ELEVATED"
    tga_prob = 75 if inp.tga < 400 else 50 if inp.tga < 600 else 30

    # Balance sheet trajectory
    bs_status = "EXPANDING" if fed_bs_t > 7.0 else "STABLE" if fed_bs_t > 6.5 else "CONTRACTING"
    bs_prob = 70 if bs_status == "EXPANDING" else 40 if bs_status == "STABLE" else 20

    # Credit conditions indicator
    credit_status = "BENIGN" if inp.hy_oas < 3.5 else "WATCHFUL" if inp.hy_oas < 5.0 else "STRESSED"
    qe_prob = 15 if credit_status == "BENIGN" else 35 if credit_status == "WATCHFUL" else 55

    easing = [
        {"mechanism": "TGA drawdowns / Treasury operations",
         "probability": tga_prob, "impact": "Moderate",
         "timeline": f"TGA at ${inp.tga:.0f}B" if inp.tga > 0 else "No data",
         "status": tga_status},
        {"mechanism": "Fed balance sheet operations",
         "probability": bs_prob, "impact": "Strong",
         "timeline": f"BS at {fed_bs_t:.2f}T",
         "status": bs_status},
        {"mechanism": "Rate cuts",
         "probability": rate_cut_prob, "impact": "Strong",
         "timeline": f"Curve {inp.yield_curve_2s10s:+.2f}%, ANFCI {inp.anfci:.2f}",
         "status": rate_cut_signal},
        {"mechanism": "Yield curve normalization",
         "probability": 50 if inp.yield_curve_2s10s < -0.3 else 25,
         "impact": "Very strong",
         "timeline": f"2s10s at {inp.yield_curve_2s10s:+.2f}%",
         "status": "POSSIBLE" if inp.yield_curve_2s10s < -0.3 else "UNLIKELY"},
        {"mechanism": "Full QE (balance sheet expansion)",
         "probability": qe_prob, "impact": "Very strong",
         "timeline": f"Credit: {credit_status}",
         "status": "POSSIBLE" if inp.hy_oas > 5 else "UNLIKELY"},
    ]

    # ── Cycle Phases (determined by MVRV and business cycle — no hardcoded dates) ──
    btc = inp.btc_price if inp.btc_price > 0 else 70000

    if inp.mvrv < 1.0:
        current_phase = 1
    elif inp.mvrv < 1.5:
        current_phase = 2 if cycle["business_phase"] in ("EARLY_RECOVERY", "EXPANSION") else 1
    elif inp.mvrv < 2.0:
        current_phase = 3
    elif inp.mvrv < 3.0:
        current_phase = 4
    else:
        current_phase = 5

    projected_phases = [
        {
            "phase": 1,
            "name": "Accumulation",
            "timeline": "MVRV < 1.0",
            "price_range": f"${btc*0.70/1000:.0f}K - ${btc*0.90/1000:.0f}K",
            "description": "Below realized price. Deep value with elevated fear, negative/flat funding.",
            "key_signals": "MVRV < 1.0, F&G < 20, negative funding, high put/call ratio",
            "status": "ACTIVE" if current_phase == 1 else ("COMPLETED" if current_phase > 1 else "PROJECTED"),
        },
        {
            "phase": 2,
            "name": "Early Recovery",
            "timeline": "MVRV 1.0 - 1.5",
            "price_range": f"${btc*0.90/1000:.0f}K - ${btc*1.20/1000:.0f}K",
            "description": "Price above realized price. Market structure stabilizing, ETF flows recovering.",
            "key_signals": "MVRV 1.0-1.5, funding normalizing, ETF inflows resuming",
            "status": "ACTIVE" if current_phase == 2 else ("COMPLETED" if current_phase > 2 else "PROJECTED"),
        },
        {
            "phase": 3,
            "name": "Expansion / Markup",
            "timeline": "MVRV 1.5 - 2.0",
            "price_range": f"${btc*1.15/1000:.0f}K - ${btc*1.60/1000:.0f}K",
            "description": "Broad participation increasing. Positive funding, sustained institutional demand.",
            "key_signals": "MVRV 1.5-2.0, sustained positive funding, ETF weekly > $500M",
            "status": "ACTIVE" if current_phase == 3 else ("COMPLETED" if current_phase > 3 else "PROJECTED"),
        },
        {
            "phase": 4,
            "name": "Late Bull / Potential Peak",
            "timeline": "MVRV 2.0 - 3.0",
            "price_range": f"${btc*1.50/1000:.0f}K - ${btc*2.20/1000:.0f}K",
            "description": "Elevated valuation. Monitor for excessive leverage and euphoria signals.",
            "key_signals": "MVRV 2.0-3.0, elevated funding, F&G > 70",
            "status": "ACTIVE" if current_phase == 4 else ("COMPLETED" if current_phase > 4 else "PROJECTED"),
        },
        {
            "phase": 5,
            "name": "Distribution / Cycle Top",
            "timeline": "MVRV > 3.0",
            "price_range": "Monitor for exits",
            "description": "Statistical extreme valuation. Historical cycle tops occur in this range.",
            "key_signals": "MVRV > 3.0, F&G > 80, funding > 0.05%, ETF outflows",
            "status": "ACTIVE" if current_phase == 5 else "PROJECTED",
        },
    ]

    # ── Accelerators / decelerators from current data ──
    accelerators = []
    decelerators = []

    etf_wk_m = inp.etf_flow_weekly / 1e6 if abs(inp.etf_flow_weekly) > 1e5 else inp.etf_flow_weekly

    if inp.wti_price > 0 and inp.wti_price < 70:
        accelerators.append(f"Oil ${inp.wti_price:.0f} — deflationary tailwind for risk assets")
    elif inp.wti_price > 0 and inp.wti_price < 85:
        accelerators.append(f"Oil ${inp.wti_price:.0f} — benign for monetary policy")
    if inp.wti_price > 100:
        decelerators.append(f"Oil ${inp.wti_price:.0f} — inflation headwind, constrains easing")

    if inp.fear_greed < 15:
        accelerators.append(f"F&G {inp.fear_greed} — extreme fear, contrarian bullish historically")
    elif inp.fear_greed < 25:
        accelerators.append(f"F&G {inp.fear_greed} — elevated fear, contrarian signal")

    if inp.funding_rate < -0.001:
        accelerators.append(f"Funding {inp.funding_rate*100:.3f}% — shorts paying, market deleveraged")
    elif abs(inp.funding_rate) < 0.005:
        accelerators.append("Neutral funding — healthy market structure")

    if inp.mvrv > 0 and inp.mvrv < 1.5:
        accelerators.append(f"MVRV {inp.mvrv:.2f} — below historical median, value zone")

    if etf_wk_m > 200:
        accelerators.append(f"ETF weekly +${etf_wk_m:.0f}M — institutional demand positive")

    if inp.anfci < -0.3:
        accelerators.append(f"ANFCI {inp.anfci:.2f} — financial conditions loose")

    if inp.yield_curve_2s10s > 0.5:
        accelerators.append(f"Yield curve +{inp.yield_curve_2s10s:.2f}% — positive slope, easing priced in")

    if inp.anfci > 0:
        decelerators.append(f"ANFCI {inp.anfci:.2f} — tightening financial conditions")
    if inp.initial_claims > 250000:
        decelerators.append(f"Claims {inp.initial_claims/1000:.0f}K — labor market softening")
    if inp.initial_claims > 300000:
        accelerators.append(f"Claims {inp.initial_claims/1000:.0f}K — deterioration may force policy response")

    if inp.hy_oas > 4.5:
        decelerators.append(f"HY OAS {inp.hy_oas:.1f}% — credit stress")

    if inp.fear_greed > 80:
        decelerators.append(f"F&G {inp.fear_greed} — euphoria zone, distribution risk")

    if inp.funding_rate > 0.05:
        decelerators.append(f"Funding {inp.funding_rate*100:.3f}% — excessive leverage")

    if etf_wk_m < -200:
        decelerators.append(f"ETF weekly ${etf_wk_m:.0f}M — institutional outflows")

    # ── Key dated events (factual calendar, no thesis assumptions) ──
    key_events = [
        {"date": "2026-05-15", "label": "Fed Chair transition", "category": "policy"},
        {"date": "2026-06-17", "label": "FOMC meeting", "category": "policy"},
        {"date": "2026-07-29", "label": "FOMC meeting", "category": "policy"},
        {"date": "2026-09-16", "label": "FOMC meeting", "category": "policy"},
        {"date": "2026-11-03", "label": "US midterm elections", "category": "political"},
        {"date": "2026-12-15", "label": "FOMC meeting", "category": "policy"},
    ]

    return {
        "position": position,
        "easing_mechanisms": easing,
        "projected_phases": projected_phases,
        "current_phase": current_phase,
        "key_events": key_events,
        "accelerators": accelerators,
        "decelerators": decelerators,
    }


# =============================================================================
# TAIL SIGNAL DETECTION
# =============================================================================

TAIL_INTERPRETATIONS = {
    "mvrv": {
        "high": "Extreme overvaluation — historically associated with cycle tops and distribution phases",
        "low":  "Extreme undervaluation — historically associated with generational buying opportunities",
    },
    "institutional_flow": {
        "high": "Exceptional institutional demand — ETF inflows at statistical extremes",
        "low":  "Extreme institutional outflows — capitulation-level redemptions",
    },
    "leverage_fragility": {
        "high": "Extreme short positioning — historically associated with squeeze setups",
        "low":  "Extreme long leverage — historically precedes liquidation cascades",
    },
    "credit": {
        "high": "Credit spreads extremely tight — risk appetite at statistical extremes",
        "low":  "Credit stress at extreme levels — broad risk-off regime, contagion risk elevated",
    },
    "cycle_phase": {
        "high": "Financial conditions extremely loose — monetary policy highly accommodative",
        "low":  "Financial conditions extremely tight — monetary tightening at statistical extremes",
    },
}


def _extract_tail_signals(layers: dict) -> list:
    """Scan z-scored layers for |z| >= 2.5 and return structured tail signal callouts."""
    tail_signals = []

    for name, layer in layers.items():
        zdata = layer.get("zscore") or layer.get("zscore_anfci")
        if not zdata or zdata.get("z") is None:
            continue
        z = zdata["z"]
        if abs(z) < 2.5:
            continue

        interp_map = TAIL_INTERPRETATIONS.get(name, {})
        invert = name in ("mvrv", "leverage_fragility", "credit", "cycle_phase")

        if invert:
            direction = "high" if z > 0 else "low"
        else:
            direction = "high" if z > 0 else "low"

        interpretation = interp_map.get(direction, f"Statistical extreme — z={z:.2f} is a rare reading")

        label_map = {
            "mvrv": "MVRV", "institutional_flow": "ETF Flow",
            "leverage_fragility": "Funding Rate", "credit": "HY OAS",
            "cycle_phase": "ANFCI",
        }

        tail_signals.append({
            "layer": label_map.get(name, name),
            "z": round(z, 2),
            "percentile": round(zdata.get("percentile", 0), 1),
            "direction": "HIGH" if z > 0 else "LOW",
            "interpretation": interpretation,
        })

    return tail_signals


# =============================================================================
# SYNOPSIS GENERATION
# =============================================================================

def generate_synopsis(inp: ModelInputs, cycle: dict, signal: dict, intelligence: dict, layers: dict = None) -> dict:
    """Generate plain-English synopsis from observable market data. No thesis assumptions."""
    score = signal.get("final_score", 0)
    signal_name = signal.get("signal", "HOLD")
    aligned = signal.get("catalysts_aligned", 0)
    total = signal.get("catalysts_total", 10)
    current_phase = intelligence.get("current_phase", 1)

    etf_wk_m = inp.etf_flow_weekly / 1e6 if abs(inp.etf_flow_weekly) > 1e5 else inp.etf_flow_weekly

    # ── Today's catalyst: biggest single driver from current data ──
    catalyst_parts = []
    if inp.wti_price > 100:
        catalyst_parts.append(f"Oil at ${inp.wti_price:.0f} — above historical comfort zone, inflation constraint")
    elif inp.wti_price > 0 and inp.wti_price < 75:
        catalyst_parts.append(f"Oil at ${inp.wti_price:.0f} — deflationary tailwind for risk assets")

    if inp.fear_greed < 15:
        catalyst_parts.append(f"Fear & Greed at {inp.fear_greed} (extreme fear) — historically strong contrarian signal")
    elif inp.fear_greed > 80:
        catalyst_parts.append(f"Fear & Greed at {inp.fear_greed} (extreme greed) — elevated distribution risk")

    if etf_wk_m > 500:
        catalyst_parts.append(f"ETF weekly flow +${etf_wk_m:.0f}M — strong institutional demand")
    elif etf_wk_m < -500:
        catalyst_parts.append(f"ETF weekly outflow ${etf_wk_m:.0f}M — institutional distribution")

    if abs(inp.funding_rate) < 0.005 and inp.mvrv < 1.5:
        catalyst_parts.append("Neutral funding + low MVRV — deleveraged market structure")

    if not catalyst_parts:
        catalyst_parts.append(f"Market consolidating at MVRV {inp.mvrv:.2f}, F&G {inp.fear_greed}")

    todays_catalyst = ". ".join(catalyst_parts) + "."

    # ── Structural picture: data-driven narrative ──
    regime_txt = cycle.get("liquidity_regime", "NEUTRAL").replace("_", " ").lower()
    biz_txt = cycle.get("business_phase", "EXPANSION").replace("_", " ").lower()
    btc_txt = cycle.get("btc_phase", "ACCUMULATION").replace("_", " ").lower()

    structural = (
        f"The model reads {regime_txt} liquidity conditions, {biz_txt} business cycle, and {btc_txt} BTC valuation phase. "
        f"{aligned}/{total} catalysts aligned; composite score {score:.1f} ({signal_name.replace('_', ' ')}). "
    )

    layers_result = signal.get("rationale", [])
    if layers_result:
        structural += f"Top contributors: {', '.join(layers_result[:3])}. "

    phases = intelligence.get("projected_phases", [])
    active_phase = next((p for p in phases if p.get("status") == "ACTIVE"), None)
    if active_phase:
        structural += f"Current phase: {active_phase['name']} ({active_phase['timeline']})."

    # ── Risks: data-conditional only ──
    risks = []
    if inp.wti_price > 0 and inp.wti_price > 95:
        risks.append(f"Oil above ${inp.wti_price:.0f} constrains monetary easing")
    if inp.hy_oas > 4.0:
        risks.append(f"Credit stress (HY OAS {inp.hy_oas:.1f}%) — risk-off conditions developing")
    if inp.fear_greed > 80:
        risks.append(f"Euphoria (F&G {inp.fear_greed}) — elevated distribution risk")
    if inp.funding_rate > 0.03:
        risks.append(f"Excessive leverage (funding {inp.funding_rate*100:.3f}%) — liquidation risk")
    if inp.anfci > 0.2:
        risks.append(f"Tight financial conditions (ANFCI {inp.anfci:.2f}) — headwind for risk assets")
    if etf_wk_m < -500:
        risks.append(f"Sustained ETF outflows (${etf_wk_m:.0f}M/wk) — institutional demand weakening")
    if inp.mvrv > 2.5:
        risks.append(f"Elevated MVRV ({inp.mvrv:.2f}) — historically associated with distribution zones")

    # Structural tail risks (factual, not thesis-dependent)
    risks.append("Geopolitical oil supply disruption: energy price shock constrains all policy options")
    risks.append("Regulatory reversal: major market access restrictions (low probability, high impact)")

    # ── Tail signals: surface any z-scored layer with |z| >= 2.5 ──
    tail_signals = _extract_tail_signals(layers or {})

    return {
        "todays_catalyst": todays_catalyst,
        "structural_picture": structural,
        "risks_remaining": risks[:5],
        "tail_signals": tail_signals,
    }


# =============================================================================
# HISTORICAL ANALOG COMPARISON (Q4 2019)
# =============================================================================

def generate_historical_analog(inp: ModelInputs, cycle: dict) -> dict:
    """Compare current conditions to multiple historical BTC cycle periods.
    Selects best-matching analog from data, not a fixed thesis period."""

    ANALOGS = {
        "Q4 2019": {
            "label": "Q4 2019 (post-QT, pre-halving)",
            "drawdown_pct": -53, "mvrv": 1.4, "fear_greed": 24, "hy_oas": 3.5,
            "what_happened": [
                "Oct 2019: Fed repo operations began (stealth liquidity)",
                "Mar 2020: COVID crash -50%, followed by massive QE",
                "12-month lag from QT end to sustained rally",
            ],
        },
        "Q1 2016": {
            "label": "Q1 2016 (post-halving accumulation)",
            "drawdown_pct": -58, "mvrv": 1.1, "fear_greed": 18, "hy_oas": 6.0,
            "what_happened": [
                "Extended accumulation at depressed valuations",
                "Slow grind higher for 18 months before parabolic move",
                "Institutional entry minimal — retail-driven cycle",
            ],
        },
        "Q3 2022": {
            "label": "Q3 2022 (post-LUNA/FTX capitulation)",
            "drawdown_pct": -72, "mvrv": 0.8, "fear_greed": 10, "hy_oas": 4.8,
            "what_happened": [
                "Extended bottom formation at MVRV < 1.0",
                "ETF approval catalyst drove new demand source",
                "Recovery took 12+ months to surpass previous levels",
            ],
        },
        "Q4 2017": {
            "label": "Q4 2017 (euphoria / cycle top)",
            "drawdown_pct": 0, "mvrv": 3.8, "fear_greed": 90, "hy_oas": 3.2,
            "what_happened": [
                "MVRV > 3.5 marked distribution zone",
                "Funding rates extremely elevated",
                "80% drawdown followed over 12 months",
            ],
        },
    }

    current = {
        "drawdown_pct": inp.drawdown_pct,
        "mvrv": inp.mvrv,
        "fear_greed": inp.fear_greed,
        "hy_oas": inp.hy_oas,
    }

    def match_pct(a, b, max_diff):
        if a == 0 and b == 0:
            return 100
        return max(0, round(100 * (1 - abs(a - b) / max_diff)))

    def score_analog(analog):
        return (
            match_pct(current["drawdown_pct"], analog["drawdown_pct"], 25) +
            match_pct(current["mvrv"], analog["mvrv"], 1.0) +
            match_pct(current["fear_greed"], analog["fear_greed"], 40) +
            match_pct(current["hy_oas"], analog["hy_oas"], 2.0)
        ) / 4

    scored = [(name, data, score_analog(data)) for name, data in ANALOGS.items()]
    scored.sort(key=lambda x: x[2], reverse=True)
    best_name, best_data, best_score = scored[0]

    metrics = [
        {
            "name": "BTC drawdown from ATH",
            "analog": f"{best_data['drawdown_pct']}%",
            "current": f"{current['drawdown_pct']:.0f}%",
            "match": match_pct(current["drawdown_pct"], best_data["drawdown_pct"], 25),
        },
        {
            "name": "MVRV",
            "analog": f"{best_data['mvrv']:.2f}",
            "current": f"{current['mvrv']:.2f}",
            "match": match_pct(current["mvrv"], best_data["mvrv"], 1.0),
        },
        {
            "name": "Fear & Greed",
            "analog": f"{best_data['fear_greed']}",
            "current": f"{current['fear_greed']}",
            "match": match_pct(current["fear_greed"], best_data["fear_greed"], 40),
        },
        {
            "name": "HY OAS",
            "analog": f"{best_data['hy_oas']:.1f}%",
            "current": f"{current['hy_oas']:.2f}%",
            "match": match_pct(current["hy_oas"], best_data["hy_oas"], 2.0),
        },
    ]

    all_analogs = [
        {"period": data["label"], "match": round(score_analog(data))}
        for name, data in ANALOGS.items()
    ]
    all_analogs.sort(key=lambda x: x["match"], reverse=True)

    return {
        "analog_period": best_data["label"],
        "overall_match": round(best_score),
        "metrics": metrics,
        "what_happened_next": best_data["what_happened"],
        "all_analogs": all_analogs,
        "lesson": "Historical analogs provide context, not prediction. Each cycle has unique structural factors (ETF access, regulatory environment, macro regime).",
    }


# =============================================================================
# ETH/BTC ROTATION ANALYSIS
# =============================================================================

def generate_rotation_analysis(inp: ModelInputs) -> dict:
    """Evaluate BTC -> ETH -> altcoin rotation conditions."""
    # Rotation conditions (all must be met for full alt season)
    btc_dom_ok = inp.btc_dominance > 0 and inp.btc_dominance < 55
    eth_btc_ok = inp.eth_btc > 0.040
    fg_ok = inp.fear_greed > 50

    conditions = [
        {
            "name": "BTC Dominance < 55%",
            "target": "< 55%",
            "current": f"{inp.btc_dominance:.1f}%" if inp.btc_dominance > 0 else "--",
            "met": btc_dom_ok,
        },
        {
            "name": "ETH/BTC > 0.040",
            "target": "> 0.040",
            "current": f"{inp.eth_btc:.5f}" if inp.eth_btc > 0 else "--",
            "met": eth_btc_ok,
        },
        {
            "name": "Fear & Greed > 50",
            "target": "> 50",
            "current": f"{inp.fear_greed}" if inp.fear_greed > 0 else "--",
            "met": fg_ok,
        },
    ]

    met_count = sum(1 for c in conditions if c["met"])

    if met_count == 3:
        signal_text = "ROTATION ACTIVE"
        signal_class = "active"
        allocation = {"BTC": 25, "ETH": 35, "ALT": 40}
    elif met_count == 2:
        signal_text = "ROTATION FORMING"
        signal_class = "forming"
        allocation = {"BTC": 30, "ETH": 35, "ALT": 35}
    elif met_count == 1:
        signal_text = "EARLY SIGNS"
        signal_class = "early"
        allocation = {"BTC": 40, "ETH": 30, "ALT": 30}
    else:
        signal_text = "NOT YET"
        signal_class = "not-yet"
        allocation = {"BTC": 40, "ETH": 30, "ALT": 30}

    # Dominance threshold indicators
    thresholds = [
        {"level": "55%", "label": "Altcoin season approaching", "crossed": inp.btc_dominance < 55 and inp.btc_dominance > 0},
        {"level": "50%", "label": "Active rotation", "crossed": inp.btc_dominance < 50 and inp.btc_dominance > 0},
        {"level": "45%", "label": "Full alt season", "crossed": inp.btc_dominance < 45 and inp.btc_dominance > 0},
    ]

    return {
        "signal": signal_text,
        "signal_class": signal_class,
        "conditions": conditions,
        "conditions_met": met_count,
        "conditions_total": len(conditions),
        "suggested_allocation": allocation,
        "thresholds": thresholds,
        "eth_btc": inp.eth_btc,
        "btc_dominance": inp.btc_dominance,
    }


# =============================================================================
# PROJECTION → PHASE BRIDGE
# =============================================================================

# Maps projected_phases phase number → composite horizon for price ranges.
_PHASE_HORIZON_MAP = {
    2: "180d",   # Phase 2 (Fed Pivot) → ~6 months out
    3: "365d",   # Phase 3 (Easing Regime) → ~12 months out
    4: "540d",   # Phase 4 (Impulse) → ~18 months out
    5: "730d",   # Phase 5 (Distribution) → ~24 months out
}


def _apply_composite_to_phases(intelligence: dict, composite: dict):
    """Replace crude price multipliers in projected_phases with composite projections.

    Phase 1 keeps its current-price-anchored range (accumulation floor/ceiling).
    Phases 2-5 use the composite bear/bull at the appropriate horizon.
    """
    phases = intelligence.get("projected_phases", [])
    for phase in phases:
        p_num = phase.get("phase")
        horizon = _PHASE_HORIZON_MAP.get(p_num)
        if horizon is None or horizon not in composite:
            continue
        c = composite[horizon]
        bear_k = c["bear"] / 1000
        bull_k = c["bull"] / 1000
        phase["price_range"] = f"${bear_k:.0f}K - ${bull_k:.0f}K"


# =============================================================================
# FULL ANALYSIS — v7.7
# =============================================================================

def run_analysis(inputs: ModelInputs) -> dict:
    """Run full v7.7 analysis and return structured result for the web dashboard."""
    layers, cycle = score_all_layers(inputs)
    result = generate_signal(layers, inputs, cycle)
    intelligence = generate_cycle_intelligence(inputs, cycle)

    # Projection engine — must run after intelligence is built
    projections = generate_projections(inputs, cycle, intelligence, result)

    # Enhance projected_phases with composite projections
    _apply_composite_to_phases(intelligence, projections.get("composite", {}))

    synopsis = generate_synopsis(inputs, cycle, result, intelligence, layers)
    analog = generate_historical_analog(inputs, cycle)
    rotation = generate_rotation_analysis(inputs)

    net_liq = inputs.fed_bs - inputs.rrp - inputs.tga if inputs.fed_bs else 0

    return {
        "model_version": "7.7",
        "timestamp": inputs.timestamp or datetime.now().isoformat(),
        "signal": result,
        "layers": layers,
        "cycle": cycle,
        "intelligence": intelligence,
        "projections": projections,
        "synopsis": synopsis,
        "historical_analog": analog,
        "rotation": rotation,
        "inputs": inputs.to_dict(),
        "market_data": {
            "btc_price": inputs.btc_price,
            "drawdown_pct": inputs.drawdown_pct,
            "mvrv": inputs.mvrv,
            "realized_price": inputs.realized_price,
            "sth_realized_price": inputs.sth_realized_price,
            "lth_realized_price": inputs.lth_realized_price,
            "nupl": inputs.nupl,
            "nupl_fetched": inputs.nupl_fetched,
            "nupl_expected": inputs.nupl_expected,
            "nupl_drift": inputs.nupl_drift,
            "fear_greed": inputs.fear_greed,
            "fear_greed_label": inputs.fear_greed_label,
            "hy_oas": inputs.hy_oas,
            "yield_curve_2s10s": inputs.yield_curve_2s10s,
            "initial_claims": inputs.initial_claims,
            "anfci": inputs.anfci,
            "etf_flow_daily": inputs.etf_flow_daily,
            "etf_flow_weekly": inputs.etf_flow_weekly,
            "etf_cumulative": inputs.etf_cumulative,
            "eth_etf_flow_daily": inputs.eth_etf_flow_daily,
            "eth_etf_cumulative": inputs.eth_etf_cumulative,
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
            "wti_price": inputs.wti_price,
            "global_m2_growth": inputs.global_m2_growth,
            "oi_total": inputs.oi_total,
            "oi_change_24h_pct": inputs.oi_change_24h_pct,
        },
        "sources": inputs.sources,
        "warnings": inputs.warnings,
    }
