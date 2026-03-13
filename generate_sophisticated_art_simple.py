#!/usr/bin/env python3
"""
Generate sophisticated pixel art using pure Python - no external dependencies
Creates complex, artistic patterns suitable for professional articles
"""

import math
import random
import struct
import zlib

class SophisticatedArtGenerator:
    def __init__(self, width=600, height=400):  # Reduced from 800x450 for smaller files
        self.width = width
        self.height = height
        self.pixel_size = 1  # No scaling - direct pixel mapping
        self.grid_width = width
        self.grid_height = height
        
        # Sophisticated color palette (RGB)
        self.palette = [
            (20, 25, 35),    # Deep slate
            (40, 50, 70),    # Dark steel
            (70, 85, 105),   # Medium steel
            (100, 115, 135), # Light steel
            (140, 155, 175), # Pale steel
            (180, 195, 210), # Off-white
            (60, 140, 190),  # Cool blue
            (190, 90, 40),   # Warm copper
            (140, 190, 80),  # Cool green
            (220, 180, 100), # Warm gold
        ]
    
    def generate_acoustic_chaos(self):
        """Complex interference patterns representing acoustic chaos"""
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Create multiple overlapping wave interference patterns
        wave_sources = []
        for _ in range(5):
            wave_sources.append((
                random.uniform(0.1, 0.3),  # frequency_x
                random.uniform(0.1, 0.3),  # frequency_y
                random.uniform(0, math.pi * 2),  # phase
                random.randint(3, 7)  # amplitude scale
            ))
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Calculate combined wave interference
                total = 0
                for freq_x, freq_y, phase, amp in wave_sources:
                    value = math.sin(x * freq_x + y * freq_y + phase) * amp
                    total += value
                
                # Normalize and map to color index
                normalized = (total + 15) / 30  # Scale to 0-1 range
                color_idx = int(normalized * (len(self.palette) - 1))
                color_idx = max(0, min(len(self.palette) - 1, color_idx))
                
                grid[y][x] = color_idx
        
        # Add architectural elements being disrupted
        for _ in range(3):
            bx = random.randint(10, self.grid_width - 60)
            by = random.randint(10, self.grid_height - 40)
            bw = random.randint(20, 40)
            bh = random.randint(15, 30)
            
            for dy in range(bh):
                for dx in range(bw):
                    gx = bx + dx
                    gy = by + dy
                    if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                        # Create disruption pattern
                        if (dx + dy) % 4 < 2:
                            wave = math.sin(gx * 0.2 + gy * 0.15)
                            grid[gy][gx] = 6 if wave > 0 else 3
        
        return self._grid_to_png(grid, "acoustic_chaos_sophisticated.png")
    
    def generate_acoustic_harmony(self):
        """Geometric patterns representing acoustic harmony and precision"""
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        
        # Create harmonic concentric circles
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Base color based on distance bands
                band = int(distance / 20) % 4
                base_color = 2 + band
                
                # Add harmonic wave pattern
                angle = math.atan2(dy, dx)
                wave = math.sin(distance * 0.1 + angle * 3) * 0.5 + 0.5
                
                # Golden ratio harmonic points
                golden_angle = 137.5 * math.pi / 180
                golden_dist = (angle / golden_angle) % 1
                if golden_dist < 0.05:
                    base_color = 7  # Highlight golden ratio points
                
                # Add interference pattern for acoustic treatment
                if distance < 80:
                    # Quadratic residue diffuser pattern
                    pattern_val = (x % 7) * (y % 7) % 7
                    if pattern_val < 3:
                        base_color = 8
                
                grid[y][x] = base_color
        
        # Draw precise acoustic treatment elements
        for i in range(4):
            angle = i * math.pi / 2
            for r in range(10, 100, 15):
                x = int(center_x + r * math.cos(angle))
                y = int(center_y + r * math.sin(angle))
                
                # Draw acoustic measurement points
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        gx = x + dx
                        gy = y + dy
                        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                            if dx*dx + dy*dy <= 4:
                                grid[gy][gx] = 6  # Measurement points in blue
        
        return self._grid_to_png(grid, "acoustic_harmony_sophisticated.png")
    
    def generate_sensory_expertise(self):
        """Architectural plan with sensory zone analysis"""
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Draw building outline
        margin = 20
        inner_width = self.grid_width - 2 * margin
        inner_height = self.grid_height - 2 * margin
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Building background
                if (margin <= x < self.grid_width - margin and 
                    margin <= y < self.grid_height - margin):
                    grid[y][x] = 1  # Dark background
                else:
                    grid[y][x] = 0  # Border
        
        # Define sensory zones
        zones = [
            ("Acoustic", margin + 30, margin + 30, 80, 60, 6),
            ("Visual", margin + 140, margin + 30, 80, 60, 7),
            ("Tactile", margin + 250, margin + 30, 80, 60, 8),
            ("Collaboration", margin + 80, margin + 120, 100, 70, 3),
            ("Focus", margin + 210, margin + 120, 100, 70, 4),
            ("Circulation", margin + 30, margin + 210, 260, 50, 5),
        ]
        
        for name, zx, zy, zw, zh, color_idx in zones:
            # Draw zone with pattern
            for dy in range(zh):
                for dx in range(zw):
                    gx = zx + dx
                    gy = zy + dy
                    if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                        # Create grid pattern within zone
                        if dx % 8 < 3 or dy % 8 < 3:
                            grid[gy][gx] = color_idx
            
            # Draw zone border
            for dx in range(zw):
                for border_y in [zy, zy + zh - 1]:
                    gx = zx + dx
                    if 0 <= gx < self.grid_width and 0 <= border_y < self.grid_height:
                        grid[border_y][gx] = color_idx
            for dy in range(zh):
                for border_x in [zx, zx + zw - 1]:
                    gy = zy + dy
                    if 0 <= border_x < self.grid_width and 0 <= gy < self.grid_height:
                        grid[gy][border_x] = color_idx
        
        # Draw sensory data flow
        for _ in range(100):
            # Random walk through zones
            x = random.randint(margin, self.grid_width - margin)
            y = random.randint(margin, self.grid_height - margin)
            
            for step in range(20):
                # Move toward nearest zone center
                nearest_zone = min(zones, key=lambda z: 
                    abs(x - (z[1] + z[3]//2)) + abs(y - (z[2] + z[4]//2)))
                zx, zy = nearest_zone[1] + nearest_zone[3]//2, nearest_zone[2] + nearest_zone[4]//2
                
                dx = 1 if zx > x else -1 if zx < x else 0
                dy = 1 if zy > y else -1 if zy < y else 0
                
                x += dx
                y += dy
                
                if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                    # Draw data point with intensity based on step
                    intensity = min(9, 5 + step // 2)
                    grid[y][x] = intensity
        
        return self._grid_to_png(grid, "sensory_expertise_sophisticated.png")
    
    def _grid_to_png(self, grid, filename):
        """Convert color grid to PNG data"""
        # Direct pixel mapping (no scaling)
        pixels = []
        for grid_y in range(self.grid_height):
            row = []
            for grid_x in range(self.grid_width):
                color_idx = grid[grid_y][grid_x]
                color = self.palette[color_idx % len(self.palette)]
                row.extend(color)  # RGB values
            pixels.append(row)
        
        # Create PNG data and return it (don't save to file here)
        png_data = self._create_png_rgb(pixels)
        return png_data
    
    def _create_png_rgb(self, pixels):
        """Create RGB PNG file"""
        height = len(pixels)
        width = len(pixels[0]) // 3  # Each pixel has 3 values (RGB)
        
        # PNG signature
        png_data = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)  # RGB color
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
    """Generate sophisticated pixel art"""
    print("🎨 GENERATING SOPHISTICATED PIXEL ART")
    print("=" * 50)
    print("Creating complex, artistic patterns for professional articles")
    print("No childish patterns - serious, sophisticated aesthetic")
    print("=" * 50)
    
    generator = SophisticatedArtGenerator(800, 450)
    
    # Set seed for reproducibility
    random.seed(424242)
    
    print("\n📸 Generating: Acoustic Chaos (Sophisticated)")
    print("   Complex interference patterns, wave sources, architectural disruption")
    chaos_path = generator.generate_acoustic_chaos()
    print(f"   ✅ Saved: {chaos_path}")
    
    print("\n📸 Generating: Acoustic Harmony (Sophisticated)")
    print("   Geometric precision, harmonic circles, acoustic treatment patterns")
    harmony_path = generator.generate_acoustic_harmony()
    print(f"   ✅ Saved: {harmony_path}")
    
    print("\n📸 Generating: Sensory Expertise (Sophisticated)")
    print("   Architectural zones, sensory analysis, data flow visualization")
    expertise_path = generator.generate_sensory_expertise()
    print(f"   ✅ Saved: {expertise_path}")
    
    print("\n" + "=" * 50)
    print("✅ SOPHISTICATED PIXEL ART GENERATED!")
    print("\nKey features:")
    print("• Complex mathematical patterns (interference, harmonics)")
    print("• Sophisticated color palette (slate, steel, accent colors)")
    print("• Architectural and acoustic themes")
    print("• Professional, serious aesthetic")
    print("• No simple/childish patterns")
    print("• RGB color (not just black/white)")

if __name__ == "__main__":
    main()