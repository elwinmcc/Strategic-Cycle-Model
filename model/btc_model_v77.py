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

    # -- 1. INSTITUTIONAL FLOW (15%) --
    wf = inp.etf_flow_weekly / 1e6 if abs(inp.etf_flow_weekly) > 1e5 else inp.etf_flow_weekly
    etf_s = interp(wf, [(-500, 15), (-100, 35), (0, 50), (100, 65), (500, 80), (1000, 92)])
    layers["institutional_flow"] = {
        "score": round(etf_s), "weight": 0.15,
        "contribution": round(etf_s * 0.15, 2),
        "reasoning": f"ETF weekly ${wf:+.0f}M -> {etf_s:.0f}.",
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

    # -- 3. LEVERAGE FRAGILITY (13%) --
    fr_s = interp(inp.funding_rate * 100, [(-5, 90), (-2, 75), (0, 60), (2, 50), (5, 35), (10, 15)])
    ls_adj = -5 if inp.long_short_ratio > 2.0 else 5 if inp.long_short_ratio < 0.8 else 0
    lev = clamp(fr_s + ls_adj)
    layers["leverage_fragility"] = {
        "score": round(lev), "weight": 0.13,
        "contribution": round(lev * 0.13, 2),
        "reasoning": f"Funding {inp.funding_rate*100:.4f}% -> {fr_s:.0f}. L/S {inp.long_short_ratio:.2f} adj {ls_adj:+d}.",
    }

    # -- 4. DERIVATIVES (10%) --
    basis_s = interp(inp.futures_basis, [(-5, 80), (0, 65), (5, 55), (10, 45), (20, 30), (30, 15)])
    deriv = clamp(0.5 * basis_s + 0.5 * fr_s)
    layers["derivatives"] = {
        "score": round(deriv), "weight": 0.10,
        "contribution": round(deriv * 0.10, 2),
        "reasoning": f"Basis {inp.futures_basis:.1f}% -> {basis_s:.0f}. Funding component {fr_s:.0f}.",
    }

    # -- 5. MVRV (12%) --
    mvrv_s = interp(inp.mvrv, [
        (0.5, 98), (0.8, 95), (1.0, 85), (1.2, 70), (1.5, 55),
        (2.0, 40), (2.5, 25), (3.0, 15), (3.7, 5)
    ])
    layers["mvrv"] = {
        "score": round(mvrv_s), "weight": 0.12,
        "contribution": round(mvrv_s * 0.12, 2),
        "reasoning": f"MVRV {inp.mvrv:.3f} -> {mvrv_s:.0f}. RP ${inp.realized_price:,.0f}. STH ${inp.sth_realized_price:,.0f}, LTH ${inp.lth_realized_price:,.0f}.",
    }

    # -- 6. LIQUIDITY REGIME (8%) --
    # Detect regime from Fed balance sheet level and net liquidity trend
    net_liq = inp.fed_bs - inp.rrp - inp.tga if inp.fed_bs else 0

    # QT ended ~Dec 2025; months since then
    qt_end = datetime(2025, 12, 1)
    months_since_qt = max(0, (datetime.now() - qt_end).days / 30.44)

    # Balance sheet level as regime proxy (trillions)
    bs_t = inp.fed_bs / 1000 if inp.fed_bs else 0
    if bs_t < 6.5:
        regime_s = 35  # Still tight
        regime_label = "POST_QT_LAG"
    elif bs_t < 7.0:
        regime_s = 50  # Neutral
        regime_label = "NEUTRAL"
    elif bs_t < 7.5:
        regime_s = 70  # Stealth easing
        regime_label = "STEALTH_QE"
    else:
        regime_s = 85  # Explicit QE
        regime_label = "EXPLICIT_QE"

    # Transition lag bonus: 3-12 months post-QT is historically bullish
    if 3 <= months_since_qt < 6:
        lag_bonus = 5
    elif 6 <= months_since_qt < 12:
        lag_bonus = 10
    elif months_since_qt >= 12:
        lag_bonus = 5
    else:
        lag_bonus = 0

    liq_regime = clamp(regime_s + lag_bonus)
    layers["liquidity_regime"] = {
        "score": round(liq_regime), "weight": 0.08,
        "contribution": round(liq_regime * 0.08, 2),
        "reasoning": f"Regime: {regime_label}. Fed BS ${inp.fed_bs:,.0f}B. {months_since_qt:.0f}mo since QT end -> lag +{lag_bonus}.",
        "regime": regime_label,
    }

    # -- 7. CYCLE PHASE (5%) --
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
    }

    # -- 8. FED TRANSITION (5%) --
    # Warsh nominated, Powell term ends May 15 2026
    now = datetime.now()
    if now >= datetime(2026, 5, 15):
        chair = "Warsh"
        chair_regime = "DOVISH"
        chair_s = 70
    else:
        chair = "Powell"
        chair_regime = "NEUTRAL"
        chair_s = 45

    # Months to first expected cut (approximate from context)
    months_to_cut = max(0, (datetime(2026, 6, 17) - now).days / 30.44)
    cut_s = interp(months_to_cut, [(0, 90), (1, 80), (3, 65), (6, 50), (12, 35), (24, 20)])

    # Market-implied cuts in next 12 months (hardcoded estimate — would use CME FedWatch API)
    implied_cuts = 2.0
    cuts_s = interp(implied_cuts, [(0, 25), (1, 45), (2, 60), (3, 75), (4, 85)])

    fed_trans = clamp(0.40 * chair_s + 0.30 * cut_s + 0.30 * cuts_s)
    layers["fed_transition"] = {
        "score": round(fed_trans), "weight": 0.05,
        "contribution": round(fed_trans * 0.05, 2),
        "reasoning": f"Chair: {chair} ({chair_regime})->{chair_s}. Months to cut: {months_to_cut:.0f}->{cut_s:.0f}. Implied cuts: {implied_cuts:.0f}->{cuts_s:.0f}.",
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

    # -- 11. CREDIT (5%) --
    credit_s = interp(inp.hy_oas, [
        (2.0, 90), (2.5, 82), (3.0, 72), (3.5, 62), (4.0, 50), (5.0, 35), (6.0, 20), (8.0, 10)
    ])
    layers["credit"] = {
        "score": round(credit_s), "weight": 0.05,
        "contribution": round(credit_s * 0.05, 2),
        "reasoning": f"HY OAS {inp.hy_oas:.2f}% -> {credit_s:.0f}. {'Orderly' if inp.hy_oas < 4.5 else 'Stress'}.",
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
        "months_since_qt_end": round(months_since_qt, 1),
        "fed_chair": chair,
        "chair_regime": chair_regime,
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

    # -- IMPULSE PROBABILITY (10 catalysts per thesis Section VII) --
    months_since_qt = cycle.get("months_since_qt_end", 0)
    catalysts = {
        "treasury_stealth": True,  # TGA drawdowns active (structural — always aligned in current regime)
        "bank_deregulation": True,  # SLR/capital reform underway (structural)
        "rate_cuts_expected": months_since_qt >= 3 and cycle.get("chair_regime") in ("DOVISH", "POLITICAL_DOVE"),
        "oil_resolved": inp.wti_price < 85 if inp.wti_price > 0 else True,
        "mvrv_value": 1.0 <= inp.mvrv <= 1.5,
        "sentiment_extreme": inp.fear_greed < 20,
        "etf_inflows": inp.etf_flow_weekly > 0,
        "regime_maturing": months_since_qt >= 3,
        "chair_dovish": cycle.get("chair_regime") in ("DOVISH", "POLITICAL_DOVE"),
        "credit_orderly": inp.hy_oas < 4.0 if inp.hy_oas > 0 else True,
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
    """Data-driven cycle position, projected phases, and timing assessment."""
    now = datetime.now()
    months_since_qt = cycle.get("months_since_qt_end", 0)

    position = {
        "liquidity_regime": cycle["liquidity_regime"],
        "months_since_qt_end": months_since_qt,
        "business_cycle": cycle["business_phase"],
        "btc_cycle": cycle["btc_phase"],
        "mvrv": inp.mvrv,
        "fed_chair": cycle["fed_chair"],
        "chair_regime": cycle["chair_regime"],
    }

    # ── Easing mechanism probability table (6 mechanisms per thesis Section V) ──
    rate_cut_prob = 80 if inp.anfci < 0 else 55
    if inp.wti_price > 100:
        rate_cut_prob = max(30, rate_cut_prob - 25)  # Oil constraint delays cuts

    easing = [
        {"mechanism": "Treasury stealth (TGA drawdown, buybacks)",
         "probability": 90, "impact": "Moderate", "timeline": "Ongoing"},
        {"mechanism": "Bank deregulation (SLR, capital requirements)",
         "probability": 85, "impact": "Strong", "timeline": "3-6 months"},
        {"mechanism": "Rate cuts (Warsh)",
         "probability": rate_cut_prob, "impact": "Strong", "timeline": "Jun-Sep 2026"},
        {"mechanism": "Regulatory catalysts (BTC reserve, stablecoin bill)",
         "probability": 60, "impact": "BTC-specific", "timeline": "Q3-Q4 2026"},
        {"mechanism": "Yield curve management",
         "probability": 40 if inp.yield_curve_2s10s < -0.5 else 25,
         "impact": "Very strong", "timeline": "If 10Y > 5%"},
        {"mechanism": "Full QE (balance sheet expansion)",
         "probability": 20 if inp.hy_oas < 5 else 40,
         "impact": "Very strong", "timeline": "Recession only"},
    ]

    # ── Projected Cycle Phases (thesis Section 4.2) ──
    # Dynamic: current phase determined by MVRV, months_since_qt, and business cycle
    # Price projections anchored to current BTC price and cycle position
    btc = inp.btc_price if inp.btc_price > 0 else 70000
    ath = btc / (1 + inp.drawdown_pct / 100) if inp.drawdown_pct < 0 else btc * 1.8

    # Determine which phase we're currently in
    if months_since_qt < 6 and inp.mvrv < 1.5:
        current_phase = 1
    elif months_since_qt < 10 and inp.mvrv < 2.0:
        current_phase = 2
    elif months_since_qt < 15 and inp.mvrv < 2.5:
        current_phase = 3
    elif inp.mvrv < 3.0:
        current_phase = 4
    else:
        current_phase = 5

    projected_phases = [
        {
            "phase": 1,
            "name": "Accumulation / Post-QT Lag",
            "timeline": "Dec 2025 - May 2026",
            "price_range": f"${btc*0.85/1000:.0f}K - ${btc*1.15/1000:.0f}K",
            "description": "Post-QT base building. Smart money accumulating, retail fear elevated.",
            "key_signals": "MVRV < 1.5, extreme fear, negative/flat funding, whale accumulation",
            "status": "ACTIVE" if current_phase == 1 else ("COMPLETED" if current_phase > 1 else "PROJECTED"),
        },
        {
            "phase": 2,
            "name": "Fed Pivot / First Cut",
            "timeline": "Jun - Sep 2026",
            "price_range": f"${btc*1.0/1000:.0f}K - ${btc*1.4/1000:.0f}K",
            "description": "Warsh first FOMC Jun 16-17. BTC front-runs first cut by 4-6 weeks.",
            "key_signals": "Rate cut pricing, ETF inflow resumption, MVRV rising toward 1.5",
            "status": "ACTIVE" if current_phase == 2 else ("COMPLETED" if current_phase > 2 else "PROJECTED"),
        },
        {
            "phase": 3,
            "name": "Easing Regime / Markup",
            "timeline": "Sep - Dec 2026",
            "price_range": f"${btc*1.3/1000:.0f}K - ${btc*1.8/1000:.0f}K",
            "description": "Multiple cuts, ETF surge, regulatory catalysts converge. 9-12mo post-QT impulse window.",
            "key_signals": "MVRV 1.5-2.0, sustained positive funding, ETF weekly > $500M",
            "status": "ACTIVE" if current_phase == 3 else ("COMPLETED" if current_phase > 3 else "PROJECTED"),
        },
        {
            "phase": 4,
            "name": "Impulse / Potential Peak",
            "timeline": "Q1 - Q3 2027",
            "price_range": f"${btc*1.7/1000:.0f}K - ${btc*2.4/1000:.0f}K",
            "description": "Full easing 12-18mo post-QT. If recession -> possible QE restart.",
            "key_signals": "MVRV 2.0-3.0, elevated funding, broad market euphoria",
            "status": "ACTIVE" if current_phase == 4 else ("COMPLETED" if current_phase > 4 else "PROJECTED"),
        },
        {
            "phase": 5,
            "name": "Distribution / Cycle Transition",
            "timeline": "Q3 2027 - Q1 2028",
            "price_range": "Monitor for exits",
            "description": "MVRV > 3.0, sustained F&G > 80, funding > 0.05%, ETF outflows > $1B/week.",
            "key_signals": "Model shifts BUY -> REDUCE -> SELL as thresholds crossed",
            "status": "ACTIVE" if current_phase == 5 else "PROJECTED",
        },
    ]

    # ── Accelerators / decelerators from current data ──
    accelerators = []
    decelerators = []

    if inp.wti_price > 0 and inp.wti_price < 70:
        accelerators.append(f"Oil ${inp.wti_price:.0f} — deflationary tailwind")
    elif inp.wti_price > 0 and inp.wti_price < 85:
        accelerators.append(f"Oil ${inp.wti_price:.0f} — within Fed comfort zone")
    if inp.wti_price > 100:
        decelerators.append(f"Oil ${inp.wti_price:.0f} — inflation headwind, delays cuts")

    if inp.fear_greed < 15:
        accelerators.append(f"F&G {inp.fear_greed} — maximum contrarian signal")
    elif inp.fear_greed < 25:
        accelerators.append(f"F&G {inp.fear_greed} — elevated fear, contrarian bullish")

    if inp.funding_rate < -0.001:
        accelerators.append(f"Funding {inp.funding_rate*100:.3f}% — shorts paying (deleveraged)")
    elif abs(inp.funding_rate) < 0.005:
        accelerators.append("Neutral funding — healthy market structure")

    if inp.mvrv > 0 and inp.mvrv < 1.5:
        accelerators.append(f"MVRV {inp.mvrv:.2f} — deep value zone")

    if inp.etf_flow_weekly > 200:
        accelerators.append(f"ETF weekly +${inp.etf_flow_weekly:.0f}M — strong institutional demand")

    if months_since_qt >= 3:
        accelerators.append(f"{months_since_qt:.0f} months post-QT — approaching historical impulse window")

    if inp.anfci > 0:
        decelerators.append(f"ANFCI {inp.anfci:.2f} — tightening financial conditions")
    if inp.initial_claims > 250000:
        decelerators.append(f"Claims {inp.initial_claims/1000:.0f}K — labor weakness")
        accelerators.append("Rising claims -> Fed forced to cut faster")

    if inp.hy_oas > 4.5:
        decelerators.append(f"HY OAS {inp.hy_oas:.1f}% — credit stress")

    if inp.fear_greed > 80:
        decelerators.append(f"F&G {inp.fear_greed} — euphoria zone, distribution risk")

    if inp.funding_rate > 0.05:
        decelerators.append(f"Funding {inp.funding_rate*100:.3f}% — excessive leverage")

    return {
        "position": position,
        "easing_mechanisms": easing,
        "projected_phases": projected_phases,
        "current_phase": current_phase,
        "accelerators": accelerators,
        "decelerators": decelerators,
    }


# =============================================================================
# FULL ANALYSIS — v7.7
# =============================================================================

def run_analysis(inputs: ModelInputs) -> dict:
    """Run full v7.7 analysis and return structured result for the web dashboard."""
    layers, cycle = score_all_layers(inputs)
    result = generate_signal(layers, inputs, cycle)
    intelligence = generate_cycle_intelligence(inputs, cycle)

    net_liq = inputs.fed_bs - inputs.rrp - inputs.tga if inputs.fed_bs else 0

    return {
        "model_version": "7.7",
        "timestamp": inputs.timestamp or datetime.now().isoformat(),
        "signal": result,
        "layers": layers,
        "cycle": cycle,
        "intelligence": intelligence,
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
            "wti_price": inputs.wti_price,
            "global_m2_growth": inputs.global_m2_growth,
            "oi_total": inputs.oi_total,
            "oi_change_24h_pct": inputs.oi_change_24h_pct,
        },
        "sources": inputs.sources,
        "warnings": inputs.warnings,
    }
