// Modern JavaScript for Disability-AI Collective
// Clean, accessible, progressive enhancement

(function() {
  'use strict';
  
  // Initialize when DOM is ready
  function init() {
    initNavigation();
    initSmoothScrolling();
    initAccessibilityAnnouncements();
  }
  
  // Mobile navigation
  function initNavigation() {
    const toggle = document.querySelector('.site-nav__toggle');
    const menu = document.querySelector('.site-nav__menu');
    
    if (!toggle || !menu) return;
    
    toggle.addEventListener('click', function() {
      const isOpen = this.getAttribute('aria-expanded') === 'true';
      const newState = !isOpen;
      
      this.setAttribute('aria-expanded', newState.toString());
      menu.style.display = newState ? 'flex' : 'none';
      
      if (newState) {
        const firstLink = menu.querySelector('a');
        if (firstLink) firstLink.focus();
      }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
      if (!toggle.contains(event.target) && !menu.contains(event.target)) {
        toggle.setAttribute('aria-expanded', 'false');
        menu.style.display = 'none';
      }
    });
    
    // Handle escape key
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        toggle.setAttribute('aria-expanded', 'false');
        menu.style.display = 'none';
        toggle.focus();
      }
    });
  }
  
  // Smooth scrolling for anchor links
  function initSmoothScrolling() {
    // Respect user's motion preferences
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }
    
    document.querySelectorAll('a[href^="#"]').forEach(link => {
      link.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href').slice(1);
        const target = document.getElementById(targetId);
        
        if (target) {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
          
          // Focus management
          target.focus();
          if (!target.hasAttribute('tabindex')) {
            target.setAttribute('tabindex', '-1');
          }
        }
      });
    });
  }
  
  // Accessibility announcements
  function initAccessibilityAnnouncements() {
    // Announce page load completion
    announceToScreenReader('Page loaded successfully');
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(event) {
      // Alt + M: Main content
      if (event.altKey && event.key === 'm') {
        event.preventDefault();
        const main = document.getElementById('main-content');
        if (main) {
          main.focus();
          if (!main.hasAttribute('tabindex')) {
            main.setAttribute('tabindex', '-1');
          }
        }
      }
      
      // Alt + N: Navigation
      if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const nav = document.getElementById('navigation');
        if (nav) {
          const firstLink = nav.querySelector('a');
          if (firstLink) firstLink.focus();
        }
      }
    });
  }
  
  // Announce messages to screen readers
  function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Clean up after announcement
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }
  
  // Copy to clipboard utility
  function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(() => {
        announceToScreenReader('Link copied to clipboard');
      });
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      try {
        document.execCommand('copy');
        announceToScreenReader('Link copied to clipboard');
      } catch (err) {
        console.error('Copy failed:', err);
        announceToScreenReader('Copy failed');
      } finally {
        textArea.remove();
      }
    }
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Export utilities for global use
  window.DisabilityAI = {
    announceToScreenReader,
    copyToClipboard
  };
  
})();