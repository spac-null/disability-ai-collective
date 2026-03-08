/* ACCESSIBILITY FEATURES - DARK THEME & ACCESSIBILITY TOGGLES */

// Dark Theme Toggle (replaces "High Contrast")
document.addEventListener('DOMContentLoaded', function() {
  function createDarkThemeToggle() {
    const toggle = document.createElement('button');
    toggle.className = 'accessibility-toggle dark-theme-toggle';
    toggle.setAttribute('aria-label', 'Toggle dark theme');
    
    // Check saved preference
    const isDarkTheme = localStorage.getItem('dark-theme') === 'true' || 
                       window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (isDarkTheme) {
      document.documentElement.classList.add('dark-theme');
      toggle.innerHTML = '☀️ Light';
      toggle.setAttribute('aria-pressed', 'true');
    } else {
      toggle.innerHTML = '🌙 Dark';
      toggle.setAttribute('aria-pressed', 'false');
    }
    
    toggle.addEventListener('click', function() {
      const currentlyDark = document.documentElement.classList.contains('dark-theme');
      
      if (currentlyDark) {
        document.documentElement.classList.remove('dark-theme');
        toggle.innerHTML = '🌙 Dark';
        toggle.setAttribute('aria-pressed', 'false');
        localStorage.setItem('dark-theme', 'false');
      } else {
        document.documentElement.classList.add('dark-theme');
        toggle.innerHTML = '☀️ Light';
        toggle.setAttribute('aria-pressed', 'true');
        localStorage.setItem('dark-theme', 'true');
      }
      
      // Announce change to screen readers
      announceToScreenReader(`Switched to ${currentlyDark ? 'light' : 'dark'} theme`);
    });
    
    document.body.appendChild(toggle);
  }
  
  // Dyslexia-Friendly Font Toggle
  function createDyslexiaToggle() {
    const toggle = document.createElement('button');
    toggle.className = 'accessibility-toggle dyslexia-toggle';
    toggle.setAttribute('aria-label', 'Toggle dyslexia-friendly font');
    
    const isDyslexiaFont = localStorage.getItem('dyslexia-font') === 'true';
    
    if (isDyslexiaFont) {
      document.documentElement.classList.add('dyslexia-friendly');
      toggle.innerHTML = '📖 Normal';
      toggle.setAttribute('aria-pressed', 'true');
    } else {
      toggle.innerHTML = '🔤 Dyslexia';
      toggle.setAttribute('aria-pressed', 'false');
    }
    
    toggle.addEventListener('click', function() {
      const currentlyDyslexia = document.documentElement.classList.contains('dyslexia-friendly');
      
      if (currentlyDyslexia) {
        document.documentElement.classList.remove('dyslexia-friendly');
        toggle.innerHTML = '🔤 Dyslexia';
        toggle.setAttribute('aria-pressed', 'false');
        localStorage.setItem('dyslexia-font', 'false');
      } else {
        document.documentElement.classList.add('dyslexia-friendly');
        toggle.innerHTML = '📖 Normal';
        toggle.setAttribute('aria-pressed', 'true');
        localStorage.setItem('dyslexia-font', 'true');
      }
      
      announceToScreenReader(`Switched to ${currentlyDyslexia ? 'normal' : 'dyslexia-friendly'} font`);
    });
    
    document.body.appendChild(toggle);
  }
  
  // Create both toggles
  createDarkThemeToggle();
  createDyslexiaToggle();
});

// Screen reader announcements
function announceToScreenReader(message) {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'visually-hidden';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(function() {
    if (document.body.contains(announcement)) {
      document.body.removeChild(announcement);
    }
  }, 2000);
}

// Page change announcements for screen readers
document.addEventListener('DOMContentLoaded', function() {
  const pageTitle = document.title;
  announceToScreenReader(`Page loaded: ${pageTitle}`);
});

// Respect system preferences
document.addEventListener('DOMContentLoaded', function() {
  // Auto-apply dark theme if user prefers it and hasn't set preference
  if (localStorage.getItem('dark-theme') === null) {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.classList.add('dark-theme');
      localStorage.setItem('dark-theme', 'true');
    }
  }
  
  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    if (localStorage.getItem('dark-theme') === null) {
      if (e.matches) {
        document.documentElement.classList.add('dark-theme');
      } else {
        document.documentElement.classList.remove('dark-theme');
      }
    }
  });
});