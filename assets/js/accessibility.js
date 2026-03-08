// Accessibility controls and enhancements
// User-controlled accessibility features

(function() {
  'use strict';
  
  // =============================================================================
  // ACCESSIBILITY PREFERENCES
  // =============================================================================
  
  const AccessibilityControls = {
    // Storage keys for user preferences
    STORAGE_KEYS: {
      HIGH_CONTRAST: 'disability-ai-high-contrast',
      LARGE_FONT: 'disability-ai-large-font',
      REDUCED_MOTION: 'disability-ai-reduced-motion',
      DYSLEXIA_FRIENDLY: 'disability-ai-dyslexia-friendly'
    },
    
    // Initialize accessibility controls
    init: function() {
      this.createControlsPanel();
      this.loadUserPreferences();
      this.initHighContrastToggle();
      this.initFontSizeToggle();
      this.initDyslexiaToggle();
      this.initReducedMotionToggle();
      this.initKeyboardShortcuts();
    },
    
    // Create accessibility controls panel
    createControlsPanel: function() {
      const existingControls = document.querySelector('.accessibility-controls-panel');
      if (existingControls) return;
      
      const panel = document.createElement('div');
      panel.className = 'accessibility-controls-panel';
      panel.setAttribute('role', 'region');
      panel.setAttribute('aria-label', 'Accessibility Controls');
      
      panel.innerHTML = `
        <button class="a11y-panel-toggle" aria-expanded="false" aria-controls="a11y-panel-content">
          <span class="a11y-panel-toggle__icon" aria-hidden="true">♿</span>
          <span class="a11y-panel-toggle__text">Accessibility</span>
        </button>
        <div id="a11y-panel-content" class="a11y-panel-content" hidden>
          <h3 class="a11y-panel-title">Accessibility Options</h3>
          <div class="a11y-controls-grid">
            <button id="contrast-toggle" class="a11y-control-btn" aria-pressed="false">
              <span class="a11y-control-icon" aria-hidden="true">🔆</span>
              <span class="a11y-control-text">High Contrast</span>
            </button>
            <button id="font-size-toggle" class="a11y-control-btn" aria-pressed="false">
              <span class="a11y-control-icon" aria-hidden="true">🔍</span>
              <span class="a11y-control-text">Large Font</span>
            </button>
            <button id="dyslexia-toggle" class="a11y-control-btn" aria-pressed="false">
              <span class="a11y-control-icon" aria-hidden="true">📖</span>
              <span class="a11y-control-text">Dyslexia Friendly</span>
            </button>
            <button id="motion-toggle" class="a11y-control-btn" aria-pressed="false">
              <span class="a11y-control-icon" aria-hidden="true">⏸️</span>
              <span class="a11y-control-text">Reduce Motion</span>
            </button>
          </div>
          <button class="a11y-reset-btn">Reset All Settings</button>
        </div>
      `;
      
      document.body.appendChild(panel);
      this.initPanelToggle();
      this.addPanelStyles();
    },
    
    // Add CSS for accessibility panel
    addPanelStyles: function() {
      const existingStyles = document.getElementById('a11y-panel-styles');
      if (existingStyles) return;
      
      const styles = document.createElement('style');
      styles.id = 'a11y-panel-styles';
      styles.textContent = `
        .accessibility-controls-panel {
          position: fixed;
          top: 50%;
          right: 20px;
          transform: translateY(-50%);
          z-index: 1000;
        }
        
        .a11y-panel-toggle {
          background: var(--color-primary);
          color: var(--color-background);
          border: none;
          border-radius: 50%;
          width: 60px;
          height: 60px;
          cursor: pointer;
          box-shadow: var(--shadow-lg);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 2px;
          transition: all var(--transition-fast);
        }
        
        .a11y-panel-toggle:hover {
          background: var(--color-secondary);
          transform: scale(1.05);
        }
        
        .a11y-panel-toggle:focus {
          outline: 3px solid var(--color-accent);
          outline-offset: 2px;
        }
        
        .a11y-panel-toggle__icon {
          font-size: 20px;
          line-height: 1;
        }
        
        .a11y-panel-toggle__text {
          font-size: 10px;
          font-weight: 500;
          line-height: 1;
        }
        
        .a11y-panel-content {
          position: absolute;
          right: 70px;
          top: 0;
          background: var(--color-background);
          border: 2px solid var(--color-primary);
          border-radius: var(--border-radius);
          box-shadow: var(--shadow-lg);
          padding: var(--space-lg);
          min-width: 250px;
        }
        
        .a11y-panel-title {
          margin: 0 0 var(--space-md) 0;
          font-size: var(--font-size-h5);
          color: var(--color-primary);
        }
        
        .a11y-controls-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-sm);
          margin-bottom: var(--space-lg);
        }
        
        .a11y-control-btn {
          background: var(--color-light);
          border: 2px solid var(--color-border);
          border-radius: var(--border-radius);
          padding: var(--space-sm);
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-xs);
          transition: all var(--transition-fast);
        }
        
        .a11y-control-btn:hover {
          border-color: var(--color-primary);
          background: var(--color-background);
        }
        
        .a11y-control-btn:focus {
          outline: 3px solid var(--color-accent);
          outline-offset: 2px;
        }
        
        .a11y-control-btn[aria-pressed="true"] {
          background: var(--color-primary);
          color: var(--color-background);
          border-color: var(--color-primary);
        }
        
        .a11y-control-icon {
          font-size: 18px;
        }
        
        .a11y-control-text {
          font-size: 12px;
          font-weight: 500;
          text-align: center;
          line-height: 1.2;
        }
        
        .a11y-reset-btn {
          background: var(--color-muted);
          color: var(--color-background);
          border: none;
          border-radius: var(--border-radius);
          padding: var(--space-sm) var(--space-md);
          font-size: 14px;
          cursor: pointer;
          width: 100%;
          transition: background var(--transition-fast);
        }
        
        .a11y-reset-btn:hover {
          background: var(--color-text);
        }
        
        .a11y-reset-btn:focus {
          outline: 3px solid var(--color-accent);
          outline-offset: 2px;
        }
        
        @media (max-width: 768px) {
          .accessibility-controls-panel {
            right: 10px;
          }
          
          .a11y-panel-content {
            right: 0;
            left: -200px;
            width: 250px;
          }
        }
      `;
      
      document.head.appendChild(styles);
    },
    
    // Initialize panel toggle
    initPanelToggle: function() {
      const toggle = document.querySelector('.a11y-panel-toggle');
      const panel = document.getElementById('a11y-panel-content');
      
      if (!toggle || !panel) return;
      
      toggle.addEventListener('click', function() {
        const isOpen = toggle.getAttribute('aria-expanded') === 'true';
        const newState = !isOpen;
        
        toggle.setAttribute('aria-expanded', newState.toString());
        panel.hidden = !newState;
        
        if (newState) {
          // Focus first button in panel
          const firstButton = panel.querySelector('.a11y-control-btn');
          if (firstButton) firstButton.focus();
        }
      });
      
      // Close panel when clicking outside
      document.addEventListener('click', function(event) {
        if (!toggle.contains(event.target) && !panel.contains(event.target)) {
          toggle.setAttribute('aria-expanded', 'false');
          panel.hidden = true;
        }
      });
      
      // Close panel on escape
      document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && !panel.hidden) {
          toggle.setAttribute('aria-expanded', 'false');
          panel.hidden = true;
          toggle.focus();
        }
      });
      
      // Reset button functionality
      const resetBtn = panel.querySelector('.a11y-reset-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => this.resetAllSettings());
      }
    },
    
    // High contrast toggle
    initHighContrastToggle: function() {
      const toggle = document.getElementById('contrast-toggle');
      if (!toggle) return;
      
      toggle.addEventListener('click', () => {
        const isEnabled = document.body.classList.contains('high-contrast-mode');
        this.toggleHighContrast(!isEnabled);
      });
    },
    
    toggleHighContrast: function(enable) {
      const toggle = document.getElementById('contrast-toggle');
      
      if (enable) {
        document.body.classList.add('high-contrast-mode');
        if (toggle) toggle.setAttribute('aria-pressed', 'true');
        localStorage.setItem(this.STORAGE_KEYS.HIGH_CONTRAST, 'true');
        this.announceChange('High contrast mode enabled');
      } else {
        document.body.classList.remove('high-contrast-mode');
        if (toggle) toggle.setAttribute('aria-pressed', 'false');
        localStorage.removeItem(this.STORAGE_KEYS.HIGH_CONTRAST);
        this.announceChange('High contrast mode disabled');
      }
    },
    
    // Font size toggle
    initFontSizeToggle: function() {
      const toggle = document.getElementById('font-size-toggle');
      if (!toggle) return;
      
      toggle.addEventListener('click', () => {
        const isEnabled = document.body.classList.contains('large-font');
        this.toggleLargeFont(!isEnabled);
      });
    },
    
    toggleLargeFont: function(enable) {
      const toggle = document.getElementById('font-size-toggle');
      
      if (enable) {
        document.body.classList.add('large-font');
        if (toggle) toggle.setAttribute('aria-pressed', 'true');
        localStorage.setItem(this.STORAGE_KEYS.LARGE_FONT, 'true');
        this.announceChange('Large font mode enabled');
      } else {
        document.body.classList.remove('large-font');
        if (toggle) toggle.setAttribute('aria-pressed', 'false');
        localStorage.removeItem(this.STORAGE_KEYS.LARGE_FONT);
        this.announceChange('Large font mode disabled');
      }
    },
    
    // Dyslexia-friendly toggle
    initDyslexiaToggle: function() {
      const toggle = document.getElementById('dyslexia-toggle');
      if (!toggle) return;
      
      toggle.addEventListener('click', () => {
        const isEnabled = document.body.classList.contains('dyslexia-friendly');
        this.toggleDyslexiaFriendly(!isEnabled);
      });
    },
    
    toggleDyslexiaFriendly: function(enable) {
      const toggle = document.getElementById('dyslexia-toggle');
      
      if (enable) {
        document.body.classList.add('dyslexia-friendly');
        if (toggle) toggle.setAttribute('aria-pressed', 'true');
        localStorage.setItem(this.STORAGE_KEYS.DYSLEXIA_FRIENDLY, 'true');
        this.announceChange('Dyslexia-friendly mode enabled');
      } else {
        document.body.classList.remove('dyslexia-friendly');
        if (toggle) toggle.setAttribute('aria-pressed', 'false');
        localStorage.removeItem(this.STORAGE_KEYS.DYSLEXIA_FRIENDLY);
        this.announceChange('Dyslexia-friendly mode disabled');
      }
    },
    
    // Reduced motion toggle
    initReducedMotionToggle: function() {
      const toggle = document.getElementById('motion-toggle');
      if (!toggle) return;
      
      toggle.addEventListener('click', () => {
        const isEnabled = document.body.classList.contains('reduced-motion');
        this.toggleReducedMotion(!isEnabled);
      });
    },
    
    toggleReducedMotion: function(enable) {
      const toggle = document.getElementById('motion-toggle');
      
      if (enable) {
        document.body.classList.add('reduced-motion');
        if (toggle) toggle.setAttribute('aria-pressed', 'true');
        localStorage.setItem(this.STORAGE_KEYS.REDUCED_MOTION, 'true');
        this.announceChange('Reduced motion mode enabled');
      } else {
        document.body.classList.remove('reduced-motion');
        if (toggle) toggle.setAttribute('aria-pressed', 'false');
        localStorage.removeItem(this.STORAGE_KEYS.REDUCED_MOTION);
        this.announceChange('Reduced motion mode disabled');
      }
    },
    
    // Keyboard shortcuts for accessibility features
    initKeyboardShortcuts: function() {
      document.addEventListener('keydown', (event) => {
        // Ctrl + Alt combinations for accessibility
        if (event.ctrlKey && event.altKey) {
          switch (event.key) {
            case 'c':
              event.preventDefault();
              const contrastEnabled = document.body.classList.contains('high-contrast-mode');
              this.toggleHighContrast(!contrastEnabled);
              break;
            case 'f':
              event.preventDefault();
              const fontEnabled = document.body.classList.contains('large-font');
              this.toggleLargeFont(!fontEnabled);
              break;
            case 'd':
              event.preventDefault();
              const dyslexiaEnabled = document.body.classList.contains('dyslexia-friendly');
              this.toggleDyslexiaFriendly(!dyslexiaEnabled);
              break;
            case 'm':
              event.preventDefault();
              const motionEnabled = document.body.classList.contains('reduced-motion');
              this.toggleReducedMotion(!motionEnabled);
              break;
            case 'a':
              event.preventDefault();
              const panelToggle = document.querySelector('.a11y-panel-toggle');
              if (panelToggle) panelToggle.click();
              break;
          }
        }
      });
    },
    
    // Load user preferences from localStorage
    loadUserPreferences: function() {
      // High contrast
      if (localStorage.getItem(this.STORAGE_KEYS.HIGH_CONTRAST)) {
        this.toggleHighContrast(true);
      }
      
      // Large font
      if (localStorage.getItem(this.STORAGE_KEYS.LARGE_FONT)) {
        this.toggleLargeFont(true);
      }
      
      // Dyslexia-friendly
      if (localStorage.getItem(this.STORAGE_KEYS.DYSLEXIA_FRIENDLY)) {
        this.toggleDyslexiaFriendly(true);
      }
      
      // Reduced motion
      if (localStorage.getItem(this.STORAGE_KEYS.REDUCED_MOTION)) {
        this.toggleReducedMotion(true);
      }
    },
    
    // Reset all accessibility settings
    resetAllSettings: function() {
      this.toggleHighContrast(false);
      this.toggleLargeFont(false);
      this.toggleDyslexiaFriendly(false);
      this.toggleReducedMotion(false);
      this.announceChange('All accessibility settings reset');
    },
    
    // Announce changes to screen readers
    announceChange: function(message) {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.className = 'sr-only';
      announcement.textContent = message;
      
      document.body.appendChild(announcement);
      
      // Remove after screen reader processes it
      setTimeout(() => {
        if (document.body.contains(announcement)) {
          document.body.removeChild(announcement);
        }
      }, 1000);
    }
  };
  
  // =============================================================================
  // INITIALIZATION
  // =============================================================================
  
  function init() {
    // Initialize accessibility controls
    AccessibilityControls.init();
    
    // Respect user's system preferences
    if (window.matchMedia('(prefers-contrast: high)').matches) {
      AccessibilityControls.toggleHighContrast(true);
    }
    
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      AccessibilityControls.toggleReducedMotion(true);
    }
    
    // Listen for changes in system preferences
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    contrastQuery.addEventListener('change', (event) => {
      if (event.matches) {
        AccessibilityControls.toggleHighContrast(true);
      }
    });
    
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    motionQuery.addEventListener('change', (event) => {
      AccessibilityControls.toggleReducedMotion(event.matches);
    });
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Export for external use
  window.AccessibilityControls = AccessibilityControls;
  
})();