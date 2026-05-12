/**
 * Smart Health Sync v2.0 — Diagnosis Engine JavaScript
 * Author: Enock Queenson Eduafo | University of Ghana 2026
 *
 * Key fix: sends features as a named dict (matches new backend API)
 */

"use strict";

// ── Feature order (matches backend FEATURE_ORDER) ─────────────
const FEATURES = [
    'Glucose', 'Cholesterol', 'Hemoglobin', 'Platelets',
    'White Blood Cells', 'Red Blood Cells', 'Hematocrit',
    'Mean Corpuscular Volume', 'Mean Corpuscular Hemoglobin',
    'Mean Corpuscular Hemoglobin Concentration',
    'Insulin', 'BMI', 'Systolic Blood Pressure', 'Diastolic Blood Pressure',
    'Triglycerides', 'HbA1c', 'LDL Cholesterol', 'HDL Cholesterol',
    'ALT', 'AST', 'Heart Rate', 'Creatinine', 'Troponin', 'C-reactive Protein'
];

const DISEASE_COLORS = {
    'Healthy':          '#C5E710',
    'Diabetes':         '#F4DF6B',
    'Anemia':           '#ff9966',
    'Heart Disease':    '#ff4757',
    'Thalassemia':      '#a855f7',
    'Thrombocytopenia': '#0099bb',
};

// ── Preset clinical biomarker values ─────────────────────────
// Order matches FEATURES array above
const PRESETS = {
    healthy:  [0.12, 0.15, 0.65, 0.55, 0.45, 0.60, 0.58, 0.52, 0.55, 0.50,
               0.15, 0.22, 0.65, 0.45, 0.18, 0.10, 0.14, 0.65, 0.15, 0.14,
               0.18, 0.15, 0.05, 0.08],
    diabetes: [0.85, 0.45, 0.55, 0.62, 0.42, 0.52, 0.50, 0.48, 0.45, 0.42,
               0.72, 0.62, 0.45, 0.42, 0.55, 0.78, 0.48, 0.25, 0.45, 0.42,
               0.48, 0.52, 0.15, 0.55],
    anemia:   [0.42, 0.35, 0.15, 0.45, 0.42, 0.22, 0.18, 0.25, 0.22, 0.18,
               0.35, 0.45, 0.35, 0.32, 0.38, 0.38, 0.32, 0.45, 0.35, 0.32,
               0.65, 0.38, 0.12, 0.45],
    heart:    [0.52, 0.85, 0.45, 0.52, 0.55, 0.40, 0.40, 0.45, 0.42, 0.40,
               0.45, 0.58, 0.82, 0.78, 0.65, 0.48, 0.82, 0.15, 0.52, 0.48,
               0.85, 0.55, 0.88, 0.85],
};

// ── DOM Ready ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initModelSelector();
    initPresets();
    initForm();
});

// ── Model Selector ────────────────────────────────────────────
function initModelSelector() {
    const options = document.querySelectorAll('.model-option');
    const hidden  = document.getElementById('selectedModel');
    options.forEach(opt => {
        opt.addEventListener('click', () => {
            options.forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            if (hidden) hidden.value = opt.dataset.model;
        });
    });
}

// ── Presets ───────────────────────────────────────────────────
function initPresets() {
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', () => applyPreset(btn.dataset.preset));
    });
}

function applyPreset(key) {
    const values = PRESETS[key];
    if (!values) return;
    const inputs = document.querySelectorAll('.biomarker-input');
    inputs.forEach((input, i) => {
        if (values[i] !== undefined) {
            setTimeout(() => {
                input.value = values[i];
                input.style.borderColor = 'var(--cyan-primary)';
                setTimeout(() => (input.style.borderColor = ''), 500);
            }, i * 25);
        }
    });
}

// ── Form ──────────────────────────────────────────────────────
function initForm() {
    const form = document.getElementById('predictionForm');
    if (!form) return;
    form.addEventListener('submit', async e => {
        e.preventDefault();
        await runDiagnosis();
    });
}

async function runDiagnosis() {
    const features = collectFeatures();
    if (!features) return;                     // validation failed
    const model = document.getElementById('selectedModel')?.value || 'random_forest';

    const btn = document.getElementById('submitBtn');
    setLoading(btn, true);

    try {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ features, model }),
        });

        const data = await res.json();

        if (!res.ok) {
            const msg = data.details
                ? `${data.error}\n\nDetails: ${JSON.stringify(data.details, null, 2)}`
                : (data.error || `HTTP ${res.status}`);
            showError(msg);
            return;
        }

        setTimeout(() => showResult(data), 600);
    } catch (err) {
        showError('Network error: ' + err.message);
    } finally {
        setTimeout(() => setLoading(btn, false), 650);
    }
}

/**
 * Collect inputs and return a named dict {featureName: value}
 * or null if validation fails.
 */
function collectFeatures() {
    const inputs  = document.querySelectorAll('.biomarker-input');
    const dict    = {};
    let hasError  = false;

    inputs.forEach((input, i) => {
        const name = input.dataset.feature || FEATURES[i];
        const val  = parseFloat(input.value);
        if (isNaN(val)) {
            hasError = true;
            input.style.borderColor = 'var(--red-critical)';
        } else {
            dict[name] = val;
            input.style.borderColor = '';
        }
    });

    if (hasError) {
        showError('Please fill in all 24 biomarker fields with valid numbers (0.0 – 1.0).');
        return null;
    }
    return dict;
}

// ── Results Panel ─────────────────────────────────────────────
function showResult(result) {
    const panel = document.getElementById('resultsPanel');
    if (!panel) return;

    panel.style.display = 'block';
    setTimeout(() => panel.classList.add('visible'), 10);

    document.getElementById('diagnosisName').textContent  = result.prediction || '—';
    document.getElementById('diagnosisName').style.color  =
        DISEASE_COLORS[result.prediction] || 'var(--cyan-primary)';
    document.getElementById('diagnosisDescription').textContent = result.description || '';
    document.getElementById('confidencePercent').textContent    =
        `Confidence: ${(result.confidence || 0).toFixed(1)}%`;
    document.getElementById('confidenceBar').style.width        =
        (result.confidence || 0) + '%';

    // Probability bars
    const table = document.getElementById('probTable');
    if (table) {
        table.innerHTML = '';
        const sorted = Object.entries(result.probabilities || {})
            .sort(([, a], [, b]) => b - a);
        sorted.forEach(([name, prob]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="padding: 8px 0; font-size:0.85rem;">${name}</td>
                <td class="prob-bar-cell">
                    <div class="prob-bar">
                        <div class="prob-fill" style="width:${prob}%;
                             background:${DISEASE_COLORS[name] || 'var(--cyan-primary)'}">
                        </div>
                    </div>
                </td>
                <td style="text-align:right;font-family:var(--font-mono);font-size:0.8rem;">
                    ${prob.toFixed(1)}%
                </td>`;
            table.appendChild(row);
        });
    }

    // Recommendations
    const list = document.getElementById('clinicalAdvice');
    if (list) {
        list.innerHTML = '';
        (result.recommendations || []).forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            list.appendChild(li);
        });
    }

    if (result.fallback_used) {
        console.warn('[SmartHealth] Fallback model was used:', result.model_used);
    }

    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── UI Helpers ────────────────────────────────────────────────
function setLoading(btn, loading) {
    if (!btn) return;
    btn.disabled = loading;
    btn.classList.toggle('loading', loading);
}

function showError(message) {
    // Try to use the results panel for a cleaner UX, fall back to alert
    const panel = document.getElementById('resultsPanel');
    if (panel) {
        panel.style.display = 'block';
        setTimeout(() => panel.classList.add('visible'), 10);
        const nameEl = document.getElementById('diagnosisName');
        const descEl = document.getElementById('diagnosisDescription');
        if (nameEl) { nameEl.textContent = '⚠ Diagnosis Error'; nameEl.style.color = 'var(--red-critical)'; }
        if (descEl) descEl.textContent = message;
        const probTable = document.getElementById('probTable');
        if (probTable) probTable.innerHTML = '';
        const advice = document.getElementById('clinicalAdvice');
        if (advice) advice.innerHTML = '<li>Please check model availability at <code>/api/health/models</code></li>';
        panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        alert('Error: ' + message);
    }
}
