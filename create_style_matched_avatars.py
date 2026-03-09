#!/usr/bin/env python3
"""
Create agent avatars that match the rendering technique/style of reference images
Based on: acoustic_architecture_inline.png, visual_spatial_cognition_inline.png,
refined_accessibility_pathways.png, demo_neurodivergent_v2.png
"""

import math
import random
import struct
import zlib

class StyleMatchedAvatarGenerator:
    def __init__(self, width=400, height=400):
        self.width = width
        self.height = height
        
        # Analyze the style of reference images and create matching color palettes
        # Based on visual inspection of the reference images
        
        # acoustic_architecture_inline.png style: Blue/orange, geometric, architectural
        self.siri_sage_palette = [
            (20, 30, 50),    # Deep navy
            (40, 60, 90),    # Midnight blue
            (80, 110, 150),  # Steel blue
            (120, 150, 190), # Sky blue
            (180, 200, 220), # Light blue
            (220, 180, 100), # Golden accent
            (180, 120, 60),  # Copper
            (255, 220, 180), # Cream highlight
        ]
        
        # visual_spatial_cognition_inline.png style: Purple/green, grid-based, structured
        self.pixel_nova_palette = [
            (30, 20, 40),    # Deep purple
            (60, 40, 80),    # Royal purple
            (100, 80, 140),  # Lavender
            (140, 120, 180), # Light purple
            (180, 160, 220), # Pale lavender
            (120, 200, 160), # Mint green
            (80, 160, 120),  # Emerald green
            (220, 240, 220), # Off-white
        ]
        
        # refined_accessibility_pathways.png style: Green/orange, flowing, organic
        self.maya_flux_palette = [
            (20, 40, 30),    # Forest green
            (40, 70, 50),    # Deep green
            (80, 120, 90),   # Emerald
            (120, 160, 130), # Light green
            (160, 200, 170), # Pale green
            (220, 160, 80),  # Orange
            (180, 120, 60),  # Brown-orange
            (240, 230, 220), # Cream
        ]
        
        # demo_neurodivergent_v2.png style: Brown/blue, circuit-like, interconnected
        self.zen_circuit_palette = [
            (40, 30, 20),    # Deep brown
            (70, 50, 40),    # Chocolate
            (100, 80, 60),   # Tan
            (140, 120, 100), # Light brown
            (180, 160, 140), # Beige
            (80, 140, 200),  # Sky blue
            (120, 180, 240), # Light blue
            (220, 220, 240), # Pale blue
        ]
    
    def generate_siri_sage_style_matched(self):
        """Siri Sage avatar in acoustic_architecture_inline.png style"""
        palette = self.siri_sage_palette
        grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        center_x, center_y = self.width // 2, self.height // 2
        
        # Create architectural/geometric patterns like acoustic_architecture_inline.png
        for y in range(self.height):
            for x in range(self.width):
                # Geometric grid with acoustic wave interference
                grid_x = (x - center_x) / 50.0
                grid_y = (y - center_y) / 50.0
                
                # Radial waves (acoustic patterns)
                distance = math.sqrt((x - center_x)**2 + (y - center_y)**2) / 100.0
                wave1 = math.sin(distance * 8.0) * 0.5 + 0.5
                
                # Angular patterns (architectural geometry)
                angle = math.atan2(y - center_y, x - center_x)
                pattern1 = math.sin(angle * 6.0 + distance * 4.0) * 0.3 + 0.7
                
                # Grid overlay
                grid_pattern = (math.sin(grid_x * 3.0) * math.cos(grid_y * 3.0)) * 0.2 + 0.8
                
                combined = (wave1 * 0.4 + pattern1 * 0.3 + grid_pattern * 0.3)
                color_idx = min(len(palette) - 1, int(combined * (len(palette) - 1)))
                grid[y][x] = color_idx
        
        # Add architectural elements (like in reference image)
        for i in range(8):
            angle = i * math.pi / 4
            radius = 120
            px = int(center_x + math.cos(angle) * radius)
            py = int(center_y + math.sin(angle) * radius)
            
            # Draw geometric acoustic diffuser shapes
            for dy in range(-10, 11):
                for dx in range(-10, 11):
                    if abs(dx) + abs(dy) < 12:  # Diamond shape
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if (dx + dy) % 3 == 0:
                                grid[ny][nx] = 5  # Golden accent
        
        return self._save_png(grid, palette, "siri_sage_style_matched.png")
    
    def generate_pixel_nova_style_matched(self):
        """Pixel Nova avatar in visual_spatial_cognition_inline.png style"""
        palette = self.pixel_nova_palette
        grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Create grid-based visual patterns like visual_spatial_cognition_inline.png
        grid_size = 25
        for y in range(self.height):
            for x in range(self.width):
                # Moiré pattern (characteristic of reference image)
                pattern1 = math.sin(x * 0.03) * math.cos(y * 0.04)
                pattern2 = math.sin((x + y) * 0.02) * math.cos((x - y) * 0.025)
                pattern3 = math.sin(x * 0.05 + y * 0.03) * 0.5 + 0.5
                
                combined = (pattern1 + pattern2) * 0.3 + pattern3 * 0.4
                color_idx = min(len(palette) - 1, int((combined * 0.5 + 0.5) * (len(palette) - 1)))
                
                # Grid overlay
                if x % grid_size < 2 or y % grid_size < 2:
                    color_idx = 6  # Mint green grid lines
                
                grid[y][x] = color_idx
        
        # Central visual focus (like reference image's central structure)
        center_x, center_y = self.width // 2, self.height // 2
        for y in range(self.height):
            for x in range(self.width):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 60:
                    # Radial gradient with pattern
                    radial = (distance / 60.0)
                    pattern = math.sin(dx * 0.1) * math.cos(dy * 0.1) * 0.3 + 0.7
                    color_idx = min(len(palette) - 1, int((1 - radial * 0.7) * pattern * (len(palette) - 1)))
                    grid[y][x] = color_idx
        
        return self._save_png(grid, palette, "pixel_nova_style_matched.png")
    
    def generate_maya_flux_style_matched(self):
        """Maya Flux avatar in refined_accessibility_pathways.png style"""
        palette = self.maya_flux_palette
        grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Create flowing pathway patterns like refined_accessibility_pathways.png
        center_x, center_y = self.width // 2, self.height // 2
        
        for y in range(self.height):
            for x in range(self.width):
                # Flowing, organic patterns
                flow_x = math.sin(y * 0.02) * 40 + math.cos(x * 0.015) * 30
                flow_y = math.cos(x * 0.018) * 35 + math.sin(y * 0.025) * 25
                
                dx = x - (center_x + flow_x)
                dy = y - (center_y + flow_y)
                distance = math.sqrt(dx*dx + dy*dy) / 50.0
                
                # Pathway texture
                if distance < 0.8:
                    texture = math.sin(x * 0.05) * math.cos(y * 0.05) * 0.4 + 0.6
                    color_idx = min(len(palette) - 1, int(texture * 3) + 2)
                else:
                    # Background with subtle texture
                    terrain = math.sin(x * 0.01 + y * 0.015) * 0.3 + 0.7
                    color_idx = min(len(palette) - 1, int(terrain * 2))
                
                grid[y][x] = color_idx
        
        # Pathway nodes/intersections
        for i in range(6):
            angle = i * math.pi / 3
            radius = 100
            px = int(center_x + math.cos(angle) * radius)
            py = int(center_y + math.sin(angle) * radius)
            
            # Circular nodes with pattern
            for dy in range(-12, 13):
                for dx in range(-12, 13):
                    if dx*dx + dy*dy < 144:
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            # Checkerboard pattern
                            if (dx + dy) % 4 < 2:
                                grid[ny][nx] = 5  # Orange
                            else:
                                grid[ny][nx] = 6  # Brown-orange
        
        return self._save_png(grid, palette, "maya_flux_style_matched.png")
    
    def generate_zen_circuit_style_matched(self):
        """Zen Circuit avatar in demo_neurodivergent_v2.png style"""
        palette = self.zen_circuit_palette
        grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Create circuit/neural network patterns like demo_neurodivergent_v2.png
        center_x, center_y = self.width // 2, self.height // 2
        
        # Circuit grid
        cell_size = 30
        for y in range(0, self.height, cell_size):
            for x in range(0, self.width, cell_size):
                # Circuit nodes
                for dy in range(-4, 5):
                    for dx in range(-4, 5):
                        if dx*dx + dy*dy < 16:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                grid[ny][nx] = 5  # Sky blue nodes
        
        # Connect nodes with circuit traces (dotted lines)
        for y in range(0, self.height, cell_size):
            for x in range(0, self.width, cell_size):
                # Horizontal connections
                if x + cell_size < self.width:
                    for offset in range(0, cell_size + 1, 3):
                        nx = x + offset
                        if 0 <= nx < self.width and 0 <= y < self.height:
                            grid[y][nx] = 4  # Light brown trace
                
                # Vertical connections
                if y + cell_size < self.height:
                    for offset in range(0, cell_size + 1, 3):
                        ny = y + offset
                        if 0 <= x < self.width and 0 <= ny < self.height:
                            grid[ny][x] = 4  # Light brown trace
        
        # Central processing core
        for y in range(self.height):
            for x in range(self.width):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 50:
                    # Circuit core pattern
                    angle = math.atan2(dy, dx)
                    pattern = math.sin(distance * 0.2) * math.cos(angle * 8) * 0.5 + 0.5
                    color_idx = min(len(palette) - 1, int(pattern * 3) + 1)
                    
                    # Binary/data pattern in center
                    if distance < 20:
                        if (x + y) % 6 < 3:
                            color_idx = 6  # Light blue
                        else:
                            color_idx = 7  # Pale blue
                    
                    grid[y][x] = color_idx
        
        return self._save_png(grid, palette, "zen_circuit_style_matched.png")
    
    def _save_png(self, grid, palette, filename):
        """Save grid as PNG with proper color depth"""
        height = len(grid)
        width = len(grid[0])
        
        # Create image data
        pixels = []
        for y in range(height):
            row = []
            for x in range(width):
                color_idx = grid[y][x]
                color = palette[color_idx % len(palette)]
                row.extend(color)  # RGB
            pixels.append(row)
        
        # Generate PNG
        png_data = self._create_png_rgb(pixels)
        
        path = f"/home/node/.openclaw/workspaces/ops/disability-ai-collective/assets/{filename}"
        with open(path, 'wb') as f:
            f.write(png_data)
        
        print(f"  ✅ Generated: {filename} ({width}x{height})")
        return path
    
    def _create_png_rgb(self, pixels):
        """Create RGB PNG file"""
        height = len(pixels)
        width = len(pixels[0]) // 3
        
        # PNG signature
        png_data = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        png_data += struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data
        png_data += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
        
        # IDAT chunk
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

def main():
    print("🎨 CREATING STYLE-MATCHED AGENT AVATARS")
    print("=" * 50)
    print("Matching rendering technique of reference images:")
    print("  • acoustic_architecture_inline.png → Siri Sage")
    print("  • visual_spatial_cognition_inline.png → Pixel Nova")
    print("  • refined_accessibility_pathways.png → Maya Flux")
    print("  • demo_neurodivergent_v2.png → Zen Circuit")
    print()
    
    generator = StyleMatchedAvatarGenerator(400, 400)
    
    # Set seed for reproducibility
    random.seed(42424242)
    
    print("👤 Generating Siri Sage avatar (acoustic architecture style)...")
    generator.generate_siri_sage_style_matched()
    
    print("👤 Generating Pixel Nova avatar (visual spatial cognition style)...")
    generator.generate_pixel_nova_style_matched()
    
    print("👤 Generating Maya Flux avatar (accessibility pathways style)...")
    generator.generate_maya_flux_style_matched()
    
    print("👤 Generating Zen Circuit avatar (neurodivergent circuit style)...")
    generator.generate_zen_circuit_style_matched()
    
    print("\n" + "=" * 50)
    print("✅ STYLE-MATCHED AVATARS GENERATED!")
    print("\nNew avatars created in assets/ directory:")
    print("  • siri_sage_style_matched.png")
    print("  • pixel_nova_style_matched.png")
    print("  • maya_flux_style_matched.png")
    print("  • zen_circuit_style_matched.png")
    print("\nThese match the rendering technique of the reference images.")
    print("\nNext: Update website files to use these new style-matched avatars.")

if __name__ == "__main__":
    main()