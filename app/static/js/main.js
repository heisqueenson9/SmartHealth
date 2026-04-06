/**
 * SmartHealth AI - Main JavaScript
 * Author: Enock Queenson Eduafo (11014444)
 */

// ── MOBILE NAVIGATION ──────────────────────────────────────
(function() {
  const navToggle  = document.getElementById('navToggle');
  const navLinks   = document.getElementById('navLinks');
  const navBackdrop = document.getElementById('navBackdrop');
  const mainNav    = document.getElementById('mainNav');

  if (!navToggle || !navLinks) return;

  function openNav() {
    navLinks.classList.add('open');
    navToggle.classList.add('open');
    navToggle.setAttribute('aria-expanded', 'true');

    // Show backdrop if it exists
    if (navBackdrop) navBackdrop.classList.add('open');

    // Lock body scroll so page content cannot shift
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.width = '100%';
  }

  function closeNav() {
    navLinks.classList.remove('open');
    navToggle.classList.remove('open');
    navToggle.setAttribute('aria-expanded', 'false');

    // Hide backdrop
    if (navBackdrop) navBackdrop.classList.remove('open');

    // Restore body scroll
    document.body.style.overflow = '';
    document.body.style.position = '';
    document.body.style.width = '';
  }

  function toggleNav() {
    if (navLinks.classList.contains('open')) {
      closeNav();
    } else {
      openNav();
    }
  }

  // Toggle on hamburger click
  navToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    toggleNav();
  });

  // Close when any nav link is clicked
  navLinks.querySelectorAll('.nav-link').forEach(function(link) {
    link.addEventListener('click', function() {
      closeNav();
    });
  });

  // Close when backdrop is clicked
  if (navBackdrop) {
    navBackdrop.addEventListener('click', function() {
      closeNav();
    });
  }

  // Close on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && navLinks.classList.contains('open')) {
      closeNav();
    }
  });

  // Navbar scroll effect
  window.addEventListener('scroll', function() {
    if (!mainNav) return;
    if (window.scrollY > 80) {
      mainNav.classList.add('scrolled');
    } else {
      mainNav.classList.remove('scrolled');
    }
  }, { passive: true });

})();

// ── REANIMATION & OBSERVERS ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // IntersectionObserver for Bar Animations
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
    }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

    const bars = document.querySelectorAll('.perf-fill, .pbar-fill, .bar-chart-fill, .bc-fill, .cv-bar-fill, .cv-bf, .mini-fill, .mbar-f, .prob-bar-fill');
    bars.forEach(bar => barObserver.observe(bar));

    // IntersectionObserver for Card Fade-in with Stagger
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal');
                cardObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

    const cards = document.querySelectorAll('.disease-card, .dis-card, .step-card, .step, .metric-card, .m-card, .arch-card, .meth-card, .cv-card, .cm-card, .lim-card, .ethics-item, .step-arrow, .stack-card, .reveal-on-scroll');
    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) ${ (i % 3) * 0.1 }s`;
        cardObserver.observe(card);
    });

    // Handle reveals
    setInterval(() => {
        document.querySelectorAll('.reveal').forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        });
    }, 100);

    // Count-up
    const countObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCountUp(entry.target);
                countObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

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
    @keyframes pulseRotate {
        0%, 100% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(5deg) scale(1.05); }
    }
    .shimmer-btn {
        position: relative;
        overflow: hidden;
    }
    .shimmer-btn::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 50%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        animation: shimmerSweep 3s infinite;
    }
    @keyframes shimmerSweep {
        100% { left: 200%; }
    }
    .step-arrow.reveal svg {
        animation: drawArrow 1s ease forwards;
        opacity: 0;
    }
    @keyframes drawArrow {
        to { opacity: 1; transform: translateX(10px); }
    }
    .stack-card.reveal {
        animation: stackEntrance 0.6s ease forwards, stackFloat 3s infinite ease-in-out;
    }
    @keyframes stackEntrance {
        from { opacity: 0; transform: translateX(-40px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes stackFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    .stack-card { 
        position: relative; overflow: hidden; border-left: 3px solid transparent; transition: all 0.3s;
    }
    .stack-card:hover { transform: scale(1.03) translateY(-6px) !important; border-left: 3px solid #A8E63D; }
    .stack-card::after {
        content: ''; position: absolute; top:0; left:-100%; width: 50%; height:100%;
        background: linear-gradient(90deg, transparent, rgba(168,230,61,0.2), transparent);
    }
    .stack-card.reveal::after { animation: shimmerPass 1.5s ease-out forwards; }
    @keyframes shimmerPass { to { left: 200%; } }
`;
document.head.appendChild(styleNode);
