// SmartHealth AI - Main JavaScript
// Author: Enock Queenson Eduafo | Student ID: 11014444
// University of Ghana - Department of Computer Science
// Information Technology | 2026

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    setupCustomCursor();
    setupScrollProgress();
    setupNavbar();
    setupParticles();
    setupEntranceAnimations();
    setupScrollAnimations();
    setupCounters();
    setupRipples();
    
    // Page Transitions: Fade in
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.4s ease';
    requestAnimationFrame(() => {
        document.body.style.opacity = '1';
    });
}

// ── CUSTOM CURSOR ───────────────────────────────────────────
function setupCustomCursor() {
    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', (e) => {
        // Lag effect (simplified)
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });

    const hoverables = document.querySelectorAll('a, button, .model-radio, .preset-btn, input');
    hoverables.forEach(el => {
        el.addEventListener('mouseenter', () => cursor.classList.add('hover'));
        el.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
    });
}

// ── SCROLL PROGRESS ─────────────────────────────────────────
function setupScrollProgress() {
    const bar = document.createElement('div');
    bar.className = 'scroll-progress';
    document.body.appendChild(bar);

    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        bar.style.width = scrolled + "%";
    });
}

// ── NAVBAR LOGIC ────────────────────────────────────────────
function setupNavbar() {
    const nav = document.querySelector('.navbar');
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    
    // Initial entrance
    setTimeout(() => {
        nav.style.opacity = '1';
        nav.style.transform = 'translateY(0)';
    }, 100);

    window.addEventListener('scroll', () => {
        if (window.scrollY > 80) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });

    if (toggle) {
        toggle.addEventListener('click', () => {
            links.classList.toggle('open');
            const spans = toggle.querySelectorAll('span');
            spans[0].style.transform = links.classList.contains('open') ? 'rotate(45deg) translate(5px, 5px)' : 'none';
            spans[1].style.opacity = links.classList.contains('open') ? '0' : '1';
            spans[2].style.transform = links.classList.contains('open') ? 'rotate(-45deg) translate(5px, -5px)' : 'none';
        });
    }
}

// ── HERO PARTICLES ──────────────────────────────────────────
function setupParticles() {
    const container = document.querySelector('.hero-particles');
    if (!container) return;

    for (let i = 0; i < 20; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        
        const startX = Math.random() * 100;
        const startY = Math.random() * 100;
        const dx = (Math.random() - 0.5) * 200;
        const dy = (Math.random() - 0.5) * 200;
        const duration = 8 + Math.random() * 12;

        p.style.left = startX + '%';
        p.style.top = startY + '%';
        p.style.setProperty('--dx', dx + 'px');
        p.style.setProperty('--dy', dy + 'px');
        p.style.animationDuration = duration + 's';
        
        container.appendChild(p);
    }
}

// ── ENTRANCE ANIMATIONS ─────────────────────────────────────
function setupEntranceAnimations() {
    const badge = document.querySelector('.hero-badge');
    if (badge) {
        setTimeout(() => {
            badge.style.opacity = '1';
            badge.style.transform = 'translateY(0)';
        }, 300);
    }

    const headline = document.querySelector('.hero-headline');
    if (headline) {
        const text = headline.innerText;
        headline.innerHTML = '';
        const words = text.split(/\s+/);
        words.forEach((word, i) => {
            const span = document.createElement('span');
            span.className = 'headline-word' + (word === 'HEALTH' ? ' glitch' : '');
            span.innerText = word + ' ';
            headline.appendChild(span);
            setTimeout(() => {
                span.style.opacity = '1';
                span.style.transform = 'translateY(0) rotateX(0)';
            }, 400 + (i * 100));
        });
    }

    const sub = document.querySelector('.hero-sub');
    if (sub) {
        setTimeout(() => {
            sub.style.opacity = '1';
            sub.style.transform = 'translateY(0)';
        }, 800);
    }

    const actions = document.querySelector('.hero-actions');
    if (actions) {
        setTimeout(() => {
            actions.style.opacity = '1';
            actions.style.transform = 'scale(1)';
        }, 1000);
    }

    const stats = document.querySelector('.hero-stats');
    if (stats) {
        setTimeout(() => {
            stats.style.opacity = '1';
        }, 1200);
    }

    const svg = document.querySelector('.hero-svg');
    if (svg) {
        setTimeout(() => svg.classList.add('animate'), 500);
    }

    const metrics = document.querySelectorAll('.metric-card');
    metrics.forEach((m, i) => {
        setTimeout(() => m.classList.add('animate'), 1400 + (i * 200));
    });
}

// ── SCROLL TRIGGERED ANIMATIONS ─────────────────────────────
function setupScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal');
                if (entry.target.classList.contains('section-how')) {
                     const steps = entry.target.querySelectorAll('.step-card');
                     steps.forEach((s, idx) => {
                         setTimeout(() => s.classList.add('reveal'), idx * 100);
                     });
                }
                if (entry.target.classList.contains('section-diseases')) {
                    const cards = entry.target.querySelectorAll('.disease-card');
                    cards.forEach((c, idx) => {
                        setTimeout(() => {
                            c.style.opacity = '1';
                            c.style.transform = 'translateY(0)';
                        }, idx * 80);
                    });
                }
            }
        });
    }, { threshold: 0.15 });

    document.querySelectorAll('.section, .card-grid, .cta-inner, .models-preview-inner').forEach(el => observer.observe(el));
    
    // Performance bars specific observer
    const barObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fill = entry.target.querySelector('.perf-fill, .bar-chart-fill');
                if (fill) {
                    const w = fill.dataset.width || fill.style.width;
                    fill.style.width = '0';
                    setTimeout(() => fill.style.width = w, 100);
                }
            }
        });
    }, { threshold: 0.5 });
    document.querySelectorAll('.perf-bar-wrap, .bar-chart-row').forEach(el => barObserver.observe(el));
}

// ── COUNTER ANIMATIONS ──────────────────────────────────────
function setupCounters() {
    const countElements = document.querySelectorAll('.stat-number');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 1 });

    countElements.forEach(el => observer.observe(el));
}

function animateCounter(el) {
    const target = parseFloat(el.innerText);
    const isFloat = el.innerText.includes('.');
    let start = 0;
    const duration = 2000;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = progress * target;
        
        el.innerText = isFloat ? current.toFixed(1) + '%' : Math.floor(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.innerText = isFloat ? target.toFixed(1) + '%' : target;
        }
    }
    requestAnimationFrame(update);
}

// ── BUTTON RIPPLE ──────────────────────────────────────────
function setupRipples() {
    document.addEventListener('click', (e) => {
        if (e.target.closest('.btn-primary, .btn-ghost, .nav-cta, .btn-predict')) {
            const btn = e.target.closest('.btn-primary, .btn-ghost, .nav-cta, .btn-predict');
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            btn.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        }
    });
}
