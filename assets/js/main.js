/* MOBILE NAVIGATION & ACCESSIBILITY */

// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.querySelector('.site-nav__toggle');
  const menu = document.querySelector('.site-nav__menu');
  
  if (toggle && menu) {
    toggle.addEventListener('click', function() {
      const isOpen = menu.classList.contains('is-open');
      
      if (isOpen) {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      } else {
        menu.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
      }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!toggle.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
    
    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && menu.classList.contains('is-open')) {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
  }
});

// Smooth scroll for anchor links
document.addEventListener('DOMContentLoaded', function() {
  const anchorLinks = document.querySelectorAll('a[href^="#"]');
  
  anchorLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href').substring(1);
      const target = document.getElementById(targetId);
      
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start' 
        });
        
        // Set focus for screen readers
        target.focus();
      }
    });
  });
});

// Skip link functionality
document.addEventListener('DOMContentLoaded', function() {
  const skipLinks = document.querySelectorAll('.skip-link');
  
  skipLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href').substring(1);
      const target = document.getElementById(targetId);
      
      if (target) {
        target.focus();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
});
// External links open in new tab
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.post-content a[href^="http"], .post-content a[href^="//"]').forEach(function(a) {
    if (a.hostname !== window.location.hostname) {
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'noopener noreferrer');
    }
  });
});
