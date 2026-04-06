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
