/**
 * SmartHealth AI - Animations Controller
 * Full-Stack Overhaul
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Reveal Elements on Scroll
    const reveals = document.querySelectorAll('.reveal');
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });
    reveals.forEach(el => revealObserver.observe(el));

    // 2. Animate Stat Counters (Home Page)
    const counters = document.querySelectorAll('.stat-value[data-target]');
    if (counters.length > 0) {
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseFloat(el.dataset.target);
                    const suffix = el.dataset.suffix || '';
                    const isDecimal = target % 1 !== 0;
                    let start = null;
                    const duration = 1800; // 1.8 seconds
                    const step = (timestamp) => {
                        if (!start) start = timestamp;
                        const progress = Math.min((timestamp - start) / duration, 1);
                        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
                        const current = eased * target;
                        el.textContent = (isDecimal ? current.toFixed(1) : Math.floor(current)) + suffix;
                        if (progress < 1) requestAnimationFrame(step);
                    };
                    requestAnimationFrame(step);
                    statsObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });
        counters.forEach(c => statsObserver.observe(c));
    }

    // 3. Animate Benchmark Bars (Results Page)
    const benchBars = document.querySelectorAll('.bench-bar-fill[data-width]');
    if (benchBars.length > 0) {
        const barObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.width = entry.target.dataset.width + '%';
                    barObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });
        benchBars.forEach(bar => barObserver.observe(bar));
    }
});
