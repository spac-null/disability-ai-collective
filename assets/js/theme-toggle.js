/**
 * Theme Toggle - Professional Dark/Light Mode Implementation
 * Disability-AI Collective Design System v2.0
 */

class ThemeManager {
  constructor() {
    this.storageKey = 'disability-ai-theme';
    this.themeToggle = document.getElementById('theme-toggle');
    this.sunIcon = this.themeToggle?.querySelector('.sun');
    this.moonIcon = this.themeToggle?.querySelector('.moon');
    
    this.init();
  }

  init() {
    // Initialize theme based on user preference or saved state
    const savedTheme = localStorage.getItem(this.storageKey);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    this.setTheme(initialTheme);
    this.updateIcon(initialTheme);
    
    // Set up event listeners
    if (this.themeToggle) {
      this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem(this.storageKey)) {
        this.setTheme(e.matches ? 'dark' : 'light');
        this.updateIcon(e.matches ? 'dark' : 'light');
      }
    });
  }

  setTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark-theme');
    } else {
      document.documentElement.classList.remove('dark-theme');
    }
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.content = theme === 'dark' ? '#2b2b2f' : '#fef9f2';
    } else {
      const meta = document.createElement('meta');
      meta.name = 'theme-color';
      meta.content = theme === 'dark' ? '#2b2b2f' : '#fef9f2';
      document.head.appendChild(meta);
    }
  }

  updateIcon(theme) {
    if (!this.sunIcon || !this.moonIcon) return;
    
    if (theme === 'dark') {
      this.sunIcon.style.display = 'none';
      this.moonIcon.style.display = 'block';
      this.themeToggle.setAttribute('aria-label', 'Switch to light theme');
      this.themeToggle.title = 'Switch to light theme';
    } else {
      this.sunIcon.style.display = 'block';
      this.moonIcon.style.display = 'none';
      this.themeToggle.setAttribute('aria-label', 'Switch to dark theme');
      this.themeToggle.title = 'Switch to dark theme';
    }
  }

  toggleTheme() {
    const currentTheme = document.documentElement.classList.contains('dark-theme') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    this.setTheme(newTheme);
    this.updateIcon(newTheme);
    
    // Save preference
    localStorage.setItem(this.storageKey, newTheme);
    
    // Announce to screen readers
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = `Theme switched to ${newTheme} mode`;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }

  getCurrentTheme() {
    return document.documentElement.classList.contains('dark-theme') ? 'dark' : 'light';
  }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});
