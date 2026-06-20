/**
 * Smart Health Sync — Portal Dashboard JavaScript
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("dashboardSidebar");
    if (toggle && sidebar) {
        toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    }
});

async function viewRecord(id, openPrint) {
    const modal = document.getElementById("recordModal");
    const body = document.getElementById("recordModalBody");
    if (!modal || !body) return;

    body.innerHTML = '<p style="color:var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin"></i> Loading…</p>';
    modal.style.display = "flex";

    // Set modal width based on role
    const contentWrap = modal.querySelector(".record-modal-content");
    if (contentWrap) {
        if (window.USER_ROLE === "patient") {
            contentWrap.classList.add("modal-wide");
        } else {
            contentWrap.classList.remove("modal-wide");
        }
    }

    try {
        const res = await fetch("/api/history/" + id);
        const data = await res.json();
        if (!res.ok) {
            body.innerHTML = '<p class="text-danger">' + (data.error || "Failed to load record.") + '</p>';
            return;
        }
        const rec = data.record;
        const result = rec.result || {};
        const exps = result.explanations || [];
        const recs = result.recommendations || [];

        // Clean grid of Biomarkers
        let biomHtml = '<div class="portal-section-title mt-3"><i class="fa-solid fa-flask"></i> Biomarkers</div><div class="biomarkers-grid">';
        for (const [k, v] of Object.entries(rec.biomarkers || {})) {
            biomHtml += `
                <div class="biomarker-item">
                    <div class="biomarker-name">${k}</div>
                    <div class="biomarker-val">${typeof v === 'number' ? v.toFixed(2) : v}</div>
                </div>
            `;
        }
        biomHtml += '</div>';

        if (window.USER_ROLE === "patient") {
            // Patient view: Left 3/4 details, Right 1/4 chat (with no model info)
            let leftHtml = `
                <div class="portal-section-title"><i class="fa-solid fa-file-medical"></i> Medical Report</div>
                <div class="result-meta-row mb-3">
                    <div>
                        <div class="confidence-value-large">${rec.prediction}</div>
                        <div class="confidence-label-small">Verdict / Condition</div>
                    </div>
                </div>
                <p style="color:var(--text-secondary);font-size:0.9rem;">${result.description || ""}</p>
                
                ${biomHtml}

                <div class="fi-title mt-4"><i class="fa-solid fa-user-doctor"></i> Doctor's Verdict & Remarks</div>
                <p style="color:var(--text-primary);font-size:0.95rem;font-style:italic;background:rgba(255,255,255,0.02);padding:12px;border-left:3px solid var(--cyan-primary);border-radius:var(--radius-sm);">${rec.doctor_remarks || "No remarks provided by doctor."}</p>
                
                <div class="result-disclaimer mt-3">
                    <div class="result-disclaimer-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <div><strong>Patient Disclaimer</strong> — This is an informational prototype. Always verify your results and consult with your physician regarding your clinical diagnosis.</div>
                </div>
                <button class="print-result-btn mt-3" onclick="printRecordReport()"><i class="fa-solid fa-print"></i> Print Report</button>
            `;

            let rightHtml = `
                <div class="modal-right-chat">
                    <div class="portal-section-title"><i class="fa-solid fa-brain"></i> AI Explainer</div>
                    <p style="color:var(--text-muted);font-size:0.75rem;margin-bottom:10px;">Ask anything about your biomarker scores or prediction context.</p>
                    <div class="ai-chat-box">
                        <div id="aiChatHistory" class="ai-chat-history">
                            <div style="color:var(--text-secondary);"><span style="color:var(--cyan-primary);font-weight:600;">AI:</span> Hello! I can help explain this diagnosis report. Ask me anything about your biomarkers or results.</div>
                        </div>
                        <div style="display:flex; gap:8px; margin-top:8px;">
                            <input type="text" id="aiChatInput" class="auth-input" style="padding:8px;" placeholder="Ask AI a question..." onkeydown="if(event.key === 'Enter') sendChatMessage(${rec.id})">
                            <button class="btn-action-verify btn-approve" style="padding:8px 16px; border-radius:var(--radius-sm);" onclick="sendChatMessage(${rec.id})">Ask</button>
                        </div>
                    </div>
                </div>
            `;

            body.innerHTML = `
                <div class="modal-split-container">
                    <div class="modal-left-details">${leftHtml}</div>
                    ${rightHtml}
                </div>
            `;
        } else if (window.USER_ROLE === "doctor" && rec.status === "draft") {
            // Doctor review and approve flow with all 4 model predictions compared
            let draftHtml = `
                <div class="portal-section-title"><i class="fa-solid fa-file-medical"></i> Review Diagnosis Draft</div>
                <p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:15px;">Compare predictions from all four classifiers, select the final model, and submit clinical remarks to sign off.</p>
                
                ${biomHtml}

                <div class="fi-title mt-4"><i class="fa-solid fa-chart-bar"></i> Multi-Model Classification Comparison</div>
                <div id="modelPreviewArea">
                    <p style="color:var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin"></i> Running models for comparative preview...</p>
                </div>

                <div class="fi-title mt-4"><i class="fa-solid fa-signature"></i> Final Verdict & Remarks</div>
                <div class="auth-form-group">
                    <label class="auth-label">Choose Approved Model</label>
                    <select id="modalSelectModel" class="auth-input">
                        <option value="random_forest">Random Forest (Accuracy: ~95%)</option>
                        <option value="svm">Support Vector Machine (Accuracy: ~95%)</option>
                        <option value="decision_tree">Decision Tree (Accuracy: ~92%)</option>
                        <option value="logistic_regression">Logistic Regression (Accuracy: ~82%)</option>
                    </select>
                </div>
                <div class="auth-form-group mt-3">
                    <label class="auth-label">Doctor's Remarks / Prescription / Recommendation</label>
                    <textarea id="modalDoctorRemarks" class="auth-input mt-1" rows="4" style="resize:vertical;" placeholder="Write doctor's verdict, remarks, or advice..."></textarea>
                </div>
                <button class="auth-btn mt-3" onclick="approveRecordReport(${rec.id})"><i class="fa-solid fa-signature"></i> Finalize, Sign Off & Approve</button>
            `;
            body.innerHTML = draftHtml;

            // Fetch comparisons
            fetch(`/api/history/${rec.id}/preview-models`)
                .then(r => r.json())
                .then(data => {
                    if (data.status === "success" && data.predictions) {
                        let tableHtml = `
                            <table class="model-predictions-table">
                                <thead>
                                    <tr>
                                        <th>Classifier Model</th>
                                        <th>Prediction Verdict</th>
                                        <th>Inference Confidence</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        for (const [mKey, pred] of Object.entries(data.predictions)) {
                            const nameFormatted = mKey.replace(/_/g, ' ').toUpperCase();
                            tableHtml += `
                                <tr>
                                    <td><strong>${nameFormatted}</strong></td>
                                    <td><span style="color:var(--cyan-primary);font-weight:600;">${pred.prediction || pred.error}</span></td>
                                    <td>${pred.confidence ? pred.confidence.toFixed(1) + '%' : '—'}</td>
                                </tr>
                            `;
                        }
                        tableHtml += `
                                </tbody>
                            </table>
                        `;
                        const area = document.getElementById("modelPreviewArea");
                        if (area) area.innerHTML = tableHtml;
                    } else {
                        document.getElementById("modelPreviewArea").innerHTML = `<p class="text-danger">Failed to load comparisons.</p>`;
                    }
                })
                .catch(() => {
                    document.getElementById("modelPreviewArea").innerHTML = `<p class="text-danger">Error fetching comparative insights.</p>`;
                });
        } else {
            // Doctor or Admin Approved view (shows full technical details)
            let detailsHtml = `
                <div class="portal-section-title"><i class="fa-solid fa-file-medical"></i> Diagnosis Report</div>
                <div class="result-meta-row mb-3">
                    <div>
                        <div class="confidence-value-large">${rec.prediction}</div>
                        <div class="confidence-label-small">Predicted Condition</div>
                    </div>
                    <div>
                        <div class="confidence-value-large">${(rec.confidence || 0).toFixed(1)}%</div>
                        <div class="confidence-label-small">Confidence Score</div>
                    </div>
                </div>
                
                ${biomHtml}

                <div class="fi-title mt-4"><i class="fa-solid fa-user-doctor"></i> Approved Doctor Remarks</div>
                <p style="color:var(--text-primary);font-size:0.9rem;font-style:italic;background:rgba(255,255,255,0.02);padding:10px;border-left:3px solid var(--cyan-primary);">${rec.doctor_remarks || "No remarks provided."}</p>

                <div class="dash-status-item mt-3"><span>Date</span><span>${rec.created_at ? new Date(rec.created_at).toLocaleString() : "—"}</span></div>
                <div class="dash-status-item"><span>Status</span><span><span class="status-badge status-${rec.status}">${rec.status}</span></span></div>
                <div class="dash-status-item"><span>Model Used</span><span>${(rec.model_used || "—").replace(/_/g, ' ').toUpperCase()}</span></div>
                
                <div class="result-disclaimer mt-3">
                    <div class="result-disclaimer-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <div><strong>Research Prototype</strong> — For clinical decision support only. All outputs must be verified by a licensed practitioner.</div>
                </div>
                <button class="print-result-btn mt-3" onclick="printRecordReport()"><i class="fa-solid fa-print"></i> Print Report</button>
            `;
            body.innerHTML = detailsHtml;
        }

        window._currentRecord = rec;
        if (openPrint) setTimeout(() => printRecordReport(), 400);
    } catch (err) {
        body.innerHTML = '<p class="text-danger">Network error loading record.</p>';
    }
}

async function approveRecordReport(id) {
    const textarea = document.getElementById("modalDoctorRemarks");
    const remarks = textarea ? textarea.value.trim() : "";
    const selectModel = document.getElementById("modalSelectModel");
    const model = selectModel ? selectModel.value : "random_forest";
    
    try {
        const res = await fetch(`/api/history/${id}/approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ remarks, model })
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || "Failed to approve record.");
            return;
        }
        alert(data.message);
        location.reload();
    } catch (err) {
        alert("Network error approving record.");
    }
}

async function sendChatMessage(id) {
    const input = document.getElementById("aiChatInput");
    const history = document.getElementById("aiChatHistory");
    if (!input || !history || !input.value.trim()) return;
    
    const query = input.value.trim();
    input.value = "";
    
    // Append user message
    const userDiv = document.createElement("div");
    userDiv.innerHTML = `<span style="color:var(--purple-neural);font-weight:600;">You:</span> ${query}`;
    history.appendChild(userDiv);
    history.scrollTop = history.scrollHeight;
    
    // Append loading spinner
    const loadingDiv = document.createElement("div");
    loadingDiv.id = "aiChatLoading";
    loadingDiv.innerHTML = `<span style="color:var(--cyan-primary);font-weight:600;">AI:</span> <i class="fa-solid fa-spinner fa-spin"></i> Analyzing context...`;
    history.appendChild(loadingDiv);
    history.scrollTop = history.scrollHeight;
    
    try {
        const res = await fetch(`/api/history/${id}/explain`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: query })
        });
        const data = await res.json();
        
        const loader = document.getElementById("aiChatLoading");
        if (loader) loader.remove();
        
        const aiDiv = document.createElement("div");
        aiDiv.innerHTML = `<span style="color:var(--cyan-primary);font-weight:600;">AI:</span> ${data.reply || "Unable to retrieve insights."}`;
        history.appendChild(aiDiv);
        history.scrollTop = history.scrollHeight;
    } catch (err) {
        const loader = document.getElementById("aiChatLoading");
        if (loader) loader.remove();
        
        const errorDiv = document.createElement("div");
        errorDiv.innerHTML = `<span style="color:var(--red-critical);font-weight:600;">System:</span> Network error. Please try again.`;
        history.appendChild(errorDiv);
        history.scrollTop = history.scrollHeight;
    }
}

function closeRecordModal() {
    const modal = document.getElementById("recordModal");
    if (modal) modal.style.display = "none";
}

function printRecordReport() {
    const rec = window._currentRecord;
    if (!rec) return;
    const result = rec.result || {};
    const exps = (result.explanations || []).map(e => `<li>${e}</li>`).join("");
    const recs = (result.recommendations || []).map(r => `<li>${r}</li>`).join("");
    const remarks = rec.doctor_remarks ? `<p><b>Doctor's Remarks:</b> <i>"${rec.doctor_remarks}"</i></p>` : "";

    const win = window.open("", "_blank");
    win.document.write(`
        <!DOCTYPE html><html><head><title>Diagnosis Report</title>
        <style>body{font-family:Georgia,serif;padding:36px;color:#111;}h1{font-size:22pt;}h2{font-size:11pt;text-transform:uppercase;color:#555;border-bottom:1px solid #ddd;padding-bottom:4px;}ul{line-height:1.7;} .conf{font-size:14pt;margin:12px 0;} .disc{background:#fff8e1;border:1px solid #f9a825;padding:10px;font-size:9pt;margin-top:20px;}</style>
        </head><body>
        <h1><i>Smart Health Sync</i> — Diagnosis Report</h1>
        <p>Ref: SHS-${rec.id} · ${rec.created_at ? new Date(rec.created_at).toLocaleString() : ""}</p>
        <h1 style="color:#2e7d32;">${rec.prediction}</h1>
        <p class="conf">Confidence Score: ${(rec.confidence || 0).toFixed(1)}%</p>
        <p>${result.description || ""}</p>
        ${remarks}
        ${exps ? `<h2>Why This Prediction Was Made</h2><ul>${exps}</ul>` : ""}
        ${recs ? `<h2>Clinical Recommendations</h2><ul>${recs}</ul>` : ""}
        <div class="disc"><strong>Disclaimer:</strong> Academic research prototype — not for unsupervised clinical use.</div>
        </body></html>
    `);
    win.document.close();
    win.print();
}
