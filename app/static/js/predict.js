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

const PRESETS = {
    'healthy': {
        'Glucose': 0.12, 'Insulin': 0.15, 'BMI': 0.22, 'HbA1c': 0.10, 'Cholesterol': 0.15,
        'LDL Cholesterol': 0.14, 'HDL Cholesterol': 0.65, 'Triglycerides': 0.12,
        'Systolic Blood Pressure': 0.20, 'Diastolic Blood Pressure': 0.15,
        'Heart Rate': 0.18, 'Troponin': 0.05, 'Hemoglobin': 0.65, 'Platelets': 0.55,
        'White Blood Cells': 0.45, 'Red Blood Cells': 0.60, 'Hematocrit': 0.58,
        'Mean Corpuscular Volume': 0.52, 'Mean Corpuscular Hemoglobin': 0.55,
        'Mean Corpuscular Hemoglobin Concentration': 0.50, 'ALT': 0.15, 'AST': 0.14,
        'Creatinine': 0.18, 'C-reactive Protein': 0.08
    },
    'diabetes': {
        'Glucose': 0.85, 'Insulin': 0.72, 'BMI': 0.62, 'HbA1c': 0.78, 'Cholesterol': 0.45,
        'LDL Cholesterol': 0.48, 'HDL Cholesterol': 0.25, 'Triglycerides': 0.55,
        'Systolic Blood Pressure': 0.45, 'Diastolic Blood Pressure': 0.42,
        'Heart Rate': 0.48, 'Troponin': 0.15, 'Hemoglobin': 0.55, 'Platelets': 0.62,
        'White Blood Cells': 0.58, 'Red Blood Cells': 0.52, 'Hematocrit': 0.50,
        'Mean Corpuscular Volume': 0.48, 'Mean Corpuscular Hemoglobin': 0.45,
        'Mean Corpuscular Hemoglobin Concentration': 0.42, 'ALT': 0.45, 'AST': 0.42,
        'Creatinine': 0.52, 'C-reactive Protein': 0.55
    },
    'anemia': {
        'Glucose': 0.42, 'Insulin': 0.35, 'BMI': 0.45, 'HbA1c': 0.38, 'Cholesterol': 0.35,
        'LDL Cholesterol': 0.32, 'HDL Cholesterol': 0.45, 'Triglycerides': 0.38,
        'Systolic Blood Pressure': 0.35, 'Diastolic Blood Pressure': 0.32,
        'Heart Rate': 0.65, 'Troponin': 0.12, 'Hemoglobin': 0.15, 'Platelets': 0.45,
        'White Blood Cells': 0.42, 'Red Blood Cells': 0.22, 'Hematocrit': 0.18,
        'Mean Corpuscular Volume': 0.25, 'Mean Corpuscular Hemoglobin': 0.22,
        'Mean Corpuscular Hemoglobin Concentration': 0.18, 'ALT': 0.35, 'AST': 0.32,
        'Creatinine': 0.38, 'C-reactive Protein': 0.45
    },
    'heart': {
        'Glucose': 0.52, 'Insulin': 0.45, 'BMI': 0.58, 'HbA1c': 0.48, 'Cholesterol': 0.85,
        'LDL Cholesterol': 0.82, 'HDL Cholesterol': 0.15, 'Triglycerides': 0.75,
        'Systolic Blood Pressure': 0.82, 'Diastolic Blood Pressure': 0.78,
        'Heart Rate': 0.85, 'Troponin': 0.88, 'Hemoglobin': 0.45, 'Platelets': 0.52,
        'White Blood Cells': 0.65, 'Red Blood Cells': 0.42, 'Hematocrit': 0.40,
        'Mean Corpuscular Volume': 0.45, 'Mean Corpuscular Hemoglobin': 0.42,
        'Mean Corpuscular Hemoglobin Concentration': 0.40, 'ALT': 0.52, 'AST': 0.48,
        'Creatinine': 0.55, 'C-reactive Protein': 0.85
    },
    'thalassemia': {
        'Glucose': 0.38, 'Insulin': 0.32, 'BMI': 0.42, 'HbA1c': 0.35, 'Cholesterol': 0.32,
        'LDL Cholesterol': 0.28, 'HDL Cholesterol': 0.42, 'Triglycerides': 0.35,
        'Systolic Blood Pressure': 0.32, 'Diastolic Blood Pressure': 0.28,
        'Heart Rate': 0.55, 'Troponin': 0.15, 'Hemoglobin': 0.22, 'Platelets': 0.48,
        'White Blood Cells': 0.45, 'Red Blood Cells': 0.72, 'Hematocrit': 0.20,
        'Mean Corpuscular Volume': 0.20, 'Mean Corpuscular Hemoglobin': 0.18,
        'Mean Corpuscular Hemoglobin Concentration': 0.15, 'ALT': 0.38, 'AST': 0.35,
        'Creatinine': 0.42, 'C-reactive Protein': 0.32
    }
};

const DISEASE_COLORS = {
    'Healthy': '#C5E710',
    'Diabetes': '#F4DF6B',
    'Anemia': '#8E9630',
    'Heart Disease': '#e74c3c',
    'Thalassemia': '#9b59b6',
    'Thrombocytopenia': '#e67e22'
};

let selectedModel = 'random_forest';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Model Selection
    const mcards = document.querySelectorAll('.mcard');
    mcards.forEach(card => {
        card.addEventListener('click', () => {
            mcards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedModel = card.getAttribute('data-model');
        });
    });

    // 2. Preset Selection
    const pbtns = document.querySelectorAll('.pbtn');
    pbtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.getAttribute('data-preset');
            applyPreset(key);
        });
    });

    // 3. Apply Preset with Staggered Animation
    function applyPreset(key) {
        const presetData = PRESETS[key];
        if (!presetData) return;

        FEATURES.forEach((feat, index) => {
            const input = document.querySelector(`input[data-feature="${feat}"]`);
            if (input) {
                setTimeout(() => {
                    input.value = presetData[feat];
                    input.classList.add('flash-lime');
                    setTimeout(() => input.classList.remove('flash-lime'), 500);
                    checkInputsFilled();
                }, index * 30);
            }
        });
    }

    // 4. Collect Features and Validate
    function collectFeatures() {
        const values = {};
        let valid = true;
        
        FEATURES.forEach(feat => {
            const input = document.querySelector(`input[data-feature="${feat}"]`);
            if (!input || input.value === '') {
                valid = false;
                if (input) input.style.borderColor = '#e74c3c';
            } else {
                values[feat] = parseFloat(input.value);
                if (input) input.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            }
        });

        return { values, valid };
    }

    // 5. Predict Button Click
    const predictBtn = document.getElementById('predictBtn');
    predictBtn.addEventListener('click', async () => {
        const { values, valid } = collectFeatures();
        
        if (!valid) {
            alert('Please fill all 24 biomarker fields for analytical consistency.');
            return;
        }

        showLoading();

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: selectedModel,
                    features: values
                })
            });

            const result = await response.json();
            if (response.ok) {
                setTimeout(() => showResult(result), 1000); // Artificial delay for feeling "analytical"
            } else {
                showError(result.error);
            }
        } catch (err) {
            showError('Network error connecting to diagnostic engine.');
        }
    });

    // 6. Interaction logic: Pulse button if all filled
    function checkInputsFilled() {
        const inputs = document.querySelectorAll('.biomarker-input');
        let allFilled = true;
        inputs.forEach(i => { if (i.value === '') allFilled = false; });
        
        if (allFilled) {
            predictBtn.classList.add('pulse-lime');
        } else {
            predictBtn.classList.remove('pulse-lime');
        }
    }
    document.querySelectorAll('.biomarker-input').forEach(i => i.addEventListener('input', checkInputsFilled));

    // 7. Reset Logic
    const resetBtn = document.getElementById('resetBtn');
    resetBtn.addEventListener('click', () => {
        document.querySelectorAll('.biomarker-input').forEach(i => i.value = '');
        document.getElementById('resultEmpty').style.display = 'flex';
        document.getElementById('resultLoading').style.display = 'none';
        document.getElementById('resultContent').style.display = 'none';
        predictBtn.classList.remove('pulse-lime');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});

// UI Helper Functions
function showLoading() {
    document.getElementById('resultEmpty').style.display = 'none';
    document.getElementById('resultContent').style.display = 'none';
    document.getElementById('resultLoading').style.display = 'flex';
}

function showError(msg) {
    document.getElementById('resultLoading').style.display = 'none';
    document.getElementById('resultEmpty').style.display = 'flex';
    alert('ERROR: ' + msg);
}

function showResult(data) {
    document.getElementById('resultLoading').style.display = 'none';
    document.getElementById('resultContent').style.display = 'block';

    const dot = document.getElementById('resultDot');
    dot.style.background = data.color;
    dot.style.boxShadow = `0 0 15px ${data.color}`;

    // Confidence Counter
    animateValue('confidenceBadge', 0, data.confidence, 1500, '%');

    // Disease Card
    const card = document.getElementById('resultDiseaseCard');
    card.style.background = `rgba(${hexToRgb(data.color)}, 0.1)`;
    card.style.borderColor = data.color;

    const iconDiv = document.getElementById('rdiseaseIcon');
    iconDiv.style.color = data.color;
    iconDiv.innerHTML = getConditionIcon(data.prediction);

    const name = document.getElementById('rdiseaseName');
    name.style.color = data.color;
    typeWriter(name, data.prediction); // Typewriter effect

    document.getElementById('rdiseaseDesc').innerText = data.description;

    // Probability Bars
    const barsContainer = document.getElementById('probBars');
    barsContainer.innerHTML = '';
    
    // Sort probabilities descending
    const sortedProbs = Object.entries(data.probabilities).sort((a,b) => b[1] - a[1]);
    
    sortedProbs.forEach(([label, p], index) => {
        const row = document.createElement('div');
        row.className = 'prob-row';
        row.innerHTML = `
            <div class="prob-label"><span>${label}</span><span>${p}%</span></div>
            <div class="prob-bar-bg"><div class="prob-bar-fill" style="--w: ${p}%; background: ${DISEASE_COLORS[label] || 'var(--olive)'}"></div></div>
        `;
        barsContainer.appendChild(row);
        
        // Trigger width transition with stagger
        setTimeout(() => {
            row.querySelector('.prob-bar-fill').style.width = p + '%';
        }, 100 + (index * 100));
    });

    // Recommendations
    const recoList = document.getElementById('recoList');
    recoList.innerHTML = '';
    data.recommendations.forEach((reco, index) => {
        const li = document.createElement('li');
        li.innerText = reco;
        li.style.animationDelay = (0.5 + index * 0.1) + 's';
        recoList.appendChild(li);
    });
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '255, 255, 255';
}

function animateValue(id, start, end, duration, suffix = '') {
    const obj = document.getElementById(id);
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const val = Math.floor(progress * (end - start) + start);
        obj.innerHTML = val.toFixed(1) + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function typeWriter(el, text) {
    el.innerText = '';
    let i = 0;
    const speed = 50;
    function type() {
        if (i < text.length) {
            el.innerText += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

function getConditionIcon(type) {
    if (type === 'Healthy') return '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>';
    if (type === 'Diabetes') return '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07L19.07 4.93"></path></svg>';
    if (type === 'Heart Disease') return '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>';
    return '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4M12 16h.01"></path></svg>';
}

// Global UI Animations
const pulseStyle = document.createElement('style');
pulseStyle.textContent = `
    .pulse-lime {
        animation: pulseLimeBtn 2s infinite;
    }
    @keyframes pulseLimeBtn {
        0% { box-shadow: 0 0 0 0 rgba(197, 231, 16, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(197, 231, 16, 0); }
        100% { box-shadow: 0 0 0 0 rgba(197, 231, 16, 0); }
    }
`;
document.head.appendChild(pulseStyle);
