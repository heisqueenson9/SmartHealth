/**
 * SmartHealth - Cinematic Animation Controller
 * Implementation: IntersectionObserver for scroll-triggered reveals
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Reveal Animations (Observer)
    const revealObserverArr = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Optional: Reveal children sequentially if they have .reveal class too
                const children = entry.target.querySelectorAll('.reveal-child');
                children.forEach((child, index) => {
                    setTimeout(() => {
                        child.classList.add('visible');
                    }, index * 100);
                });
                
                // unobserve if we only want it to reveal once
                // revealObserverArr.unobserve(entry.target);
            }
        });
    }, { 
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px' // offset so it reveals slightly before entering viewport
    });

    // 2. Initialize Revealable Elements
    const revealableElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
    revealableElements.forEach(el => revealObserverArr.observe(el));

    // 3. Staggered Entrance for specific sections
    const autoStagger = document.querySelectorAll('.stagger-grid');
    autoStagger.forEach(grid => {
        const items = grid.children;
        Array.from(items).forEach((item, index) => {
            item.classList.add('reveal');
            item.style.transitionDelay = `${index * 0.1}s`;
            revealObserverArr.observe(item);
        });
    });

    // 4. Count Up Stats (Hero Section)
    const countStats = () => {
        const stats = document.querySelectorAll('.stat-n');
        stats.forEach(stat => {
            const targetStr = stat.innerText;
            const target = parseFloat(targetStr.replace(/[^0-9.]/g, ''));
            const suffix = targetStr.replace(/[0-9.]/g, '');
            let count = 0;
            const duration = 2000; // 2 seconds
            const increment = target / (duration / 16); // 16ms per frame
            
            const updateCount = () => {
                count += increment;
                if (count < target) {
                    if (target % 1 === 0) {
                        stat.innerText = Math.round(count) + suffix;
                    } else {
                        stat.innerText = count.toFixed(1) + suffix;
                    }
                    requestAnimationFrame(updateCount);
                } else {
                    stat.innerText = targetStr;
                }
            };
            
            // Only trigger if statistic section is visible
            const obs = new IntersectionObserver(entries => {
                if(entries[0].isIntersecting) {
                    updateCount();
                    obs.unobserve(stat);
                }
            });
            obs.observe(stat);
        });
    };
    
    countStats();
});
