/* ACCESSIBILITY FEATURES - SUPPORT TOGGLES & ANNOUNCEMENTS */

const THEME_STORAGE_KEY = 'disability-ai-theme';
const LEGACY_THEME_STORAGE_KEY = 'dark-theme';
const DYSLEXIA_STORAGE_KEY = 'dyslexia-font';

function announceToScreenReader(message) {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  setTimeout(function() {
    if (document.body.contains(announcement)) {
      document.body.removeChild(announcement);
    }
  }, 2000);
}

function hasSavedThemePreference() {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  const legacyTheme = localStorage.getItem(LEGACY_THEME_STORAGE_KEY);

  return savedTheme === 'dark' || savedTheme === 'light' || legacyTheme === 'true' || legacyTheme === 'false';
}

function getInitialTheme() {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === 'dark' || savedTheme === 'light') {
    return savedTheme;
  }

  const legacyTheme = localStorage.getItem(LEGACY_THEME_STORAGE_KEY);
  if (legacyTheme === 'true' || legacyTheme === 'false') {
    return legacyTheme === 'true' ? 'dark' : 'light';
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
  document.documentElement.classList.toggle('dark-theme', theme === 'dark');
}

function persistTheme(theme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  localStorage.setItem(LEGACY_THEME_STORAGE_KEY, theme === 'dark' ? 'true' : 'false');
}

function createFallbackThemeToggle() {
  if (document.getElementById('theme-toggle') || document.querySelector('.dark-theme-toggle')) {
    return;
  }

  const toggle = document.createElement('button');
  toggle.className = 'accessibility-toggle dark-theme-toggle';
  toggle.type = 'button';
  toggle.setAttribute('aria-label', 'Toggle dark theme');

  const updateToggleLabel = function(theme) {
    const isDark = theme === 'dark';
    toggle.innerHTML = isDark ? '☀️ Light' : '🌙 Dark';
    toggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
  };

  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);
  updateToggleLabel(initialTheme);

  toggle.addEventListener('click', function() {
    const currentTheme = document.documentElement.classList.contains('dark-theme') ? 'dark' : 'light';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';

    applyTheme(nextTheme);
    persistTheme(nextTheme);
    updateToggleLabel(nextTheme);
    announceToScreenReader(`Switched to ${nextTheme} theme`);
  });

  const prefersDarkQuery = window.matchMedia('(prefers-color-scheme: dark)');
  if (!hasSavedThemePreference()) {
    prefersDarkQuery.addEventListener('change', function(event) {
      const nextTheme = event.matches ? 'dark' : 'light';
      applyTheme(nextTheme);
      updateToggleLabel(nextTheme);
    });
  }

  document.body.appendChild(toggle);
}

function createDyslexiaToggle() {
  if (document.querySelector('.dyslexia-toggle')) {
    return;
  }

  const toggle = document.createElement('button');
  toggle.className = 'accessibility-toggle dyslexia-toggle';
  toggle.type = 'button';
  toggle.setAttribute('aria-label', 'Toggle dyslexia-friendly font');

  const isDyslexiaEnabled = localStorage.getItem(DYSLEXIA_STORAGE_KEY) === 'true';
  document.documentElement.classList.toggle('dyslexia-friendly', isDyslexiaEnabled);
  toggle.innerHTML = isDyslexiaEnabled ? '📖 Normal' : '🔤 Dyslexia';
  toggle.setAttribute('aria-pressed', isDyslexiaEnabled ? 'true' : 'false');

  toggle.addEventListener('click', function() {
    const currentlyEnabled = document.documentElement.classList.contains('dyslexia-friendly');
    const nextEnabled = !currentlyEnabled;

    document.documentElement.classList.toggle('dyslexia-friendly', nextEnabled);
    localStorage.setItem(DYSLEXIA_STORAGE_KEY, String(nextEnabled));
    toggle.innerHTML = nextEnabled ? '📖 Normal' : '🔤 Dyslexia';
    toggle.setAttribute('aria-pressed', nextEnabled ? 'true' : 'false');

    announceToScreenReader(`Switched to ${nextEnabled ? 'dyslexia-friendly' : 'normal'} font`);
  });

  document.body.appendChild(toggle);
}

document.addEventListener('DOMContentLoaded', function() {
  createFallbackThemeToggle();
  createDyslexiaToggle();
  announceToScreenReader(`Page loaded: ${document.title}`);
});
