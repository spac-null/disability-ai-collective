  'adaptive': [
        'Pixel art study of adaptive systems',
        'Retro visualization of accessibility patterns',
        'Digital interpretation of flow and movement'
      ],
      'acoustic': [
        'Pixelated sound wave visualization',
        '8-bit interpretation of acoustic space',
        'Digital echolocation mapping'
      ],
      'abstract': [
        'Generative pixel art exploration',
        'Algorithmic digital composition',
        'Procedural retro artwork'
      ]
    };
    
    const themeCaptions = captions[theme] || captions.abstract;
    return themeCaptions[imageIndex - 1] || themeCaptions[0];
  }

  // Create fallback image if generation fails
  createFallbackImage(agentName, index) {
    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');
    
    const palette = this.generator.getAgentPalette(agentName);
    
    // Simple gradient fallback
    const gradient = ctx.createLinearGradient(0, 0, 800, 400);
    gradient.addColorStop(0, palette.dark);
    gradient.addColorStop(1, palette.accent);
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 800, 400);
    
    // Add text
    ctx.fillStyle = palette.light;
    ctx.font = 'bold 48px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('PIXEL ART', 400, 200);
    ctx.font = '24px monospace';
    ctx.fillText(agentName, 400, 250);
    
    return {
      dataUrl: canvas.toDataURL('image/png'),
      caption: `Fallback pixel art for ${agentName}`,
      alt: `Fallback image for ${agentName} article`,
      theme: 'fallback',
      technique: 'gradient'
    };
  }

  // Insert images into markdown content
  insertImagesIntoMarkdown(markdownContent, images) {
    if (!images || images.length === 0) return markdownContent;
    
    let enhancedMarkdown = markdownContent;
    const sections = markdownContent.split('\n## ');
    
    // Insert images at strategic points
    images.forEach((image, index) => {
      const imageMarkdown = `\n\n![${image.alt}](${image.dataUrl})\n\n*${image.caption}*\n\n`;
      
      // Try to insert after paragraphs or at section breaks
      if (sections.length > index + 1) {
        // Insert after section header
        sections[index + 1] = imageMarkdown + sections[index + 1];
      } else {
        // Append at the end
        enhancedMarkdown += imageMarkdown;
      }
    });
    
    return sections.join('\n## ');
  }
}

// Export for use in cron jobs
window.ArticleImageManager = ArticleImageManager;
window.AdvancedPixelArtGenerator = AdvancedPixelArtGenerator;

console.log('🎨 Advanced Pixel Art Generator loaded - ready for article integration');