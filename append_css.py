import os

css_to_append = """
/* ────────────────────────────────────────
   DESKTOP RESPONSIVENESS OVERRIDES
   ──────────────────────────────────────── */

@media (min-width: 769px) {
  /* 1. CONTAINER WIDTH */
  .container, .page-container, main, .content-wrapper {
    max-width: 1280px;
    width: 100%;
    margin: 0 auto;
    padding: 0 60px;
    box-sizing: border-box;
  }

  /* 2. NAVBAR */
  nav, .navbar, header nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 60px;
    height: 72px;
  }
  .nav-links, .nav-menu {
    display: flex !important;
    flex-direction: row;
    gap: 36px;
    align-items: center;
  }
  .nav-links a, .nav-menu a {
    font-size: 0.95rem;
    white-space: nowrap;
  }
  .hamburger, .menu-toggle, .mobile-menu-btn, .nav-toggle {
    display: none !important;
  }

  /* 3. HERO SECTION */
  .hero, .hero-section {
    padding: 120px 60px 80px;
    text-align: center;
  }
  .hero h1, .hero-title {
    font-size: clamp(3rem, 6vw, 5.5rem);
    max-width: 900px;
    margin: 0 auto 24px;
    line-height: 1.05;
  }
  .hero p, .hero-subtitle {
    font-size: clamp(1rem, 1.5vw, 1.2rem);
    max-width: 680px;
    margin: 0 auto 40px;
  }
  .hero-buttons, .cta-buttons {
    display: flex;
    flex-direction: row;
    gap: 16px;
    justify-content: center;
  }

  /* 4. STATS ROW */
  .stats-grid, .stats-row, .hero-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 32px;
    max-width: 900px;
    margin: 60px auto;
    text-align: center;
  }
  .stat-item .stat-number {
    font-size: clamp(2.5rem, 4vw, 3.5rem);
  }

  /* 5. RADAR / CIRCULAR CHART */
  .radar-chart, .chart-wrapper, .accuracy-chart {
    width: 320px;
    height: 320px;
    margin: 0 auto;
    overflow: visible;
    position: relative;
  }
  .accuracy-badge, .chart-badge {
    position: absolute;
    right: -20px;
    top: 50%;
    transform: translateY(-50%);
    white-space: nowrap;
  }

  /* 6. INTELLIGENT WORKFLOW STEPS */
  .workflow-grid, .steps-grid, .process-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 32px;
    align-items: start;
  }
  .workflow-step, .step-card {
    padding: 40px 32px;
  }
  .step-connector, .workflow-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* 7. CONDITION CARDS */
  .conditions-grid, .capabilities-grid, .disease-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
  }
  .condition-card, .disease-card {
    padding: 36px 28px;
  }

  /* 8. PERFORMANCE BARS SECTION */
  .performance-section, .benchmarks-section, .models-preview-inner {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 64px;
    align-items: center;
    max-width: 1100px;
    margin: 0 auto;
    padding: 80px 60px;
  }
  .performance-bars, .bar-chart, .preview-bars {
    width: 100%;
  }
  .bar-item, .bar-row {
    margin-bottom: 20px;
  }
  .bar-label, .bar-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 0.95rem;
  }
  .bar-track, .bar-bg {
    height: 8px;
    border-radius: 999px;
    background: rgba(255,255,255,0.1);
    overflow: hidden;
  }
  .bar-fill {
    height: 100%;
    border-radius: 999px;
    background: #A8E63D;
    transform-origin: left;
  }

  /* 9. CTA BANNER */
  .cta-section, .cta-banner, .cta-inner {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 48px;
    max-width: 1100px;
    margin: 80px auto;
    padding: 60px 64px;
    border-radius: 24px;
  }
  .cta-text {
    text-align: left;
  }
  .cta-text h2 {
    font-size: clamp(1.8rem, 3vw, 2.8rem);
  }
  .cta-shield-icon, .cta-illustration {
    width: 120px;
    height: 120px;
    flex-shrink: 0;
  }

  /* 10. PAGE LAYOUT DIAGNOSE */
  .diagnose-layout, .predict-wrapper, .diagnose-grid, .predict-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 48px;
    align-items: start;
    max-width: 1280px;
    margin: 0 auto;
    padding: 60px 60px;
  }

  /* 11. CLASSIFIER SELECTOR */
  .classifier-grid, .model-selector {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  .classifier-card, .model-card, .mcard {
    padding: 20px;
    cursor: pointer;
    border-radius: 12px;
  }

  /* 12. QUICK FILL PRESETS */
  .presets-row, .quick-fill, .preset-buttons {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 12px;
  }
  .preset-btn, .pbtn {
    white-space: nowrap;
    padding: 10px 24px;
    border-radius: 999px;
  }

  /* 13. CLINICAL MARKERS FORM */
  .markers-grid, .biomarker-grid, .form-grid, .input-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
  .form-group, .marker-field, .bm-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .form-group label, .bm-lbl {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.7);
  }
  .form-group input, .bm-input {
    padding: 12px 16px;
    border-radius: 8px;
    width: 100%;
    box-sizing: border-box;
  }
  .run-btn, .submit-btn, .btn-pred {
    width: 100%;
    padding: 18px;
    font-size: 1rem;
    border-radius: 12px;
    margin-top: 24px;
  }

  /* 14. RESULT PANEL */
  .result-panel, .analysis-box, .result-box, .res-panel {
    position: sticky;
    top: 100px;
    padding: 40px;
    border-radius: 20px;
    min-height: 400px;
    box-sizing: border-box;
  }

  /* 15. PAGE HERO RESULTS */
  .results-hero, .results-header, .results-header.pg-hdr {
    text-align: center;
    padding: 100px 60px 60px;
    max-width: 800px;
    margin: 0 auto;
  }

  /* 16. ACCURACY TABLE */
  .accuracy-table, .model-table, .metrics-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.95rem;
  }
  .accuracy-table th, .model-table th, .metrics-table th {
    padding: 14px 20px;
    text-align: left;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #A8E63D;
    border-bottom: 1px solid rgba(168,230,61,0.2);
  }
  .accuracy-table td, .model-table td, .metrics-table td {
    padding: 14px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .accuracy-table tr:hover, .metrics-table tr:hover {
    background: rgba(168,230,61,0.04);
  }

  /* 17. METRIC BENCHMARKING BARS */
  .benchmarking-grid, .metric-grid, .cm-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 48px;
    padding: 60px;
  }

  /* 18. CONFUSION MATRICES */
  .matrices-grid, .confusion-grid, .cv-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 40px;
  }
  .matrix-wrapper {
    overflow-x: auto;
  }
  .confusion-table, .cm-table {
    font-size: 0.85rem;
    border-collapse: collapse;
    width: 100%;
  }
  .confusion-table th, .confusion-table td, .cm-table th, .cm-table td {
    padding: 10px 14px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
  }
  .confusion-table .diagonal, .cm-table .diagonal {
    background: rgba(168,230,61,0.15);
    color: #A8E63D;
    font-weight: 700;
  }

  /* 19. ABOUT HERO */
  .about-hero, .about-header {
    text-align: center;
    max-width: 800px;
    margin: 0 auto;
    padding: 100px 60px 60px;
  }

  /* 20. CORE MANDATE */
  .mandate-section, .about-mandate {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 64px;
    padding: 80px 60px;
    max-width: 1100px;
    margin: 0 auto;
  }

  /* 21. SYSTEM ARCHITECTURE STEPS */
  .architecture-grid, .arch-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
    padding: 0 60px;
  }
  .arch-step, .arch-card {
    padding: 32px 24px;
  }

  /* 22. DETECTABLE CONDITIONS TABLE */
  .conditions-table {
    width: 100%;
    border-collapse: collapse;
  }
  .conditions-table th {
    padding: 14px 20px;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #A8E63D;
    border-bottom: 1px solid rgba(168,230,61,0.2);
  }
  .conditions-table td {
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    font-size: 0.9rem;
  }

  /* 23. DEVELOPMENT INFRASTRUCTURE SECTION */
  .infra-grid, .tech-stack-grid, .infrastructure-grid, .stack-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 32px;
    padding: 0 60px;
    max-width: 1100px;
    margin: 0 auto;
  }
  .infra-item, .tech-item {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 32px;
    border-radius: 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    transition: transform 0.3s ease, border-color 0.3s ease;
  }
  .infra-item:hover, .tech-item:hover {
    transform: translateY(-6px);
    border-color: rgba(168,230,61,0.4);
  }

  /* 24. ETHICS / WARNING CARDS */
  .ethics-grid, .warning-grid, .eth-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    padding: 0 60px;
  }

  /* 25. RESEARCHER PROFILE CARD */
  .researcher-card, .about-researcher {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 40px;
    align-items: center;
    max-width: 900px;
    margin: 60px auto;
    padding: 48px;
    border-radius: 20px;
  }

  /* 26. FOOTER */
  footer, .site-footer {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
    padding: 60px;
    gap: 48px;
  }
  .footer-brand {
    max-width: 320px;
  }
  .footer-copy, .footer-bottom {
    text-align: right;
    font-size: 0.8rem;
    color: rgba(255,255,255,0.4);
  }
}
"""

with open("app/static/css/main.css", "a") as f:
    f.write(css_to_append)
