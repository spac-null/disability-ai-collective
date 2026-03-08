/* ACCESSIBILITY FEATURES */

// High Contrast Toggle
document.addEventListener('DOMContentLoaded', function() {
  function createContrastToggle() {
    const toggle = document.createElement('button');
    toggle.textContent = 'High Contrast';
    toggle.className = 'contrast-toggle';
    toggle.setAttribute('aria-label', 'Toggle high contrast mode');
    toggle.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 20px;
      background: var(--color-black);
      color: var(--color-white);
      border: 1px solid var(--color-black);
      padding: 8px 12px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      z-index: 1000;
    `;
    
    const isHighContrast = localStorage.getItem('high-contrast') === 'true';
    if (isHighContrast) {
      document.body.style.filter = 'contrast(2)';
      toggle.textContent = 'Normal Contrast';
    }
    
    toggle.addEventListener('click', function() {
      const currentlyHighContrast = document.body.style.filter === 'contrast(2)';
      
      if (currentlyHighContrast) {
        document.body.style.filter = '';
        toggle.textContent = 'High Contrast';
        localStorage.setItem('high-contrast', 'false');
      } else {
        document.body.style.filter = 'contrast(2)';
        toggle.textContent = 'Normal Contrast';
        localStorage.setItem('high-contrast', 'true');
      }
    });
    
    document.body.appendChild(toggle);
  }
  
  createContrastToggle();
});

// Dyslexia-Friendly Font Toggle
document.addEventListener('DOMContentLoaded', function() {
  const savedFont = localStorage.getItem('dyslexia-font');
  
  if (savedFont === 'true') {
    document.body.classList.add('dyslexia-friendly');
  }
  
  // Add toggle to accessibility page if it exists
  const accessibilityPage = document.body.querySelector('main h1');
  if (accessibilityPage && accessibilityPage.textContent.includes('Accessibility')) {
    const toggle = document.createElement('button');
    toggle.textContent = 'Toggle Dyslexia Font';
    toggle.className = 'btn btn--outline';
    toggle.style.marginTop = '20px';
    
    toggle.addEventListener('click', function() {
      const isActive = document.body.classList.contains('dyslexia-friendly');
      
      if (isActive) {
        document.body.classList.remove('dyslexia-friendly');
        localStorage.setItem('dyslexia-font', 'false');
      } else {
        document.body.classList.add('dyslexia-friendly');
        localStorage.setItem('dyslexia-font', 'true');
      }
    });
    
    accessibilityPage.parentNode.appendChild(toggle);
  }
});

// Announce page changes to screen readers
document.addEventListener('DOMContentLoaded', function() {
  const pageTitle = document.title;
  
  // Create announcement for screen readers
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.className = 'visually-hidden';
  announcement.textContent = `Page loaded: ${pageTitle}`;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(function() {
    if (document.body.contains(announcement)) {
      document.body.removeChild(announcement);
    }
  }, 2000);
});