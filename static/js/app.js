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
    updateValuation(data);
    updatePhase(data);
    updateLiquidity(data);
    updateTopDetection(data);
    updateBusinessCycle(data);
    updateTrends(data);
    updateAltRotation(data);
    updateMonteCarlo(data);
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

    document.getElementById('phase-name').textContent = phase.phase || '--';
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

    // Phase
    document.getElementById('alt-phase').textContent =
        (alts.phase || '--').replace('_', ' ');

    // Metrics
    document.getElementById('eth-btc').textContent =
        (ethBtc.value || 0).toFixed(4);
    document.getElementById('btc-dom').textContent =
        (alts.btc_dominance || 0).toFixed(1) + '%';

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
