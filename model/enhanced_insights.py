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

    # User-friendly phase names (technical name -> display name)
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
            'display_name': 'Cycle Bottom',
            'simple_explanation': 'The market has crashed. Everyone is scared. This is where generational wealth is made.',
            'description': 'Maximum fear and despair. Weak hands capitulate, selling at a loss. Price is below what most holders paid (realized price).',
            'psychology': 'Denial → Panic → Capitulation → Depression',
            'typical_mvrv': '< 0.5 (below realized price)',
            'typical_duration': '2-4 months',
            'typical_drawdown': '75-85% from ATH',
            'smart_money_behavior': 'Aggressive accumulation by long-term holders',
            'retail_behavior': 'Panic selling, declaring "crypto is dead"',
            'media_sentiment': 'Obituaries, regulatory FUD, "bubble popped"',
            'what_to_do': 'Maximum conviction buying. This is generational opportunity. Back up the truck.',
            'historical_examples': ['Dec 2018 ($3,150)', 'Mar 2020 ($3,800)', 'Nov 2022 ($15,500)'],
            'key_signals_to_exit': ['MVRV crosses above 0', 'F&G sustained >25', 'Price reclaims 200D MA'],
            'emoji': '🩸'
        },
        'ACCUMULATION': {
            'display_name': 'Recovery / Accumulation',
            'simple_explanation': 'The bleeding has stopped. Smart money is quietly buying while most people are still scared.',
            'description': 'Post-crash recovery. Smart money quietly accumulates while retail remains fearful and skeptical.',
            'psychology': 'Depression → Disbelief → Hope',
            'typical_mvrv': '0.5 - 1.5',
            'typical_duration': '6-12 months',
            'typical_drawdown': '60-75% from ATH',
            'smart_money_behavior': 'Steady accumulation, building positions',
            'retail_behavior': 'Skeptical, "dead cat bounce" calls, low engagement',
            'media_sentiment': 'Cautious, "crypto winter", focus on failures',
            'what_to_do': 'Continue accumulating. DCA aggressively. Build your full position before the bull starts.',
            'historical_examples': ['Q1-Q3 2019', 'Q2-Q4 2020', 'Q1-Q3 2023'],
            'key_signals_to_exit': ['MVRV > 1.5', 'Break above 200D MA with volume', 'ETF/institutional inflows'],
            'emoji': '🌱'
        },
        'EARLY_MARKUP': {
            'display_name': 'Early Bull Market',
            'simple_explanation': 'The bull market has started! Early adopters are getting in. Still lots of upside ahead.',
            'description': 'Bull market confirmed. Trend has reversed. Early adopters recognize the new cycle while skeptics still doubt.',
            'psychology': 'Hope → Optimism → Belief',
            'typical_mvrv': '1.5 - 2.5',
            'typical_duration': '3-6 months',
            'typical_drawdown': '30-40% corrections normal',
            'smart_money_behavior': 'Holding core positions, adding on dips',
            'retail_behavior': 'Starting to notice, FOMO beginning, "maybe it\'s real"',
            'media_sentiment': 'Cautiously positive, "recovery", institutional interest stories',
            'what_to_do': 'HOLD your positions. Buy dips aggressively. Do NOT sell too early - biggest gains are ahead.',
            'historical_examples': ['Q4 2020', 'Q4 2023 - Q1 2024'],
            'key_signals_to_exit': ['MVRV > 2.5', 'Weekly RSI > 70', 'Mainstream media attention'],
            'emoji': '🌤️'
        },
        'MID_MARKUP': {
            'display_name': 'Bull Market',
            'simple_explanation': 'Full bull market mode. Everyone is making money. Start planning your exit strategy.',
            'description': 'Bull market in full swing. Price climbing steadily. Retail FOMO accelerating. Greed increasing.',
            'psychology': 'Belief → Thrill → Euphoria building',
            'typical_mvrv': '2.5 - 4.0',
            'typical_duration': '4-8 months',
            'typical_drawdown': '20-30% corrections',
            'smart_money_behavior': 'Beginning to take profits, rotating to alts',
            'retail_behavior': 'Full FOMO, leveraged longs, "this time is different"',
            'media_sentiment': 'Bullish, price predictions, celebrity endorsements',
            'what_to_do': 'Create your exit plan NOW. Take 10-20% profits. Set trailing stops. Don\'t get greedy.',
            'historical_examples': ['Q1-Q2 2021', 'Q1-Q2 2024'],
            'key_signals_to_exit': ['MVRV > 4.0', 'Pi Cycle approaching', 'Extreme F&G (>80)'],
            'emoji': '☀️'
        },
        'LATE_MARKUP': {
            'display_name': 'Late Bull / Peak Zone',
            'simple_explanation': 'DANGER ZONE. Parabolic moves. Maximum greed. This is where you SELL, not buy.',
            'description': 'Final euphoric push. Parabolic price action. Maximum greed. Cycle peak approaching or occurring.',
            'psychology': 'Euphoria → Complacency → Anxiety',
            'typical_mvrv': '4.0 - 6.0+',
            'typical_duration': '1-3 months',
            'typical_drawdown': 'Volatile 10-20% swings',
            'smart_money_behavior': 'Distributing to retail, moving to stables',
            'retail_behavior': 'Maximum leverage, "we\'re going to $1M", quitting jobs',
            'media_sentiment': 'Mania, mainstream adoption hype, "new paradigm"',
            'what_to_do': 'SELL NOW. Distribute 50-70% of position. This is your exit window. Don\'t wait for the top.',
            'historical_examples': ['Nov-Dec 2017', 'Oct-Nov 2021'],
            'key_signals_to_exit': ['MVRV > 5.5', 'Pi Cycle cross', 'Funding > 0.1%', 'Weekly RSI > 90'],
            'emoji': '🔥'
        },
        'DISTRIBUTION': {
            'display_name': 'Cycle Top / Distribution',
            'simple_explanation': 'The top is in or forming. Smart money has exited. Don\'t be the last one holding.',
            'description': 'Cycle top forming. Smart money exits while retail still buying dips. Bear market imminent.',
            'psychology': 'Anxiety → Denial → Fear',
            'typical_mvrv': '3.5 - 5.5 (declining from peak)',
            'typical_duration': '1-3 months',
            'typical_drawdown': 'Initial 20-30% from ATH',
            'smart_money_behavior': 'Completed distribution, fully in stables',
            'retail_behavior': '"Buy the dip", "shakeout before $200K", denial',
            'media_sentiment': 'Mixed, "healthy correction", "institutional buying"',
            'what_to_do': 'Complete your exit. Move to stables. Do NOT buy dips. Prepare for bear market.',
            'historical_examples': ['Dec 2017 - Jan 2018', 'Nov 2021 - Jan 2022'],
            'key_signals_to_exit': ['Break below 50D MA', 'Lower highs forming', 'Volume declining on rallies'],
            'emoji': '⚠️'
        },
        'EARLY_MARKDOWN': {
            'display_name': 'Early Bear Market',
            'simple_explanation': 'Bear market has started. Denial is high. Every bounce is a trap. Stay out.',
            'description': 'Bear market confirmed. Denial still high. Bounces are selling opportunities, not buying opportunities.',
            'psychology': 'Fear → Desperation',
            'typical_mvrv': '2.0 - 3.5 (declining)',
            'typical_duration': '2-4 months',
            'typical_drawdown': '40-50% from ATH',
            'smart_money_behavior': 'Sidelined in stables, looking for re-entry much lower',
            'retail_behavior': 'Still buying dips, "diamond hands", copium',
            'media_sentiment': 'Concerned, regulatory fears, exchange issues',
            'what_to_do': 'Stay in stables. Do NOT buy dips yet. Every bounce is a trap. Wait for capitulation.',
            'historical_examples': ['Jan-May 2018', 'Jan-May 2022'],
            'key_signals_to_exit': ['Break below 200D MA', 'MVRV < 2.0', 'Major liquidation events'],
            'emoji': '🌧️'
        },
        'MID_MARKDOWN': {
            'display_name': 'Bear Market',
            'simple_explanation': 'Deep bear market. Hope is fading. Start preparing to buy - bottom is approaching.',
            'description': 'Bear market deepens. Hope fading. Approaching capitulation. Smart money starts nibbling.',
            'psychology': 'Desperation → Panic → Capitulation approaching',
            'typical_mvrv': '0.5 - 2.0 (declining)',
            'typical_duration': '4-8 months',
            'typical_drawdown': '60-80% from ATH',
            'smart_money_behavior': 'Starting to scale in slowly at deep value',
            'retail_behavior': 'Giving up, selling at loss, "never again"',
            'media_sentiment': 'Bearish, obituaries, "I told you so"',
            'what_to_do': 'Start your DCA plan. Small buys at deep value. Prepare accumulation strategy for capitulation.',
            'historical_examples': ['Jun-Nov 2018', 'Jun-Nov 2022'],
            'key_signals_to_exit': ['MVRV < 0.5', 'F&G < 15', 'Volume capitulation'],
            'emoji': '❄️'
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
                'display_name': education.get('display_name', self.PHASE_DISPLAY_NAMES.get(phase, phase)),
                'simple_explanation': education.get('simple_explanation', ''),
                'emoji': education.get('emoji', ''),
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

        display_name = self.PHASE_DISPLAY_NAMES.get(phase, phase)

        if phase == 'CAPITULATION':
            return f"We are at the CYCLE BOTTOM 🩸 - maximum fear and despair. MVRV at {mvrv:.2f} indicates price is {'below' if mvrv < 1 else 'near'} realized value. This is historically the BEST buying opportunity - generational wealth is made here. Only {progress:.0f}% through the cycle."

        elif phase == 'ACCUMULATION':
            return f"We are in RECOVERY / ACCUMULATION 🌱 at {progress:.0f}% cycle progress. MVRV {mvrv:.2f} shows we're still in value territory. Smart money is building positions while retail remains skeptical. Continue accumulating - the bull market hasn't started yet."

        elif phase == 'EARLY_MARKUP':
            return f"We are in the EARLY BULL MARKET 🌤️ - the new uptrend has been confirmed! At {progress:.0f}% cycle progress with MVRV {mvrv:.2f}, we're past accumulation but still early in the bull run. HOLD positions and buy dips. Most gains are still ahead."

        elif phase == 'MID_MARKUP':
            return f"We are in the BULL MARKET ☀️ at {progress:.0f}% cycle progress. MVRV {mvrv:.2f} shows we're in fair value territory. The bull is running strong! Start planning your exit strategy but don't sell too early - there's still upside."

        elif phase == 'LATE_MARKUP':
            return f"We are in LATE BULL / PEAK ZONE 🔥 - approaching cycle top! At {progress:.0f}% cycle progress with MVRV {mvrv:.2f}, we're in EXTENDED territory. This is your EXIT window. Scale out 50-70% of position. Don't be greedy."

        elif phase == 'DISTRIBUTION':
            return f"We are at the CYCLE TOP / DISTRIBUTION ⚠️ phase. Smart money has exited at {progress:.0f}% cycle progress. MVRV {mvrv:.2f} indicates overvaluation. Complete your exit NOW. Bear market is approaching."

        elif phase == 'EARLY_MARKDOWN':
            return f"We are in the EARLY BEAR MARKET 🌧️ - the top is in. At {progress:.0f}% cycle progress, every bounce is a TRAP. Stay in stables. Wait for capitulation before buying. Preserve capital."

        elif phase == 'MID_MARKDOWN':
            return f"We are in the BEAR MARKET ❄️ - deep in the downtrend. At {progress:.0f}% cycle progress, hope is fading. Start preparing your DCA plan - the bottom is approaching. Small nibbles at deep value only."

        return f"Current phase: {display_name} at {progress:.0f}% cycle progress with MVRV {mvrv:.2f}."

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

        next_phase_internal, triggers = transitions.get(current_phase, ('UNKNOWN', []))

        # Convert to friendly display name
        next_phase_display = self.PHASE_DISPLAY_NAMES.get(next_phase_internal, next_phase_internal)

        return {
            'next_phase': next_phase_display,
            'next_phase_internal': next_phase_internal,
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
        """Analyze potential drawdown scenarios and risk/reward"""

        # Historical drawdown by MVRV zone
        if mvrv < 1.0:
            typical_dd = 25
            max_dd = 40
            dd_desc = "Limited downside from deep value"
            downside_risk = 'LOW'
            upside_potential = 'EXTREME (5-10x)'
            risk_reward = 'EXCELLENT'
        elif mvrv < 2.0:
            typical_dd = 35
            max_dd = 50
            dd_desc = "Moderate drawdown possible in corrections"
            downside_risk = 'LOW-MEDIUM'
            upside_potential = 'HIGH (3-5x)'
            risk_reward = 'FAVORABLE'
        elif mvrv < 3.0:
            typical_dd = 45
            max_dd = 60
            dd_desc = "Significant drawdown risk in bear market"
            downside_risk = 'MEDIUM'
            upside_potential = 'GOOD (2-3x)'
            risk_reward = 'FAVORABLE'
        elif mvrv < 4.5:
            typical_dd = 55
            max_dd = 70
            dd_desc = "High drawdown risk from extended levels"
            downside_risk = 'MEDIUM-HIGH'
            upside_potential = 'LIMITED (1.5-2x)'
            risk_reward = 'NEUTRAL'
        else:
            typical_dd = 70
            max_dd = 85
            dd_desc = "Severe drawdown risk from euphoria zone"
            downside_risk = 'HIGH'
            upside_potential = 'MINIMAL (<1.5x)'
            risk_reward = 'UNFAVORABLE'

        return {
            'typical_drawdown_pct': typical_dd,
            'max_historical_drawdown_pct': max_dd,
            'description': dd_desc,
            'price_at_typical_dd': int(price * (1 - typical_dd/100)),
            'price_at_max_dd': int(price * (1 - max_dd/100)),
            'mental_preparation': f"If you buy here, be prepared for price to drop to ${int(price * (1 - typical_dd/100)):,} ({typical_dd}% drawdown) without panicking.",
            'downside_risk': downside_risk,
            'upside_potential': upside_potential,
            'risk_reward_rating': risk_reward
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


# =============================================================================
# PEAK TIMING FORECAST ENGINE
# =============================================================================

class PeakTimingEngine:
    """
    Forecasts cycle peak timing using historical patterns, current phase,
    and Monte Carlo simulation.
    """

    # Historical cycle data
    CYCLE_HISTORY = {
        'cycle_1': {
            'halving': '2012-11-28',
            'bottom': '2011-11-18',
            'peak': '2013-11-29',
            'days_halving_to_peak': 366,
            'days_bottom_to_peak': 742,
            'peak_mvrv': 5.8
        },
        'cycle_2': {
            'halving': '2016-07-09',
            'bottom': '2015-01-14',
            'peak': '2017-12-17',
            'days_halving_to_peak': 526,
            'days_bottom_to_peak': 1068,
            'peak_mvrv': 4.7
        },
        'cycle_3': {
            'halving': '2020-05-11',
            'bottom': '2018-12-15',
            'peak': '2021-11-10',
            'days_halving_to_peak': 548,
            'days_bottom_to_peak': 1060,
            'peak_mvrv': 3.9
        },
        'cycle_4': {
            'halving': '2024-04-20',
            'bottom': '2022-11-21',
            'peak': None,  # TBD
            'days_halving_to_peak': None,
            'days_bottom_to_peak': None,
            'peak_mvrv': None
        }
    }

    def analyze(self, phase: str, mvrv: float, cycle_progress: float,
                price: float, fear_greed: int, liquidity_score: float) -> Dict:
        """Generate peak timing forecast"""

        # Current cycle reference dates
        halving_date = date(2024, 4, 20)
        cycle_bottom = date(2022, 11, 21)
        today = date.today()

        days_since_halving = (today - halving_date).days
        days_since_bottom = (today - cycle_bottom).days

        # Historical pattern analysis
        historical_analysis = self._analyze_historical_patterns(days_since_halving, days_since_bottom)

        # Monte Carlo peak timing simulation
        monte_carlo = self._monte_carlo_peak_timing(
            days_since_halving, days_since_bottom, mvrv, cycle_progress
        )

        # Phase-based timeline
        phase_timeline = self._phase_based_timeline(phase, mvrv, cycle_progress)

        # Composite forecast
        composite = self._composite_forecast(historical_analysis, monte_carlo, phase_timeline, mvrv)

        # Peak price estimates
        price_targets = self._estimate_peak_prices(price, mvrv, monte_carlo)

        return {
            'current_cycle': {
                'halving_date': str(halving_date),
                'cycle_bottom': str(cycle_bottom),
                'days_since_halving': days_since_halving,
                'days_since_bottom': days_since_bottom,
                'current_mvrv': mvrv,
                'cycle_progress_pct': cycle_progress
            },
            'historical_patterns': historical_analysis,
            'monte_carlo_timing': monte_carlo,
            'phase_based_timeline': phase_timeline,
            'composite_forecast': composite,
            'peak_price_estimates': price_targets,
            'confidence_factors': self._confidence_factors(mvrv, fear_greed, liquidity_score),
            'key_dates_to_watch': self._key_dates()
        }

    def _analyze_historical_patterns(self, days_since_halving: int, days_since_bottom: int) -> Dict:
        """Analyze historical cycle patterns"""

        # Average days from halving to peak (cycles 1-3)
        avg_halving_to_peak = (366 + 526 + 548) / 3  # ~480 days
        std_halving_to_peak = 98  # Standard deviation

        # Average days from bottom to peak
        avg_bottom_to_peak = (742 + 1068 + 1060) / 3  # ~957 days
        std_bottom_to_peak = 186

        # Project peak dates
        halving_date = date(2024, 4, 20)
        bottom_date = date(2022, 11, 21)

        # Based on halving
        peak_from_halving_early = halving_date + timedelta(days=int(avg_halving_to_peak - std_halving_to_peak))
        peak_from_halving_mid = halving_date + timedelta(days=int(avg_halving_to_peak))
        peak_from_halving_late = halving_date + timedelta(days=int(avg_halving_to_peak + std_halving_to_peak))

        # Based on bottom
        peak_from_bottom_early = bottom_date + timedelta(days=int(avg_bottom_to_peak - std_bottom_to_peak))
        peak_from_bottom_mid = bottom_date + timedelta(days=int(avg_bottom_to_peak))
        peak_from_bottom_late = bottom_date + timedelta(days=int(avg_bottom_to_peak + std_bottom_to_peak))

        # Progress based on halving
        halving_progress = (days_since_halving / avg_halving_to_peak) * 100
        bottom_progress = (days_since_bottom / avg_bottom_to_peak) * 100

        return {
            'from_halving': {
                'avg_days': int(avg_halving_to_peak),
                'current_days': days_since_halving,
                'progress_pct': round(min(100, halving_progress), 1),
                'remaining_days_est': max(0, int(avg_halving_to_peak - days_since_halving)),
                'peak_window': {
                    'early': str(peak_from_halving_early),
                    'mid': str(peak_from_halving_mid),
                    'late': str(peak_from_halving_late)
                }
            },
            'from_bottom': {
                'avg_days': int(avg_bottom_to_peak),
                'current_days': days_since_bottom,
                'progress_pct': round(min(100, bottom_progress), 1),
                'remaining_days_est': max(0, int(avg_bottom_to_peak - days_since_bottom)),
                'peak_window': {
                    'early': str(peak_from_bottom_early),
                    'mid': str(peak_from_bottom_mid),
                    'late': str(peak_from_bottom_late)
                }
            },
            'cycle_comparison': [
                {'cycle': 1, 'halving_to_peak': 366, 'bottom_to_peak': 742, 'peak_mvrv': 5.8},
                {'cycle': 2, 'halving_to_peak': 526, 'bottom_to_peak': 1068, 'peak_mvrv': 4.7},
                {'cycle': 3, 'halving_to_peak': 548, 'bottom_to_peak': 1060, 'peak_mvrv': 3.9},
            ],
            'pattern_note': 'Cycles lengthening: 366 → 526 → 548 days from halving. Peak MVRV declining: 5.8 → 4.7 → 3.9'
        }

    def _monte_carlo_peak_timing(self, days_since_halving: int, days_since_bottom: int,
                                  mvrv: float, cycle_progress: float) -> Dict:
        """
        Monte Carlo simulation for peak timing.

        CRITICAL: Time-based estimates are overridden by MVRV gate.
        - Peak MVRV is historically 3.9-5.8 (declining each cycle)
        - If current MVRV < 3.0, peak has NOT occurred regardless of time elapsed
        - This cycle may be extended due to macro conditions (ISM contraction since Q3 2022)
        """

        n_simulations = 10000

        # Historical parameters (from halving)
        # Cycle 1: 366 days, Cycle 2: 526 days, Cycle 3: 548 days
        # Trend: cycles lengthening by ~80-90 days each
        # Cycle 4 projection: 548 + 80 = ~628 days, with possible extension to 700+

        # Use extended mean for cycle 4 (macro headwinds, ISM contraction)
        mean_days = 628  # Extended from historical due to cycle lengthening
        std_days = 120   # Wider uncertainty this cycle

        # Further adjust if MVRV shows we're early (hasn't even started run-up)
        if mvrv < 2.0:
            # Still early in cycle - extend projections
            mean_days = max(mean_days, days_since_halving + 180)
        elif mvrv < 2.5:
            mean_days = max(mean_days, days_since_halving + 120)

        # Run simulation
        np.random.seed(42)  # Reproducible
        simulated_days = np.random.normal(mean_days, std_days, n_simulations)
        simulated_days = np.clip(simulated_days, 400, 900)  # Extended realistic bounds

        # Calculate remaining days
        remaining_days = simulated_days - days_since_halving
        remaining_days = np.clip(remaining_days, 0, 600)

        # Calculate percentiles
        p10 = int(np.percentile(remaining_days, 10))
        p25 = int(np.percentile(remaining_days, 25))
        p50 = int(np.percentile(remaining_days, 50))
        p75 = int(np.percentile(remaining_days, 75))
        p90 = int(np.percentile(remaining_days, 90))

        today = date.today()

        # Peak date estimates
        peak_p10 = today + timedelta(days=max(30, p10))  # At least 30 days out
        peak_p25 = today + timedelta(days=max(60, p25))
        peak_p50 = today + timedelta(days=max(90, p50))
        peak_p75 = today + timedelta(days=max(120, p75))
        peak_p90 = today + timedelta(days=max(180, p90))

        # MVRV-GATED probability calculation
        # Peak NEVER occurs below MVRV 3.0 historically
        # This is the critical override - time doesn't matter if MVRV says we're early
        if mvrv < 2.0:
            # Clearly early in cycle - peak is 0% likely to have passed
            prob_passed = 0.0
            prob_3m = 5.0   # Very unlikely
            prob_6m = 15.0
            prob_12m = 45.0
        elif mvrv < 2.5:
            # Mid-cycle - still very unlikely peak passed
            prob_passed = 2.0
            prob_3m = 10.0
            prob_6m = 25.0
            prob_12m = 60.0
        elif mvrv < 3.0:
            # Getting warmer but still below peak zone
            prob_passed = 5.0
            prob_3m = 15.0
            prob_6m = 35.0
            prob_12m = 70.0
        elif mvrv < 3.5:
            # Approaching peak zone
            prob_passed = 10.0
            prob_3m = 25.0
            prob_6m = 50.0
            prob_12m = 85.0
        else:
            # In peak zone (MVRV > 3.5) - use time-based MC probabilities
            prob_passed = (simulated_days < days_since_halving).mean() * 100
            prob_3m = ((remaining_days > 0) & (remaining_days <= 90)).mean() * 100
            prob_6m = ((remaining_days > 0) & (remaining_days <= 180)).mean() * 100
            prob_12m = ((remaining_days > 0) & (remaining_days <= 365)).mean() * 100

        return {
            'simulations': n_simulations,
            'remaining_days': {
                'p10': max(30, p10),
                'p25': max(60, p25),
                'median': max(90, p50),
                'p75': max(120, p75),
                'p90': max(180, p90)
            },
            'peak_date_estimates': {
                'earliest_likely': str(peak_p10),
                'early': str(peak_p25),
                'most_likely': str(peak_p50),
                'late': str(peak_p75),
                'latest_likely': str(peak_p90)
            },
            'probabilities': {
                'peak_already_passed': round(prob_passed, 1),
                'peak_within_3_months': round(prob_3m, 1),
                'peak_within_6_months': round(prob_6m, 1),
                'peak_within_12_months': round(prob_12m, 1)
            },
            'mvrv_gate': {
                'current_mvrv': mvrv,
                'peak_mvrv_threshold': 3.5,
                'note': f'MVRV {mvrv:.2f} is {"below" if mvrv < 3.5 else "in"} peak zone (3.5+). Peak requires elevated MVRV.'
            },
            'interpretation': self._interpret_timing(max(90, p50), prob_6m, mvrv)
        }

    def _interpret_timing(self, median_days: int, prob_6m: float, mvrv: float) -> str:
        """Interpret Monte Carlo timing results"""

        if median_days < 60:
            timing = "IMMINENT"
            urgency = "Peak likely within 2 months. Distribution phase critical."
        elif median_days < 120:
            timing = "NEAR-TERM"
            urgency = "Peak likely within 4 months. Begin scaling out."
        elif median_days < 240:
            timing = "MID-TERM"
            urgency = "Peak likely within 8 months. Prepare exit strategy."
        elif median_days < 365:
            timing = "EXTENDED"
            urgency = "Peak likely within 12 months. Still time to accumulate."
        else:
            timing = "DISTANT"
            urgency = "Peak likely 12+ months away. Accumulation zone."

        mvrv_context = ""
        if mvrv < 2.0:
            mvrv_context = f" MVRV {mvrv:.2f} confirms we're early - room for significant upside."
        elif mvrv < 3.0:
            mvrv_context = f" MVRV {mvrv:.2f} shows fair value - balanced risk/reward."
        else:
            mvrv_context = f" MVRV {mvrv:.2f} elevated - timing for exits more important."

        return f"{timing}: {urgency}{mvrv_context}"

    def _phase_based_timeline(self, phase: str, mvrv: float, progress: float) -> Dict:
        """Timeline based on current phase"""

        phase_durations = {
            'CAPITULATION': {'to_accumulation': (1, 3), 'to_peak': (24, 36)},
            'ACCUMULATION': {'to_early_markup': (3, 9), 'to_peak': (18, 30)},
            'EARLY_MARKUP': {'to_mid_markup': (3, 6), 'to_peak': (12, 24)},
            'MID_MARKUP': {'to_late_markup': (4, 8), 'to_peak': (6, 15)},
            'LATE_MARKUP': {'to_distribution': (1, 3), 'to_peak': (0, 4)},
            'DISTRIBUTION': {'to_bear': (1, 3), 'to_peak': (0, 1)},
            'EARLY_MARKDOWN': {'to_bottom': (8, 14), 'to_peak': (30, 42)},
            'MID_MARKDOWN': {'to_bottom': (2, 8), 'to_peak': (26, 38)}
        }

        timing = phase_durations.get(phase, {'to_peak': (12, 24)})
        min_months, max_months = timing.get('to_peak', (12, 24))

        today = date.today()
        peak_earliest = today + timedelta(days=min_months * 30)
        peak_latest = today + timedelta(days=max_months * 30)
        peak_mid = today + timedelta(days=((min_months + max_months) / 2) * 30)

        return {
            'current_phase': phase,
            'months_to_peak': {
                'min': min_months,
                'max': max_months,
                'mid': (min_months + max_months) / 2
            },
            'peak_window': {
                'earliest': str(peak_earliest),
                'most_likely': str(peak_mid),
                'latest': str(peak_latest)
            },
            'phase_interpretation': self._phase_to_timing_text(phase, min_months, max_months)
        }

    def _phase_to_timing_text(self, phase: str, min_m: int, max_m: int) -> str:
        """Convert phase to timing interpretation"""

        interpretations = {
            'CAPITULATION': f"At cycle bottom. Peak typically {min_m}-{max_m} months away. Maximum accumulation window.",
            'ACCUMULATION': f"Recovery phase. Peak typically {min_m}-{max_m} months away. Continue building position.",
            'EARLY_MARKUP': f"Bull market confirmed. Peak typically {min_m}-{max_m} months away. Hold and add dips.",
            'MID_MARKUP': f"Bull running strong. Peak typically {min_m}-{max_m} months away. Start planning exits.",
            'LATE_MARKUP': f"Approaching peak zone. Peak likely within {min_m}-{max_m} months. Active distribution recommended.",
            'DISTRIBUTION': f"At or near peak. Peak may be NOW or within {min_m}-{max_m} months. Complete exits.",
            'EARLY_MARKDOWN': f"Bear market started. Next peak {min_m}-{max_m} months away. Preserve capital.",
            'MID_MARKDOWN': f"Deep bear market. Next peak {min_m}-{max_m} months away. Prepare for accumulation."
        }

        return interpretations.get(phase, f"Peak estimated {min_m}-{max_m} months away.")

    def _composite_forecast(self, historical: Dict, mc: Dict, phase: Dict, mvrv: float) -> Dict:
        """
        Combine all methods into composite forecast.

        OPTIMIZED v7.2: Better integration of timing methodologies.

        Historical halving patterns show cycles are LENGTHENING:
        - Cycle 1: 366 days halving-to-peak
        - Cycle 2: 526 days
        - Cycle 3: 548 days
        - Cycle 4: Expected 600-700 days (cycle lengthening)

        Weight adjustment by MVRV (accounts for cycle position):
        - MVRV < 2.0: Phase 40%, Historical 25%, MC 15%, Reserve 20% for LPPL
        - MVRV 2.0-3.0: Phase 30%, Historical 25%, MC 25%, Reserve 20% for LPPL
        - MVRV > 3.0: Phase 20%, Historical 20%, MC 40%, Reserve 20% for LPPL

        Note: 20% is reserved for LPPL integration done in _integrate_lppl_with_peak_timing
        """
        hist_mid_days_original = historical['from_halving']['remaining_days_est']
        mc_mid_days = mc['remaining_days']['median']
        phase_mid_days = phase['months_to_peak']['mid'] * 30

        # Account for cycle lengthening: if historical shows 0 (past average),
        # use extended estimate based on cycle lengthening trend
        # Historical averages: C1=366, C2=526, C3=548 days → ~6% lengthening per cycle
        # C4 projection: 548 * 1.15 ≈ 630-700 days (conservative: 700-750)
        halving_date = date(2024, 4, 20)
        days_since_halving = (date.today() - halving_date).days

        if hist_mid_days_original == 0:
            # Past the old average (480 days) - use extended cycle 4 estimate
            extended_avg = 730  # Cycle 4 with ~15% lengthening from C3
            hist_mid_days = max(30, extended_avg - days_since_halving)  # Min 30 days
            hist_adjusted = True
        else:
            hist_mid_days = hist_mid_days_original
            hist_adjusted = False

        # Dynamic weighting based on MVRV
        if mvrv < 2.0:
            # Early cycle: phase-based dominates, historical useful
            weight_phase = 0.40
            weight_mc = 0.15
            weight_hist = 0.25
            # Remaining 20% allocated to LPPL in integration step
            confidence = 'LOW'
            note = 'Early cycle - phase-based and LPPL timing dominate'
        elif mvrv < 3.0:
            # Mid cycle: balanced approach
            weight_phase = 0.30
            weight_mc = 0.25
            weight_hist = 0.25
            confidence = 'MEDIUM'
            note = 'Mid-cycle - balanced timing approach with LPPL'
        elif mvrv < 4.0:
            # Late cycle: Monte Carlo more important
            weight_phase = 0.20
            weight_mc = 0.40
            weight_hist = 0.20
            confidence = 'HIGH'
            note = 'Late cycle - peak approaching, MC timing important'
        else:
            # Extended: peak imminent
            weight_phase = 0.15
            weight_mc = 0.45
            weight_hist = 0.20
            confidence = 'VERY HIGH'
            note = 'Extended valuation - peak likely imminent'

        # Normalize weights to 80% (LPPL gets 20% in integration)
        total_base = weight_phase + weight_mc + weight_hist
        weight_phase = weight_phase / total_base * 0.80
        weight_mc = weight_mc / total_base * 0.80
        weight_hist = weight_hist / total_base * 0.80

        # Weighted average (80% of final - LPPL adds remaining 20%)
        composite_days = int(
            hist_mid_days * weight_hist +
            mc_mid_days * weight_mc +
            phase_mid_days * weight_phase
        )

        # Ensure minimum days based on MVRV (can't peak with MVRV < 3.0)
        if mvrv < 2.0:
            composite_days = max(composite_days, 240)  # At least 8 months
        elif mvrv < 2.5:
            composite_days = max(composite_days, 150)  # At least 5 months
        elif mvrv < 3.0:
            composite_days = max(composite_days, 90)   # At least 3 months

        today = date.today()
        composite_peak = today + timedelta(days=composite_days)

        # Determine quarter
        peak_quarter = f"Q{(composite_peak.month - 1) // 3 + 1} {composite_peak.year}"

        return {
            'days_to_peak_est': composite_days,
            'peak_date_est': str(composite_peak),
            'peak_quarter': peak_quarter,
            'confidence': confidence,
            'confidence_note': note,
            'methodology': f'Weighted by MVRV ({mvrv:.2f}): {int(weight_hist*100)}% historical, {int(weight_mc*100)}% MC, {int(weight_phase*100)}% phase (80% base, 20% LPPL added in integration)',
            'weights_used': {
                'historical': round(weight_hist, 2),
                'monte_carlo': round(weight_mc, 2),
                'phase_based': round(weight_phase, 2),
                'lppl_reserved': 0.20
            },
            'component_estimates': {
                'historical_days': hist_mid_days,
                'historical_adjusted': hist_adjusted,
                'historical_note': 'Adjusted for cycle lengthening (C4 ~730 days)' if hist_adjusted else 'Within historical average',
                'monte_carlo_days': mc_mid_days,
                'phase_based_days': int(phase_mid_days)
            },
            'recommendation': self._timing_recommendation(composite_days, mvrv, phase['current_phase'])
        }

    def _timing_recommendation(self, days: int, mvrv: float, phase: str) -> str:
        """Generate timing-based recommendation"""

        if days < 90 and mvrv > 3.0:
            return "URGENT: Peak likely within 3 months. Prioritize distribution. Don't wait for the top."
        elif days < 180 and mvrv > 2.5:
            return "ACTIVE DISTRIBUTION: Peak within 6 months. Scale out 50%+ of position."
        elif days < 365 and mvrv > 2.0:
            return "PREPARE EXITS: Peak within 12 months. Create exit plan, start small profit-taking."
        elif days < 365 and mvrv < 2.0:
            return "ACCUMULATE: Still early. Peak 6-12 months away. Buy dips aggressively."
        else:
            return "PATIENT ACCUMULATION: Peak likely 12+ months away. DCA and hold conviction."

    def _estimate_peak_prices(self, current_price: float, mvrv: float, mc: Dict) -> Dict:
        """Estimate peak prices based on MVRV targets"""

        # Historical peak MVRVs: 5.8 → 4.7 → 3.9 (declining)
        # Estimate cycle 4 peak MVRV: 3.2 - 4.0

        # Current realized price approximation
        realized_price = current_price / mvrv if mvrv > 0 else current_price

        # Peak MVRV scenarios
        conservative_mvrv = 3.0
        base_mvrv = 3.5
        optimistic_mvrv = 4.2

        return {
            'current_price': int(current_price),
            'estimated_realized_price': int(realized_price),
            'peak_scenarios': {
                'conservative': {
                    'mvrv_target': conservative_mvrv,
                    'price_target': int(realized_price * conservative_mvrv),
                    'upside_pct': round((realized_price * conservative_mvrv / current_price - 1) * 100, 0)
                },
                'base_case': {
                    'mvrv_target': base_mvrv,
                    'price_target': int(realized_price * base_mvrv),
                    'upside_pct': round((realized_price * base_mvrv / current_price - 1) * 100, 0)
                },
                'optimistic': {
                    'mvrv_target': optimistic_mvrv,
                    'price_target': int(realized_price * optimistic_mvrv),
                    'upside_pct': round((realized_price * optimistic_mvrv / current_price - 1) * 100, 0)
                }
            },
            'note': 'Peak MVRV declining each cycle: 5.8 → 4.7 → 3.9. Expect 3.0-4.0 for cycle 4.'
        }

    def _confidence_factors(self, mvrv: float, fg: int, liq_score: float) -> Dict:
        """Factors affecting forecast confidence"""

        factors = []

        # MVRV clarity
        if mvrv < 1.5:
            factors.append({'factor': 'MVRV', 'impact': 'LOW CONFIDENCE', 'reason': 'Early cycle - wide range of outcomes'})
        elif mvrv < 2.5:
            factors.append({'factor': 'MVRV', 'impact': 'MODERATE', 'reason': 'Mid-cycle - timing still uncertain'})
        elif mvrv < 4.0:
            factors.append({'factor': 'MVRV', 'impact': 'HIGH CONFIDENCE', 'reason': 'Extended - peak window narrowing'})
        else:
            factors.append({'factor': 'MVRV', 'impact': 'VERY HIGH', 'reason': 'Euphoria zone - peak imminent'})

        # Sentiment
        if fg < 25:
            factors.append({'factor': 'Sentiment', 'impact': 'BULLISH', 'reason': 'Extreme fear - likely not at top'})
        elif fg > 75:
            factors.append({'factor': 'Sentiment', 'impact': 'BEARISH', 'reason': 'Extreme greed - top may be near'})
        else:
            factors.append({'factor': 'Sentiment', 'impact': 'NEUTRAL', 'reason': 'Mixed sentiment'})

        # Liquidity
        if liq_score > 60:
            factors.append({'factor': 'Liquidity', 'impact': 'SUPPORTIVE', 'reason': 'Strong liquidity - can extend cycle'})
        elif liq_score < 40:
            factors.append({'factor': 'Liquidity', 'impact': 'HEADWIND', 'reason': 'Weak liquidity - may shorten cycle'})

        return {
            'factors': factors,
            'overall_confidence': 'HIGH' if mvrv > 2.5 else 'MODERATE' if mvrv > 1.5 else 'LOW'
        }

    def _key_dates(self) -> List[Dict]:
        """Key dates to watch"""

        return [
            {'date': '2024-04-20', 'event': 'Bitcoin Halving', 'status': 'COMPLETED', 'impact': 'Supply shock initiated'},
            {'date': '2025-Q1', 'event': 'Post-halving acceleration', 'status': 'CURRENT', 'impact': 'Historical parabolic phase'},
            {'date': '2025-Q2/Q3', 'event': 'Potential early peak window', 'status': 'UPCOMING', 'impact': 'Watch for distribution signals'},
            {'date': '2025-Q4', 'event': 'Historical peak window', 'status': 'UPCOMING', 'impact': 'Most likely peak zone based on patterns'},
            {'date': '2026-Q1', 'event': 'Extended peak window', 'status': 'UPCOMING', 'impact': 'If cycle lengthening continues'}
        ]


# =============================================================================
# POWER LAW WITH LPPL BUBBLE DETECTION ENGINE
# =============================================================================

class PowerLawLPPLEngine:
    """
    Bitcoin Power Law with Log-Periodic Power Law (LPPL) Bubble Detection.

    Based on Stephen Perrenod's research:
    - Bitcoin follows continuous scale invariance: P ~ T^k
    - Bubbles follow discrete scale invariance with log-periodic oscillations
    - λ (log-periodic wavelength) ≈ 2.07 determines bubble spacing

    Key findings:
    - Power law index k ≈ 5.3-5.7 (uses 5.4 as baseline)
    - Fundamental mode bubbles: 2011, 2013, 2017 peaks
    - First harmonic (√λ): 2021 double-peak
    - Next fundamental bubble predicted: May 2027 (age ~18.4 years)
    - 2025 has NO bubble predicted under this framework

    Reference: https://stephenperrenod.substack.com/p/why-is-there-no-bitcoin-bubble-in
    """

    # Bitcoin Genesis: January 3, 2009
    GENESIS_DATE = date(2009, 1, 3)

    # Power Law Parameters
    POWER_LAW_INDEX_USD = 5.7      # k for USD price
    POWER_LAW_INDEX_GOLD = 5.3    # k for gold-denominated
    POWER_LAW_INDEX = 5.4         # Average/baseline

    # LPPL Parameters (from Fourier/wavelet analysis)
    LAMBDA = 2.07                  # Log-periodic wavelength
    LAMBDA_HARMONIC = np.sqrt(2.07)  # First harmonic ≈ 1.44

    # Historical bubble ages (years since genesis)
    HISTORICAL_BUBBLES = {
        '2011': 2.92,   # Nov 2011 peak
        '2013': 4.92,   # Dec 2013 peak
        '2017': 8.95,   # Dec 2017 peak
        '2021': 12.89,  # Nov 2021 peak (harmonic)
    }

    # Calibration constant (derived from fitting historical data)
    # P = A * T^k where A is calibrated to historical prices
    CALIBRATION_A = 0.0002  # Approximate - gives reasonable fair values

    def analyze(self, price: float, btc_age_days: int = None) -> Dict:
        """
        Comprehensive Power Law and LPPL analysis.

        Args:
            price: Current BTC price in USD
            btc_age_days: Days since genesis (calculated if not provided)

        Returns:
            Dict with power law metrics, bubble status, and predictions
        """
        today = date.today()

        if btc_age_days is None:
            btc_age_days = (today - self.GENESIS_DATE).days

        btc_age_years = btc_age_days / 365.25

        # Power Law calculations
        power_law = self._calculate_power_law(price, btc_age_years)

        # LPPL Bubble analysis
        lppl = self._analyze_lppl_bubbles(btc_age_years, price, power_law['fair_value'])

        # Bubble predictions
        predictions = self._predict_bubbles(btc_age_years)

        # Current status assessment
        status = self._assess_current_status(
            price, power_law, lppl, btc_age_years
        )

        return {
            'bitcoin_age': {
                'days': btc_age_days,
                'years': round(btc_age_years, 2),
                'genesis_date': str(self.GENESIS_DATE)
            },
            'power_law': power_law,
            'lppl_analysis': lppl,
            'bubble_predictions': predictions,
            'current_status': status,
            'methodology': {
                'power_law_index': self.POWER_LAW_INDEX,
                'lambda': self.LAMBDA,
                'reference': 'Perrenod LPPL Model'
            }
        }

    def _calculate_power_law(self, price: float, age_years: float) -> Dict:
        """
        Calculate Power Law fair value and deviation.

        Formula: P_fair = A * T^k
        Where T is age in years and k is the power law index.
        """
        # Calculate fair value using power law
        # Using a more sophisticated calibration based on historical data
        # The formula P = A * T^k needs calibration

        # Calibrate A using known data point: $69,000 at age 12.89 years (Nov 2021)
        # A = P / T^k = 69000 / (12.89^5.4) ≈ 0.085
        # But that was a bubble peak. Use support line instead.
        # Support at Nov 2022 (~$16,000 at age ~13.9): A ≈ 0.015

        # Better approach: Use regression-derived coefficients
        # Log(P) = log(A) + k * log(T)
        # From historical data fitting: log(A) ≈ -2.5, so A ≈ 0.082

        # CALIBRATED coefficients from historical cycle data (v7.2):
        # - Nov 2022 cycle bottom: $15,500 at age 13.9 years
        # - Nov 2021 cycle peak: $69,000 at age 12.89 years
        # These anchor the support (bottoms) and upper (peaks) bounds.
        A_support = 0.0104   # Lower bound - where cycle bottoms occur
        A_median = 0.027     # Median fair value (geometric mean)
        A_upper = 0.070      # Upper bound - where cycle peaks occur

        fair_value_support = A_support * (age_years ** self.POWER_LAW_INDEX)
        fair_value_median = A_median * (age_years ** self.POWER_LAW_INDEX)
        fair_value_upper = A_upper * (age_years ** self.POWER_LAW_INDEX)

        # Deviation from median fair value
        deviation_pct = ((price - fair_value_median) / fair_value_median) * 100

        # Percentile within the power law corridor
        if price <= fair_value_support:
            percentile = 0
        elif price >= fair_value_upper:
            percentile = 100
        else:
            # Linear interpolation within corridor
            range_size = fair_value_upper - fair_value_support
            percentile = ((price - fair_value_support) / range_size) * 100

        # Zone classification
        if percentile < 20:
            zone = 'DEEP_VALUE'
            zone_desc = 'At or below power law support - maximum opportunity'
        elif percentile < 40:
            zone = 'VALUE'
            zone_desc = 'Lower half of corridor - favorable entry'
        elif percentile < 60:
            zone = 'FAIR'
            zone_desc = 'Middle of corridor - fair value'
        elif percentile < 80:
            zone = 'EXTENDED'
            zone_desc = 'Upper corridor - above fair value'
        else:
            zone = 'BUBBLE_TERRITORY'
            zone_desc = 'Above corridor - bubble conditions possible'

        return {
            'fair_value': int(fair_value_median),  # Primary fair value reference
            'fair_value_support': int(fair_value_support),
            'fair_value_median': int(fair_value_median),
            'fair_value_upper': int(fair_value_upper),
            'current_price': int(price),
            'deviation_from_median_pct': round(deviation_pct, 1),
            'percentile_in_corridor': round(percentile, 1),
            'zone': zone,
            'zone_description': zone_desc,
            'power_law_index': self.POWER_LAW_INDEX
        }

    def _analyze_lppl_bubbles(self, age_years: float, price: float,
                               fair_value: float) -> Dict:
        """
        Analyze Log-Periodic Power Law bubble patterns.

        LPPL bubbles follow discrete scale invariance where peaks occur
        at ages related by the log-periodic wavelength λ ≈ 2.07.

        Fundamental mode: T_n+1 / T_n ≈ λ
        First harmonic: T_n+1 / T_n ≈ √λ
        """
        # Calculate ratios from historical bubbles
        bubble_ages = list(self.HISTORICAL_BUBBLES.values())

        # Calculate age ratios
        ratios = []
        for i in range(1, len(bubble_ages)):
            ratio = bubble_ages[i] / bubble_ages[i-1]
            ratios.append(ratio)

        # Check if current age aligns with bubble pattern
        last_bubble_age = bubble_ages[-1]  # 2021 peak at 12.89 years

        # Next fundamental bubble: last_age * λ
        next_fundamental = last_bubble_age * self.LAMBDA  # ≈ 26.7 years (2035)

        # But 2021 was a harmonic, so check fundamental sequence
        # 2017 was at 8.95 years, next fundamental = 8.95 * λ ≈ 18.5 years (May 2027)
        fundamental_2017_age = self.HISTORICAL_BUBBLES['2017']
        next_fundamental_from_2017 = fundamental_2017_age * self.LAMBDA  # ~18.5 years

        # Calculate proximity to bubble windows
        proximity_to_next_fundamental = abs(age_years - next_fundamental_from_2017)
        proximity_to_2027_bubble = next_fundamental_from_2017 - age_years

        # Bubble window detection (within 0.5 years of predicted peak)
        in_bubble_window = proximity_to_next_fundamental < 0.5

        # Calculate oscillation phase
        # Using log-periodic oscillation: cos(ω * ln(Tc - t))
        # Simplified: check if we're in bubble-prone phase
        log_age = np.log(age_years)
        omega = 2 * np.pi / np.log(self.LAMBDA)
        oscillation_phase = np.cos(omega * log_age)

        # Phase interpretation
        if oscillation_phase > 0.7:
            phase_status = 'BUBBLE_PRONE'
            phase_desc = 'In bubble-favorable phase of LPPL oscillation'
        elif oscillation_phase > 0.3:
            phase_status = 'TRANSITION'
            phase_desc = 'Transitioning toward/from bubble phase'
        elif oscillation_phase > -0.3:
            phase_status = 'NEUTRAL'
            phase_desc = 'Neutral phase - growth without bubble dynamics'
        else:
            phase_status = 'CORRECTION_PRONE'
            phase_desc = 'In correction-favorable phase'

        # 2025 specific note from the research
        years_to_2027_bubble = max(0, proximity_to_2027_bubble)

        return {
            'lambda': self.LAMBDA,
            'lambda_harmonic': round(self.LAMBDA_HARMONIC, 3),
            'historical_ratios': [round(r, 2) for r in ratios],
            'next_fundamental_bubble': {
                'predicted_age': round(next_fundamental_from_2017, 2),
                'predicted_date': 'May 2027',
                'years_away': round(years_to_2027_bubble, 2),
                'source': '2017 peak × λ (2.07)'
            },
            'oscillation_phase': round(oscillation_phase, 3),
            'phase_status': phase_status,
            'phase_description': phase_desc,
            'in_bubble_window': in_bubble_window,
            'perrenod_2025_note': 'No bubble predicted for 2025 under LPPL framework',
            'bubble_probability': self._calculate_bubble_probability(
                age_years, oscillation_phase, price, fair_value
            )
        }

    def _calculate_bubble_probability(self, age: float, phase: float,
                                       price: float, fair_value: float) -> Dict:
        """
        Calculate probability of being in a bubble based on multiple factors.
        """
        # Factor 1: Price deviation from fair value
        deviation = (price - fair_value) / fair_value
        if deviation > 1.5:
            price_factor = 90
        elif deviation > 1.0:
            price_factor = 70
        elif deviation > 0.5:
            price_factor = 40
        elif deviation > 0.2:
            price_factor = 20
        else:
            price_factor = 5

        # Factor 2: Oscillation phase
        phase_factor = max(0, phase * 50 + 25)  # 0-75 range

        # Factor 3: Proximity to predicted bubble (2027)
        next_bubble_age = 18.5  # May 2027
        years_to_bubble = abs(age - next_bubble_age)
        if years_to_bubble < 0.5:
            timing_factor = 80
        elif years_to_bubble < 1.0:
            timing_factor = 50
        elif years_to_bubble < 2.0:
            timing_factor = 20
        else:
            timing_factor = 5

        # Weighted probability
        probability = (
            price_factor * 0.50 +
            phase_factor * 0.25 +
            timing_factor * 0.25
        )

        if probability > 70:
            assessment = 'HIGH'
            action = 'Bubble conditions present - distribution recommended'
        elif probability > 40:
            assessment = 'MODERATE'
            action = 'Some bubble characteristics - monitor closely'
        elif probability > 20:
            assessment = 'LOW'
            action = 'Normal market conditions - accumulation favorable'
        else:
            assessment = 'MINIMAL'
            action = 'No bubble indicators - strong accumulation zone'

        return {
            'probability_pct': round(probability, 1),
            'assessment': assessment,
            'action': action,
            'factors': {
                'price_deviation': round(price_factor, 1),
                'lppl_phase': round(phase_factor, 1),
                'timing_proximity': round(timing_factor, 1)
            }
        }

    def _predict_bubbles(self, current_age: float) -> Dict:
        """
        Predict future bubble windows based on LPPL model.
        """
        # Historical bubbles for reference
        history = [
            {'year': 2011, 'age': 2.92, 'type': 'Fundamental', 'peak': '$32'},
            {'year': 2013, 'age': 4.92, 'type': 'Fundamental', 'peak': '$1,150'},
            {'year': 2017, 'age': 8.95, 'type': 'Fundamental', 'peak': '$19,800'},
            {'year': 2021, 'age': 12.89, 'type': 'Harmonic', 'peak': '$69,000'},
        ]

        # Future predictions
        # Next fundamental from 2017: 8.95 × 2.07 = 18.5 years = May 2027
        next_fundamental_age = 8.95 * self.LAMBDA
        next_fundamental_date = self.GENESIS_DATE + timedelta(days=next_fundamental_age * 365.25)

        # Next harmonic from 2021: 12.89 × 1.44 = 18.6 years ≈ May 2027 (converges!)
        next_harmonic_age = 12.89 * self.LAMBDA_HARMONIC

        # Following fundamental: 18.5 × 2.07 ≈ 38.3 years = 2047
        following_fundamental_age = next_fundamental_age * self.LAMBDA

        predictions = [
            {
                'type': 'NEXT_FUNDAMENTAL',
                'predicted_age': round(next_fundamental_age, 2),
                'predicted_date': str(next_fundamental_date),
                'approximate_date': 'May 2027',
                'years_away': round(next_fundamental_age - current_age, 2),
                'confidence': 'HIGH',
                'note': 'Fundamental mode bubble (2017 × λ)'
            },
            {
                'type': 'FOLLOWING_FUNDAMENTAL',
                'predicted_age': round(following_fundamental_age, 1),
                'approximate_date': '~2047',
                'years_away': round(following_fundamental_age - current_age, 1),
                'confidence': 'LOW',
                'note': 'Long-term extrapolation'
            }
        ]

        # No 2025 bubble warning
        no_2025_bubble = {
            'year': 2025,
            'bubble_predicted': False,
            'explanation': 'LPPL model shows no log-periodic alignment for 2025. Current age (~16 years) falls between bubble windows.',
            'implication': 'Potential for strong growth without bubble dynamics - healthier bull market'
        }

        return {
            'historical': history,
            'predictions': predictions,
            'current_age': round(current_age, 2),
            'no_2025_bubble': no_2025_bubble,
            'model_insight': 'Bubbles are not random - they follow discrete scale invariance with λ ≈ 2.07'
        }

    def _assess_current_status(self, price: float, power_law: Dict,
                                lppl: Dict, age_years: float) -> Dict:
        """
        Comprehensive assessment of current market status.
        """
        pl_zone = power_law['zone']
        pl_percentile = power_law['percentile_in_corridor']
        bubble_prob = lppl['bubble_probability']['probability_pct']
        phase_status = lppl['phase_status']

        # Overall assessment
        if pl_zone == 'DEEP_VALUE' and bubble_prob < 20:
            status = 'MAXIMUM_OPPORTUNITY'
            recommendation = 'Aggressive accumulation - at power law support with no bubble risk'
            risk_level = 'LOW'
        elif pl_zone == 'VALUE' and bubble_prob < 30:
            status = 'FAVORABLE_ENTRY'
            recommendation = 'Strong accumulation zone - good risk/reward'
            risk_level = 'LOW-MEDIUM'
        elif pl_zone == 'FAIR' and bubble_prob < 50:
            status = 'NEUTRAL_GROWTH'
            recommendation = 'Hold positions - normal cycle progression'
            risk_level = 'MEDIUM'
        elif pl_zone == 'EXTENDED' or bubble_prob > 50:
            status = 'CAUTION'
            recommendation = 'Begin profit-taking - above fair value'
            risk_level = 'MEDIUM-HIGH'
        elif pl_zone == 'BUBBLE_TERRITORY' or bubble_prob > 70:
            status = 'DISTRIBUTION_ZONE'
            recommendation = 'Active distribution - bubble conditions present'
            risk_level = 'HIGH'
        else:
            status = 'MONITORING'
            recommendation = 'Continue monitoring - mixed signals'
            risk_level = 'MEDIUM'

        # 2025 specific insight
        years_to_next_bubble = max(0, 18.5 - age_years)

        return {
            'status': status,
            'recommendation': recommendation,
            'risk_level': risk_level,
            'power_law_zone': pl_zone,
            'power_law_percentile': pl_percentile,
            'bubble_probability': bubble_prob,
            'lppl_phase': phase_status,
            'years_to_next_bubble': round(years_to_next_bubble, 2),
            'key_insight': self._generate_insight(pl_zone, bubble_prob, years_to_next_bubble)
        }

    def _generate_insight(self, zone: str, bubble_prob: float,
                          years_to_bubble: float) -> str:
        """Generate key insight based on current conditions."""

        if years_to_bubble > 1.0 and bubble_prob < 30:
            return f"LPPL model suggests growth without bubble dynamics until ~May 2027. Current conditions favor accumulation with {years_to_bubble:.1f} years until next predicted bubble window."

        elif years_to_bubble < 1.0:
            return f"Approaching bubble window (May 2027). Monitor for parabolic price action and begin exit planning within {years_to_bubble:.1f} years."

        elif zone in ['DEEP_VALUE', 'VALUE']:
            return f"Price at {zone.replace('_', ' ').lower()} within power law corridor. Historical data shows strong forward returns from this zone."

        elif zone == 'BUBBLE_TERRITORY':
            return "Price above power law corridor - bubble-like conditions. Exercise caution regardless of timing model."

        else:
            return f"Normal cycle progression. Power law zone: {zone}. Bubble probability: {bubble_prob:.0f}%."
