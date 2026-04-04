/**
 * SmartHealth AI - Main JavaScript
 * Author: Enock Queenson Eduafo (11014444)
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Hamburger Toggle - Fixed and Enhanced
    const navToggle = document.getElementById('navToggle');
    const navLinks  = document.getElementById('navLinks');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            navToggle.classList.toggle('open');
            document.body.style.overflow = 
                navLinks.classList.contains('open') ? 'hidden' : '';
        });

        // Close menu when clicking links
        navLinks.querySelectorAll('a, .nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('open');
                navToggle.classList.remove('open');
                document.body.style.overflow = '';
            });
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
                navLinks.classList.remove('open');
                navToggle.classList.remove('open');
                document.body.style.overflow = '';
            }
        });
    }

    // 2. Navbar Scroll Effect (Blur & Border)
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 3. IntersectionObserver for Bar Animations
    const barObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target;
                const width = bar.style.getPropertyValue('--w') || '0%';
                bar.style.width = width;
                
                if (bar.classList.contains('bar-chart-fill')) {
                    bar.style.animation = 'barOvershoot 1s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
                }
                
                barObserver.unobserve(bar);
            }
        });
    }, { threshold: 0.1 });

    const bars = document.querySelectorAll('.perf-fill, .pbar-fill, .bar-chart-fill, .bc-fill, .cv-bar-fill, .cv-bf, .mini-fill, .mbar-f, .prob-bar-fill');
    bars.forEach(bar => barObserver.observe(bar));

    // 4. IntersectionObserver for Card Fade-in with Stagger
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal');
                cardObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    const cards = document.querySelectorAll('.disease-card, .dis-card, .step-card, .step, .metric-card, .m-card, .arch-card, .meth-card, .cv-card, .cm-card, .lim-card, .ethics-item');
    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) ${ (i % 3) * 0.1 }s`;
        cardObserver.observe(card);
    });

    document.querySelectorAll('.reveal-on-scroll').forEach(el => {
        const obs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    obs.unobserve(entry.target);
                }
            });
        });
        obs.observe(el);
    });

    // Handle reveals
    setInterval(() => {
        document.querySelectorAll('.reveal').forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        });
    }, 100);

    // 5. IntersectionObserver for Count-up
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
        const targetAttr = el.getAttribute('data-target');
        if (!targetAttr) return;
        
        const target = parseFloat(targetAttr);
        const suffix = el.getAttribute('data-suffix') || '';
        const duration = 1500;
        const startTime = performance.now();
        const isDecimal = targetAttr.includes('.');

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3);
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
const styleNode = document.createElement('style');
styleNode.textContent = `
    @keyframes barOvershoot {
        0% { width: 0; }
        70% { width: calc(var(--w) + 5%); }
        100% { width: var(--w); }
    }
`;
document.head.appendChild(styleNode);
