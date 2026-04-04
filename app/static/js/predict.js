// SmartHealth AI - Diagnosis Page Logic
// Author: Enock Queenson Eduafo | Student ID: 11014444
// University of Ghana - Department of Computer Science
// Information Technology | 2026

const FEATURES = [
  'Glucose', 'Cholesterol', 'Hemoglobin', 'Platelets', 'White Blood Cells',
  'Red Blood Cells', 'Hematocrit', 'Mean Corpuscular Volume',
  'Mean Corpuscular Hemoglobin', 'Mean Corpuscular Hemoglobin Concentration',
  'Insulin', 'BMI', 'Systolic Blood Pressure', 'Diastolic Blood Pressure',
  'Triglycerides', 'HbA1c', 'LDL Cholesterol', 'HDL Cholesterol',
  'ALT', 'AST', 'Heart Rate', 'Creatinine', 'Troponin', 'C-reactive Protein'
];

const PRESETS = {
  healthy: {
    'Glucose': 0.74, 'Cholesterol': 0.65, 'Hemoglobin': 0.71, 'Platelets': 0.87,
    'White Blood Cells': 0.69, 'Red Blood Cells': 0.53, 'Hematocrit': 0.29,
    'Mean Corpuscular Volume': 0.63, 'Mean Corpuscular Hemoglobin': 0.00,
    'Mean Corpuscular Hemoglobin Concentration': 0.80, 'Insulin': 0.03,
    'BMI': 0.07, 'Systolic Blood Pressure': 0.19, 'Diastolic Blood Pressure': 0.07,
    'Triglycerides': 0.65, 'HbA1c': 0.50, 'LDL Cholesterol': 0.22,
    'HDL Cholesterol': 0.51, 'ALT': 0.06, 'AST': 0.61, 'Heart Rate': 0.94,
    'Creatinine': 0.10, 'Troponin': 0.47, 'C-reactive Protein': 0.77
  },
  diabetes: {
    'Glucose': 0.90, 'Cholesterol': 0.72, 'Hemoglobin': 0.45, 'Platelets': 0.55,
    'White Blood Cells': 0.60, 'Red Blood Cells': 0.48, 'Hematocrit': 0.38,
    'Mean Corpuscular Volume': 0.50, 'Mean Corpuscular Hemoglobin': 0.35,
    'Mean Corpuscular Hemoglobin Concentration': 0.42, 'Insulin': 0.88,
    'BMI': 0.82, 'Systolic Blood Pressure': 0.68, 'Diastolic Blood Pressure': 0.62,
    'Triglycerides': 0.78, 'HbA1c': 0.91, 'LDL Cholesterol': 0.70,
    'HDL Cholesterol': 0.22, 'ALT': 0.55, 'AST': 0.52, 'Heart Rate': 0.60,
    'Creatinine': 0.45, 'Troponin': 0.20, 'C-reactive Protein': 0.65
  },
  anemia: {
    'Glucose': 0.40, 'Cholesterol': 0.35, 'Hemoglobin': 0.12, 'Platelets': 0.45,
    'White Blood Cells': 0.38, 'Red Blood Cells': 0.18, 'Hematocrit': 0.14,
    'Mean Corpuscular Volume': 0.22, 'Mean Corpuscular Hemoglobin': 0.18,
    'Mean Corpuscular Hemoglobin Concentration': 0.20, 'Insulin': 0.30,
    'BMI': 0.25, 'Systolic Blood Pressure': 0.30, 'Diastolic Blood Pressure': 0.28,
    'Triglycerides': 0.30, 'HbA1c': 0.32, 'LDL Cholesterol': 0.28,
    'HDL Cholesterol': 0.55, 'ALT': 0.22, 'AST': 0.25, 'Heart Rate': 0.70,
    'Creatinine': 0.20, 'Troponin': 0.10, 'C-reactive Protein': 0.38
  },
  heart: {
    'Glucose': 0.60, 'Cholesterol': 0.88, 'Hemoglobin': 0.55, 'Platelets': 0.60,
    'White Blood Cells': 0.58, 'Red Blood Cells': 0.50, 'Hematocrit': 0.48,
    'Mean Corpuscular Volume': 0.55, 'Mean Corpuscular Hemoglobin': 0.52,
    'Mean Corpuscular Hemoglobin Concentration': 0.58, 'Insulin': 0.45,
    'BMI': 0.72, 'Systolic Blood Pressure': 0.88, 'Diastolic Blood Pressure': 0.82,
    'Triglycerides': 0.80, 'HbA1c': 0.60, 'LDL Cholesterol': 0.88,
    'HDL Cholesterol': 0.18, 'ALT': 0.40, 'AST': 0.42, 'Heart Rate': 0.85,
    'Creatinine': 0.55, 'Troponin': 0.92, 'C-reactive Protein': 0.80
  },
  thalassemia: {
    'Glucose': 0.45, 'Cholesterol': 0.40, 'Hemoglobin': 0.25, 'Platelets': 0.50,
    'White Blood Cells': 0.42, 'Red Blood Cells': 0.65, 'Hematocrit': 0.30,
    'Mean Corpuscular Volume': 0.15, 'Mean Corpuscular Hemoglobin': 0.12,
    'Mean Corpuscular Hemoglobin Concentration': 0.18, 'Insulin': 0.28,
    'BMI': 0.30, 'Systolic Blood Pressure': 0.28, 'Diastolic Blood Pressure': 0.25,
    'Triglycerides': 0.32, 'HbA1c': 0.30, 'LDL Cholesterol': 0.25,
    'HDL Cholesterol': 0.48, 'ALT': 0.28, 'AST': 0.30, 'Heart Rate': 0.65,
    'Creatinine': 0.22, 'Troponin': 0.08, 'C-reactive Protein': 0.35
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

document.querySelectorAll('.model-radio').forEach(radio => {
  radio.addEventListener('click', () => {
    document.querySelectorAll('.model-radio').forEach(r => r.classList.remove('active'));
    radio.classList.add('active');
    const inp = radio.querySelector('input');
    if (inp) inp.checked = true;
  });
});

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const presetKey = btn.dataset.preset;
    applyPresetCascade(presetKey);
  });
});

// ── CASCADE FILL ANIMATION ────────────────────────────
function applyPresetCascade(key) {
    const preset = PRESETS[key];
    const inputs = document.querySelectorAll('.biomarker-input');
    inputs.forEach((input, i) => {
        const feat = input.dataset.feature;
        if (preset[feat] !== undefined) {
            setTimeout(() => {
                input.value = preset[feat].toFixed(4);
                const wrap = input.closest('.input-field-wrap');
                if (wrap) {
                    wrap.classList.add('highlight');
                    setTimeout(() => wrap.classList.remove('highlight'), 300);
                }
                checkFormFilled();
            }, i * 30);
        }
    });
}

function checkFormFilled() {
    let allFilled = true;
    document.querySelectorAll('.biomarker-input').forEach(inp => {
        if (!inp.value) allFilled = false;
    });
    const btn = document.getElementById('predictBtn');
    if (allFilled) {
        btn.classList.add('btn-pulse');
    } else {
        btn.classList.remove('btn-pulse');
    }
}

document.querySelectorAll('.biomarker-input').forEach(inp => {
    inp.addEventListener('input', checkFormFilled);
});

async function runDiagnosis() {
  const model = document.querySelector('.model-radio.active').dataset.model;
  const features = {};
  let valid = true;
  document.querySelectorAll('.biomarker-input').forEach(inp => {
    const val = parseFloat(inp.value);
    if (isNaN(val) || val < 0 || val > 1) {
      inp.classList.add('invalid');
      valid = false;
    } else {
      inp.classList.remove('invalid');
      features[inp.dataset.feature] = val;
    }
  });

  if (!valid) {
    alert('Please fill all fields with values between 0.0000 and 1.0000.');
    return;
  }

  const resultPanel = document.getElementById('resultPanel');
  const emptyState = document.getElementById('resultEmpty');
  const loadingState = document.getElementById('resultLoading');
  const resultContent = document.getElementById('resultContent');

  emptyState.style.display = 'none';
  resultContent.style.display = 'none';
  loadingState.style.display = 'flex';
  resultPanel.classList.add('loading');

  try {
    const resp = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, features })
    });
    const data = await resp.json();
    
    // Simulate thinking for a bit for better movie-like experience
    await new Promise(r => setTimeout(r, 1500));
    
    if (data.error) throw new Error(data.error);

    displayResults(data);
  } catch (err) {
    alert(err.message || 'Network error.');
    loadingState.style.display = 'none';
    emptyState.style.display = 'flex';
    resultPanel.classList.remove('loading');
  }
}

function displayResults(data) {
  const loadingState = document.getElementById('resultLoading');
  const resultContent = document.getElementById('resultContent');
  const resultPanel = document.getElementById('resultPanel');
  
  loadingState.style.display = 'none';
  resultPanel.classList.remove('loading');
  resultContent.style.display = 'block';

  // ── Result Appearance Animation ───────────────────
  resultContent.style.opacity = '0';
  resultContent.style.transform = 'translateX(30px)';
  requestAnimationFrame(() => {
      resultContent.style.transition = 'all 0.6s ease-out';
      resultContent.style.opacity = '1';
      resultContent.style.transform = 'translateX(0)';
  });

  const color = data.color || DISEASE_COLORS[data.prediction] || '#C5E710';
  document.getElementById('resultDot').style.background = color;
  
  // Confidence count up
  const confEl = document.getElementById('confidenceBadge');
  confEl.innerText = '0% Confidence';
  if (data.confidence) {
      animateCountUp(confEl, data.confidence, '% Confidence');
  }

  const card = document.getElementById('resultDiseaseCard');
  card.style.borderColor = color + '40';
  card.style.background = color + '10';

  // Typewriter/Flicker effect for Disease Name
  const nameEl = document.getElementById('rdiseaseName');
  nameEl.innerText = '';
  nameEl.style.color = color;
  typeWriter(nameEl, data.prediction);

  document.getElementById('rdiseaseDesc').innerText = data.description;
  
  // Probability bars with stagger
  const probBars = document.getElementById('probBars');
  probBars.innerHTML = '';
  if (data.probabilities) {
    const sorted = Object.entries(data.probabilities).sort((a,b) => b[1]-a[1]);
    sorted.forEach(([label, pct], i) => {
      const row = document.createElement('div');
      row.className = 'prob-row';
      row.style.opacity = '0';
      row.style.transform = 'translateX(-10px)';
      row.innerHTML = `
        <span class="prob-name">${label}</span>
        <div class="prob-track"><div class="prob-fill" style="width:0; background:${DISEASE_COLORS[label] || '#8E9630'};"></div></div>
        <span class="prob-pct">${pct.toFixed(1)}%</span>
      `;
      probBars.appendChild(row);
      setTimeout(() => {
          row.style.transition = 'all 0.4s ease';
          row.style.opacity = '1';
          row.style.transform = 'translateX(0)';
          row.querySelector('.prob-fill').style.width = pct + '%';
      }, 300 + (i * 100));
    });
  }

  // Recommendations dropping in one by one
  const recoList = document.getElementById('recoList');
  recoList.innerHTML = '';
  (data.recommendations || []).forEach((r, i) => {
    const li = document.createElement('li');
    li.innerText = r;
    li.style.opacity = '0';
    li.style.transform = 'translateY(10px)';
    recoList.appendChild(li);
    setTimeout(() => {
        li.style.transition = 'all 0.3s ease';
        li.style.opacity = '1';
        li.style.transform = 'translateY(0)';
    }, 800 + (i * 150));
  });
}

function animateCountUp(el, target, suffix) {
    let start = 0;
    const duration = 1200;
    const startTime = performance.now();
    function update(t) {
        const progress = Math.min((t - startTime) / duration, 1);
        el.innerText = (progress * target).toFixed(1) + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function typeWriter(el, text) {
    let i = 0;
    function next() {
        if (i < text.length) {
            el.innerHTML += text.charAt(i);
            i++;
            setTimeout(next, 50);
        }
    }
    next();
}

document.getElementById('predictBtn').addEventListener('click', runDiagnosis);
document.getElementById('resetBtn').addEventListener('click', () => {
  document.querySelectorAll('.biomarker-input').forEach(inp => inp.value = '');
  document.getElementById('resultContent').style.display = 'none';
  document.getElementById('resultEmpty').style.display = 'flex';
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  checkFormFilled();
});
