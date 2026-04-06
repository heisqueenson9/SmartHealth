/**
 * SmartHealth AI - Cinematic Animation Engine
 * Handles Particles, IntersectionObserver, Counters, and Custom Cursors
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // ────────────────────────────────────────
    // INJECT HUD ELEMENTS
    // ────────────────────────────────────────
    
    // Only on desktop
    if (window.innerWidth > 768) {
        // Create Canvas for particles
        const canvas = document.createElement('canvas');
        canvas.id = 'particle-canvas';
        document.body.appendChild(canvas);
        
        // Create Cursor
        const cursorDot = document.createElement('div');
        cursorDot.id = 'cursor-dot';
        const cursorRing = document.createElement('div');
        cursorRing.id = 'cursor-ring';
        document.body.appendChild(cursorDot);
        document.body.appendChild(cursorRing);
        
        initParticles(canvas);
        initCursor(cursorDot, cursorRing);
    }
    
    // Page Transition Overlay
    const overlay = document.createElement('div');
    overlay.id = 'page-transition';
    document.body.appendChild(overlay);
    
    // Simple fade-out on load
    overlay.classList.add('sweep-out');
    
    // ────────────────────────────────────────
    // SCROLL REVEAL SYSTEM
    // ────────────────────────────────────────
    
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                
                // If it's a counter, trigger counting
                if (entry.target.dataset.reveal === 'counter') {
                    animateCount(entry.target);
                }
                
                // If it's a bar, triggr filling
                if (entry.target.classList.contains('bar-fill') || entry.target.classList.contains('perf-fill')) {
                    const targetWidth = entry.target.getAttribute('data-width') || entry.target.style.width;
                    entry.target.style.width = targetWidth;
                }
                
                // Handle staggered children
                if (entry.target.classList.contains('reveal-stagger')) {
                    const children = entry.target.querySelectorAll('.reveal-child');
                    children.forEach((child, i) => {
                        setTimeout(() => {
                            child.classList.add('active');
                        }, i * 120);
                    });
                }
            }
        });
    }, { threshold: 0.15 });

    // Mark elements for reveals
    const revealElements = document.querySelectorAll('.reveal, .bar-fill, .perf-fill');
    revealElements.forEach(el => revealObserver.observe(el));

    // ────────────────────────────────────────
    // HERO HEADLINE WORD SPLIT
    // ────────────────────────────────────────
    
    const heroes = document.querySelectorAll('.hero h1, .hero-title, .page-header h1, .pg-hdr h1');
    heroes.forEach(h1 => {
        const words = h1.innerText.split(' ');
        h1.innerHTML = '';
        words.forEach((word, index) => {
            h1.innerHTML += `
                <span class="word-wrap">
                    <span class="word-inner" style="transition-delay: ${index * 80}ms">${word}</span>
                </span>${index < words.length - 1 ? '&nbsp;' : ''}
            `;
        });
        
        setTimeout(() => h1.classList.add('active'), 200);
    });

    // ────────────────────────────────────────
    // COUNTER ANIMATION
    // ────────────────────────────────────────
    
    function animateCount(el) {
        const targetStr = el.innerText.replace(/[%,+]/g, '');
        const target = parseFloat(targetStr);
        const suffix = el.innerText.match(/[%,+]/g) ? el.innerText.match(/[%,+]/g)[0] : '';
        const duration = 2000;
        const startTime = performance.now();
        const startVal = 0;
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Ease out expo
            const easeProgress = 1 - Math.pow(2, -10 * progress);
            const currentVal = startVal + (target - startVal) * easeProgress;
            
            el.innerText = (suffix === '%' ? currentVal.toFixed(1) : Math.floor(currentVal)) + suffix;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.classList.add('badge-pop');
            }
        }
        requestAnimationFrame(update);
    }
    
    // Tag stats as counters if they have decimals or are numbers
    document.querySelectorAll('.stat-number, .stat-n, .mcard-acc, .cv-score').forEach(el => {
        el.dataset.reveal = 'counter';
        el.classList.add('reveal');
        revealObserver.observe(el);
    });

    // ────────────────────────────────────────
    // PARTICLES ENGINE
    // ────────────────────────────────────────
    
    function initParticles(canvas) {
        const ctx = canvas.getContext('2d');
        let width, height;
        let particles = [];
        let mouse = { x: -100, y: -100 };
        
        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }
        
        window.addEventListener('resize', resize);
        resize();
        
        window.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });
        
        class Particle {
            constructor() {
                this.reset();
            }
            reset() {
                this.x = Math.random() * width;
                this.y = height + Math.random() * 200;
                this.vx = (Math.random() - 0.5) * 0.2;
                this.vy = -(0.2 + Math.random() * 0.6);
                this.size = Math.random() * 2 + 1;
                this.opacity = Math.random() * 0.5 + 0.1;
                this.pulse = Math.random() * 0.02;
            }
            update() {
                this.x += this.vx;
                this.y += this.vy;
                this.opacity += this.pulse;
                if (this.opacity > 0.6 || this.opacity < 0.1) this.pulse *= -1;
                
                // Repel from mouse
                const dx = this.x - mouse.x;
                const dy = this.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 100) {
                    const angle = Math.atan2(dy, dx);
                    this.x += Math.cos(angle) * 2;
                    this.y += Math.sin(angle) * 2;
                }
                
                if (this.y < -50) this.reset();
            }
            draw() {
                ctx.fillStyle = `rgba(168, 230, 61, ${this.opacity})`;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        for (let i = 0; i < 60; i++) particles.push(new Particle());
        
        function loop() {
            ctx.clearRect(0, 0, width, height);
            
            particles.forEach((p, i) => {
                p.update();
                p.draw();
                
                // Draw lines
                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const dx = p.x - p2.x;
                    const dy = p.y - p2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 120) {
                        ctx.strokeStyle = `rgba(168, 230, 61, ${0.1 * (1 - dist / 120)})`;
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                }
            });
            requestAnimationFrame(loop);
        }
        loop();
    }

    // ────────────────────────────────────────
    // CUSTOM CURSOR
    // ────────────────────────────────────────
    
    function initCursor(dot, ring) {
        let mouseX = 0, mouseY = 0;
        let ringX = 0, ringY = 0;
        
        window.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            
            dot.style.transform = `translate(${mouseX - 4}px, ${mouseY - 4}px)`;
        });
        
        function animateRing() {
            // Lerp ring follow
            ringX += (mouseX - ringX) * 0.15;
            ringY += (mouseY - ringY) * 0.15;
            
            ring.style.transform = `translate(${ringX - 18}px, ${ringY - 18}px)`;
            requestAnimationFrame(animateRing);
        }
        animateRing();
        
        // Hover effects
        const interactive = document.querySelectorAll('a, button, .mcard, .pbtn, .model-selector .mcard');
        interactive.forEach(el => {
            el.addEventListener('mouseenter', () => {
                ring.classList.add('ring-hover');
                dot.style.opacity = '0';
            });
            el.addEventListener('mouseleave', () => {
                ring.classList.remove('ring-hover');
                dot.style.opacity = '1';
            });
        });
    }

    // ────────────────────────────────────────
    // PAGE NAVIGATION TRANSITION
    // ────────────────────────────────────────
    
    document.querySelectorAll('a').forEach(link => {
        if (link.hostname === window.location.hostname && !link.hash && link.target !== '_blank') {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetUrl = link.href;
                overlay.classList.remove('sweep-out');
                overlay.classList.add('sweep-in');
                
                setTimeout(() => {
                    window.location.href = targetUrl;
                }, 400);
            });
        }
    });
});
