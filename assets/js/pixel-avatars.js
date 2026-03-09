/* URBIT-STYLE PIXEL AVATAR GENERATOR */
/* Clean algorithmic avatars inspired by Urbit's sigil system */

class UrbitAvatarGenerator {
  constructor() {
    this.size = 48;
    this.gridSize = 12;
    this.pixelSize = this.size / this.gridSize;
  }

  generateAvatar(agentName, element) {
    const canvas = document.createElement('canvas');
    canvas.width = this.size;
    canvas.height = this.size;
    const ctx = canvas.getContext('2d');
    
    // Get agent-specific colors and patterns
    const colors = this.getAgentPalette(agentName);
    const seed = this.hashString(agentName);
    const pattern = this.generateSymmetricPattern(seed, agentName);
    
    // Render with crisp pixels
    ctx.imageSmoothingEnabled = false;
    
    // Background
    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, this.size, this.size);
    
    // Pattern
    this.renderPattern(ctx, pattern, colors);
    
    // Replace emoji with pixel art
    element.innerHTML = '';
    element.appendChild(canvas);
  }

  hashString(str) {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) + hash) + str.charCodeAt(i);
    }
    return Math.abs(hash);
  }

  generateSymmetricPattern(seed, agentName) {
    const rng = this.seededRandom(seed);
    const halfWidth = Math.floor(this.gridSize / 2);
    const pattern = [];
    
    for (let y = 0; y < this.gridSize; y++) {
      pattern[y] = [];
      for (let x = 0; x < halfWidth; x++) {
        // Agent-specific pattern logic
        const value = this.getPatternValue(x, y, agentName, rng);
        pattern[y][x] = value;
        // Mirror symmetrically
        pattern[y][this.gridSize - 1 - x] = value;
      }
      // Handle center column for odd grid sizes
      if (this.gridSize % 2 === 1) {
        pattern[y][halfWidth] = this.getPatternValue(halfWidth, y, agentName, rng);
      }
    }
    
    return pattern;
  }

  getPatternValue(x, y, agentName, rng) {
    const centerX = this.gridSize / 2;
    const centerY = this.gridSize / 2;
    const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
    const maxDist = Math.sqrt(centerX ** 2 + centerY ** 2);
    const normalizedDist = distance / maxDist;
    
    // Agent-specific algorithms
    switch (agentName) {
      case 'Siri Sage':
        // Concentric rings like sound waves
        const ringPattern = Math.sin(distance * 1.5) > 0;
        return ringPattern && rng() > 0.3 ? 1 : 0;
        
      case 'Pixel Nova':
        // Angular, geometric patterns
        const angle = Math.atan2(y - centerY, x - centerX);
        const segments = Math.floor((angle + Math.PI) / (Math.PI / 3)) % 2;
        return segments && distance > 2 && distance < 5 ? 1 : 0;
        
      case 'Maya Flux':
        // Flowing, organic curves
        const wave = Math.sin(x * 0.8) + Math.cos(y * 0.8);
        return wave > 0 && normalizedDist < 0.8 ? 1 : 0;
        
      case 'Zen Circuit':
        // Complex cellular automata-like pattern
        const cellular = (x + y) % 3 === 0 || (x * y) % 5 === 0;
        return cellular && rng() > 0.4 ? 1 : 0;
        
      default:
        return rng() > 0.5 ? 1 : 0;
    }
  }

  renderPattern(ctx, pattern, colors) {
    for (let y = 0; y < this.gridSize; y++) {
      for (let x = 0; x < this.gridSize; x++) {
        if (pattern[y][x]) {
          ctx.fillStyle = colors.fg;
          ctx.fillRect(
            x * this.pixelSize,
            y * this.pixelSize,
            this.pixelSize,
            this.pixelSize
          );
        }
      }
    }
  }

  getAgentPalette(agentName) {
    // Access CSS variables from the document's root
    const getCssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

    const palettes = {
      'Siri Sage': {
        bg: getCssVar('--color-neutral-900'), // Dark background
        fg: getCssVar('--color-primary-300')  // Primary color for pattern
      },
      'Pixel Nova': {
        bg: getCssVar('--color-neutral-800'),
        fg: getCssVar('--color-secondary-300')
      },
      'Maya Flux': {
        bg: getCssVar('--color-primary-800'),
        fg: getCssVar('--color-error-300') // Using error for a vibrant, distinct color
      },
      'Zen Circuit': {
        bg: getCssVar('--color-secondary-900'),
        fg: getCssVar('--color-info-300') // Using info for another distinct color
      }
    };
    
    return palettes[agentName] || { bg: getCssVar('--color-neutral-700'), fg: getCssVar('--color-primary-500') };
  }

  seededRandom(seed) {
    let value = seed;
    return function() {
      value = (value * 9301 + 49297) % 233280;
      return value / 233280;
    };
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  const generator = new UrbitAvatarGenerator();
  const agentCards = document.querySelectorAll('.generative-card');
  const agentNames = ['Siri Sage', 'Pixel Nova', 'Maya Flux', 'Zen Circuit'];
  
  agentCards.forEach((card, index) => {
    const avatar = card.querySelector('.agent-avatar');
    if (avatar && agentNames[index]) {
      generator.generateAvatar(agentNames[index], avatar);
    }
  });
  
  console.log('🎨 Generated Urbit-style pixel avatars for', agentNames.length, 'agents');
});