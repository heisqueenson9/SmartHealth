/**
 * Smart Health Sync - Predict Page JavaScript
 * Full-Stack Overhaul (Lime & Black Theme)
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
    'Healthy Reference': '#C5E710',
    'Type 2 Diabetes': '#F4DF6B',
    'Clinical Anemia': '#8E9630',
    'Heart Condition': '#ff4757',
    'Thalassemia': '#a855f7',
    'Thrombocytopenia': '#0099bb'
};

const PRESETS = {
    'healthy': [0.12, 0.15, 0.22, 0.10, 0.15, 0.14, 0.65, 0.12, 0.20, 0.15, 0.18, 0.05, 0.65, 0.55, 0.45, 0.60, 0.58, 0.52, 0.55, 0.50, 0.15, 0.14, 0.18, 0.08],
    'diabetes': [0.85, 0.72, 0.62, 0.78, 0.45, 0.48, 0.25, 0.55, 0.45, 0.42, 0.48, 0.15, 0.55, 0.62, 0.58, 0.52, 0.50, 0.48, 0.45, 0.42, 0.45, 0.42, 0.52, 0.55],
    'anemia': [0.42, 0.35, 0.45, 0.38, 0.35, 0.32, 0.45, 0.38, 0.35, 0.32, 0.65, 0.12, 0.15, 0.45, 0.42, 0.22, 0.18, 0.25, 0.22, 0.18, 0.35, 0.32, 0.38, 0.45],
    'heart': [0.52, 0.45, 0.58, 0.48, 0.85, 0.82, 0.15, 0.75, 0.82, 0.78, 0.85, 0.88, 0.45, 0.52, 0.65, 0.42, 0.40, 0.45, 0.42, 0.40, 0.52, 0.48, 0.55, 0.85]
};

document.addEventListener('DOMContentLoaded', () => {
    // Model Selection
    const modelOptions = document.querySelectorAll('.model-option');
    const selectedModelInput = document.getElementById('selectedModel');
    
    modelOptions.forEach(option => {
        option.addEventListener('click', () => {
            modelOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            selectedModelInput.value = option.dataset.model;
        });
    });

    // Preset Selection
    const presetBtns = document.querySelectorAll('.preset-btn');
    presetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const presetKey = btn.dataset.preset;
            applyPreset(presetKey);
        });
    });

    const predictionForm = document.getElementById('predictionForm');
    const submitBtn = document.getElementById('submitBtn');

    if (predictionForm) {
        predictionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await runDiagnosis();
        });
    }

    async function runDiagnosis() {
        const features = getFormValues();
        const model = selectedModelInput.value;

        if (features.length !== 24) {
            alert('Please ensure all 24 biomarkers are filled.');
            return;
        }

        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ features, model })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error');
            }

            const result = await response.json();
            
            // Wait a small bit for "thinking" feel
            setTimeout(() => {
                showResult(result);
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }, 800);

        } catch (error) {
            alert('Error: ' + error.message);
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
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

    function applyPreset(key) {
        const values = PRESETS[key];
        if (!values) return;
        
        const inputs = document.querySelectorAll('.biomarker-input');
        inputs.forEach((input, i) => {
            if (values[i] !== undefined) {
                // Staggered fill effect
                setTimeout(() => {
                    input.value = values[i];
                    input.style.borderColor = 'var(--cyan-primary)';
                    setTimeout(() => input.style.borderColor = '', 500);
                }, i * 30);
            }
        });
    }

    function showResult(result) {
        const resultsPanel = document.getElementById('resultsPanel');
        const diagnosisName = document.getElementById('diagnosisName');
        const diagnosisDescription = document.getElementById('diagnosisDescription');
        const confidencePercent = document.getElementById('confidencePercent');
        const confidenceBar = document.getElementById('confidenceBar');
        const probTable = document.getElementById('probTable');
        const clinicalAdvice = document.getElementById('clinicalAdvice');

        resultsPanel.style.display = 'block';
        resultsPanel.classList.add('visible');

        diagnosisName.textContent = result.prediction;
        diagnosisName.style.color = DISEASE_COLORS[result.prediction] || 'var(--cyan-primary)';
        diagnosisDescription.textContent = result.description;
        
        confidencePercent.textContent = `Confidence: ${result.confidence.toFixed(1)}%`;
        confidenceBar.style.width = result.confidence + '%';
        
        // Probability Table
        probTable.innerHTML = '';
        Object.entries(result.probabilities).forEach(([name, prob]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${name}</td>
                <td class="prob-bar-cell">
                    <div class="prob-bar">
                        <div class="prob-fill" style="width: ${prob}%; background: ${DISEASE_COLORS[name] || 'var(--cyan-primary)'}"></div>
                    </div>
                </td>
                <td style="text-align: right; font-family: var(--font-mono);">${prob.toFixed(1)}%</td>
            `;
            probTable.appendChild(row);
        });

        // Advice List
        clinicalAdvice.innerHTML = '';
        result.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            clinicalAdvice.appendChild(li);
        });

        // Scroll to results
        resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
