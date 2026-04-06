(function() {
'use strict';

/* ══════════════════════════════════
   PARTICLE CANVAS BACKGROUND
══════════════════════════════════ */
function initParticles() {
  const canvas = document.createElement('canvas');
  canvas.id = 'particle-canvas';
  document.body.prepend(canvas);
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];
  let mouse = { x: -999, y: -999 };

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });

  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 1.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -(Math.random() * 0.4 + 0.15),
      alpha: Math.random() * 0.6 + 0.2
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      const dx = p.x - mouse.x, dy = p.y - mouse.y;
      const dist = Math.sqrt(dx*dx + dy*dy);
      if (dist < 80) {
        p.x += (dx / dist) * 1.5;
        p.y += (dy / dist) * 1.5;
      }
      p.x += p.vx; p.y += p.vy;
      if (p.y < -10) { p.y = H + 10; p.x = Math.random() * W; }
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(168,230,61,${p.alpha})`;
      ctx.fill();
    });

    // Connection lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i+1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(168,230,61,${0.12 * (1 - dist/120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
}

/* ══════════════════════════════════
   CUSTOM CURSOR
══════════════════════════════════ */
function initCursor() {
  if (window.innerWidth < 769) return;
  const dot  = document.createElement('div'); dot.id  = 'cursor-dot';
  const ring = document.createElement('div'); ring.id = 'cursor-ring';
  document.body.append(dot, ring);

  let rx = 0, ry = 0;
  document.addEventListener('mousemove', e => {
    dot.style.left  = e.clientX + 'px';
    dot.style.top   = e.clientY + 'px';
    rx += (e.clientX - rx) * 0.12;
    ry += (e.clientY - ry) * 0.12;
    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';
  });

  function lerpCursor() {
    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';
    requestAnimationFrame(lerpCursor);
  }
  lerpCursor();

  document.querySelectorAll('a, button, [class*="btn"], .condition-card, .classifier-card')
    .forEach(el => {
      el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
      el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
    });
}

/* ══════════════════════════════════
   PAGE TRANSITION
══════════════════════════════════ */
function initPageTransition() {
  const overlay = document.createElement('div');
  overlay.id = 'page-transition';
  document.body.prepend(overlay);

  // Slide out on load
  requestAnimationFrame(() => {
    overlay.classList.add('leaving');
    setTimeout(() => overlay.style.display = 'none', 500);
  });

  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto')) return;
    link.addEventListener('click', function(e) {
      e.preventDefault();
      overlay.style.display = 'block';
      overlay.style.left = '-100%';
      overlay.classList.remove('leaving');
      requestAnimationFrame(() => {
        overlay.classList.add('entering');
        setTimeout(() => window.location.href = href, 450);
      });
    });
  });
}

/* ══════════════════════════════════
   SCROLL REVEAL
══════════════════════════════════ */
function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        const delay = entry.target.dataset.delay || 0;
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, parseInt(delay));
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
  
  // Auto-stagger children of reveal-stagger containers
  document.querySelectorAll('.reveal-stagger').forEach(container => {
    Array.from(container.children).forEach((child, i) => {
      child.classList.add('reveal');
      if (!child.dataset.reveal) child.dataset.reveal = 'up';
      child.dataset.delay = i * 110;
      observer.observe(child);
    });
  });
}

/* ══════════════════════════════════
   HERO WORD SPLIT
══════════════════════════════════ */
function initHeroWordSplit() {
  const hero = document.querySelector('h1, .hero-title, .page-title');
  if (!hero) return;
  const words = hero.textContent.trim().split(' ');
  hero.innerHTML = words.map((w, i) =>
    `<span class="word-reveal" style="--i:${i}">
       <span class="word-reveal-inner" style="transition-delay:${i * 80 + 200}ms">${w}</span>
     </span>`
  ).join(' ');
  setTimeout(() => {
    hero.querySelectorAll('.word-reveal-inner').forEach(el => el.classList.add('visible'));
  }, 100);
}

/* ══════════════════════════════════
   BLUR REVEAL FOR SUBTITLE
══════════════════════════════════ */
function initBlurReveal() {
  document.querySelectorAll('.hero p, .hero-subtitle, .page-subtitle').forEach((el, i) => {
    el.classList.add('blur-reveal');
    setTimeout(() => el.classList.add('visible'), 900 + i * 150);
  });
}

/* ══════════════════════════════════
   COUNTERS
══════════════════════════════════ */
function initCounters() {
  function easeOutExpo(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }

  function animateCounter(el) {
    const raw = el.dataset.target || el.textContent;
    const isFloat = raw.includes('.');
    const hasPercent = raw.includes('%');
    const target = parseFloat(raw.replace(/[^0-9.]/g, ''));
    const duration = 2000;
    const start = performance.now();

    function update(now) {
      const t = Math.min((now - start) / duration, 1);
      const val = target * easeOutExpo(t);
      el.textContent = (isFloat ? val.toFixed(1) : Math.floor(val)) + (hasPercent ? '%' : '');
      if (t < 1) requestAnimationFrame(update);
      else {
        el.textContent = raw.includes('%') ? target + '%' : target;
        el.classList.add('counter-flash');
      }
    }
    requestAnimationFrame(update);
  }

  const counterObserver = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animateCounter(e.target);
        counterObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.stat-number, .counter, [data-counter]').forEach(el => {
    if (!el.dataset.target) el.dataset.target = el.textContent.trim();
    el.textContent = '0';
    counterObserver.observe(el);
  });
}

/* ══════════════════════════════════
   ANIMATED BARS
══════════════════════════════════ */
function initBars() {
  const barObserver = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const fills = e.target.querySelectorAll('[data-target], .bar-fill, .cv-bar-fill, .validation-bar');
        fills.forEach((bar, i) => {
          const target = parseFloat(bar.dataset.target || bar.dataset.width || 0);
          setTimeout(() => {
            bar.style.transition = 'width 1.4s cubic-bezier(0.16, 1, 0.3, 1)';
            bar.style.width = target + '%';
          }, i * 200);
        });
        barObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.performance-section, .benchmarks-section, .bar-section, .results-bars').forEach(s => barObserver.observe(s));
  // Also observe individual bars directly
  document.querySelectorAll('.bar-fill, .cv-bar-fill').forEach(bar => {
    const target = parseFloat(bar.dataset.target || 0);
    bar.style.width = '0%';
    barObserver.observe(bar.closest('section') || bar.parentElement);
  });
}

/* ══════════════════════════════════
   SECTION LABEL WIPE
══════════════════════════════════ */
function initLabelWipe() {
  document.querySelectorAll('.section-label, .label-tag, [class*="label"]').forEach(el => {
    if (el.textContent.trim().length < 30) {
      el.classList.add('label-wipe');
    }
  });
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
  }, { threshold: 0.5 });
  document.querySelectorAll('.label-wipe').forEach(el => obs.observe(el));
}

/* ══════════════════════════════════
   CONFUSION MATRIX CELL FLASH
══════════════════════════════════ */
function initMatrixAnimation() {
  document.querySelectorAll('table').forEach(table => {
    const rows = table.querySelectorAll('tr');
    rows.forEach((row, ri) => {
      const cells = row.querySelectorAll('td');
      cells.forEach((cell, ci) => {
        if (ri === ci + 1) { // diagonal (accounting for header row offset)
          cell.classList.add('matrix-diagonal');
          cell.style.animationDelay = ((ri * cells.length + ci) * 20) + 'ms';
        }
      });
    });
    const tableObs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.querySelectorAll('td').forEach((cell, i) => {
            cell.style.opacity = '0';
            setTimeout(() => {
              cell.style.transition = 'opacity 0.3s ease';
              cell.style.opacity = '1';
            }, i * 18);
          });
          tableObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.2 });
    tableObs.observe(table);
  });
}

/* ══════════════════════════════════
   BUTTON RIPPLE
══════════════════════════════════ */
function initRipple() {
  document.querySelectorAll('button, .btn, [class*="btn"], [class*="-button"]').forEach(btn => {
    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.addEventListener('click', function(e) {
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 2;
      const ripple = document.createElement('span');
      ripple.className = 'ripple-effect';
      ripple.style.cssText = `
        width:${size}px; height:${size}px;
        left:${e.clientX - rect.left - size/2}px;
        top:${e.clientY - rect.top - size/2}px;
      `;
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });
}

/* ══════════════════════════════════
   SHIMMER ON PRIMARY BUTTONS
══════════════════════════════════ */
function initShimmerButtons() {
  document.querySelectorAll('.btn-primary, .cta-btn, [class*="run-btn"], [class*="submit"]').forEach(btn => {
    btn.classList.add('btn-shimmer');
  });
}

/* ══════════════════════════════════
   NAVBAR SCROLL EFFECT
══════════════════════════════════ */
function initNavScroll() {
  const nav = document.querySelector('nav, header');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
}

/* ══════════════════════════════════
   FLOATING ICONS
══════════════════════════════════ */
function initFloatingIcons() {
  document.querySelectorAll('.infra-item svg, .infra-item img, .tech-item svg, .tech-item img').forEach((icon, i) => {
    icon.style.animation = `floatY ${3.5 + (i % 3) * 0.5}s ease-in-out infinite`;
    icon.style.animationDelay = `${i * 0.4}s`;
  });
}

/* ══════════════════════════════════
   SHIELD + DISCLAIMER CLASSES
══════════════════════════════════ */
function initSpecialElements() {
  document.querySelectorAll('[class*="shield"], .cta-icon svg').forEach(el => el.classList.add('shield-beat'));
  document.querySelectorAll('.disclaimer, [class*="disclaimer"], .academic-notice').forEach(el => el.classList.add('disclaimer-glow'));
  document.querySelectorAll('.accuracy-badge, [class*="badge"]').forEach(el => el.classList.add('badge-pop'));
  document.querySelectorAll('[class*="radar"], [class*="chart-ring"]').forEach(el => el.classList.add('radar-spin'));
}

/* ══════════════════════════════════
   ADD REVEAL CLASSES TO ALL SECTIONS
══════════════════════════════════ */
function addRevealClasses() {
  const sectionSelectors = [
    '.hero > *:not(h1):not(.hero-title)',
    '.workflow-step, .step-card',
    '.condition-card',
    '.infra-item, .tech-item',
    '.arch-step',
    '.ethics-card, .warning-card',
    '.researcher-card',
    '.matrix-wrapper',
    '.bar-item',
    'footer > *'
  ];
  sectionSelectors.forEach((sel, groupIdx) => {
    document.querySelectorAll(sel).forEach((el, i) => {
      if (!el.classList.contains('reveal')) {
        el.classList.add('reveal');
        el.dataset.reveal = ['up','left','scale','right','up'][groupIdx % 5];
        el.dataset.delay = i * 110;
      }
    });
  });

  // Section headings
  document.querySelectorAll('h2, h3').forEach((el, i) => {
    if (!el.classList.contains('reveal') && !el.closest('.hero')) {
      el.classList.add('reveal');
      el.dataset.reveal = 'up';
      el.dataset.delay = 0;
    }
  });
}

/* ══════════════════════════════════
   INIT ALL
══════════════════════════════════ */
function init() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  
  initParticles();
  initCursor();
  initPageTransition();
  addRevealClasses();
  initReveal();
  initHeroWordSplit();
  initBlurReveal();
  initCounters();
  initBars();
  initLabelWipe();
  initMatrixAnimation();
  initRipple();
  initShimmerButtons();
  initNavScroll();
  initFloatingIcons();
  initSpecialElements();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

})();
