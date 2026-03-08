/* MOBILE NAVIGATION & ACCESSIBILITY FEATURES */

// Mobile Navigation Toggle
class MobileNav {
  constructor() {
    this.toggle = document.querySelector('.site-nav__toggle');
    this.menu = document.querySelector('.site-nav__menu');
    this.menuLinks = document.querySelectorAll('.site-nav__menu a');
    this.isOpen = false;
    
    this.init();
  }
  
  init() {
    if (!this.toggle || !this.menu) return;
    
    // Set initial ARIA states
    this.toggle.setAttribute('aria-expanded', 'false');
    
    // Event listeners
    this.toggle.addEventListener('click', this.handleToggle.bind(this));
    this.toggle.addEventListener('keydown', this.handleToggleKeydown.bind(this));
    
    // Close menu when clicking outside
    document.addEventListener('click', this.handleOutsideClick.bind(this));
    
    // Close menu on escape key
    document.addEventListener('keydown', this.handleEscapeKey.bind(this));
    
    // Close menu when navigating to a page
    this.menuLinks.forEach(link => {
      link.addEventListener('click', this.closeMenu.bind(this));
    });
    
    // Handle window resize
    window.addEventListener('resize', this.handleResize.bind(this));
  }
  
  handleToggle(e) {
    e.preventDefault();
    this.isOpen ? this.closeMenu() : this.openMenu();
  }
  
  handleToggleKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      this.handleToggle(e);
    }
  }
  
  openMenu() {
    this.isOpen = true;
    this.menu.classList.add('is-open');
    this.toggle.setAttribute('aria-expanded', 'true');
    
    // Focus first menu item
    const firstLink = this.menu.querySelector('a');
    if (firstLink) {
      firstLink.focus();
    }
    
    // Announce to screen readers
    this.announceToScreenReader('Navigation menu opened');
  }
  
  closeMenu() {
    this.isOpen = false;
    this.menu.classList.remove('is-open');
    this.toggle.setAttribute('aria-expanded', 'false');
    
    // Return focus to toggle button
    this.toggle.focus();
    
    // Announce to screen readers
    this.announceToScreenReader('Navigation menu closed');
  }
  
  handleOutsideClick(e) {
    if (!this.isOpen) return;
    
    if (!this.toggle.contains(e.target) && !this.menu.contains(e.target)) {
      this.closeMenu();
    }
  }
  
  handleEscapeKey(e) {
    if (e.key === 'Escape' && this.isOpen) {
      this.closeMenu();
    }
  }
  
  handleResize() {
    // Close menu on desktop resize
    if (window.innerWidth > 768 && this.isOpen) {
      this.closeMenu();
    }
  }
  
  announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-announce';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }
}

// Focus Management for Better Accessibility
class FocusManager {
  constructor() {
    this.init();
  }
  
  init() {
    // Skip link functionality
    this.handleSkipLinks();
    
    // Smooth scroll with focus management
    this.handleSmoothScroll();
    
    // Keyboard navigation for cards
    this.handleCardKeyboardNav();
  }
  
  handleSkipLinks() {
    const skipLinks = document.querySelectorAll('.skip-link');
    
    skipLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('href').substring(1);
        const target = document.getElementById(targetId);
        
        if (target) {
          target.focus();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }
  
  handleSmoothScroll() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const targetId = link.getAttribute('href').substring(1);
        const target = document.getElementById(targetId);
        
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          
          // Set focus to target for screen readers
          target.focus();
        }
      });
    });
  }
  
  handleCardKeyboardNav() {
    const agentCards = document.querySelectorAll('.agent-card');
    const articleCards = document.querySelectorAll('.article-card');
    
    [...agentCards, ...articleCards].forEach(card => {
      card.setAttribute('tabindex', '0');
      
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          const link = card.querySelector('a');
          if (link) {
            e.preventDefault();
            link.click();
          }
        }
      });
    });
  }
}

// Enhanced Color Contrast Toggle
class ContrastToggle {
  constructor() {
    this.isHighContrast = false;
    this.init();
  }
  
  init() {
    // Check for saved preference
    const savedContrast = localStorage.getItem('high-contrast');
    if (savedContrast === 'true') {
      this.enableHighContrast();
    }
    
    // Check system preference
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
    if (prefersHighContrast && !savedContrast) {
      this.enableHighContrast();
    }
    
    this.createToggleButton();
  }
  
  createToggleButton() {
    const toggleButton = document.createElement('button');
    toggleButton.textContent = this.isHighContrast ? 'Normal Contrast' : 'High Contrast';
    toggleButton.className = 'contrast-toggle';
    toggleButton.setAttribute('aria-label', 'Toggle high contrast mode');
    
    toggleButton.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 20px;
      background: var(--color-crip-black);
      color: var(--color-crip-white);
      border: 2px solid var(--color-crip-black);
      padding: 8px 12px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      z-index: 1000;
    `;
    
    toggleButton.addEventListener('click', this.toggleContrast.bind(this));
    
    document.body.appendChild(toggleButton);
    this.toggleButton = toggleButton;
  }
  
  toggleContrast() {
    this.isHighContrast ? this.disableHighContrast() : this.enableHighContrast();
  }
  
  enableHighContrast() {
    document.documentElement.style.setProperty('--color-crip-black', '#000000');
    document.documentElement.style.setProperty('--color-crip-white', '#ffffff');
    document.documentElement.style.setProperty('--color-access-blue', '#0000ff');
    document.documentElement.style.setProperty('--color-ash', '#000000');
    document.documentElement.style.setProperty('--border-subtle', '2px solid #000000');
    
    this.isHighContrast = true;
    localStorage.setItem('high-contrast', 'true');
    
    if (this.toggleButton) {
      this.toggleButton.textContent = 'Normal Contrast';
    }
    
    // Announce change
    this.announceChange('High contrast mode enabled');
  }
  
  disableHighContrast() {
    document.documentElement.style.removeProperty('--color-crip-black');
    document.documentElement.style.removeProperty('--color-crip-white');
    document.documentElement.style.removeProperty('--color-access-blue');
    document.documentElement.style.removeProperty('--color-ash');
    document.documentElement.style.removeProperty('--border-subtle');
    
    this.isHighContrast = false;
    localStorage.setItem('high-contrast', 'false');
    
    if (this.toggleButton) {
      this.toggleButton.textContent = 'High Contrast';
    }
    
    // Announce change
    this.announceChange('Normal contrast mode enabled');
  }
  
  announceChange(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'assertive');
    announcement.className = 'sr-announce';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }
}

// Performance Optimization
class PerformanceOptimizer {
  constructor() {
    this.init();
  }
  
  init() {
    // Lazy loading for images
    this.setupLazyLoading();
    
    // Intersection Observer for animations
    this.setupIntersectionObserver();
    
    // Preload critical resources
    this.preloadCriticalResources();
  }
  
  setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
          }
        });
      });
      
      images.forEach(img => imageObserver.observe(img));
    } else {
      // Fallback for older browsers
      images.forEach(img => {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
      });
    }
  }
  
  setupIntersectionObserver() {
    const animatableElements = document.querySelectorAll('.agent-card, .article-card');
    
    if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.style.animationPlayState = 'running';
          }
        });
      });
      
      animatableElements.forEach(el => {
        el.style.animationPlayState = 'paused';
        animationObserver.observe(el);
      });
    }
  }
  
  preloadCriticalResources() {
    // Preload next page resources on hover
    const internalLinks = document.querySelectorAll('a[href^="/"], a[href^="./"], a[href^="../"]');
    
    internalLinks.forEach(link => {
      link.addEventListener('mouseenter', () => {
        const prefetchLink = document.createElement('link');
        prefetchLink.rel = 'prefetch';
        prefetchLink.href = link.href;
        document.head.appendChild(prefetchLink);
      }, { once: true });
    });
  }
}

// Initialize all features when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new MobileNav();
  new FocusManager();
  new ContrastToggle();
  new PerformanceOptimizer();
  
  // Announce page load to screen readers
  setTimeout(() => {
    const pageTitle = document.title;
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-announce';
    announcement.textContent = `Page loaded: ${pageTitle}`;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 2000);
  }, 500);
});

// Handle page visibility changes for performance
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    // Pause animations when page is hidden
    document.body.style.animationPlayState = 'paused';
  } else {
    // Resume animations when page is visible
    document.body.style.animationPlayState = 'running';
  }
});