// Accessibility controls for Disability-AI Collective
// User-controlled accessibility features

(function() {
  'use strict';
  
  const AccessibilityPanel = {
    init() {
      this.createPanel();
      this.loadPreferences();
      this.bindEvents();
    },
    
    createPanel() {
      // Create floating accessibility button
      const button = document.createElement('button');
      button.className = 'a11y-toggle';
      button.innerHTML = '♿';
      button.setAttribute('aria-label', 'Accessibility Options');
      button.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: var(--color-primary);
        color: white;
        border: none;
        font-size: 24px;
        cursor: pointer;
        z-index: 1000;
        box-shadow: var(--shadow-lg);
        transition: var(--transition-all);
      `;
      
      // Create panel
      const panel = document.createElement('div');
      panel.className = 'a11y-panel';
      panel.style.cssText = `
        position: fixed;
        bottom: 85px;
        right: 20px;
        background: var(--color-background);
        border: 1px solid var(--color-border);
        border-radius: var(--border-radius-lg);
        padding: var(--space-6);
        box-shadow: var(--shadow-xl);
        z-index: 1000;
        min-width: 280px;
        display: none;
      `;
      
      panel.innerHTML = `
        <h3 style="margin-bottom: var(--space-4); font-size: var(--font-size-lg);">Accessibility</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); margin-bottom: var(--space-4);">
          <button class="a11y-btn" data-feature="contrast">
            <span>🔆</span><br>High Contrast
          </button>
          <button class="a11y-btn" data-feature="font-size">
            <span>🔍</span><br>Large Font
          </button>
          <button class="a11y-btn" data-feature="dyslexia">
            <span>📖</span><br>Dyslexia Font
          </button>
          <button class="a11y-btn" data-feature="motion">
            <span>⏸️</span><br>Reduce Motion
          </button>
        </div>
        <button class="a11y-reset" style="width: 100%; padding: var(--space-2); background: var(--color-gray-500); color: white; border: none; border-radius: var(--border-radius); cursor: pointer;">
          Reset All
        </button>
      `;
      
      // Add styles for buttons
      const style = document.createElement('style');
      style.textContent = `
        .a11y-btn {
          padding: var(--space-3);
          border: 1px solid var(--color-border);
          border-radius: var(--border-radius);
          background: var(--color-surface);
          cursor: pointer;
          text-align: center;
          font-size: var(--font-size-xs);
          line-height: 1.2;
          transition: var(--transition-colors);
        }
        .a11y-btn:hover {
          border-color: var(--color-primary);
        }
        .a11y-btn.active {
          background: var(--color-primary);
          color: white;
          border-color: var(--color-primary);
        }
        .a11y-btn span {
          display: block;
          font-size: 18px;
          margin-bottom: var(--space-1);
        }
        .a11y-toggle:hover {
          transform: scale(1.05);
        }
      `;
      
      document.head.appendChild(style);
      document.body.appendChild(button);
      document.body.appendChild(panel);
      
      this.button = button;
      this.panel = panel;
    },
    
    bindEvents() {
      // Toggle panel
      this.button.addEventListener('click', () => {
        const isVisible = this.panel.style.display === 'block';
        this.panel.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
          this.panel.querySelector('.a11y-btn').focus();
        }
      });
      
      // Close panel when clicking outside
      document.addEventListener('click', (e) => {
        if (!this.button.contains(e.target) && !this.panel.contains(e.target)) {
          this.panel.style.display = 'none';
        }
      });
      
      // Feature toggles
      this.panel.querySelectorAll('.a11y-btn[data-feature]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const feature = e.currentTarget.dataset.feature;
          this.toggleFeature(feature);
        });
      });
      
      // Reset button
      this.panel.querySelector('.a11y-reset').addEventListener('click', () => {
        this.resetAll();
      });
      
      // Keyboard shortcuts
      document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.altKey) {
          switch (e.key) {
            case 'c':
              e.preventDefault();
              this.toggleFeature('contrast');
              break;
            case 'f':
              e.preventDefault();
              this.toggleFeature('font-size');
              break;
            case 'd':
              e.preventDefault();
              this.toggleFeature('dyslexia');
              break;
            case 'm':
              e.preventDefault();
              this.toggleFeature('motion');
              break;
          }
        }
      });
    },
    
    toggleFeature(feature) {
      const btn = this.panel.querySelector(`[data-feature="${feature}"]`);
      const isActive = document.body.classList.contains(`a11y-${feature}`);
      
      if (isActive) {
        document.body.classList.remove(`a11y-${feature}`);
        btn.classList.remove('active');
        localStorage.removeItem(`a11y-${feature}`);
      } else {
        document.body.classList.add(`a11y-${feature}`);
        btn.classList.add('active');
        localStorage.setItem(`a11y-${feature}`, 'true');
      }
      
      this.announce(`${feature} ${isActive ? 'disabled' : 'enabled'}`);
    },
    
    resetAll() {
      ['contrast', 'font-size', 'dyslexia', 'motion'].forEach(feature => {
        document.body.classList.remove(`a11y-${feature}`);
        const btn = this.panel.querySelector(`[data-feature="${feature}"]`);
        if (btn) btn.classList.remove('active');
        localStorage.removeItem(`a11y-${feature}`);
      });
      this.announce('All accessibility settings reset');
    },
    
    loadPreferences() {
      ['contrast', 'font-size', 'dyslexia', 'motion'].forEach(feature => {
        if (localStorage.getItem(`a11y-${feature}`)) {
          document.body.classList.add(`a11y-${feature}`);
          const btn = this.panel.querySelector(`[data-feature="${feature}"]`);
          if (btn) btn.classList.add('active');
        }
      });
    },
    
    announce(message) {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.className = 'sr-only';
      announcement.textContent = message;
      document.body.appendChild(announcement);
      
      setTimeout(() => {
        document.body.removeChild(announcement);
      }, 1000);
    }
  };
  
  // Add accessibility CSS
  const accessibilityStyles = document.createElement('style');
  accessibilityStyles.textContent = `
    .a11y-contrast {
      --color-background: #000000 !important;
      --color-text: #ffffff !important;
      --color-primary: #ffff00 !important;
      --color-secondary: #00ff00 !important;
      --color-border: #ffffff !important;
      --color-surface: #333333 !important;
    }
    
    .a11y-font-size {
      font-size: 1.2em !important;
    }
    
    .a11y-dyslexia {
      font-family: 'OpenDyslexic', 'Comic Sans MS', cursive !important;
      letter-spacing: 0.12em !important;
      word-spacing: 0.16em !important;
      line-height: 1.8 !important;
    }
    
    .a11y-motion * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  `;
  document.head.appendChild(accessibilityStyles);
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AccessibilityPanel.init());
  } else {
    AccessibilityPanel.init();
  }
  
})();