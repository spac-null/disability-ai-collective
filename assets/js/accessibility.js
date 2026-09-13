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

function getInitialTheme() {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === 'dark' || savedTheme === 'light') {
    return savedTheme;
  }

  const legacyTheme = localStorage.getItem(LEGACY_THEME_STORAGE_KEY);
  if (legacyTheme === 'true' || legacyTheme === 'false') {
    return legacyTheme === 'true' ? 'dark' : 'light';
  }

  return 'light';
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
    toggle.textContent = isDark ? 'Light Theme' : 'Dark Theme';
    toggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
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

// WHERE THE CONTROLS LIVE.
//
// On desktop they are floating pills in the corner, which is fine: there is room beside
// the reading column. On a phone there is no beside -- they were pinned over the top of
// the article and covered the text they were meant to help someone read.
//
// So on narrow screens the SAME two buttons move into the header menu, where the rest of
// the navigation already is. They are moved, never duplicated: the elements keep their
// own listeners, aria-pressed state, labels and keyboard behaviour, and nothing about
// what the controls do changes -- only where they sit.
const NAV_BREAKPOINT = '(max-width: 768px)';

function accessibilityControls() {
  return [
    document.getElementById('theme-toggle'),
    document.querySelector('.dyslexia-toggle')
  ].filter(Boolean);
}

function placeAccessibilityControls() {
  const menu = document.getElementById('site-nav-menu');
  const controls = accessibilityControls();
  if (!menu || !controls.length) {
    return;
  }

  let slot = document.getElementById('site-nav-a11y');

  if (window.matchMedia(NAV_BREAKPOINT).matches) {
    if (!slot) {
      slot = document.createElement('li');
      slot.id = 'site-nav-a11y';
      slot.className = 'site-nav__a11y';
      menu.appendChild(slot);
    }
    controls.forEach(function(el) {
      if (el.parentNode !== slot) {
        slot.appendChild(el);
      }
    });
  } else {
    controls.forEach(function(el) {
      if (el.parentNode !== document.body) {
        document.body.appendChild(el);
      }
    });
    if (slot) {
      slot.remove();
    }
  }
}

document.addEventListener('DOMContentLoaded', function() {
  createFallbackThemeToggle();
  createDyslexiaToggle();
  placeAccessibilityControls();
  announceToScreenReader(`Page loaded: ${document.title}`);
});

// Rotating a phone, or resizing a desktop window across the breakpoint, must put the
// controls back where they belong rather than leaving them in the wrong place.
if (window.matchMedia) {
  const mq = window.matchMedia(NAV_BREAKPOINT);
  const onChange = function() { placeAccessibilityControls(); };
  if (mq.addEventListener) {
    mq.addEventListener('change', onChange);
  } else if (mq.addListener) {
    mq.addListener(onChange);
  }
}
