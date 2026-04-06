/**
 * SmartHealth AI - Predict Page JavaScript
 * Author: Enock Queenson Eduafo
 */

const FEATURES = [
    'Glucose', 'Insulin', 'BMI', 'HbA1c', 'Cholesterol', 'LDL Cholesterol', 
    'HDL Cholesterol', 'Triglycerides', 'Systolic Blood Pressure', 
    'Diastolic Blood Pressure', 'Heart Rate', 'Troponin', 'Hemoglobin', 
    'Platelets', 'White Blood Cells', 'Red Blood Cells', 'Hematocrit', 
    'Mean Corpuscular Volume', 'Mean Corpuscular Hemoglobin', 
    'Mean Corpuscular Hemoglobin Concentration', 'ALT', 'AST', 'Creatinine', 
    'C-reactive Protein'
];

const DISEASE_COLORS = {
    'Healthy Reference': '#A8E63D',
    'Type 2 Diabetes': '#F4DF6B',
    'Clinical Anemia': '#8E9630',
    'Heart Condition': '#e74c3c',
    'Thalassemia': '#9b59b6',
    'Thrombocytopenia': '#e67e22'
};

const PRESETS = {
    'healthy': [0.12, 0.15, 0.22, 0.10, 0.15, 0.14, 0.65, 0.12, 0.20, 0.15, 0.18, 0.05, 0.65, 0.55, 0.45, 0.60, 0.58, 0.52, 0.55, 0.50, 0.15, 0.14, 0.18, 0.08],
    'diabetes': [0.85, 0.72, 0.62, 0.78, 0.45, 0.48, 0.25, 0.55, 0.45, 0.42, 0.48, 0.15, 0.55, 0.62, 0.58, 0.52, 0.50, 0.48, 0.45, 0.42, 0.45, 0.42, 0.52, 0.55],
    'anemia': [0.42, 0.35, 0.45, 0.38, 0.35, 0.32, 0.45, 0.38, 0.35, 0.32, 0.65, 0.12, 0.15, 0.45, 0.42, 0.22, 0.18, 0.25, 0.22, 0.18, 0.35, 0.32, 0.38, 0.45],
    'heart': [0.52, 0.45, 0.58, 0.48, 0.85, 0.82, 0.15, 0.75, 0.82, 0.78, 0.85, 0.88, 0.45, 0.52, 0.65, 0.42, 0.40, 0.45, 0.42, 0.40, 0.52, 0.48, 0.55, 0.85]
};

let selectedModel = 'random_forest';

document.addEventListener('DOMContentLoaded', () => {
    const mcards = document.querySelectorAll('.classifier-card, .mcard');
    mcards.forEach(card => {
        card.addEventListener('click', () => {
            mcards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedModel = card.getAttribute('data-model') || 'random_forest';
        });
    });

    const pbtns = document.querySelectorAll('.preset-btn, .pbtn');
    pbtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.getAttribute('data-preset');
            applyPreset(key);
        });
    });

    function applyPreset(key) {
        const values = PRESETS[key];
        if (!values) return;
        const inputs = document.querySelectorAll('.biomarker-input');
        inputs.forEach((input, i) => {
            if (values[i] !== undefined) {
                setTimeout(() => {
                    input.value = values[i];
                    input.classList.add('flash-lime');
                    setTimeout(() => input.classList.remove('flash-lime'), 500);
                    checkInputsFilled();
                }, i * 30);
            }
        });
    }

    const predictBtn = document.getElementById('predictBtn');
    if (predictBtn) {
        predictBtn.addEventListener('click', runDiagnosis);
    }

    async function runDiagnosis() {
        const features = getFormValues();
        if (features.length !== 24) {
            showError('Please fill all 24 biomarker fields.');
            return;
        }

        showLoading();

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    features: features, 
                    model: selectedModel 
                })
            });
            
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Server error');
            }
            
            const result = await response.json();
            setTimeout(() => showResult(result), 800);
            
        } catch (error) {
            showError(error.message);
        }
    }

    function getFormValues() {
        const inputs = document.querySelectorAll('.biomarker-input');
        const values = [];
        inputs.forEach(input => {
            if (input.value !== '') values.push(parseFloat(input.value));
        });
        return values;
    }

    function checkInputsFilled() {
        const inputs = document.querySelectorAll('.biomarker-input');
        let filled = 0;
        inputs.forEach(i => { if (i.value !== '') filled++; });
        if (predictBtn) {
            if (filled === 24) predictBtn.classList.add('pulse-lime');
            else predictBtn.classList.remove('pulse-lime');
        }
    }

    document.querySelectorAll('.biomarker-input').forEach(i => {
        i.addEventListener('input', checkInputsFilled);
    });
});

function showLoading() {
    const empty = document.getElementById('resultEmpty');
    const load = document.getElementById('resultLoading');
    const content = document.getElementById('resultContent');
    if (empty) empty.style.display = 'none';
    if (content) content.style.display = 'none';
    if (load) load.style.display = 'flex';
}

function showError(msg) {
    const load = document.getElementById('resultLoading');
    const empty = document.getElementById('resultEmpty');
    if (load) load.style.display = 'none';
    if (empty) empty.style.display = 'flex';
    alert('Diagnosis Error: ' + msg);
}

function showResult(result) {
    const load = document.getElementById('resultLoading');
    const content = document.getElementById('resultContent');
    if (load) load.style.display = 'none';
    if (content) {
        content.style.display = 'block';
        content.classList.add('result-animate-in');
    }

    // Map JSON to UI
    const nameEl = document.getElementById('rdiseaseName');
    const descEl = document.getElementById('rdiseaseDesc');
    const confEl = document.getElementById('confidenceBadge');
    
    if (nameEl) {
        nameEl.innerText = result.prediction;
        nameEl.style.color = DISEASE_COLORS[result.prediction] || '#A8E63D';
    }
    if (descEl) descEl.innerText = result.description;
    
    if (confEl) {
        animateValue('confidenceBadge', 0, result.confidence, 1500, '%');
    }

    // Probabilities
    const probContainer = document.getElementById('probBars');
    if (probContainer) {
        probContainer.innerHTML = '';
        Object.entries(result.probabilities).forEach(([label, prob]) => {
            const row = document.createElement('div');
            row.className = 'prob-row reveal';
            row.innerHTML = `
                <div class="prob-label">
                    <span>${label}</span>
                    <span>${prob.toFixed(1)}%</span>
                </div>
                <div class="prob-bar-bg">
                    <div class="bar-fill" data-target="${prob}" style="width:0%; background:${DISEASE_COLORS[label] || '#8E9630'}"></div>
                </div>
            `;
            probContainer.appendChild(row);
        });
        
        // Animate bars
        setTimeout(() => {
            probContainer.querySelectorAll('.prob-bar-fill').forEach(bar => {
                const target = bar.getAttribute('data-target');
                bar.style.transition = 'width 1.2s cubic-bezier(0.16, 1, 0.3, 1)';
                bar.style.width = target + '%';
            });
        }, 100);
    }

    // Recommendations
    const recoList = document.getElementById('recoList');
    if (recoList) {
        recoList.innerHTML = '';
        result.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.innerText = rec;
            recoList.appendChild(li);
        });
    }

    // Set dot color
    const dot = document.getElementById('resultDot');
    if (dot) dot.style.background = DISEASE_COLORS[result.prediction] || '#A8E63D';
}

function animateValue(id, start, end, duration, suffix = '') {
    const obj = document.getElementById(id);
    if (!obj) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const val = progress * (end - start) + start;
        obj.innerHTML = val.toFixed(1) + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}
