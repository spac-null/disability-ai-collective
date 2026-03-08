/* GENERATIVE ARTWORK SYSTEM */
/* Algorithmic SVG generation inspired by disability culture + Urbit aesthetics */

class GenerativeArt {
  constructor() {
    this.colors = {
      neural: ['#000000', '#0066cc', '#00ffff'],
      spatial: ['#ccff00', '#ff69b4'],
      pattern: ['#ff6600', '#0066cc'],
      void: ['#000000', '#333333', '#666666']
    };
    this.init();
  }
  
  init() {
    this.generateAgentAvatars();
    this.generateHeroBackground();
    this.generatePatternElements();
  }
  
  // Agent Avatar Generation
  generateAgentAvatars() {
    const agents = [
      { id: 'siri', type: 'neural', symbol: '👁️‍🗨️' },
      { id: 'pixel', type: 'spatial', symbol: '🤟' },
      { id: 'maya', type: 'pattern', symbol: '♿' },
      { id: 'zen', type: 'void', symbol: '🧠' }
    ];
    
    agents.forEach(agent => {
      const avatar = this.createAvatar(agent);
      const container = document.querySelector(`[data-agent="${agent.id}"] .agent-avatar`);
      if (container) {
        container.innerHTML = avatar;
      }
    });
  }
  
  createAvatar(agent) {
    const size = 64;
    const patterns = this.generatePattern(agent.type, size);
    
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <defs>
          ${this.generateGradients(agent.type)}
          ${patterns}
        </defs>
        <rect width="100%" height="100%" fill="url(#gradient-${agent.type})"/>
        <use href="#pattern-${agent.type}" opacity="0.3"/>
        <text x="50%" y="55%" text-anchor="middle" font-size="24" fill="white" text-shadow="0 2px 4px rgba(0,0,0,0.5)">
          ${agent.symbol}
        </text>
      </svg>
    `;
  }
  
  generateGradients(type) {
    const colors = this.colors[type];
    if (!colors) return '';
    
    switch(type) {
      case 'neural':
        return `
          <linearGradient id="gradient-neural" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="${colors[0]}"/>
            <stop offset="50%" stop-color="${colors[1]}"/>
            <stop offset="100%" stop-color="${colors[2]}"/>
          </linearGradient>
        `;
      case 'spatial':
        return `
          <linearGradient id="gradient-spatial" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="${colors[0]}"/>
            <stop offset="100%" stop-color="${colors[1]}"/>
          </linearGradient>
        `;
      case 'pattern':
        return `
          <linearGradient id="gradient-pattern" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="${colors[0]}"/>
            <stop offset="100%" stop-color="${colors[1]}"/>
          </linearGradient>
        `;
      case 'void':
        return `
          <radialGradient id="gradient-void" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="${colors[0]}"/>
            <stop offset="100%" stop-color="${colors[2]}"/>
          </radialGradient>
        `;
      default:
        return '';
    }
  }
  
  generatePattern(type, size) {
    const unit = size / 8;
    
    switch(type) {
      case 'neural':
        return `
          <pattern id="pattern-neural" x="0" y="0" width="${unit * 2}" height="${unit * 2}" patternUnits="userSpaceOnUse">
            <circle cx="${unit}" cy="${unit}" r="${unit * 0.3}" fill="white" opacity="0.2"/>
            <line x1="0" y1="${unit}" x2="${unit * 2}" y2="${unit}" stroke="white" stroke-width="1" opacity="0.1"/>
          </pattern>
        `;
      case 'spatial':
        return `
          <pattern id="pattern-spatial" x="0" y="0" width="${unit * 3}" height="${unit * 3}" patternUnits="userSpaceOnUse">
            <rect x="${unit}" y="${unit}" width="${unit}" height="${unit}" fill="white" opacity="0.15"/>
            <polygon points="${unit * 0.5},${unit * 0.5} ${unit * 1.5},${unit * 0.5} ${unit},${unit * 1.5}" fill="white" opacity="0.1"/>
          </pattern>
        `;
      case 'pattern':
        return `
          <pattern id="pattern-pattern" x="0" y="0" width="${unit * 4}" height="${unit * 4}" patternUnits="userSpaceOnUse">
            <path d="M 0,${unit * 2} Q ${unit * 2},0 ${unit * 4},${unit * 2}" stroke="white" stroke-width="2" fill="none" opacity="0.2"/>
            <circle cx="${unit * 2}" cy="${unit * 2}" r="${unit * 0.5}" fill="white" opacity="0.15"/>
          </pattern>
        `;
      case 'void':
        return `
          <pattern id="pattern-void" x="0" y="0" width="${unit}" height="${unit}" patternUnits="userSpaceOnUse">
            <rect x="0" y="0" width="${unit * 0.5}" height="${unit * 0.5}" fill="white" opacity="0.05"/>
            <rect x="${unit * 0.5}" y="${unit * 0.5}" width="${unit * 0.5}" height="${unit * 0.5}" fill="white" opacity="0.05"/>
          </pattern>
        `;
      default:
        return '';
    }
  }
  
  // Hero Background Generation
  generateHeroBackground() {
    const heroElement = document.querySelector('.hero');
    if (!heroElement) return;
    
    const svg = this.createHeroArt();
    const backgroundDiv = document.createElement('div');
    backgroundDiv.className = 'hero-generative-bg';
    backgroundDiv.style.cssText = `
      position: absolute;
      inset: 0;
      opacity: 0.1;
      z-index: -1;
      pointer-events: none;
    `;
    backgroundDiv.innerHTML = svg;
    
    heroElement.style.position = 'relative';
    heroElement.appendChild(backgroundDiv);
  }
  
  createHeroArt() {
    const width = 1200;
    const height = 600;
    const nodes = this.generateNetworkNodes(12);
    
    return `
      <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="network-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0066cc" stop-opacity="0.3"/>
            <stop offset="50%" stop-color="#00ffff" stop-opacity="0.1"/>
            <stop offset="100%" stop-color="#ccff00" stop-opacity="0.2"/>
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        <!-- Network connections -->
        ${this.generateConnections(nodes)}
        
        <!-- Network nodes -->
        ${nodes.map(node => `
          <circle cx="${node.x}" cy="${node.y}" r="${node.r}" 
                  fill="url(#network-gradient)" 
                  filter="url(#glow)"
                  opacity="${node.opacity}">
            <animate attributeName="r" values="${node.r};${node.r * 1.5};${node.r}" 
                     dur="${node.duration}s" repeatCount="indefinite"/>
          </circle>
        `).join('')}
        
        <!-- Algorithmic patterns -->
        ${this.generateAlgorithmicShapes(width, height)}
      </svg>
    `;
  }
  
  generateNetworkNodes(count) {
    const nodes = [];
    for (let i = 0; i < count; i++) {
      nodes.push({
        x: Math.random() * 1200,
        y: Math.random() * 600,
        r: 3 + Math.random() * 8,
        opacity: 0.3 + Math.random() * 0.4,
        duration: 2 + Math.random() * 4
      });
    }
    return nodes;
  }
  
  generateConnections(nodes) {
    let connections = '';
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const distance = Math.sqrt(
          Math.pow(nodes[i].x - nodes[j].x, 2) + 
          Math.pow(nodes[i].y - nodes[j].y, 2)
        );
        
        if (distance < 200) {
          connections += `
            <line x1="${nodes[i].x}" y1="${nodes[i].y}" 
                  x2="${nodes[j].x}" y2="${nodes[j].y}" 
                  stroke="url(#network-gradient)" 
                  stroke-width="1" 
                  opacity="${0.6 - distance / 300}"/>
          `;
        }
      }
    }
    return connections;
  }
  
  generateAlgorithmicShapes(width, height) {
    const shapes = [];
    
    // Fibonacci spiral
    shapes.push(`
      <path d="M ${width * 0.8} ${height * 0.2} 
               Q ${width * 0.9} ${height * 0.3} ${width * 0.85} ${height * 0.4}
               Q ${width * 0.7} ${height * 0.5} ${width * 0.6} ${height * 0.3}"
            stroke="#0066cc" stroke-width="2" fill="none" opacity="0.3"/>
    `);
    
    // Golden ratio rectangles
    shapes.push(`
      <rect x="${width * 0.1}" y="${height * 0.7}" width="89" height="55" 
            stroke="#ccff00" stroke-width="1" fill="none" opacity="0.2"/>
      <rect x="${width * 0.05}" y="${height * 0.6}" width="55" height="34" 
            stroke="#ff69b4" stroke-width="1" fill="none" opacity="0.2"/>
    `);
    
    return shapes.join('');
  }
  
  // Pattern Elements for Cards
  generatePatternElements() {
    const cards = document.querySelectorAll('.generative-card');
    cards.forEach((card, index) => {
      const pattern = this.createCardPattern(index);
      const patternDiv = document.createElement('div');
      patternDiv.className = 'card-pattern';
      patternDiv.style.cssText = `
        position: absolute;
        inset: 0;
        opacity: 0.05;
        z-index: -1;
        pointer-events: none;
      `;
      patternDiv.innerHTML = pattern;
      
      card.style.position = 'relative';
      card.appendChild(patternDiv);
    });
  }
  
  createCardPattern(index) {
    const patterns = [
      this.createGridPattern(),
      this.createCirclePattern(),
      this.createWavePattern(),
      this.createTrianglePattern()
    ];
    
    return patterns[index % patterns.length];
  }
  
  createGridPattern() {
    return `
      <svg width="100%" height="100%" viewBox="0 0 100 100">
        <defs>
          <pattern id="grid-pattern" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#0066cc" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid-pattern)"/>
      </svg>
    `;
  }
  
  createCirclePattern() {
    return `
      <svg width="100%" height="100%" viewBox="0 0 100 100">
        <defs>
          <pattern id="circle-pattern" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="10" cy="10" r="3" fill="none" stroke="#ccff00" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#circle-pattern)"/>
      </svg>
    `;
  }
  
  createWavePattern() {
    return `
      <svg width="100%" height="100%" viewBox="0 0 100 100">
        <defs>
          <pattern id="wave-pattern" x="0" y="0" width="40" height="20" patternUnits="userSpaceOnUse">
            <path d="M 0 10 Q 10 0 20 10 Q 30 20 40 10" fill="none" stroke="#ff69b4" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#wave-pattern)"/>
      </svg>
    `;
  }
  
  createTrianglePattern() {
    return `
      <svg width="100%" height="100%" viewBox="0 0 100 100">
        <defs>
          <pattern id="triangle-pattern" x="0" y="0" width="15" height="15" patternUnits="userSpaceOnUse">
            <polygon points="7.5,2 13,13 2,13" fill="none" stroke="#ff6600" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#triangle-pattern)"/>
      </svg>
    `;
  }
}

// Initialize generative art system
document.addEventListener('DOMContentLoaded', () => {
  const generativeArt = new GenerativeArt();
  
  // Regenerate patterns on resize (debounced)
  let resizeTimeout;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      generativeArt.generateHeroBackground();
    }, 250);
  });
});

// Logo Animation System
class LogoAnimation {
  constructor() {
    this.init();
  }
  
  init() {
    const logo = document.querySelector('.site-title');
    if (!logo) return;
    
    logo.innerHTML = this.createAnimatedLogo(logo.textContent);
  }
  
  createAnimatedLogo(text) {
    const letters = text.split('').map((letter, i) => {
      if (letter === ' ') return ' ';
      return `<span style="animation-delay: ${i * 0.1}s" class="logo-letter">${letter}</span>`;
    }).join('');
    
    return `
      <span class="logo-generative">
        ${letters}
      </span>
    `;
  }
}

// Initialize logo animation
document.addEventListener('DOMContentLoaded', () => {
  new LogoAnimation();
});

// Add CSS for logo letters
const logoStyles = `
  .logo-letter {
    display: inline-block;
    animation: float-letter 3s ease-in-out infinite alternate;
  }
  
  @keyframes float-letter {
    0% { transform: translateY(0px); }
    100% { transform: translateY(-2px); }
  }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = logoStyles;
document.head.appendChild(styleSheet);