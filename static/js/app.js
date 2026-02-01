/**
 * Bitcoin Strategic Cycle Model - Dashboard JavaScript
 */

// Global state
let lastAnalysis = null;
let isLoading = false;

// API endpoints
const API = {
    analyze: '/api/analyze',
    analyzeDefault: '/api/analyze/default',
    liveData: '/api/live-data',
    overrides: '/api/overrides',
    thesis: '/api/thesis',
    signal: '/api/signal'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    refreshData();
});

// Refresh data
async function refreshData() {
    if (isLoading) return;

    setLoading(true);

    try {
        const response = await fetch(API.analyze);
        if (!response.ok) throw new Error('Failed to fetch analysis');

        const data = await response.json();
        lastAnalysis = data;
        updateDashboard(data);

    } catch (error) {
        console.error('Error fetching data:', error);
        // Fall back to default data
        try {
            const response = await fetch(API.analyzeDefault);
            const data = await response.json();
            lastAnalysis = data;
            updateDashboard(data);
        } catch (fallbackError) {
            console.error('Fallback also failed:', fallbackError);
            showError('Failed to load data. Please try again.');
        }
    } finally {
        setLoading(false);
    }
}

// Update dashboard with data
function updateDashboard(data) {
    updateHeader(data);
    updateSignalCard(data);
    updateCompositeScore(data);
    updateValuation(data);
    updatePhase(data);
    updateLiquidity(data);
    updateTopDetection(data);
    updateBusinessCycle(data);
    updateTrends(data);
    updateAltRotation(data);
    updateMonteCarlo(data);

    // v7.1 Enhanced Sections
    updateCycleIntelligence(data);
    updateScenarios(data);
    updatePeakTiming(data);
    updateRiskManagement(data);
    updateTradeLevels(data);
    updateWatchlist(data);

    updateThesis(data);
    updateFooter(data);
}

// Header updates
function updateHeader(data) {
    const price = data.meta?.btc_price || 0;
    const priceEl = document.getElementById('btc-price');
    const changeEl = document.getElementById('btc-change');

    priceEl.textContent = formatCurrency(price);

    // Calculate 24h change from trends if available
    const change24h = data.btc_trends?.STF?.changes?.['1d'] || 0;
    changeEl.textContent = formatPercent(change24h);
    changeEl.className = 'change ' + (change24h >= 0 ? 'positive' : 'negative');
}

// Composite Score updates
function updateCompositeScore(data) {
    const composite = data.composite_score || {};
    const components = composite.components || {};

    // Main score and rating
    const score = composite.overall_score || 0;
    document.getElementById('composite-score').textContent = score.toFixed(0);

    const ratingEl = document.getElementById('composite-rating');
    const rating = composite.rating || '--';
    ratingEl.textContent = rating;
    ratingEl.className = 'composite-rating ' + rating.toLowerCase().replace(' ', '-');

    // Gauge fill
    const gaugeFill = document.getElementById('composite-gauge-fill');
    gaugeFill.style.width = score + '%';

    // Color based on score
    if (score >= 65) {
        gaugeFill.style.background = 'linear-gradient(90deg, #10b981, #34d399)';
    } else if (score >= 50) {
        gaugeFill.style.background = 'linear-gradient(90deg, #f59e0b, #fbbf24)';
    } else if (score >= 35) {
        gaugeFill.style.background = 'linear-gradient(90deg, #f97316, #fb923c)';
    } else {
        gaugeFill.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
    }

    // Component bars
    const updateComponent = (id, comp) => {
        const fillEl = document.getElementById('comp-' + id);
        const valEl = document.getElementById('comp-' + id + '-val');
        if (fillEl && comp) {
            fillEl.style.width = comp.score + '%';
            // Color based on score
            if (comp.score >= 65) {
                fillEl.style.backgroundColor = '#10b981';
            } else if (comp.score >= 50) {
                fillEl.style.backgroundColor = '#f59e0b';
            } else if (comp.score >= 35) {
                fillEl.style.backgroundColor = '#f97316';
            } else {
                fillEl.style.backgroundColor = '#ef4444';
            }
        }
        if (valEl && comp) {
            valEl.textContent = comp.score.toFixed(0);
        }
    };

    updateComponent('valuation', components.valuation);
    updateComponent('liquidity', components.liquidity);
    updateComponent('trend', components.trend);
    updateComponent('bizcycle', components.business_cycle);
    updateComponent('phase', components.phase);
    updateComponent('sentiment', components.sentiment);

    // Action text
    document.getElementById('composite-action').textContent =
        composite.action || 'Loading...';
}

// Signal card updates
function updateSignalCard(data) {
    const signal = data.signal || {};
    const signalEl = document.getElementById('signal-value');
    const allocEl = document.getElementById('allocation-value');
    const confEl = document.getElementById('confidence-value');
    const rationaleEl = document.getElementById('signal-rationale');
    const cardEl = document.getElementById('signal-card');

    // Signal value
    const signalText = signal.signal || 'UNKNOWN';
    signalEl.textContent = signalText;

    // Apply signal class
    signalEl.className = 'signal-value';
    if (signalText.includes('ACCUMULATE')) {
        signalEl.classList.add('accumulate');
    } else if (signalText === 'HOLD') {
        signalEl.classList.add('hold');
    } else if (signalText === 'REDUCE') {
        signalEl.classList.add('reduce');
    } else if (signalText === 'DISTRIBUTE') {
        signalEl.classList.add('distribute');
    }

    // Allocation and confidence
    allocEl.textContent = (signal.allocation || 0) + '%';
    confEl.textContent = signal.confidence || '--';

    // Rationale
    const rationale = signal.rationale || [];
    rationaleEl.textContent = Array.isArray(rationale) ? rationale.join(' | ') : rationale;
}

// Valuation updates
function updateValuation(data) {
    const phase = data.phase || {};
    const details = phase.value_details || {};

    // MVRV
    const mvrv = details.mvrv || 0;
    document.getElementById('mvrv-value').textContent = mvrv.toFixed(2);

    // Zone
    const zone = phase.value_zone || 'UNKNOWN';
    const zoneEl = document.getElementById('value-zone');
    zoneEl.textContent = zone.replace('_', ' ');
    zoneEl.className = 'metric-value zone-badge ' + zone.toLowerCase().replace('_', '-');

    // MVRV gauge (scale 0-7 to 0-100%)
    const mvrvPct = Math.min(100, Math.max(0, (mvrv / 7) * 100));
    document.getElementById('mvrv-fill').style.width = mvrvPct + '%';

    // Power Law
    const plFair = details.power_law_fair || 0;
    const plDev = details.power_law_deviation || 0;
    document.getElementById('pl-fair').textContent = formatCurrency(plFair);
    document.getElementById('pl-dev').textContent = formatPercent(plDev);

    // Buy zone indicator
    const buyZoneEl = document.getElementById('buy-zone-indicator');
    const inBuyZone = phase.in_buy_zone;
    buyZoneEl.className = 'buy-zone-indicator' + (inBuyZone ? '' : ' not-buy');
    buyZoneEl.querySelector('.indicator-text').textContent =
        inBuyZone ? 'IN BUY ZONE' : 'NOT in buy zone';
}

// Phase updates
function updatePhase(data) {
    const phase = data.phase || {};
    const forecast = data.forecast?.transition || {};
    const intel = data.cycle_intelligence?.current_phase || {};

    // Use friendly display name if available, fallback to raw phase
    const displayName = intel.display_name || phase.phase || '--';
    const emoji = intel.emoji || '';
    document.getElementById('phase-name').textContent = emoji + ' ' + displayName;
    document.getElementById('phase-confidence').textContent =
        (phase.phase_confidence || 0).toFixed(0) + '% conf';

    // Progress
    const progress = phase.cycle_progress || 0;
    document.getElementById('cycle-progress-fill').style.width = progress + '%';
    document.getElementById('cycle-progress-text').textContent = progress.toFixed(0) + '% complete';

    // Transition
    document.getElementById('next-phase').textContent = forecast.next || '--';
    document.getElementById('transition-prob').textContent =
        (forecast.probability || 0) + '% prob';
    document.getElementById('phase-timeline').textContent =
        'Timeline: ' + (forecast.timeline || '--');
}

// Liquidity updates
function updateLiquidity(data) {
    const liq = data.liquidity || {};

    // Regime badge
    const regimeEl = document.getElementById('liq-regime');
    const regime = liq.regime || 'UNKNOWN';
    regimeEl.textContent = regime;
    regimeEl.className = 'regime-badge ' + regime.toLowerCase();

    // Metrics
    document.getElementById('net-liq').textContent = '$' + (liq.net_liquidity_T || 0).toFixed(2) + 'T';
    document.getElementById('rrp-depleted').textContent = (liq.rrp_depletion_pct || 0).toFixed(0) + '%';
    document.getElementById('fed-90d').textContent = formatPercent(liq.fed_mom_90d || 0);
    document.getElementById('m2-yoy').textContent = formatPercent(liq.m2_yoy || 0);

    // Score
    const score = liq.score || 0;
    document.getElementById('liq-score-fill').style.width = score + '%';
    document.getElementById('liq-score').textContent = score.toFixed(0) + '/100';
}

// Top Detection updates
function updateTopDetection(data) {
    const phase = data.phase || {};
    const warning = phase.top_warning || 'NONE';
    const score = phase.top_score || 0;
    const indicators = phase.top_indicators || [];

    // Warning badge
    const warningEl = document.querySelector('.warning-badge');
    warningEl.textContent = warning;
    warningEl.className = 'warning-badge ' + warning.toLowerCase();

    // Score
    document.getElementById('top-score').textContent = score + '/100';

    // Indicators
    const indicatorsEl = document.getElementById('top-indicators');
    indicatorsEl.innerHTML = indicators.length > 0
        ? indicators.slice(0, 5).map(i => `<div class="top-indicator">${i}</div>`).join('')
        : '<div class="top-indicator">No signals triggered</div>';
}

// Business Cycle updates
function updateBusinessCycle(data) {
    const biz = data.business_cycle || {};
    const regional = biz.regional_fed || {};

    // Stage
    const stageEl = document.getElementById('biz-stage');
    stageEl.textContent = biz.stage || '--';

    // Metrics
    document.getElementById('ism-mfg').textContent = (biz.ism_mfg || 0).toFixed(1);
    document.getElementById('ism-svc').textContent = (biz.ism_svc || 0).toFixed(1);
    document.getElementById('ism-preview').textContent = (biz.ism_preview || 0).toFixed(1);
    document.getElementById('regional-signal').textContent = regional.signal || '--';

    // Early warning
    const earlyEl = document.getElementById('early-warning');
    if (biz.early_warning) {
        const divergence = biz.regional_vs_ism_divergence || 0;
        earlyEl.className = 'early-warning active';
        earlyEl.textContent = `Divergence: ${divergence > 0 ? '+' : ''}${divergence.toFixed(1)} pts`;
    } else {
        earlyEl.className = 'early-warning inactive';
        earlyEl.textContent = 'No divergence warning';
    }
}

// Trends updates
function updateTrends(data) {
    const trends = data.btc_trends || {};

    // Alignment
    const alignmentEl = document.getElementById('trend-alignment');
    const alignment = trends.alignment || 'UNKNOWN';
    alignmentEl.textContent = alignment.replace('_', ' ');
    alignmentEl.className = 'alignment-badge';
    if (alignment.includes('BULLISH')) {
        alignmentEl.classList.add('bullish');
    } else if (alignment.includes('BEARISH')) {
        alignmentEl.classList.add('bearish');
    } else {
        alignmentEl.classList.add('mixed');
    }

    // Timeframes
    updateTimeframe('tf-stf', trends.STF);
    updateTimeframe('tf-mtf', trends.MTF);
    updateTimeframe('tf-ltf', trends.LTF);
}

function updateTimeframe(id, tf) {
    if (!tf) return;

    const el = document.getElementById(id);
    const trendEl = el.querySelector('.tf-trend');
    const momEl = el.querySelector('.tf-momentum');

    trendEl.textContent = tf.trend || '--';
    trendEl.className = 'tf-trend';
    if (tf.trend?.includes('UP')) {
        trendEl.classList.add('up');
    } else if (tf.trend?.includes('DOWN')) {
        trendEl.classList.add('down');
    } else {
        trendEl.classList.add('neutral');
    }

    momEl.textContent = formatPercent(tf.momentum || 0);
}

// Alt Rotation updates
function updateAltRotation(data) {
    const alts = data.altcoins || {};
    const ethBtc = alts.eth_btc || {};
    const allocation = alts.allocation_suggestion || {};
    const meta = data.meta || {};

    // Phase
    document.getElementById('alt-phase').textContent =
        (alts.phase || '--').replace('_', ' ');

    // ETH Price
    const ethPriceEl = document.getElementById('eth-price');
    if (ethPriceEl) {
        const ethPrice = meta.eth_price || 0;
        ethPriceEl.textContent = formatCurrency(ethPrice);
    }

    // Metrics
    document.getElementById('eth-btc').textContent =
        (ethBtc.value || 0).toFixed(4);
    document.getElementById('btc-dom').textContent =
        (alts.btc_dominance || 0).toFixed(1) + '%';

    // OTHERS vs BTC performance
    const othersBtcEl = document.getElementById('others-btc');
    if (othersBtcEl) {
        const othersPerf = alts.others_vs_btc || 0;
        othersBtcEl.textContent = formatPercent(othersPerf);
        othersBtcEl.className = 'metric-value ' + (othersPerf >= 0 ? 'positive' : 'negative');
    }

    // Allocation bars
    const btcAlloc = allocation.BTC || 50;
    const ethAlloc = allocation.ETH || 30;
    const altsAlloc = allocation.ALTS || 20;

    document.getElementById('alloc-btc').style.width = btcAlloc + '%';
    document.getElementById('alloc-eth').style.width = ethAlloc + '%';
    document.getElementById('alloc-alts').style.width = altsAlloc + '%';

    document.getElementById('alloc-btc-pct').textContent = btcAlloc + '%';
    document.getElementById('alloc-eth-pct').textContent = ethAlloc + '%';
    document.getElementById('alloc-alts-pct').textContent = altsAlloc + '%';
}

// Monte Carlo updates
function updateMonteCarlo(data) {
    const mc = data.forecast?.monte_carlo || {};

    updateMCHorizon('mc-30d', mc['30d']);
    updateMCHorizon('mc-90d', mc['90d']);
    updateMCHorizon('mc-365d', mc['365d']);

    // Probabilities (from 12M forecast)
    const mc12m = mc['365d'] || {};
    document.getElementById('prob-100k').textContent =
        (mc12m.prob_above_100k || 0).toFixed(0) + '%';
    document.getElementById('prob-150k').textContent =
        (mc12m.prob_above_150k || 0).toFixed(0) + '%';
    document.getElementById('prob-75k').textContent =
        (mc12m.prob_below_75k || 0).toFixed(0) + '%';
}

function updateMCHorizon(id, data) {
    if (!data) return;

    const el = document.getElementById(id);
    el.querySelector('.horizon-median').textContent = formatCurrency(data.median || 0);
    el.querySelector('.horizon-range').textContent =
        formatCompact(data.p10 || 0) + ' to ' + formatCompact(data.p90 || 0);

    const returnEl = el.querySelector('.horizon-return');
    const ret = data.expected_return || 0;
    returnEl.textContent = formatPercent(ret);
    returnEl.className = 'horizon-return ' + (ret >= 0 ? 'positive' : 'negative');
}

// ═══════════════════════════════════════════════════════════════════════════
// v7.1 ENHANCED INSIGHTS
// ═══════════════════════════════════════════════════════════════════════════

// Cycle Intelligence updates
function updateCycleIntelligence(data) {
    const intel = data.cycle_intelligence || {};
    const current = intel.current_phase || {};
    const metrics = intel.cycle_metrics || {};
    const behavior = intel.behavior_guide || {};
    const timing = intel.timing_estimates || {};

    // Display name and simple explanation (new in v7.1)
    const displayNameEl = document.getElementById('phase-display-name');
    if (displayNameEl) {
        const emoji = current.emoji || '';
        displayNameEl.textContent = emoji + ' ' + (current.display_name || current.name || '--');
    }

    const simpleExplanationEl = document.getElementById('simple-explanation');
    if (simpleExplanationEl) {
        simpleExplanationEl.textContent = current.simple_explanation || '';
    }

    // Position badge
    document.getElementById('cycle-position').textContent =
        metrics.estimated_position || 'UNKNOWN';

    // Where we are explanation
    document.getElementById('position-explanation').textContent =
        current.where_we_are || 'Loading...';

    // Psychology
    document.getElementById('phase-psychology').textContent =
        current.psychology || '--';

    // Behaviors
    document.getElementById('smart-money-behavior').textContent =
        behavior.smart_money || '--';
    document.getElementById('retail-behavior').textContent =
        behavior.retail || '--';
    document.getElementById('what-to-do').textContent =
        behavior.what_you_should_do || '--';

    // Metrics
    document.getElementById('rally-from-low').textContent =
        (metrics.rally_from_cycle_low_pct || 0).toFixed(0) + '%';
    document.getElementById('dd-from-ath').textContent =
        (metrics.drawdown_from_ath_pct || 0).toFixed(0) + '%';
    document.getElementById('phase-duration').textContent =
        current.typical_duration || '--';
}

// Scenario updates
function updateScenarios(data) {
    const scenarios = data.scenarios?.scenarios || {};
    const expected = data.scenarios?.expected_value || {};

    // Bull scenario
    const bull = scenarios.bull || {};
    const bullCard = document.getElementById('scenario-bull');
    if (bullCard) {
        bullCard.querySelector('.scenario-prob').textContent =
            (bull.probability || 0) + '%';
        bullCard.querySelector('.scenario-target').textContent =
            formatCurrency(bull.target_12m || 0);

        const bullCatalysts = document.getElementById('bull-catalysts');
        if (bullCatalysts && bull.catalysts) {
            bullCatalysts.innerHTML = '<ul>' +
                bull.catalysts.slice(0, 3).map(c => `<li>${c}</li>`).join('') +
                '</ul>';
        }
    }

    // Base scenario
    const base = scenarios.base || {};
    const baseCard = document.getElementById('scenario-base');
    if (baseCard) {
        baseCard.querySelector('.scenario-prob').textContent =
            (base.probability || 0) + '%';
        baseCard.querySelector('.scenario-target').textContent =
            formatCurrency(base.target_12m || 0);

        const baseCatalysts = document.getElementById('base-catalysts');
        if (baseCatalysts && base.catalysts) {
            baseCatalysts.innerHTML = '<ul>' +
                base.catalysts.slice(0, 3).map(c => `<li>${c}</li>`).join('') +
                '</ul>';
        }
    }

    // Bear scenario
    const bear = scenarios.bear || {};
    const bearCard = document.getElementById('scenario-bear');
    if (bearCard) {
        bearCard.querySelector('.scenario-prob').textContent =
            (bear.probability || 0) + '%';
        bearCard.querySelector('.scenario-target').textContent =
            formatCurrency(bear.target_12m || 0);

        const bearCatalysts = document.getElementById('bear-catalysts');
        if (bearCatalysts && bear.catalysts) {
            bearCatalysts.innerHTML = '<ul>' +
                bear.catalysts.slice(0, 3).map(c => `<li>${c}</li>`).join('') +
                '</ul>';
        }
    }

    // Expected value
    document.getElementById('expected-value').textContent =
        formatCurrency(expected.expected_price_12m || 0);
    document.getElementById('expected-return').textContent =
        '(' + formatPercent(expected.expected_return_pct || 0) + ')';
}

// Peak Timing Forecast updates
function updatePeakTiming(data) {
    const peak = data.peak_timing || {};
    const composite = peak.composite_forecast || {};
    const mc = peak.monte_carlo_timing || {};
    const probs = mc.probabilities || {};
    const prices = peak.peak_price_estimates || {};
    const priceScenarios = prices.peak_scenarios || {};
    const historical = peak.historical_patterns || {};
    const current = peak.current_cycle || {};

    // Main forecast
    const peakDateEl = document.getElementById('peak-date');
    if (peakDateEl) {
        peakDateEl.textContent = composite.peak_date_est || '--';
    }

    const peakQuarterEl = document.getElementById('peak-quarter');
    if (peakQuarterEl) {
        peakQuarterEl.textContent = composite.peak_quarter || '--';
    }

    const peakConfEl = document.getElementById('peak-confidence');
    if (peakConfEl) {
        const confidence = composite.confidence || '--';
        peakConfEl.textContent = confidence;
        peakConfEl.className = 'conf-value ' + confidence.toLowerCase().replace(' ', '-');
    }

    const daysEl = document.getElementById('days-to-peak');
    if (daysEl) {
        daysEl.textContent = composite.days_to_peak_est || '--';
    }

    // Probabilities
    document.getElementById('prob-peak-3m').textContent =
        (probs.peak_within_3_months || 0).toFixed(0) + '%';
    document.getElementById('prob-peak-6m').textContent =
        (probs.peak_within_6_months || 0).toFixed(0) + '%';
    document.getElementById('prob-peak-12m').textContent =
        (probs.peak_within_12_months || 0).toFixed(0) + '%';
    document.getElementById('prob-peak-passed').textContent =
        (probs.peak_already_passed || 0).toFixed(0) + '%';

    // Price targets
    const conservative = priceScenarios.conservative || {};
    const base = priceScenarios.base_case || {};
    const optimistic = priceScenarios.optimistic || {};

    document.getElementById('peak-price-conservative').textContent =
        formatCurrency(conservative.price_target || 0);
    document.getElementById('peak-mvrv-conservative').textContent =
        'MVRV ' + (conservative.mvrv_target || 0);

    document.getElementById('peak-price-base').textContent =
        formatCurrency(base.price_target || 0);
    document.getElementById('peak-mvrv-base').textContent =
        'MVRV ' + (base.mvrv_target || 0);

    document.getElementById('peak-price-optimistic').textContent =
        formatCurrency(optimistic.price_target || 0);
    document.getElementById('peak-mvrv-optimistic').textContent =
        'MVRV ' + (optimistic.mvrv_target || 0);

    // Recommendation
    document.getElementById('peak-recommendation').textContent =
        composite.recommendation || 'Loading...';

    // Progress bars
    const halvingProgress = historical.from_halving?.progress_pct || 0;
    const bottomProgress = historical.from_bottom?.progress_pct || 0;

    const halvingFill = document.getElementById('halving-progress-fill');
    if (halvingFill) {
        halvingFill.style.width = Math.min(100, halvingProgress) + '%';
    }
    document.getElementById('halving-progress').textContent =
        halvingProgress.toFixed(0) + '%';

    const bottomFill = document.getElementById('bottom-progress-fill');
    if (bottomFill) {
        bottomFill.style.width = Math.min(100, bottomProgress) + '%';
    }
    document.getElementById('bottom-progress').textContent =
        bottomProgress.toFixed(0) + '%';

    // Cycle stats
    document.getElementById('days-since-halving').textContent =
        (current.days_since_halving || 0) + ' days since halving';
    document.getElementById('days-since-bottom').textContent =
        (current.days_since_bottom || 0) + ' days since bottom';
}

// Risk Management updates
function updateRiskManagement(data) {
    const risk = data.risk_management || {};
    const sizing = risk.position_sizing || {};
    const drawdown = risk.drawdown_analysis || {};
    const riskRward = risk.drawdown_analysis || {};

    // Position sizing
    document.getElementById('recommended-allocation').textContent =
        (sizing.recommended_allocation_pct || 0) + '%';
    document.getElementById('conviction-level').textContent =
        sizing.conviction_level || '--';
    document.getElementById('position-rationale').textContent =
        sizing.mvrv_justification || '--';

    // Drawdown
    document.getElementById('typical-dd').textContent =
        (drawdown.typical_drawdown_pct || 0) + '%';
    document.getElementById('max-dd').textContent =
        (drawdown.max_historical_drawdown_pct || 0) + '%';
    document.getElementById('mental-prep').textContent =
        drawdown.mental_preparation || '--';

    // Risk/Reward
    const rrRating = document.getElementById('rr-rating');
    if (rrRating) {
        const rr = risk.drawdown_analysis || {};
        rrRating.textContent = rr.risk_reward_rating || '--';
    }
    document.getElementById('downside-risk').textContent =
        drawdown.downside_risk || '--';
    document.getElementById('upside-potential').textContent =
        drawdown.upside_potential || '--';
}

// Trade Levels updates
function updateTradeLevels(data) {
    const levels = data.trade_levels || {};
    const entries = levels.entry_zones || [];
    const exits = levels.exit_targets || [];
    const stops = levels.stop_loss_levels || {};

    // Entry levels
    const entryList = document.getElementById('entry-levels');
    if (entryList) {
        entryList.innerHTML = entries.map(e => `
            <div class="level-item">
                <span class="level-price">${e.price_range || '--'}</span>
                <span class="level-action">${e.size || ''}</span>
            </div>
        `).join('') || '<div class="level-item">No entries at current levels</div>';
    }

    // Exit levels
    const exitList = document.getElementById('exit-levels');
    if (exitList) {
        exitList.innerHTML = exits.map(e => `
            <div class="level-item">
                <span class="level-price">${formatCurrency(e.price || 0)}</span>
                <span class="level-action">Sell ${e.sell_pct || 0}%</span>
            </div>
        `).join('') || '<div class="level-item">See trade plan</div>';
    }

    // Stop levels
    const stopList = document.getElementById('stop-levels');
    if (stopList && stops.soft_stop) {
        stopList.innerHTML = `
            <div class="level-item">
                <span class="level-price">${formatCurrency(stops.soft_stop?.price || 0)}</span>
                <span class="level-action">Soft Stop</span>
            </div>
            <div class="level-item">
                <span class="level-price">${formatCurrency(stops.hard_stop?.price || 0)}</span>
                <span class="level-action">Hard Stop</span>
            </div>
        `;
    }

    // Trade plan
    const tradePlan = document.getElementById('trade-plan');
    if (tradePlan) {
        tradePlan.textContent = levels.trade_plan || 'Loading trade plan...';
    }
}

// Watchlist updates
function updateWatchlist(data) {
    const watchlist = data.watchlist || {};
    const daily = watchlist.daily_watchlist || [];
    const levels = watchlist.key_levels_to_watch || {};
    const redFlags = watchlist.red_flags || [];
    const greenFlags = watchlist.green_flags || [];

    // Daily watchlist
    const dailyList = document.getElementById('daily-watchlist');
    if (dailyList) {
        dailyList.innerHTML = daily.map(item => `
            <li><strong>${item.metric}:</strong> ${item.watch_for || item.current || ''}</li>
        `).join('');
    }

    // Key price levels
    const priceList = document.getElementById('key-price-levels');
    if (priceList) {
        priceList.innerHTML = `
            <div class="price-level">
                <span class="price-level-label">Support 1</span>
                <span class="price-level-value support">${formatCurrency(levels.immediate_support || 0)}</span>
            </div>
            <div class="price-level">
                <span class="price-level-label">Support 2</span>
                <span class="price-level-value support">${formatCurrency(levels.strong_support || 0)}</span>
            </div>
            <div class="price-level">
                <span class="price-level-label">Resistance 1</span>
                <span class="price-level-value resistance">${formatCurrency(levels.immediate_resistance || 0)}</span>
            </div>
            <div class="price-level">
                <span class="price-level-label">Resistance 2</span>
                <span class="price-level-value resistance">${formatCurrency(levels.major_resistance || 0)}</span>
            </div>
        `;
    }

    // Red flags
    const redList = document.getElementById('red-flags');
    if (redList) {
        redList.innerHTML = redFlags.slice(0, 5).map(f => `<li>${f}</li>`).join('');
    }

    // Green flags
    const greenList = document.getElementById('green-flags');
    if (greenList) {
        greenList.innerHTML = greenFlags.slice(0, 5).map(f => `<li>${f}</li>`).join('');
    }
}

// ═══════════════════════════════════════════════════════════════════════════

// Thesis updates
function updateThesis(data) {
    document.getElementById('thesis-content').textContent =
        data.thesis || 'No thesis available';
}

// Footer updates
function updateFooter(data) {
    const source = data.data_source || {};
    const timestamp = source.timestamp ? new Date(source.timestamp) : new Date();

    document.getElementById('last-updated').textContent =
        'Last updated: ' + timestamp.toLocaleString();

    let dataSourceText = 'Live Data';
    if (source.live_data_status === 'demo') {
        dataSourceText = 'Demo Data';
    } else if (source.has_manual_overrides) {
        dataSourceText = 'Live + Overrides';
    }
    document.getElementById('data-source').textContent = 'Data: ' + dataSourceText;
}

// Copy thesis to clipboard
function copyThesis() {
    const thesis = document.getElementById('thesis-content').textContent;
    navigator.clipboard.writeText(thesis).then(() => {
        const btn = document.querySelector('.btn-copy');
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = originalText, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Toggle overrides section
function toggleOverrides() {
    const section = document.getElementById('overrides-section');
    section.classList.toggle('collapsed');
}

// Apply manual overrides
async function applyOverrides() {
    const overrides = {};

    const fields = [
        { id: 'override-mvrv', key: 'mvrv', type: 'float' },
        { id: 'override-nupl', key: 'nupl', type: 'float' },
        { id: 'override-fed-bs', key: 'fed_bs', type: 'float' },
        { id: 'override-rrp', key: 'rrp', type: 'float' },
        { id: 'override-ism-mfg', key: 'ism_mfg', type: 'float' },
        { id: 'override-fg', key: 'fear_greed', type: 'int' }
    ];

    fields.forEach(field => {
        const el = document.getElementById(field.id);
        if (el && el.value) {
            overrides[field.key] = field.type === 'int'
                ? parseInt(el.value)
                : parseFloat(el.value);
        }
    });

    if (Object.keys(overrides).length === 0) {
        alert('Please enter at least one override value');
        return;
    }

    try {
        const response = await fetch(API.overrides, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(overrides)
        });

        if (!response.ok) throw new Error('Failed to set overrides');

        // Refresh data with new overrides
        await refreshData();

    } catch (error) {
        console.error('Error applying overrides:', error);
        alert('Failed to apply overrides');
    }
}

// Clear all overrides
async function clearOverrides() {
    try {
        await fetch(API.overrides, { method: 'DELETE' });

        // Clear input fields
        document.querySelectorAll('.override-item input').forEach(input => {
            input.value = '';
        });

        // Refresh data
        await refreshData();

    } catch (error) {
        console.error('Error clearing overrides:', error);
    }
}

// Loading state
function setLoading(loading) {
    isLoading = loading;
    const btn = document.querySelector('.btn-refresh');
    const container = document.querySelector('.container');

    if (loading) {
        btn.classList.add('loading');
        container.classList.add('loading');
    } else {
        btn.classList.remove('loading');
        container.classList.remove('loading');
    }
}

// Show error message
function showError(message) {
    alert(message); // Simple for now, could be improved with toast notifications
}

// Formatting utilities
function formatCurrency(value) {
    if (typeof value !== 'number') return '$--';
    return '$' + value.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

function formatCompact(value) {
    if (typeof value !== 'number') return '--';
    if (value >= 1000000) {
        return '$' + (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return '$' + (value / 1000).toFixed(0) + 'K';
    }
    return '$' + value.toFixed(0);
}

function formatPercent(value) {
    if (typeof value !== 'number') return '--%';
    const sign = value >= 0 ? '+' : '';
    return sign + value.toFixed(1) + '%';
}

// Auto-refresh every 5 minutes
setInterval(refreshData, 5 * 60 * 1000);
