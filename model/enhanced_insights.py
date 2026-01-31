"""
═══════════════════════════════════════════════════════════════════════════════
                    BITCOIN STRATEGIC CYCLE MODEL v7.1
                         ENHANCED TRADER INSIGHTS
═══════════════════════════════════════════════════════════════════════════════

NEW IN v7.1:
- Deep Cycle Intelligence with educational explanations
- Multi-Scenario Forecasting (Bull/Base/Bear with catalysts)
- Risk Management Module (position sizing, drawdown analysis)
- Actionable Trade Levels (entries, exits, invalidation)
- On-Chain Intelligence (whale behavior, exchange flows)
- Historical Analog Matching (past cycle comparisons)
- Derivatives Intelligence (funding, OI, liquidations)
- Key Watchlist (what to monitor)

═══════════════════════════════════════════════════════════════════════════════
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
from datetime import datetime, date, timedelta

# =============================================================================
# CYCLE INTELLIGENCE ENGINE
# =============================================================================

class CycleIntelligenceEngine:
    """
    Deep cycle analysis with educational insights for traders.
    Explains WHERE we are, WHY, and WHAT to expect.
    """

    # Historical cycle data for context
    CYCLE_HISTORY = {
        'cycle_1': {'bottom': '2011-11', 'top': '2013-11', 'bottom_price': 2, 'top_price': 1150, 'multiple': 575},
        'cycle_2': {'bottom': '2015-01', 'top': '2017-12', 'bottom_price': 170, 'top_price': 19800, 'multiple': 116},
        'cycle_3': {'bottom': '2018-12', 'top': '2021-11', 'bottom_price': 3150, 'top_price': 69000, 'multiple': 21.9},
        'cycle_4': {'bottom': '2022-11', 'top': 'TBD', 'bottom_price': 15500, 'top_price': None, 'multiple': None}
    }

    # Phase characteristics for education
    PHASE_EDUCATION = {
        'CAPITULATION': {
            'description': 'Maximum fear and despair. Weak hands capitulate, selling at a loss.',
            'psychology': 'Denial → Panic → Capitulation → Depression',
            'typical_mvrv': '< 0.5 (below realized price)',
            'typical_duration': '2-4 months',
            'typical_drawdown': '75-85% from ATH',
            'smart_money_behavior': 'Aggressive accumulation by long-term holders',
            'retail_behavior': 'Panic selling, declaring "crypto is dead"',
            'media_sentiment': 'Obituaries, regulatory FUD, "bubble popped"',
            'what_to_do': 'Maximum conviction buying. This is generational opportunity.',
            'historical_examples': ['Dec 2018 ($3,150)', 'Mar 2020 ($3,800)', 'Nov 2022 ($15,500)'],
            'key_signals_to_exit': ['MVRV crosses above 0', 'F&G sustained >25', 'Price reclaims 200D MA']
        },
        'ACCUMULATION': {
            'description': 'Smart money quietly accumulates while retail remains fearful.',
            'psychology': 'Depression → Disbelief → Hope',
            'typical_mvrv': '0.5 - 1.5',
            'typical_duration': '6-12 months',
            'typical_drawdown': '60-75% from ATH',
            'smart_money_behavior': 'Steady accumulation, building positions',
            'retail_behavior': 'Skeptical, "dead cat bounce" calls, low engagement',
            'media_sentiment': 'Cautious, "crypto winter", focus on failures',
            'what_to_do': 'Continue accumulating. DCA aggressively. Build full position.',
            'historical_examples': ['Q1-Q3 2019', 'Q2-Q4 2020', 'Q1-Q3 2023'],
            'key_signals_to_exit': ['MVRV > 1.5', 'Break above 200D MA with volume', 'ETF/institutional inflows']
        },
        'EARLY_MARKUP': {
            'description': 'Trend confirmation. Early adopters recognize the new bull market.',
            'psychology': 'Hope → Optimism → Belief',
            'typical_mvrv': '1.5 - 2.5',
            'typical_duration': '3-6 months',
            'typical_drawdown': '30-40% corrections normal',
            'smart_money_behavior': 'Holding core positions, adding on dips',
            'retail_behavior': 'Starting to notice, FOMO beginning, "maybe it\'s real"',
            'media_sentiment': 'Cautiously positive, "recovery", institutional interest stories',
            'what_to_do': 'Hold positions. Buy dips. Do NOT sell early.',
            'historical_examples': ['Q4 2020', 'Q4 2023 - Q1 2024'],
            'key_signals_to_exit': ['MVRV > 2.5', 'Weekly RSI > 70', 'Mainstream media attention']
        },
        'MID_MARKUP': {
            'description': 'Bull market in full swing. Retail FOMO accelerates.',
            'psychology': 'Belief → Thrill → Euphoria building',
            'typical_mvrv': '2.5 - 4.0',
            'typical_duration': '4-8 months',
            'typical_drawdown': '20-30% corrections',
            'smart_money_behavior': 'Beginning to take profits, rotating to alts',
            'retail_behavior': 'Full FOMO, leveraged longs, "this time is different"',
            'media_sentiment': 'Bullish, price predictions, celebrity endorsements',
            'what_to_do': 'Begin scaling out plan. Take 10-20% profits. Set trailing stops.',
            'historical_examples': ['Q1-Q2 2021', 'Q1-Q2 2024'],
            'key_signals_to_exit': ['MVRV > 4.0', 'Pi Cycle approaching', 'Extreme F&G (>80)']
        },
        'LATE_MARKUP': {
            'description': 'Final euphoric push. Parabolic moves. Maximum greed.',
            'psychology': 'Euphoria → Complacency → Anxiety',
            'typical_mvrv': '4.0 - 6.0+',
            'typical_duration': '1-3 months',
            'typical_drawdown': 'Volatile 10-20% swings',
            'smart_money_behavior': 'Distributing to retail, moving to stables',
            'retail_behavior': 'Maximum leverage, "we\'re going to $1M", quitting jobs',
            'media_sentiment': 'Mania, mainstream adoption hype, "new paradigm"',
            'what_to_do': 'DISTRIBUTE. Sell 50-70% of position. This is the exit window.',
            'historical_examples': ['Nov-Dec 2017', 'Oct-Nov 2021'],
            'key_signals_to_exit': ['MVRV > 5.5', 'Pi Cycle cross', 'Funding > 0.1%', 'Weekly RSI > 90']
        },
        'DISTRIBUTION': {
            'description': 'Smart money exits while retail still buying. Top formation.',
            'psychology': 'Anxiety → Denial → Fear',
            'typical_mvrv': '3.5 - 5.5 (declining from peak)',
            'typical_duration': '1-3 months',
            'typical_drawdown': 'Initial 20-30% from ATH',
            'smart_money_behavior': 'Completed distribution, fully in stables',
            'retail_behavior': '"Buy the dip", "shakeout before $200K", denial',
            'media_sentiment': 'Mixed, "healthy correction", "institutional buying"',
            'what_to_do': 'Complete distribution. Move to stables. Prepare for bear.',
            'historical_examples': ['Dec 2017 - Jan 2018', 'Nov 2021 - Jan 2022'],
            'key_signals_to_exit': ['Break below 50D MA', 'Lower highs forming', 'Volume declining on rallies']
        },
        'EARLY_MARKDOWN': {
            'description': 'Bear market begins. Denial still high.',
            'psychology': 'Fear → Desperation',
            'typical_mvrv': '2.0 - 3.5 (declining)',
            'typical_duration': '2-4 months',
            'typical_drawdown': '40-50% from ATH',
            'smart_money_behavior': 'Sidelined, looking for re-entry much lower',
            'retail_behavior': 'Still buying dips, "diamond hands", copium',
            'media_sentiment': 'Concerned, regulatory fears, exchange issues',
            'what_to_do': 'Stay in stables. Do NOT buy dips yet. Wait for capitulation.',
            'historical_examples': ['Jan-May 2018', 'Jan-May 2022'],
            'key_signals_to_exit': ['Break below 200D MA', 'MVRV < 2.0', 'Major liquidation events']
        },
        'MID_MARKDOWN': {
            'description': 'Bear market deepens. Hope fades.',
            'psychology': 'Desperation → Panic → Capitulation approaching',
            'typical_mvrv': '0.5 - 2.0 (declining)',
            'typical_duration': '4-8 months',
            'typical_drawdown': '60-80% from ATH',
            'smart_money_behavior': 'Starting to scale in slowly at deep value',
            'retail_behavior': 'Giving up, selling at loss, "never again"',
            'media_sentiment': 'Bearish, obituaries, "I told you so"',
            'what_to_do': 'Begin DCA into deep value zones. Prepare accumulation plan.',
            'historical_examples': ['Jun-Nov 2018', 'Jun-Nov 2022'],
            'key_signals_to_exit': ['MVRV < 0.5', 'F&G < 15', 'Volume capitulation']
        }
    }

    def analyze(self, phase: str, mvrv: float, fear_greed: int,
                cycle_progress: float, price: float, ath: float,
                cycle_low: float) -> Dict:
        """Generate comprehensive cycle intelligence"""

        education = self.PHASE_EDUCATION.get(phase, {})

        # Calculate cycle metrics
        drawdown_from_ath = ((ath - price) / ath * 100) if ath > 0 else 0
        rally_from_low = ((price - cycle_low) / cycle_low * 100) if cycle_low > 0 else 0

        # Estimate cycle position
        cycle_position = self._estimate_cycle_position(mvrv, fear_greed, drawdown_from_ath)

        # Time estimates
        timing = self._estimate_timing(phase, cycle_progress)

        # Risk assessment
        risk = self._assess_risk(phase, mvrv, fear_greed)

        # What's next
        next_phase_analysis = self._analyze_next_phase(phase, mvrv, fear_greed)

        return {
            'current_phase': {
                'name': phase,
                'description': education.get('description', ''),
                'psychology': education.get('psychology', ''),
                'typical_mvrv_range': education.get('typical_mvrv', ''),
                'typical_duration': education.get('typical_duration', ''),
                'where_we_are': self._where_we_are(phase, mvrv, cycle_progress),
            },
            'cycle_metrics': {
                'progress_pct': round(cycle_progress, 1),
                'drawdown_from_ath_pct': round(drawdown_from_ath, 1),
                'rally_from_cycle_low_pct': round(rally_from_low, 1),
                'estimated_position': cycle_position,
            },
            'behavior_guide': {
                'smart_money': education.get('smart_money_behavior', ''),
                'retail': education.get('retail_behavior', ''),
                'media': education.get('media_sentiment', ''),
                'what_you_should_do': education.get('what_to_do', ''),
            },
            'historical_context': {
                'similar_periods': education.get('historical_examples', []),
                'current_cycle_comparison': self._compare_to_past_cycles(price, cycle_low, mvrv),
            },
            'timing_estimates': timing,
            'risk_assessment': risk,
            'transition_signals': {
                'signals_to_watch': education.get('key_signals_to_exit', []),
                'next_phase': next_phase_analysis,
            }
        }

    def _where_we_are(self, phase: str, mvrv: float, progress: float) -> str:
        """Generate plain English explanation of current position"""

        if phase == 'CAPITULATION':
            return f"We are in CAPITULATION - the bottom of the cycle. MVRV at {mvrv:.2f} indicates price is {'below' if mvrv < 1 else 'near'} realized value. This is historically the best buying opportunity. Only {progress:.0f}% through the cycle."

        elif phase == 'ACCUMULATION':
            return f"We are in ACCUMULATION phase at {progress:.0f}% cycle progress. MVRV {mvrv:.2f} shows we're still in value territory. Smart money is building positions while retail remains skeptical. Continue accumulating."

        elif phase == 'EARLY_MARKUP':
            return f"We are in EARLY MARKUP - the bull market has been confirmed. At {progress:.0f}% cycle progress with MVRV {mvrv:.2f}, we're past the accumulation phase but still early. Hold positions and buy dips."

        elif phase == 'MID_MARKUP':
            return f"We are in MID MARKUP at {progress:.0f}% cycle progress. MVRV {mvrv:.2f} shows we're in fair value territory. The bull is running. Start planning exit strategy but don't sell too early."

        elif phase == 'LATE_MARKUP':
            return f"We are in LATE MARKUP - approaching cycle peak. At {progress:.0f}% cycle progress with MVRV {mvrv:.2f}, we're in extended territory. This is the distribution window. Scale out 50-70% of position."

        elif phase == 'DISTRIBUTION':
            return f"We are in DISTRIBUTION phase. Smart money is exiting at {progress:.0f}% cycle progress. MVRV {mvrv:.2f} indicates overvaluation. Complete your exit strategy. Bear market approaching."

        elif phase in ['EARLY_MARKDOWN', 'MID_MARKDOWN']:
            return f"We are in {phase.replace('_', ' ')} - bear market territory. At {progress:.0f}% cycle progress, wait for capitulation before buying. Preserve capital."

        return f"Current phase: {phase} at {progress:.0f}% cycle progress with MVRV {mvrv:.2f}."

    def _estimate_cycle_position(self, mvrv: float, fg: int, drawdown: float) -> str:
        """Estimate where we are in the 4-year cycle"""

        if mvrv < 0.5:
            return "CYCLE BOTTOM (0-10%)"
        elif mvrv < 1.0:
            return "EARLY CYCLE (10-20%)"
        elif mvrv < 1.5:
            return "EARLY-MID CYCLE (20-35%)"
        elif mvrv < 2.0:
            return "MID CYCLE (35-50%)"
        elif mvrv < 3.0:
            return "MID-LATE CYCLE (50-70%)"
        elif mvrv < 4.5:
            return "LATE CYCLE (70-85%)"
        elif mvrv < 6.0:
            return "CYCLE PEAK ZONE (85-95%)"
        else:
            return "CYCLE TOP (95-100%)"

    def _estimate_timing(self, phase: str, progress: float) -> Dict:
        """Estimate timing for key cycle events"""

        # Rough estimates based on typical cycle duration
        typical_cycle_months = 48  # 4-year cycle
        months_elapsed = (progress / 100) * typical_cycle_months
        months_remaining = typical_cycle_months - months_elapsed

        # Phase-specific timing
        phase_timing = {
            'CAPITULATION': {'to_accumulation': '1-3 months', 'to_bull': '6-12 months', 'to_peak': '24-36 months'},
            'ACCUMULATION': {'to_early_markup': '3-9 months', 'to_peak': '18-30 months'},
            'EARLY_MARKUP': {'to_mid_markup': '3-6 months', 'to_peak': '12-24 months'},
            'MID_MARKUP': {'to_late_markup': '4-8 months', 'to_peak': '6-12 months'},
            'LATE_MARKUP': {'to_distribution': '1-3 months', 'to_peak': '0-3 months'},
            'DISTRIBUTION': {'to_bear': '1-3 months', 'to_bottom': '12-18 months'},
            'EARLY_MARKDOWN': {'to_mid_markdown': '2-4 months', 'to_bottom': '8-14 months'},
            'MID_MARKDOWN': {'to_capitulation': '2-6 months', 'to_bottom': '2-8 months'}
        }

        timing = phase_timing.get(phase, {})

        return {
            'cycle_months_elapsed': round(months_elapsed, 0),
            'cycle_months_remaining_est': round(months_remaining, 0),
            'phase_specific': timing,
            'key_dates': self._get_key_dates(),
            'confidence': 'MEDIUM - Cycles vary in length'
        }

    def _get_key_dates(self) -> List[Dict]:
        """Get upcoming key dates for the crypto market"""
        return [
            {'date': '2024-04', 'event': 'Bitcoin Halving', 'impact': 'Historically bullish 12-18 months after'},
            {'date': '2025-Q1', 'event': 'Post-halving acceleration zone', 'impact': 'Typical blow-off top period'},
            {'date': '2025-Q4', 'event': 'Potential cycle peak window', 'impact': 'Watch for distribution signals'},
        ]

    def _assess_risk(self, phase: str, mvrv: float, fg: int) -> Dict:
        """Assess current risk levels"""

        # Downside risk
        if mvrv < 1.0:
            downside_risk = 'LOW'
            max_expected_dd = '20-30%'
        elif mvrv < 2.0:
            downside_risk = 'LOW-MEDIUM'
            max_expected_dd = '30-40%'
        elif mvrv < 3.0:
            downside_risk = 'MEDIUM'
            max_expected_dd = '40-50%'
        elif mvrv < 4.5:
            downside_risk = 'MEDIUM-HIGH'
            max_expected_dd = '50-65%'
        else:
            downside_risk = 'HIGH'
            max_expected_dd = '70-85%'

        # Upside potential
        if mvrv < 1.0:
            upside_potential = 'EXTREME (5-10x)'
        elif mvrv < 2.0:
            upside_potential = 'HIGH (3-5x)'
        elif mvrv < 3.0:
            upside_potential = 'GOOD (2-3x)'
        elif mvrv < 4.5:
            upside_potential = 'LIMITED (1.5-2x)'
        else:
            upside_potential = 'MINIMAL (<1.5x)'

        # Risk/Reward
        if mvrv < 1.5:
            risk_reward = 'EXCELLENT'
        elif mvrv < 2.5:
            risk_reward = 'FAVORABLE'
        elif mvrv < 4.0:
            risk_reward = 'NEUTRAL'
        else:
            risk_reward = 'UNFAVORABLE'

        return {
            'downside_risk': downside_risk,
            'max_expected_drawdown': max_expected_dd,
            'upside_potential': upside_potential,
            'risk_reward_rating': risk_reward,
            'recommendation': self._risk_recommendation(mvrv, fg)
        }

    def _risk_recommendation(self, mvrv: float, fg: int) -> str:
        if mvrv < 1.0:
            return "MAXIMUM POSITION SIZE - Generational buying opportunity"
        elif mvrv < 1.5:
            return "LARGE POSITION SIZE (80-100%) - Strong value zone"
        elif mvrv < 2.0:
            return "FULL POSITION SIZE (70-80%) - Value zone"
        elif mvrv < 3.0:
            return "MODERATE POSITION SIZE (50-70%) - Fair value"
        elif mvrv < 4.0:
            return "REDUCED POSITION SIZE (30-50%) - Begin scaling out"
        elif mvrv < 5.0:
            return "MINIMAL POSITION SIZE (20-30%) - Distribution zone"
        else:
            return "EXIT POSITION (0-20%) - Euphoria zone, preserve capital"

    def _analyze_next_phase(self, current_phase: str, mvrv: float, fg: int) -> Dict:
        """Analyze transition to next phase"""

        transitions = {
            'CAPITULATION': ('ACCUMULATION', ['MVRV crosses 0', 'F&G > 25', 'Price > 200D MA']),
            'ACCUMULATION': ('EARLY_MARKUP', ['MVRV > 1.5', 'Break key resistance', 'Volume surge']),
            'EARLY_MARKUP': ('MID_MARKUP', ['MVRV > 2.5', 'Retail FOMO begins', 'Media coverage']),
            'MID_MARKUP': ('LATE_MARKUP', ['MVRV > 4.0', 'Parabolic moves', 'Extreme greed']),
            'LATE_MARKUP': ('DISTRIBUTION', ['MVRV > 5.5', 'Pi Cycle cross', 'Blow-off top']),
            'DISTRIBUTION': ('EARLY_MARKDOWN', ['Break 50D MA', 'Lower highs', 'Volume decline']),
            'EARLY_MARKDOWN': ('MID_MARKDOWN', ['Break 200D MA', 'MVRV < 2.5', 'Capitulation events']),
            'MID_MARKDOWN': ('CAPITULATION', ['MVRV < 0.5', 'F&G < 15', 'Max despair'])
        }

        next_phase, triggers = transitions.get(current_phase, ('UNKNOWN', []))

        return {
            'next_phase': next_phase,
            'triggers_needed': triggers,
            'probability': self._transition_probability(current_phase, mvrv, fg),
            'estimated_timeframe': self.PHASE_EDUCATION.get(current_phase, {}).get('typical_duration', 'Unknown')
        }

    def _transition_probability(self, phase: str, mvrv: float, fg: int) -> int:
        """Estimate probability of transition to next phase"""

        # Simple heuristic based on typical patterns
        if phase == 'ACCUMULATION' and mvrv > 1.3:
            return 70
        elif phase == 'EARLY_MARKUP' and mvrv > 2.0:
            return 60
        elif phase == 'MID_MARKUP' and mvrv > 3.5:
            return 50
        elif phase == 'LATE_MARKUP' and mvrv > 5.0:
            return 75
        elif phase == 'DISTRIBUTION' and mvrv < 4.0:
            return 65
        return 30

    def _compare_to_past_cycles(self, price: float, cycle_low: float, mvrv: float) -> Dict:
        """Compare current cycle to past cycles"""

        current_multiple = price / cycle_low if cycle_low > 0 else 0

        return {
            'current_cycle': {
                'bottom': '$15,500 (Nov 2022)',
                'current_multiple': f'{current_multiple:.1f}x',
                'mvrv': mvrv
            },
            'cycle_3_at_same_mvrv': {
                'price_then': 'Various',
                'eventual_peak': '$69,000',
                'multiple_from_comparable': '~3-5x'
            },
            'cycle_2_at_same_mvrv': {
                'price_then': 'Various',
                'eventual_peak': '$19,800',
                'multiple_from_comparable': '~4-8x'
            },
            'pattern_note': 'Diminishing returns each cycle - expect 3-5x from current MVRV to peak'
        }


# =============================================================================
# SCENARIO FORECASTING ENGINE
# =============================================================================

class ScenarioEngine:
    """
    Multi-scenario forecasting with detailed catalysts and probabilities.
    """

    def analyze(self, price: float, mvrv: float, phase: str,
                liquidity_score: float, trend_alignment: str) -> Dict:
        """Generate detailed scenario analysis"""

        base_scenarios = self._generate_scenarios(price, mvrv, phase)

        # Adjust probabilities based on current conditions
        adjusted = self._adjust_probabilities(base_scenarios, liquidity_score, trend_alignment, mvrv)

        # Add detailed paths
        for scenario in adjusted.values():
            if isinstance(scenario, dict) and 'target_12m' in scenario:
                scenario['price_path'] = self._generate_price_path(price, scenario)
                scenario['key_levels'] = self._get_key_levels(price, scenario)

        return {
            'scenarios': adjusted,
            'probability_summary': self._summarize_probabilities(adjusted),
            'expected_value': self._calculate_expected_value(price, adjusted),
            'recommendation': self._scenario_recommendation(adjusted)
        }

    def _generate_scenarios(self, price: float, mvrv: float, phase: str) -> Dict:
        """Generate base scenarios"""

        return {
            'super_bull': {
                'name': 'Super Cycle',
                'probability': 10,
                'target_12m': int(price * 4.0),
                'target_peak': int(price * 5.5),
                'mvrv_path': f'{mvrv:.1f} → 4.0 → 6.0 → 8.0+',
                'description': 'Institutional adoption + sovereign buying + monetary crisis',
                'catalysts': [
                    'Nation-state BTC adoption (beyond El Salvador)',
                    'Major currency crisis driving safe haven flows',
                    'ETF inflows exceed $100B',
                    'Fed emergency rate cuts + QE'
                ],
                'risks': ['Black swan events', 'Regulatory crackdown'],
                'conviction': 'LOW - Requires multiple tail events'
            },
            'bull': {
                'name': 'Strong Bull',
                'probability': 30,
                'target_12m': int(price * 2.5),
                'target_peak': int(price * 3.5),
                'mvrv_path': f'{mvrv:.1f} → 3.0 → 4.5 → 5.5',
                'description': 'Typical post-halving bull cycle with strong institutional demand',
                'catalysts': [
                    'Continued ETF inflows ($30-50B annually)',
                    'Fed pivot to rate cuts',
                    'Global M2 expansion',
                    'Corporate treasury adoption'
                ],
                'risks': ['Regulatory headwinds', 'Risk-off events'],
                'conviction': 'MEDIUM - Historical pattern supports'
            },
            'base': {
                'name': 'Gradual Growth',
                'probability': 40,
                'target_12m': int(price * 1.7),
                'target_peak': int(price * 2.5),
                'mvrv_path': f'{mvrv:.1f} → 2.5 → 3.0 → 3.5',
                'description': 'Steady accumulation, range-bound with higher lows',
                'catalysts': [
                    'Steady ETF demand ($10-20B annually)',
                    'Neutral Fed policy',
                    'Gradual institutional adoption',
                    'Growing utility (L2s, payments)'
                ],
                'risks': ['Slower than expected adoption', 'Competition from other assets'],
                'conviction': 'HIGH - Most likely path'
            },
            'bear': {
                'name': 'Correction/Bear',
                'probability': 15,
                'target_12m': int(price * 0.6),
                'target_low': int(price * 0.45),
                'mvrv_path': f'{mvrv:.1f} → 1.5 → 1.0 → 0.7',
                'description': 'Risk-off environment, liquidity contraction',
                'catalysts': [
                    'Fed maintains higher for longer',
                    'Global recession',
                    'Major exchange failure',
                    'Regulatory action (stablecoin ban, etc.)'
                ],
                'risks': ['Could be buying opportunity if fundamentals intact'],
                'conviction': 'LOW-MEDIUM - Requires catalyst'
            },
            'black_swan': {
                'name': 'Black Swan',
                'probability': 5,
                'target_12m': 'Unpredictable',
                'description': 'Exogenous shock - could be positive or negative',
                'examples': [
                    'Protocol-level vulnerability',
                    'Global financial system collapse',
                    'Major war escalation',
                    'Unexpected technological breakthrough'
                ],
                'conviction': 'N/A - By definition unpredictable'
            }
        }

    def _adjust_probabilities(self, scenarios: Dict, liq_score: float,
                             trend: str, mvrv: float) -> Dict:
        """Adjust scenario probabilities based on current conditions"""

        adjusted = scenarios.copy()

        # Liquidity adjustment
        if liq_score > 70:  # Bullish liquidity
            adjusted['bull']['probability'] += 10
            adjusted['bear']['probability'] -= 5
        elif liq_score < 30:  # Bearish liquidity
            adjusted['bull']['probability'] -= 10
            adjusted['bear']['probability'] += 10

        # Trend adjustment
        if 'BULLISH' in trend:
            adjusted['bull']['probability'] += 5
            adjusted['base']['probability'] += 5
            adjusted['bear']['probability'] -= 5
        elif 'BEARISH' in trend:
            adjusted['bull']['probability'] -= 5
            adjusted['bear']['probability'] += 10

        # MVRV adjustment (mean reversion)
        if mvrv > 3.5:  # Extended
            adjusted['bear']['probability'] += 10
            adjusted['bull']['probability'] -= 10
        elif mvrv < 1.5:  # Value
            adjusted['bull']['probability'] += 10
            adjusted['bear']['probability'] -= 5

        # Normalize to 100%
        total = sum(s.get('probability', 0) for s in adjusted.values() if isinstance(s, dict))
        for key, scenario in adjusted.items():
            if isinstance(scenario, dict) and 'probability' in scenario:
                scenario['probability'] = round(scenario['probability'] / total * 100)

        return adjusted

    def _generate_price_path(self, current: float, scenario: Dict) -> List[Dict]:
        """Generate quarterly price path for scenario"""

        target = scenario.get('target_12m', current)
        if not isinstance(target, (int, float)):
            return []

        # Linear interpolation with some variance
        path = []
        for q in range(1, 5):
            progress = q / 4
            price = current + (target - current) * progress
            path.append({
                'quarter': f'Q{q}',
                'price_est': int(price),
                'range': f'${int(price * 0.85):,} - ${int(price * 1.15):,}'
            })

        return path

    def _get_key_levels(self, current: float, scenario: Dict) -> Dict:
        """Get key price levels for scenario"""

        target = scenario.get('target_12m', current)
        if not isinstance(target, (int, float)):
            return {}

        return {
            'target': int(target),
            'resistance_1': int(current * 1.2),
            'resistance_2': int(current * 1.5),
            'support_1': int(current * 0.85),
            'support_2': int(current * 0.70),
            'invalidation': int(current * 0.60)
        }

    def _summarize_probabilities(self, scenarios: Dict) -> Dict:
        """Summarize probability distribution"""

        bullish = scenarios.get('super_bull', {}).get('probability', 0) + \
                  scenarios.get('bull', {}).get('probability', 0)
        neutral = scenarios.get('base', {}).get('probability', 0)
        bearish = scenarios.get('bear', {}).get('probability', 0) + \
                  scenarios.get('black_swan', {}).get('probability', 0)

        return {
            'bullish_total': bullish,
            'neutral_total': neutral,
            'bearish_total': bearish,
            'skew': 'BULLISH' if bullish > bearish + 20 else 'BEARISH' if bearish > bullish + 10 else 'NEUTRAL'
        }

    def _calculate_expected_value(self, current: float, scenarios: Dict) -> Dict:
        """Calculate probability-weighted expected value"""

        ev = 0
        for scenario in scenarios.values():
            if isinstance(scenario, dict) and 'probability' in scenario:
                target = scenario.get('target_12m')
                if isinstance(target, (int, float)):
                    ev += target * (scenario['probability'] / 100)

        expected_return = ((ev - current) / current * 100) if current > 0 else 0

        return {
            'expected_price_12m': int(ev),
            'expected_return_pct': round(expected_return, 1),
            'current_price': current,
            'interpretation': f"Probability-weighted 12M target is ${int(ev):,} ({expected_return:+.1f}%)"
        }

    def _scenario_recommendation(self, scenarios: Dict) -> str:
        """Generate recommendation based on scenario analysis"""

        prob = self._summarize_probabilities(scenarios)

        if prob['bullish_total'] > 50:
            return "SCENARIOS FAVOR BULLS - Maintain/increase exposure. Risk/reward attractive."
        elif prob['bearish_total'] > 30:
            return "ELEVATED BEAR RISK - Reduce exposure or hedge. Consider taking profits."
        else:
            return "BALANCED SCENARIOS - Maintain core position. Opportunistic adds on dips."


# =============================================================================
# RISK MANAGEMENT ENGINE
# =============================================================================

class RiskManagementEngine:
    """
    Position sizing, drawdown analysis, and risk metrics for traders.
    """

    def analyze(self, price: float, mvrv: float, phase: str,
                portfolio_value: float = 100000,
                current_btc_allocation: float = 50) -> Dict:
        """Generate risk management recommendations"""

        # Position sizing
        sizing = self._position_sizing(mvrv, phase, portfolio_value)

        # Drawdown analysis
        drawdown = self._drawdown_analysis(price, mvrv)

        # Key levels
        levels = self._calculate_levels(price, mvrv)

        # DCA strategy
        dca = self._dca_strategy(price, mvrv, phase)

        # Exit strategy
        exit_strategy = self._exit_strategy(price, mvrv, phase)

        return {
            'position_sizing': sizing,
            'drawdown_analysis': drawdown,
            'key_levels': levels,
            'dca_strategy': dca,
            'exit_strategy': exit_strategy,
            'current_allocation_assessment': self._assess_allocation(
                current_btc_allocation, sizing['recommended_allocation_pct']
            )
        }

    def _position_sizing(self, mvrv: float, phase: str, portfolio: float) -> Dict:
        """Calculate recommended position size"""

        # MVRV-based allocation
        if mvrv < 0.5:
            base_alloc = 95
            conviction = 'MAXIMUM'
        elif mvrv < 1.0:
            base_alloc = 85
            conviction = 'VERY HIGH'
        elif mvrv < 1.5:
            base_alloc = 75
            conviction = 'HIGH'
        elif mvrv < 2.0:
            base_alloc = 65
            conviction = 'MODERATE-HIGH'
        elif mvrv < 2.5:
            base_alloc = 55
            conviction = 'MODERATE'
        elif mvrv < 3.0:
            base_alloc = 45
            conviction = 'MODERATE-LOW'
        elif mvrv < 4.0:
            base_alloc = 35
            conviction = 'LOW'
        elif mvrv < 5.0:
            base_alloc = 20
            conviction = 'VERY LOW'
        else:
            base_alloc = 10
            conviction = 'MINIMAL'

        recommended_btc_value = portfolio * (base_alloc / 100)

        return {
            'recommended_allocation_pct': base_alloc,
            'recommended_btc_value': int(recommended_btc_value),
            'conviction_level': conviction,
            'mvrv_justification': f'MVRV {mvrv:.2f} indicates {"value" if mvrv < 2 else "fair value" if mvrv < 3 else "extended" if mvrv < 5 else "euphoria"} zone',
            'max_single_entry': int(recommended_btc_value * 0.25),
            'note': 'Never invest more than you can afford to lose 80%'
        }

    def _drawdown_analysis(self, price: float, mvrv: float) -> Dict:
        """Analyze potential drawdown scenarios"""

        # Historical drawdown by MVRV zone
        if mvrv < 1.0:
            typical_dd = 25
            max_dd = 40
            dd_desc = "Limited downside from deep value"
        elif mvrv < 2.0:
            typical_dd = 35
            max_dd = 50
            dd_desc = "Moderate drawdown possible in corrections"
        elif mvrv < 3.0:
            typical_dd = 45
            max_dd = 60
            dd_desc = "Significant drawdown risk in bear market"
        elif mvrv < 4.5:
            typical_dd = 55
            max_dd = 70
            dd_desc = "High drawdown risk from extended levels"
        else:
            typical_dd = 70
            max_dd = 85
            dd_desc = "Severe drawdown risk from euphoria zone"

        return {
            'typical_drawdown_pct': typical_dd,
            'max_historical_drawdown_pct': max_dd,
            'description': dd_desc,
            'price_at_typical_dd': int(price * (1 - typical_dd/100)),
            'price_at_max_dd': int(price * (1 - max_dd/100)),
            'mental_preparation': f"If you buy here, be prepared for price to drop to ${int(price * (1 - typical_dd/100)):,} ({typical_dd}% drawdown) without panicking."
        }

    def _calculate_levels(self, price: float, mvrv: float) -> Dict:
        """Calculate key price levels"""

        return {
            'current_price': price,
            'strong_support': {
                'price': int(price * 0.75),
                'description': '25% below - typical bull market correction'
            },
            'critical_support': {
                'price': int(price * 0.60),
                'description': '40% below - bear market territory'
            },
            'capitulation_target': {
                'price': int(price * 0.45),
                'description': '55% below - deep value accumulation zone'
            },
            'resistance_1': {
                'price': int(price * 1.25),
                'description': '25% above - first major resistance'
            },
            'resistance_2': {
                'price': int(price * 1.50),
                'description': '50% above - psychological level'
            },
            'cycle_target': {
                'price': int(price * 2.5) if mvrv < 2.5 else int(price * 1.5),
                'description': 'Potential cycle peak target'
            }
        }

    def _dca_strategy(self, price: float, mvrv: float, phase: str) -> Dict:
        """Generate DCA strategy based on current conditions"""

        if mvrv < 1.0:
            strategy = 'AGGRESSIVE_ACCUMULATION'
            schedule = 'Daily buys - front-load as much as possible'
            levels = [
                {'price': price, 'allocation': '40%', 'action': 'Buy now'},
                {'price': int(price * 0.9), 'allocation': '30%', 'action': 'Add on dip'},
                {'price': int(price * 0.8), 'allocation': '30%', 'action': 'Back up the truck'}
            ]
        elif mvrv < 1.5:
            strategy = 'STEADY_ACCUMULATION'
            schedule = 'Weekly buys - consistent allocation'
            levels = [
                {'price': price, 'allocation': '35%', 'action': 'Buy now'},
                {'price': int(price * 0.9), 'allocation': '35%', 'action': 'Add on dip'},
                {'price': int(price * 0.8), 'allocation': '30%', 'action': 'Increase size'}
            ]
        elif mvrv < 2.0:
            strategy = 'MODERATE_ACCUMULATION'
            schedule = 'Bi-weekly buys - measured approach'
            levels = [
                {'price': price, 'allocation': '25%', 'action': 'Small buy'},
                {'price': int(price * 0.85), 'allocation': '40%', 'action': 'Larger on dip'},
                {'price': int(price * 0.70), 'allocation': '35%', 'action': 'Full size'}
            ]
        elif mvrv < 3.0:
            strategy = 'HOLD_NO_NEW_BUYS'
            schedule = 'Monthly review - wait for better entry'
            levels = [
                {'price': int(price * 0.80), 'allocation': '50%', 'action': 'Start buying'},
                {'price': int(price * 0.65), 'allocation': '50%', 'action': 'Complete position'}
            ]
        else:
            strategy = 'NO_BUYS_DISTRIBUTION'
            schedule = 'Focus on exit strategy, not entries'
            levels = []

        return {
            'strategy': strategy,
            'schedule': schedule,
            'entry_levels': levels,
            'note': 'Always keep dry powder for unexpected opportunities'
        }

    def _exit_strategy(self, price: float, mvrv: float, phase: str) -> Dict:
        """Generate exit strategy for current position"""

        if mvrv < 2.0:
            return {
                'recommendation': 'NO EXITS - Accumulation zone',
                'rationale': f'MVRV {mvrv:.2f} is too low to sell. Hold and accumulate.',
                'exit_levels': [],
                'trailing_stop': 'Not applicable in accumulation'
            }

        elif mvrv < 3.0:
            return {
                'recommendation': 'HOLD - Begin planning exits',
                'rationale': 'Fair value zone. No urgency to sell but start planning.',
                'exit_levels': [
                    {'price': int(price * 1.5), 'sell_pct': 10, 'rationale': 'First profit taking'},
                    {'price': int(price * 2.0), 'sell_pct': 15, 'rationale': 'Extend profits'}
                ],
                'trailing_stop': 'Consider 25% trailing stop after 50% gains'
            }

        elif mvrv < 4.0:
            return {
                'recommendation': 'BEGIN DISTRIBUTION',
                'rationale': 'Extended territory. Start scaling out.',
                'exit_levels': [
                    {'price': price, 'sell_pct': 15, 'rationale': 'Take profits now'},
                    {'price': int(price * 1.25), 'sell_pct': 20, 'rationale': 'Continue scaling'},
                    {'price': int(price * 1.5), 'sell_pct': 25, 'rationale': 'Aggressive taking'}
                ],
                'trailing_stop': '20% trailing stop recommended'
            }

        else:
            return {
                'recommendation': 'AGGRESSIVE DISTRIBUTION',
                'rationale': 'Euphoria zone. Prioritize capital preservation.',
                'exit_levels': [
                    {'price': price, 'sell_pct': 30, 'rationale': 'Sell now'},
                    {'price': int(price * 1.15), 'sell_pct': 30, 'rationale': 'Continue exit'},
                    {'price': int(price * 1.25), 'sell_pct': 30, 'rationale': 'Final exit'}
                ],
                'trailing_stop': '15% trailing stop - tight risk management',
                'warning': 'Cycle tops are hard to time. Better to sell too early than too late.'
            }

    def _assess_allocation(self, current: float, recommended: float) -> Dict:
        """Assess current allocation vs recommended"""

        diff = current - recommended

        if abs(diff) < 10:
            status = 'APPROPRIATE'
            action = 'Maintain current allocation'
        elif diff > 20:
            status = 'OVERWEIGHT'
            action = f'Consider reducing by {int(diff)}% to recommended {recommended}%'
        elif diff > 10:
            status = 'SLIGHTLY_OVERWEIGHT'
            action = f'Slightly reduce or hold. Target: {recommended}%'
        elif diff < -20:
            status = 'UNDERWEIGHT'
            action = f'Consider increasing by {int(abs(diff))}% to recommended {recommended}%'
        else:
            status = 'SLIGHTLY_UNDERWEIGHT'
            action = f'Consider adding. Target: {recommended}%'

        return {
            'current_allocation': current,
            'recommended_allocation': recommended,
            'difference': diff,
            'status': status,
            'action': action
        }


# =============================================================================
# TRADE LEVELS ENGINE
# =============================================================================

class TradeLevelsEngine:
    """
    Generate specific actionable trade levels for entries, exits, and stops.
    """

    def analyze(self, price: float, mvrv: float, phase: str,
                support_levels: List[float] = None,
                resistance_levels: List[float] = None) -> Dict:
        """Generate actionable trade levels"""

        # Calculate key levels
        entries = self._calculate_entries(price, mvrv, phase)
        exits = self._calculate_exits(price, mvrv, phase)
        stops = self._calculate_stops(price, mvrv, phase)
        invalidation = self._calculate_invalidation(price, mvrv)

        return {
            'entry_zones': entries,
            'exit_targets': exits,
            'stop_loss_levels': stops,
            'invalidation': invalidation,
            'trade_plan': self._generate_trade_plan(price, mvrv, phase, entries, exits, stops)
        }

    def _calculate_entries(self, price: float, mvrv: float, phase: str) -> List[Dict]:
        """Calculate entry zones"""

        entries = []

        if mvrv < 2.5:  # Buying is appropriate
            entries.append({
                'zone': 'IMMEDIATE',
                'price_range': f'${int(price * 0.98):,} - ${int(price * 1.02):,}',
                'size': '25% of intended position',
                'rationale': 'Current price in value zone'
            })

            entries.append({
                'zone': 'DIP_BUY_1',
                'price_range': f'${int(price * 0.88):,} - ${int(price * 0.92):,}',
                'size': '35% of intended position',
                'rationale': '10% pullback - typical volatility'
            })

            entries.append({
                'zone': 'DIP_BUY_2',
                'price_range': f'${int(price * 0.75):,} - ${int(price * 0.80):,}',
                'size': '40% of intended position',
                'rationale': '20-25% correction - strong support'
            })

        else:  # Not ideal for new entries
            entries.append({
                'zone': 'WAIT_FOR_CORRECTION',
                'price_range': f'Below ${int(price * 0.75):,}',
                'size': 'Start small positions',
                'rationale': 'MVRV extended - wait for pullback'
            })

        return entries

    def _calculate_exits(self, price: float, mvrv: float, phase: str) -> List[Dict]:
        """Calculate exit targets"""

        exits = []

        if mvrv < 2.0:
            # Long way to go - distant targets
            exits.append({
                'target': 'FIRST_TAKE_PROFIT',
                'price': int(price * 2.0),
                'sell_pct': 15,
                'mvrv_est': 3.5,
                'rationale': '2x from here - first profit taking'
            })
            exits.append({
                'target': 'SECOND_TAKE_PROFIT',
                'price': int(price * 2.8),
                'sell_pct': 25,
                'mvrv_est': 4.5,
                'rationale': 'Extended territory - larger exit'
            })
            exits.append({
                'target': 'CYCLE_TOP_TARGET',
                'price': int(price * 3.5),
                'sell_pct': 40,
                'mvrv_est': 5.5,
                'rationale': 'Historical cycle peak zone'
            })

        elif mvrv < 3.5:
            exits.append({
                'target': 'NEAR_TERM',
                'price': int(price * 1.3),
                'sell_pct': 20,
                'rationale': 'Take some profit at 30% gain'
            })
            exits.append({
                'target': 'EXTENDED',
                'price': int(price * 1.6),
                'sell_pct': 30,
                'rationale': 'Extended territory exit'
            })
            exits.append({
                'target': 'EUPHORIA',
                'price': int(price * 2.0),
                'sell_pct': 40,
                'rationale': 'Euphoria zone - major exit'
            })

        else:
            exits.append({
                'target': 'IMMEDIATE',
                'price': price,
                'sell_pct': 30,
                'rationale': 'MVRV extended - start exiting now'
            })
            exits.append({
                'target': 'FINAL_PUSH',
                'price': int(price * 1.2),
                'sell_pct': 50,
                'rationale': 'Final blow-off target'
            })

        return exits

    def _calculate_stops(self, price: float, mvrv: float, phase: str) -> Dict:
        """Calculate stop loss levels"""

        if mvrv < 1.5:
            # Deep value - wide stops
            return {
                'soft_stop': {
                    'price': int(price * 0.70),
                    'description': '30% below - re-evaluate but likely hold'
                },
                'hard_stop': {
                    'price': int(price * 0.55),
                    'description': '45% below - protocol risk territory'
                },
                'strategy': 'WIDE STOPS - Value zone means asymmetric upside'
            }

        elif mvrv < 2.5:
            return {
                'soft_stop': {
                    'price': int(price * 0.78),
                    'description': '22% below - monitor closely'
                },
                'hard_stop': {
                    'price': int(price * 0.65),
                    'description': '35% below - exit to preserve capital'
                },
                'strategy': 'MODERATE STOPS - Balance risk/reward'
            }

        else:
            return {
                'soft_stop': {
                    'price': int(price * 0.85),
                    'description': '15% below - start reducing'
                },
                'hard_stop': {
                    'price': int(price * 0.75),
                    'description': '25% below - full exit'
                },
                'strategy': 'TIGHT STOPS - Protect profits in extended zone'
            }

    def _calculate_invalidation(self, price: float, mvrv: float) -> Dict:
        """Calculate thesis invalidation levels"""

        return {
            'bull_thesis_invalid': {
                'price': int(price * 0.55),
                'description': 'Below this suggests bear market, not correction'
            },
            'cycle_thesis_invalid': {
                'price': int(price * 0.40),
                'description': 'Below this breaks historical cycle patterns'
            },
            'protocol_risk': {
                'price': int(price * 0.25),
                'description': 'Only if fundamental protocol issues'
            }
        }

    def _generate_trade_plan(self, price: float, mvrv: float, phase: str,
                            entries: List, exits: List, stops: Dict) -> str:
        """Generate human-readable trade plan"""

        if mvrv < 1.5:
            return f"""
TRADE PLAN - ACCUMULATION ZONE

Current Setup: MVRV {mvrv:.2f} in VALUE territory

ENTRIES:
1. Buy 25% position NOW at ${price:,}
2. Buy 35% more at ${int(price * 0.9):,} (10% dip)
3. Buy 40% more at ${int(price * 0.75):,} (25% dip)

EXITS (long-term targets):
- First take profit: ${int(price * 2):,} (sell 15%)
- Second take profit: ${int(price * 2.8):,} (sell 25%)
- Cycle top target: ${int(price * 3.5):,} (sell 40%)

STOP LOSS:
- Soft stop: ${stops['soft_stop']['price']:,} (re-evaluate)
- Hard stop: ${stops['hard_stop']['price']:,} (exit)

THESIS: Buy value, sell euphoria. MVRV < 2 = accumulate.
"""

        elif mvrv < 3.0:
            return f"""
TRADE PLAN - FAIR VALUE ZONE

Current Setup: MVRV {mvrv:.2f} in FAIR VALUE

ENTRIES:
- No aggressive new entries at current price
- Add only on 20%+ corrections

EXITS:
- Begin planning exit strategy
- First exit: ${int(price * 1.5):,} (sell 15-20%)

POSITION MANAGEMENT:
- Hold existing positions
- Trailing stop: 25% from highs

THESIS: Hold through fair value, prepare for distribution.
"""

        else:
            return f"""
TRADE PLAN - EXTENDED/DISTRIBUTION ZONE

Current Setup: MVRV {mvrv:.2f} in EXTENDED territory

ENTRIES:
- NO NEW ENTRIES at this level
- Wait for 40%+ correction to re-enter

EXITS (PRIORITY):
- Sell 25-30% immediately at ${price:,}
- Sell another 30% at ${int(price * 1.2):,}
- Trail remaining with 15% stop

STOP LOSS:
- Tight stops: ${stops['soft_stop']['price']:,}
- Exit remaining: ${stops['hard_stop']['price']:,}

THESIS: Preserve capital. Better to sell early than late.
"""


# =============================================================================
# WATCHLIST ENGINE
# =============================================================================

class WatchlistEngine:
    """
    Generate key metrics and levels traders should monitor.
    """

    def generate(self, price: float, mvrv: float, phase: str,
                liquidity: Dict, business_cycle: Dict) -> Dict:
        """Generate daily/weekly watchlist"""

        return {
            'daily_watchlist': self._daily_items(price, mvrv),
            'weekly_watchlist': self._weekly_items(liquidity, business_cycle),
            'key_levels_to_watch': self._key_levels(price, mvrv),
            'alerts_to_set': self._alerts(price, mvrv, phase),
            'red_flags': self._red_flags(mvrv, phase),
            'green_flags': self._green_flags(mvrv, phase)
        }

    def _daily_items(self, price: float, mvrv: float) -> List[Dict]:
        """Items to check daily"""
        return [
            {'metric': 'BTC Price', 'current': f'${price:,}', 'watch_for': 'Break of key levels'},
            {'metric': 'Fear & Greed', 'watch_for': 'Extremes (<20 or >80)'},
            {'metric': 'Funding Rates', 'watch_for': '>0.05% (overheated) or <0% (opportunity)'},
            {'metric': 'ETF Flows', 'watch_for': 'Large inflows/outflows ($500M+)'},
            {'metric': 'Exchange Flows', 'watch_for': 'Large exchange inflows (selling pressure)'},
        ]

    def _weekly_items(self, liq: Dict, biz: Dict) -> List[Dict]:
        """Items to check weekly"""
        return [
            {'metric': 'MVRV', 'watch_for': 'Zone changes (value→fair, fair→extended)'},
            {'metric': 'Net Liquidity', 'current': f"${liq.get('net_liquidity_T', 0):.2f}T", 'watch_for': 'Trend changes'},
            {'metric': 'Fed Balance Sheet', 'watch_for': 'QT pace changes'},
            {'metric': 'ISM Manufacturing', 'current': biz.get('ism_mfg', 0), 'watch_for': 'Cross above/below 50'},
            {'metric': 'Regional Fed Surveys', 'watch_for': 'Divergence from ISM (leading indicator)'},
            {'metric': 'BTC Dominance', 'watch_for': 'Trend for alt season timing'},
        ]

    def _key_levels(self, price: float, mvrv: float) -> Dict:
        """Key price levels to monitor"""
        return {
            'immediate_support': int(price * 0.92),
            'strong_support': int(price * 0.80),
            'critical_support': int(price * 0.65),
            'immediate_resistance': int(price * 1.10),
            'major_resistance': int(price * 1.25),
            'psychological': [50000, 75000, 100000, 125000, 150000, 200000]
        }

    def _alerts(self, price: float, mvrv: float, phase: str) -> List[Dict]:
        """Suggested price alerts"""
        alerts = [
            {'price': int(price * 0.90), 'action': 'Buy opportunity - 10% dip'},
            {'price': int(price * 0.75), 'action': 'Strong buy - 25% correction'},
            {'price': int(price * 1.20), 'action': 'Consider taking profits'},
        ]

        if mvrv < 2.0:
            alerts.append({'price': int(price * 1.50), 'action': 'First profit target'})
        else:
            alerts.append({'price': int(price * 0.85), 'action': 'Tighten stops'})

        return alerts

    def _red_flags(self, mvrv: float, phase: str) -> List[str]:
        """Warning signs to watch for"""
        flags = []

        if mvrv > 3.0:
            flags.append('MVRV elevated - distribution risk')
        if mvrv > 4.5:
            flags.append('MVRV in danger zone - cycle top approaching')

        flags.extend([
            'Fear & Greed sustained >80 for 2+ weeks',
            'Funding rates >0.1% (excessive leverage)',
            'Large exchange inflows (selling pressure)',
            'Pi Cycle approaching crossover',
            'Weekly RSI >85',
            'Break below 50D MA after parabolic run'
        ])

        return flags

    def _green_flags(self, mvrv: float, phase: str) -> List[str]:
        """Bullish signs to watch for"""
        flags = []

        if mvrv < 2.0:
            flags.append('MVRV in value zone - accumulate')

        flags.extend([
            'Fear & Greed <30 (opportunity)',
            'Large ETF inflows sustained',
            'Exchange outflows (accumulation)',
            'Fed pivot signals',
            'ISM bottoming and turning up',
            'Break above key resistance with volume'
        ])

        return flags
