#!/usr/bin/env python3
"""
UNIQUE ARTICLE IMAGE GENERATOR
Creates truly unique images for each article based on article content
"""

import os
import re
import hashlib
import math
import random
import struct
import zlib
from pathlib import Path

class UniqueArticleImageGenerator:
    def __init__(self, width=800, height=450):
        self.width = width
        self.height = height
        self.grid_width = width
        self.grid_height = height
        
        # Sophisticated color palettes
        self.palettes = [
            # Palette 1: Architectural/Professional
            [
                (25, 30, 40),    # Deep charcoal
                (50, 65, 85),    # Steel blue
                (85, 105, 125),  # Medium slate
                (120, 140, 160), # Light steel
                (160, 175, 190), # Cool gray
                (200, 210, 220), # Soft white
                (70, 150, 200),  # Architecture blue
                (200, 120, 60),  # Warm accent
                (100, 180, 90),  # Life green
            ],
            # Palette 2: Technology/Digital
            [
                (15, 20, 30),    # Screen black
                (30, 45, 60),    # Device dark
                (60, 80, 100),   # Interface gray
                (100, 120, 140), # UI medium
                (150, 165, 180), # Text gray
                (200, 210, 220), # Background
                (100, 150, 255), # Link blue
                (255, 150, 100), # Accent orange
                (150, 255, 150), # Success green
            ],
            # Palette 3: Cultural/Arts
            [
                (30, 25, 35),    # Theater dark
                (60, 45, 55),    # Velvet deep
                (90, 75, 85),    # Cultural medium
                (130, 115, 125), # Gallery gray
                (170, 155, 165), # Exhibition light
                (210, 195, 205), # Museum white
                (180, 100, 140), # Arts magenta
                (140, 180, 100), # Creative lime
                (100, 140, 180), # Culture blue
            ]
        ]

    def create_article_specific_image(self, article_content, image_type="concept"):
        """Create a unique image based on article content."""
        # Create deterministic seed from article content
        seed_hash = hashlib.md5((article_content + image_type).encode()).hexdigest()
        seed_int = int(seed_hash[:8], 16)
        
        # Use seed to determine parameters
        random.seed(seed_int)
        
        # Select palette based on content
        palette_idx = seed_int % len(self.palettes)
        palette = self.palettes[palette_idx]
        
        # Create grid
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Generate unique pattern based on article content and image type
        if image_type == "concept":
            self._generate_concept_pattern(grid, palette, seed_int)
        elif image_type == "context":
            self._generate_context_pattern(grid, palette, seed_int)
        else:  # solution
            self._generate_solution_pattern(grid, palette, seed_int)
        
        return self._grid_to_png(grid, palette)

    def _generate_concept_pattern(self, grid, palette, seed):
        """Generate primary concept pattern."""
        random.seed(seed)
        
        # Create wave interference pattern with unique parameters
        wave_count = random.randint(3, 8)
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

    def _generate_context_pattern(self, grid, palette, seed):
        """Generate context pattern."""
        random.seed(seed + 1)  # Different seed
        
        # Create architectural/structural pattern
        structure_count = random.randint(4, 7)
        
        for _ in range(structure_count):
            x = random.randint(50, self.grid_width - 100)
            y = random.randint(30, self.grid_height - 60)
            width = random.randint(40, 80)
            height = random.randint(20, 50)
            
            # Draw structure
            for dy in range(height):
                for dx in range(width):
                    if x + dx < self.grid_width and y + dy < self.grid_height:
                        # Vary color based on position
                        color_idx = (dx + dy + seed) % len(palette)
                        grid[y + dy][x + dx] = color_idx

    def _generate_solution_pattern(self, grid, palette, seed):
        """Generate solution pattern."""
        random.seed(seed + 2)  # Different seed
        
        # Create harmonious/flow pattern
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Calculate distance from center
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Create radial pattern
                angle = math.atan2(dy, dx)
                pattern_value = math.sin(distance * 0.05 + angle * 2 + seed * 0.01)
                
                normalized = (pattern_value + 1) / 2  # Convert to 0-1 range
                color_idx = int(normalized * (len(palette) - 1))
                grid[y][x] = color_idx

    def _grid_to_png(self, grid, palette):
        """Convert color grid to PNG data."""
        pixels = []
        for grid_y in range(self.grid_height):
            row = []
            for grid_x in range(self.grid_width):
                color_idx = grid[grid_y][grid_x]
                color = palette[color_idx % len(palette)]
                row.extend(color)  # RGB values
            pixels.append(row)
        
        return self._create_png_rgb(pixels)

    def _create_png_rgb(self, pixels):
        """Create RGB PNG file data."""
        height = len(pixels)
        width = len(pixels[0]) // 3  # Each pixel has 3 values (RGB)
        
        # PNG signature
        png_data = b'\\x89PNG\\r\\n\\x1a\\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)  # RGB color
        png_data += struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data
        png_data += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
        
        # IDAT chunk
        image_data = b''
        for row in pixels:
            image_data += b'\\x00'  # Filter type (None)
            image_data += bytes(row)
        
        compressed_data = zlib.compress(image_data)
        png_data += struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data
        png_data += struct.pack('>I', zlib.crc32(b'IDAT' + compressed_data) & 0xffffffff)
        
        # IEND chunk
        png_data += struct.pack('>I', 0) + b'IEND'
        png_data += struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
        
        return png_data

def regenerate_truly_unique_images():
    """Regenerate truly unique images for all articles."""
    print("🔄 Regenerating TRULY UNIQUE images for all articles...")
    
    generator = UniqueArticleImageGenerator(width=800, height=450)
    posts_dir = Path('_posts')
    assets_dir = Path('assets')
    
    article_files = sorted([f for f in os.listdir(posts_dir) if f.startswith('2026-03-') and f.endswith('.md')])
    
    for article_file in article_files:
        print(f"\n🎨 Processing: {article_file}")
        
        # Read article content
        with open(posts_dir / article_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract slug
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', article_file)
        slug = re.sub(r'\.md$', '', slug)
        
        print(f"   Slug: {slug}")
        
        # Generate 3 unique images
        for i, img_type in enumerate(['concept', 'context', 'solution']):
            filename = f"{slug}_{img_type}_{i+1}.png"
            filepath = assets_dir / filename
            
            # Create unique image based on article content
            png_data = generator.create_article_specific_image(content, img_type)
            
            with open(filepath, 'wb') as f:
                f.write(png_data)
            
            file_size = os.path.getsize(filepath)
            print(f"   ✅ {filename} - {file_size/1024:.1f}KB")
        
        # Update frontmatter if needed
        if f"image: /assets/{slug}_concept_1.png" not in content:
            content = re.sub(
                r'image:\s*/assets/[^\n]+',
                f'image: /assets/{slug}_concept_1.png',
                content
            )
            with open(posts_dir / article_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   🔄 Updated frontmatter image")
    
    print(f"\n✅ Regeneration complete! {len(article_files)} articles processed.")

if __name__ == "__main__":
    regenerate_truly_unique_images()