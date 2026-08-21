/**
 * Smart Health Sync v2.0 — Clinical Workflow & Diagnosis Engine
 * Author: Enock Queenson Eduafo | University of Ghana 2026
 */

"use strict";

let currentStep = 1;
let currentCaseId = null;
let recordedSymptoms = [];
let preliminaryCandidates = [];
let selectedInvestigations = [];
let biomarkerValues = {};
let latestPrediction = null;

document.addEventListener("DOMContentLoaded", () => {
    initStepNavigation();
    initPatientSelector();
    initSymptomSearch();
    resumeExistingCase();

    const btn1 = document.getElementById("btnStep1Next");
    if (btn1) {
        btn1.addEventListener("click", (e) => {
            e.preventDefault();
            proceedToStep2();
        });
    }
});

// ── 1. Step Navigation & Stepper Bar ─────────────────────────────────
function navigateToStep(stepNum) {
    if (stepNum > 1 && !currentCaseId) {
        showToast("Please complete Patient Case initialization first.", "warning");
        return;
    }
    
    currentStep = stepNum;
    for (let i = 1; i <= 6; i++) {
        const container = document.getElementById(`stepContainer${i}`);
        const badge = document.getElementById(`stepBadge${i}`);
        if (container) container.style.display = (i === stepNum) ? "block" : "none";
        if (badge) {
            if (i === stepNum) {
                badge.style.borderColor = "var(--cyan-primary)";
                badge.style.background = "rgba(197, 231, 16, 0.1)";
                badge.style.color = "var(--cyan-primary)";
            } else if (i < stepNum) {
                badge.style.borderColor = "rgba(197, 231, 16, 0.4)";
                badge.style.background = "rgba(197, 231, 16, 0.03)";
                badge.style.color = "var(--text-primary)";
            } else {
                badge.style.borderColor = "rgba(255, 255, 255, 0.1)";
                badge.style.background = "transparent";
                badge.style.color = "var(--text-secondary)";
            }
        }
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function initStepNavigation() {
    navigateToStep(1);
}

// ── 2. Patient Case Selection (Dedicated API: POST /api/cases) ────────
function initPatientSelector() {
    // UI selection handler
}

async function initOrCreateCase() {
    if (currentCaseId) return currentCaseId;
    
    const select = document.getElementById("linkPatientSelect");
    let patientId = null;
    let patUuid = null;

    if (select && select.value) {
        patientId = parseInt(select.value, 10);
        if (isNaN(patientId)) patientId = null;
        const opt = select.options[select.selectedIndex];
        if (opt) {
            patUuid = (opt.dataset && opt.dataset.uuid) || opt.getAttribute("data-uuid") || null;
        }
    }
    
    const response = await fetch("/api/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            patient_id: patientId,
            patient_reference: patUuid
        })
    });
    
    const data = await response.json();
    if (!response.ok || data.status !== "success") {
        console.error("[SmartHealth] /api/cases failed:", response.status, data);
        throw new Error(data.error || `Unable to create patient case (HTTP ${response.status})`);
    }
    
    currentCaseId = data.case.id;
    const hidden = document.getElementById("currentCaseId");
    if (hidden) hidden.value = currentCaseId;
    
    logger(`Case initialized ID: ${currentCaseId}`);
    return currentCaseId;
}

async function proceedToStep2() {
    const btn = document.getElementById("btnStep1Next");
    if (btn) { btn.disabled = true; btn.textContent = "Saving Case..."; }
    try {
        const caseId = await initOrCreateCase();
        if (caseId) {
            navigateToStep(2);
        } else {
            showToast("Unable to initialize case. Please try again.", "error");
        }
    } catch (error) {
        console.error("[SmartHealth] Case creation failed:", error);
        showToast(error.message || "Unable to save case.", "error");
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Save & Continue to Symptoms →"; }
    }
}

// Bind to window for inline onclick handlers
window.navigateToStep = navigateToStep;
window.proceedToStep2 = proceedToStep2;
window.initOrCreateCase = initOrCreateCase;

async function resumeExistingCase() {
    const hidden = document.getElementById("resumeCaseId");
    const caseId = hidden && hidden.value ? parseInt(hidden.value, 10) : null;
    if (!caseId) return;

    try {
        const res = await fetch(`/api/cases/${caseId}`);
        const data = await res.json();
        if (!res.ok || !data.case) {
            showToast("Could not load that case — it may no longer exist.", "error");
            return;
        }

        currentCaseId = caseId;
        const caseHidden = document.getElementById("currentCaseId");
        if (caseHidden) caseHidden.value = caseId;

        const stageMap = {
            "Draft Case": 1,
            "Symptoms Captured": 2,
            "Pre-Assessment Ready": 3,
            "Investigations Selected": 4,
            "Results Available": 5,
            "Prediction Available": 6,
            "Case Reviewed": 6,
            "Reported/Archived": 6
        };

        const targetStep = stageMap[data.case.case_status] || 2;
        navigateToStep(targetStep);
        showToast(`Resumed case ${data.case.patient_reference || '#' + caseId}.`, "info");
    } catch (err) {
        console.error("[SmartHealth] Failed to resume case:", err);
        showToast("Could not resume the case. Starting fresh.", "warning");
    }
}

// ── 3. Symptom Capture & Searchable Multi-Select ─────────────────────
function initSymptomSearch() {
    const input = document.getElementById("symptomSearchInput");
    const menu = document.getElementById("symptomDropdownMenu");
    
    if (!input || !menu) return;
    
    let debounceTimer;
    input.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        const q = input.value.trim();
        if (q.length < 1) {
            menu.style.display = "none";
            return;
        }
        
        debounceTimer = setTimeout(() => {
            fetch(`/api/symptoms?query=${encodeURIComponent(q)}`)
            .then(res => res.json())
            .then(data => {
                menu.innerHTML = "";
                if (data.symptoms && data.symptoms.length > 0) {
                    menu.style.display = "block";
                    data.symptoms.forEach(sym => {
                        const item = document.createElement("div");
                        item.className = "dropdown-item p-2";
                        item.style.cursor = "pointer";
                        item.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
                        item.innerHTML = `<strong>${escapeHtml(sym.display_name)}</strong> <span style="font-size:0.75rem; color:var(--text-secondary);">(${escapeHtml(sym.category || 'General')})</span>`;
                        item.onclick = () => {
                            addSymptomChip(sym.display_name, sym.id, "selected", "Moderate", 3, "days");
                            input.value = "";
                            menu.style.display = "none";
                        };
                        menu.appendChild(item);
                    });
                } else {
                    menu.style.display = "block";
                    menu.innerHTML = `<div class="p-2 text-muted" style="font-size:0.85rem;">No catalog match for "${escapeHtml(q)}". <a href="#" onclick="addCustomSymptomFromQuery('${escapeHtml(q)}'); return false;" style="color:var(--cyan-primary);">Add as custom symptom</a></div>`;
                }
            })
            .catch(err => console.error("Error fetching symptoms:", err));
        }, 250);
    });

    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !menu.contains(e.target)) {
            menu.style.display = "none";
        }
    });
}

function addSymptomChip(name, catalogId = null, source = "selected", severity = "Moderate", durVal = 3, durUnit = "days") {
    // Fixed s.display_name.lower bug -> String(s.display_name || "").toLowerCase()
    if (recordedSymptoms.some(s => String(s.display_name || "").toLowerCase() === name.toLowerCase())) {
        showToast(`Symptom "${name}" is already added.`, "info");
        return;
    }
    
    const symObj = {
        standard_symptom_id: catalogId,
        display_name: name,
        raw_text: name,
        source: source,
        severity: severity,
        duration_value: durVal,
        duration_unit: durUnit,
        notes: ""
    };
    recordedSymptoms.push(symObj);
    renderSymptomChips();
}

function addCustomSymptom() {
    const txtInput = document.getElementById("customSymptomText");
    const sevSelect = document.getElementById("customSymptomSeverity");
    const durInput = document.getElementById("customSymptomDurationVal");
    const durUnitSelect = document.getElementById("customSymptomDurationUnit");
    
    const text = txtInput ? txtInput.value.trim() : "";
    if (!text) {
        showToast("Please enter symptom description.", "warning");
        return;
    }
    
    addSymptomChip(
        text,
        null,
        "typed",
        sevSelect ? sevSelect.value : "Moderate",
        durInput ? parseInt(durInput.value, 10) || 3 : 3,
        durUnitSelect ? durUnitSelect.value : "days"
    );
    
    if (txtInput) txtInput.value = "";
}

function addCustomSymptomFromQuery(query) {
    addSymptomChip(query, null, "typed", "Moderate", 3, "days");
    const input = document.getElementById("symptomSearchInput");
    const menu = document.getElementById("symptomDropdownMenu");
    if (input) input.value = "";
    if (menu) menu.style.display = "none";
}

function removeSymptomChip(index) {
    recordedSymptoms.splice(index, 1);
    renderSymptomChips();
}

function renderSymptomChips() {
    const container = document.getElementById("symptomChipsContainer");
    const badge = document.getElementById("symptomCountBadge");
    
    if (!container) return;
    if (badge) badge.textContent = recordedSymptoms.length;
    
    container.innerHTML = "";
    if (recordedSymptoms.length === 0) {
        container.innerHTML = '<span class="text-muted" style="font-size:0.85rem; font-style:italic;">No symptoms added yet. Use the search bar above or custom entry below.</span>';
        return;
    }
    
    recordedSymptoms.forEach((sym, idx) => {
        const chip = document.createElement("div");
        chip.style.cssText = "display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:20px; background:rgba(197,231,16,0.12); border:1px solid rgba(197,231,16,0.3); color:var(--text-primary); font-size:0.85rem;";
        
        let sevColor = "var(--amber-warn)";
        if (sym.severity === "Severe") sevColor = "var(--red-critical)";
        if (sym.severity === "Mild") sevColor = "var(--cyan-primary)";
        
        chip.innerHTML = `
            <span><strong>${escapeHtml(sym.display_name)}</strong></span>
            <span style="font-size:0.75rem; color:${sevColor}; border:1px solid ${sevColor}; padding:1px 6px; border-radius:10px;">${sym.severity}</span>
            <span style="font-size:0.75rem; color:var(--text-secondary);">${sym.duration_value} ${sym.duration_unit}</span>
            <i class="fa-solid fa-xmark" style="cursor:pointer; color:var(--text-secondary);" onclick="removeSymptomChip(${idx})"></i>
        `;
        container.appendChild(chip);
    });
}

async function proceedToStep3() {
    if (recordedSymptoms.length === 0) {
        showToast("Please add at least one presenting symptom before continuing.", "warning");
        return;
    }
    
    try {
        await initOrCreateCase();
        const response = await fetch(`/api/cases/${currentCaseId}/symptoms`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                replace: true,
                symptoms: recordedSymptoms
            })
        });
        
        const data = await response.json();
        if (!response.ok || data.status !== "success") {
            throw new Error(data.error || "Failed to save symptoms.");
        }
        
        runPreliminaryAssessmentBackend();
    } catch (error) {
        console.error(error);
        showToast(error.message, "error");
    }
}

// ── 4. Preliminary Assessment Engine ────────────────────────────────
function runPreliminaryAssessmentBackend() {
    navigateToStep(3);
    const container = document.getElementById("preliminaryCandidatesContainer");
    if (container) {
        container.innerHTML = `
            <div class="col-12 text-center p-4">
              <span class="btn-spinner" style="display:inline-block; width:24px; height:24px;"></span>
              <p class="text-muted mt-2">Evaluating symptom presentation and clinical rules...</p>
            </div>
        `;
    }
    
    fetch(`/api/cases/${currentCaseId}/pre-assessment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success" && data.preliminary_assessment) {
            preliminaryCandidates = data.preliminary_assessment.candidates || [];
            renderPreliminaryCandidates(preliminaryCandidates);
        } else {
            if (container) container.innerHTML = `<div class="col-12 text-danger p-3">Error running assessment: ${escapeHtml(data.error || 'Failed')}</div>`;
        }
    })
    .catch(err => console.error("Error running assessment:", err));
}

function renderPreliminaryCandidates(candidates) {
    const container = document.getElementById("preliminaryCandidatesContainer");
    if (!container) return;
    container.innerHTML = "";
    
    if (candidates.length === 0) {
        container.innerHTML = '<div class="col-12 text-muted p-3">No specific differential candidates identified from presentation.</div>';
        return;
    }
    
    candidates.forEach((cand) => {
        const col = document.createElement("div");
        col.className = "col-12 col-md-6";
        
        let badgeHtml = cand.supported_by_biomarker_model
            ? '<span class="badge" style="background:rgba(197,231,16,0.15); color:var(--cyan-primary); border:1px solid rgba(197,231,16,0.3);"><i class="fa-solid fa-circle-check"></i> Supported by Biomarker Model</span>'
            : '<span class="badge" style="background:rgba(244,223,107,0.15); color:var(--amber-warn); border:1px solid rgba(244,223,107,0.3);"><i class="fa-solid fa-triangle-exclamation"></i> No biomarker prediction model available in current system</span>';
            
        col.innerHTML = `
            <div class="portal-card h-100" style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08);">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h4 style="font-size:1.1rem; color:var(--text-primary); font-family:var(--font-display); margin:0;">
                  #${cand.rank} ${escapeHtml(cand.condition_name)}
                </h4>
                <span style="font-family:var(--font-mono); font-size:1rem; font-weight:700; color:var(--cyan-primary);">${cand.score}% score</span>
              </div>
              <div class="mb-3">${badgeHtml}</div>
              <p style="color:var(--text-secondary); font-size:0.85rem; line-height:1.6; margin:0;">
                ${escapeHtml(cand.rationale)}
              </p>
            </div>
        `;
        container.appendChild(col);
    });
}

function proceedToStep4() {
    navigateToStep(4);
    fetchInvestigationRecommendations();
}

// ── 5. Investigation Recommendation & Selection ─────────────────────
function fetchInvestigationRecommendations() {
    const container = document.getElementById("investigationsListContainer");
    if (container) {
        container.innerHTML = `
            <div class="col-12 text-center p-4">
              <span class="btn-spinner" style="display:inline-block; width:24px; height:24px;"></span>
              <p class="text-muted mt-2">Loading recommended investigation panels...</p>
            </div>
        `;
    }
    
    fetch(`/api/cases/${currentCaseId}/investigation-recommendations`)
    .then(res => res.json())
    .then(data => {
        if (data.status === "success" && data.recommendations) {
            renderInvestigationRecommendations(data.recommendations);
        } else {
            if (container) container.innerHTML = '<div class="col-12 text-danger p-3">Failed to load recommendations.</div>';
        }
    })
    .catch(err => console.error("Error fetching recommendations:", err));
}

function renderInvestigationRecommendations(recs) {
    const container = document.getElementById("investigationsListContainer");
    if (!container) return;
    container.innerHTML = "";
    
    selectedInvestigations = recs;
    
    recs.forEach((rec) => {
        const inv = rec.investigation;
        const col = document.createElement("div");
        col.className = "col-12 col-md-6";
        
        let prioColor = "var(--cyan-primary)";
        if (rec.priority === "High") prioColor = "var(--red-critical)";
        if (rec.priority === "Medium") prioColor = "var(--amber-warn)";
        
        col.innerHTML = `
            <div class="portal-card h-100" style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08);">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <label class="d-flex align-items-center gap-2" style="cursor:pointer; font-weight:600; font-size:0.95rem; color:var(--text-primary);">
                  <input type="checkbox" class="inv-checkbox" data-inv-id="${inv.id}" ${rec.doctor_selected ? 'checked' : ''} onchange="toggleInvestigationSelection(${inv.id}, this.checked)">
                  ${escapeHtml(inv.name)}
                </label>
                <span style="font-size:0.75rem; color:${prioColor}; border:1px solid ${prioColor}; padding:2px 8px; border-radius:10px;">${rec.priority} Priority</span>
              </div>
              <p style="color:var(--text-secondary); font-size:0.82rem; line-height:1.5; margin-bottom:8px;">
                ${escapeHtml(rec.reason)}
              </p>
              <div style="font-size:0.75rem; color:var(--text-muted);">Category: ${escapeHtml(inv.category)} · Biomarkers: ${inv.biomarker_keys ? inv.biomarker_keys.length : 0} markers</div>
            </div>
        `;
        container.appendChild(col);
    });
}

function toggleInvestigationSelection(invId, isSelected) {
    const found = selectedInvestigations.find(r => r.investigation_id === invId);
    if (found) {
        found.doctor_selected = isSelected;
    }
}

async function proceedToStep5() {
    const activeSelection = selectedInvestigations.filter(r => r.doctor_selected);
    if (activeSelection.length === 0) {
        showToast("Please select at least one investigation panel.", "warning");
        return;
    }
    
    try {
        const response = await fetch(`/api/cases/${currentCaseId}/investigations`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                investigations: activeSelection
            })
        });
        const data = await response.json();
        if (!response.ok || data.status !== "success") {
            throw new Error(data.error || "Failed to save selected investigations.");
        }
        
        navigateToStep(5);
        buildDynamicBiomarkerForm(activeSelection);
    } catch (error) {
        console.error(error);
        showToast(error.message, "error");
    }
}

// Real clinical reference ranges — must match backend/ml/preprocessing/normalization.py exactly
const BIOMARKER_META = {
    "Glucose": { unit: "mg/dL", min: 50, max: 300, step: 1, placeholder: "e.g. 95" },
    "Cholesterol": { unit: "mg/dL", min: 100, max: 400, step: 1, placeholder: "e.g. 180" },
    "Hemoglobin": { unit: "g/dL", min: 5, max: 25, step: 0.1, placeholder: "e.g. 14.5" },
    "Platelets": { unit: "x10\u00b3/\u00b5L", min: 50, max: 600, step: 1, placeholder: "e.g. 250" },
    "White Blood Cells": { unit: "x10\u00b3/\u00b5L", min: 1, max: 20, step: 0.1, placeholder: "e.g. 7.5" },
    "Red Blood Cells": { unit: "x10\u2076/\u00b5L", min: 2, max: 8, step: 0.1, placeholder: "e.g. 4.8" },
    "Hematocrit": { unit: "%", min: 20, max: 60, step: 0.1, placeholder: "e.g. 42" },
    "Mean Corpuscular Volume": { unit: "fL", min: 50, max: 120, step: 0.1, placeholder: "e.g. 88" },
    "Mean Corpuscular Hemoglobin": { unit: "pg", min: 15, max: 45, step: 0.1, placeholder: "e.g. 30" },
    "Mean Corpuscular Hemoglobin Concentration": { unit: "g/dL", min: 25, max: 40, step: 0.1, placeholder: "e.g. 34" },
    "Insulin": { unit: "\u00b5IU/mL", min: 1, max: 100, step: 0.1, placeholder: "e.g. 10" },
    "BMI": { unit: "kg/m\u00b2", min: 10, max: 50, step: 0.1, placeholder: "e.g. 23.5" },
    "Systolic Blood Pressure": { unit: "mmHg", min: 70, max: 220, step: 1, placeholder: "e.g. 120" },
    "Diastolic Blood Pressure": { unit: "mmHg", min: 40, max: 130, step: 1, placeholder: "e.g. 80" },
    "Triglycerides": { unit: "mg/dL", min: 30, max: 500, step: 1, placeholder: "e.g. 120" },
    "HbA1c": { unit: "%", min: 3, max: 15, step: 0.1, placeholder: "e.g. 5.4" },
    "LDL Cholesterol": { unit: "mg/dL", min: 30, max: 300, step: 1, placeholder: "e.g. 95" },
    "HDL Cholesterol": { unit: "mg/dL", min: 10, max: 100, step: 1, placeholder: "e.g. 55" },
    "ALT": { unit: "U/L", min: 0, max: 200, step: 1, placeholder: "e.g. 25" },
    "AST": { unit: "U/L", min: 0, max: 200, step: 1, placeholder: "e.g. 22" },
    "Heart Rate": { unit: "bpm", min: 30, max: 200, step: 1, placeholder: "e.g. 72" },
    "Creatinine": { unit: "mg/dL", min: 0.1, max: 10, step: 0.1, placeholder: "e.g. 0.9" },
    "Troponin": { unit: "ng/mL", min: 0, max: 2, step: 0.01, placeholder: "e.g. 0.02" },
    "C-reactive Protein": { unit: "mg/L", min: 0, max: 100, step: 0.1, placeholder: "e.g. 3" }
};

// ── 6. Dynamic Lab Results Entry Form ───────────────────────────────
function buildDynamicBiomarkerForm(activeInvestigations) {
    const container = document.getElementById("dynamicBiomarkerGroupsContainer");
    if (!container) return;
    container.innerHTML = "";
    
    const requiredKeys = new Set();
    activeInvestigations.forEach(inv => {
        const keys = inv.investigation ? inv.investigation.biomarker_keys : [];
        keys.forEach(k => requiredKeys.add(k));
    });

    if (requiredKeys.size === 0) {
        ["Glucose", "Hemoglobin", "Platelets", "White Blood Cells", "Red Blood Cells", "HbA1c", "Cholesterol"].forEach(k => requiredKeys.add(k));
    }
    
    const METABOLIC_KEYS = ["Glucose", "HbA1c", "Insulin", "BMI"];
    const CARDIOPULMONARY_KEYS = ["Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides", "Systolic Blood Pressure", "Diastolic Blood Pressure", "Heart Rate", "Troponin", "C-reactive Protein"];
    const HEMATOLOGY_KEYS = ["Hemoglobin", "Platelets", "White Blood Cells", "Red Blood Cells", "Hematocrit", "Mean Corpuscular Volume", "Mean Corpuscular Hemoglobin", "Mean Corpuscular Hemoglobin Concentration"];
    const LFT_KFT_KEYS = ["ALT", "AST", "Creatinine"];
    const TYPHOID_KEYS = ["Widal O Titer", "Widal H Titer"];

    const groups = [
        { title: "Metabolic & Glycemic Indices", keys: METABOLIC_KEYS.filter(k => requiredKeys.has(k)) },
        { title: "Cardiovascular & Inflammatory Markers", keys: CARDIOPULMONARY_KEYS.filter(k => requiredKeys.has(k)) },
        { title: "Full Blood Count (FBC / Hematology)", keys: HEMATOLOGY_KEYS.filter(k => requiredKeys.has(k)) },
        { title: "Hepatic & Renal Markers", keys: LFT_KFT_KEYS.filter(k => requiredKeys.has(k)) },
        { title: "Special Serology Titers", keys: TYPHOID_KEYS.filter(k => requiredKeys.has(k)) }
    ];

    groups.forEach(group => {
        if (group.keys.length === 0) return;
        
        const grpCard = document.createElement("div");
        grpCard.className = "portal-card mb-4";
        grpCard.style.cssText = "background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.06);";
        
        let rowHtml = `<div class="biomarker-group-title mb-3" style="color:var(--cyan-primary); font-family:var(--font-display); font-size:1rem;">${group.title}</div><div class="row g-3">`;
        
        group.keys.forEach(k => {
            const meta = BIOMARKER_META[k] || { unit: "", min: 0, max: 1000, step: 0.1, placeholder: "" };
            const currentVal = biomarkerValues[k] !== undefined ? biomarkerValues[k] : "";
            rowHtml += `
                <div class="col-12 col-sm-6 col-md-4 col-lg-3">
                  <label class="input-label" style="font-size:0.85rem; color:var(--text-primary); display:block; margin-bottom:4px;">
                    ${escapeHtml(k)}${meta.unit ? ` <span style="color:var(--text-secondary); font-size:0.75rem;">(${meta.unit})</span>` : ''}
                  </label>
                  <input type="number" step="${meta.step}" min="${meta.min}" max="${meta.max}" placeholder="${escapeHtml(meta.placeholder)}" class="biomarker-input auth-input" data-biomarker-key="${escapeHtml(k)}" value="${currentVal}">
                </div>
            `;
        });
        rowHtml += `</div>`;
        grpCard.innerHTML = rowHtml;
        container.appendChild(grpCard);
    });
}

// Fixed: Post results to actual selected investigation IDs instead of hardcoded /investigations/1/results
async function proceedToStep6() {
    const inputs = document.querySelectorAll(".biomarker-input");
    const enteredBiomarkers = {};
    
    inputs.forEach(inp => {
        const key = inp.dataset.biomarkerKey;
        if (key) {
            const val = parseFloat(inp.value);
            if (!Number.isNaN(val)) {
                enteredBiomarkers[key] = val;
                biomarkerValues[key] = val;
            }
        }
    });

    if (Object.keys(enteredBiomarkers).length === 0) {
        showToast("Please enter at least one biomarker test result.", "warning");
        return;
    }

    try {
        const activeInvestigations = selectedInvestigations.filter(item => item.doctor_selected);
        if (activeInvestigations.length === 0) {
            throw new Error("No investigation selected.");
        }

        for (const item of activeInvestigations) {
            const investigation = item.investigation;
            const allowedKeys = investigation?.biomarker_keys || [];
            const investigationResults = {};

            allowedKeys.forEach(key => {
                if (Object.prototype.hasOwnProperty.call(enteredBiomarkers, key)) {
                    investigationResults[key] = enteredBiomarkers[key];
                }
            });

            if (Object.keys(investigationResults).length === 0) {
                // If test has general biomarkers, pass entered biomarkers
                Object.assign(investigationResults, enteredBiomarkers);
            }

            const response = await fetch(
                `/api/cases/${currentCaseId}/investigations/${item.id}/results`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ results: investigationResults })
                }
            );

            const data = await response.json();
            if (!response.ok || data.status !== "success") {
                throw new Error(data.error || `Failed to save ${investigation ? investigation.name : 'investigation results'}`);
            }
        }

        navigateToStep(6);
        runBiomarkerPredictionBackend(enteredBiomarkers);
    } catch (error) {
        console.error(error);
        showToast(error.message, "error");
    }
}

// ── 7. Predicted Diagnosis, AI Summary & Report Builder ──────────────
function runBiomarkerPredictionBackend(biomarkers = null, selectedModel = "random_forest") {
    fetch(`/api/cases/${currentCaseId}/predictions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            model: selectedModel,
            features: biomarkers || biomarkerValues
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            latestPrediction = data;
            renderPredictionResults(data);
            generateWholeCaseAISummary();
        } else {
            showToast("Prediction error: " + (data.error || "Failed"), "error");
        }
    })
    .catch(err => console.error("Error running prediction:", err));
}

function switchClassifierModel(modelKey) {
    document.getElementById("selectedModel").value = modelKey;
    runBiomarkerPredictionBackend(null, modelKey);
}

function renderPredictionResults(data) {
    const diagName = document.getElementById("diagnosisName");
    const confLarge = document.getElementById("confidenceLarge");
    const confBar = document.getElementById("confidenceBar");
    const desc = document.getElementById("diagnosisDescription");
    const modelLbl = document.getElementById("modelUsedLabel");
    const probTable = document.getElementById("probTable");

    if (diagName) diagName.textContent = data.predicted_diagnosis || "Healthy";
    if (confLarge) confLarge.textContent = `${data.confidence || 0}%`;
    if (confBar) confBar.style.width = `${data.confidence || 0}%`;
    if (modelLbl) modelLbl.textContent = `Model: ${data.prediction_details?.model_used || 'random_forest'}`;
    
    if (desc) {
        desc.textContent = data.prediction_details?.description || "Algorithmic inference completed based on normalised biomarker profile.";
    }
    
    if (probTable && data.prediction_details?.probabilities) {
        probTable.innerHTML = "";
        const probs = data.prediction_details.probabilities;
        for (let cls in probs) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="padding:6px; color:var(--text-primary); font-weight:600;">${escapeHtml(cls)}</td>
                <td style="padding:6px; width:60%;">
                  <div style="background:rgba(255,255,255,0.05); height:8px; border-radius:4px; overflow:hidden;">
                    <div style="width:${probs[cls]}%; height:100%; background:var(--cyan-primary);"></div>
                  </div>
                </td>
                <td style="padding:6px; text-align:right; font-family:var(--font-mono); font-size:0.85rem; color:var(--cyan-primary);">${probs[cls]}%</td>
            `;
            probTable.appendChild(tr);
        }
    }
}

function generateWholeCaseAISummary() {
    const notesInput = document.getElementById("doctorClinicalNotes");
    
    fetch(`/api/cases/${currentCaseId}/ai-summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            doctor_notes: notesInput ? notesInput.value.trim() : ""
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success" && data.ai_summary) {
            const txt = document.getElementById("caseAISummaryText");
            if (txt) txt.value = data.ai_summary.summary_text;
        }
    })
    .catch(err => console.error("Error generating AI summary:", err));
}

function refreshAISummary() {
    generateWholeCaseAISummary();
}

function finalizeAndBuildReport() {
    const checkboxes = document.querySelectorAll(".report-sec-cb:checked");
    const selectedSections = Array.from(checkboxes).map(cb => cb.value);
    const signatureInput = document.getElementById("doctorSignatureInput");
    
    fetch(`/api/cases/${currentCaseId}/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sections: selectedSections,
            doctor_signature: signatureInput ? signatureInput.value.trim() : "Dr. Physician"
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            showToast("Report generated and case saved to history successfully!", "success");
            // Fixed query parameter name from &id= to &record_id=
            setTimeout(() => {
                window.location.href = `/portal?section=view_record&record_id=${currentCaseId}`;
            }, 1200);
        } else {
            showToast("Failed to generate report.", "error");
        }
    })
    .catch(err => console.error("Error generating report:", err));
}

// ── Helpers ─────────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function logger(msg) {
    console.log("[SmartHealth Workflow]", msg);
}

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'success'} position-fixed bottom-0 end-0 m-3 z-index-toast`;
    toast.style.cssText = "z-index: 9999; box-shadow: 0 0 20px rgba(0,0,0,0.5);";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}
