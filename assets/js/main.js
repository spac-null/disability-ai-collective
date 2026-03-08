// Main JavaScript for Disability-AI Collective
// Accessibility-first, progressive enhancement

(function() {
  'use strict';
  
  // =============================================================================
  // MOBILE NAVIGATION
  // =============================================================================
  
  function initMobileNavigation() {
    const navToggle = document.querySelector('.site-nav__toggle');
    const navMenu = document.querySelector('.site-nav__menu');
    
    if (!navToggle || !navMenu) return;
    
    navToggle.addEventListener('click', function() {
      const isOpen = navMenu.getAttribute('data-open') === 'true';
      const newState = !isOpen;
      
      navMenu.setAttribute('data-open', newState.toString());
      navToggle.setAttribute('aria-expanded', newState.toString());
      
      // Focus management
      if (newState) {
        const firstLink = navMenu.querySelector('a');
        if (firstLink) firstLink.focus();
      }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
      if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
        navMenu.setAttribute('data-open', 'false');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
    
    // Close menu on escape key
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape' && navMenu.getAttribute('data-open') === 'true') {
        navMenu.setAttribute('data-open', 'false');
        navToggle.setAttribute('aria-expanded', 'false');
        navToggle.focus();
      }
    });
  }
  
  // =============================================================================
  // FOCUS MANAGEMENT
  // =============================================================================
  
  function initFocusManagement() {
    // Track if user is using keyboard for navigation
    let isUsingKeyboard = false;
    
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Tab') {
        isUsingKeyboard = true;
        document.body.classList.add('keyboard-navigation');
      }
    });
    
    document.addEventListener('mousedown', function() {
      isUsingKeyboard = false;
      document.body.classList.remove('keyboard-navigation');
    });
    
    // Skip links functionality
    const skipLinks = document.querySelectorAll('.skip-link');
    skipLinks.forEach(function(link) {
      link.addEventListener('click', function(event) {
        event.preventDefault();
        const targetId = this.getAttribute('href').slice(1);
        const target = document.getElementById(targetId);
        
        if (target) {
          target.focus();
          // Ensure the target is focusable
          if (!target.hasAttribute('tabindex')) {
            target.setAttribute('tabindex', '-1');
          }
        }
      });
    });
  }
  
  // =============================================================================
  // SMOOTH SCROLLING (with reduced motion respect)
  // =============================================================================
  
  function initSmoothScrolling() {
    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) return;
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(function(link) {
      link.addEventListener('click', function(event) {
        const targetId = this.getAttribute('href').slice(1);
        const target = document.getElementById(targetId);
        
        if (target) {
          event.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
          
          // Update focus
          target.focus();
          if (!target.hasAttribute('tabindex')) {
            target.setAttribute('tabindex', '-1');
          }
        }
      });
    });
  }
  
  // =============================================================================
  // PERFORMANCE OPTIMIZATION
  // =============================================================================
  
  function initPerformanceOptimizations() {
    // Lazy loading for images (if supported)
    if ('IntersectionObserver' in window) {
      const images = document.querySelectorAll('img[data-src]');
      
      const imageObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.getAttribute('data-src');
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
          }
        });
      });
      
      images.forEach(function(img) {
        imageObserver.observe(img);
      });
    }
  }
  
  // =============================================================================
  // PROGRESSIVE ENHANCEMENT CHECKS
  // =============================================================================
  
  function addJavaScriptClass() {
    document.documentElement.classList.add('js');
    document.documentElement.classList.remove('no-js');
  }
  
  // =============================================================================
  // FORM ENHANCEMENTS (for future forms)
  // =============================================================================
  
  function initFormEnhancements() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
      // Add ARIA live region for form status
      const statusElement = document.createElement('div');
      statusElement.setAttribute('aria-live', 'polite');
      statusElement.setAttribute('aria-atomic', 'true');
      statusElement.className = 'form-status sr-only';
      form.appendChild(statusElement);
      
      // Enhanced form validation
      const inputs = form.querySelectorAll('input, textarea, select');
      inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
          validateField(this);
        });
      });
      
      form.addEventListener('submit', function(event) {
        const isValid = validateForm(this);
        if (!isValid) {
          event.preventDefault();
          announceFormErrors(this);
        }
      });
    });
  }
  
  function validateField(field) {
    const isValid = field.checkValidity();
    const errorElement = document.getElementById(field.getAttribute('aria-describedby'));
    
    if (!isValid && errorElement) {
      errorElement.textContent = field.validationMessage;
      field.setAttribute('aria-invalid', 'true');
    } else if (errorElement) {
      errorElement.textContent = '';
      field.setAttribute('aria-invalid', 'false');
    }
  }
  
  function validateForm(form) {
    const inputs = form.querySelectorAll('input, textarea, select');
    let isFormValid = true;
    
    inputs.forEach(function(input) {
      if (!input.checkValidity()) {
        isFormValid = false;
        validateField(input);
      }
    });
    
    return isFormValid;
  }
  
  function announceFormErrors(form) {
    const statusElement = form.querySelector('.form-status');
    const invalidFields = form.querySelectorAll('[aria-invalid="true"]');
    
    if (statusElement && invalidFields.length > 0) {
      statusElement.textContent = `Please correct ${invalidFields.length} error${invalidFields.length > 1 ? 's' : ''} in the form.`;
      statusElement.classList.remove('sr-only');
      
      // Focus first invalid field
      invalidFields[0].focus();
    }
  }
  
  // =============================================================================
  // KEYBOARD SHORTCUTS
  // =============================================================================
  
  function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
      // Alt + M: Go to main content
      if (event.altKey && event.key === 'm') {
        event.preventDefault();
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
          mainContent.focus();
          if (!mainContent.hasAttribute('tabindex')) {
            mainContent.setAttribute('tabindex', '-1');
          }
        }
      }
      
      // Alt + N: Go to navigation
      if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const navigation = document.getElementById('navigation');
        if (navigation) {
          const firstLink = navigation.querySelector('a');
          if (firstLink) firstLink.focus();
        }
      }
      
      // Alt + F: Go to footer
      if (event.altKey && event.key === 'f') {
        event.preventDefault();
        const footer = document.getElementById('footer');
        if (footer) {
          footer.focus();
          if (!footer.hasAttribute('tabindex')) {
            footer.setAttribute('tabindex', '-1');
          }
        }
      }
    });
  }
  
  // =============================================================================
  // ERROR HANDLING
  // =============================================================================
  
  function initErrorHandling() {
    window.addEventListener('error', function(event) {
      console.error('JavaScript error:', event.error);
      
      // Optionally report to analytics or error tracking service
      // But respect user privacy
    });
    
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
      console.error('Unhandled promise rejection:', event.reason);
    });
  }
  
  // =============================================================================
  // INITIALIZATION
  // =============================================================================
  
  function init() {
    // Basic feature detection
    if (!document.querySelector || !document.addEventListener) {
      return; // Graceful degradation for very old browsers
    }
    
    // Add JavaScript class to HTML element
    addJavaScriptClass();
    
    // Initialize all modules
    initMobileNavigation();
    initFocusManagement();
    initSmoothScrolling();
    initPerformanceOptimizations();
    initFormEnhancements();
    initKeyboardShortcuts();
    initErrorHandling();
    
    // Announce page load to screen readers
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = 'Page loaded successfully';
    document.body.appendChild(announcement);
    
    // Remove announcement after screen reader has processed it
    setTimeout(function() {
      document.body.removeChild(announcement);
    }, 1000);
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Export for testing purposes (if needed)
  window.DisabilityAI = {
    init: init,
    version: '1.0.0'
  };
  
})();