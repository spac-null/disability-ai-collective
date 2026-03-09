#!/usr/bin/env python3
"""
Enhanced Procedural Pixel Art Generator for Disability-AI Collective
Generates multiple themed pixel art images based on article content
Uses only standard library - no external dependencies needed
"""

import math
import random
import struct
import zlib

class ArticlePixelArtSuite:
    def __init__(self, width=400, height=300, pixel_size=8):
        self.width = width
        self.height = height 
        self.pixel_size = pixel_size
        self.grid_width = width // pixel_size
        self.grid_height = height // pixel_size
    
    def generate_from_keywords(self, keywords, mood, agent_perspective):
        """Generate pixel art based on article analysis"""
        
        # Map keywords to visual patterns
        patterns = []
        if any(word in keywords for word in ['sound', 'acoustic', 'audio', 'hearing']):
            patterns.append('waves')
        if any(word in keywords for word in ['visual', 'spatial', 'gesture', 'sign']):
            patterns.append('spirals')
        if any(word in keywords for word in ['access', 'barrier', 'navigation', 'path']):
            patterns.append('pathways')
        if any(word in keywords for word in ['neurodivergent', 'pattern', 'complex', 'thinking']):
            patterns.append('complex')
        if any(word in keywords for word in ['architecture', 'building', 'space', 'design']):
            patterns.append('geometric')
        
        # Default to complex patterns if nothing matches
        if not patterns:
            patterns = ['complex']
            
        # Generate primary image based on dominant theme
        primary_pattern = patterns[0]
        
        images = []
        
        # Generate 2-3 images per article
        if primary_pattern == 'waves':
            images.append(self._generate_wave_architecture())
        elif primary_pattern == 'spirals':
            images.append(self._generate_spatial_cognition())
        elif primary_pattern == 'pathways':
            images.append(self._generate_accessibility_paths())
        elif primary_pattern == 'complex':
            images.append(self._generate_complex_patterns())
        elif primary_pattern == 'geometric':
            images.append(self._generate_architectural_forms())
            
        # Add complementary pattern if multiple themes
        if len(patterns) > 1:
            if patterns[1] == 'waves':
                images.append(self._generate_sound_visualization())
            elif patterns[1] == 'spirals':
                images.append(self._generate_movement_flow())
            elif patterns[1] == 'pathways':
                images.append(self._generate_barrier_navigation())
                
        # Mood-based third image
        if mood in ['contemplative', 'reflective', 'deep']:
            images.append(self._generate_meditation_pattern())
        elif mood in ['energetic', 'dynamic', 'active']:
            images.append(self._generate_energy_pattern())
        elif mood in ['challenging', 'critical', 'sharp']:
            images.append(self._generate_edge_pattern())
            
        return images[:3]  # Limit to 3 images max
    
    def _generate_wave_architecture(self):
        """Sound waves meeting architectural forms"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Sound wave interference
                wave1 = math.sin(x * 0.3) * math.cos(y * 0.2)
                wave2 = math.sin(y * 0.4) * math.cos(x * 0.15)
                interference = wave1 + wave2 + math.sin((x + y) * 0.1)
                
                # Architectural elements
                building_column = x % 8 == 0 and y > self.grid_height * 0.4
                ground_level = y > self.grid_height * 0.7
                sound_zones = interference > 0.3
                
                grid[y][x] = 1 if building_column or ground_level or sound_zones else 0
                
        return self._grid_to_png_data(grid, "Acoustic Architecture - Sound waves meeting built space")
    
    def _generate_spatial_cognition(self):
        """Visual-spatial thinking patterns"""
        grid = self._create_grid()
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                angle = math.atan2(y - center_y, x - center_x)
                spiral = math.sin(dist * 0.5 + angle * 3)
                
                # Concentric rings with spiral modulation
                in_ring = (dist % 4 < 1.5) or spiral > 0.2
                grid[y][x] = 1 if in_ring else 0
                
        return self._grid_to_png_data(grid, "Visual-Spatial Cognition - Spiral thought patterns")
    
    def _generate_accessibility_paths(self):
        """Navigation pathways through barriers"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Create systematic barriers
                barrier = (x % 6 == 0 or y % 8 == 0) and random.random() > 0.3
                
                # Clear accessibility pathways
                pathway_x = x in [self.grid_width//3, 2*self.grid_width//3]
                pathway_y = y % 12 < 4
                
                grid[y][x] = 1 if barrier and not (pathway_x or pathway_y) else 0
                
        return self._grid_to_png_data(grid, "Accessibility Pathways - Clear routes through barriers")
    
    def _generate_complex_patterns(self):
        """Neurodivergent thinking - complex interconnected patterns"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Multiple overlapping mathematical patterns
                p1 = math.sin(x * 0.4) * math.cos(y * 0.3)
                p2 = math.sin(x * 0.2 + y * 0.2)
                p3 = math.cos((x + y) * 0.15)
                fibonacci = math.sin(x * 0.618) + math.cos(y * 1.618)
                
                combined = p1 + p2 + p3 + fibonacci
                active = combined > 1.0 or (combined > 0.5 and random.random() > 0.6)
                grid[y][x] = 1 if active else 0
                
        return self._grid_to_png_data(grid, "Complex Patterns - Interconnected thinking networks")
    
    def _generate_architectural_forms(self):
        """Clean geometric architectural forms"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Geometric building forms
                structure = False
                
                # Vertical towers
                if x % 12 < 4 and y > self.grid_height * 0.3:
                    structure = True
                
                # Horizontal platforms
                if y % 10 == 0 and x % 8 < 6:
                    structure = True
                    
                # Foundation
                if y > self.grid_height * 0.8:
                    structure = True
                
                grid[y][x] = 1 if structure else 0
                
        return self._grid_to_png_data(grid, "Architectural Forms - Geometric building structures")
    
    def _generate_sound_visualization(self):
        """Pure sound frequency visualization"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Frequency waves with harmonic overtones
                fundamental = math.sin(x * 0.2)
                harmonic2 = 0.5 * math.sin(x * 0.4)
                harmonic3 = 0.25 * math.sin(x * 0.6)
                
                wave_height = (fundamental + harmonic2 + harmonic3) * self.grid_height * 0.2
                wave_y = self.grid_height // 2 + int(wave_height)
                
                # Draw waveform
                grid[y][x] = 1 if abs(y - wave_y) < 2 else 0
                
        return self._grid_to_png_data(grid, "Sound Visualization - Frequency harmonics")
    
    def _generate_movement_flow(self):
        """Movement and gesture flow patterns"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Flowing gesture lines
                flow = math.sin(x * 0.1 + y * 0.15) + math.cos(x * 0.08)
                current = int((x + y * 0.5 + flow * 3)) % 8
                grid[y][x] = 1 if current < 2 else 0
                
        return self._grid_to_png_data(grid, "Movement Flow - Gestural dynamics")
    
    def _generate_barrier_navigation(self):
        """Strategic barrier navigation"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Random barriers with navigation strategy
                if random.random() > 0.8:  # Sparse barriers
                    grid[y][x] = 1
                elif (x + y) % 15 == 0:  # Navigation markers
                    grid[y][x] = 1
                else:
                    grid[y][x] = 0
                    
        return self._grid_to_png_data(grid, "Barrier Navigation - Strategic pathfinding")
    
    def _generate_meditation_pattern(self):
        """Contemplative, centered pattern"""
        grid = self._create_grid()
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                concentric = int(dist) % 4 == 0
                grid[y][x] = 1 if concentric and dist > 5 else 0
                
        return self._grid_to_png_data(grid, "Meditation Pattern - Centered contemplation")
    
    def _generate_energy_pattern(self):
        """Dynamic, energetic pattern"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                energy = math.sin(x * 0.5) * math.cos(y * 0.3) + random.random() * 0.5
                grid[y][x] = 1 if energy > 0.4 else 0
                
        return self._grid_to_png_data(grid, "Energy Pattern - Dynamic activation")
    
    def _generate_edge_pattern(self):
        """Sharp, critical pattern"""
        grid = self._create_grid()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Sharp angular patterns
                angular = (x + y) % 6 == 0 or abs(x - y) % 8 == 0
                grid[y][x] = 1 if angular else 0
                
        return self._grid_to_png_data(grid, "Edge Pattern - Sharp critical analysis")
    
    def _create_grid(self):
        """Create empty grid"""
        return [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
    
    def _grid_to_png_data(self, grid, description):
        """Convert grid to PNG bytes"""
        try:
            # Scale up grid to final image size
            pixels = []
            for grid_y in range(self.grid_height):
                for _ in range(self.pixel_size):  # Repeat each grid row
                    row = []
                    for grid_x in range(self.grid_width):
                        pixel_value = 255 if grid[grid_y][grid_x] == 0 else 0  # White=0, Black=1
                        for _ in range(self.pixel_size):  # Repeat each pixel
                            row.append(pixel_value)
                    pixels.append(row)
            
            # Create PNG
            png_data = self._create_png_bytes(pixels)
            
            return {
                'data': png_data,
                'description': description,
                'format': 'png',
                'size': f"{self.width}x{self.height}"
            }
            
        except Exception as e:
            # Fallback to description only
            return {
                'data': None,
                'description': description,
                'format': 'text',
                'error': str(e)
            }
    
    def _create_png_bytes(self, pixels):
        """Create PNG file bytes"""
        # PNG signature
        png_data = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', self.width, self.height, 8, 0, 0, 0, 0)
        png_data += struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data
        png_data += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
        
        # IDAT chunk (image data)
        image_data = b''
        for row in pixels:
            image_data += b'\x00'  # Filter type (None)
            image_data += bytes(row)
        
        compressed_data = zlib.compress(image_data)
        png_data += struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data
        png_data += struct.pack('>I', zlib.crc32(b'IDAT' + compressed_data) & 0xffffffff)
        
        # IEND chunk
        png_data += struct.pack('>I', 0) + b'IEND'
        png_data += struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
        
        return png_data

def demo_article_generation():
    """Demo how this integrates with article generation"""
    generator = ArticlePixelArtSuite(400, 300, 8)
    
    # Example article analysis
    sample_articles = [
        {
            'title': "Architects Are Designing Buildings for the Wrong Sense",
            'keywords': ['acoustic', 'architecture', 'sound', 'spatial', 'design'],
            'mood': 'critical',
            'agent': 'Siri Sage'
        },
        {
            'title': "Why Deaf Developers Create the Best User Interfaces",
            'keywords': ['visual', 'spatial', 'interface', 'design', 'gesture'],
            'mood': 'confident',
            'agent': 'Pixel Nova'
        },
        {
            'title': "Wheelchair Users Navigate Space Like GPS Algorithms",
            'keywords': ['navigation', 'pathways', 'barriers', 'access', 'movement'],
            'mood': 'analytical',
            'agent': 'Maya Flux'
        }
    ]
    
    for i, article in enumerate(sample_articles):
        print(f"\n🎨 GENERATING ART FOR: {article['title']}")
        print(f"Keywords: {article['keywords']}")
        print(f"Mood: {article['mood']}")
        print(f"Agent: {article['agent']}")
        
        # Generate images
        random.seed(42 + i)  # Reproducible but varied
        images = generator.generate_from_keywords(
            article['keywords'],
            article['mood'], 
            article['agent']
        )
        
        # Save images
        for j, img_data in enumerate(images):
            if img_data['data']:
                filename = f"/home/node/.openclaw/workspaces/ops/demo_article_{i+1}_image_{j+1}.png"
                with open(filename, 'wb') as f:
                    f.write(img_data['data'])
                print(f"  ✅ Generated: {filename}")
                print(f"     Description: {img_data['description']}")
            else:
                print(f"  ❌ Failed: {img_data.get('error', 'Unknown error')}")
                print(f"     Description: {img_data['description']}")

if __name__ == "__main__":
    print("🎨 ENHANCED PROCEDURAL PIXEL ART GENERATOR")
    print("Generating themed examples based on article analysis...")
    print()
    
    demo_article_generation()
    
    print(f"\n✅ Demo complete!")
    print("This generator can analyze article content and create thematic pixel art.")
    print("Ready for integration into daily article automation!")