#!/usr/bin/env python3
"""
SOPHISTICATED CONTENT-AWARE IMAGE GENERATOR (PATTERN-BASED)
- Analyzes article content to understand themes
- Generates diverse, sophisticated patterns based on analysis
- Creates unique, visually rich images without external AI models
"""

import math
import random
import struct
import zlib
import re
import hashlib
from pathlib import Path
from PIL import Image # Ensure PIL is available

class SophisticatedContentAwareImageGenerator:
    def __init__(self, width=800, height=450):
        self.width = width
        self.height = height
        self.grid_width = width
        self.grid_height = height
        
        self.palettes = {
            'architectural': [
                (25, 30, 40), (50, 65, 85), (85, 105, 125), (120, 140, 160),
                (160, 175, 190), (200, 210, 220), (70, 150, 200), (200, 120, 60), (100, 180, 90),
            ],
            'navigation': [
                (20, 25, 35), (40, 55, 70), (80, 95, 110), (120, 135, 150),
                (180, 190, 200), (220, 225, 230), (255, 200, 60), (60, 180, 120), (180, 60, 60),
            ],
            'technology': [
                (15, 20, 30), (30, 45, 60), (60, 80, 100), (100, 120, 140),
                (150, 165, 180), (200, 210, 220), (100, 150, 255), (255, 150, 100), (150, 255, 150),
            ],
            'cultural': [
                (30, 25, 35), (60, 45, 55), (90, 75, 85), (130, 115, 125),
                (170, 155, 165), (210, 195, 205), (180, 100, 140), (140, 180, 100), (100, 140, 180),
            ]
        }

    def analyze_content(self, content, title):
        """Analyze article content to determine themes and context."""
        content_lower = (content + ' ' + title).lower()
        
        analysis = {
            'primary_theme': 'architectural',  # default
            'disability_perspective': 'general',
            'complexity_level': 'medium'
        }
        
        # Detect primary theme
        if any(word in content_lower for word in ['building', 'space', 'office', 'architecture', 'acoustic', 'sound', 'echo', 'design']):
            analysis['primary_theme'] = 'architectural'
        elif any(word in content_lower for word in ['transport', 'navigation', 'station', 'street', 'route', 'mobility', 'wheelchair', 'barrier']):
            analysis['primary_theme'] = 'navigation'
        elif any(word in content_lower for word in ['technology', 'interface', 'digital', 'screen', 'app', 'software', 'system', 'pattern']):
            analysis['primary_theme'] = 'technology'
        elif any(word in content_lower for word in ['culture', 'film', 'art', 'entertainment', 'oscar', 'hollywood', 'media', 'caption']):
            analysis['primary_theme'] = 'cultural'
        
        # Detect disability perspective
        if any(word in content_lower for word in ['deaf', 'hearing', 'visual', 'sign', 'caption', 'audio']):
            analysis['disability_perspective'] = 'deaf_visual'
        elif any(word in content_lower for word in ['blind', 'sight', 'spatial', 'touch', 'acoustic', 'echo']):
            analysis['disability_perspective'] = 'blind_spatial'
        elif any(word in content_lower for word in ['wheelchair', 'mobility', 'navigation', 'barrier', 'access']):
            analysis['disability_perspective'] = 'mobility'
        elif any(word in content_lower for word in ['autistic', 'neurodivergent', 'sensory']):
            analysis['disability_perspective'] = 'neurodivergent'
        
        # Detect complexity level
        if any(word in content_lower for word in ['complex', 'chaos', 'interference', 'overlapping', 'multiple']):
            analysis['complexity_level'] = 'high'
        elif any(word in content_lower for word in ['simple', 'clear', 'minimal', 'basic']):
            analysis['complexity_level'] = 'low'
        
        return analysis

    def generate_article_specific_image(self, article_content, title, image_type="concept"):
        """
        Generate a unique, context-aware image based on article content and type.
        Returns PIL Image object.
        """
        analysis = self.analyze_content(article_content, title)
        palette = self.palettes[analysis['primary_theme']]
        
        # Create deterministic seed from article content
        seed_hash = hashlib.md5((article_content + title + image_type).encode()).hexdigest()
        seed_int = int(seed_hash[:8], 16)
        random.seed(seed_int)
        
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        if image_type == "concept":
            self._generate_concept_pattern(grid, palette, seed_int, analysis)
        elif image_type == "context":
            self._generate_context_pattern(grid, palette, seed_int, analysis)
        else: # solution
            self._generate_solution_pattern(grid, palette, seed_int, analysis)
            
        return self._grid_to_pil_image(grid, palette)

    def _generate_concept_pattern(self, grid, palette, seed, analysis):
        """Generate primary concept pattern based on analysis."""
        random.seed(seed)
        
        # Use themes to influence patterns
        if analysis['primary_theme'] == 'architectural':
            self._create_acoustic_chaos_pattern(grid, palette, seed, analysis['complexity_level'])
        elif analysis['primary_theme'] == 'navigation':
            self._create_navigation_grid_pattern(grid, palette, seed, analysis['complexity_level'])
        elif analysis['primary_theme'] == 'technology':
            self._create_interface_flow_pattern(grid, palette, seed, analysis['complexity_level'])
        else: # cultural
            self._create_media_layer_pattern(grid, palette, seed, analysis['complexity_level'])
        
        # Add a central element related to disability perspective
        if analysis['disability_perspective'] == 'deaf_visual':
            self._add_visual_sound_wave(grid, palette, seed)
        elif analysis['disability_perspective'] == 'mobility':
            self._add_pathway_focus(grid, palette, seed)

    def _generate_context_pattern(self, grid, palette, seed, analysis):
        """Generate real-world context illustration based on analysis."""
        random.seed(seed + 1) # Different seed for context
        
        if analysis['primary_theme'] == 'architectural':
            self._create_disrupted_building_elements(grid, palette, seed, analysis['complexity_level'])
        elif analysis['primary_theme'] == 'navigation':
            self._create_urban_barriers_pattern(grid, palette, seed, analysis['complexity_level'])
        elif analysis['primary_theme'] == 'technology':
            self._create_broken_interface_pattern(grid, palette, seed, analysis['complexity_level'])
        else: # cultural
            self._create_fragmented_media_pattern(grid, palette, seed, analysis['complexity_level'])

    def _generate_solution_pattern(self, grid, palette, seed, analysis):
        """Generate solution vision based on analysis."""
        random.seed(seed + 2) # Different seed for solution
        
        if analysis['primary_theme'] == 'architectural':
            self._create_acoustic_harmony_pattern(grid, palette, seed, analysis['complexity_level'])
        elif analysis['primary_theme'] == 'navigation':
            self._create_accessible_flow_pattern(grid, palette, seed, analysis['complexity_level'])
        elif analysis['primary_theme'] == 'technology':
            self._create_inclusive_interface_pattern(grid, palette, seed, analysis['complexity_level'])
        else: # cultural
            self._create_integrated_media_pattern(grid, palette, seed, analysis['complexity_level'])

    # --- Core Pattern Generation Methods (influenced by seed and analysis) ---
    def _create_acoustic_chaos_pattern(self, grid, palette, seed, complexity):
        # Similar to previous acoustic chaos but with more randomized parameters based on seed
        random.seed(seed)
        wave_count = random.randint(5, 10) if complexity == 'high' else 3
        sources = []
        for _ in range(wave_count):
            sources.append({
                'x': random.uniform(0.1, 0.9) * self.grid_width,
                'y': random.uniform(0.1, 0.9) * self.grid_height,
                'frequency': random.uniform(0.01, 0.1),
                'amplitude': random.uniform(1, 5),
                'phase': random.uniform(0, math.pi * 2)
            })
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                total_wave = 0
                for source in sources:
                    distance = math.sqrt((x - source['x'])**2 + (y - source['y'])**2)
                    wave = source['amplitude'] * math.sin(distance * source['frequency'] + source['phase'])
                    total_wave += wave
                
                normalized = (total_wave + wave_count * 3) / (wave_count * 6)
                normalized = max(0, min(1, normalized))
                color_idx = int(normalized * (len(palette) - 1))
                grid[y][x] = color_idx
        
        self._add_disrupted_structures(grid, palette, seed, complexity)

    def _create_navigation_grid_pattern(self, grid, palette, seed, complexity):
        random.seed(seed)
        # Grid of pathways with randomized turns and obstacles
        for y in range(0, self.grid_height, 10):
            for x in range(0, self.grid_width, 10):
                color_idx = (x // 10 + y // 10 + seed) % len(palette)
                grid[y][x] = color_idx
                
                # Add paths
                if random.random() < 0.7:
                    for i in range(10):
                        if x+i < self.grid_width: grid[y][x+i] = color_idx
                if random.random() < 0.7:
                    for i in range(10):
                        if y+i < self.grid_height: grid[y+i][x] = color_idx
        
        if complexity == 'high':
            self._add_random_obstacles(grid, palette, seed)

    def _create_interface_flow_pattern(self, grid, palette, seed, complexity):
        random.seed(seed)
        # Layers of interface elements with data flow lines
        layer_count = random.randint(3, 6)
        
        for layer in range(layer_count):
            intensity = (layer + seed) % len(palette)
            for _ in range(random.randint(5, 15)):
                x = random.randint(0, self.grid_width - 1)
                y = random.randint(0, self.grid_height - 1)
                size = random.randint(10, 40)
                self._draw_filled_rect(grid, x, y, size, size, intensity)
        
        if complexity == 'high':
            self._add_data_flow_lines(grid, palette, seed)

    def _create_media_layer_pattern(self, grid, palette, seed, complexity):
        random.seed(seed)
        # Overlapping media layers, some distorted or with gaps
        for _ in range(random.randint(5, 10)):
            x = random.randint(0, self.grid_width - 50)
            y = random.randint(0, self.grid_height - 50)
            width = random.randint(100, self.grid_width // 2)
            height = random.randint(100, self.grid_height // 2)
            color_idx = random.randint(0, len(palette) - 1)
            
            self._draw_filled_rect(grid, x, y, width, height, color_idx)
            
            if complexity == 'high' and random.random() < 0.4: # Add distortion/gaps
                self._add_media_distortion(grid, palette, x, y, width, height, seed)

    # --- Disability-Specific Elements ---
    def _add_visual_sound_wave(self, grid, palette, seed):
        random.seed(seed)
        # Draw a prominent sound wave pattern
        start_y = self.grid_height // 2
        for x in range(self.grid_width):
            wave_y = int(start_y + math.sin(x * 0.1 + seed * 0.01) * 20)
            if 0 <= wave_y < self.grid_height:
                grid[wave_y][x] = (seed % 3) + 6 # Accent color
                if x % 5 == 0: # Add visual pulses
                    for i in range(5): grid[max(0, wave_y-i)][x] = (seed % 3) + 6

    def _add_pathway_focus(self, grid, palette, seed):
        random.seed(seed)
        # Highlight an accessible pathway
        center_x = random.randint(self.grid_width // 4, self.grid_width * 3 // 4)
        center_y = random.randint(self.grid_height // 4, self.grid_height * 3 // 4)
        
        for y in range(max(0, center_y-20), min(self.grid_height, center_y+20)):
            for x in range(max(0, center_x-80), min(self.grid_width, center_x+80)):
                if (x + y + seed) % 5 < 2: # Light pattern
                    grid[y][x] = 5 # Lightest color
                elif (x + y + seed) % 10 == 0: # Accent marks
                    grid[y][x] = (seed % 3) + 6

    # --- Helper drawing functions ---
    def _draw_filled_rect(self, grid, x, y, width, height, color_idx):
        for dy in range(height):
            for dx in range(width):
                if (x + dx < self.grid_width and 
                    y + dy < self.grid_height and
                    x + dx >=0 and y+dy >= 0):
                    grid[y + dy][x + dx] = color_idx

    # --- PNG Utility ---
    def _grid_to_pil_image(self, grid, palette):
        """Convert color grid to PIL Image object."""
        pixels = []
        for grid_y in range(self.grid_height):
            row = []
            for grid_x in range(self.grid_width):
                color_idx = grid[grid_y][grid_x]
                color = palette[color_idx % len(palette)]
                row.extend(color)  # RGB values
            pixels.append(tuple(row))
        
        img = Image.new('RGB', (self.width, self.height))
        img.putdata([item for sublist in pixels for item in sublist]) # Flatten list
        
        return img


# --- Orchestration for article image generation ---
def generate_enhanced_images_for_all_articles():
    """Generate enhanced content-aware images for all articles."""
    print("🚀 GENERATING ENHANCED CONTENT-AWARE IMAGES FOR ALL ARTICLES (Pattern-Based)")
    print("=" * 60)
    
    posts_dir = Path('_posts')
    assets_dir = Path('assets')
    
    generator = SophisticatedContentAwareImageGenerator(width=800, height=450)
    
    article_files = sorted([f for f in os.listdir(posts_dir) if f.startswith('2026-03-') and f.endswith('.md')])
    
    for article_file in article_files:
        print(f"\n🎨 Processing: {article_file}")
        
        # Read article content
        with open(posts_dir / article_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'title:\s*["\']([^"\']+)["\']', content)
        title = title_match.group(1) if title_match else article_file
        
        # Extract slug
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', article_file)
        slug = re.sub(r'\.md$', '', slug)
        
        print(f"   Title: {title}")
        
        # Generate 3 unique images
        for i, img_type in enumerate(['concept', 'context', 'solution']):
            filename = f"{slug}_{img_type}_{i+1}.png"
            filepath = assets_dir / filename
            
            # Create unique image based on article content and type
            image = generator.generate_article_specific_image(content, title, img_type)
            
            # Save image
            image.save(filepath, 'PNG', quality=95)
            file_size = os.path.getsize(filepath)
            print(f"   ✅ {filename} - {file_size/1024:.1f}KB")
        
        # Update frontmatter
        if f"image: /assets/{slug}_concept_1.png" not in content:
            content = re.sub(
                r'image:\s*/assets/[^\n]+',
                f'image: /assets/{slug}_concept_1.png',
                content
            )
            with open(posts_dir / article_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   🔄 Updated frontmatter image")
    
    print(f"\n✅ ENHANCED GENERATION COMPLETE!")
    print(f"   Articles processed: {len(article_files)}")
    print(f"   Images generated: {len(article_files) * 3}")


if __name__ == "__main__":
    generate_enhanced_images_for_all_articles()