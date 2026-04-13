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
    updatePositionTriplet(data);
    updateImpulseHeadline(data);
    updateCycleTimeline(data);
    updateProjections(data);
    updateCompositeScore(data);
    saveAndRenderScoreHistory(data);
    updateLiquidityDashboard(data);
    updateEasingTracker(data);
    updateImpulseEngine(data);
    updateLayersGrouped(data);
    updateMarketData(data);
    updateRotation(data);
    updateSynopsis(data);
    updateHistoricalAnalog(data);
    updateAcceleratorsDecelerators(data);
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
// CYCLE POSITION TRIPLET (headline block)
// ═══════════════════════════════════════════════════════════════════

function updatePositionTriplet(data) {
    const cycle = data.cycle || {};
    const intel = data.intelligence || {};
    const pos = intel.position || cycle;
    const el = document.getElementById('position-triplet');
    if (!el) return;

    const months = pos.months_since_qt_end || 0;
    const regime = (pos.liquidity_regime || '--').replace(/_/g, ' ');
    const biz = (pos.business_cycle || pos.business_phase || '--').replace(/_/g, ' ');
    const btcPh = (pos.btc_cycle || pos.btc_phase || '--').replace(/_/g, ' ');

    const cards = [
        {
            label: 'Liquidity Regime',
            value: regime,
            sub: `${months.toFixed(0)} months post-QT`,
            icon: 'L',
        },
        {
            label: 'Business Cycle',
            value: biz,
            sub: `ANFCI ${(data.market_data?.anfci || 0).toFixed(2)}`,
            icon: 'B',
        },
        {
            label: 'BTC Cycle',
            value: btcPh,
            sub: `MVRV ${(data.market_data?.mvrv || 0).toFixed(2)}`,
            icon: 'C',
        },
    ];

    let html = '';
    for (const c of cards) {
        html += `<div class="triplet-card">`;
        html += `<div class="triplet-label">${c.label}</div>`;
        html += `<div class="triplet-value">${c.value}</div>`;
        html += `<div class="triplet-sub">${c.sub}</div>`;
        html += `</div>`;
    }
    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// IMPULSE HEADLINE (headline block)
// ═══════════════════════════════════════════════════════════════════

function updateImpulseHeadline(data) {
    const sig = data.signal || {};
    const el = document.getElementById('impulse-headline');
    if (!el) return;

    const imp = sig.impulse_probability || {};
    const aligned = sig.catalysts_aligned || 0;
    const total = sig.catalysts_total || 10;
    const window = sig.impulse_window || 'NOT_OPEN';
    const alignPct = total > 0 ? (aligned / total) * 100 : 0;

    let html = `<div class="impulse-headline-inner ${window.toLowerCase().replace('_','-')}">`;
    html += `<div class="impulse-headline-top">`;
    html += `<div class="impulse-title">Impulse Window</div>`;
    html += `<div class="impulse-status">${window.replace(/_/g, ' ')}</div>`;
    html += `</div>`;

    // Catalyst alignment progress bar
    html += `<div class="impulse-align-row">`;
    html += `<span class="impulse-align-label">${aligned}/${total} catalysts aligned</span>`;
    html += `<div class="impulse-align-track"><div class="impulse-align-fill" style="width:${alignPct}%"></div></div>`;
    html += `</div>`;

    // Probability strip
    html += `<div class="impulse-prob-strip">`;
    const periods = [
        { key: '1m', label: '1mo' },
        { key: '3m', label: '3mo' },
        { key: '6m', label: '6mo' },
        { key: '12m', label: '12mo' },
    ];
    for (const p of periods) {
        const pct = imp[p.key] || 0;
        html += `<div class="impulse-prob-item"><div class="impulse-prob-pct">${pct}%</div><div class="impulse-prob-label">${p.label}</div></div>`;
    }
    html += `</div></div>`;

    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// CYCLE TIMELINE (THE DIFFERENTIATOR)
// ═══════════════════════════════════════════════════════════════════

function updateCycleTimeline(data) {
    const intel = data.intelligence || {};
    const phases = intel.projected_phases || [];
    const events = intel.key_events || [];
    const el = document.getElementById('cycle-timeline');
    if (!el || phases.length === 0) return;

    const currentPhase = intel.current_phase || 1;

    let html = '';

    // Horizontal timeline bar
    html += '<div class="timeline-bar">';
    const phaseCount = phases.length;
    for (let i = 0; i < phaseCount; i++) {
        const p = phases[i];
        const statusClass = p.status === 'ACTIVE' ? 'active' : p.status === 'COMPLETED' ? 'completed' : 'projected';
        const isYouHere = p.status === 'ACTIVE';
        html += `<div class="timeline-segment ${statusClass}" style="flex:1" data-phase="${p.phase}" onclick="togglePhaseDetail(${p.phase})">`;
        if (isYouHere) {
            html += `<div class="you-are-here"><div class="you-marker">&#9660;</div><div class="you-label">YOU ARE HERE</div></div>`;
        }
        html += `<div class="timeline-segment-inner">`;
        html += `<div class="timeline-phase-num">Phase ${p.phase}</div>`;
        html += `<div class="timeline-phase-name">${p.name}</div>`;
        html += `<div class="timeline-phase-range">${p.timeline}</div>`;
        html += `<div class="timeline-phase-price">${p.price_range}</div>`;
        html += `</div>`;
        html += `</div>`;
    }
    html += '</div>';

    // Key events annotations
    if (events.length > 0) {
        html += '<div class="timeline-events">';
        html += '<div class="timeline-events-title">Calendar Checkpoints</div>';
        html += '<div class="timeline-events-list">';
        for (const ev of events) {
            const d = new Date(ev.date);
            const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const passed = d < new Date();
            html += `<div class="timeline-event ${passed ? 'passed' : 'future'} ${ev.category}">`;
            html += `<span class="event-date">${dateStr}</span>`;
            html += `<span class="event-label">${ev.label}</span>`;
            html += `</div>`;
        }
        html += '</div></div>';
    }

    // Expanded details for active phase
    const active = phases.find(p => p.status === 'ACTIVE');
    if (active) {
        html += `<div class="timeline-detail" id="timeline-detail">`;
        html += `<div class="detail-header"><strong>Phase ${active.phase}: ${active.name}</strong> <span class="detail-range">${active.timeline}</span></div>`;
        html += `<div class="detail-desc">${active.description}</div>`;
        html += `<div class="detail-signals"><strong>Key signals:</strong> ${active.key_signals}</div>`;
        html += `<div class="detail-price"><strong>BTC price range:</strong> ${active.price_range}</div>`;
        html += `</div>`;
    }

    el.innerHTML = html;
}

function togglePhaseDetail(phase) {
    const data = lastAnalysis;
    if (!data) return;
    const phases = (data.intelligence || {}).projected_phases || [];
    const p = phases.find(x => x.phase === phase);
    if (!p) return;
    const detail = document.getElementById('timeline-detail');
    if (!detail) return;
    detail.innerHTML =
        `<div class="detail-header"><strong>Phase ${p.phase}: ${p.name}</strong> <span class="detail-range">${p.timeline}</span> <span class="detail-status-${p.status.toLowerCase()}">${p.status}</span></div>` +
        `<div class="detail-desc">${p.description}</div>` +
        `<div class="detail-signals"><strong>Key signals:</strong> ${p.key_signals}</div>` +
        `<div class="detail-price"><strong>BTC price range:</strong> ${p.price_range}</div>`;
}

// ═══════════════════════════════════════════════════════════════════
// PRICE PROJECTIONS
// ═══════════════════════════════════════════════════════════════════

function updateProjections(data) {
    const proj = data.projections || {};
    const el = document.getElementById('projections-dashboard');
    if (!el || !proj.composite) return;

    const horizons = proj.horizons || [];
    const composite = proj.composite || {};
    const methods = proj.methods || {};
    const assumptions = proj.assumptions || {};
    const disclaimers = proj.disclaimers || [];

    let html = '';

    // ── Composite projection table ──
    html += '<div class="proj-composite">';
    html += '<div class="proj-composite-header">';
    html += '<h3>Composite Projection</h3>';
    html += '<div class="proj-assumptions-inline">';
    html += `<span>MVRV ${assumptions.current_mvrv || '--'}</span>`;
    html += `<span>RP $${((assumptions.current_rp || 0) / 1000).toFixed(0)}K</span>`;
    html += `<span>${(assumptions.current_phase || '--').replace(/_/g, ' ')}</span>`;
    html += `<span>&beta; ${assumptions.beta_used || '--'}</span>`;
    html += '</div></div>';

    html += '<div class="proj-table">';
    html += '<div class="proj-row proj-head">';
    html += '<span class="proj-cell">Horizon</span>';
    html += '<span class="proj-cell">Bear</span>';
    html += '<span class="proj-cell">Base</span>';
    html += '<span class="proj-cell">Bull</span>';
    html += '<span class="proj-cell">Convergence</span>';
    html += '<span class="proj-cell">Confidence</span>';
    html += '</div>';

    for (const h of horizons) {
        const c = composite[h];
        if (!c) continue;
        const confClass = (c.confidence || '').toLowerCase().replace('_', '-');
        const btcPrice = (data.market_data || {}).btc_price || 0;
        const baseReturn = btcPrice > 0 ? ((c.base - btcPrice) / btcPrice * 100).toFixed(0) : '--';

        html += `<div class="proj-row">`;
        html += `<span class="proj-cell proj-horizon">${h}</span>`;
        html += `<span class="proj-cell proj-bear">$${(c.bear / 1000).toFixed(0)}K</span>`;
        html += `<span class="proj-cell proj-base">$${(c.base / 1000).toFixed(0)}K <span class="proj-return">(${baseReturn > 0 ? '+' : ''}${baseReturn}%)</span></span>`;
        html += `<span class="proj-cell proj-bull">$${(c.bull / 1000).toFixed(0)}K</span>`;
        html += `<span class="proj-cell proj-conv">${c.convergence_pct}%</span>`;
        html += `<span class="proj-cell proj-conf ${confClass}">${(c.confidence || '').replace(/_/g, ' ')}</span>`;
        html += `</div>`;
    }
    html += '</div></div>';

    // ── Visual range bars ──
    html += '<div class="proj-range-chart">';
    // Find global min/max for scaling
    let globalMin = Infinity, globalMax = 0;
    for (const h of horizons) {
        const c = composite[h];
        if (!c) continue;
        globalMin = Math.min(globalMin, c.bear);
        globalMax = Math.max(globalMax, c.bull);
    }
    const range = globalMax - globalMin || 1;

    for (const h of horizons) {
        const c = composite[h];
        if (!c) continue;
        const bearPct = ((c.bear - globalMin) / range * 100);
        const basePct = ((c.base - globalMin) / range * 100);
        const bullPct = ((c.bull - globalMin) / range * 100);
        const barLeft = bearPct;
        const barWidth = bullPct - bearPct;

        html += `<div class="proj-bar-row">`;
        html += `<span class="proj-bar-label">${h}</span>`;
        html += `<div class="proj-bar-track">`;
        html += `<div class="proj-bar-range" style="left:${barLeft}%;width:${barWidth}%">`;
        html += `<div class="proj-bar-base" style="left:${barWidth > 0 ? ((basePct - bearPct) / barWidth * 100) : 50}%"></div>`;
        html += `</div>`;
        html += `</div>`;
        html += `<span class="proj-bar-val">$${(c.base / 1000).toFixed(0)}K</span>`;
        html += `</div>`;
    }
    html += '</div>';

    // ── Per-method breakdown (collapsible) ──
    html += '<div class="proj-methods">';
    html += '<div class="proj-methods-toggle" onclick="toggleSection(\'proj-methods-content\')"><h3>Method Breakdown</h3><span class="toggle-icon">&#9660;</span></div>';
    html += '<div class="proj-methods-content collapsed" id="proj-methods-content">';

    const methodLabels = {
        mvrv_anchored: 'MVRV-Anchored (40%)',
        score_to_return: 'Score-to-Return (25%)',
        liquidity_beta: 'Liquidity Beta (15%)',
        catalyst_weighted: 'Catalyst-Weighted (20%)',
    };

    for (const [key, label] of Object.entries(methodLabels)) {
        const m = methods[key];
        html += `<div class="proj-method-card">`;
        html += `<div class="proj-method-name">${label}</div>`;
        if (!m) {
            html += '<div class="proj-method-na">Data unavailable</div>';
        } else {
            html += '<div class="proj-method-grid">';
            for (const h of horizons) {
                const entry = m[h];
                if (!entry) continue;
                html += `<div class="proj-method-item">`;
                html += `<span class="pmh">${h}</span>`;
                html += `<span class="pmv">$${(entry.bear / 1000).toFixed(0)}K - $${(entry.bull / 1000).toFixed(0)}K</span>`;
                html += `</div>`;
            }
            html += '</div>';
            // Show notes from 365d entry
            const note = (m['365d'] || {}).notes;
            if (note) {
                html += `<div class="proj-method-note">${note}</div>`;
            }
        }
        html += '</div>';
    }

    html += '</div></div>';

    // ── Disclaimers ──
    if (disclaimers.length > 0) {
        html += '<div class="proj-disclaimers">';
        for (const d of disclaimers) {
            html += `<span class="proj-disclaimer">${d}</span>`;
        }
        html += '</div>';
    }

    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// LIQUIDITY DASHBOARD
// ═══════════════════════════════════════════════════════════════════

function updateLiquidityDashboard(data) {
    const md = data.market_data || {};
    const cycle = data.cycle || {};
    const el = document.getElementById('liquidity-dashboard');
    if (!el) return;

    const fedBs = md.fed_bs || 0;
    const rrp = md.rrp || 0;
    const tga = md.tga || 0;
    const netLiq = md.net_liquidity_b || 0;
    const m2Growth = md.global_m2_growth || 0;
    const regime = (cycle.liquidity_regime || '--').replace(/_/g, ' ');
    const monthsPostQt = cycle.months_since_qt_end || 0;

    let html = '';

    // ── Regime banner ──
    const regimeClass = regime.includes('QE') ? 'easing' : regime.includes('LAG') ? 'tightening' : 'neutral';
    html += `<div class="liq-regime-banner ${regimeClass}">`;
    html += `<div class="liq-regime-label">Liquidity Regime</div>`;
    html += `<div class="liq-regime-value">${regime}</div>`;
    html += `<div class="liq-regime-sub">${monthsPostQt.toFixed(0)} months post-QT end</div>`;
    html += '</div>';

    // ── Component cards (Fed BS, RRP, TGA, Net Liq) ──
    html += '<div class="liq-components">';

    const components = [
        { label: 'Fed Balance Sheet', value: fedBs, unit: 'B', color: 'var(--accent-blue)', desc: 'WALCL', sign: '+' },
        { label: 'Reverse Repo (RRP)', value: rrp, unit: 'B', color: 'var(--accent-red)', desc: 'RRPONTSYD', sign: '-' },
        { label: 'Treasury (TGA)', value: tga, unit: 'B', color: 'var(--accent-yellow)', desc: 'WTREGEN', sign: '-' },
    ];

    for (const c of components) {
        const displayVal = c.value >= 1 ? c.value.toFixed(0) : c.value.toFixed(1);
        html += `<div class="liq-card">`;
        html += `<div class="liq-card-header">`;
        html += `<span class="liq-card-label">${c.label}</span>`;
        html += `<span class="liq-card-sign" style="color:${c.color}">${c.sign}</span>`;
        html += `</div>`;
        html += `<div class="liq-card-value" style="color:${c.color}">$${displayVal}${c.unit}</div>`;
        html += `<div class="liq-card-desc">${c.desc}</div>`;
        html += `</div>`;
    }
    html += '</div>';

    // ── Net Liquidity formula bar ──
    html += '<div class="liq-formula">';
    html += `<div class="liq-formula-eq">`;
    html += `<span class="liq-f-term">Fed BS</span>`;
    html += `<span class="liq-f-op">-</span>`;
    html += `<span class="liq-f-term">RRP</span>`;
    html += `<span class="liq-f-op">-</span>`;
    html += `<span class="liq-f-term">TGA</span>`;
    html += `<span class="liq-f-op">=</span>`;
    html += `<span class="liq-f-result">Net Liquidity</span>`;
    html += `</div>`;
    const fmtB = v => v >= 1 ? `$${v.toFixed(0)}B` : `$${v.toFixed(1)}B`;
    html += `<div class="liq-formula-vals">`;
    html += `<span>${fmtB(fedBs)}</span>`;
    html += `<span>-</span>`;
    html += `<span>${fmtB(rrp)}</span>`;
    html += `<span>-</span>`;
    html += `<span>${fmtB(tga)}</span>`;
    html += `<span>=</span>`;
    html += `<span class="liq-net-val">${fmtB(netLiq)}</span>`;
    html += `</div>`;
    html += '</div>';

    // ── M2 Growth ──
    html += '<div class="liq-m2">';
    html += `<span class="liq-m2-label">Global M2 Growth (YoY)</span>`;
    const m2Class = m2Growth > 5 ? 'positive' : m2Growth > 0 ? 'neutral' : 'negative';
    html += `<span class="liq-m2-value ${m2Class}">${m2Growth.toFixed(1)}%</span>`;
    html += '</div>';

    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// EASING MECHANISM TRACKER
// ═══════════════════════════════════════════════════════════════════

function updateEasingTracker(data) {
    const intel = data.intelligence || {};
    const easing = intel.easing_mechanisms || [];
    const el = document.getElementById('easing-tracker');
    if (!el) return;

    let html = '<div class="easing-tracker-list">';
    html += '<div class="easing-tracker-header"><span>Mechanism</span><span>Probability</span><span>Status</span><span>Impact</span><span>Timeline</span></div>';
    for (const em of easing) {
        const pct = em.probability || 0;
        const statusClass = (em.status || 'unknown').toLowerCase();
        const barColor = pct >= 80 ? 'rgba(63, 185, 80, 0.4)' : pct >= 50 ? 'rgba(210, 153, 34, 0.4)' : 'rgba(139, 148, 158, 0.3)';
        html += `<div class="easing-tracker-row">`;
        html += `<span class="et-name">${em.mechanism}</span>`;
        html += `<div class="et-prob">`;
        html += `<div class="et-bar" style="width:${pct}%;background:${barColor}"></div>`;
        html += `<span class="et-pct">${pct}%</span>`;
        html += `</div>`;
        html += `<span class="et-status status-${statusClass}">${em.status || '--'}</span>`;
        html += `<span class="et-impact">${em.impact || ''}</span>`;
        html += `<span class="et-timeline">${em.timeline || ''}</span>`;
        html += `</div>`;
    }
    html += '</div>';
    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// SYNOPSIS BLOCK
// ═══════════════════════════════════════════════════════════════════

function updateSynopsis(data) {
    const syn = data.synopsis || {};
    const el = document.getElementById('synopsis-block');
    if (!el) return;

    let html = '';

    if (syn.todays_catalyst) {
        html += '<div class="synopsis-item">';
        html += '<h3 class="synopsis-title">Today\'s Catalyst</h3>';
        html += `<p class="synopsis-text">${syn.todays_catalyst}</p>`;
        html += '</div>';
    }

    if (syn.structural_picture) {
        html += '<div class="synopsis-item">';
        html += '<h3 class="synopsis-title">Structural Picture</h3>';
        html += `<p class="synopsis-text">${syn.structural_picture}</p>`;
        html += '</div>';
    }

    const risks = syn.risks_remaining || [];
    if (risks.length > 0) {
        html += '<div class="synopsis-item">';
        html += '<h3 class="synopsis-title">Risks Remaining</h3>';
        html += '<ul class="synopsis-risks">';
        for (const r of risks) {
            html += `<li>${r}</li>`;
        }
        html += '</ul></div>';
    }

    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// HISTORICAL ANALOG
// ═══════════════════════════════════════════════════════════════════

function updateHistoricalAnalog(data) {
    const analog = data.historical_analog || {};
    const el = document.getElementById('historical-analog');
    if (!el) return;

    const metrics = analog.metrics || [];
    const overall = analog.overall_match || 0;
    const matchClass = overall >= 80 ? 'high' : overall >= 60 ? 'medium' : 'low';

    let html = '';

    html += `<div class="analog-header">`;
    html += `<div class="analog-period">${analog.analog_period || 'Historical Analog'}</div>`;
    html += `<div class="analog-match ${matchClass}">Overall Match: <strong>${overall}%</strong></div>`;
    html += `</div>`;

    // Comparison table
    html += '<div class="analog-table">';
    html += '<div class="analog-row analog-head"><span>Metric</span><span>Q4 2019</span><span>Current</span><span>Match</span></div>';
    for (const m of metrics) {
        const matchC = m.match >= 80 ? 'high' : m.match >= 60 ? 'medium' : 'low';
        html += `<div class="analog-row">`;
        html += `<span class="analog-metric">${m.name}</span>`;
        html += `<span class="analog-past">${m.q4_2019}</span>`;
        html += `<span class="analog-curr">${m.current}</span>`;
        html += `<span class="analog-mpct match-${matchC}">${m.match}%</span>`;
        html += `</div>`;
    }
    html += '</div>';

    // What happened next
    const happened = analog.what_happened_next || [];
    if (happened.length > 0) {
        html += '<div class="analog-next">';
        html += '<h4>What Happened Next in the Analog Period</h4>';
        html += '<ul>';
        for (const h of happened) {
            html += `<li>${h}</li>`;
        }
        html += '</ul></div>';
    }

    if (analog.lesson) {
        html += `<div class="analog-lesson">${analog.lesson}</div>`;
    }

    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// ROTATION ANALYSIS
// ═══════════════════════════════════════════════════════════════════

function updateRotation(data) {
    const rot = data.rotation || {};
    const el = document.getElementById('rotation-analysis');
    if (!el) return;

    const conditions = rot.conditions || [];
    const allocation = rot.suggested_allocation || { BTC: 40, ETH: 30, ALT: 30 };

    let html = '';

    // Signal banner
    html += `<div class="rotation-banner rotation-${rot.signal_class || 'not-yet'}">`;
    html += `<div class="rotation-signal">${rot.signal || 'NOT YET'}</div>`;
    html += `<div class="rotation-met">${rot.conditions_met || 0}/${rot.conditions_total || 3} conditions met</div>`;
    html += `</div>`;

    // Conditions checklist
    html += '<div class="rotation-conditions">';
    html += '<h4>Rotation Conditions</h4>';
    for (const c of conditions) {
        const icon = c.met ? '&#10003;' : '&#10007;';
        const cls = c.met ? 'met' : 'not-met';
        html += `<div class="rotation-cond ${cls}">`;
        html += `<span class="rot-icon">${icon}</span>`;
        html += `<span class="rot-name">${c.name}</span>`;
        html += `<span class="rot-current">Current: <strong>${c.current}</strong></span>`;
        html += `</div>`;
    }
    html += '</div>';

    // Allocation suggestion
    html += '<div class="rotation-allocation">';
    html += '<h4>Suggested Allocation</h4>';
    html += '<div class="alloc-bars">';
    for (const [asset, pct] of Object.entries(allocation)) {
        const color = asset === 'BTC' ? '#f7931a' : asset === 'ETH' ? '#627eea' : '#a371f7';
        html += `<div class="alloc-item">`;
        html += `<div class="alloc-asset">${asset}</div>`;
        html += `<div class="alloc-bar-track"><div class="alloc-bar-fill" style="width:${pct}%;background:${color}"></div></div>`;
        html += `<div class="alloc-pct">${pct}%</div>`;
        html += `</div>`;
    }
    html += '</div></div>';

    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// LAYERS GROUPED BY CATEGORY
// ═══════════════════════════════════════════════════════════════════

const LAYER_GROUPS = [
    { name: 'Demand', layers: ['institutional_flow', 'institutional_struct'], weight_label: '25%' },
    { name: 'Risk', layers: ['leverage_fragility', 'derivatives', 'credit'], weight_label: '28%' },
    { name: 'Valuation', layers: ['mvrv', 'support'], weight_label: '14%' },
    { name: 'Macro', layers: ['liquidity_regime', 'cycle_phase', 'fed_transition', 'global_liquidity', 'oil_energy'], weight_label: '26%' },
    { name: 'Sentiment', layers: ['options_sentiment', 'sentiment'], weight_label: '7%' },
];

function updateLayersGrouped(data) {
    const layers = data.layers || {};
    const el = document.getElementById('layers-grouped');
    if (!el) return;

    let html = '';
    for (const group of LAYER_GROUPS) {
        // Calculate actual group weight
        let groupWeight = 0;
        let groupContribution = 0;
        for (const name of group.layers) {
            if (layers[name]) {
                groupWeight += (layers[name].weight || 0) * 100;
                groupContribution += layers[name].contribution || 0;
            }
        }

        html += `<div class="layer-group">`;
        html += `<div class="layer-group-header">`;
        html += `<h3 class="layer-group-name">${group.name}</h3>`;
        html += `<div class="layer-group-meta">${groupWeight.toFixed(0)}% weight · ${groupContribution.toFixed(1)} contribution</div>`;
        html += `</div>`;
        html += `<div class="layer-group-cards">`;

        for (const name of group.layers) {
            const layer = layers[name];
            if (!layer) continue;
            const score = layer.score || 0;
            const weight = ((layer.weight || 0) * 100).toFixed(0);
            const contribution = (layer.contribution || 0).toFixed(2);
            const barColor = getScoreColor(score);
            const label = LAYER_LABELS[name] || name;

            html += `<div class="layer-card">`;
            html += `<div class="layer-header">`;
            html += `<span class="layer-name">${label}</span>`;
            html += `<span class="layer-weight">${weight}%</span>`;
            html += `</div>`;
            html += `<div class="layer-bar-row">`;
            html += `<div class="layer-bar"><div class="layer-bar-fill" style="width:${score}%;background:${barColor};"></div></div>`;
            html += `<span class="layer-score">${score}</span>`;
            html += `</div>`;
            html += `<div class="layer-contribution">Contribution: ${contribution}</div>`;
            html += `<div class="layer-reasoning">${layer.reasoning || ''}</div>`;
            html += `</div>`;
        }

        html += `</div></div>`;
    }
    el.innerHTML = html;
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
// COMPOSITE SCORE HISTORY CHART
// ═══════════════════════════════════════════════════════════════════

const SCORE_HISTORY_KEY = 'btc_model_score_history';
const MAX_HISTORY_POINTS = 200;
let scoreChart = null;

function getScoreHistory() {
    try {
        return JSON.parse(localStorage.getItem(SCORE_HISTORY_KEY) || '[]');
    } catch { return []; }
}

function saveScoreEntry(data) {
    const sig = data.signal || {};
    const md = data.market_data || {};
    const ts = data.timestamp || new Date().toISOString();

    // Don't save demo/zero entries
    if (!sig.final_score || sig.final_score === 0) return;

    const history = getScoreHistory();

    // Deduplicate: skip if last entry is within 2 minutes
    if (history.length > 0) {
        const lastTime = new Date(history[history.length - 1].time).getTime();
        const thisTime = new Date(ts).getTime();
        if (Math.abs(thisTime - lastTime) < 120000) return;
    }

    history.push({
        time: ts,
        score: sig.final_score,
        base: sig.base_score,
        signal: sig.signal,
        price: md.btc_price || 0,
    });

    // Trim to max points
    while (history.length > MAX_HISTORY_POINTS) history.shift();

    localStorage.setItem(SCORE_HISTORY_KEY, JSON.stringify(history));
}

function clearScoreHistory() {
    localStorage.removeItem(SCORE_HISTORY_KEY);
    renderScoreChart([]);
}

function saveAndRenderScoreHistory(data) {
    saveScoreEntry(data);
    renderScoreChart(getScoreHistory());
}

function renderScoreChart(history) {
    const ctx = document.getElementById('score-history-chart');
    if (!ctx) return;

    const metaEl = document.getElementById('chart-data-points');
    if (metaEl) metaEl.textContent = history.length + ' data points';

    const labels = history.map(h => {
        const d = new Date(h.time);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
               ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    });

    const scores = history.map(h => h.score);
    const bases = history.map(h => h.base);
    const prices = history.map(h => h.price);

    // Signal zone backgrounds via annotation-like approach
    const zoneColors = scores.map(s => {
        if (s >= 75) return 'rgba(63, 185, 80, 0.9)';   // STRONG_BUY+
        if (s >= 65) return 'rgba(52, 211, 153, 0.9)';   // BUY
        if (s >= 55) return 'rgba(210, 153, 34, 0.9)';   // ACCUMULATE
        if (s >= 45) return 'rgba(245, 158, 11, 0.7)';   // HOLD
        if (s >= 35) return 'rgba(249, 115, 22, 0.8)';   // REDUCE
        return 'rgba(248, 81, 73, 0.9)';                  // SELL
    });

    if (scoreChart) {
        scoreChart.destroy();
    }

    scoreChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Final Score',
                    data: scores,
                    borderColor: '#58a6ff',
                    backgroundColor: 'rgba(88, 166, 255, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: zoneColors,
                    pointBorderColor: zoneColors,
                    pointRadius: history.length > 50 ? 2 : 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y',
                },
                {
                    label: 'Base Score',
                    data: bases,
                    borderColor: 'rgba(139, 148, 158, 0.5)',
                    borderWidth: 1,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0.3,
                    yAxisID: 'y',
                },
                {
                    label: 'BTC Price',
                    data: prices,
                    borderColor: '#f7931a',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.3,
                    yAxisID: 'y1',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: { color: '#8b949e', font: { family: "'Inter', sans-serif", size: 11 } },
                },
                tooltip: {
                    backgroundColor: '#1c2128',
                    titleColor: '#e6edf3',
                    bodyColor: '#8b949e',
                    borderColor: '#30363d',
                    borderWidth: 1,
                    callbacks: {
                        afterBody: function(items) {
                            const idx = items[0].dataIndex;
                            const h = getScoreHistory()[idx];
                            return h ? ['Signal: ' + (h.signal || '--')] : [];
                        },
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: '#6e7681',
                        font: { size: 10 },
                        maxRotation: 45,
                        maxTicksLimit: 12,
                    },
                    grid: { color: 'rgba(48, 54, 61, 0.5)' },
                },
                y: {
                    position: 'left',
                    min: 0,
                    max: 100,
                    ticks: {
                        color: '#8b949e',
                        font: { size: 11 },
                        stepSize: 25,
                        callback: function(v) {
                            if (v === 25) return '25 SELL';
                            if (v === 45) return '45 HOLD';
                            if (v === 65) return '65 BUY';
                            if (v === 85) return '85 AGG BUY';
                            return v;
                        },
                    },
                    grid: {
                        color: function(context) {
                            const v = context.tick.value;
                            if (v === 65) return 'rgba(63, 185, 80, 0.3)';
                            if (v === 45) return 'rgba(210, 153, 34, 0.3)';
                            if (v === 25) return 'rgba(248, 81, 73, 0.3)';
                            return 'rgba(48, 54, 61, 0.3)';
                        },
                    },
                },
                y1: {
                    position: 'right',
                    ticks: {
                        color: '#f7931a',
                        font: { size: 10 },
                        callback: function(v) { return '$' + (v/1000).toFixed(0) + 'K'; },
                    },
                    grid: { drawOnChartArea: false },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════════
// 14-LAYER SCORING
// ═══════════════════════════════════════════════════════════════════

const LAYER_LABELS = {
    institutional_flow: 'Institutional Flow',
    institutional_struct: 'Institutional Structure',
    leverage_fragility: 'Leverage Fragility',
    derivatives: 'Derivatives',
    mvrv: 'MVRV',
    liquidity_regime: 'Liquidity Regime',
    cycle_phase: 'Cycle Phase',
    fed_transition: 'Fed Transition',
    global_liquidity: 'Global Liquidity',
    options_sentiment: 'Options Sentiment',
    credit: 'Credit',
    oil_energy: 'Oil/Energy Risk',
    support: 'Support',
    sentiment: 'Sentiment',
    // v7.6 compat
    institutional: 'Institutional',
    macro_liquidity: 'Macro-Liquidity',
    momentum: 'Momentum',
};

const LAYER_ORDER = [
    'institutional_flow', 'institutional_struct', 'leverage_fragility', 'derivatives',
    'mvrv', 'liquidity_regime', 'cycle_phase', 'fed_transition',
    'global_liquidity', 'options_sentiment', 'credit', 'oil_energy',
    'support', 'sentiment',
    // v7.6 fallbacks (only shown if v7.7 layers not present)
    'institutional', 'macro_liquidity', 'momentum',
];

function getScoreColor(score) {
    if (score >= 70) return '#10b981';
    if (score >= 55) return '#34d399';
    if (score >= 45) return '#f59e0b';
    if (score >= 35) return '#f97316';
    return '#ef4444';
}

// ═══════════════════════════════════════════════════════════════════
// IMPULSE PROBABILITY ENGINE
// ═══════════════════════════════════════════════════════════════════

const CATALYST_LABELS = {
    treasury_stealth: 'Treasury Stealth Easing',
    bank_deregulation: 'Bank Deregulation',
    rate_cuts_expected: 'Rate Cuts Expected <6mo',
    oil_resolved: 'Oil Resolved (<$85 WTI)',
    mvrv_value: 'MVRV Value Zone (1.0-1.5)',
    sentiment_extreme: 'Extreme Fear (F&G <20)',
    etf_inflows: 'ETF Net Inflows',
    regime_maturing: 'Regime Maturing (>3mo)',
    chair_dovish: 'Chair Dovish Bias',
    credit_orderly: 'Credit Orderly (HY OAS <4%)',
};

function updateImpulseEngine(data) {
    const sig = data.signal || {};
    const el = document.getElementById('impulse-engine');
    if (!el) return;

    const imp = sig.impulse_probability || {};
    const catalysts = sig.catalysts_detail || {};
    const aligned = sig.catalysts_aligned || 0;
    const total = sig.catalysts_total || 10;
    const window = sig.impulse_window || 'NOT_OPEN';

    let html = '';

    // Window status banner
    html += `<div class="impulse-banner ${window.toLowerCase().replace('_','-')}">`;
    html += `<div class="impulse-window-label">Impulse Window: <strong>${window.replace(/_/g, ' ')}</strong></div>`;
    html += `<div class="impulse-aligned">${aligned}/${total} Catalysts Aligned</div>`;
    html += '</div>';

    // Probability timeline
    html += '<div class="impulse-probabilities">';
    html += '<h4>Impulse Probability Timeline</h4>';
    html += '<div class="prob-grid">';
    const periods = [
        { key: '1m', label: '1 Month' },
        { key: '3m', label: '3 Months' },
        { key: '6m', label: '6 Months' },
        { key: '12m', label: '12 Months' },
    ];
    for (const p of periods) {
        const pct = imp[p.key] || 0;
        const barColor = pct >= 60 ? '#3fb950' : pct >= 30 ? '#d29922' : '#8b949e';
        html += `<div class="prob-item">`;
        html += `<div class="prob-label">${p.label}</div>`;
        html += `<div class="prob-bar-track"><div class="prob-bar-fill" style="width:${pct}%;background:${barColor}"></div></div>`;
        html += `<div class="prob-value">${pct}%</div>`;
        html += `</div>`;
    }
    html += '</div></div>';

    // Catalyst grid
    html += '<div class="catalyst-grid">';
    html += '<h4>Catalyst Status</h4>';
    html += '<div class="catalyst-items">';
    for (const [key, value] of Object.entries(catalysts)) {
        const label = CATALYST_LABELS[key] || key.replace(/_/g, ' ');
        const status = value ? 'aligned' : 'not-aligned';
        const icon = value ? '&#10003;' : '&#10007;';
        html += `<div class="catalyst-item ${status}">`;
        html += `<span class="catalyst-icon">${icon}</span>`;
        html += `<span class="catalyst-name">${label}</span>`;
        html += '</div>';
    }
    html += '</div></div>';

    el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════
// PROJECTED CYCLE PHASES
// ═══════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════
// ACCELERATORS & DECELERATORS
// ═══════════════════════════════════════════════════════════════════

function updateAcceleratorsDecelerators(data) {
    const intel = data.intelligence || {};
    const el = document.getElementById('cycle-intelligence');
    if (!el) return;

    let html = '';

    const accel = intel.accelerators || [];
    const decel = intel.decelerators || [];
    if (accel.length > 0 || decel.length > 0) {
        html += '<div class="cycle-drivers">';
        if (accel.length > 0) {
            html += '<div class="drivers-col"><h4>Accelerators</h4>';
            accel.forEach(a => html += `<div class="driver-item positive">+ ${a}</div>`);
            html += '</div>';
        }
        if (decel.length > 0) {
            html += '<div class="drivers-col"><h4>Decelerators</h4>';
            decel.forEach(d => html += `<div class="driver-item negative">- ${d}</div>`);
            html += '</div>';
        }
        html += '</div>';
    } else {
        html = '<p class="no-data">No active accelerators or decelerators.</p>';
    }

    el.innerHTML = html;
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
    setText('eth-etf-daily', formatFlowM(md.eth_etf_flow_daily || 0));
    setText('eth-etf-cumulative', formatCompact(md.eth_etf_cumulative || 0));

    // Macro
    setText('hy-oas', (md.hy_oas || 0).toFixed(2) + '%');
    setText('yield-curve', (md.yield_curve_2s10s || 0).toFixed(2) + '%');
    setText('init-claims', ((md.initial_claims || 0) / 1000).toFixed(0) + 'K');
    setText('anfci-value', (md.anfci || 0).toFixed(3));
    setText('wti-price', '$' + (md.wti_price || 0).toFixed(0));
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
    if (ds.live_data_status === 'no_data') statusText = 'NO DATA — Check API Keys';
    else if (ds.live_data_status === 'demo') statusText = 'Demo Data';
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
