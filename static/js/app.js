/**
 * BTC Econometric Model v7.6 — Dashboard JavaScript
 */

let lastAnalysis = null;
let isLoading = false;

const API = {
    analyze: '/api/analyze',
    analyzeDefault: '/api/analyze/default',
    liveData: '/api/live-data',
    overrides: '/api/overrides',
    signal: '/api/signal'
};

document.addEventListener('DOMContentLoaded', () => {
    refreshData();
});

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

function updateDashboard(data) {
    updateHeader(data);
    updateSignal(data);
    updateCompositeScore(data);
    updateLayers(data);
    updateMarketData(data);
    updateAudit(data);
    updateFooter(data);
}

// ═══════════════════════════════════════════════════════════════════
// HEADER
// ═══════════════════════════════════════════════════════════════════

function updateHeader(data) {
    const md = data.market_data || {};
    const price = md.btc_price || 0;
    document.getElementById('btc-price').textContent = formatCurrency(price);

    const dd = md.drawdown_pct || 0;
    const ddEl = document.getElementById('btc-drawdown');
    ddEl.textContent = dd.toFixed(1) + '% from ATH';
    ddEl.className = 'change ' + (dd >= 0 ? 'positive' : 'negative');
}

// ═══════════════════════════════════════════════════════════════════
// SIGNAL CARD
// ═══════════════════════════════════════════════════════════════════

function updateSignal(data) {
    const sig = data.signal || {};
    const signalEl = document.getElementById('signal-value');
    const signalText = sig.signal || 'UNKNOWN';
    signalEl.textContent = signalText;

    // Signal coloring
    signalEl.className = 'signal-value';
    if (signalText.includes('BUY') || signalText === 'ACCUMULATE') {
        signalEl.classList.add('bullish');
    } else if (signalText === 'HOLD') {
        signalEl.classList.add('neutral');
    } else {
        signalEl.classList.add('bearish');
    }

    document.getElementById('signal-score').textContent = sig.final_score || '--';
    document.getElementById('allocation-value').textContent = (sig.allocation || 0) + '%';
    document.getElementById('confidence-value').textContent = sig.confidence || '--';
    document.getElementById('macro-phase').textContent = (sig.macro_phase || '--').replace('_', ' ');
    document.getElementById('btc-cycle').textContent = (sig.btc_cycle || '--').replace('_', ' ');

    const rationale = sig.rationale || [];
    document.getElementById('signal-rationale').textContent =
        Array.isArray(rationale) ? rationale.join(' | ') : rationale;
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSITE SCORE
// ═══════════════════════════════════════════════════════════════════

function updateCompositeScore(data) {
    const sig = data.signal || {};
    const score = sig.final_score || 0;

    document.getElementById('composite-score').textContent = score.toFixed(1);

    const gaugeFill = document.getElementById('composite-gauge-fill');
    gaugeFill.style.width = Math.min(100, score) + '%';

    if (score >= 65) {
        gaugeFill.style.background = 'linear-gradient(90deg, #10b981, #34d399)';
    } else if (score >= 45) {
        gaugeFill.style.background = 'linear-gradient(90deg, #f59e0b, #fbbf24)';
    } else if (score >= 35) {
        gaugeFill.style.background = 'linear-gradient(90deg, #f97316, #fb923c)';
    } else {
        gaugeFill.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
    }

    // Adjustments
    const adjEl = document.getElementById('score-adjustments');
    let adjHTML = `<div class="adj-item"><span>Base Score:</span> <span>${sig.base_score || '--'}</span></div>`;
    if (sig.phase_adjustment) {
        adjHTML += `<div class="adj-item adj-bonus"><span>+ Phase (${(sig.macro_phase || '').replace('_', ' ')}):</span> <span>+${sig.phase_adjustment}</span></div>`;
    }
    if (sig.mvrv_adjustment) {
        adjHTML += `<div class="adj-item adj-bonus"><span>+ MVRV Value Zone:</span> <span>+${sig.mvrv_adjustment}</span></div>`;
    }
    if (sig.fear_adjustment) {
        adjHTML += `<div class="adj-item adj-bonus"><span>+ Extreme Fear:</span> <span>+${sig.fear_adjustment}</span></div>`;
    }
    adjHTML += `<div class="adj-item adj-total"><span>Final Score:</span> <span>${sig.final_score || '--'}</span></div>`;
    adjEl.innerHTML = adjHTML;
}

// ═══════════════════════════════════════════════════════════════════
// 12-LAYER SCORING
// ═══════════════════════════════════════════════════════════════════

const LAYER_LABELS = {
    institutional: 'Institutional',
    leverage_fragility: 'Leverage Fragility',
    derivatives: 'Derivatives',
    mvrv: 'MVRV',
    cycle_phase: 'Cycle Phase',
    global_liquidity: 'Global Liquidity',
    options_sentiment: 'Options Sentiment',
    credit: 'Credit',
    macro_liquidity: 'Macro-Liquidity',
    support: 'Support',
    momentum: 'Momentum',
    sentiment: 'Sentiment'
};

const LAYER_ORDER = [
    'institutional', 'leverage_fragility', 'derivatives', 'mvrv',
    'cycle_phase', 'global_liquidity', 'options_sentiment', 'credit',
    'macro_liquidity', 'support', 'momentum', 'sentiment'
];

function updateLayers(data) {
    const layers = data.layers || {};
    const grid = document.getElementById('layers-grid');

    let html = '';
    for (const name of LAYER_ORDER) {
        const layer = layers[name];
        if (!layer) continue;

        const score = layer.score || 0;
        const weight = ((layer.weight || 0) * 100).toFixed(0);
        const contribution = (layer.contribution || 0).toFixed(2);
        const barWidth = score;
        const barColor = getScoreColor(score);
        const label = LAYER_LABELS[name] || name;

        html += `
            <div class="layer-card">
                <div class="layer-header">
                    <span class="layer-name">${label}</span>
                    <span class="layer-weight">${weight}%</span>
                </div>
                <div class="layer-bar-row">
                    <div class="layer-bar">
                        <div class="layer-bar-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
                    </div>
                    <span class="layer-score">${score}</span>
                </div>
                <div class="layer-contribution">Contribution: ${contribution}</div>
                <div class="layer-reasoning">${layer.reasoning || ''}</div>
            </div>
        `;
    }
    grid.innerHTML = html;
}

function getScoreColor(score) {
    if (score >= 70) return '#10b981';
    if (score >= 55) return '#34d399';
    if (score >= 45) return '#f59e0b';
    if (score >= 35) return '#f97316';
    return '#ef4444';
}

// ═══════════════════════════════════════════════════════════════════
// MARKET DATA
// ═══════════════════════════════════════════════════════════════════

function updateMarketData(data) {
    const md = data.market_data || {};

    // Valuation
    setText('mvrv-value', (md.mvrv || 0).toFixed(3));
    setText('realized-price', formatCurrency(md.realized_price || 0));
    setText('sth-realized', formatCurrency(md.sth_realized_price || 0));
    setText('lth-realized', formatCurrency(md.lth_realized_price || 0));
    setText('nupl-value', (md.nupl || 0).toFixed(3));

    // Sentiment
    const fg = md.fear_greed || 0;
    const fgEl = document.getElementById('fear-greed');
    if (fgEl) {
        let fgLabel = fg;
        let fgClass = 'neutral';
        if (fg <= 20) { fgClass = 'extreme-fear'; fgLabel = fg + ' Extreme Fear'; }
        else if (fg <= 40) { fgClass = 'fear'; fgLabel = fg + ' Fear'; }
        else if (fg <= 60) { fgClass = 'neutral'; fgLabel = fg + ' Neutral'; }
        else if (fg <= 80) { fgClass = 'greed'; fgLabel = fg + ' Greed'; }
        else { fgClass = 'extreme-greed'; fgLabel = fg + ' Extreme Greed'; }
        fgEl.textContent = fgLabel;
        fgEl.className = 'data-value fear-greed-badge ' + fgClass;
    }

    setText('cb-premium', (md.coinbase_premium || 0).toFixed(2) + '%');
    setText('btc-dom', (md.btc_dominance || 0).toFixed(1) + '%');
    setText('eth-btc', (md.eth_btc || 0).toFixed(5));
    setText('eth-price', formatCurrency(md.eth_price || 0));

    // Derivatives
    setText('funding-rate', ((md.funding_rate || 0) * 100).toFixed(4) + '%');
    setText('futures-basis', (md.futures_basis || 0).toFixed(1) + '%');
    setText('ls-ratio', (md.long_short_ratio || 0).toFixed(2));
    setText('liq-24h', formatCompact(md.liquidation_24h || 0));
    setText('oi-change', (md.oi_change_24h_pct || 0).toFixed(1) + '%');

    // Options
    setText('put-call', (md.put_call_ratio || 0).toFixed(2));
    setText('max-pain', formatCurrency(md.max_pain || 0));
    setText('options-oi', formatCompact(md.options_oi || 0));

    // ETF
    setText('etf-daily', formatFlowM(md.etf_flow_daily || 0));
    setText('etf-weekly', formatFlowM(md.etf_flow_weekly || 0));
    setText('etf-cumulative', formatCompact(md.etf_cumulative || 0));

    // Macro
    setText('hy-oas', (md.hy_oas || 0).toFixed(2) + '%');
    setText('yield-curve', (md.yield_curve_2s10s || 0).toFixed(2) + '%');
    setText('init-claims', ((md.initial_claims || 0) / 1000).toFixed(0) + 'K');
    setText('anfci-value', (md.anfci || 0).toFixed(3));
    setText('net-liq', '$' + (md.net_liquidity_b || 0).toFixed(0) + 'B');
    setText('m2-growth', (md.global_m2_growth || 0).toFixed(1) + '%');
}

// ═══════════════════════════════════════════════════════════════════
// DATA SOURCE AUDIT
// ═══════════════════════════════════════════════════════════════════

function updateAudit(data) {
    const sources = data.sources || {};
    const warnings = data.warnings || [];

    const sourcesList = document.getElementById('sources-list');
    let html = `<h3>${Object.keys(sources).length} Verified Sources</h3>`;
    for (const [key, src] of Object.entries(sources).sort()) {
        html += `<div class="source-item"><span class="source-check">&#10003;</span> <span class="source-key">${key}</span> <span class="source-val">${src}</span></div>`;
    }
    sourcesList.innerHTML = html;

    const warningsList = document.getElementById('warnings-list');
    if (warnings.length > 0) {
        warningsList.innerHTML = '<h3>Warnings</h3>' +
            warnings.map(w => `<div class="warning-item">${w}</div>`).join('');
    } else {
        warningsList.innerHTML = '';
    }
}

// ═══════════════════════════════════════════════════════════════════
// FOOTER
// ═══════════════════════════════════════════════════════════════════

function updateFooter(data) {
    const ds = data.data_source || {};
    const timestamp = ds.timestamp ? new Date(ds.timestamp) : new Date();
    document.getElementById('last-updated').textContent = 'Last updated: ' + timestamp.toLocaleString();

    let statusText = 'Live Data';
    if (ds.live_data_status === 'demo') statusText = 'Demo Data';
    else if (ds.has_manual_overrides) statusText = 'Live + Overrides';
    document.getElementById('data-source').textContent = 'Data: ' + statusText;
    document.getElementById('sources-count').textContent = (ds.sources_count || 0) + ' sources verified';
}

// ═══════════════════════════════════════════════════════════════════
// OVERRIDES
// ═══════════════════════════════════════════════════════════════════

async function applyOverrides() {
    const overrides = {};
    const fields = [
        { id: 'override-mvrv', key: 'mvrv', type: 'float' },
        { id: 'override-nupl', key: 'nupl', type: 'float' },
        { id: 'override-fear_greed', key: 'fear_greed', type: 'int' },
        { id: 'override-funding_rate', key: 'funding_rate', type: 'float' },
        { id: 'override-put_call_ratio', key: 'put_call_ratio', type: 'float' },
        { id: 'override-hy_oas', key: 'hy_oas', type: 'float' },
    ];

    fields.forEach(f => {
        const el = document.getElementById(f.id);
        if (el && el.value) {
            overrides[f.key] = f.type === 'int' ? parseInt(el.value) : parseFloat(el.value);
        }
    });

    if (Object.keys(overrides).length === 0) {
        alert('Please enter at least one override value');
        return;
    }

    try {
        const resp = await fetch(API.overrides, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(overrides)
        });
        if (!resp.ok) throw new Error('Failed to set overrides');
        await refreshData();
    } catch (error) {
        console.error('Error applying overrides:', error);
        alert('Failed to apply overrides');
    }
}

async function clearOverrides() {
    try {
        await fetch(API.overrides, { method: 'DELETE' });
        document.querySelectorAll('.override-item input').forEach(el => el.value = '');
        await refreshData();
    } catch (error) {
        console.error('Error clearing overrides:', error);
    }
}

// ═══════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════

function toggleSection(id) {
    const el = document.getElementById(id);
    el.classList.toggle('collapsed');
}

function setLoading(loading) {
    isLoading = loading;
    const btn = document.querySelector('.btn-refresh');
    if (loading) btn.classList.add('loading');
    else btn.classList.remove('loading');
}

function showError(message) {
    alert(message);
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function formatCurrency(value) {
    if (typeof value !== 'number') return '$--';
    return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatCompact(value) {
    if (typeof value !== 'number') return '--';
    if (Math.abs(value) >= 1e9) return '$' + (value / 1e9).toFixed(1) + 'B';
    if (Math.abs(value) >= 1e6) return '$' + (value / 1e6).toFixed(1) + 'M';
    if (Math.abs(value) >= 1e3) return '$' + (value / 1e3).toFixed(0) + 'K';
    return '$' + value.toFixed(0);
}

function formatFlowM(value) {
    if (typeof value !== 'number') return '$--';
    const v = Math.abs(value) > 1e5 ? value / 1e6 : value;
    const sign = v >= 0 ? '+' : '';
    return sign + '$' + Math.abs(v).toFixed(0) + 'M';
}

// Auto-refresh every 5 minutes
setInterval(refreshData, 5 * 60 * 1000);
