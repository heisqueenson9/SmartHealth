// SmartHealth AI - Model Results Page
// Author: Enock Queenson Eduafo | Student ID: 11014444
// University of Ghana - Department of Computer Science
// Information Technology | 2026

document.addEventListener('DOMContentLoaded', () => {
    initResults();
});

function initResults() {
    setupAccuracyChart();
    setupConfusionMatrixIntensities();
    setupCardsDeal();
    setupScrollTriggeredBars();
}

// ── ACCURACY CHART ANIMATION ────────────────────────────
function setupAccuracyChart() {
    const chart = document.querySelector('.chart-line');
    if (!chart) return;
    
    // Using simple approach: just restart animation
    chart.style.strokeDashoffset = '1000';
    setTimeout(() => {
        chart.style.transition = 'stroke-dashoffset 1.5s ease-out';
        chart.style.strokeDashoffset = '0';
    }, 500);
}

// ── CV CARDS DEAL ANIMATION ─────────────────────────────
function setupCardsDeal() {
    const cards = document.querySelectorAll('.cv-card-inner');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                cards.forEach((card, i) => {
                    setTimeout(() => card.classList.add('deal'), i * 150);
                });
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });

    const grid = document.querySelector('.cv-grid');
    if (grid) observer.observe(grid);
}

// ── CONFUSION MATRIX INTENSITIES & PULSE ──────────────────
function setupConfusionMatrixIntensities() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const table = entry.target;
                const cells = table.querySelectorAll('.cm-diag');
                cells.forEach((cell, i) => {
                    setTimeout(() => {
                        cell.style.boxShadow = '0 0 15px var(--lime)';
                        setTimeout(() => cell.style.boxShadow = 'none', 600);
                    }, i * 100);
                });
                observer.unobserve(table);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.cm-table').forEach(table => {
        observer.observe(table);
        
        // Intensity coloring (inherited logic from previous version but refined)
        const cells = table.querySelectorAll('.cm-cell');
        let maxVal = 0;
        cells.forEach(c => {
          const v = parseInt(c.dataset.val || 0);
          if (v > maxVal) maxVal = v;
        });

        cells.forEach(c => {
            const v = parseInt(c.dataset.val || 0);
            if (v === 0) return;
            const intensity = maxVal > 0 ? v / maxVal : 0;
            if (c.classList.contains('cm-diag')) {
                c.style.background = `rgba(197,231,16,${0.1 + intensity * 0.4})`;
            } else if (intensity > 0.05) {
                c.style.background = `rgba(231,76,60,${intensity * 0.3})`;
                c.style.color = 'rgba(231,76,60,0.9)';
            }
        });
    });
}

// ── SCROLL TRIGGERED BARS ───────────────────────────────
function setupScrollTriggeredBars() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fill = entry.target;
                const targetW = fill.dataset.width || fill.style.width;
                fill.style.width = '0';
                setTimeout(() => {
                    fill.style.transition = 'width 1.2s ease-out';
                    fill.style.width = targetW;
                }, 100);
                observer.unobserve(fill);
            }
        });
    }, { threshold: 1 });

    document.querySelectorAll('.bar-chart-fill, .cv-bar-fill, .mini-fill').forEach(el => observer.observe(el));
}
