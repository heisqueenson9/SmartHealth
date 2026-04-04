/**
 * SmartHealth AI - Main JavaScript
 * Author: Enock Queenson Eduafo
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Hamburger Toggle
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            hamburger.classList.toggle('active');
        });
    }

    // 2. Navbar Scroll Effect (Blur & Border)
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 80) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 3. IntersectionObserver for Bar Animations
    // Targets: perf-fill, pbar-fill, bar-chart-fill, bc-fill, cv-bar-fill, cv-bf, mini-fill, mbar-f
    const barObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target;
                const width = bar.style.getPropertyValue('--w') || '0%';
                bar.style.width = width;
                
                // Add overshoot animation if requested for specific elements
                if (bar.classList.contains('bar-chart-fill')) {
                    bar.style.animation = 'barOvershoot 1s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
                }
                
                barObserver.unobserve(bar);
            }
        });
    }, { threshold: 0.1 });

    const bars = document.querySelectorAll('.perf-fill, .pbar-fill, .bar-chart-fill, .bc-fill, .cv-bar-fill, .cv-bf, .mini-fill, .mbar-f');
    bars.forEach(bar => barObserver.observe(bar));

    // 4. IntersectionObserver for Card Fade-in with Stagger
    // Targets: disease-card, dis-card, step-card, step, metric-card, m-card
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal');
                cardObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    const cards = document.querySelectorAll('.disease-card, .dis-card, .step-card, .step, .metric-card, .m-card, .arch-card, .meth-card, .cv-card, .cm-card');
    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) ${ (i % 3) * 0.15 }s`;
        cardObserver.observe(card);
    });

    // Handle "reveal" class for cards
    document.querySelectorAll('.disease-card, .dis-card, .step-card, .step, .metric-card, .m-card, .arch-card, .meth-card, .cv-card, .cm-card').forEach(card => {
        const obs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    obs.unobserve(entry.target);
                }
            });
        });
        obs.observe(card);
    });

    // 5. IntersectionObserver for Count-up
    // Targets: stat-number, stat-n, cv-score, cv-sc
    const countObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCountUp(entry.target);
                countObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    const numbers = document.querySelectorAll('.stat-number, .stat-n, .cv-score, .cv-sc');
    numbers.forEach(num => countObserver.observe(num));

    function animateCountUp(el) {
        const target = parseFloat(el.getAttribute('data-target'));
        const suffix = el.getAttribute('data-suffix') || '';
        const duration = 1500;
        const startTime = performance.now();
        const isDecimal = el.getAttribute('data-target').includes('.');

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3); // Cubic ease-out
            const currentVal = (easeProgress * target);

            el.innerHTML = (isDecimal ? currentVal.toFixed(1) : Math.floor(currentVal)) + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        requestAnimationFrame(update);
    }
});

// Custom Bar CSS Keyframe (injected)
const style = document.createElement('style');
style.textContent = `
    @keyframes barOvershoot {
        0% { width: 0; }
        70% { width: calc(var(--w) + 5%); }
        100% { width: var(--w); }
    }
`;
document.head.appendChild(style);
